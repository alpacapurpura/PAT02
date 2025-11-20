from odoo import models
import logging
import json

_logger = logging.getLogger(__name__)


class PatcoAIProcessor(models.AbstractModel):
    _name = 'patco.ai.processor'
    _description = 'PATCO AI Message Processor'

    def process(self, msg):
        try:
            env = self.env
            icp = env['ir.config_parameter'].sudo()
            pid = icp.get_param('ai.bot_partner_id')
            _logger.info('patco_ai: STEP resolve bot_partner_id=%s', pid)
            bot_partner = env['res.partner'].browse(int(pid)) if pid else False
            if not bot_partner or not bot_partner.exists():
                bot_user = env['res.users'].sudo().search([('login', '=', 'odoo_bot')], limit=1)
                bot_partner = bot_user.partner_id if bot_user else False
            if not bot_partner:
                return False
            if msg.author_id and msg.author_id.id == bot_partner.id:
                return False
            channel = False
            if msg.model == 'discuss.channel' and msg.res_id:
                channel = env['discuss.channel'].browse(msg.res_id)
            elif hasattr(msg, 'channel_ids') and msg.channel_ids:
                channel = msg.channel_ids[0]
            _logger.info('patco_ai: STEP resolve channel id=%s', channel.id if channel else None)
            if not channel:
                return False
            author_user = False
            if msg.author_id and msg.author_id.user_ids:
                author_user = msg.author_id.user_ids[0]
            if not author_user:
                author_user = env.user
            # Buscar órdenes activas del usuario (no finalizadas ni canceladas)
            # Asumimos que 'done' marca finalizado. Para cancelado, buscamos si existe stage_id con nombre 'Cancelled' o similar.
            # Como no tenemos certeza del nombre exacto del estado cancelado, usaremos una búsqueda segura.
            domain = [('user_id', '=', author_user.id), ('done', '=', False)]
            # Intentar excluir etapa cancelada si existe
            try:
                cancelled_stage = env['maintenance.stage'].search([('name', 'ilike', 'cancel')], limit=1)
                if cancelled_stage:
                    domain.append(('stage_id', '!=', cancelled_stage.id))
            except Exception:
                pass
            
            requests = env['maintenance.request'].search(domain)
            _logger.info('patco_ai: STEP active requests count=%s', len(requests))
            if not requests:
                channel.sudo().with_context(ai_handler_invoked=True).message_post(
                    body="Hola! No tienes ninguna orden de mantenimiento activa en estos momentos =(. Soy tu asistente técnico, cuando tengas una orden de mantenimiento, ahí estaré!",
                    author_id=bot_partner.id,
                    message_type='comment',
                    subtype_id=env.ref('mail.mt_comment').id,
                )
                return True
            cats = requests.mapped('equipment_id.category_id').ids
            equipment_ids = requests.mapped('equipment_id').ids
            # conversation_id por contexto
            conv_id = f"channel_{channel.id}"
            if equipment_ids:
                conv_id = f"fsm_req_{requests[0].id}"
            _logger.info('patco_ai: STEP build payload conversation_id=%s equipment_ids=%s', conv_id, equipment_ids)
            payload = {
                'conversation_id': conv_id,
                'message': {
                    'role': 'user',
                    'content': msg.body or '',
                },
                'context': {
                    'equipment_category_id': cats[0] if cats else None,
                    'equipment_ids': equipment_ids,
                    'customer_id': requests[0].eq_customer_id.id if hasattr(requests[0], 'eq_customer_id') else None,
                }
            }
            text = env['patco.ai.client'].rag_query(json.dumps(payload))
            _logger.info('patco_ai: STEP backend response empty=%s', not bool(text))
            if not text:
                channel.sudo().with_context(ai_handler_invoked=True).message_post(
                    body="⚠️ Ocurrió un error al procesar tu solicitud. Intenta nuevamente en unos minutos o contacta soporte.",
                    author_id=bot_partner.id,
                    message_type='comment',
                    subtype_id=env.ref('mail.mt_comment').id,
                )
                return True
            channel.sudo().with_context(ai_handler_invoked=True).message_post(
                body=text,
                author_id=bot_partner.id,
                message_type='comment',
                subtype_id=env.ref('mail.mt_comment').id,
            )
            return True
        except Exception:
            _logger.exception('patco_ai: processor exception')
            return False