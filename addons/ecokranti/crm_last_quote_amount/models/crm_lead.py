from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    last_quote_amount = fields.Monetary(
        string='Last Quote Amount',
        compute='_compute_last_quote_amount',
        currency_field='company_currency',
        store=True # Allows you to group, sort, and filter by this amount in list views!
    )

    @api.depends('order_ids', 'order_ids.amount_total')
    def _compute_last_quote_amount(self):
        for lead in self:
            if lead.order_ids:
                # Sort the linked orders by ID descending (highest ID is the newest)
                latest_quote = lead.order_ids.sorted(key=lambda q: q.id, reverse=True)[0]
                lead.last_quote_amount = latest_quote.amount_total
            else:
                lead.last_quote_amount = 0.0