#!/usr/bin/env python3
"""
Herramientas FSM (Field Service Management)
Implementación de herramientas para gestión de órdenes de servicio de campo
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date, timedelta

from schemas.fsm import (
    FSMOrder, FSMTask, FSMEquipment, FSMPartner, FSMUser,
    FSMOrderStage, FSMTaskStage, FSMOrderPriority,
    FSMOrderRequest, FSMOrderResponse,
    FSMOrderUpdateRequest, FSMOrderUpdateResponse,
    FSMOrderListRequest, FSMOrderListResponse,
    create_fsm_order_response,
    validate_fsm_stage_transition,
    calculate_fsm_order_progress
)
from schemas.base import ErrorResponse, ErrorTypeEnum, create_error_response, create_success_response
from utils.odoo_client import OdooClient
from utils.db_client import DatabaseClient
from config import get_settings

_logger = logging.getLogger(__name__)
settings = get_settings()

class FSMToolsManager:
    """Manager para herramientas FSM"""
    
    def __init__(self, odoo_client: OdooClient, db_client: DatabaseClient):
        self.odoo_client = odoo_client
        self.db_client = db_client
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_fsm_order(self, request: FSMOrderRequest) -> Union[FSMOrderResponse, ErrorResponse]:
        """Obtener información detallada de una orden FSM"""
        try:
            self._logger.info(f"Obteniendo orden FSM {request.order_id}")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    ErrorTypeEnum.AUTHENTICATION_ERROR,
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Buscar la orden en Odoo
            domain = [('id', '=', request.order_id)]
            
            # Aplicar filtros adicionales si se especifican
            if request.include_archived is False:
                domain.append(('active', '=', True))
            
            # Campos a obtener
            fields = [
                'id', 'name', 'description', 'stage_id', 'priority',
                'partner_id', 'location_id', 'equipment_id', 'user_id',
                'team_id', 'date_start', 'date_end', 'duration',
                'progress', 'active', 'create_date', 'write_date',
                'task_ids', 'tag_ids', 'company_id'
            ]
            
            orders = await self.odoo_client.search_read(
                'fsm.order',
                domain=domain,
                fields=fields,
                limit=1
            )
            
            if not orders:
                return create_error_response(
                    ErrorTypeEnum.NOT_FOUND,
                    "not_found",
                    f"Orden FSM {request.order_id} no encontrada"
                )
            
            order_data = orders[0]
            
            # Obtener información adicional si se solicita
            if request.include_tasks:
                # Obtener tareas asociadas
                if order_data.get('task_ids'):
                    task_fields = [
                        'id', 'name', 'description', 'stage_id', 'priority',
                        'user_id', 'date_start', 'date_end', 'duration',
                        'progress', 'active'
                    ]
                    
                    tasks = await self.odoo_client.search_read(
                        'fsm.task',
                        domain=[('id', 'in', order_data['task_ids'])],
                        fields=task_fields
                    )
                    order_data['tasks'] = tasks
            
            if request.include_equipment:
                # Obtener información del equipo
                if order_data.get('equipment_id'):
                    equipment_id = order_data['equipment_id'][0] if isinstance(order_data['equipment_id'], list) else order_data['equipment_id']
                    
                    equipment_fields = [
                        'id', 'name', 'model', 'serial_no', 'category_id',
                        'location_id', 'partner_id', 'active'
                    ]
                    
                    equipment = await self.odoo_client.search_read(
                        'maintenance.equipment',
                        domain=[('id', '=', equipment_id)],
                        fields=equipment_fields,
                        limit=1
                    )
                    
                    if equipment:
                        order_data['equipment_info'] = equipment[0]
            
            if request.include_history:
                # Obtener historial de cambios (mail.message)
                messages = await self.odoo_client.search_read(
                    'mail.message',
                    domain=[
                        ('model', '=', 'fsm.order'),
                        ('res_id', '=', request.order_id)
                    ],
                    fields=['id', 'date', 'author_id', 'body', 'message_type'],
                    order='date desc',
                    limit=50
                )
                order_data['history'] = messages
            
            # Crear objeto FSMOrder
            fsm_order = create_fsm_order_from_odoo_data(order_data)
            
            return FSMOrderResponse(
                order=fsm_order,
                message=f"Orden FSM {request.order_id} obtenida exitosamente"
            )
            
        except Exception as e:
            self._logger.error(f"Error obteniendo orden FSM {request.order_id}: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    async def update_fsm_order(self, request: FSMOrderUpdateRequest) -> Union[FSMOrderUpdateResponse, ErrorResponse]:
        """Actualizar una orden FSM"""
        try:
            self._logger.info(f"Actualizando orden FSM {request.order_id}")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Verificar que la orden existe
            existing_order = await self.odoo_client.search_read(
                'fsm.order',
                domain=[('id', '=', request.order_id)],
                fields=['id', 'stage_id', 'name'],
                limit=1
            )
            
            if not existing_order:
                return create_error_response(
                    ErrorTypeEnum.NOT_FOUND,
                    "not_found",
                    f"Orden FSM {request.order_id} no encontrada"
                )
            
            # Preparar datos para actualizar
            update_data = {}
            
            # Actualizar campos básicos
            if request.name is not None:
                update_data['name'] = request.name
            
            if request.description is not None:
                update_data['description'] = request.description
            
            if request.priority is not None:
                update_data['priority'] = request.priority.value
            
            if request.user_id is not None:
                update_data['user_id'] = request.user_id
            
            if request.team_id is not None:
                update_data['team_id'] = request.team_id
            
            if request.date_start is not None:
                update_data['date_start'] = request.date_start.isoformat()
            
            if request.date_end is not None:
                update_data['date_end'] = request.date_end.isoformat()
            
            # Validar transición de etapa si se especifica
            if request.stage_id is not None:
                current_stage_id = existing_order[0]['stage_id'][0] if isinstance(existing_order[0]['stage_id'], list) else existing_order[0]['stage_id']
                
                # Obtener información de las etapas
                stages = await self.odoo_client.search_read(
                    'fsm.stage',
                    domain=[('id', 'in', [current_stage_id, request.stage_id])],
                    fields=['id', 'name', 'sequence', 'fold']
                )
                
                if len(stages) == 2:
                    current_stage = next(s for s in stages if s['id'] == current_stage_id)
                    new_stage = next(s for s in stages if s['id'] == request.stage_id)
                    
                    # Validar transición (lógica básica)
                    if new_stage['sequence'] < current_stage['sequence'] and not request.force_update:
                        return create_error_response(
                            "invalid_transition",
                            f"No se puede retroceder de '{current_stage['name']}' a '{new_stage['name']}' sin forzar"
                        )
                
                update_data['stage_id'] = request.stage_id
            
            # Actualizar progreso si se especifica
            if request.progress is not None:
                update_data['progress'] = request.progress
            
            # Actualizar tags si se especifican
            if request.tag_ids is not None:
                update_data['tag_ids'] = [(6, 0, request.tag_ids)]  # Reemplazar tags
            
            # Realizar la actualización en Odoo
            if update_data:
                success = await self.odoo_client.write(
                    'fsm.order',
                    [request.order_id],
                    update_data
                )
                
                if not success:
                    return create_error_response(
                        "update_failed",
                        "Error actualizando la orden en Odoo"
                    )
            
            # Crear nota si se especifica
            if request.note:
                await self.odoo_client.call(
                    'mail.thread',
                    'message_post',
                    [request.order_id],
                    {
                        'body': request.note,
                        'message_type': 'comment',
                        'subtype_xmlid': 'mail.mt_comment'
                    },
                    model='fsm.order'
                )
            
            # Obtener la orden actualizada
            updated_order = await self.odoo_client.search_read(
                'fsm.order',
                domain=[('id', '=', request.order_id)],
                fields=[
                    'id', 'name', 'description', 'stage_id', 'priority',
                    'partner_id', 'location_id', 'equipment_id', 'user_id',
                    'team_id', 'date_start', 'date_end', 'duration',
                    'progress', 'active', 'write_date'
                ],
                limit=1
            )
            
            if updated_order:
                fsm_order = create_fsm_order_from_odoo_data(updated_order[0])
                
                return FSMOrderUpdateResponse(
                order=updated_order,
                message=f"Orden FSM {request.order_id} actualizada exitosamente"
            )
            else:
                return create_error_response(
                    "not_found",
                    "Error obteniendo la orden actualizada"
                )
            
        except Exception as e:
            self._logger.error(f"Error actualizando orden FSM {request.order_id}: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                f"Error interno: {str(e)}"
            )
    
    async def list_fsm_orders(self, request: FSMOrderListRequest) -> Union[FSMOrderListResponse, ErrorResponse]:
        """Listar órdenes FSM con filtros"""
        try:
            self._logger.info("Listando órdenes FSM")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Construir dominio de búsqueda
            domain = []
            
            # Filtros básicos
            if request.stage:
                domain.append(('stage_id', '=', request.stage.value))
            
            if request.user_id:
                domain.append(('user_id', '=', request.user_id))
            
            if request.partner_id:
                domain.append(('partner_id', '=', request.partner_id))
            
            if request.equipment_id:
                domain.append(('equipment_id', '=', request.equipment_id))
            
            if request.priority:
                domain.append(('priority', '=', request.priority.value))
            
            # Filtros de fecha
            if request.date_from:
                domain.append(('date_start', '>=', request.date_from.isoformat()))
            
            if request.date_to:
                domain.append(('date_end', '<=', request.date_to.isoformat()))
            
            # Filtro de texto
            if hasattr(request, 'search_text') and request.search_text:
                domain.append('|')
                domain.append(('name', 'ilike', request.search_text))
                domain.append(('description', 'ilike', request.search_text))
            
            # Filtro de archivados - por defecto no incluir archivados
            domain.append(('active', '=', True))
            
            # Campos a obtener
            fields = [
                'id', 'name', 'description', 'stage_id', 'priority',
                'partner_id', 'location_id', 'equipment_id', 'user_id',
                'team_id', 'date_start', 'date_end', 'duration',
                'progress', 'active', 'create_date', 'write_date'
            ]
            
            # Calcular offset basado en página
            offset = (request.page - 1) * request.page_size
            
            # Construir orden
            order_str = request.order_by or 'create_date'
            if request.order_direction:
                order_str += f' {request.order_direction}'
            else:
                order_str += ' desc'
            
            # Realizar búsqueda
            orders = await self.odoo_client.search_read(
                'fsm.order',
                domain=domain,
                fields=fields,
                order=order_str,
                limit=request.page_size,
                offset=offset
            )
            
            # Obtener conteo total
            total_count = await self.odoo_client.search_count(
                'fsm.order',
                domain=domain
            )
            
            # Convertir a objetos FSMOrder
            fsm_orders = []
            for order_data in orders:
                try:
                    fsm_order = create_fsm_order_from_odoo_data(order_data)
                    fsm_orders.append(fsm_order)
                except Exception as e:
                    self._logger.warning(f"Error procesando orden {order_data.get('id')}: {str(e)}")
                    continue
            
            return FSMOrderListResponse(
                orders=fsm_orders,
                total_count=total_count,
                page=request.page,
                page_size=request.page_size,
                total_pages=(total_count + request.page_size - 1) // request.page_size,
                message=f"Se encontraron {len(fsm_orders)} órdenes FSM"
            )
            
        except Exception as e:
            self._logger.error(f"Error listando órdenes FSM: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    # async def create_fsm_task(self, request: CreateFSMTaskRequest) -> Union[CreateFSMTaskResponse, ErrorResponse]:
    #     """Crear una nueva tarea FSM"""
    #     # TODO: Implementar cuando se definan las clases CreateFSMTaskRequest y CreateFSMTaskResponse
    #     return create_error_response(
    #         "not_implemented",
    #         "Funcionalidad de creación de tareas FSM no implementada"
    #     )

# Funciones de herramientas individuales

async def get_fsm_order(
    order_id: int,
    include_tasks: bool = False,
    include_equipment: bool = False,
    include_history: bool = False,
    include_archived: bool = False,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[FSMOrderResponse, ErrorResponse]:
    """Obtener información de una orden FSM"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = FSMToolsManager(odoo_client, db_client)
    request = FSMOrderRequest(
        order_id=order_id,
        include_tasks=include_tasks,
        include_equipment=include_equipment,
        include_history=include_history,
        include_archived=include_archived
    )
    
    return await manager.get_fsm_order(request)

