from odoo import http, fields
from odoo.http import request
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class ShopifyOrderController(http.Controller):

    # --- HELPER: MAP ADDRESS DATA ---
    def _get_or_create_partner(self, data, parent_id=False, address_type='contact', shopify_id=False):
        if not data:
            return False

        ResPartner = request.env['res.partner'].sudo()
        domain = []
        
        if shopify_id:
            domain = [('shopify_customer_id', '=', str(shopify_id))]
        elif parent_id and data.get('first_name'):
            # Look for existing billing/shipping addresses under the parent
            domain = [
                ('parent_id', '=', parent_id), 
                ('type', '=', address_type),
                ('name', 'ilike', f"{data.get('first_name', '')} {data.get('last_name', '')}".strip())
            ]

        partner = ResPartner.search(domain, limit=1) if domain else False

        partner_vals = {
            'name': f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or data.get('name') or 'Shopify Customer',
            'email': data.get('email'),
            'phone': data.get('phone'),
            'street': data.get('address1'),
            'street2': data.get('address2'),
            'city': data.get('city'),
            'zip': data.get('zip'),
            'type': address_type,
        }

        if parent_id:
            partner_vals['parent_id'] = parent_id
        if shopify_id:
            partner_vals['shopify_customer_id'] = str(shopify_id)

        # Map Country and State
        country_code = data.get('country_code')
        if country_code:
            country = request.env['res.country'].sudo().search([('code', '=', country_code)], limit=1)
            if country:
                partner_vals['country_id'] = country.id
                province_code = data.get('province_code')
                if province_code:
                    state = request.env['res.country.state'].sudo().search([
                        ('code', '=', province_code),
                        ('country_id', '=', country.id)
                    ], limit=1)
                    if state:
                        partner_vals['state_id'] = state.id

        if partner:
            partner.write(partner_vals)
            return partner
        else:
            return ResPartner.create(partner_vals)

    # --- HELPER: ON-THE-FLY PRODUCT CREATION ---
    def _get_or_create_product(self, line):
        product_id = str(line.get('product_id')) if line.get('product_id') else False
        variant_id = str(line.get('variant_id')) if line.get('variant_id') else False
        sku = line.get('sku')
        title = line.get('title', 'Unknown Shopify Product')
        price = float(line.get('price', 0.0))

        ProductProduct = request.env['product.product'].sudo()
        ProductTemplate = request.env['product.template'].sudo()

        # 1. Try finding by Variant ID
        if variant_id:
            product = ProductProduct.search([('shopify_variant_id', '=', variant_id)], limit=1)
            if product: return product

        # 2. Try finding by Product ID (Fallback to template)
        if product_id:
            template = ProductTemplate.search([('shopify_product_id', '=', product_id)], limit=1)
            if template:
                return ProductProduct.search([('product_tmpl_id', '=', template.id)], limit=1)
        
        # 3. Try finding by SKU
        if sku:
            product = ProductProduct.search([('default_code', '=', sku)], limit=1)
            if product:
                # Update it with Shopify IDs so we don't have to search by SKU next time
                product.write({'shopify_variant_id': variant_id})
                product.product_tmpl_id.write({'shopify_product_id': product_id})
                return product

        # 4. If all fails, CREATE THE PRODUCT ON THE FLY
        _logger.info(f"Product not found in Odoo. Creating on the fly: {title} (SKU: {sku})")
        new_template = ProductTemplate.create({
            'name': title,
            'list_price': price,
            'type': 'consu',
            'is_storable': True,
            'shopify_product_id': product_id,
        })
        
        # Odoo auto-creates 1 variant. Let's update it with the SKU and Variant ID
        new_product = ProductProduct.search([('product_tmpl_id', '=', new_template.id)], limit=1)
        new_product.write({
            'default_code': sku,
            'shopify_variant_id': variant_id
        })
        
        return new_product

    # --- UPSERT: CREATE OR UPDATE ORDER ---
    @http.route(['/shopify/webhook/order_create', '/shopify/webhook/order_update'], type='http', auth='public', methods=['POST'], csrf=False)
    def shopify_order_sync(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.data)
            shopify_order_id = str(payload.get('id'))
            
            if not shopify_order_id or shopify_order_id == 'None':
                return request.make_response(json.dumps({'error': 'No Shopify Order ID'}), status=400)

            # 1. MAP MAX CUSTOMER DATA (Main, Billing, Shipping)
            customer_data = payload.get('customer')
            main_partner = self._get_or_create_partner(
                data=customer_data.get('default_address') if customer_data and customer_data.get('default_address') else customer_data,
                address_type='contact',
                shopify_id=customer_data.get('id') if customer_data else False
            )

            # If the payload lacks a customer block but has billing, use billing as main
            if not main_partner and payload.get('billing_address'):
                main_partner = self._get_or_create_partner(payload.get('billing_address'), address_type='contact')

            if not main_partner:
                return request.make_response(json.dumps({'error': 'Could not resolve customer'}), status=400)

            invoice_partner = self._get_or_create_partner(payload.get('billing_address'), parent_id=main_partner.id, address_type='invoice')
            shipping_partner = self._get_or_create_partner(payload.get('shipping_address'), parent_id=main_partner.id, address_type='delivery')

            # 2. BUILD THE ORDER HEADER
            # Parse order date (Shopify uses ISO format with timezone, we extract just the date/time string for Odoo)
            date_order = fields.Datetime.now()
            if payload.get('created_at'):
                try:
                    date_order = datetime.strptime(payload.get('created_at')[:19], "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass

            # Combine tags and notes
            order_notes = payload.get('note') or ""
            if payload.get('tags'):
                order_notes += f"\nTags: {payload.get('tags')}"

            order_vals = {
                'partner_id': main_partner.id,
                'partner_invoice_id': invoice_partner.id if invoice_partner else main_partner.id,
                'partner_shipping_id': shipping_partner.id if shipping_partner else main_partner.id,
                'shopify_order_id': shopify_order_id,
                'client_order_ref': payload.get('name'), # e.g. #9999
                'note': order_notes.strip(),
                'date_order': date_order,
            }

            SaleOrder = request.env['sale.order'].sudo()
            existing_order = SaleOrder.search([('shopify_order_id', '=', shopify_order_id)], limit=1)

            if existing_order:
                existing_order.write(order_vals)
                order = existing_order
            else:
                order = SaleOrder.create(order_vals)

            # 3. PROCESS LINE ITEMS (WITH ON-THE-FLY CREATION)
            incoming_line_ids = []
            for line in payload.get('line_items', []):
                shopify_line_id = str(line.get('id'))
                incoming_line_ids.append(shopify_line_id)
                
                # Get existing product or create it instantly!
                product = self._get_or_create_product(line)

                line_vals = {
                    'order_id': order.id,
                    'product_id': product.id,
                    'product_uom_qty': float(line.get('quantity', 1)),
                    'price_unit': float(line.get('price', 0.0)),
                    'name': line.get('name') or line.get('title'),
                    'shopify_line_id': shopify_line_id
                }

                existing_line = request.env['sale.order.line'].sudo().search([('order_id', '=', order.id), ('shopify_line_id', '=', shopify_line_id)], limit=1)
                if existing_line:
                    existing_line.write(line_vals)
                else:
                    request.env['sale.order.line'].sudo().create(line_vals)

            # 4. PROCESS SHIPPING LINES
            for ship_line in payload.get('shipping_lines', []):
                ship_price = float(ship_line.get('price', 0.0))
                if ship_price >= 0:
                    shipping_product = request.env['product.product'].sudo().search([('default_code', '=', 'SHIP')], limit=1)
                    if not shipping_product:
                        shipping_product = request.env['product.product'].sudo().create({
                            'name': 'Shipping Charge',
                            'type': 'service',
                            'default_code': 'SHIP'
                        })
                    
                    ship_line_id = f"ship_{ship_line.get('id')}"
                    incoming_line_ids.append(ship_line_id)

                    ship_vals = {
                        'order_id': order.id,
                        'product_id': shipping_product.id,
                        'product_uom_qty': 1.0,
                        'price_unit': ship_price,
                        'name': ship_line.get('title', 'Shipping'),
                        'shopify_line_id': ship_line_id
                    }

                    existing_ship = request.env['sale.order.line'].sudo().search([('order_id', '=', order.id), ('shopify_line_id', '=', ship_line_id)], limit=1)
                    if existing_ship:
                        existing_ship.write(ship_vals)
                    else:
                        request.env['sale.order.line'].sudo().create(ship_vals)

            # 5. CLEAN UP REMOVED LINES (For Updates)
            for order_line in order.order_line:
                if order_line.shopify_line_id and order_line.shopify_line_id not in incoming_line_ids:
                    order_line.unlink()

            return request.make_response(json.dumps({'status': 'success', 'order': order.client_order_ref}), headers=[('Content-Type', 'application/json')])

        except Exception as e:
            _logger.error(f"Shopify Order Sync Error: {str(e)}")
            return request.make_response(json.dumps({'error': str(e)}), status=500)

    # --- DELETE: CANCEL ORDER ---
    @http.route('/shopify/webhook/order_delete', type='http', auth='public', methods=['POST'], csrf=False)
    def shopify_order_delete(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.data)
            shopify_order_id = str(payload.get('id'))
            
            order = request.env['sale.order'].sudo().search([('shopify_order_id', '=', shopify_order_id)], limit=1)
            if order and order.state != 'cancel':
                order.action_cancel()

            return request.make_response(json.dumps({'status': 'cancelled'}), headers=[('Content-Type', 'application/json')])
        except Exception as e:
            return request.make_response(json.dumps({'error': str(e)}), status=500)