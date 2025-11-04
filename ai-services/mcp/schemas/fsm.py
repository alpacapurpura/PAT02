#!/usr/bin/env python3
"""
Esquemas para herramientas FSM (Field Service Management)
Definición de requests y responses para órdenes de servicio
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseRequest, BaseResponse, BaseConfig, StatusEnum

class FSMOrderStage(str, Enum):
    """Etapas de una orden FSM"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class FSMOrderPriority(str, Enum):
    """Prioridades de orden FSM"""
    LOW = "0"
    NORMAL = "1"
    HIGH = "2"
    URGENT = "3"

class FSMTaskStage(str, Enum):
    """Etapas de tareas FSM"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class FSMPartner(BaseModel, BaseConfig):
    """Información de partner/cliente"""
    id: int = Field(description="ID del partner")
    name: str = Field(description="Nombre del partner")
    email: Optional[str] = Field(None, description="Email del partner")
    phone: Optional[str] = Field(None, description="Teléfono del partner")
    mobile: Optional[str] = Field(None, description="Móvil del partner")
    street: Optional[str] = Field(None, description="Dirección")
    city: Optional[str] = Field(None, description="Ciudad")
    state_id: Optional[int] = Field(None, description="ID del estado/provincia")
    country_id: Optional[int] = Field(None, description="ID del país")
    vat: Optional[str] = Field(None, description="RUC/VAT")

class FSMUser(BaseModel, BaseConfig):
    """Información de usuario/técnico"""
    id: int = Field(description="ID del usuario")
    name: str = Field(description="Nombre del usuario")
    login: Optional[str] = Field(None, description="Login del usuario")
    email: Optional[str] = Field(None, description="Email del usuario")
    phone: Optional[str] = Field(None, description="Teléfono del usuario")
    mobile: Optional[str] = Field(None, description="Móvil del usuario")

class FSMEquipment(BaseModel, BaseConfig):
    """Información de equipo relacionado"""
    id: int = Field(description="ID del equipo")
    name: str = Field(description="Nombre del equipo")
    serial_no: Optional[str] = Field(None, description="Número de serie")
    model: Optional[str] = Field(None, description="Modelo")
    brand: Optional[str] = Field(None, description="Marca")
    category_id: Optional[int] = Field(None, description="ID de categoría")
    location: Optional[str] = Field(None, description="Ubicación")

class FSMTask(BaseModel, BaseConfig):
    """Tarea de una orden FSM"""
    id: int = Field(description="ID de la tarea")
    name: str = Field(description="Nombre de la tarea")
    description: Optional[str] = Field(None, description="Descripción de la tarea")
    stage: FSMTaskStage = Field(description="Etapa de la tarea")
    user_id: Optional[int] = Field(None, description="ID del usuario asignado")
    user_name: Optional[str] = Field(None, description="Nombre del usuario asignado")
    planned_hours: Optional[float] = Field(None, description="Horas planificadas")
    effective_hours: Optional[float] = Field(None, description="Horas efectivas")
    date_start: Optional[datetime] = Field(None, description="Fecha de inicio")
    date_end: Optional[datetime] = Field(None, description="Fecha de fin")
    notes: Optional[str] = Field(None, description="Notas de la tarea")

class FSMOrder(BaseModel, BaseConfig):
    """Orden de servicio FSM completa"""
    id: int = Field(description="ID de la orden")
    name: str = Field(description="Número/nombre de la orden")
    description: Optional[str] = Field(None, description="Descripción")
    stage: FSMOrderStage = Field(description="Etapa actual")
    priority: FSMOrderPriority = Field(description="Prioridad")
    
    # Fechas
    date_start: Optional[datetime] = Field(None, description="Fecha de inicio planificada")
    date_end: Optional[datetime] = Field(None, description="Fecha de fin planificada")
    date_start_actual: Optional[datetime] = Field(None, description="Fecha de inicio real")
    date_end_actual: Optional[datetime] = Field(None, description="Fecha de fin real")
    create_date: Optional[datetime] = Field(None, description="Fecha de creación")
    write_date: Optional[datetime] = Field(None, description="Fecha de modificación")
    
    # Relaciones
    partner_id: Optional[int] = Field(None, description="ID del cliente")
    partner: Optional[FSMPartner] = Field(None, description="Información del cliente")
    user_id: Optional[int] = Field(None, description="ID del técnico asignado")
    user: Optional[FSMUser] = Field(None, description="Información del técnico")
    equipment_id: Optional[int] = Field(None, description="ID del equipo")
    equipment: Optional[FSMEquipment] = Field(None, description="Información del equipo")
    
    # Tareas
    tasks: Optional[List[FSMTask]] = Field(None, description="Tareas de la orden")
    
    # Información adicional
    location_id: Optional[int] = Field(None, description="ID de ubicación")
    location_name: Optional[str] = Field(None, description="Nombre de ubicación")
    company_id: Optional[int] = Field(None, description="ID de la compañía")
    
    # Campos calculados
    duration_planned: Optional[float] = Field(None, description="Duración planificada (horas)")
    duration_actual: Optional[float] = Field(None, description="Duración real (horas)")
    progress: Optional[float] = Field(None, description="Progreso (0-100)")
    
    # Metadatos
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Campos personalizados")

# Requests

class FSMOrderRequest(BaseRequest):
    """Request para obtener una orden FSM"""
    order_id: int = Field(
        description="ID de la orden FSM",
        gt=0
    )
    include_tasks: bool = Field(
        default=False,
        description="Incluir tareas de la orden"
    )
    include_partner: bool = Field(
        default=True,
        description="Incluir información del cliente"
    )
    include_equipment: bool = Field(
        default=True,
        description="Incluir información del equipo"
    )
    include_user: bool = Field(
        default=True,
        description="Incluir información del técnico"
    )

class FSMOrderUpdateRequest(BaseRequest):
    """Request para actualizar una orden FSM"""
    order_id: int = Field(
        description="ID de la orden FSM",
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
            'description', 'stage', 'priority', 'date_start', 'date_end',
            'date_start_actual', 'date_end_actual', 'user_id', 'location_id',
            'notes', 'custom_fields'
        }
        
        invalid_fields = set(v.keys()) - allowed_fields
        if invalid_fields:
            raise ValueError(f"Campos no permitidos: {invalid_fields}")
        
        # Validar valores de stage
        if 'stage' in v and v['stage'] not in [s.value for s in FSMOrderStage]:
            raise ValueError(f"Stage inválido: {v['stage']}")
        
        # Validar valores de priority
        if 'priority' in v and v['priority'] not in [p.value for p in FSMOrderPriority]:
            raise ValueError(f"Priority inválido: {v['priority']}")
        
        return v

class FSMOrderListRequest(BaseRequest):
    """Request para listar órdenes FSM"""
    # Filtros
    stage: Optional[FSMOrderStage] = Field(
        None,
        description="Filtrar por etapa"
    )
    priority: Optional[FSMOrderPriority] = Field(
        None,
        description="Filtrar por prioridad"
    )
    user_id: Optional[int] = Field(
        None,
        description="Filtrar por técnico asignado"
    )
    partner_id: Optional[int] = Field(
        None,
        description="Filtrar por cliente"
    )
    equipment_id: Optional[int] = Field(
        None,
        description="Filtrar por equipo"
    )
    date_from: Optional[date] = Field(
        None,
        description="Fecha desde (fecha de inicio)"
    )
    date_to: Optional[date] = Field(
        None,
        description="Fecha hasta (fecha de inicio)"
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
        default="create_date",
        description="Campo para ordenar"
    )
    order_direction: Optional[str] = Field(
        default="desc",
        description="Dirección del ordenamiento (asc/desc)"
    )
    
    # Inclusiones
    include_tasks: bool = Field(
        default=False,
        description="Incluir tareas"
    )
    include_partner: bool = Field(
        default=True,
        description="Incluir información del cliente"
    )
    include_equipment: bool = Field(
        default=True,
        description="Incluir información del equipo"
    )
    
    @validator('order_direction')
    def validate_order_direction(cls, v):
        if v is None:
            return v
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("order_direction debe ser 'asc' o 'desc'")
        return v.lower()

# Responses

class FSMOrderResponse(BaseResponse):
    """Response con información de orden FSM"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: FSMOrder = Field(
        description="Datos de la orden FSM"
    )

