from odoo import models, fields


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    inline_url = fields.Char(compute='_compute_inline_url', string='Inline URL', store=False)
    inline_supported = fields.Boolean(compute='_compute_inline_supported', string='Inline Supported', store=False)

    def _compute_inline_url(self):
        for att in self:
            url = False
            if att.type == 'binary':
                url = f"/web/content/{att.id}?download=false"
            att.inline_url = url

    def _compute_inline_supported(self):
        supported_images = {
            'image/png', 'image/jpeg', 'image/jpg', 'image/webp',
            'image/gif', 'image/bmp', 'image/tiff', 'image/svg+xml'
        }
        for att in self:
            att.inline_supported = bool(
                att.type == 'binary' and (
                    att.mimetype == 'application/pdf' or (att.mimetype in supported_images)
                )
            )

    def action_open_inline_url(self):
        self.ensure_one()
        url = f"/web/content/{self.id}?download=false"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }