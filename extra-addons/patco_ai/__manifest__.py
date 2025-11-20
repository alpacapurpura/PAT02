{
    'name': 'PATCO AI Integration',
    'summary': 'RAG sync for manuals and AI conversations with odoo_bot',
    'version': '18.0.1.0.1',
    'license': 'LGPL-3',
    'author': 'PATCO',
    'website': 'https://patcoperu.com',
    'depends': ['base', 'mail', 'maintenance', 'patco_equipment', 'patco_manuales'],
    'data': [
        'security/ir.model.access.csv',
        'data/ai_bot_user.xml',
        'data/align_dev_cron.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'application': False,
    'category': 'Hidden',
}