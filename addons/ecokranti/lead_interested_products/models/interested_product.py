from odoo import models, fields

class CrmInterestedProductLine(models.Model):
    _name = 'crm.interested.product.line'
    _description = 'Interested Product Line'

    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Char(string='Quantity')

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    interested_product_line_ids = fields.One2many(
        'crm.interested.product.line', 
        'lead_id', 
        string='Interested Products'
    )