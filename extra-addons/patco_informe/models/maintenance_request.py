from odoo import api, fields, models
from odoo.exceptions import UserError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    report_started = fields.Boolean(string='Report Started', default=False)
    report_start_datetime = fields.Datetime(string='Report Start')
    report_end_datetime = fields.Datetime(string='Report End')
    report_duration_hours = fields.Float(string='Report Duration (h)', compute='_compute_report_duration', store=True)
    report_notes = fields.Text(string='Service Notes')
    include_checklists = fields.Boolean(string='Incluir Checklists utilizados')

    report_image_ids = fields.One2many('maintenance.request.image', 'request_id', string='Service Photos')

    informe_count = fields.Integer(string='Reports', compute='_compute_informe_count', store=False)

    eq_location = fields.Char(string='Location', related='equipment_id.location', readonly=True)
    eq_technician_user_id = fields.Many2one('res.users', string='Equipment Technician', related='equipment_id.technician_id', readonly=True)

    @api.depends('report_start_datetime', 'report_end_datetime')
    def _compute_report_duration(self):
        for rec in self:
            if rec.report_start_datetime and rec.report_end_datetime and rec.report_end_datetime >= rec.report_start_datetime:
                delta = rec.report_end_datetime - rec.report_start_datetime
                rec.report_duration_hours = delta.total_seconds() / 3600.0
            else:
                rec.report_duration_hours = 0.0

    def _compute_informe_count(self):
        for rec in self:
            rec.informe_count = 1 if rec.report_started or rec.report_notes or rec.report_image_ids else 0

    def action_start_report(self):
        for rec in self:
            if not rec.report_started:
                rec.report_started = True
                rec.report_start_datetime = fields.Datetime.now()

    def action_finish_report(self):
        for rec in self:
            if rec.report_started and not rec.report_end_datetime:
                if not rec.report_notes and not rec.report_image_ids:
                    raise UserError('Para finalizar el reporte, agrega notas o al menos una foto.')
                rec.report_end_datetime = fields.Datetime.now()

    def action_add_photo(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agregar foto',
            'res_model': 'maintenance.request.image',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
            },
        }

    def action_export_informe(self):
        self.ensure_one()
        return self.env.ref('patco_informe.action_report_maintenance_request_informe').report_action(self, config=False)


class MaintenanceRequestImage(models.Model):
    _name = 'maintenance.request.image'
    _description = 'Maintenance Request Photo'

    request_id = fields.Many2one('maintenance.request', string='Request', required=True, ondelete='cascade', index=True)
    description = fields.Char(string='Description')
    image = fields.Image(string='Image', max_width=1920, max_height=1920, attachment=True, required=True)
    image_256 = fields.Image(related='image', string='Image 256', max_width=256, max_height=256, store=True)

    def action_open_image_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tomar/Agregar foto',
            'res_model': 'maintenance.request.image',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }