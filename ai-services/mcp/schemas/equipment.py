#!/usr/bin/env python3
"""
Esquemas para herramientas de equipos
Definición de requests y responses para gestión de equipos
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseRequest, BaseResponse, BaseConfig, StatusEnum

class EquipmentState(str, Enum):
    """Estados de un equipo"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    BROKEN = "broken"
    RETIRED = "retired"

class MaintenanceType(str, Enum):
    """Tipos de mantenimiento"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"

class MaintenanceState(str, Enum):
    """Estados de mantenimiento"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class EquipmentCategory(BaseModel, BaseConfig):
    """Categoría de equipo"""
    id: int = Field(description="ID de la categoría")
    name: str = Field(description="Nombre de la categoría")
    code: Optional[str] = Field(None, description="Código de la categoría")
    parent_id: Optional[int] = Field(None, description="ID de categoría padre")
    parent_name: Optional[str] = Field(None, description="Nombre de categoría padre")

class EquipmentLocation(BaseModel, BaseConfig):
    """Ubicación de equipo"""
    id: int = Field(description="ID de la ubicación")
    name: str = Field(description="Nombre de la ubicación")
    complete_name: Optional[str] = Field(None, description="Nombre completo con jerarquía")
    parent_id: Optional[int] = Field(None, description="ID de ubicación padre")
    parent_name: Optional[str] = Field(None, description="Nombre de ubicación padre")

class EquipmentPartner(BaseModel, BaseConfig):
    """Partner/Cliente propietario del equipo"""
    id: int = Field(description="ID del partner")
    name: str = Field(description="Nombre del partner")
    email: Optional[str] = Field(None, description="Email del partner")
    phone: Optional[str] = Field(None, description="Teléfono del partner")
    mobile: Optional[str] = Field(None, description="Móvil del partner")
    vat: Optional[str] = Field(None, description="RUC/VAT")

class EquipmentUser(BaseModel, BaseConfig):
    """Usuario responsable del equipo"""
    id: int = Field(description="ID del usuario")
    name: str = Field(description="Nombre del usuario")
    login: Optional[str] = Field(None, description="Login del usuario")
    email: Optional[str] = Field(None, description="Email del usuario")

class MaintenanceRequest(BaseModel, BaseConfig):
    """Solicitud de mantenimiento"""
    id: int = Field(description="ID de la solicitud")
    name: str = Field(description="Nombre/descripción de la solicitud")
    maintenance_type: MaintenanceType = Field(description="Tipo de mantenimiento")
    state: MaintenanceState = Field(description="Estado de la solicitud")
    request_date: Optional[datetime] = Field(None, description="Fecha de solicitud")
    schedule_date: Optional[datetime] = Field(None, description="Fecha programada")
    close_date: Optional[datetime] = Field(None, description="Fecha de cierre")
    user_id: Optional[int] = Field(None, description="ID del técnico asignado")
    user_name: Optional[str] = Field(None, description="Nombre del técnico")
    description: Optional[str] = Field(None, description="Descripción del mantenimiento")
    priority: Optional[str] = Field(None, description="Prioridad (0=Baja, 1=Normal, 2=Alta, 3=Urgente)")

class EquipmentDocument(BaseModel, BaseConfig):
    """Documento relacionado al equipo"""
    id: int = Field(description="ID del documento")
    name: str = Field(description="Nombre del documento")
    mimetype: Optional[str] = Field(None, description="Tipo MIME")
    file_size: Optional[int] = Field(None, description="Tamaño del archivo")
    url: Optional[str] = Field(None, description="URL de descarga")
    description: Optional[str] = Field(None, description="Descripción del documento")
    create_date: Optional[datetime] = Field(None, description="Fecha de creación")

