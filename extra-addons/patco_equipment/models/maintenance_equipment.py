import base64
import io
import qrcode
from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    x_patco_code = fields.Char(string='PATCO Code', copy=False, readonly=True, default='New', tracking=True)
    x_customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    x_service_location_id = fields.Many2one('res.partner', string='Service Location', tracking=True)
    x_qr_code = fields.Binary(string='QR Code', readonly=True)
    x_qr_url = fields.Char(string='QR URL', readonly=True)

    x_service_order_ids = fields.One2many('fsm.order', 'x_equipment_id', string='Service Orders')
    x_fsm_order_count = fields.Integer(string='FSM Orders', compute='_compute_fsm_order_count', store=True)
    technician_ids = fields.Many2many('res.users', 'maintenance_equipment_res_users_rel', 'equipment_id', 'user_id', string='Technicians')
    technician_id = fields.Many2one('res.users', string='Primary Technician')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('x_patco_code', 'New') == 'New':
                vals['x_patco_code'] = self.env['ir.sequence'].next_by_code('maintenance.equipment.patco') or 'New'
        records = super().create(vals_list)
        records._generate_qr_code()
        return records

    def write(self, vals):
        result = super().write(vals)
        qr_fields = ['name', 'x_patco_code', 'x_customer_id', 'x_service_location_id']
        if any(field in vals for field in qr_fields):
            self._generate_qr_code()
        return result

    def _generate_qr_code(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            equipment_url = f"{base_url}/web#id={record.id}&model=maintenance.equipment&view_type=form"
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(equipment_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_image = base64.b64encode(buffer.getvalue())
            record.sudo().write({'x_qr_code': qr_image, 'x_qr_url': equipment_url})

    @api.depends('x_service_order_ids')
    def _compute_fsm_order_count(self):
        for record in self:
            record.x_fsm_order_count = len(record.x_service_order_ids)

    def action_view_fsm_orders(self):
        self.ensure_one()
        return {
            'name': 'FSM Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'fsm.order',
            'domain': [('id', 'in', self.x_service_order_ids.ids)],
            'context': {'default_x_equipment_id': self.id},
        }