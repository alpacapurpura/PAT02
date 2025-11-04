#!/usr/bin/env python3
"""
Esquemas para el protocolo MCP (Model Context Protocol)
Definición de requests, responses y estructuras MCP
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseRequest, BaseResponse, BaseConfig, StatusEnum

class MCPMethodEnum(str, Enum):
    """Métodos disponibles en el protocolo MCP"""
    # Métodos de herramientas
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    
    # Métodos de recursos
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    
    # Métodos de prompts
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    
    # Métodos de logging
    LOGGING_SET_LEVEL = "logging/setLevel"
    
    # Métodos personalizados para FSM
    FSM_GET_ORDER = "fsm/get_order"
    FSM_UPDATE_ORDER = "fsm/update_order"
    FSM_LIST_ORDERS = "fsm/list_orders"
    
    # Métodos para equipos
    EQUIPMENT_GET_INFO = "equipment/get_info"
    EQUIPMENT_LIST = "equipment/list"
    EQUIPMENT_SEARCH = "equipment/search"
    
    # Métodos para base de conocimiento
    KNOWLEDGE_SEARCH = "knowledge/search"
    KNOWLEDGE_GET_DOCUMENT = "knowledge/get_document"
    
    # Métodos para conversaciones IA
    CONVERSATION_CREATE = "conversation/create"
    CONVERSATION_MESSAGE = "conversation/message"
    CONVERSATION_LIST = "conversation/list"

class MCPToolType(str, Enum):
    """Tipos de herramientas MCP"""
    FUNCTION = "function"
    RESOURCE = "resource"
    PROMPT = "prompt"

class MCPParameterType(str, Enum):
    """Tipos de parámetros MCP"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

class MCPParameter(BaseModel, BaseConfig):
    """Parámetro de una herramienta MCP"""
    name: str = Field(
        description="Nombre del parámetro"
    )
    type: MCPParameterType = Field(
        description="Tipo del parámetro"
    )
    description: str = Field(
        description="Descripción del parámetro"
    )
    required: bool = Field(
        default=False,
        description="Si el parámetro es requerido"
    )
    default: Optional[Any] = Field(
        None,
        description="Valor por defecto"
    )
    enum: Optional[List[Any]] = Field(
        None,
        description="Valores permitidos"
    )
    minimum: Optional[Union[int, float]] = Field(
        None,
        description="Valor mínimo para números"
    )
    maximum: Optional[Union[int, float]] = Field(
        None,
        description="Valor máximo para números"
    )
    pattern: Optional[str] = Field(
        None,
        description="Patrón regex para strings"
    )

class MCPTool(BaseModel, BaseConfig):
    """Definición de una herramienta MCP"""
    name: str = Field(
        description="Nombre único de la herramienta"
    )
    type: MCPToolType = Field(
        default=MCPToolType.FUNCTION,
        description="Tipo de herramienta"
    )
    description: str = Field(
        description="Descripción de la herramienta"
    )
    parameters: List[MCPParameter] = Field(
        default_factory=list,
        description="Parámetros de la herramienta"
    )
    returns: Optional[str] = Field(
        None,
        description="Descripción de lo que retorna"
    )
    examples: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Ejemplos de uso"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Tags para categorización"
    )
    version: Optional[str] = Field(
        None,
        description="Versión de la herramienta"
    )

class MCPToolCall(BaseModel, BaseConfig):
    """Llamada a una herramienta MCP"""
    tool: str = Field(
        description="Nombre de la herramienta a llamar"
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Argumentos para la herramienta"
    )
    call_id: Optional[str] = Field(
        None,
        description="ID único de la llamada"
    )
    timeout: Optional[int] = Field(
        None,
        description="Timeout en segundos"
    )

class MCPResult(BaseModel, BaseConfig):
    """Resultado de una herramienta MCP"""
    success: bool = Field(
        description="Si la ejecución fue exitosa"
    )
    result: Optional[Any] = Field(
        None,
        description="Resultado de la herramienta"
    )
    error: Optional[str] = Field(
        None,
        description="Mensaje de error si falló"
    )
    error_code: Optional[str] = Field(
        None,
        description="Código de error"
    )
    execution_time_ms: Optional[float] = Field(
        None,
        description="Tiempo de ejecución en ms"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos adicionales"
    )

