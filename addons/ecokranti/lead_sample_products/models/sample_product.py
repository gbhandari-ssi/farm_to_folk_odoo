from odoo import models, fields

class CrmSampleProductLine(models.Model):
    _name = 'crm.sample.product.line'
    _description = 'Sample Product Line'

    lead_id = fields.Many2one('crm.lead', string='Opportunity', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    is_provided = fields.Boolean(string='Provided', default=False)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sample_line_ids = fields.One2many(
        'crm.sample.product.line', 
        'lead_id', 
        string='Sample Products'
    )