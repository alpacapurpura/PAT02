# -*- coding: utf-8 -*-
{
    'name': 'PATCO Base - Módulos de mejora UX',
    'version': '18.0.1.0.0',
    'category': 'Mejoras visuales (UX)',
    'summary': 'PATCO UX - Mejoras en la eXperiencia de Usuario (UX)',
    'description': """
        PATCO UX
        =================
        
        Este módulo mejora la experiencia de usuario (UX) del sistema PATCO.
    """,
    'author': 'PATCO',
    'website': 'https://www.patcoperu.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',

        # --- Branding & Theming (Marca Blanca) ---
        'mail_debrand',             # Elimina "Powered by Odoo" de emails
        'disable_odoo_online',      # Desactiva telemetría y enlaces a Odoo
        #'web_brand',                Falta dependencia# Cambia logo principal y título de ventana (¡AGREGADO!)
        'web_favicon',              # Favicon personalizado
        'web_company_color',        # Colores de la compañía en la UI

        # --- Responsi veness & Layout ---
        'web_responsive',           # ¡Crítico para móviles y tablets!
        'web_dialog_size',          # Permite redimensionar pop-ups

        # --- QOL & Usabilidad (Calidad de Vida) ---
        'web_tree_many2one_clickable', # Clic directo en M2O en vistas de lista (¡AGREGADO!)
        'web_refresher',               # Botón para refrescar vistas sin recargar (F5)
        # 'web_listview_range_select', # Si lo encuentras para v18, actívalo
        'web_timeline',                     # Línea de tiempo web
        'web_notify',                       # Notificaciones web
        #'web_environment_ribbon',           # Cinta de ambiente
        'web_dialog_size',                  # Tamaño de diálogos
        'fieldservice',                     # Vistas Field Service (para herencia)

        # --- Búsqueda y Filtros ---
        #'web_search_with_and',      # Permite búsquedas "AND" con Shift
        #'base_name_search_improved',# Búsqueda flexible en name_search
        #'web_searchbar_full_width', # Barra de búsqueda más ancha (¡AGREGADO!)

        # --- Widgets para Vistas (Para ti como dev) ---
        'web_widget_x2many_2d_matrix', # Widget para matrices 2D

        # --- SERVER-UX (Experiencia de Usuario) ---
        #'base_tier_validation',             # Validación por niveles base
        #'base_technical_features',          # Características técnicas
        'date_range',                       # Rangos de fechas
        #'sequence_check_digit',             # Dígitos de verificación
        #'server_action_mass_edit',          # Edición masiva
    ],
    'data': [
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}