class Equipment(BaseModel, BaseConfig):
    """Equipo completo"""
    id: int = Field(description="ID del equipo")
    name: str = Field(description="Nombre del equipo")
    
    # Información básica
    serial_no: Optional[str] = Field(None, description="Número de serie")
    model: Optional[str] = Field(None, description="Modelo")
    brand: Optional[str] = Field(None, description="Marca")
    manufacturer: Optional[str] = Field(None, description="Fabricante")
    year: Optional[int] = Field(None, description="Año de fabricación")
    
    # Estado y categoría
    state: EquipmentState = Field(description="Estado del equipo")
    category_id: Optional[int] = Field(None, description="ID de categoría")
    category: Optional[EquipmentCategory] = Field(None, description="Información de categoría")
    
    # Ubicación y responsables
    location_id: Optional[int] = Field(None, description="ID de ubicación")
    location: Optional[EquipmentLocation] = Field(None, description="Información de ubicación")
    partner_id: Optional[int] = Field(None, description="ID del propietario")
    partner: Optional[EquipmentPartner] = Field(None, description="Información del propietario")
    user_id: Optional[int] = Field(None, description="ID del responsable")
    user: Optional[EquipmentUser] = Field(None, description="Información del responsable")
    
    # Fechas importantes
    purchase_date: Optional[date] = Field(None, description="Fecha de compra")
    warranty_date: Optional[date] = Field(None, description="Fecha de vencimiento de garantía")
    installation_date: Optional[date] = Field(None, description="Fecha de instalación")
    create_date: Optional[datetime] = Field(None, description="Fecha de creación")
    write_date: Optional[datetime] = Field(None, description="Fecha de modificación")
    
    # Información técnica
    specifications: Optional[str] = Field(None, description="Especificaciones técnicas")
    notes: Optional[str] = Field(None, description="Notas adicionales")
    barcode: Optional[str] = Field(None, description="Código de barras")
    qr_code: Optional[str] = Field(None, description="Código QR")
    
    # Información financiera
    cost: Optional[Decimal] = Field(None, description="Costo de adquisición")
    residual_value: Optional[Decimal] = Field(None, description="Valor residual")
    currency_id: Optional[int] = Field(None, description="ID de moneda")
    currency_name: Optional[str] = Field(None, description="Nombre de moneda")
    
    # Mantenimiento
    maintenance_requests: Optional[List[MaintenanceRequest]] = Field(
        None, description="Solicitudes de mantenimiento"
    )
    next_maintenance_date: Optional[date] = Field(
        None, description="Próxima fecha de mantenimiento"
    )
    maintenance_count: Optional[int] = Field(
        None, description="Número total de mantenimientos"
    )
    
    # Documentos
    documents: Optional[List[EquipmentDocument]] = Field(
        None, description="Documentos relacionados"
    )
    
    # Campos personalizados
    custom_fields: Optional[Dict[str, Any]] = Field(
        None, description="Campos personalizados"
    )
    
    # Metadatos
    company_id: Optional[int] = Field(None, description="ID de la compañía")
    active: bool = Field(default=True, description="Equipo activo")

# Requests

class EquipmentRequest(BaseRequest):
    """Request para obtener información de un equipo"""
    equipment_id: int = Field(
        description="ID del equipo",
        gt=0
    )
    include_category: bool = Field(
        default=True,
        description="Incluir información de categoría"
    )
    include_location: bool = Field(
        default=True,
        description="Incluir información de ubicación"
    )
    include_partner: bool = Field(
        default=True,
        description="Incluir información del propietario"
    )
    include_user: bool = Field(
        default=True,
        description="Incluir información del responsable"
    )
    include_maintenance: bool = Field(
        default=False,
        description="Incluir solicitudes de mantenimiento"
    )
    include_documents: bool = Field(
        default=False,
        description="Incluir documentos relacionados"
    )
    maintenance_limit: int = Field(
        default=10,
        description="Límite de solicitudes de mantenimiento a incluir",
        ge=1,
        le=50
    )

