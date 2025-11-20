{
    'name': 'PATCO FSM Employee Integration',
    'version': '18.0.1.0.0',
    'summary': 'Unidirectional sync from Employees to FSM Workers via res.partner',
    'author': 'PATCO',
    'website': 'https://www.patco.pe',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'fieldservice',
        'patco_equipment',
        'patco_manuales',
        'patco_informe',
    ],
    'data': [
        'views/hr_employee_views.xml',
        'views/fsm_worker_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}