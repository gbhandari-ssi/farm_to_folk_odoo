from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sample_delivery_partner = fields.Selection([
        ('blue_dart', 'Blue Dart'),
        ('delhivery', 'Delhivery'),
        ('dtdc', 'DTDC'),
        ('fedex', 'FedEx')
    ], string='Delivery Partner')
    
    tracking_id = fields.Char(string='Tracking ID')
    tracking_link = fields.Char(string='Tracking Link')
    
    sample_sent_date = fields.Datetime(string='Sample Sent')
    sample_delivered_date = fields.Datetime(string='Sample Delivered')
    
    sample_approved = fields.Boolean(string='Sample Approved')