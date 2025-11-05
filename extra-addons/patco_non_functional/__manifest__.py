# -*- coding: utf-8 -*-
{
    'name': 'PATCO Non Functional',
    'version': '18.0.1.0.0',
    'category': 'Mejoras visuales (UX)',
    'summary': 'PATCO  - Mejoras no funcionales (Infraestructura)',
    'description': """
        PATCO Non Functional
        =================
        
        Este módulo mejora la infraestructura del sistema PATCO.
    """,
    'author': 'PATCO',
    'website': 'https://www.patcoperu.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',

        # --- QUEUE (Colas de Trabajo) ---
        #'queue_job',                        # Trabajos en cola
        #'queue_job_batch',                  # Lotes de trabajos
        #'queue_job_cron',                   # Trabajos programados
        
        # --- CONNECTOR (Conectores) ---
        #'connector',                        # Conector base
        #'component',                        # Componentes
        #'component_event',                  # Eventos de componentes

        # CONFIGURACIÓN & UTILIDADES
        #'server_environment',  # Ambiente del servidor
        # E-COMMERCE & CONECTORES
        #'connector',  # Framework base para conectores e-commerce
        #'connector_base_product',  # Conectores específicos para productos

    ],
    'data': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}