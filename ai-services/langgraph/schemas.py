#!/usr/bin/env python3
"""
Esquemas de datos para LangGraph Server - PATCO Suite

Define los modelos Pydantic para el estado de conversación,
mensajes y estructuras de datos del grafo conversacional.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Modelo para mensajes de conversación."""
    
    role: str = Field(..., description="Rol del mensaje (user, assistant, system)")
    content: str = Field(..., description="Contenido del mensaje")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp del mensaje")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos adicionales")
    message_id: Optional[str] = Field(default=None, description="ID único del mensaje")


class ConversationContext(BaseModel):
    """Contexto de la conversación."""
    
    fsm_order_id: Optional[int] = Field(default=None, description="ID de la orden FSM")
    technician_id: Optional[int] = Field(default=None, description="ID del técnico")
    equipment_ids: List[int] = Field(default_factory=list, description="IDs de equipos relacionados")
    equipment_category_id: Optional[int] = Field(default=None, description="ID de categoría de equipo")
    service_nature_id: Optional[int] = Field(default=None, description="ID de naturaleza de servicio")
    service_area_id: Optional[int] = Field(default=None, description="ID de área de servicio")
    location: Optional[str] = Field(default=None, description="Ubicación del servicio")
    customer_id: Optional[int] = Field(default=None, description="ID del cliente")


class ExtractedEntities(BaseModel):
    """Entidades extraídas del mensaje."""
    
    numbers: List[str] = Field(default_factory=list, description="Números mencionados")
    equipment_mentioned: Optional[str] = Field(default=None, description="Equipo mencionado")
    action: Optional[str] = Field(default=None, description="Acción identificada")
    measurements: List[Dict[str, Any]] = Field(default_factory=list, description="Mediciones mencionadas")
    problems: List[str] = Field(default_factory=list, description="Problemas identificados")
    locations: List[str] = Field(default_factory=list, description="Ubicaciones mencionadas")


class RAGResult(BaseModel):
    """Resultado de búsqueda RAG."""
    
    attachment_id: int = Field(..., description="ID del documento")
    content: str = Field(..., description="Contenido del fragmento")
    similarity: float = Field(..., description="Score de similitud")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos del documento")
    document_name: Optional[str] = Field(default=None, description="Nombre del documento")
    document_type: Optional[str] = Field(default=None, description="Tipo de documento")


class ConversationAction(BaseModel):
    """Acción a ejecutar en la conversación."""
    
    action_type: str = Field(..., description="Tipo de acción")
    target: str = Field(..., description="Objetivo de la acción")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros de la acción")
    priority: str = Field(default="normal", description="Prioridad de la acción")
    requires_confirmation: bool = Field(default=False, description="Requiere confirmación del usuario")


class ConversationState(BaseModel):
    """Estado completo de la conversación en LangGraph."""
    
    # Mensajes de la conversación
    messages: List[ConversationMessage] = Field(default_factory=list, description="Historial de mensajes")
    
    # Contexto de la conversación
    context: ConversationContext = Field(default_factory=ConversationContext, description="Contexto de la conversación")
    
    # Estado actual del procesamiento
    current_intent: Optional[str] = Field(default=None, description="Intención actual detectada")
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities, description="Entidades extraídas")
    
    # Resultados de búsqueda RAG
    rag_results: List[RAGResult] = Field(default_factory=list, description="Resultados de búsqueda RAG")
    
    # Respuesta generada
    response: Optional[str] = Field(default=None, description="Respuesta generada")
    
    # Acciones a ejecutar
    actions: List[ConversationAction] = Field(default_factory=list, description="Acciones a ejecutar")
    
    # Estado de la conversación
    conversation_state: str = Field(default="initiated", description="Estado de la conversación")
    
    # Metadatos adicionales
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos de procesamiento")
    
    # Control de flujo
    should_continue: bool = Field(default=True, description="Indica si debe continuar el procesamiento")
    error_message: Optional[str] = Field(default=None, description="Mensaje de error si aplica")


class ProcessMessageRequest(BaseModel):
    """Request para procesar un mensaje."""
    
    conversation_id: str = Field(..., description="ID de la conversación")
    message: ConversationMessage = Field(..., description="Mensaje a procesar")
    context: Optional[ConversationContext] = Field(default=None, description="Contexto adicional")


class ProcessMessageResponse(BaseModel):
    """Response del procesamiento de mensaje."""
    
    conversation_id: str = Field(..., description="ID de la conversación")
    response: Optional[str] = Field(default=None, description="Respuesta generada")
    actions: List[ConversationAction] = Field(default_factory=list, description="Acciones a ejecutar")
    conversation_state: str = Field(..., description="Estado actual de la conversación")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de la respuesta")
    processing_time: Optional[float] = Field(default=None, description="Tiempo de procesamiento en segundos")


class ConversationHistoryResponse(BaseModel):
    """Response del historial de conversación."""
    
    conversation_id: str = Field(..., description="ID de la conversación")
    messages: List[ConversationMessage] = Field(default_factory=list, description="Historial de mensajes")
    state: str = Field(..., description="Estado actual de la conversación")
    context: ConversationContext = Field(default_factory=ConversationContext, description="Contexto de la conversación")


class HealthCheckResponse(BaseModel):
    """Response del health check."""
    
    status: str = Field(..., description="Estado del servicio")
    service: str = Field(..., description="Nombre del servicio")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp del check")
    version: str = Field(default="1.0.0", description="Versión del servicio")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Estado de dependencias")


class MCPToolCall(BaseModel):
    """Llamada a herramienta MCP."""
    
    tool_name: str = Field(..., description="Nombre de la herramienta")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos de la herramienta")
    timeout: int = Field(default=30, description="Timeout en segundos")


class MCPToolResponse(BaseModel):
    """Respuesta de herramienta MCP."""
    
    success: bool = Field(..., description="Indica si la llamada fue exitosa")
    result: Optional[Any] = Field(default=None, description="Resultado de la herramienta")
    error: Optional[str] = Field(default=None, description="Mensaje de error si aplica")
    execution_time: Optional[float] = Field(default=None, description="Tiempo de ejecución")


# Estados válidos de conversación
CONVERSATION_STATES = [
    "initiated",
    "equipment_selected", 
    "checklist_entry",
    "work_in_progress",
    "checklist_exit",
    "report_generated",
    "completed",
    "archived",
    "error"
]

# Intenciones válidas
VALID_INTENTS = [
    "question",
    "action", 
    "status_update",
    "greeting",
    "confirmation",
    "complaint",
    "request_help",
    "other"
]

# Tipos de acciones válidas
ACTION_TYPES = [
    "update_fsm_order",
    "get_equipment_info",
    "search_knowledge_base",
    "create_checklist",
    "generate_report",
    "send_notification",
    "schedule_task"
]