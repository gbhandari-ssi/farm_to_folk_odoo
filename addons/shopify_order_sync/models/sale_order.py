from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shopify_order_id = fields.Char(
        string='Shopify Order ID', 
        copy=False, 
        index=True,
        help="Unique identifier from Shopify to prevent duplicate orders."
    )

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    shopify_line_id = fields.Char(
        string='Shopify Line ID', 
        copy=False, 
        index=True
    )