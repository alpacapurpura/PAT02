from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    fsm_order_ids = fields.Many2many('fsm.order', 'fsm_order_equipment_rel', 'equipment_id', 'order_id', string='FSM Orders (History)')
    maintenance_request_ids = fields.One2many('maintenance.request', 'equipment_id', string='Maintenance Requests')