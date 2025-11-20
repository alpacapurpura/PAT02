{
    'name': 'PATCO Maintenance Simple Report',
    'summary': 'Single service report per maintenance request with photos and notes',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'PATCO',
    'website': 'https://patcoperu.com',
    'depends': ['base', 'web', 'maintenance', 'patco_equipment', 'patco_reports', 'patco_manuales'],
    'data': [
        'data/sequences.xml',
        'security/ir.model.access.csv',
        'data/report.xml',
        'views/maintenance_request_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/report_maintenance_request_informe.xml',
    ],
    'application': False,
}