class MCPRequest(BaseRequest):
    """Request MCP estándar"""
    method: MCPMethodEnum = Field(
        description="Método MCP a ejecutar"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parámetros del método"
    )
    id: Optional[str] = Field(
        None,
        description="ID del request JSON-RPC"
    )
    jsonrpc: str = Field(
        default="2.0",
        description="Versión JSON-RPC"
    )
    
    @validator('jsonrpc')
    def validate_jsonrpc_version(cls, v):
        if v != "2.0":
            raise ValueError("Solo se soporta JSON-RPC 2.0")
        return v

class MCPResponse(BaseResponse):
    """Response MCP estándar"""
    id: Optional[str] = Field(
        None,
        description="ID del request original"
    )
    jsonrpc: str = Field(
        default="2.0",
        description="Versión JSON-RPC"
    )
    result: Optional[Any] = Field(
        None,
        description="Resultado del método"
    )
    error: Optional[Dict[str, Any]] = Field(
        None,
        description="Error JSON-RPC si ocurrió"
    )

class MCPToolsListRequest(MCPRequest):
    """Request para listar herramientas disponibles"""
    method: MCPMethodEnum = Field(
        default=MCPMethodEnum.TOOLS_LIST,
        description="Método siempre es tools/list"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parámetros vacíos para list"
    )

class MCPToolsListResponse(MCPResponse):
    """Response con lista de herramientas"""
    result: Dict[str, List[MCPTool]] = Field(
        description="Lista de herramientas disponibles"
    )

class MCPToolsCallRequest(MCPRequest):
    """Request para llamar una herramienta"""
    method: MCPMethodEnum = Field(
        default=MCPMethodEnum.TOOLS_CALL,
        description="Método siempre es tools/call"
    )
    params: Dict[str, Any] = Field(
        description="Parámetros de la herramienta"
    )
    
    @validator('params')
    def validate_tool_call_params(cls, v):
        if 'name' not in v:
            raise ValueError("El parámetro 'name' es requerido")
        if 'arguments' not in v:
            v['arguments'] = {}
        return v

class MCPToolsCallResponse(MCPResponse):
    """Response de llamada a herramienta"""
    result: MCPResult = Field(
        description="Resultado de la herramienta"
    )

class MCPErrorCode(str, Enum):
    """Códigos de error MCP estándar"""
    PARSE_ERROR = "-32700"
    INVALID_REQUEST = "-32600"
    METHOD_NOT_FOUND = "-32601"
    INVALID_PARAMS = "-32602"
    INTERNAL_ERROR = "-32603"
    
    # Errores personalizados
    TOOL_NOT_FOUND = "-32001"
    TOOL_EXECUTION_ERROR = "-32002"
    AUTHENTICATION_ERROR = "-32003"
    AUTHORIZATION_ERROR = "-32004"
    RATE_LIMIT_ERROR = "-32005"
    TIMEOUT_ERROR = "-32006"

class MCPError(BaseModel, BaseConfig):
    """Error MCP estándar"""
    code: MCPErrorCode = Field(
        description="Código de error"
    )
    message: str = Field(
        description="Mensaje de error"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Datos adicionales del error"
    )

class MCPErrorResponse(MCPResponse):
    """Response de error MCP"""
    status: StatusEnum = Field(
        default=StatusEnum.ERROR,
        description="Estado siempre es error"
    )
    error: MCPError = Field(
        description="Detalles del error"
    )
    result: Optional[Any] = Field(
        default=None,
        description="Result es null en errores"
    )

# Funciones de utilidad para MCP

def create_mcp_success_response(
    request_id: Optional[str],
    result: Any,
    execution_time_ms: Optional[float] = None
) -> MCPResponse:
    """Crear respuesta MCP exitosa"""
    return MCPResponse(
        id=request_id,
        status=StatusEnum.SUCCESS,
        result=result,
        execution_time_ms=execution_time_ms
    )

def create_mcp_error_response(
    request_id: Optional[str],
    error_code: MCPErrorCode,
    message: str,
    data: Optional[Dict[str, Any]] = None
) -> MCPErrorResponse:
    """Crear respuesta MCP de error"""
    return MCPErrorResponse(
        id=request_id,
        error=MCPError(
            code=error_code,
            message=message,
            data=data
        )
    )