class EquipmentSearchRequest(BaseRequest):
    """Request para buscar equipos"""
    # Filtros de búsqueda
    name: Optional[str] = Field(
        None,
        description="Buscar por nombre (búsqueda parcial)"
    )
    serial_no: Optional[str] = Field(
        None,
        description="Buscar por número de serie"
    )
    model: Optional[str] = Field(
        None,
        description="Buscar por modelo"
    )
    brand: Optional[str] = Field(
        None,
        description="Buscar por marca"
    )
    barcode: Optional[str] = Field(
        None,
        description="Buscar por código de barras"
    )
    
    # Filtros por relaciones
    category_id: Optional[int] = Field(
        None,
        description="Filtrar por categoría"
    )
    location_id: Optional[int] = Field(
        None,
        description="Filtrar por ubicación"
    )
    partner_id: Optional[int] = Field(
        None,
        description="Filtrar por propietario"
    )
    user_id: Optional[int] = Field(
        None,
        description="Filtrar por responsable"
    )
    
    # Filtros por estado
    state: Optional[EquipmentState] = Field(
        None,
        description="Filtrar por estado"
    )
    active: Optional[bool] = Field(
        None,
        description="Filtrar por equipos activos/inactivos"
    )
    
    # Filtros por fechas
    purchase_date_from: Optional[date] = Field(
        None,
        description="Fecha de compra desde"
    )
    purchase_date_to: Optional[date] = Field(
        None,
        description="Fecha de compra hasta"
    )
    warranty_expired: Optional[bool] = Field(
        None,
        description="Filtrar por garantía vencida"
    )
    
    # Paginación
    page: int = Field(
        default=1,
        description="Número de página",
        ge=1
    )
    page_size: int = Field(
        default=20,
        description="Tamaño de página",
        ge=1,
        le=100
    )
    
    # Ordenamiento
    order_by: Optional[str] = Field(
        default="name",
        description="Campo para ordenar"
    )
    order_direction: Optional[str] = Field(
        default="asc",
        description="Dirección del ordenamiento (asc/desc)"
    )
    
    # Inclusiones
    include_category: bool = Field(
        default=True,
        description="Incluir información de categoría"
    )
    include_location: bool = Field(
        default=True,
        description="Incluir información de ubicación"
    )
    include_partner: bool = Field(
        default=False,
        description="Incluir información del propietario"
    )
    include_maintenance_summary: bool = Field(
        default=False,
        description="Incluir resumen de mantenimiento"
    )
    
    @validator('order_direction')
    def validate_order_direction(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("order_direction debe ser 'asc' o 'desc'")
        return v.lower()

class EquipmentUpdateRequest(BaseRequest):
    """Request para actualizar un equipo"""
    equipment_id: int = Field(
        description="ID del equipo",
        gt=0
    )
    updates: Dict[str, Any] = Field(
        description="Campos a actualizar"
    )
    
    @validator('updates')
    def validate_updates(cls, v):
        if not v:
            raise ValueError("Se debe proporcionar al menos un campo para actualizar")
        
        # Validar campos permitidos
        allowed_fields = {
            'name', 'serial_no', 'model', 'brand', 'manufacturer', 'year',
            'state', 'category_id', 'location_id', 'partner_id', 'user_id',
            'purchase_date', 'warranty_date', 'installation_date',
            'specifications', 'notes', 'barcode', 'qr_code',
            'cost', 'residual_value', 'currency_id', 'active', 'custom_fields'
        }
        
        invalid_fields = set(v.keys()) - allowed_fields
        if invalid_fields:
            raise ValueError(f"Campos no permitidos: {invalid_fields}")
        
        # Validar valores de state
        if 'state' in v and v['state'] not in [s.value for s in EquipmentState]:
            raise ValueError(f"State inválido: {v['state']}")
        
        return v

class MaintenanceRequestCreateRequest(BaseRequest):
    """Request para crear solicitud de mantenimiento"""
    equipment_id: int = Field(
        description="ID del equipo",
        gt=0
    )
    name: str = Field(
        description="Nombre/descripción de la solicitud"
    )
    maintenance_type: MaintenanceType = Field(
        description="Tipo de mantenimiento"
    )
    description: Optional[str] = Field(
        None,
        description="Descripción detallada"
    )
    schedule_date: Optional[datetime] = Field(
        None,
        description="Fecha programada"
    )
    user_id: Optional[int] = Field(
        None,
        description="ID del técnico asignado"
    )
    priority: Optional[str] = Field(
        default="1",
        description="Prioridad (0=Baja, 1=Normal, 2=Alta, 3=Urgente)"
    )
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['0', '1', '2', '3']:
            raise ValueError("Priority debe ser '0', '1', '2' o '3'")
        return v

# Responses

class EquipmentResponse(BaseResponse):
    """Response con información de equipo"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: Equipment = Field(
        description="Datos del equipo"
    )

class EquipmentSearchResponse(BaseResponse):
    """Response con lista de equipos"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: List[Equipment] = Field(
        description="Lista de equipos"
    )
    total_count: int = Field(
        description="Total de equipos que cumplen los filtros"
    )
    page: int = Field(
        description="Página actual"
    )
    page_size: int = Field(
        description="Tamaño de página"
    )
    total_pages: int = Field(
        description="Total de páginas"
    )

class EquipmentUpdateResponse(BaseResponse):
    """Response de actualización de equipo"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: Equipment = Field(
        description="Equipo actualizado"
    )
    updated_fields: List[str] = Field(
        description="Campos que fueron actualizados"
    )

class MaintenanceRequestResponse(BaseResponse):
    """Response de creación de solicitud de mantenimiento"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: MaintenanceRequest = Field(
        description="Solicitud de mantenimiento creada"
    )

# Funciones de utilidad

