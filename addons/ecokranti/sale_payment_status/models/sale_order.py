from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_status = fields.Char(
        string='Payment Status',
        compute='_compute_payment_status',
        store=True
    )

    # Added 'invoice_status' to the dependencies so it updates dynamically
    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.payment_state', 'invoice_status')
    def _compute_payment_status(self):
        for order in self:
            # 1. Look at all active invoices
            invoices = order.invoice_ids.filtered(lambda inv: inv.state != 'cancel')
            
            if not invoices:
                order.payment_status = 'No Invoice'
            else:
                states = [inv.payment_state for inv in invoices]
                
                # 2. Check if literally nothing has been paid yet
                if all(s in ('not_paid', 'posted', 'draft') for s in states):
                    order.payment_status = 'Not Paid'
                
                # 3. Check if all EXISTING invoices are paid
                elif all(s in ('paid', 'in_payment', 'reversed') for s in states):
                    
                    # THE FIX: Are all existing invoices paid, AND is the whole order invoiced?
                    if order.invoice_status == 'invoiced':
                        order.payment_status = 'Fully Paid'
                    else:
                        # Down payment scenario: The existing invoice is paid, but more invoices are coming!
                        order.payment_status = 'Partially Paid'
                        
                # 4. A mix of paid and unpaid invoices
                else:
                    order.payment_status = 'Partially Paid'