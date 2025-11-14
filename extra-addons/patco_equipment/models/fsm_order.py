from odoo import api, fields, models


class FsmOrder(models.Model):
    _inherit = "fsm.order"

    x_equipment_id = fields.Many2one(
        "maintenance.equipment", string="Equipment"
    )
    x_equipment_ids = fields.Many2many(
        "maintenance.equipment",
        "fsm_order_equipment_rel",
        "order_id",
        "equipment_id",
        string="Equipments",
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
        orders = super().create(vals_list)
        for order in orders:
            equipments = order.equipment_ids or (order.equipment_id and order.equipment_id) or self.env["maintenance.equipment"]
            # include custom links if provided
            if order.x_equipment_id:
                equipments |= order.x_equipment_id
            if order.x_equipment_ids:
                equipments |= order.x_equipment_ids
            if equipments and hasattr(equipments, "ids"):
                assigned = order.person_id and order.person_id.partner_id and order.person_id.partner_id.user_ids and order.person_id.partner_id.user_ids[:1]
                assigned_user = assigned and assigned[0] or self.env.user
                for eq in equipments:
                    self.env["maintenance.request"].create_from_fsm_order(order, eq, assigned_user)
        return orders

    def _compute_equipment_meta(self):
        for order in self:
            eqs = order.equipment_ids or self.env["maintenance.equipment"]
            if order.equipment_id:
                eqs |= order.equipment_id
            if order.x_equipment_id:
                eqs |= order.x_equipment_id
            if order.x_equipment_ids:
                eqs |= order.x_equipment_ids
            order.x_equipment_count = len(eqs)
            order.x_equipment_code = order.x_equipment_id and order.x_equipment_id.x_patco_code or ""
            order.x_all_equipment_codes = ", ".join(filter(None, eqs.mapped("x_patco_code")))

    def _compute_equipment_categories(self):
        for order in self:
            eqs = order.equipment_ids or self.env["maintenance.equipment"]
            if order.equipment_id:
                eqs |= order.equipment_id
            if order.x_equipment_id:
                eqs |= order.x_equipment_id
            if order.x_equipment_ids:
                eqs |= order.x_equipment_ids
            order.x_equipment_categories = eqs.mapped("category_id")

    def action_view_all_equipment(self):
        self.ensure_one()
        eqs = self.x_equipment_ids
        if self.x_equipment_id:
            eqs |= self.x_equipment_id
        if self.equipment_id:
            eqs |= self.equipment_id
        if self.equipment_ids:
            eqs |= self.equipment_ids
        return {
            "name": "Equipos de la Orden",
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "maintenance.equipment",
            "domain": [("id", "in", eqs.ids)],
            "target": "current",
        }