def create_equipment_response(
    equipment_data: Dict[str, Any],
    include_category: bool = True,
    include_location: bool = True,
    include_partner: bool = True,
    include_user: bool = True,
    include_maintenance: bool = False,
    include_documents: bool = False
) -> Equipment:
    """Crear objeto Equipment desde datos de Odoo"""
    
    # Procesar categoría
    category = None
    if include_category and equipment_data.get('category_id'):
        category_data = equipment_data.get('category_data', {})
        if category_data:
            category = EquipmentCategory(**category_data)
    
    # Procesar ubicación
    location = None
    if include_location and equipment_data.get('location_id'):
        location_data = equipment_data.get('location_data', {})
        if location_data:
            location = EquipmentLocation(**location_data)
    
    # Procesar propietario
    partner = None
    if include_partner and equipment_data.get('partner_id'):
        partner_data = equipment_data.get('partner_data', {})
        if partner_data:
            partner = EquipmentPartner(**partner_data)
    
    # Procesar responsable
    user = None
    if include_user and equipment_data.get('user_id'):
        user_data = equipment_data.get('user_data', {})
        if user_data:
            user = EquipmentUser(**user_data)
    
    # Procesar mantenimientos
    maintenance_requests = None
    if include_maintenance and equipment_data.get('maintenance_ids'):
        maintenance_data = equipment_data.get('maintenance_data', [])
        if maintenance_data:
            maintenance_requests = [
                MaintenanceRequest(**maint_data) for maint_data in maintenance_data
            ]
    
    # Procesar documentos
    documents = None
    if include_documents and equipment_data.get('document_ids'):
        documents_data = equipment_data.get('documents_data', [])
        if documents_data:
            documents = [
                EquipmentDocument(**doc_data) for doc_data in documents_data
            ]
    
    # Crear equipo
    equipment = Equipment(
        id=equipment_data['id'],
        name=equipment_data['name'],
        serial_no=equipment_data.get('serial_no'),
        model=equipment_data.get('model'),
        brand=equipment_data.get('brand'),
        manufacturer=equipment_data.get('manufacturer'),
        year=equipment_data.get('year'),
        state=EquipmentState(equipment_data.get('state', 'active')),
        category_id=equipment_data.get('category_id'),
        category=category,
        location_id=equipment_data.get('location_id'),
        location=location,
        partner_id=equipment_data.get('partner_id'),
        partner=partner,
        user_id=equipment_data.get('user_id'),
        user=user,
        purchase_date=equipment_data.get('purchase_date'),
        warranty_date=equipment_data.get('warranty_date'),
        installation_date=equipment_data.get('installation_date'),
        create_date=equipment_data.get('create_date'),
        write_date=equipment_data.get('write_date'),
        specifications=equipment_data.get('specifications'),
        notes=equipment_data.get('notes'),
        barcode=equipment_data.get('barcode'),
        qr_code=equipment_data.get('qr_code'),
        cost=equipment_data.get('cost'),
        residual_value=equipment_data.get('residual_value'),
        currency_id=equipment_data.get('currency_id'),
        currency_name=equipment_data.get('currency_name'),
        maintenance_requests=maintenance_requests,
        next_maintenance_date=equipment_data.get('next_maintenance_date'),
        maintenance_count=equipment_data.get('maintenance_count'),
        documents=documents,
        custom_fields=equipment_data.get('custom_fields'),
        company_id=equipment_data.get('company_id'),
        active=equipment_data.get('active', True)
    )
    
    return equipment

def is_warranty_expired(warranty_date: Optional[date]) -> bool:
    """Verificar si la garantía ha expirado"""
    if not warranty_date:
        return False
    
    from datetime import date as date_class
    return warranty_date < date_class.today()

def get_equipment_age_in_years(purchase_date: Optional[date]) -> Optional[float]:
    """Calcular la edad del equipo en años"""
    if not purchase_date:
        return None
    
    from datetime import date as date_class
    today = date_class.today()
    age_days = (today - purchase_date).days
    return age_days / 365.25  # Considerar años bisiestos

def build_equipment_search_domain(
    search_params: EquipmentSearchRequest
) -> List[tuple]:
    """Construir dominio de búsqueda para Odoo"""
    domain = []
    
    # Filtros de texto
    if search_params.name:
        domain.append(('name', 'ilike', search_params.name))
    if search_params.serial_no:
        domain.append(('serial_no', '=', search_params.serial_no))
    if search_params.model:
        domain.append(('model', 'ilike', search_params.model))
    if search_params.brand:
        domain.append(('brand', 'ilike', search_params.brand))
    if search_params.barcode:
        domain.append(('barcode', '=', search_params.barcode))
    
    # Filtros por relaciones
    if search_params.category_id:
        domain.append(('category_id', '=', search_params.category_id))
    if search_params.location_id:
        domain.append(('location_id', '=', search_params.location_id))
    if search_params.partner_id:
        domain.append(('partner_id', '=', search_params.partner_id))
    if search_params.user_id:
        domain.append(('user_id', '=', search_params.user_id))
    
    # Filtros por estado
    if search_params.state:
        domain.append(('state', '=', search_params.state.value))
    if search_params.active is not None:
        domain.append(('active', '=', search_params.active))
    
    # Filtros por fechas
    if search_params.purchase_date_from:
        domain.append(('purchase_date', '>=', search_params.purchase_date_from))
    if search_params.purchase_date_to:
        domain.append(('purchase_date', '<=', search_params.purchase_date_to))
    if search_params.warranty_expired is not None:
        from datetime import date as date_class
        today = date_class.today()
        if search_params.warranty_expired:
            domain.append(('warranty_date', '<', today))
        else:
            domain.append(('warranty_date', '>=', today))
    
    return domain