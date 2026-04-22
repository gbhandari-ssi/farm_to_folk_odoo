from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        # 1. Let Odoo do its normal job first (confirming the quote, locking it, etc.)
        res = super(SaleOrder, self).action_confirm()

        # 2. Loop through the orders being confirmed
        for order in self:
            # 3. Check if this specific order is linked to a CRM opportunity
            if order.opportunity_id:
                # 4. Trigger the standard 'Won' action on that specific opportunity
                order.opportunity_id.action_set_won()

        # 5. Return the result so the UI continues loading smoothly
        return res