from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AssignEquipmentWizard(models.TransientModel):
    _name = "assign.equipment.wizard"
    _description = "Assign Equipment to FSM Order"

    fsm_order_id = fields.Many2one("fsm.order", required=True)
    customer_id = fields.Many2one(
        "res.partner",
        related="fsm_order_id.customer_id",
        readonly=True,
    )
    location_id = fields.Many2one(
        "fsm.location",
        related="fsm_order_id.location_id",
        readonly=True,
    )
    request_early = fields.Datetime(
        related="fsm_order_id.request_early",
        readonly=True,
    )

    equipment_id = fields.Many2one(
        "maintenance.equipment",
        required=True,
    )
    technician_id = fields.Many2one(
        "res.users",
        required=True,
        domain=[("share", "=", False)],
        default=lambda self: self.env.user,
    )
    maintenance_type = fields.Selection(
        selection=[
            ("preventive", "Preventivo"),
            ("corrective", "Correctivo"),
        ],
        default="corrective",
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if active_id:
            res["fsm_order_id"] = active_id
        return res

    def action_assign(self):
        self.ensure_one()
        order = self.fsm_order_id
        if not (order.customer_id and order.location_id and order.request_early):
            raise ValidationError(
                "Complete los campos obligatorios de la orden (Cliente, Ubicación y Fecha)."
            )
        if not self.equipment_id:
            raise ValidationError("Debe seleccionar un equipo")
        if not self.technician_id:
            raise ValidationError("Debe seleccionar un técnico")

        if order.customer_id and self.equipment_id.x_customer_id != order.customer_id:
            raise ValidationError("El equipo seleccionado no pertenece al cliente de la orden")

        if self.equipment_id not in order.x_equipment_ids:
            order.x_equipment_ids = [(4, self.equipment_id.id)]

        maintenance_vals = {
            "name": f"FSM {order.name} - {self.equipment_id.display_name}",
            "equipment_id": self.equipment_id.id,
            "user_id": self.technician_id.id,
            "technician_id": self.technician_id.id,
            "fsm_order_id": order.id,
            "maintenance_type": self.maintenance_type,
            "request_date": order.request_early,
        }
        self.env["maintenance.request"].create(maintenance_vals)
        return {"type": "ir.actions.act_window_close"}