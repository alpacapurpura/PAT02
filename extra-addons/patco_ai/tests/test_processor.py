from odoo.tests.common import TransactionCase


class TestPatcoAIProcessor(TransactionCase):
    def setUp(self):
        super().setUp()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('ai.rag_endpoint_base', 'http://patco-langgraph-server-dev:8001')
        icp.set_param('ai.rag_endpoint', 'http://patco-langgraph-server-dev:8001/conversation/{conversation_id}/message')
        icp.set_param('ai.rag_timeout', '2')

        # Ensure bot
        self.env['patco.ai.bot.user'].ensure_bot()

        # Create a channel and user
        # self.channel = self.env['discuss.channel'].sudo().create({
        #     'name': 'Test General',
        #     'channel_type': 'channel',
        # })
        # self.user = self.env['res.users'].sudo().create({
        #     'name': 'Tester',
        #     'login': 'tester',
        #     'email': 'tester@example.com',
        # })

        # Get bot partner
        pid = icp.get_param('ai.bot_partner_id')
        self.bot_partner = self.env['res.partner'].browse(int(pid)) if pid else self.env['res.users'].sudo().search([('login', '=', 'odoo_bot')], limit=1).partner_id

    def _post_from(self, author_partner, body):
        return self.channel.sudo().with_context(ai_handler_invoked=False).message_post(
            body=body,
            author_id=author_partner.id,
            message_type='comment',
            subtype_id=self.env.ref('mail.mt_comment').id,
        )

    def test_cortesia_sin_orden(self):
        msg = self._post_from(self.user.partner_id, 'Hola')
        self.assertTrue(msg)

    def test_error_backend(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('ai.rag_endpoint_base', 'http://127.0.0.1:5999')
        msg = self._post_from(self.user.partner_id, 'Prueba fallida')
        self.assertTrue(msg)