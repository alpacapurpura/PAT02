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
        'web',
        'account',
        'stock',
        'sale_management',
        'product',
        'purchase',
        'delivery',
        'point_of_sale',
        
        # === MÓDULOS OCA PARA COMERCIALIZACIÓN ORGÁNICA ===
        # INVENTARIO & LOGÍSTICA
        'stock_dynamic_routing',  # Enrutamiento dinámico de stock
        'stock_picking_batch_creation',  # Creación de lotes de picking
        'stock_picking_group_by_partner_by_carrier',  # Agrupación por socio y transportista
        'stock_picking_invoice_link',  # Enlace picking-factura
        'stock_picking_mass_action',  # Acciones masivas en picking
        'stock_picking_partner_note',  # Notas de socio en picking
        'stock_picking_progress',  # Progreso de picking
        'stock_picking_send_by_mail',  # Envío de picking por correo
        'stock_no_negative',  # Prevención de stock negativo
        'stock_production_lot_active',  # Lotes de producción activos
        'stock_restrict_lot',  # Restricción de lotes
        'stock_landed_costs_purchase_auto',  # Costos de aterrizaje automático
        'scrap_reason_code',  # Códigos de razón de desecho
        'delivery_total_weight_from_packaging',  # Peso total de entrega desde empaque
        
        # E-COMMERCE & CONECTORES
        'connector',  # Framework base para conectores e-commerce
        'connector_base_product',  # Conectores específicos para productos
        
        # GESTIÓN DE PRODUCTOS
        'product_assortment',  # Gestión de surtidos por cliente - crucial para B2B
        'product_manufacturer',  # Fabricantes de marca propia
        'product_category_code',  # Códigos de categorías para organización
        'product_category_tag',  # Etiquetas de categorías
        'product_barcode_required',  # Códigos de barras obligatorios
        'product_multi_category',  # Múltiples categorías por producto
        'product_packaging_dimension',  # Dimensiones de empaque
        'product_packaging_level',  # Niveles de empaque
        'product_net_weight',  # Peso neto - importante para productos orgánicos
        'product_total_weight_from_packaging',  # Peso total desde empaque
        'product_secondary_unit',  # Unidades secundarias de medida
        'product_state',  # Estados de producto (activo, descontinuado, etc.)
        'product_supplierinfo_archive',  # Archivo de información de proveedores
        'product_supplierinfo_revision',  # Revisión de información de proveedores
        'product_main_supplierinfo',  # Proveedor principal
        'product_cost_security',  # Seguridad en costos de productos
        'product_sequence',  # Secuencias de productos
        'product_set',  # Conjuntos de productos
        'product_tags_code',  # Códigos de etiquetas
        'uom_alias',  # Alias de unidades de medida
        'stock_lot_production_date',  # Fecha de producción de lotes
        
        # COMPRAS & PROVEEDORES
        'purchase_request',  # Solicitudes de compra
        'purchase_request_tier_validation',  # Validación por niveles
        'purchase_order_type',  # Tipos de orden de compra
        'purchase_advance_payment',  # Pagos anticipados a proveedores
        'purchase_last_price_info',  # Información del último precio
        'purchase_order_general_discount',  # Descuentos generales en compras
        'purchase_tier_validation',  # Validación por niveles en compras
        'purchase_tag',  # Etiquetas de compras
        
        # VENTAS & DISTRIBUCIÓN
        'sale_automatic_workflow',  # Flujo automático de ventas
        'sale_order_type',  # Tipos de orden de venta
        'sale_order_tag',  # Etiquetas de orden de venta
        'sale_order_line_tag',  # Etiquetas de línea de venta
        'sale_order_product_assortment',  # Surtido de productos en venta
        'sale_order_product_recommendation',  # Recomendación de productos en venta
        'sale_global_discount',  # Descuentos globales
        'sale_order_general_discount',  # Descuentos generales en orden
        'sale_fixed_discount',  # Descuentos fijos
        'sale_discount_display_amount',  # Mostrar monto de descuento
        'sale_tier_validation',  # Validación por niveles en ventas
        'sale_partner_incoterm',  # Incoterms por socio
        'sale_product_set',  # Conjuntos de productos en venta
        'sale_packaging_default',  # Empaque por defecto
        'sale_order_carrier_auto_assign',  # Asignación automática de transportista
        'sale_stock_delivery_address',  # Dirección de entrega
        'sale_stock_delivery_state',  # Estado de entrega
        'pricelist_cache',  # Caché de listas de precios
        'product_customerinfo_sale',  # Información de cliente en ventas
        
        # CRM & SOCIOS (SOLO MÓDULOS EXISTENTES)
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
        
        # GESTIÓN DOCUMENTAL
        'dms',  # Sistema de gestión de documentos
        
        # REPORTES (SOLO MÓDULOS EXISTENTES)
        'report_xlsx',  # Reportes en Excel
        'report_xlsx_helper',  # Ayudante para reportes Excel
        
        # CONFIGURACIÓN & UTILIDADES
        'server_environment',  # Ambiente del servidor
        
        # === MÓDULOS PERSONALIZADOS ===
        'patco_ux',  # Mejoras de UX personalizadas
    ],
    'data': [
        'data/andessuyo_general_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}