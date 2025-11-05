# -*- coding: utf-8 -*-
{
    'name': 'Patco Base OCA',
    'version': '18.0.1.0.0',
    'summary': 'PATCO - Módulo de gestión administrativa OCA',
    'description': """
        Módulo de instalación y configuración de módulos OCA para la gestión de una empresa de servicio de mantenimiento de activos para otras empresas en el rubro HORECA
    """,
    'author': 'PATCO',
    'website': 'https://patcoperu.com',
    'license': 'LGPL-3',
    'depends': [
        # === DEPENDENCIAS NATIVAS ODOO ===
        # === MÓDULOS PERSONALIZADOS ===
        'patco_base_nativo',  # Módulo de instalación y configuración de módulos Nativos
        'patco_ux',  # Mejoras de UX personalizadas

        # GESTIÓN DOCUMENTAL
        'dms',  # Sistema de gestión de documentos

        # === CONTRATOS & ACUERDOS (CORE ADMINISTRATIVO) ===
        'contract',  # Contratos recurrentes - facturación automática - YA TIENES
        'contract_sale',  # Ventas → Contratos automáticos - YA TIENES
        'contract_payment_mode',  # Modos de pago en contratos - YA TIENES
        'product_contract',  # Productos contractuales/servicios recurrentes - YA TIENES
        'agreement',  # Acuerdos base - contratos marco - YA TIENES
        'agreement_sale',  # Acuerdos → Órdenes de venta - YA TIENES
        
        # === CONTRATOS AVANZADOS ===
        'contract_forecast',  # Pronósticos de ingresos por contratos - ÚTIL para planificación
        
        # === ACUERDOS LEGALES & ADMINISTRATIVOS ===
        'agreement_legal',  # Gestión legal completa de acuerdos - IMPORTANTE para B2B
        'agreement_account',  # Integración acuerdos con contabilidad
        'agreement_rebate',  # Descuentos y rebajas por acuerdos marco
        
        # === VENTAS & ADMINISTRACIÓN COMERCIAL ===
        'sale_order_line_date',  # Fechas específicas en líneas de venta
        'sale_order_archive',  # Archivo histórico de órdenes
        'sale_elaboration',  # Elaboración/preparación de ventas
        'sale_order_secondary_unit',  # Unidades secundarias (kg/cajas/etc)
        'sale_blanket_order',  # Órdenes marco/contratos comerciales
        'sale_order_lot_selection',  # Selección de lotes en ventas
        'sale_order_product_recommendation',  # Recomendaciones de productos
        
        # === PARTNER CONTACT (GESTIÓN ADMINISTRATIVA CLIENTES) # CRM & SOCIOS===
        'partner_contact_access_link',  # Acceso rápido a contactos
        'partner_contact_role',  # Roles administrativos (facturación, compras, etc.)
        'partner_contact_birthdate',  # Fecha de nacimiento de contactos
        'partner_contact_department',  # Departamento de contactos
        'partner_contact_job_position',  # Posición de trabajo de contactos
        'partner_contact_personal_information_page',  # Página de información personal
        'partner_external_map',  # Mapas externos de socios
        'partner_firstname',  # Nombre de contactos
        'partner_identification',  # Identificación de socios
        
        # === HR ADMINISTRATIVO (GASTOS & COSTOS) ===
        'hr_timesheet_sheet',  # Hojas de tiempo para costos - YA TIENES
        'hr_timesheet_task_required',  # Tareas obligatorias en timesheet - YA TIENES
        
        # === HR EMPLEADOS & DATOS BÁSICOS ===
        'hr_skills',  # Habilidades de empleados
        'hr_employee_id',  # ID automático de empleados
        'hr_contract_reference',  # Referencias de contratos
        
        # === TIMESHEET AVANZADO ===
        'hr_timesheet_begin_end',  # Horas inicio/fin en timesheet - ÚTIL para técnicos
        'hr_timesheet_task_stage',  # Estados de tareas en timesheet
        
        # === GASTOS AVANZADOS ===
        'hr_expense_invoice',  # Facturas de proveedores en gastos
        'hr_expense_sequence',  # Secuencias automáticas de gastos
        

        # === CONFIGURACIÓN ADMINISTRATIVA ===
        'base_location',  # Ubicaciones geográficas para sucursales
        'base_location_geonames_import',  # Importar ubicaciones geográficas
        'web_widget_x2many_2d_matrix',  # Widget matriz para configuraciones

        # === MÓDULOS CONTABLES B2B (ALTA PRIORIDAD) ===
        'account_invoice_start_end_dates',  # Fechas inicio/fin en facturas - CRÍTICO para servicios
        'partner_invoicing_mode',  # Modos de facturación por cliente (mensual, por servicio)
        'partner_invoicing_mode_monthly',  # Facturación mensual automática para contratos
        'account_invoice_date_due',  # Gestión avanzada de fechas de vencimiento
        #'account_asset_number',  # Numeración de activos
        #'account_spread_cost_revenue',  # Distribución de costos/ingresos en el tiempo
        'account_due_list',  # Lista de vencimientos - CRÍTICO para cobranzas B2B
        'account_payment_term_extension',  # Términos de pago extendidos para B2B
        #'account_payment_notification',  # Notificaciones de pagos
        'account_credit_control',  # Control de créditos y débitos
        
        # === REPORTES & HERRAMIENTAS CONTABLES (MEDIA PRIORIDAD) ===
        'account_usability',  # Mejoras de usabilidad contable
        'account_fiscal_year',  # Gestión de ejercicios fiscales
        'account_invoice_refund_link',  # Vinculación de facturas y notas de crédito

        # === MÓDULOS BANCARIOS B2B (ALTA PRIORIDAD) ===
        'account_payment_mode',  # Modos de pago por cliente - CRÍTICO para B2B
        'account_payment_partner',  # Modos de pago en socios y facturas - ESENCIAL
        'account_payment_sale',  # Integración pagos con ventas
        
        # === PAGOS MASIVOS & LOTES (MEDIA PRIORIDAD) ===
        'account_payment_base_oca',  # Base para pagos OCA
        'account_payment_purchase',  # Pagos desde compras

        
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}