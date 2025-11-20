from odoo import api, fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    fsm_order_id = fields.Many2one("fsm.order", string="Orden FSM", index=True)
    technician_id = fields.Many2one("res.users", string="Técnico", index=True)
    qr_code = fields.Binary(string="Código QR", related="equipment_id.x_qr_code", readonly=True)
    qr_url = fields.Char(string="URL del QR", related="equipment_id.x_qr_url", readonly=True)
    eq_model = fields.Char(string="Modelo", related="equipment_id.model", readonly=True)
    eq_brand = fields.Char(string="Marca", related="equipment_id.x_brand", readonly=True)
    eq_serial_no = fields.Char(string="Número de serie", related="equipment_id.serial_no", readonly=True)
    eq_customer_id = fields.Many2one(string="Cliente", comodel_name="res.partner", related="equipment_id.x_customer_id", readonly=True)
    eq_service_location_id = fields.Many2one(string="Ubicación", comodel_name="res.partner", related="equipment_id.x_service_location_id", readonly=True)

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
