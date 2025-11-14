{
    'name': 'PATCO Reports',
    'summary': 'Customized QWeb reports for quotations and invoices',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'PATCO',
    'website': 'https://patcoperu.com',
    'depends': ['base', 'web', 'sale', 'account'],
    'data': [
        'data/paperformat.xml',
        'views/report_templates.xml',
        'data/report_actions.xml',
    ],
    'application': False,
}
