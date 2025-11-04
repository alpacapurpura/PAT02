#!/usr/bin/env python3
"""
Esquemas base para el servidor MCP
Clases base para requests y responses
"""

from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Configuración base para todos los modelos
class BaseConfig:
    """Configuración base para modelos Pydantic"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        extra='forbid',
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

class StatusEnum(str, Enum):
    """Estados posibles para respuestas"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"

class ErrorTypeEnum(str, Enum):
    """Tipos de errores"""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    INTERNAL_ERROR = "internal_error"
    EXTERNAL_API_ERROR = "external_api_error"
    DATABASE_ERROR = "database_error"
    TIMEOUT_ERROR = "timeout_error"

class BaseRequest(BaseModel, BaseConfig):
    """Clase base para todos los requests"""
    request_id: Optional[str] = Field(
        None, 
        description="ID único del request para trazabilidad"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp del request"
    )
    user_id: Optional[int] = Field(
        None,
        description="ID del usuario que hace el request"
    )
    session_id: Optional[str] = Field(
        None,
        description="ID de sesión para contexto"
    )

class BaseResponse(BaseModel, BaseConfig):
    """Clase base para todas las respuestas"""
    status: StatusEnum = Field(
        description="Estado de la respuesta"
    )
    message: Optional[str] = Field(
        None,
        description="Mensaje descriptivo"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de la respuesta"
    )
    request_id: Optional[str] = Field(
        None,
        description="ID del request original"
    )
    execution_time_ms: Optional[float] = Field(
        None,
        description="Tiempo de ejecución en milisegundos"
    )

class ErrorDetail(BaseModel, BaseConfig):
    """Detalle de un error"""
    code: str = Field(
        description="Código del error"
    )
    message: str = Field(
        description="Mensaje del error"
    )
    field: Optional[str] = Field(
        None,
        description="Campo relacionado con el error"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalles adicionales del error"
    )

class ErrorResponse(BaseResponse):
    """Respuesta de error estándar"""
    status: StatusEnum = Field(
        default=StatusEnum.ERROR,
        description="Estado siempre es error"
    )
    error_type: ErrorTypeEnum = Field(
        description="Tipo de error"
    )
    error_code: str = Field(
        description="Código específico del error"
    )
    errors: List[ErrorDetail] = Field(
        default_factory=list,
        description="Lista de errores detallados"
    )
    trace_id: Optional[str] = Field(
        None,
        description="ID de trazabilidad para debugging"
    )

T = TypeVar('T')

class SuccessResponse(BaseResponse, Generic[T]):
    """Respuesta exitosa con datos"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado siempre es success"
    )
    data: T = Field(
        description="Datos de la respuesta"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos adicionales"
    )

class PaginationInfo(BaseModel, BaseConfig):
    """Información de paginación"""
    page: int = Field(
        ge=1,
        description="Página actual (base 1)"
    )
    page_size: int = Field(
        ge=1,
        le=1000,
        description="Tamaño de página"
    )
    total_items: int = Field(
        ge=0,
        description="Total de elementos"
    )
    total_pages: int = Field(
        ge=0,
        description="Total de páginas"
    )
    has_next: bool = Field(
        description="Hay página siguiente"
    )
    has_previous: bool = Field(
        description="Hay página anterior"
    )

class PaginatedResponse(BaseResponse, Generic[T]):
    """Respuesta paginada"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: List[T] = Field(
        description="Lista de elementos"
    )
    pagination: PaginationInfo = Field(
        description="Información de paginación"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos adicionales"
    )

class HealthResponse(BaseModel, BaseConfig):
    """Respuesta del health check"""
    status: str = Field(
        description="Estado del servicio (healthy/unhealthy)"
    )
    version: str = Field(
        description="Versión del servicio"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp del check"
    )
    uptime_seconds: Optional[float] = Field(
        None,
        description="Tiempo activo en segundos"
    )
    services: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Estado de servicios dependientes"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Métricas del sistema"
    )

class ValidationErrorDetail(BaseModel, BaseConfig):
    """Detalle de error de validación"""
    field: str = Field(
        description="Campo con error"
    )
    message: str = Field(
        description="Mensaje del error"
    )
    invalid_value: Any = Field(
        description="Valor inválido"
    )
    constraint: Optional[str] = Field(
        None,
        description="Restricción violada"
    )

class ValidationErrorResponse(ErrorResponse):
    """Respuesta específica para errores de validación"""
    error_type: ErrorTypeEnum = Field(
        default=ErrorTypeEnum.VALIDATION_ERROR,
        description="Tipo siempre es validation_error"
    )
    validation_errors: List[ValidationErrorDetail] = Field(
        default_factory=list,
        description="Errores de validación específicos"
    )

# Funciones de utilidad

def create_success_response(
    data: T,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
    execution_time_ms: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> SuccessResponse[T]:
    """Crear respuesta exitosa"""
    return SuccessResponse(
        data=data,
        message=message,
        request_id=request_id,
        execution_time_ms=execution_time_ms,
        metadata=metadata
    )

def create_error_response(
    error_type: ErrorTypeEnum,
    error_code: str,
    message: str,
    errors: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None
) -> ErrorResponse:
    """Crear respuesta de error"""
    return ErrorResponse(
        error_type=error_type,
        error_code=error_code,
        message=message,
        errors=errors or [],
        request_id=request_id,
        trace_id=trace_id
    )

def create_validation_error_response(
    message: str,
    validation_errors: List[ValidationErrorDetail],
    request_id: Optional[str] = None
) -> ValidationErrorResponse:
    """Crear respuesta de error de validación"""
    return ValidationErrorResponse(
        error_code="VALIDATION_FAILED",
        message=message,
        validation_errors=validation_errors,
        request_id=request_id
    )

def create_paginated_response(
    data: List[T],
    page: int,
    page_size: int,
    total_items: int,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> PaginatedResponse[T]:
    """Crear respuesta paginada"""
    total_pages = (total_items + page_size - 1) // page_size
    
    pagination = PaginationInfo(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    
    return PaginatedResponse(
        data=data,
        pagination=pagination,
        message=message,
        request_id=request_id,
        metadata=metadata
    )

# Validadores personalizados

def validate_positive_int(value: int) -> int:
    """Validar que un entero sea positivo"""
    if value <= 0:
        raise ValueError("El valor debe ser positivo")
    return value

def validate_non_empty_string(value: str) -> str:
    """Validar que una cadena no esté vacía"""
    if not value or not value.strip():
        raise ValueError("La cadena no puede estar vacía")
    return value.strip()

def validate_email(value: str) -> str:
    """Validar formato de email básico"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        raise ValueError("Formato de email inválido")
    return value.lower()