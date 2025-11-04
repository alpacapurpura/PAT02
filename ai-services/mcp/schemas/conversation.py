#!/usr/bin/env python3
"""
Esquemas para herramientas de conversación con IA
Definición de requests y responses para gestión de conversaciones
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseRequest, BaseResponse, BaseConfig, StatusEnum

class ConversationType(str, Enum):
    """Tipos de conversación"""
    SUPPORT = "support"          # Soporte técnico
    CONSULTATION = "consultation" # Consulta general
    TROUBLESHOOTING = "troubleshooting" # Resolución de problemas
    TRAINING = "training"        # Entrenamiento/capacitación
    ANALYSIS = "analysis"        # Análisis de datos
    PLANNING = "planning"        # Planificación
    OTHER = "other"              # Otros

class MessageRole(str, Enum):
    """Roles en la conversación"""
    USER = "user"           # Usuario humano
    ASSISTANT = "assistant" # Asistente IA
    SYSTEM = "system"       # Mensaje del sistema
    TOOL = "tool"           # Resultado de herramienta

class ConversationStatus(str, Enum):
    """Estados de conversación"""
    ACTIVE = "active"       # Conversación activa
    PAUSED = "paused"       # Pausada temporalmente
    COMPLETED = "completed" # Completada exitosamente
    CANCELLED = "cancelled" # Cancelada
    ERROR = "error"         # Error en la conversación

class MessageType(str, Enum):
    """Tipos de mensaje"""
    TEXT = "text"           # Mensaje de texto
    IMAGE = "image"         # Imagen
    FILE = "file"           # Archivo adjunto
    CODE = "code"           # Código
    TOOL_CALL = "tool_call" # Llamada a herramienta
    TOOL_RESULT = "tool_result" # Resultado de herramienta

class Priority(str, Enum):
    """Prioridades de conversación"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AIModel(str, Enum):
    """Modelos de IA disponibles"""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"

class ConversationContext(BaseModel, BaseConfig):
    """Contexto de la conversación"""
    # Contexto del usuario
    user_id: Optional[int] = Field(None, description="ID del usuario")
    user_name: Optional[str] = Field(None, description="Nombre del usuario")
    user_role: Optional[str] = Field(None, description="Rol del usuario")
    company_id: Optional[int] = Field(None, description="ID de la compañía")
    
    # Contexto del negocio
    department: Optional[str] = Field(None, description="Departamento")
    project_id: Optional[int] = Field(None, description="ID del proyecto")
    equipment_id: Optional[int] = Field(None, description="ID del equipo relacionado")
    fsm_order_id: Optional[int] = Field(None, description="ID de orden FSM relacionada")
    
    # Contexto técnico
    session_id: Optional[str] = Field(None, description="ID de sesión")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Información del cliente")
    location: Optional[str] = Field(None, description="Ubicación")
    timezone: Optional[str] = Field(None, description="Zona horaria")
    
    # Preferencias
    language: Optional[str] = Field(None, description="Idioma preferido")
    ai_model: Optional[AIModel] = Field(None, description="Modelo de IA preferido")
    max_tokens: Optional[int] = Field(None, description="Máximo de tokens por respuesta")
    temperature: Optional[float] = Field(None, description="Temperatura del modelo")
    
    # Metadatos adicionales
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Campos personalizados")

class MessageAttachment(BaseModel, BaseConfig):
    """Adjunto de mensaje"""
    id: int = Field(description="ID del adjunto")
    name: str = Field(description="Nombre del archivo")
    file_size: Optional[int] = Field(None, description="Tamaño del archivo")
    mimetype: Optional[str] = Field(None, description="Tipo MIME")
    file_url: Optional[str] = Field(None, description="URL del archivo")
    thumbnail_url: Optional[str] = Field(None, description="URL de miniatura")
    
    # Metadatos del archivo
    width: Optional[int] = Field(None, description="Ancho (para imágenes)")
    height: Optional[int] = Field(None, description="Alto (para imágenes)")
    duration: Optional[float] = Field(None, description="Duración (para audio/video)")
    
    # Procesamiento
    processed: bool = Field(default=False, description="Archivo procesado")
    extracted_text: Optional[str] = Field(None, description="Texto extraído")
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="Resultado del análisis")

