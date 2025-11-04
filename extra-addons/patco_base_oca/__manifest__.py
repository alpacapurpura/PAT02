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
        
        'fleet',  # Módulo de Gestión de Vehículos y Mantenimiento

        # GESTIÓN DOCUMENTAL
        'dms',  # Sistema de gestión de documentos
        
        # REPORTES
        'report_xlsx',  # Reportes en Excel
        'report_xlsx_helper',  # Ayudante para reportes Excel
        

        # === CONTRATOS & ACUERDOS (CORE ADMINISTRATIVO) ===
        'contract',  # Contratos recurrentes - facturación automática - YA TIENES
        'contract_sale',  # Ventas → Contratos automáticos - YA TIENES
        'contract_payment_mode',  # Modos de pago en contratos - YA TIENES
        'product_contract',  # Productos contractuales/servicios recurrentes - YA TIENES
        'agreement',  # Acuerdos base - contratos marco - YA TIENES
        'agreement_sale',  # Acuerdos → Órdenes de venta - YA TIENES
        
        # === CONTRATOS AVANZADOS ===
        'contract_forecast',  # Pronósticos de ingresos por contratos - ÚTIL para planificación
        'contract_queue_job',  # Facturación masiva de contratos en background
        'contract_mandate',  # Mandatos de débito directo en contratos
        'contract_termination',  # Terminación controlada de contratos
        'contract_price_revision',  # Revisión automática de precios
        
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
        'partner_industry_secondary',  # Industria secundaria
        'partner_multi_relation',  # Relaciones múltiples de socios
        'partner_ref_unique',  # Referencia única de socio
        'partner_second_lastname',  # Segundo apellido
        'partner_supplierinfo_smartbutton',  # Botón inteligente de info de proveedor
        
        # === HR ADMINISTRATIVO (GASTOS & COSTOS) ===
        'hr_timesheet_sheet',  # Hojas de tiempo para costos - YA TIENES
        'hr_timesheet_task_required',  # Tareas obligatorias en timesheet - YA TIENES
        'hr_expense_advance_clearing',  # Adelantos y liquidación de gastos - YA TIENES
        'hr_holidays_public',  # Feriados públicos para cálculos - YA TIENES
        
        # === HR EMPLEADOS & DATOS BÁSICOS ===
        'hr_skills',  # Habilidades de empleados
        'hr_employee_firstname',  # Nombres separados de empleados
        'hr_employee_id',  # ID automático de empleados
        'hr_employee_phone_extension',  # Extensiones telefónicas
        'hr_department_code',  # Códigos de departamento
        'hr_contract_reference',  # Referencias de contratos
        
        # === TIMESHEET AVANZADO ===
        'hr_timesheet_begin_end',  # Horas inicio/fin en timesheet - ÚTIL para técnicos
        'hr_timesheet_task_stage',  # Estados de tareas en timesheet
        'crm_timesheet',  # Timesheet desde CRM/oportunidades
        'sale_timesheet_budget',  # Presupuesto de horas en ventas
        
        # === ASISTENCIA & CONTROL ===
        'hr_attendance_reason',  # Razones de entrada/salida
        'hr_attendance_report_theoretical_time',  # Reportes de tiempo teórico vs real
        
        # === GASTOS AVANZADOS ===
        'hr_expense_invoice',  # Facturas de proveedores en gastos
        'hr_expense_sequence',  # Secuencias automáticas de gastos
        'hr_expense_tier_validation',  # Validación por niveles de gastos grandes
        
        # === VACACIONES & AUSENCIAS ===
        'hr_holidays_leave_repeated',  # Ausencias repetitivas/programadas
        'hr_holidays_settings',  # Configuraciones avanzadas de vacaciones
        
        # === PAYROLL (OPCIONAL) ===
        'payroll',  # Nómina básica
        'payroll_account',  # Integración nómina con contabilidad
        
        # === STOCK & COSTOS ===
        'stock_secondary_unit',  # Unidades secundarias para costos
        'product_secondary_unit',  # Productos con unidades múltiples
        
        
        # === CONFIGURACIÓN ADMINISTRATIVA ===
        # TEMPORALMENTE COMENTADO: Módulos que requieren 'astor' (dependencia de base_view_inheritance_extension)
        # 'base_name_search_improved',  # Búsqueda mejorada en formularios - REQUIERE ASTOR
        'base_location',  # Ubicaciones geográficas para sucursales
        'base_location_geonames_import',  # Importar ubicaciones geográficas
        'web_widget_x2many_2d_matrix',  # Widget matriz para configuraciones

        # === MÓDULOS CONTABLES B2B (ALTA PRIORIDAD) ===
        'account_invoice_start_end_dates',  # Fechas inicio/fin en facturas - CRÍTICO para servicios
        'partner_invoicing_mode',  # Modos de facturación por cliente (mensual, por servicio)
        'partner_invoicing_mode_monthly',  # Facturación mensual automática para contratos
        'account_invoice_date_due',  # Gestión avanzada de fechas de vencimiento
        #'account_global_discount',  falta dependencia - # Descuentos globales para clientes corporativos
        'account_asset_management',  # Gestión de activos fijos - ESENCIAL para equipos
        'account_asset_number',  # Numeración de activos
        'account_spread_cost_revenue',  # Distribución de costos/ingresos en el tiempo
        'account_due_list',  # Lista de vencimientos - CRÍTICO para cobranzas B2B
        'account_payment_term_extension',  # Términos de pago extendidos para B2B
        'account_payment_notification',  # Notificaciones de pagos
        'account_credit_control',  # Control de créditos y débitos
        
        # === REPORTES & HERRAMIENTAS CONTABLES (MEDIA PRIORIDAD) ===
        'partner_statement',  # Estados de cuenta de clientes - IMPORTANTE para B2B
        'account_financial_report',  # Reportes financieros avanzados
        'account_tax_balance',  # Balance de impuestos
        'account_move_template',  # Plantillas de asientos para servicios recurrentes
        'account_netting',  # Compensación de deudas entre empresas
        'account_usability',  # Mejoras de usabilidad contable
        'account_fiscal_year',  # Gestión de ejercicios fiscales
        'account_invoice_refund_link',  # Vinculación de facturas y notas de crédito
        'account_invoice_warn_message',  # Mensajes de advertencia en facturas
        'stock_picking_invoicing',  # Facturación desde albaranes de entrega

        # === MÓDULOS BANCARIOS B2B (ALTA PRIORIDAD) ===
        'account_payment_mode',  # Modos de pago por cliente - CRÍTICO para B2B
        'account_payment_partner',  # Modos de pago en socios y facturas - ESENCIAL
        'account_payment_order',  # Órdenes de pago masivas - MUY ÚTIL para múltiples clientes
        'account_payment_sale',  # Integración pagos con ventas
        'account_statement_base',  # Base para extractos bancarios - REQUERIDO por import modules
        'account_statement_import_base',  # Base para importar extractos bancarios
        'account_statement_import_file',  # Importar extractos desde archivos - ÚTIL
        'account_statement_import_ofx',  # Formato OFX (común en bancos peruanos)
        
        # === PAGOS MASIVOS & LOTES (MEDIA PRIORIDAD) ===
        'account_payment_batch_oca',  # Pagos en lotes - ÚTIL para múltiples proveedores
        'account_payment_base_oca',  # Base para pagos OCA
        'account_payment_purchase',  # Pagos desde compras
        'account_statement_import_camt',  # Formato CAMT (estándar europeo)
        'account_statement_import_online',  # Importación automática online
        
        # === RECONCILIACIÓN AVANZADA (ACCOUNT-RECONCILE) ===
        'account_reconcile_oca',  # Reconciliación avanzada para Community - IMPORTANTE
        'account_reconcile_model_oca',  # Modelos de reconciliación automática
        'base_transaction_id',  # ID de transacciones para institutos financieros

        
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}