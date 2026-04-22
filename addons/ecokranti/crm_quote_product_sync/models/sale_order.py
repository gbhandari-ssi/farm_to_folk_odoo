from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('opportunity_id')
    def _onchange_opportunity_id_sync_products(self):
        """
        Dynamically pull 'Interested Products' into the order lines
        when a user selects an Opportunity, syncing ONLY the products.
        """
        # 1. Check if an opportunity was selected and if our custom field exists
        if self.opportunity_id and 'interested_product_line_ids' in self.opportunity_id._fields:
            
            # 2. Only proceed if the lead has interested products listed
            if self.opportunity_id.interested_product_line_ids:
                
                # 3. Clear existing order lines to prevent duplicates
                commands = [(5, 0, 0)]
                
                # 4. Loop through the CRM lines and build the new Quotation lines
                for line in self.opportunity_id.interested_product_line_ids:
                    if line.product_id:
                        # Notice we completely removed the quantity line here!
                        commands.append((0, 0, {
                            'product_id': line.product_id.id,
                        }))
                
                # 5. Apply the commands to the active screen
                self.order_line = commands