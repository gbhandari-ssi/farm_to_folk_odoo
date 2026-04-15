from odoo import models, fields

class InterestedProductLine(models.Model):
    _name = 'interested.product.line'
    _description = 'Interested Product Line'

    # Reference back to the lead
    lead_id = fields.Many2one('crm.lead', string='Lead Reference', ondelete='cascade')
    
    # Custom fields 
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Name')
    quantity = fields.Char(string='Quantity') 

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # The One2many field that connects the lead to the product lines
    interested_line_ids = fields.One2many(
        'interested.product.line', 
        'lead_id', 
        string='Interested Products'
    )