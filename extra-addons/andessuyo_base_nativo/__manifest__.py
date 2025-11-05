# -*- coding: utf-8 -*-
{
    'name': 'Andessuyo',
    'version': '18.0.1.0.0',
    'summary': 'Andessuyo - Módulo de gestión administrativa',
    'description': """
        Módulo de instalación de módulos para la gestión de una empresa de comercialización de Cacao y Café que cuenta con un e-commerce como canal de ventas (pero no el único)
    """,
    'author': 'AndesSuyo',
    'website': 'https://andessuyo.com',
    'license': 'LGPL-3',
    'depends': [
        # === DEPENDENCIAS NATIVAS ODOO ===
        'base',
        'contacts',         # Módulo de Contactos (Clientes, Proveedores, Empleados)
        'mail',             # Módulo de comunicación (necesario para todo)
        'account',
        'accountant',
        'stock',
        'sale_management',
        'product',
        'project',
        'purchase',
        'delivery',
        'point_of_sale',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}