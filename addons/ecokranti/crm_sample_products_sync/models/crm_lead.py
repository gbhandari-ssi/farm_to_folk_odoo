from odoo import models, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def write(self, vals):
        # 1. Let Odoo perform the standard database save first
        res = super(CrmLead, self).write(vals)

        # 2. Check if the 'type' field was just changed to 'opportunity' (Conversion)
        if vals.get('type') == 'opportunity':
            for lead in self:
                # 3. Safety Check: Ensure the custom fields exist in the database 
                # before trying to use them, preventing crashes if other modules are uninstalled.
                if 'interested_product_line_ids' in lead._fields and 'sample_line_ids' in lead._fields:
                    
                    # 4. Only proceed if there are actually products to copy
                    if lead.interested_product_line_ids:
                        
                        # Get IDs of products already in the Sample tab to prevent duplicates
                        existing_product_ids = lead.sample_line_ids.mapped('product_id.id')
                        new_sample_commands = []

                        # 5. Loop through interested products and prep the copy commands
                        for line in lead.interested_product_line_ids:
                            if line.product_id and line.product_id.id not in existing_product_ids:
                                # (0, 0, {values}) is the Odoo ORM command to create a new linked record
                                new_sample_commands.append((0, 0, {
                                    'product_id': line.product_id.id,
                                    'is_provided': False,
                                }))

                        # 6. Execute a single database write with all new lines at once (highly efficient)
                        if new_sample_commands:
                            lead.sample_line_ids = new_sample_commands

        return res