class FSMOrderUpdateResponse(BaseResponse):
    """Response de actualización de orden FSM"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: FSMOrder = Field(
        description="Orden FSM actualizada"
    )
    updated_fields: List[str] = Field(
        description="Campos que fueron actualizados"
    )

class FSMOrderListResponse(BaseResponse):
    """Response con lista de órdenes FSM"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: List[FSMOrder] = Field(
        description="Lista de órdenes FSM"
    )
    total_count: int = Field(
        description="Total de órdenes que cumplen los filtros"
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

# Funciones de utilidad

def create_fsm_order_response(
    order_data: Dict[str, Any],
    include_tasks: bool = False,
    include_partner: bool = True,
    include_equipment: bool = True,
    include_user: bool = True
) -> FSMOrder:
    """Crear objeto FSMOrder desde datos de Odoo"""
    
    # Procesar partner
    partner = None
    if include_partner and order_data.get('partner_id'):
        partner_data = order_data.get('partner_data', {})
        if partner_data:
            partner = FSMPartner(**partner_data)
    
    # Procesar usuario/técnico
    user = None
    if include_user and order_data.get('user_id'):
        user_data = order_data.get('user_data', {})
        if user_data:
            user = FSMUser(**user_data)
    
    # Procesar equipo
    equipment = None
    if include_equipment and order_data.get('equipment_id'):
        equipment_data = order_data.get('equipment_data', {})
        if equipment_data:
            equipment = FSMEquipment(**equipment_data)
    
    # Procesar tareas
    tasks = None
    if include_tasks and order_data.get('task_ids'):
        tasks_data = order_data.get('tasks_data', [])
        if tasks_data:
            tasks = [FSMTask(**task_data) for task_data in tasks_data]
    
    # Crear orden FSM
    fsm_order = FSMOrder(
        id=order_data['id'],
        name=order_data['name'],
        description=order_data.get('description'),
        stage=FSMOrderStage(order_data.get('stage', 'draft')),
        priority=FSMOrderPriority(order_data.get('priority', '1')),
        date_start=order_data.get('date_start'),
        date_end=order_data.get('date_end'),
        date_start_actual=order_data.get('date_start_actual'),
        date_end_actual=order_data.get('date_end_actual'),
        create_date=order_data.get('create_date'),
        write_date=order_data.get('write_date'),
        partner_id=order_data.get('partner_id'),
        partner=partner,
        user_id=order_data.get('user_id'),
        user=user,
        equipment_id=order_data.get('equipment_id'),
        equipment=equipment,
        tasks=tasks,
        location_id=order_data.get('location_id'),
        location_name=order_data.get('location_name'),
        company_id=order_data.get('company_id'),
        duration_planned=order_data.get('duration_planned'),
        duration_actual=order_data.get('duration_actual'),
        progress=order_data.get('progress'),
        custom_fields=order_data.get('custom_fields')
    )
    
    return fsm_order

def validate_fsm_stage_transition(
    current_stage: FSMOrderStage,
    new_stage: FSMOrderStage
) -> bool:
    """Validar si una transición de etapa es válida"""
    
    # Definir transiciones válidas
    valid_transitions = {
        FSMOrderStage.DRAFT: [FSMOrderStage.CONFIRMED, FSMOrderStage.CANCELLED],
        FSMOrderStage.CONFIRMED: [FSMOrderStage.ASSIGNED, FSMOrderStage.CANCELLED],
        FSMOrderStage.ASSIGNED: [FSMOrderStage.IN_PROGRESS, FSMOrderStage.CANCELLED],
        FSMOrderStage.IN_PROGRESS: [FSMOrderStage.DONE, FSMOrderStage.CANCELLED],
        FSMOrderStage.DONE: [],  # Estado final
        FSMOrderStage.CANCELLED: []  # Estado final
    }
    
    return new_stage in valid_transitions.get(current_stage, [])

def calculate_fsm_order_progress(tasks: List[FSMTask]) -> float:
    """Calcular progreso de una orden basado en sus tareas"""
    if not tasks:
        return 0.0
    
    completed_tasks = sum(1 for task in tasks if task.stage == FSMTaskStage.DONE)
    return (completed_tasks / len(tasks)) * 100

def get_fsm_order_duration(
    date_start: Optional[datetime],
    date_end: Optional[datetime]
) -> Optional[float]:
    """Calcular duración en horas entre dos fechas"""
    if not date_start or not date_end:
        return None
    
    duration = date_end - date_start
    return duration.total_seconds() / 3600  # Convertir a horas