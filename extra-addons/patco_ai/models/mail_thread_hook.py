from odoo import models


class MailThreadHook(models.AbstractModel):
    _inherit = 'mail.thread'

    def message_post(self, **kwargs):
        msg = super().message_post(**kwargs)
        # try:
        #     if self._name in ('discuss.channel', 'mail.channel') and msg:
        #         ctx = self.env.context or {}
        #         if not ctx.get('ai_handler_invoked'):
        #             self.env['patco.ai.processor'].with_context(ai_handler_invoked=True).process(msg)
        # except Exception:
        #     pass
        return msg