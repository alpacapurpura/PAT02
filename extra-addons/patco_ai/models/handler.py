from odoo import models
import logging
import re
import json

_logger = logging.getLogger(__name__)


class PatcoAIHandler(models.AbstractModel):
    _name = 'patco.ai.handler'
    _description = 'PATCO AI Chat Handler'

    def handle(self, msg):
        try:
            body = msg.body or ''
            _logger.info('patco_ai: [STEP1 entry] msg_id=%s model=%s res_id=%s body="%s"', msg.id, msg.model, msg.res_id, body[:200])
            channel = False
            if not msg.model or not msg.res_id:
                ch = False
                try:
                    if hasattr(msg, 'channel_ids') and msg.channel_ids:
                        ch = msg.channel_ids[0]
                except Exception:
                    ch = False
                if not ch:
                    _logger.info('patco_ai: [STEP1 entry] skip: missing model/res_id')
                    return
                channel = ch
            else:
                channel = self.env[msg.model].browse(msg.res_id)
            icp = self.env['ir.config_parameter'].sudo()
            pid = icp.get_param('ai.bot_partner_id')
            bot_partner = False
            if pid:
                try:
                    bot_partner = self.env['res.partner'].browse(int(pid))
                except Exception:
                    bot_partner = False
            if not bot_partner or not bot_partner.exists():
                bot_user = self.env['res.users'].sudo().search([('login', '=', 'odoo_bot')], limit=1)
                if not bot_user:
                    bot_user = self.env['res.users'].sudo().search([('login', 'in', ['odoobot', 'odoo.bot'])], limit=1)
                bot_partner = bot_user.partner_id if bot_user else False
                if bot_partner:
                    icp.set_param('ai.bot_partner_id', str(bot_partner.id))
            if not bot_partner:
                _logger.info('patco_ai: [STEP2 bot] no bot partner; abort')
                return
            if msg.author_id and msg.author_id.id == bot_partner.id:
                _logger.info('patco_ai: [STEP2 bot] author is bot; skip')
                return
            partners = False
            if hasattr(channel, 'channel_partner_ids'):
                partners = channel.channel_partner_ids
            elif hasattr(channel, 'partner_ids'):
                partners = channel.partner_ids
            elif hasattr(channel, 'member_ids'):
                partners = channel.member_ids.mapped('partner_id')
            partners = partners or self.env['res.partner']
            if bot_partner not in partners:
                try:
                    channel.sudo().add_members(bot_partner)
                    _logger.info('patco_ai: [STEP2 bot] added bot to channel=%s', channel.id)
                except Exception:
                    _logger.info('patco_ai: [STEP2 bot] could not add bot to channel=%s', channel.id)
            ctype = getattr(channel, 'channel_type', '') or getattr(channel, 'channel_type_name', '')
            is_dm = (ctype in ('chat', 'direct', 'direct_message', 'private')) or (len(partners) and len(partners) <= 2)
            _logger.info('patco_ai: [STEP3 context] channel=%s type=%s members=%s author_partner=%s', channel.id, ctype, len(partners), msg.author_id.id if msg.author_id else None)
            mentioned = False
            for m in re.findall(r'data-oe-id="(\d+)"', body):
                try:
                    if int(m) == bot_partner.id:
                        mentioned = True
                        break
                except Exception:
                    pass
            aliases = (icp.get_param('ai.bot_aliases') or '').lower().split(',')
            bl = body.lower()
            for a in aliases:
                a = a.strip()
                if a and f'@{a}' in bl:
                    mentioned = True
                    break
            _logger.info('patco_ai: [STEP4 mention] is_dm=%s mentioned=%s', is_dm, mentioned)
            require_mention = (icp.get_param('ai.bot_require_mention') or '').lower() in ('1', 'true', 'yes')
            if not is_dm and require_mention and not mentioned:
                _logger.info('patco_ai: [STEP4 mention] group message without mention; require_mention=True -> skip')
                return
            author_user = False
            if msg.author_id and msg.author_id.user_ids:
                author_user = msg.author_id.user_ids[0]
            if not author_user and msg.author_id:
                author_user = self.env['res.users'].sudo().search([('partner_id', '=', msg.author_id.id)], limit=1)
            if not author_user:
                author_user = self.env.user
            _logger.info('patco_ai: [STEP5 author] author_user=%s', author_user.id if author_user else None)
            if not author_user:
                _logger.info('patco_ai: [courtesy] posting courtesy (no author) body="%s"', body[:200])
                channel.sudo().with_context(ai_handler_invoked=True).message_post(
                    body="Hola! No tienes ninguna orden de mantenimiento activa en estos momentos =(. Soy tu asistente técnico, cuando tengas una orden de mantenimiento, ahí estaré!",
                    author_id=bot_partner.id,
                    message_type='comment',
                    subtype_id=self.env.ref('mail.mt_comment').id,
                )
                return
            requests = self.env['maintenance.request'].search([('user_id', '=', author_user.id), ('done', '=', False)])
            _logger.info('patco_ai: [STEP7 requests] active_requests=%s', len(requests))
            if not requests:
                _logger.info('patco_ai: [courtesy] posting courtesy (no active requests)')
                channel.sudo().with_context(ai_handler_invoked=True).message_post(
                    body="Hola! No tienes ninguna orden de mantenimiento activa en estos momentos =(. Soy tu asistente técnico, cuando tengas una orden de mantenimiento, ahí estaré!",
                    author_id=bot_partner.id,
                    message_type='comment',
                    subtype_id=self.env.ref('mail.mt_comment').id,
                )
                return
            cats = requests.mapped('equipment_id.category_id')
            _logger.info('patco_ai: [STEP9 categories] categories=%s', cats.ids)
            payload = {
                'user_id': author_user.id,
                'question': body,
                'category_ids': cats.ids,
                'include_checklists': True,
            }
            resp = self.env['patco.ai.client'].rag_query(json.dumps(payload))
            try:
                text = resp.decode('utf-8') if isinstance(resp, (bytes, bytearray)) else str(resp)
            except Exception:
                text = ''
            _logger.info('patco_ai: [STEP10 rag] rag_response_len=%s', len(text or ''))
            if not text:
                _logger.info('patco_ai: [courtesy] empty rag response -> courtesy')
                channel.sudo().with_context(ai_handler_invoked=True).message_post(
                    body="Hola! No tienes ninguna orden de mantenimiento activa en estos momentos =(. Soy tu asistente técnico, cuando tengas una orden de mantenimiento, ahí estaré!",
                    author_id=bot_partner.id,
                    message_type='comment',
                    subtype_id=self.env.ref('mail.mt_comment').id,
                )
                return
            channel.sudo().with_context(ai_handler_invoked=True).message_post(
                body=text,
                author_id=bot_partner.id,
                message_type='comment',
                subtype_id=self.env.ref('mail.mt_comment').id,
            )
        except Exception:
            _logger.exception('patco_ai: handler exception')