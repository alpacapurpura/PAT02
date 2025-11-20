from odoo import api, fields, models


class AIBotUser(models.TransientModel):
    _name = 'patco.ai.bot.user'
    _description = 'Ensure odoo_bot user'

    @api.model
    def ensure_bot(self):
        bot = self.env['res.users'].sudo().search([('login', '=', 'odoo_bot')], limit=1)
        if not bot:
            bot = self.env['res.users'].sudo().create({
                'name': 'Odoo Bot',
                'login': 'odoo_bot',
                'email': 'bot@patco.local',
            })
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('ai.bot_user_xmlid', 'patco_ai.user_odoo_bot')
        if bot.partner_id:
            icp.set_param('ai.bot_partner_id', str(bot.partner_id.id))
        # Always disable native OdooBot onboarding per user
        try:
            self.env['res.users'].sudo().search([]).write({'odoobot_state': 'disabled'})
        except Exception:
            pass
        return bot.id