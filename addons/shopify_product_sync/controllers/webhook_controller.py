from odoo import http
from odoo.http import request
from odoo.tools import html2plaintext # Imports Odoo's HTML stripper
import json
import logging

_logger = logging.getLogger(__name__)

class ShopifyWebhookController(http.Controller):

    @http.route('/shopify/webhook/product_create', type='http', auth='public', methods=['POST'], csrf=False)
    def shopify_product_create(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.data)
            
            shopify_id = str(payload.get('id'))
            if not shopify_id or shopify_id == 'None':
                return request.make_response(json.dumps({'error': 'No Shopify ID provided'}), status=400)

            title = payload.get('title')
            # Clean the HTML tags into plain text for Odoo's quotation fields
            raw_html = payload.get('body_html') or ''
            clean_description = html2plaintext(raw_html)
            
            variants = payload.get('variants', [])
            options = payload.get('options', [])

            ProductTemplate = request.env['product.template'].sudo()
            ProductProduct = request.env['product.product'].sudo()

            # 1. Handle the Product Template (Parent)
            existing_template = ProductTemplate.search([('shopify_product_id', '=', shopify_id)], limit=1)

            # Establish the base list_price from the first variant
            list_price = float(variants[0].get('price', 0.0)) if variants else 0.0
            
            template_vals = {
                'name': title,
                'description_sale': clean_description, # Use the cleaned text here
                'list_price': list_price,
                'type': 'consu',          # Goods in Odoo 19
                'is_storable': True,      # Enables inventory tracking
                'shopify_product_id': shopify_id,
            }

            if existing_template:
                existing_template.write(template_vals)
                template = existing_template
                _logger.info(f"Updated Shopify Template: {title}")
            else:
                template = ProductTemplate.create(template_vals)
                _logger.info(f"Created Shopify Template: {title}")

            # --- THE FALLBACK FIX ---
            if not options and variants:
                inferred_vals = set(v.get('option1') for v in variants if v.get('option1') and v.get('option1') != 'Default Title')
                if inferred_vals:
                    options.append({'name': 'Variation', 'values': list(inferred_vals)})

            # 2. Handle Attributes
            if options:
                for option in options:
                    attr_name = option.get('name')
                    attr_values = option.get('values', [])
                    
                    if attr_name == 'Title' and 'Default Title' in attr_values:
                        continue 
                        
                    attribute = request.env['product.attribute'].sudo().search([('name', '=', attr_name)], limit=1)
                    if not attribute:
                        attribute = request.env['product.attribute'].sudo().create({'name': attr_name})
                    
                    val_ids = []
                    for val_name in attr_values:
                        attr_val = request.env['product.attribute.value'].sudo().search([
                            ('name', '=', val_name),
                            ('attribute_id', '=', attribute.id)
                        ], limit=1)
                        if not attr_val:
                            attr_val = request.env['product.attribute.value'].sudo().create({
                                'name': val_name,
                                'attribute_id': attribute.id
                            })
                        val_ids.append(attr_val.id)
                    
                    attr_line = request.env['product.template.attribute.line'].sudo().search([
                        ('product_tmpl_id', '=', template.id),
                        ('attribute_id', '=', attribute.id)
                    ], limit=1)
                    
                    if attr_line:
                        attr_line.write({'value_ids': [(6, 0, val_ids)]})
                    else:
                        request.env['product.template.attribute.line'].sudo().create({
                            'product_tmpl_id': template.id,
                            'attribute_id': attribute.id,
                            'value_ids': [(6, 0, val_ids)]
                        })

            # 3. Update the Auto-Generated Variants & Set Pricing
            if variants:
                odoo_variants = ProductProduct.search([('product_tmpl_id', '=', template.id)])
                
                for var in variants:
                    var_id = str(var.get('id'))
                    var_sku = var.get('sku') or False
                    option1 = var.get('option1') 
                    var_price = float(var.get('price', 0.0))
                    
                    for ov in odoo_variants:
                        val_names = ov.product_template_attribute_value_ids.mapped('name')
                        
                        if len(odoo_variants) == 1 or (option1 and option1 in val_names):
                            ov.write({
                                'shopify_variant_id': var_id,
                                'default_code': var_sku,
                            })
                            
                            # Calculate and apply the Odoo price_extra
                            # Odoo Variant Price = Template Base Price + Extra Price
                            price_extra = var_price - list_price
                            if ov.product_template_attribute_value_ids:
                                ov.product_template_attribute_value_ids[0].write({'price_extra': price_extra})

                            _logger.info(f"Mapped Variant: {var_sku} | Extra Price: {price_extra}")
                            break

            return request.make_response(
                json.dumps({'status': 'success', 'shopify_id': shopify_id}), 
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            _logger.error(f"Shopify Product Webhook Error: {str(e)}")
            return request.make_response(json.dumps({'error': 'Internal Server Error'}), status=500)