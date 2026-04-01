from odoo import http
from odoo.http import request
from odoo.tools import html2plaintext
import json
import logging
import requests
import base64

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
            raw_html = payload.get('body_html') or ''
            clean_description = html2plaintext(raw_html)
            
            variants = payload.get('variants', [])
            options = payload.get('options', [])

            # --- FETCH THE MAIN IMAGE ---
            image_base64 = False
            image_data = payload.get('image')
            if image_data and image_data.get('src'):
                try:
                    response = requests.get(image_data.get('src'), timeout=10)
                    if response.status_code == 200:
                        image_base64 = base64.b64encode(response.content)
                except Exception as img_e:
                    _logger.warning(f"Could not fetch main image for {title}: {str(img_e)}")

            ProductTemplate = request.env['product.template'].sudo()
            ProductProduct = request.env['product.product'].sudo()

            existing_template = ProductTemplate.search([('shopify_product_id', '=', shopify_id)], limit=1)
            list_price = float(variants[0].get('price', 0.0)) if variants else 0.0
            
            template_vals = {
                'name': title,
                'description_sale': clean_description,
                'list_price': list_price,
                'type': 'consu',          
                'is_storable': True,      
                'shopify_product_id': shopify_id,
            }

            if image_base64:
                template_vals['image_1920'] = image_base64

            if existing_template:
                existing_template.write(template_vals)
                template = existing_template
                _logger.info(f"Updated Shopify Template: {title}")
            else:
                template = ProductTemplate.create(template_vals)
                _logger.info(f"Created Shopify Template: {title}")

            if not options and variants:
                inferred_vals = set(v.get('option1') for v in variants if v.get('option1') and v.get('option1') != 'Default Title')
                if inferred_vals:
                    options.append({'name': 'Variation', 'values': list(inferred_vals)})

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

            # --- PROCESS VARIANTS & SPECIFIC IMAGES ---
            if variants:
                odoo_variants = ProductProduct.search([('product_tmpl_id', '=', template.id)])
                
                # Create a lookup map for variant image URLs from the payload's bottom 'images' array
                master_images = {img.get('id'): img.get('src') for img in payload.get('images', [])}
                downloaded_images = {} # Cache to avoid re-downloading the same image
                
                for var in variants:
                    var_id = str(var.get('id'))
                    var_sku = var.get('sku') or False
                    option1 = var.get('option1') 
                    var_price = float(var.get('price', 0.0))
                    var_img_id = var.get('image_id')
                    
                    for ov in odoo_variants:
                        val_names = ov.product_template_attribute_value_ids.mapped('name')
                        
                        if len(odoo_variants) == 1 or (option1 and option1 in val_names):
                            var_vals = {
                                'shopify_variant_id': var_id,
                                'default_code': var_sku,
                            }
                            
                            # If the variant has a specific image, download and apply it
                            if var_img_id and var_img_id in master_images:
                                if var_img_id not in downloaded_images:
                                    try:
                                        img_resp = requests.get(master_images[var_img_id], timeout=10)
                                        if img_resp.status_code == 200:
                                            downloaded_images[var_img_id] = base64.b64encode(img_resp.content)
                                    except Exception as e:
                                        _logger.warning(f"Could not fetch variant image: {str(e)}")
                                
                                if var_img_id in downloaded_images:
                                    var_vals['image_1920'] = downloaded_images[var_img_id]

                            ov.write(var_vals)
                            
                            price_extra = var_price - list_price
                            if ov.product_template_attribute_value_ids:
                                ov.product_template_attribute_value_ids[0].write({'price_extra': price_extra})

                            break

            return request.make_response(
                json.dumps({'status': 'success', 'shopify_id': shopify_id}), 
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            _logger.error(f"Shopify Product Webhook Error: {str(e)}")
            return request.make_response(json.dumps({'error': 'Internal Server Error'}), status=500)