class ConversationMessage(BaseModel, BaseConfig):
    """Mensaje de conversación"""
    id: int = Field(description="ID del mensaje")
    conversation_id: int = Field(description="ID de la conversación")
    
    # Contenido del mensaje
    role: MessageRole = Field(description="Rol del emisor")
    message_type: MessageType = Field(description="Tipo de mensaje")
    content: str = Field(description="Contenido del mensaje")
    
    # Metadatos del mensaje
    sequence_number: int = Field(description="Número de secuencia en la conversación")
    parent_message_id: Optional[int] = Field(None, description="ID del mensaje padre (para hilos)")
    
    # Fechas
    create_date: datetime = Field(description="Fecha de creación")
    edit_date: Optional[datetime] = Field(None, description="Fecha de edición")
    
    # Usuario
    user_id: Optional[int] = Field(None, description="ID del usuario")
    user_name: Optional[str] = Field(None, description="Nombre del usuario")
    
    # IA
    ai_model: Optional[AIModel] = Field(None, description="Modelo de IA usado")
    tokens_used: Optional[int] = Field(None, description="Tokens utilizados")
    processing_time_ms: Optional[float] = Field(None, description="Tiempo de procesamiento")
    
    # Adjuntos
    attachments: Optional[List[MessageAttachment]] = Field(None, description="Archivos adjuntos")
    
    # Herramientas
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Llamadas a herramientas")
    tool_results: Optional[List[Dict[str, Any]]] = Field(None, description="Resultados de herramientas")
    
    # Metadatos
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    
    # Estado
    is_edited: bool = Field(default=False, description="Mensaje editado")
    is_deleted: bool = Field(default=False, description="Mensaje eliminado")
    
    # Calificación
    rating: Optional[int] = Field(None, description="Calificación del mensaje (1-5)")
    feedback: Optional[str] = Field(None, description="Comentarios del usuario")

class Conversation(BaseModel, BaseConfig):
    """Conversación con IA"""
    id: int = Field(description="ID de la conversación")
    name: str = Field(description="Nombre de la conversación")
    
    # Tipo y estado
    conversation_type: ConversationType = Field(description="Tipo de conversación")
    status: ConversationStatus = Field(description="Estado de la conversación")
    priority: Priority = Field(default=Priority.MEDIUM, description="Prioridad")
    
    # Descripción
    description: Optional[str] = Field(None, description="Descripción de la conversación")
    summary: Optional[str] = Field(None, description="Resumen de la conversación")
    tags: Optional[List[str]] = Field(None, description="Etiquetas")
    
    # Fechas
    create_date: datetime = Field(description="Fecha de creación")
    start_date: Optional[datetime] = Field(None, description="Fecha de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha de finalización")
    last_activity: Optional[datetime] = Field(None, description="Última actividad")
    
    # Participantes
    user_id: int = Field(description="ID del usuario principal")
    user_name: Optional[str] = Field(None, description="Nombre del usuario")
    participants: Optional[List[int]] = Field(None, description="IDs de otros participantes")
    
    # Configuración de IA
    ai_model: AIModel = Field(description="Modelo de IA usado")
    system_prompt: Optional[str] = Field(None, description="Prompt del sistema")
    temperature: Optional[float] = Field(None, description="Temperatura del modelo")
    max_tokens: Optional[int] = Field(None, description="Máximo de tokens")
    
    # Contexto
    context: Optional[ConversationContext] = Field(None, description="Contexto de la conversación")
    
    # Estadísticas
    message_count: int = Field(default=0, description="Número de mensajes")
    total_tokens: Optional[int] = Field(None, description="Total de tokens utilizados")
    total_cost: Optional[Decimal] = Field(None, description="Costo total")
    
    # Calificación
    rating: Optional[float] = Field(None, description="Calificación promedio")
    feedback_count: int = Field(default=0, description="Número de feedbacks")
    
    # Metadatos
    company_id: Optional[int] = Field(None, description="ID de la compañía")
    department: Optional[str] = Field(None, description="Departamento")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Campos personalizados")
    
    # Estado
    active: bool = Field(default=True, description="Conversación activa")
    archived: bool = Field(default=False, description="Conversación archivada")

