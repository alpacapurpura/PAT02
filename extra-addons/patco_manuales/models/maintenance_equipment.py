from odoo import models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    def action_open_category_knowledge(self):
        self.ensure_one()
        if not self.category_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Category',
                    'message': 'Select a category to open its documentation.',
                    'type': 'warning',
                }
            }
        return self.category_id.action_view_knowledge_base()