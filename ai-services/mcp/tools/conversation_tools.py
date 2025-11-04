#!/usr/bin/env python3
"""
Herramientas de Conversación con IA
Implementación de herramientas para gestionar conversaciones y mensajes con IA
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import uuid

from schemas.conversation import (
    CreateConversationRequest, CreateConversationResponse,
    SendMessageRequest, SendMessageResponse,
    GetConversationRequest, GetConversationResponse,
    ListConversationsRequest, ListConversationsResponse,
    UpdateConversationRequest, UpdateConversationResponse,
    Conversation, ConversationMessage, ConversationStatus,
    MessageType, MessageRole, ConversationContext, AIModel,
    ConversationType, Priority, MessageAttachment, create_conversation_from_odoo_data
)
from schemas.base import ErrorResponse, create_error_response, create_success_response, ErrorTypeEnum
from utils.odoo_client import OdooClient
from utils.db_client import DatabaseClient
from config import get_settings

_logger = logging.getLogger(__name__)
settings = get_settings()

class ConversationToolsManager:
    """Manager para herramientas de conversación con IA"""
    
    def __init__(self, odoo_client: OdooClient, db_client: DatabaseClient):
        self.odoo_client = odoo_client
        self.db_client = db_client
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Configuración de IA
        self.default_ai_model = AIModel.GPT_4
        self.max_context_length = 4000
        self.max_messages_per_conversation = 100
    
    async def create_conversation(self, request: CreateConversationRequest) -> Union[CreateConversationResponse, ErrorResponse]:
        """Crear una nueva conversación con IA"""
        try:
            self._logger.info(f"Creando conversación: '{request.title}'")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    ErrorTypeEnum.AUTHENTICATION_ERROR,
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Preparar datos para crear la conversación en Odoo
            conversation_data = {
                'name': request.title,
                'description': request.description or '',
                'conversation_type': request.conversation_type.value,
                'ai_model': request.ai_model.value,
                'priority': request.priority.value,
                'state': ConversationStatus.ACTIVE.value,
                'user_id': request.user_id,
                'context_data': json.dumps(request.context.dict() if request.context else {}),
                'max_tokens': request.max_tokens,
                'temperature': request.temperature,
                'system_prompt': request.system_prompt or '',
                'tags': ','.join(request.tags) if request.tags else ''
            }
            
            # Crear conversación en Odoo (usando un modelo personalizado)
            conversation_id = await self.odoo_client.create(
                'ai.conversation',
                conversation_data
            )
            
            if not conversation_id:
                return create_error_response(
                    ErrorTypeEnum.INTERNAL_ERROR,
                    "creation_failed",
                    "No se pudo crear la conversación en Odoo"
                )
            
            # Obtener la conversación creada
            conversation_record = await self.odoo_client.read(
                'ai.conversation',
                [conversation_id],
                [
                    'id', 'name', 'description', 'conversation_type', 'ai_model',
                    'priority', 'state', 'user_id', 'context_data', 'max_tokens',
                    'temperature', 'system_prompt', 'tags', 'create_date',
                    'write_date', 'message_count', 'total_tokens', 'total_cost'
                ]
            )
            
            if not conversation_record:
                return create_error_response(
                    ErrorTypeEnum.NOT_FOUND,
                    "not_found",
                    "Conversación creada pero no se pudo recuperar"
                )
            
            # Convertir a objeto Conversation
            conversation = create_conversation_from_odoo(conversation_record[0])
            
            # Crear mensaje inicial del sistema si se proporcionó
            if request.system_prompt:
                system_message_data = {
                    'conversation_id': conversation_id,
                    'role': MessageRole.SYSTEM.value,
                    'content': request.system_prompt,
                    'message_type': MessageType.TEXT.value,
                    'tokens': len(request.system_prompt.split()),  # Estimación simple
                    'cost': 0.0
                }
                
                await self.odoo_client.create(
                    'ai.conversation.message',
                    system_message_data
                )
            
            return CreateConversationResponse(
                conversation=conversation,
                message=f"Conversación '{request.title}' creada exitosamente"
            )
            
        except Exception as e:
            self._logger.error(f"Error creando conversación: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    async def send_message(self, request: SendMessageRequest) -> Union[SendMessageResponse, ErrorResponse]:
        """Enviar un mensaje en una conversación"""
        try:
            self._logger.info(f"Enviando mensaje a conversación {request.conversation_id}")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    ErrorTypeEnum.AUTHENTICATION_ERROR,
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Verificar que la conversación existe y está activa
            conversation_data = await self.odoo_client.read(
                'ai.conversation',
                [request.conversation_id],
                ['id', 'state', 'ai_model', 'max_tokens', 'temperature', 'system_prompt']
            )
            
            if not conversation_data:
                return create_error_response(
                    ErrorTypeEnum.NOT_FOUND,
                    "not_found",
                    f"Conversación {request.conversation_id} no encontrada"
                )
            
            conversation_info = conversation_data[0]
            
            if conversation_info['state'] != ConversationStatus.ACTIVE.value:
                return create_error_response(
                    ErrorTypeEnum.VALIDATION_ERROR,
                    "conversation_inactive",
                    "La conversación no está activa"
                )
            
            # Crear mensaje del usuario
            user_message_data = {
                'conversation_id': request.conversation_id,
                'role': MessageRole.USER.value,
                'content': request.content,
                'message_type': request.message_type.value,
                'tokens': len(request.content.split()),  # Estimación simple
                'cost': 0.0,
                'metadata': json.dumps(request.metadata or {})
            }
            
            # Agregar attachments si existen
            if request.attachments:
                attachments_data = []
                for attachment in request.attachments:
                    attachments_data.append({
                        'file_name': attachment.file_name,
                        'file_type': attachment.file_type,
                        'file_size': attachment.file_size,
                        'file_url': attachment.file_url,
                        'description': attachment.description
                    })
                user_message_data['attachments'] = json.dumps(attachments_data)
            
            user_message_id = await self.odoo_client.create(
                'ai.conversation.message',
                user_message_data
            )
            
            if not user_message_id:
                return create_error_response(
                    ErrorTypeEnum.INTERNAL_ERROR,
                    "message_creation_failed",
                    "No se pudo crear el mensaje del usuario"
                )
            
            # Generar respuesta de IA (simulada por ahora)
            ai_response = await self._generate_ai_response(
                conversation_id=request.conversation_id,
                user_message=request.content,
                ai_model=AIModel(conversation_info['ai_model']),
                max_tokens=conversation_info['max_tokens'],
                temperature=conversation_info['temperature']
            )
            
            # Crear mensaje de respuesta de IA
            ai_message_data = {
                'conversation_id': request.conversation_id,
                'role': MessageRole.ASSISTANT.value,
                'content': ai_response['content'],
                'message_type': MessageType.TEXT.value,
                'tokens': ai_response['tokens'],
                'cost': ai_response['cost'],
                'metadata': json.dumps({
                    'model_used': ai_response['model'],
                    'processing_time': ai_response['processing_time'],
                    'confidence': ai_response.get('confidence', 0.0)
                })
            }
            
            ai_message_id = await self.odoo_client.create(
                'ai.conversation.message',
                ai_message_data
            )
            
            # Actualizar estadísticas de la conversación
            await self._update_conversation_stats(
                conversation_id=request.conversation_id,
                new_tokens=user_message_data['tokens'] + ai_message_data['tokens'],
                new_cost=ai_message_data['cost']
            )
            
            # Obtener los mensajes creados
            user_message = await self._get_message(user_message_id)
            ai_message = await self._get_message(ai_message_id)
            
            return SendMessageResponse(
                user_message=user_message,
                ai_response=ai_message,
                conversation_id=request.conversation_id,
                message="Mensaje enviado y respuesta generada exitosamente"
            )
            
        except Exception as e:
            self._logger.error(f"Error enviando mensaje: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    async def _generate_ai_response(
        self,
        conversation_id: int,
        user_message: str,
        ai_model: AIModel,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generar respuesta de IA (simulada por ahora)"""
        try:
            # Por ahora, generar una respuesta simulada
            # En una implementación real, aquí se llamaría a la API de OpenAI, Claude, etc.
            
            import time
            start_time = time.time()
            
            # Respuesta simulada basada en el contenido del mensaje
            if "hola" in user_message.lower():
                response_content = "¡Hola! ¿En qué puedo ayudarte hoy?"
            elif "ayuda" in user_message.lower():
                response_content = "Estoy aquí para ayudarte. ¿Qué necesitas saber?"
            elif "gracias" in user_message.lower():
                response_content = "¡De nada! ¿Hay algo más en lo que pueda ayudarte?"
            else:
                response_content = f"He recibido tu mensaje: '{user_message}'. ¿Podrías ser más específico sobre lo que necesitas?"
            
            processing_time = time.time() - start_time
            
            # Calcular tokens y costo estimado
            response_tokens = len(response_content.split())
            input_tokens = len(user_message.split())
            total_tokens = response_tokens + input_tokens
            
            # Costo estimado (basado en precios aproximados de OpenAI)
            cost_per_token = {
                AIModel.GPT_3_5_TURBO: 0.000002,
                AIModel.GPT_4: 0.00003,
                AIModel.GPT_4_TURBO: 0.00001,
                AIModel.CLAUDE_3_SONNET: 0.000015,
                AIModel.CLAUDE_3_OPUS: 0.000075,
                AIModel.GEMINI_PRO: 0.0000005
            }
            
            estimated_cost = total_tokens * cost_per_token.get(ai_model, 0.00001)
            
            return {
                'content': response_content,
                'tokens': response_tokens,
                'cost': estimated_cost,
                'model': ai_model.value,
                'processing_time': processing_time,
                'confidence': 0.85  # Confianza simulada
            }
            
        except Exception as e:
            self._logger.error(f"Error generando respuesta de IA: {str(e)}")
            return {
                'content': "Lo siento, hubo un error al generar la respuesta.",
                'tokens': 10,
                'cost': 0.0,
                'model': ai_model.value,
                'processing_time': 0.0,
                'confidence': 0.0
            }
    
    async def _update_conversation_stats(
        self,
        conversation_id: int,
        new_tokens: int,
        new_cost: float
    ) -> None:
        """Actualizar estadísticas de la conversación"""
        try:
            # Obtener estadísticas actuales
            current_stats = await self.odoo_client.read(
                'ai.conversation',
                [conversation_id],
                ['message_count', 'total_tokens', 'total_cost']
            )
            
            if current_stats:
                stats = current_stats[0]
                
                # Actualizar estadísticas
                updated_data = {
                    'message_count': (stats.get('message_count', 0) + 2),  # +2 por user + AI
                    'total_tokens': (stats.get('total_tokens', 0) + new_tokens),
                    'total_cost': (stats.get('total_cost', 0.0) + new_cost),
                    'write_date': datetime.now().isoformat()
                }
                
                await self.odoo_client.write(
                    'ai.conversation',
                    [conversation_id],
                    updated_data
                )
                
        except Exception as e:
            self._logger.error(f"Error actualizando estadísticas de conversación: {str(e)}")
    
    async def _get_message(self, message_id: int) -> Optional[ConversationMessage]:
        """Obtener un mensaje por ID"""
        try:
            message_data = await self.odoo_client.read(
                'ai.conversation.message',
                [message_id],
                [
                    'id', 'conversation_id', 'role', 'content', 'message_type',
                    'tokens', 'cost', 'metadata', 'attachments', 'create_date',
                    'write_date'
                ]
            )
            
            if message_data:
                return create_message_from_odoo(message_data[0])
            
            return None
            
        except Exception as e:
            self._logger.error(f"Error obteniendo mensaje {message_id}: {str(e)}")
            return None
    
    async def get_conversation(self, request: GetConversationRequest) -> Union[GetConversationResponse, ErrorResponse]:
        """Obtener una conversación específica"""
        try:
            self._logger.info(f"Obteniendo conversación {request.conversation_id}")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    ErrorTypeEnum.AUTHENTICATION_ERROR,
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Obtener datos de la conversación
            conversation_data = await self.odoo_client.read(
                'ai.conversation',
                [request.conversation_id],
                [
                    'id', 'name', 'description', 'conversation_type', 'ai_model',
                    'priority', 'state', 'user_id', 'context_data', 'max_tokens',
                    'temperature', 'system_prompt', 'tags', 'create_date',
                    'write_date', 'message_count', 'total_tokens', 'total_cost'
                ]
            )
            
            if not conversation_data:
                return create_error_response(
                    ErrorTypeEnum.NOT_FOUND,
                    "not_found",
                    f"Conversación {request.conversation_id} no encontrada"
                )
            
            # Convertir a objeto Conversation
            conversation = create_conversation_from_odoo(conversation_data[0])
            
            # Obtener mensajes si se solicita
            if request.include_messages:
                messages_data = await self.odoo_client.search_read(
                    'ai.conversation.message',
                    domain=[('conversation_id', '=', request.conversation_id)],
                    fields=[
                        'id', 'conversation_id', 'role', 'content', 'message_type',
                        'tokens', 'cost', 'metadata', 'attachments', 'create_date',
                        'write_date'
                    ],
                    order='create_date asc',
                    limit=request.message_limit
                )
                
                messages = []
                for msg_data in messages_data:
                    try:
                        message = create_message_from_odoo(msg_data)
                        messages.append(message)
                    except Exception as e:
                        self._logger.warning(f"Error procesando mensaje: {str(e)}")
                        continue
                
                conversation.messages = messages
            
            return GetConversationResponse(
                conversation=conversation,
                message=f"Conversación {request.conversation_id} obtenida exitosamente"
            )
            
        except Exception as e:
            self._logger.error(f"Error obteniendo conversación {request.conversation_id}: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    async def list_conversations(self, request: ListConversationsRequest) -> Union[ListConversationsResponse, ErrorResponse]:
        """Listar conversaciones con filtros"""
        try:
            self._logger.info("Listando conversaciones")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    ErrorTypeEnum.AUTHENTICATION_ERROR,
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Construir dominio de búsqueda
            domain = []
            
            # Filtro por usuario
            if request.user_id:
                domain.append(('user_id', '=', request.user_id))
            
            # Filtro por tipo de conversación
            if request.conversation_types:
                type_values = [ct.value for ct in request.conversation_types]
                domain.append(('conversation_type', 'in', type_values))
            
            # Filtro por estado
            if request.states:
                state_values = [s.value for s in request.states]
                domain.append(('state', 'in', state_values))
            
            # Filtro por modelo de IA
            if request.ai_models:
                model_values = [m.value for m in request.ai_models]
                domain.append(('ai_model', 'in', model_values))
            
            # Filtro por fecha
            if request.date_from:
                domain.append(('create_date', '>=', request.date_from.isoformat()))
            
            if request.date_to:
                domain.append(('create_date', '<=', request.date_to.isoformat()))
            
            # Filtro de búsqueda de texto
            if request.search_text:
                domain.append('|')
                domain.append(('name', 'ilike', request.search_text))
                domain.append(('description', 'ilike', request.search_text))
            
            # Campos a obtener
            fields = [
                'id', 'name', 'description', 'conversation_type', 'ai_model',
                'priority', 'state', 'user_id', 'create_date', 'write_date',
                'message_count', 'total_tokens', 'total_cost'
            ]
            
            # Realizar búsqueda
            conversations_data = await self.odoo_client.search_read(
                'ai.conversation',
                domain=domain,
                fields=fields,
                order=request.order_by or 'write_date desc',
                limit=request.limit,
                offset=request.offset
            )
            
            # Obtener conteo total
            total_count = await self.odoo_client.search_count(
                'ai.conversation',
                domain=domain
            )
            
            # Convertir a objetos Conversation
            conversations = []
            for conv_data in conversations_data:
                try:
                    conversation = create_conversation_from_odoo(conv_data)
                    conversations.append(conversation)
                except Exception as e:
                    self._logger.warning(f"Error procesando conversación {conv_data.get('id')}: {str(e)}")
                    continue
            
            return ListConversationsResponse(
                conversations=conversations,
                total_count=total_count,
                offset=request.offset,
                limit=request.limit,
                message=f"Se encontraron {len(conversations)} conversaciones"
            )
            
        except Exception as e:
            self._logger.error(f"Error listando conversaciones: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    async def update_conversation(self, request: UpdateConversationRequest) -> Union[UpdateConversationResponse, ErrorResponse]:
        """Actualizar una conversación"""
        try:
            self._logger.info(f"Actualizando conversación {request.conversation_id}")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    ErrorTypeEnum.AUTHENTICATION_ERROR,
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Verificar que la conversación existe
            existing_conversation = await self.odoo_client.read(
                'ai.conversation',
                [request.conversation_id],
                ['id', 'state']
            )
            
            if not existing_conversation:
                return create_error_response(
                    ErrorTypeEnum.NOT_FOUND,
                    "not_found",
                    f"Conversación {request.conversation_id} no encontrada"
                )
            
            # Preparar datos de actualización
            update_data = {}
            
            if request.title is not None:
                update_data['name'] = request.title
            
            if request.description is not None:
                update_data['description'] = request.description
            
            if request.state is not None:
                update_data['state'] = request.state.value
            
            if request.priority is not None:
                update_data['priority'] = request.priority.value
            
            if request.tags is not None:
                update_data['tags'] = ','.join(request.tags)
            
            if request.max_tokens is not None:
                update_data['max_tokens'] = request.max_tokens
            
            if request.temperature is not None:
                update_data['temperature'] = request.temperature
            
            if request.system_prompt is not None:
                update_data['system_prompt'] = request.system_prompt
            
            if not update_data:
                return create_error_response(
                    ErrorTypeEnum.VALIDATION_ERROR,
                    "no_changes",
                    "No se proporcionaron cambios para actualizar"
                )
            
            # Actualizar en Odoo
            success = await self.odoo_client.write(
                'ai.conversation',
                [request.conversation_id],
                update_data
            )
            
            if not success:
                return create_error_response(
                    ErrorTypeEnum.INTERNAL_ERROR,
                    "update_failed",
                    "No se pudo actualizar la conversación"
                )
            
            # Obtener conversación actualizada
            updated_conversation_data = await self.odoo_client.read(
                'ai.conversation',
                [request.conversation_id],
                [
                    'id', 'name', 'description', 'conversation_type', 'ai_model',
                    'priority', 'state', 'user_id', 'context_data', 'max_tokens',
                    'temperature', 'system_prompt', 'tags', 'create_date',
                    'write_date', 'message_count', 'total_tokens', 'total_cost'
                ]
            )
            
            if updated_conversation_data:
                updated_conversation = create_conversation_from_odoo(updated_conversation_data[0])
                
                return UpdateConversationResponse(
                    conversation=updated_conversation,
                    message=f"Conversación {request.conversation_id} actualizada exitosamente"
                )
            else:
                return create_error_response(
                    ErrorTypeEnum.NOT_FOUND,
                    "not_found",
                    "Conversación actualizada pero no se pudo recuperar"
                )
            
        except Exception as e:
            self._logger.error(f"Error actualizando conversación {request.conversation_id}: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "internal_error",
                f"Error interno: {str(e)}"
            )

# Funciones de herramientas individuales

async def create_ai_conversation(
    title: str,
    conversation_type: ConversationType = ConversationType.CONSULTATION,
    ai_model: AIModel = AIModel.GPT_4,
    user_id: Optional[int] = None,
    description: Optional[str] = None,
    priority: Priority = Priority.MEDIUM,
    context: Optional[ConversationContext] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system_prompt: Optional[str] = None,
    tags: Optional[List[str]] = None,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[CreateConversationResponse, ErrorResponse]:
    """Crear una nueva conversación con IA"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            ErrorTypeEnum.VALIDATION_ERROR,
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = ConversationToolsManager(odoo_client, db_client)
    request = CreateConversationRequest(
        title=title,
        conversation_type=conversation_type,
        ai_model=ai_model,
        user_id=user_id,
        description=description,
        priority=priority,
        context=context,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt,
        tags=tags
    )
    
    return await manager.create_conversation(request)

async def send_message_to_conversation(
    conversation_id: int,
    content: str,
    message_type: MessageType = MessageType.TEXT,
    attachments: Optional[List[MessageAttachment]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[SendMessageResponse, ErrorResponse]:
    """Enviar un mensaje a una conversación"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            ErrorTypeEnum.VALIDATION_ERROR,
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = ConversationToolsManager(odoo_client, db_client)
    request = SendMessageRequest(
        conversation_id=conversation_id,
        content=content,
        message_type=message_type,
        attachments=attachments,
        metadata=metadata
    )
    
    return await manager.send_message(request)

async def get_conversation(
    conversation_id: int,
    include_messages: bool = True,
    message_limit: int = 50,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[GetConversationResponse, ErrorResponse]:
    """Obtener una conversación específica"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            ErrorTypeEnum.VALIDATION_ERROR,
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = ConversationToolsManager(odoo_client, db_client)
    request = GetConversationRequest(
        conversation_id=conversation_id,
        include_messages=include_messages,
        message_limit=message_limit
    )
    
    return await manager.get_conversation(request)

async def list_conversations(
    user_id: Optional[int] = None,
    conversation_types: Optional[List[ConversationType]] = None,
    states: Optional[List[ConversationStatus]] = None,
    ai_models: Optional[List[AIModel]] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search_text: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    order_by: Optional[str] = None,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[ListConversationsResponse, ErrorResponse]:
    """Listar conversaciones con filtros"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            ErrorTypeEnum.VALIDATION_ERROR,
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = ConversationToolsManager(odoo_client, db_client)
    request = ListConversationsRequest(
        user_id=user_id,
        conversation_types=conversation_types,
        states=states,
        ai_models=ai_models,
        date_from=date_from,
        date_to=date_to,
        search_text=search_text,
        limit=limit,
        offset=offset,
        order_by=order_by
    )
    
    return await manager.list_conversations(request)

async def update_conversation(
    conversation_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    state: Optional[ConversationStatus] = None,
    priority: Optional[Priority] = None,
    tags: Optional[List[str]] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system_prompt: Optional[str] = None,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[UpdateConversationResponse, ErrorResponse]:
    """Actualizar una conversación"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            ErrorTypeEnum.VALIDATION_ERROR,
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = ConversationToolsManager(odoo_client, db_client)
    request = UpdateConversationRequest(
        conversation_id=conversation_id,
        title=title,
        description=description,
        state=state,
        priority=priority,
        tags=tags,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt
    )
    
    return await manager.update_conversation(request)