async def update_fsm_order(
    order_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    stage_id: Optional[int] = None,
    priority: Optional[FSMOrderPriority] = None,
    user_id: Optional[int] = None,
    team_id: Optional[int] = None,
    date_start: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    progress: Optional[float] = None,
    tag_ids: Optional[List[int]] = None,
    note: Optional[str] = None,
    force_update: bool = False,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[FSMOrderUpdateResponse, ErrorResponse]:
    """Actualizar una orden FSM"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = FSMToolsManager(odoo_client, db_client)
    request = FSMOrderUpdateRequest(
        order_id=order_id,
        name=name,
        description=description,
        stage_id=stage_id,
        priority=priority,
        user_id=user_id,
        team_id=team_id,
        date_start=date_start,
        date_end=date_end,
        progress=progress,
        tag_ids=tag_ids,
        note=note,
        force_update=force_update
    )
    
    return await manager.update_fsm_order(request)

async def list_fsm_orders(
    stage: Optional[FSMOrderStage] = None,
    priority: Optional[FSMOrderPriority] = None,
    user_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    equipment_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 50,
    order_by: Optional[str] = None,
    order_direction: Optional[str] = None,
    include_tasks: bool = False,
    include_partner: bool = False,
    include_equipment: bool = False,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[FSMOrderListResponse, ErrorResponse]:
    """Listar órdenes FSM"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = FSMToolsManager(odoo_client, db_client)
    request = FSMOrderListRequest(
        stage=stage,
        priority=priority,
        user_id=user_id,
        partner_id=partner_id,
        equipment_id=equipment_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_direction=order_direction,
        include_tasks=include_tasks,
        include_partner=include_partner,
        include_equipment=include_equipment
    )
    
    return await manager.list_fsm_orders(request)

async def create_fsm_task(
    order_id: int,
    name: str,
    description: Optional[str] = None,
    priority: Optional[FSMOrderPriority] = None,
    user_id: Optional[int] = None,
    date_start: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    duration: Optional[float] = None,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[dict, ErrorResponse]:
    """Crear una tarea FSM - TEMPORALMENTE DESHABILITADO"""
    
    # Función temporalmente deshabilitada hasta implementar CreateFSMTaskResponse
    return create_error_response(
        "not_implemented",
        "Funcionalidad de creación de tareas FSM temporalmente deshabilitada"
    )
    
    manager = FSMToolsManager(odoo_client, db_client)
    request = CreateFSMTaskRequest(
        order_id=order_id,
        name=name,
        description=description,
        priority=priority,
        user_id=user_id,
        date_start=date_start,
        date_end=date_end,
        duration=duration
    )
    
    return await manager.create_fsm_task(request)