# Requests

class CreateConversationRequest(BaseRequest):
    """Request para crear nueva conversación"""
    name: str = Field(
        description="Nombre de la conversación",
        min_length=3,
        max_length=200
    )
    conversation_type: ConversationType = Field(
        description="Tipo de conversación"
    )
    description: Optional[str] = Field(
        None,
        description="Descripción de la conversación",
        max_length=1000
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Prioridad de la conversación"
    )
    
    # Configuración de IA
    ai_model: AIModel = Field(
        default=AIModel.GPT_4,
        description="Modelo de IA a usar"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="Prompt del sistema personalizado",
        max_length=2000
    )
    temperature: Optional[float] = Field(
        None,
        description="Temperatura del modelo",
        ge=0.0,
        le=2.0
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Máximo de tokens por respuesta",
        ge=1,
        le=4000
    )
    
    # Contexto inicial
    context: Optional[ConversationContext] = Field(
        None,
        description="Contexto inicial de la conversación"
    )
    
    # Mensaje inicial
    initial_message: Optional[str] = Field(
        None,
        description="Mensaje inicial de la conversación",
        max_length=5000
    )
    
    # Metadatos
    tags: Optional[List[str]] = Field(
        None,
        description="Etiquetas para la conversación"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        None,
        description="Campos personalizados"
    )

class SendMessageRequest(BaseRequest):
    """Request para enviar mensaje"""
    conversation_id: int = Field(
        description="ID de la conversación",
        gt=0
    )
    content: str = Field(
        description="Contenido del mensaje",
        min_length=1,
        max_length=10000
    )
    message_type: MessageType = Field(
        default=MessageType.TEXT,
        description="Tipo de mensaje"
    )
    
    # Adjuntos
    attachment_ids: Optional[List[int]] = Field(
        None,
        description="IDs de archivos adjuntos"
    )
    
    # Configuración específica para esta respuesta
    ai_model: Optional[AIModel] = Field(
        None,
        description="Modelo de IA específico para esta respuesta"
    )
    temperature: Optional[float] = Field(
        None,
        description="Temperatura específica",
        ge=0.0,
        le=2.0
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Máximo de tokens específico",
        ge=1,
        le=4000
    )
    
    # Herramientas
    enable_tools: bool = Field(
        default=True,
        description="Habilitar uso de herramientas"
    )
    allowed_tools: Optional[List[str]] = Field(
        None,
        description="Herramientas permitidas para esta respuesta"
    )
    
    # Contexto adicional
    context_update: Optional[Dict[str, Any]] = Field(
        None,
        description="Actualización del contexto"
    )
    
    # Metadatos
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos del mensaje"
    )

class GetConversationRequest(BaseRequest):
    """Request para obtener conversación"""
    conversation_id: int = Field(
        description="ID de la conversación",
        gt=0
    )
    include_messages: bool = Field(
        default=True,
        description="Incluir mensajes de la conversación"
    )
    message_limit: Optional[int] = Field(
        None,
        description="Límite de mensajes a incluir",
        ge=1,
        le=100
    )
    include_attachments: bool = Field(
        default=False,
        description="Incluir adjuntos en los mensajes"
    )
    include_context: bool = Field(
        default=True,
        description="Incluir contexto de la conversación"
    )

