from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class ShopifyCustomerController(http.Controller):

    # --- UPSERT: CREATE OR UPDATE CUSTOMER ---
    @http.route([
        '/shopify/webhook/customer_create', 
        '/shopify/webhook/customer_update'
    ], type='http', auth='public', methods=['POST'], csrf=False)
    def shopify_customer_sync(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.data)
            
            shopify_id = str(payload.get('id'))
            if not shopify_id or shopify_id == 'None':
                return request.make_response(json.dumps({'error': 'No Shopify Customer ID provided'}), status=400)

            # Combine First and Last Name
            first_name = payload.get('first_name') or ''
            last_name = payload.get('last_name') or ''
            full_name = f"{first_name} {last_name}".strip()
            
            # Fallback if name is completely empty
            if not full_name:
                full_name = payload.get('email', f"Shopify Customer {shopify_id}")

            partner_vals = {
                'name': full_name,
                'email': payload.get('email'),
                'phone': payload.get('phone'),
                'comment': payload.get('note'),
                'shopify_customer_id': shopify_id,
            }

            # Address mapping
            default_address = payload.get('default_address')
            if default_address:
                partner_vals.update({
                    'street': default_address.get('address1'),
                    'street2': default_address.get('address2'),
                    'city': default_address.get('city'),
                    'zip': default_address.get('zip'),
                })
                
                # Use address phone if main account phone is null
                if not partner_vals['phone']:
                    partner_vals['phone'] = default_address.get('phone')

                # Map Country (e.g., "CA" -> Canada)
                country_code = default_address.get('country_code')
                if country_code:
                    country = request.env['res.country'].sudo().search([('code', '=', country_code)], limit=1)
                    if country:
                        partner_vals['country_id'] = country.id
                        
                        # Map State/Province (e.g., "ON" -> Ontario), MUST match Country
                        province_code = default_address.get('province_code')
                        if province_code:
                            state = request.env['res.country.state'].sudo().search([
                                ('code', '=', province_code),
                                ('country_id', '=', country.id)
                            ], limit=1)
                            if state:
                                partner_vals['state_id'] = state.id

            ResPartner = request.env['res.partner'].sudo()
            existing_partner = ResPartner.search([('shopify_customer_id', '=', shopify_id)], limit=1)

            if existing_partner:
                existing_partner.write(partner_vals)
                _logger.info(f"Updated Shopify Customer: {full_name}")
            else:
                ResPartner.create(partner_vals)
                _logger.info(f"Created Shopify Customer: {full_name}")

            return request.make_response(
                json.dumps({'status': 'success', 'shopify_customer_id': shopify_id}), 
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            _logger.error(f"Shopify Customer Sync Error: {str(e)}")
            return request.make_response(json.dumps({'error': 'Internal Server Error'}), status=500)

    # --- DELETE: ARCHIVE CUSTOMER ---
    @http.route('/shopify/webhook/customer_delete', type='http', auth='public', methods=['POST'], csrf=False)
    def shopify_customer_delete(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.data)
            
            shopify_id = str(payload.get('id'))
            if not shopify_id or shopify_id == 'None':
                return request.make_response(json.dumps({'error': 'No Shopify Customer ID provided'}), status=400)

            ResPartner = request.env['res.partner'].sudo()
            existing_partner = ResPartner.search([('shopify_customer_id', '=', shopify_id)], limit=1)

            if existing_partner:
                # Soft delete to preserve historical invoice/sales order integrity
                existing_partner.write({'active': False})
                _logger.info(f"Archived Shopify Customer ID: {shopify_id}")
            else:
                _logger.warning(f"Delete request ignored: Shopify Customer ID {shopify_id} not found.")

            return request.make_response(
                json.dumps({'status': 'success', 'shopify_customer_id': shopify_id, 'action': 'archived'}), 
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            _logger.error(f"Shopify Customer Delete Error: {str(e)}")
            return request.make_response(json.dumps({'error': 'Internal Server Error'}), status=500)