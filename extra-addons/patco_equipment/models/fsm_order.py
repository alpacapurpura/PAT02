from odoo import api, fields, models


class FsmOrder(models.Model):
    _inherit = "fsm.order"

    x_equipment_ids = fields.Many2many(
        "maintenance.equipment",
        "fsm_order_equipment_rel",
        "order_id",
        "equipment_id",
        string="Equipos",
        help="Equipos asociados a la orden"
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="location_id.owner_id",
        store=True,
        readonly=True,
    )
    x_equipment_code = fields.Char(compute="_compute_equipment_meta")
    x_equipment_count = fields.Integer(compute="_compute_equipment_meta")
    x_all_equipment_codes = fields.Char(compute="_compute_equipment_meta")
    x_equipment_categories = fields.Many2many(
        "maintenance.equipment.category",
        compute="_compute_equipment_categories",
        string="Equipment Categories",
    )

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def _compute_equipment_meta(self):
        for order in self:
            eqs = order.x_equipment_ids or self.env["maintenance.equipment"]
            order.x_equipment_count = len(eqs)
            order.x_equipment_code = eqs[:1].x_patco_code if eqs else ""
            order.x_all_equipment_codes = ", ".join(filter(None, eqs.mapped("x_patco_code")))

    def _compute_equipment_categories(self):
        for order in self:
            eqs = order.x_equipment_ids or self.env["maintenance.equipment"]
            order.x_equipment_categories = eqs.mapped("category_id")

    def action_view_all_equipment(self):
        self.ensure_one()
        eqs = self.x_equipment_ids
        customer_id = self.customer_id and self.customer_id.id
        return {
            "name": "Equipos de la Orden",
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "maintenance.equipment",
            "domain": customer_id and [("id", "in", eqs.ids), ("x_customer_id", "=", customer_id)] or [("id", "in", eqs.ids)],
            "target": "current",
        }