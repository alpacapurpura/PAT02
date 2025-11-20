from . import models
from .models import setup


def post_init_hook(env):
    env['patco.ai.bot.user'].ensure_bot()
    # Disable OdooBot onboarding for all users at install/upgrade
    users = env['res.users'].sudo().search([])
    if users:
        try:
            users.write({'odoobot_state': 'disabled'})
        except Exception:
            pass
    # Prune native OdooBot from channels (if exists), apply avatar and ensure params
    env['patco.ai.setup'].disable_native_odoobot()
    env['patco.ai.setup'].prune_channels()
    env['patco.ai.setup'].apply_bot_avatar()
    env['patco.ai.setup'].ensure_ai_params()
    try:
        env['patco.ai.setup'].align_dev_and_validate()
    except Exception:
        pass
    # Defaults seguros para LangGraph si no están definidos
    try:
        icp = env['ir.config_parameter'].sudo()
        if not icp.get_param('ai.rag_endpoint_base'):
            icp.set_param('ai.rag_endpoint_base', 'http://patco-langgraph-server-dev:8001')
        if not icp.get_param('ai.rag_endpoint'):
            icp.set_param('ai.rag_endpoint', 'http://patco-langgraph-server-dev:8001/conversation/{conversation_id}/message')
        if not icp.get_param('ai.rag_timeout'):
            icp.set_param('ai.rag_timeout', '20')
    except Exception:
        pass