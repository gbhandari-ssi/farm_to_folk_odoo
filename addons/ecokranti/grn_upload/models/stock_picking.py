from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Tracking fields
    grn_received = fields.Boolean(string="GRN Received", default=False, copy=False)
    grn_attachment_id = fields.Many2one('ir.attachment', string="GRN Attachment", copy=False)

    def action_open_grn_wizard(self):
        """Opens the pop-up wizard to upload the GRN"""
        self.ensure_one()
        return {
            'name': 'Upload GRN',
            'type': 'ir.actions.act_window',
            'res_model': 'upload.grn.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_picking_id': self.id}
        }

    def action_view_grn(self):
        """Action for the Smart Button to open the GRN file list"""
        self.ensure_one()
        # Make sure the module name here matches your actual module name
        list_view_id = self.env.ref('grn_upload.view_grn_attachment_list').id
        
        return {
            'name': 'GRN Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'views': [(list_view_id, 'list')],
            # UPDATE: Filter to show ONLY the specific GRN attachment
            'domain': [('id', '=', self.grn_attachment_id.id)],
        }

    def button_validate(self):
        """Override to block validation if GRN is missing on outgoing transfers"""
        for picking in self:
            if picking.picking_type_id.code == 'outgoing' and not picking.grn_received:
                raise UserError(_("You must upload the GRN document before validating this delivery."))
        return super(StockPicking, self).button_validate()


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    # Determine if the delivery is locked (done) to prevent deleting the GRN
    is_picking_done = fields.Boolean(compute="_compute_is_picking_done")

    def _compute_is_picking_done(self):
        for attachment in self:
            if attachment.res_model == 'stock.picking' and attachment.res_id:
                picking = self.env['stock.picking'].browse(attachment.res_id)
                attachment.is_picking_done = picking.state == 'done'
            else:
                attachment.is_picking_done = False

    def action_replace_grn_from_list(self):
        """Action for the Replace button inside the GRN list view"""
        self.ensure_one()
        if self.res_model == 'stock.picking':
            return {
                'name': 'Replace GRN Document',
                'type': 'ir.actions.act_window',
                'res_model': 'upload.grn.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_picking_id': self.res_id} 
            }

    def action_remove_grn_from_list(self):
        """Action for the Remove button inside the GRN list view"""
        self.ensure_one()
        if self.res_model == 'stock.picking':
            picking = self.env['stock.picking'].browse(self.res_id)
            
            # Backend fallback protection
            if picking.state == 'done':
                raise UserError(_("You cannot remove a GRN once the delivery is validated."))
            
            # Reset Picking fields
            picking.grn_received = False
            picking.grn_attachment_id = False
            picking.message_post(body="GRN document was removed by user.")
            
            # Delete the file
            self.unlink()

            # Return to the Delivery Order
            return {
                'name': picking.name,
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'view_mode': 'form',
            }


class UploadGrnWizard(models.TransientModel):
    _name = 'upload.grn.wizard'
    _description = 'Upload GRN Wizard'

    picking_id = fields.Many2one('stock.picking', string="Transfer")
    grn_document = fields.Binary(string="GRN Document", required=True)
    grn_filename = fields.Char(string="Filename")

    def action_upload(self):
        """Saves the uploaded file, handles replacing old files, and updates the picking"""
        for wizard in self:
            if wizard.grn_document:
                
                # If replacing, delete the old attachment first
                if wizard.picking_id.grn_attachment_id:
                    wizard.picking_id.grn_attachment_id.unlink()

                # Save the new attachment
                attachment = self.env['ir.attachment'].create({
                    'name': wizard.grn_filename,
                    'type': 'binary',
                    'datas': wizard.grn_document,
                    'res_model': 'stock.picking',
                    'res_id': wizard.picking_id.id,
                })
                
                # Link and mark as received
                wizard.picking_id.grn_attachment_id = attachment.id
                wizard.picking_id.grn_received = True

                wizard.picking_id.message_post(
                    body="GRN document successfully uploaded/updated.",
                    attachment_ids=[attachment.id]
                )