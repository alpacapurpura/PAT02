from odoo import models
from odoo.modules.module import get_module_resource
import base64


class PatcoAISetup(models.AbstractModel):
    _name = 'patco.ai.setup'
    _description = 'PATCO AI Setup Utilities'

    def disable_native_odoobot(self):
        users = self.env['res.users'].sudo().search([])
        if users:
            try:
                users.write({'odoobot_state': 'disabled'})
            except Exception:
                pass

    def prune_channels(self):
        Users = self.env['res.users'].sudo()
        Partners = self.env['res.partner'].sudo()
        Discuss = self.env['discuss.channel'].sudo()
        # Identify any native OdooBot-like partners distinct from our bot
        our_bot = Users.search([('login', '=', 'odoo_bot')], limit=1)
        our_partner = our_bot.partner_id if our_bot else False
        candidates = Partners.search([('name', 'ilike', 'OdooBot')])
        native_partners = candidates
        if our_partner:
            native_partners = candidates.filtered(lambda p: p.id != our_partner.id)
        if not native_partners:
            return
        chans = Discuss.search([])
        for ch in chans:
            members = False
            if hasattr(ch, 'channel_partner_ids'):
                members = ch.channel_partner_ids
            elif hasattr(ch, 'member_ids'):
                members = ch.member_ids.mapped('partner_id')
            members = members or Partners
            for np in native_partners:
                if np in members:
                    try:
                        ch.sudo().remove_members(np)
                    except Exception:
                        try:
                            ch.sudo().write({'channel_partner_ids': [(3, np.id)]})
                        except Exception:
                            pass
                ctype = getattr(ch, 'channel_type', '') or getattr(ch, 'channel_type_name', '')
                if ctype in ('chat','direct','direct_message','private'):
                    try:
                        ch.sudo().unlink()
                    except Exception:
                        pass

    def apply_bot_avatar(self):
        Users = self.env['res.users'].sudo()
        our = Users.search([('login','=','odoo_bot')], limit=1)
        partner = our.partner_id if our else False
        if not partner:
            return
        try:
            path = get_module_resource('patco_ai', 'static', 'patco_odoo_bot.png')
            if path:
                with open(path, 'rb') as f:
                    data = f.read()
                partner.write({'image_1920': base64.b64encode(data)})
        except Exception:
            pass

    def ensure_ai_params(self):
        Users = self.env['res.users'].sudo()
        # Identify our bot strictly by login/email 'odoo_bot'
        our = Users.search(['|',('login','=','odoo_bot'),('email','=','odoo_bot')], limit=1)
        icp = self.env['ir.config_parameter'].sudo()
        if our and our.partner_id:
            icp.set_param('ai.bot_partner_id', str(our.partner_id.id))
        icp.set_param('ai.bot_aliases', 'odoo_bot,OdooBot,Odoo Bot')

    def clean_pycache(self):
        import os
        import shutil
        module_path = os.path.join('/mnt', 'extra-addons', 'patco_ai')
        for root, dirs, files in os.walk(module_path):
            for d in dirs:
                if d == '__pycache__':
                    p = os.path.join(root, d)
                    try:
                        shutil.rmtree(p)
                    except Exception:
                        pass

    def upgrade_module_self(self):
        Mod = self.env['ir.module.module'].sudo()
        rec = Mod.search([('name', '=', 'patco_ai')], limit=1)
        if rec:
            try:
                rec.button_immediate_upgrade()
            except Exception:
                try:
                    rec.button_immediate_install()
                except Exception:
                    pass

    def configure_dev_icp(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('ai.rag_endpoint_base', 'http://patco-langgraph-server-dev:8001')
        icp.set_param('ai.rag_endpoint', 'http://patco-langgraph-server-dev:8001/conversation/{conversation_id}/message')
        icp.set_param('ai.rag_timeout', '20')
        icp.set_param('ai.bot_require_mention', 'false')

    def validate_end_to_end(self):
        Users = self.env['res.users'].sudo()
        Channel = self.env['discuss.channel'].sudo()
        icp = self.env['ir.config_parameter'].sudo()
        ch = Channel.search([('name', '=', 'General')], limit=1)
        if not ch:
            ch = Channel.create({'name': 'General', 'channel_type': 'channel'})
        self.ensure_ai_params()
        pid = icp.get_param('ai.bot_partner_id')
        bot_partner = self.env['res.partner'].browse(int(pid)) if pid else False
        if not bot_partner:
            bot_user = Users.search([('login', '=', 'odoo_bot')], limit=1)
            bot_partner = bot_user.partner_id if bot_user else False
        # Caso 1: cortesía
        tester1 = Users.search([('login', '=', 'tester_ai_1')], limit=1)
        if not tester1:
            tester1 = Users.create({'name': 'Tester AI 1', 'login': 'tester_ai_1', 'email': 'tester_ai_1@example.com'})
        self.env['maintenance.request'].sudo().search([('user_id', '=', tester1.id)]).write({'done': True})
        ch.message_post(body='Ping sin orden', author_id=tester1.partner_id.id, message_type='comment', subtype_id=self.env.ref('mail.mt_comment').id)
        # Caso 2: técnica
        Equip = self.env['maintenance.equipment'].sudo()
        Cat = self.env['maintenance.equipment.category'].sudo()
        tester2 = Users.search([('login', '=', 'tester_ai_2')], limit=1)
        if not tester2:
            tester2 = Users.create({'name': 'Tester AI 2', 'login': 'tester_ai_2', 'email': 'tester_ai_2@example.com'})
        cat = Cat.create({'name': 'Bombas'})
        eq = Equip.create({'name': 'Bomba #1', 'category_id': cat.id})
        self.env['maintenance.request'].sudo().create({'name': 'Orden Test', 'equipment_id': eq.id, 'user_id': tester2.id})
        ch.message_post(body='Ping con orden activa', author_id=tester2.partner_id.id, message_type='comment', subtype_id=self.env.ref('mail.mt_comment').id)
        # Caso 3: error backend
        base_prev = icp.get_param('ai.rag_endpoint_base')
        icp.set_param('ai.rag_endpoint_base', 'http://127.0.0.1:5999')
        tester3 = Users.search([('login', '=', 'tester_ai_3')], limit=1)
        if not tester3:
            tester3 = Users.create({'name': 'Tester AI 3', 'login': 'tester_ai_3', 'email': 'tester_ai_3@example.com'})
        self.env['maintenance.request'].sudo().search([('user_id', '=', tester3.id)]).write({'done': True})
        ch.message_post(body='Ping con backend caído', author_id=tester3.partner_id.id, message_type='comment', subtype_id=self.env.ref('mail.mt_comment').id)
        icp.set_param('ai.rag_endpoint_base', base_prev or 'http://patco-langgraph-server-dev:8001')
        return True

    def align_dev_and_validate(self):
        self.clean_pycache()
        # self.upgrade_module_self()
        self.configure_dev_icp()
        self.validate_end_to_end()
        return True