class ListConversationsRequest(BaseRequest):
    """Request para listar conversaciones"""
    # Filtros
    conversation_type: Optional[ConversationType] = Field(
        None,
        description="Filtrar por tipo de conversación"
    )
    status: Optional[ConversationStatus] = Field(
        None,
        description="Filtrar por estado"
    )
    priority: Optional[Priority] = Field(
        None,
        description="Filtrar por prioridad"
    )
    user_id: Optional[int] = Field(
        None,
        description="Filtrar por usuario"
    )
    
    # Búsqueda por texto
    search_text: Optional[str] = Field(
        None,
        description="Buscar en nombre y descripción"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filtrar por etiquetas"
    )
    
    # Filtros por fecha
    created_from: Optional[date] = Field(
        None,
        description="Fecha de creación desde"
    )
    created_to: Optional[date] = Field(
        None,
        description="Fecha de creación hasta"
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
        default="last_activity",
        description="Campo para ordenar"
    )
    order_direction: Optional[str] = Field(
        default="desc",
        description="Dirección del ordenamiento (asc/desc)"
    )
    
    @validator('order_direction')
    def validate_order_direction(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("order_direction debe ser 'asc' o 'desc'")
        return v.lower()

class UpdateConversationRequest(BaseRequest):
    """Request para actualizar conversación"""
    conversation_id: int = Field(
        description="ID de la conversación",
        gt=0
    )
    
    # Campos actualizables
    name: Optional[str] = Field(
        None,
        description="Nuevo nombre",
        min_length=3,
        max_length=200
    )
    description: Optional[str] = Field(
        None,
        description="Nueva descripción",
        max_length=1000
    )
    status: Optional[ConversationStatus] = Field(
        None,
        description="Nuevo estado"
    )
    priority: Optional[Priority] = Field(
        None,
        description="Nueva prioridad"
    )
    
    # Configuración de IA
    ai_model: Optional[AIModel] = Field(
        None,
        description="Nuevo modelo de IA"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="Nuevo prompt del sistema",
        max_length=2000
    )
    temperature: Optional[float] = Field(
        None,
        description="Nueva temperatura",
        ge=0.0,
        le=2.0
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Nuevo máximo de tokens",
        ge=1,
        le=4000
    )
    
    # Metadatos
    tags: Optional[List[str]] = Field(
        None,
        description="Nuevas etiquetas"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        None,
        description="Campos personalizados actualizados"
    )
    
    # Contexto
    context_update: Optional[Dict[str, Any]] = Field(
        None,
        description="Actualización del contexto"
    )

# Responses

class CreateConversationResponse(BaseResponse):
    """Response de creación de conversación"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: Conversation = Field(
        description="Conversación creada"
    )
    initial_message: Optional[ConversationMessage] = Field(
        None,
        description="Mensaje inicial si se proporcionó"
    )

class SendMessageResponse(BaseResponse):
    """Response de envío de mensaje"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    user_message: ConversationMessage = Field(
        description="Mensaje del usuario enviado"
    )
    ai_response: Optional[ConversationMessage] = Field(
        None,
        description="Respuesta de la IA"
    )
    conversation: Conversation = Field(
        description="Estado actualizado de la conversación"
    )

