from odoo import api, fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    fsm_order_id = fields.Many2one("fsm.order", string="FSM Order", index=True)
    technician_id = fields.Many2one("res.users", string="Technician", index=True)

    @api.model
    def create_from_fsm_order(self, fsm_order, equipment, technician):
        vals = {
            "name": f"FSM {fsm_order.name} - {equipment.display_name}",
            "equipment_id": equipment.id,
            "user_id": technician.id,
            "technician_id": technician.id,
            "fsm_order_id": fsm_order.id,
            "maintenance_type": "corrective",
        }
        return self.create(vals)
