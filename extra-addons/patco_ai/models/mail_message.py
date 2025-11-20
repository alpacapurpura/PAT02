from odoo import api, models
import logging
import json

_logger = logging.getLogger(__name__)

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for msg in records:
            try:
                _logger.info('patco_ai: incoming message id=%s model=%s res_id=%s author=%s', msg.id, msg.model, msg.res_id, msg.author_id.id if msg.author_id else None)
                ctx = self.env.context or {}
                if not ctx.get('ai_handler_invoked'):
                    if msg.model in ('discuss.channel', 'mail.channel') and msg.res_id:
                        self.env['patco.ai.processor'].with_context(ai_handler_invoked=True).process(msg)
                    elif not msg.model:
                        try:
                            self.env['patco.ai.processor'].with_context(ai_handler_invoked=True).process(msg)
                        except Exception:
                            _logger.exception('patco_ai: processor failed for bare message; ignore')
            except Exception:
                # Fallback visible para el usuario
                try:
                    ch = False
                    if msg.model == 'discuss.channel' and msg.res_id:
                        ch = self.env['discuss.channel'].browse(msg.res_id)
                    elif hasattr(msg, 'channel_ids') and msg.channel_ids:
                        ch = msg.channel_ids[0]
                    icp = self.env['ir.config_parameter'].sudo()
                    pid = icp.get_param('ai.bot_partner_id')
                    bot_partner = self.env['res.partner'].browse(int(pid)) if pid else False
                    if ch and bot_partner:
                        ch.sudo().with_context(ai_handler_invoked=True).message_post(
                            body="⚠️ No pude procesar tu mensaje por un error interno. Intenta nuevamente o contacta soporte.",
                            author_id=bot_partner.id,
                            message_type='comment',
                            subtype_id=self.env.ref('mail.mt_comment').id,
                        )
                except Exception:
                    pass
        return records

    def _mentioned_bot(self, text, bot_partner):
        import re
        t = (text or '')
        # data-oe-id detection
        for m in re.findall(r'data-oe-id="(\d+)"', t):
            try:
                if int(m) == bot_partner.id:
                    return True
            except Exception:
                pass
        # optional aliases
        aliases = (self.env['ir.config_parameter'].sudo().get_param('ai.bot_aliases') or '').lower().split(',')
        msg_l = t.lower()
        for a in aliases:
            a = a.strip()
            if a and f'@{a}' in msg_l:
                return True
        return False

    def _find_bot_partner(self, channel):
        # If the channel already contains a bot partner, prefer it
        for p in channel.channel_partner_ids:
            name = (p.name or '').lower()
            if name.startswith('odoo bot') or name == 'odoobot':
                return p
        # Prefer our custom bot user
        bot_user = self.env['res.users'].sudo().search([('login', '=', 'odoo_bot')], limit=1)
        if bot_user:
            return bot_user.partner_id
        # Fallback: built-in OdooBot
        bot_user2 = self.env['res.users'].sudo().search([('login', 'in', ['odoobot', 'odoo.bot'])], limit=1)
        if bot_user2:
            return bot_user2.partner_id
        bot_partner = self.env['res.partner'].sudo().search([('name', 'ilike', 'OdooBot')], limit=1)
        if bot_partner:
            return bot_partner
        bot_partner2 = self.env['res.partner'].sudo().search([('name', 'ilike', 'Odoo Bot')], limit=1)
        return bot_partner2

    def _handle_bot_reply(self, msg):
        try:
            return self.env['patco.ai.handler'].handle(msg)
        except Exception:
            _logger.exception('patco_ai: error delegating to handler from _handle_bot_reply')