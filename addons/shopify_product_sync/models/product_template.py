from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopify_product_id = fields.Char(string='Shopify Product ID', copy=False, index=True)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    shopify_variant_id = fields.Char(string='Shopify Variant ID', copy=False, index=True)