from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    shopify_customer_id = fields.Char(
        string='Shopify Customer ID', 
        copy=False, 
        index=True,
        help="Unique identifier from Shopify to prevent duplicate contacts."
    )