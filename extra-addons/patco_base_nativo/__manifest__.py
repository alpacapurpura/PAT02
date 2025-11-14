# -*- coding: utf-8 -*-
{
    'name': 'Patco Base - Módulos Nativos',
    'version': '18.0.1.0.0',
    'summary': 'PATCO - Módulo de gestión administrativa Nativa',
    'description': """
        Módulo de instalación y configuración de módulos Nativos para la gestión de una empresa de servicio de mantenimiento de activos para otras empresas en el rubro HORECA
    """,
    'author': 'PATCO',
    'website': 'https://patcoperu.com',
    'license': 'LGPL-3',
    'depends': [
        # === DEPENDENCIAS NATIVAS ODOO ===
        # --- Núcleo y Contactos ---
        'base',
        'contacts',         # Módulo de Contactos (Clientes, Proveedores, Empleados)
        'mail',             # Módulo de comunicación (necesario para todo)

        # --- Recursos Humanos ---
        'hr',               # Módulo de Empleados (para tus técnicos)
        'hr_expense',       # Módulo de Gastos (para viáticos, combustible, etc.)
        'hr_timesheet',     # Módulo de Partes de Horas (para costear la mano de obra)

        # --- Operaciones y Ventas ---
        'product',          # Módulo de Productos (para tus repuestos y servicios)
        'stock',            # Módulo de Inventario/Stock (para tus almacenes de repuestos)
        'purchase',         # Módulo de Compras (para reabastecer tus repuestos)
        'sale_management',  # Módulo de Ventas (para cotizaciones y órdenes de servicio)

        # --- Finanzas y Contratos ---
        'account',          # Módulo de Facturación y Contabilidad (Cobros y Pagos)
        #'analytic',         # Módulo de Costos (Contabilidad Analítica)
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}