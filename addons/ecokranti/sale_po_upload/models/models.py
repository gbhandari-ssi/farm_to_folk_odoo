from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Tracking fields
    po_received = fields.Boolean(string="PO Received", default=False, copy=False)
    po_attachment_id = fields.Many2one('ir.attachment', string="PO Attachment", copy=False)

    def action_open_po_wizard(self):
        """Opens the pop-up wizard to upload the initial PO"""
        self.ensure_one()
        return {
            'name': 'Upload Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'upload.po.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id}
        }

    def action_view_po(self):
        """Action for the Smart Button to open a clean list of PO files"""
        self.ensure_one()
        list_view_id = self.env.ref('sale_po_upload.view_po_attachment_list').id
        
        return {
            'name': 'Purchase Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'views': [(list_view_id, 'list')],
            'domain': [('res_model', '=', 'sale.order'), ('res_id', '=', self.id)],
        }

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    # New computed field to tell the UI if the parent SO is invoiced
    is_sale_invoiced = fields.Boolean(compute="_compute_is_sale_invoiced")

    def _compute_is_sale_invoiced(self):
        for attachment in self:
            # Check if this attachment is specifically linked to a Sales Order
            if attachment.res_model == 'sale.order' and attachment.res_id:
                order = self.env['sale.order'].browse(attachment.res_id)
                # True if invoices exist, False if not
                attachment.is_sale_invoiced = order.invoice_count > 0
            else:
                attachment.is_sale_invoiced = False

    def action_replace_po_from_list(self):
        """Action for the Replace button inside the PO list view"""
        self.ensure_one()
        if self.res_model == 'sale.order':
            return {
                'name': 'Replace Purchase Order',
                'type': 'ir.actions.act_window',
                'res_model': 'upload.po.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_sale_order_id': self.res_id} 
            }

    def action_remove_po_from_list(self):
        """Action for the Remove button inside the PO list view"""
        self.ensure_one()
        if self.res_model == 'sale.order':
            order = self.env['sale.order'].browse(self.res_id)
            
            # Backend fallback protection
            if order.invoice_count > 0:
                raise UserError("You cannot remove a Purchase Order once an invoice has been created.")
            
            # Reset SO fields
            order.po_received = False
            order.po_attachment_id = False
            order.message_post(body="Purchase Order document was removed by user.")
            
            # Delete the file
            self.unlink()

            # Navigate the user back to the Sales Order
            return {
                'name': order.name,
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': order.id,
                'view_mode': 'form',
            }

class UploadPoWizard(models.TransientModel):
    _name = 'upload.po.wizard'
    _description = 'Upload Purchase Order Wizard'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    po_document = fields.Binary(string="PO Document", required=True)
    po_filename = fields.Char(string="Filename")

    def action_upload(self):
        """Saves the uploaded file, handles replacing old files, and updates the SO"""
        for wizard in self:
            if wizard.po_document:
                
                # If the user is REPLACING a PO, delete the old attachment first
                if wizard.sale_order_id.po_attachment_id:
                    wizard.sale_order_id.po_attachment_id.unlink()

                # Save the new attachment
                attachment = self.env['ir.attachment'].create({
                    'name': wizard.po_filename,
                    'type': 'binary',
                    'datas': wizard.po_document,
                    'res_model': 'sale.order',
                    'res_id': wizard.sale_order_id.id,
                })
                
                # Link the attachment and mark as received
                wizard.sale_order_id.po_attachment_id = attachment.id
                wizard.sale_order_id.po_received = True

                # Post a message in the chatter
                wizard.sale_order_id.message_post(
                    body="Purchase Order document successfully uploaded/updated.",
                    attachment_ids=[attachment.id]
                )