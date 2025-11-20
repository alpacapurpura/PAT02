from odoo import models, fields, api
import base64
import zipfile
import io


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    x_knowledge_base = fields.Html(string='Knowledge Base')
    x_attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Attachments',
        domain=[('res_model', '=', 'maintenance.equipment.category')],
    )
    x_entry_checklist_template = fields.Html(string='Entry Checklist Template')
    x_exit_checklist_template = fields.Html(string='Exit Checklist Template')
    x_knowledge_base_count = fields.Integer(string='Knowledge Docs', compute='_compute_knowledge_base_count')
    x_inherit_checklists = fields.Boolean(string='Inherit Checklists', default=True)
    x_inherit_knowledge_base = fields.Boolean(string='Inherit Knowledge Base', default=True)
    x_effective_entry_checklist = fields.Html(string='Effective Entry Checklist', compute='_compute_effective_checklists', recursive=True)
    x_effective_exit_checklist = fields.Html(string='Effective Exit Checklist', compute='_compute_effective_checklists', recursive=True)
    x_inherited_knowledge_count = fields.Integer(string='Inherited Docs', compute='_compute_inherited_knowledge_count')
    x_effective_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Effective Documents',
        compute='_compute_effective_attachments'
    )

    @api.depends('x_attachment_ids')
    def _compute_knowledge_base_count(self):
        for record in self:
            record.x_knowledge_base_count = len(record.x_attachment_ids)

    @api.depends('x_entry_checklist_template', 'x_exit_checklist_template', 'parent_id.x_effective_entry_checklist', 'parent_id.x_effective_exit_checklist', 'x_inherit_checklists')
    def _compute_effective_checklists(self):
        for record in self:
            if record.x_inherit_checklists and record.parent_id:
                entry_sections = []
                exit_sections = []
                if record.x_entry_checklist_template:
                    entry_sections.append(record.x_entry_checklist_template)
                if record.x_exit_checklist_template:
                    exit_sections.append(record.x_exit_checklist_template)
                current = record.parent_id
                while current:
                    if current.x_effective_entry_checklist:
                        title = f"<h5>Checklist del {current.complete_name or current.name}</h5><hr/>"
                        entry_sections.append(title + current.x_effective_entry_checklist)
                    if current.x_effective_exit_checklist:
                        title = f"<h5>Checklist del {current.complete_name or current.name}</h5><hr/>"
                        exit_sections.append(title + current.x_effective_exit_checklist)
                    current = current.parent_id
                record.x_effective_entry_checklist = '\n'.join(entry_sections) if entry_sections else False
                record.x_effective_exit_checklist = '\n'.join(exit_sections) if exit_sections else False
            else:
                record.x_effective_entry_checklist = record.x_entry_checklist_template or False
                record.x_effective_exit_checklist = record.x_exit_checklist_template or False

    @api.depends('parent_id', 'x_inherit_knowledge_base')
    def _compute_inherited_knowledge_count(self):
        for record in self:
            inherited_count = 0
            if record.x_inherit_knowledge_base and record.parent_id:
                for parent in record._get_parent_categories():
                    inherited_count += len(parent.x_attachment_ids)
            record.x_inherited_knowledge_count = inherited_count

    def _get_parent_categories(self):
        parents = self.env['maintenance.equipment.category']
        current = self.parent_id
        while current:
            parents |= current
            current = current.parent_id
        return parents

    def _get_all_attachments(self):
        self.ensure_one()
        all_attachments = self.x_attachment_ids
        if self.x_inherit_knowledge_base and self.parent_id:
            for parent in self._get_parent_categories():
                all_attachments |= parent.x_attachment_ids
        return all_attachments

    def _compute_effective_attachments(self):
        for record in self:
            attachments = record._get_all_attachments() if (record.x_inherit_knowledge_base and record.parent_id) else record.x_attachment_ids
            record.x_effective_attachment_ids = attachments

    def action_view_knowledge_base(self):
        self.ensure_one()
        domain = [('res_model', '=', self._name), ('res_id', '=', self.id)]
        if self.x_inherit_knowledge_base and self.parent_id:
            parent_ids = self._get_parent_categories().ids + [self.id]
            domain = [('res_model', '=', self._name), ('res_id', 'in', parent_ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Knowledge Base',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
            'target': 'current',
        }

    def action_view_inherited_knowledge_base(self):
        self.ensure_one()
        if not self.x_inherit_knowledge_base or not self.parent_id:
            return {'type': 'ir.actions.act_window_close'}
        parent_categories = self._get_parent_categories()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inherited Knowledge',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [
                ('res_model', '=', self._name),
                ('res_id', 'in', parent_categories.ids),
            ],
            'context': {'create': False},
            'target': 'current',
        }

    def action_export_knowledge_base(self):
        self.ensure_one()
        all_attachments = self._get_all_attachments()
        if not all_attachments:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Documents',
                    'message': 'No documents to export for this category.',
                    'type': 'warning',
                    'sticky': False,
                },
            }
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for attachment in all_attachments:
                if attachment.datas:
                    folder = 'Own' if attachment.res_id == self.id else 'Inherited'
                    file_path = f"{folder}/{attachment.name}"
                    file_data = base64.b64decode(attachment.datas)
                    zip_file.writestr(file_path, file_data)
        zip_buffer.seek(0)
        zip_data = base64.b64encode(zip_buffer.getvalue()).decode()
        zip_name = f"Docs_{self.name.replace(' ', '_')}_{fields.Date.today().strftime('%Y%m%d')}.zip"
        zip_attachment = self.env['ir.attachment'].create({
            'name': zip_name,
            'type': 'binary',
            'raw': zip_data,
            'res_model': 'maintenance.equipment.category',
            'res_id': self.id,
            'mimetype': 'application/zip',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{zip_attachment.id}?download=true',
            'target': 'self',
        }