from odoo import models, fields, api


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    x_history_request_ids = fields.One2many(
        'maintenance.request',
        'equipment_id',
        string='History Requests',
        compute='_compute_history_request_ids',
        readonly=True
    )
    x_req_entry_checklist = fields.Html(string='Entry Checklist', related='equipment_id.category_id.x_effective_entry_checklist', readonly=True)
    x_req_exit_checklist = fields.Html(string='Exit Checklist', related='equipment_id.category_id.x_effective_exit_checklist', readonly=True)
    x_req_attachment_ids = fields.Many2many('ir.attachment', string='Effective Documents', compute='_compute_req_attachments', readonly=True)

    def _compute_history_request_ids(self):
        for record in self:
            if record.equipment_id:
                record.x_history_request_ids = self.env['maintenance.request'].search([
                    ('equipment_id', '=', record.equipment_id.id)
                ])
            else:
                record.x_history_request_ids = self.env['maintenance.request']

    def _compute_req_attachments(self):
        for record in self:
            attachments = self.env['ir.attachment']
            if record.equipment_id and record.equipment_id.category_id:
                attachments = record.equipment_id.category_id.x_effective_attachment_ids
            record.x_req_attachment_ids = attachments