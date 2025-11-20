from odoo import models
import logging
import re
import json

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def message_post(self, **kwargs):
        msg = super().message_post(**kwargs)
        # try:
        #     ctx = self.env.context or {}
        #     if not ctx.get('ai_handler_invoked'):
        #         self.env['patco.ai.processor'].with_context(ai_handler_invoked=True).process(msg)
        # except Exception:
        #     _logger.exception('patco_ai: error in message_post discuss.channel')
        return msg


# removed inheritance of mail.channel (not present in Odoo 18)
