from odoo import models, fields, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_partner = fields.Selection([
        ('blue_dart', 'Blue Dart'),
        ('delhivery', 'Delhivery'),
        ('dtdc', 'DTDC'),
        ('fedex', 'FedEx')
    ], string='Delivery Partner')
    
    tracking_id = fields.Char(string='Tracking ID')
    tracking_link = fields.Char(string='Tracking Link')

    def button_validate(self):
        """ 1. The Gatekeeper: Blocks PICK validation if data is missing """
        for picking in self:
            if 'PICK' in picking.name:
                missing_errors = []

                if not picking.delivery_partner:
                    missing_errors.append("• Delivery Partner")

                if not picking.tracking_id and not picking.tracking_link:
                    missing_errors.append("• Tracking ID or Tracking Link")

                if missing_errors:
                    error_message = _("You cannot validate this transfer yet. Please provide the following mandatory courier details:\n\n%s") % "\n".join(missing_errors)
                    raise UserError(error_message)

        return super(StockPicking, self).button_validate()

    def _action_done(self):
        """ 2. The Data Pusher: Syncs data to OUT when PICK completes """
        
        # Let Odoo finish making the transfer 'Done' (and generate any backorders)
        res = super(StockPicking, self)._action_done()

        for picking in self:
            # When a PICK is successfully marked as Done...
            if 'PICK' in picking.name:
                
                # Find the downstream OUT transfers linked to this PICK
                dest_moves = picking.move_ids.mapped('move_dest_ids')
                dest_pickings = dest_moves.mapped('picking_id')
                
                for dp in dest_pickings:
                    if 'OUT' in dp.name:
                        
                        # Use your brilliant backorder climbing logic!
                        current_pick = picking
                        while current_pick and not current_pick.delivery_partner:
                            if current_pick.backorder_id:
                                current_pick = current_pick.backorder_id
                            else:
                                break
                                
                        # Directly push the data into the waiting OUT transfer
                        if current_pick and current_pick.delivery_partner:
                            dp.delivery_partner = current_pick.delivery_partner
                            dp.tracking_id = current_pick.tracking_id
                            dp.tracking_link = current_pick.tracking_link

        return res