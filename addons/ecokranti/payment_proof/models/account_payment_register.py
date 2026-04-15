from odoo import models, fields
from markupsafe import Markup  # Tells Odoo our HTML is safe

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    payment_proof = fields.Binary(string="Payment Proof")
    payment_proof_filename = fields.Char(string="Proof Filename")

    def _create_payments(self):
        # Let Odoo process the standard payment creation first
        payments = super(AccountPaymentRegister, self)._create_payments()

        # If the user uploaded a file, process the attachments
        if self.payment_proof:
            
            # 1. NEW: Force Odoo to finalize the "Paid" status tracking message first
            self.env.flush_all()

            for payment in payments:
                # Attach it directly to the Payment record
                attachment = self.env['ir.attachment'].create({
                    'name': self.payment_proof_filename or 'Payment_Proof',
                    'type': 'binary',
                    'datas': self.payment_proof,
                    'res_model': 'account.payment',
                    'res_id': payment.id,
                })
                # 2. NEW: Wrap the body in Markup() so the <b> tags render properly
                payment.message_post(
                    body=Markup("<b>Payment Proof Attached:</b> A document was uploaded to verify this transaction."), 
                    attachment_ids=[attachment.id]
                )

                # Mirror it to the related Invoices
                for move in self.line_ids.mapped('move_id'):
                    invoice_attachment = self.env['ir.attachment'].create({
                        'name': self.payment_proof_filename or 'Payment_Proof',
                        'type': 'binary',
                        'datas': self.payment_proof,
                        'res_model': 'account.move',
                        'res_id': move.id,
                    })
                    move.message_post(
                        body=Markup("<b>Payment Proof Attached:</b> A document was uploaded to verify this transaction."), 
                        attachment_ids=[invoice_attachment.id]
                    )

        return payments