class GetConversationResponse(BaseResponse):
    """Response de obtención de conversación"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: Conversation = Field(
        description="Datos de la conversación"
    )
    messages: Optional[List[ConversationMessage]] = Field(
        None,
        description="Mensajes de la conversación"
    )

class ListConversationsResponse(BaseResponse):
    """Response de listado de conversaciones"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: List[Conversation] = Field(
        description="Lista de conversaciones"
    )
    total_count: int = Field(
        description="Total de conversaciones que cumplen los filtros"
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

class UpdateConversationResponse(BaseResponse):
    """Response de actualización de conversación"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: Conversation = Field(
        description="Conversación actualizada"
    )

# Funciones de utilidad

def create_conversation_from_odoo_data(
    odoo_data: Dict[str, Any]
) -> Conversation:
    """Crear objeto Conversation desde datos de Odoo"""
    
    # Mapear campos básicos
    conversation_data = {
        'id': odoo_data.get('id'),
        'name': odoo_data.get('name', ''),
        'conversation_type': ConversationType(odoo_data.get('conversation_type', 'support')),
        'status': ConversationStatus(odoo_data.get('status', 'active')),
        'priority': Priority(odoo_data.get('priority', 'medium')),
        'description': odoo_data.get('description'),
        'summary': odoo_data.get('summary'),
        'create_date': odoo_data.get('create_date'),
        'start_date': odoo_data.get('start_date'),
        'end_date': odoo_data.get('end_date'),
        'last_activity': odoo_data.get('last_activity'),
        'user_id': odoo_data.get('user_id'),
        'user_name': odoo_data.get('user_name'),
        'ai_model': AIModel(odoo_data.get('ai_model', 'gpt-4')),
        'system_prompt': odoo_data.get('system_prompt'),
        'temperature': odoo_data.get('temperature'),
        'max_tokens': odoo_data.get('max_tokens'),
        'message_count': odoo_data.get('message_count', 0),
        'total_tokens': odoo_data.get('total_tokens'),
        'total_cost': odoo_data.get('total_cost'),
        'rating': odoo_data.get('rating'),
        'feedback_count': odoo_data.get('feedback_count', 0),
        'company_id': odoo_data.get('company_id'),
        'department': odoo_data.get('department'),
        'active': odoo_data.get('active', True),
        'archived': odoo_data.get('archived', False)
    }
    
    # Procesar tags
    if 'tags' in odoo_data and odoo_data['tags']:
        conversation_data['tags'] = odoo_data['tags'].split(',') if isinstance(odoo_data['tags'], str) else odoo_data['tags']
    
    # Procesar participantes
    if 'participants' in odoo_data and odoo_data['participants']:
        conversation_data['participants'] = odoo_data['participants'] if isinstance(odoo_data['participants'], list) else [odoo_data['participants']]
    
    # Procesar contexto
    if 'context' in odoo_data and odoo_data['context']:
        if isinstance(odoo_data['context'], dict):
            conversation_data['context'] = ConversationContext(**odoo_data['context'])
        elif isinstance(odoo_data['context'], str):
            import json
            try:
                context_dict = json.loads(odoo_data['context'])
                conversation_data['context'] = ConversationContext(**context_dict)
            except (json.JSONDecodeError, TypeError):
                pass
    
    # Procesar campos personalizados
    if 'custom_fields' in odoo_data and odoo_data['custom_fields']:
        if isinstance(odoo_data['custom_fields'], dict):
            conversation_data['custom_fields'] = odoo_data['custom_fields']
        elif isinstance(odoo_data['custom_fields'], str):
            import json
            try:
                conversation_data['custom_fields'] = json.loads(odoo_data['custom_fields'])
            except (json.JSONDecodeError, TypeError):
                pass
    
    return Conversation(**conversation_data)

def create_message_from_odoo_data(
    odoo_data: Dict[str, Any]
) -> ConversationMessage:
    """Crear objeto ConversationMessage desde datos de Odoo"""
    
    # Mapear campos básicos
    message_data = {
        'id': odoo_data.get('id'),
        'conversation_id': odoo_data.get('conversation_id'),
        'role': MessageRole(odoo_data.get('role', 'user')),
        'message_type': MessageType(odoo_data.get('message_type', 'text')),
        'content': odoo_data.get('content', ''),
        'sequence_number': odoo_data.get('sequence_number', 1),
        'parent_message_id': odoo_data.get('parent_message_id'),
        'create_date': odoo_data.get('create_date'),
        'edit_date': odoo_data.get('edit_date'),
        'user_id': odoo_data.get('user_id'),
        'user_name': odoo_data.get('user_name'),
        'ai_model': AIModel(odoo_data.get('ai_model')) if odoo_data.get('ai_model') else None,
        'tokens_used': odoo_data.get('tokens_used'),
        'processing_time_ms': odoo_data.get('processing_time_ms'),
        'is_edited': odoo_data.get('is_edited', False),
        'is_deleted': odoo_data.get('is_deleted', False),
        'rating': odoo_data.get('rating'),
        'feedback': odoo_data.get('feedback')
    }
    
    # Procesar adjuntos
    if 'attachments' in odoo_data and odoo_data['attachments']:
        attachments = []
        for att_data in odoo_data['attachments']:
            if isinstance(att_data, dict):
                attachments.append(MessageAttachment(**att_data))
        message_data['attachments'] = attachments
    
    # Procesar tool calls y results
    if 'tool_calls' in odoo_data and odoo_data['tool_calls']:
        if isinstance(odoo_data['tool_calls'], str):
            import json
            try:
                message_data['tool_calls'] = json.loads(odoo_data['tool_calls'])
            except (json.JSONDecodeError, TypeError):
                pass
        else:
            message_data['tool_calls'] = odoo_data['tool_calls']
    
    if 'tool_results' in odoo_data and odoo_data['tool_results']:
        if isinstance(odoo_data['tool_results'], str):
            import json
            try:
                message_data['tool_results'] = json.loads(odoo_data['tool_results'])
            except (json.JSONDecodeError, TypeError):
                pass
        else:
            message_data['tool_results'] = odoo_data['tool_results']
    
    # Procesar metadatos
    if 'metadata' in odoo_data and odoo_data['metadata']:
        if isinstance(odoo_data['metadata'], dict):
            message_data['metadata'] = odoo_data['metadata']
        elif isinstance(odoo_data['metadata'], str):
            import json
            try:
                message_data['metadata'] = json.loads(odoo_data['metadata'])
            except (json.JSONDecodeError, TypeError):
                pass
    
    return ConversationMessage(**message_data)

def calculate_conversation_cost(
    messages: List[ConversationMessage],
    model_pricing: Optional[Dict[str, Dict[str, float]]] = None
) -> Decimal:
    """Calcular costo total de una conversación"""
    
    if not model_pricing:
        # Precios por defecto (por 1K tokens)
        model_pricing = {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
            'gemini-pro': {'input': 0.0005, 'output': 0.0015}
        }
    
    total_cost = Decimal('0')
    
    for message in messages:
        if message.role == MessageRole.ASSISTANT and message.tokens_used and message.ai_model:
            model_key = message.ai_model.value
            if model_key in model_pricing:
                # Asumir 70% input, 30% output para simplificar
                input_tokens = int(message.tokens_used * 0.7)
                output_tokens = int(message.tokens_used * 0.3)
                
                input_cost = Decimal(str(input_tokens / 1000 * model_pricing[model_key]['input']))
                output_cost = Decimal(str(output_tokens / 1000 * model_pricing[model_key]['output']))
                
                total_cost += input_cost + output_cost
    
    return total_cost

def get_conversation_statistics(
    conversation: Conversation,
    messages: List[ConversationMessage]
) -> Dict[str, Any]:
    """Obtener estadísticas de una conversación"""
    
    stats = {
        'total_messages': len(messages),
        'user_messages': len([m for m in messages if m.role == MessageRole.USER]),
        'assistant_messages': len([m for m in messages if m.role == MessageRole.ASSISTANT]),
        'system_messages': len([m for m in messages if m.role == MessageRole.SYSTEM]),
        'total_tokens': sum(m.tokens_used or 0 for m in messages),
        'avg_response_time': 0,
        'total_attachments': 0,
        'message_types': {},
        'ai_models_used': set(),
        'conversation_duration': None
    }
    
    # Calcular tiempo promedio de respuesta
    response_times = [m.processing_time_ms for m in messages if m.processing_time_ms and m.role == MessageRole.ASSISTANT]
    if response_times:
        stats['avg_response_time'] = sum(response_times) / len(response_times)
    
    # Contar adjuntos
    for message in messages:
        if message.attachments:
            stats['total_attachments'] += len(message.attachments)
    
    # Contar tipos de mensaje
    for message in messages:
        msg_type = message.message_type.value
        stats['message_types'][msg_type] = stats['message_types'].get(msg_type, 0) + 1
    
    # Modelos de IA usados
    for message in messages:
        if message.ai_model:
            stats['ai_models_used'].add(message.ai_model.value)
    
    stats['ai_models_used'] = list(stats['ai_models_used'])
    
    # Duración de la conversación
    if conversation.start_date and conversation.end_date:
        duration = conversation.end_date - conversation.start_date
        stats['conversation_duration'] = duration.total_seconds()
    elif conversation.start_date and messages:
        last_message_date = max(m.create_date for m in messages)
        duration = last_message_date - conversation.start_date
        stats['conversation_duration'] = duration.total_seconds()
    
    return stats