def create_mcp_tool_result(
    success: bool,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    error_code: Optional[str] = None,
    execution_time_ms: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> MCPResult:
    """Crear resultado de herramienta MCP"""
    return MCPResult(
        success=success,
        result=result,
        error=error,
        error_code=error_code,
        execution_time_ms=execution_time_ms,
        metadata=metadata
    )

def validate_mcp_request(request_data: Dict[str, Any]) -> MCPRequest:
    """Validar y parsear request MCP"""
    try:
        return MCPRequest(**request_data)
    except Exception as e:
        raise ValueError(f"Request MCP inválido: {str(e)}")

def get_available_tools() -> List[MCPTool]:
    """Obtener lista de herramientas MCP disponibles"""
    return [
        # Herramientas FSM
        MCPTool(
            name="get_fsm_order",
            description="Obtener información de una orden de servicio FSM",
            parameters=[
                MCPParameter(
                    name="order_id",
                    type=MCPParameterType.INTEGER,
                    description="ID de la orden FSM",
                    required=True
                ),
                MCPParameter(
                    name="include_tasks",
                    type=MCPParameterType.BOOLEAN,
                    description="Incluir tareas de la orden",
                    default=False
                )
            ],
            returns="Información completa de la orden FSM",
            tags=["fsm", "orders"]
        ),
        
        MCPTool(
            name="update_fsm_order",
            description="Actualizar una orden de servicio FSM",
            parameters=[
                MCPParameter(
                    name="order_id",
                    type=MCPParameterType.INTEGER,
                    description="ID de la orden FSM",
                    required=True
                ),
                MCPParameter(
                    name="updates",
                    type=MCPParameterType.OBJECT,
                    description="Campos a actualizar",
                    required=True
                )
            ],
            returns="Orden FSM actualizada",
            tags=["fsm", "orders", "update"]
        ),
        
        # Herramientas de equipos
        MCPTool(
            name="get_equipment_info",
            description="Obtener información de un equipo",
            parameters=[
                MCPParameter(
                    name="equipment_id",
                    type=MCPParameterType.INTEGER,
                    description="ID del equipo",
                    required=True
                ),
                MCPParameter(
                    name="include_maintenance",
                    type=MCPParameterType.BOOLEAN,
                    description="Incluir historial de mantenimiento",
                    default=False
                )
            ],
            returns="Información completa del equipo",
            tags=["equipment", "maintenance"]
        ),
        
        # Herramientas de conocimiento
        MCPTool(
            name="search_knowledge_base",
            description="Buscar en la base de conocimiento usando RAG",
            parameters=[
                MCPParameter(
                    name="query",
                    type=MCPParameterType.STRING,
                    description="Consulta de búsqueda",
                    required=True
                ),
                MCPParameter(
                    name="max_results",
                    type=MCPParameterType.INTEGER,
                    description="Máximo número de resultados",
                    default=10,
                    minimum=1,
                    maximum=50
                ),
                MCPParameter(
                    name="similarity_threshold",
                    type=MCPParameterType.NUMBER,
                    description="Umbral de similitud",
                    default=0.7,
                    minimum=0.0,
                    maximum=1.0
                )
            ],
            returns="Documentos relevantes de la base de conocimiento",
            tags=["knowledge", "rag", "search"]
        ),
        
        # Herramientas de conversación
        MCPTool(
            name="create_ai_conversation",
            description="Crear una nueva conversación con el agente IA",
            parameters=[
                MCPParameter(
                    name="fsm_order_id",
                    type=MCPParameterType.INTEGER,
                    description="ID de la orden FSM relacionada",
                    required=True
                ),
                MCPParameter(
                    name="initial_message",
                    type=MCPParameterType.STRING,
                    description="Mensaje inicial",
                    required=True
                ),
                MCPParameter(
                    name="context",
                    type=MCPParameterType.OBJECT,
                    description="Contexto adicional",
                    required=False
                )
            ],
            returns="Nueva conversación creada",
            tags=["conversation", "ai", "chat"]
        )
    ]