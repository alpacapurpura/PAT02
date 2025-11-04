# ai-services/mcp/tools/base.py
"""
Módulo base para herramientas MCP
Contiene funciones y clases comunes utilizadas por todas las herramientas
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ErrorTypeEnum(Enum):
    """Enumeración de tipos de errores para respuestas MCP"""
    VALIDATION_ERROR = "validation_error"
    CONNECTION_ERROR = "connection_error"
    NOT_FOUND = "not_found"
    PERMISSION_ERROR = "permission_error"
    INTERNAL_ERROR = "internal_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"

def create_error_response(
    error_type: ErrorTypeEnum, 
    message: str, 
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crea una respuesta de error estandarizada para herramientas MCP
    
    Args:
        error_type: Tipo de error de la enumeración ErrorTypeEnum
        message: Mensaje descriptivo del error
        details: Detalles adicionales del error (opcional)
    
    Returns:
        Dict con la estructura de error estandarizada
    """
    error_response = {
        "success": False,
        "error": {
            "type": error_type.value,
            "message": message,
            "timestamp": str(datetime.now().isoformat())
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    logger.error(f"Error {error_type.value}: {message}", extra={"details": details})
    
    return error_response

def create_success_response(
    data: Any, 
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crea una respuesta de éxito estandarizada para herramientas MCP
    
    Args:
        data: Datos de respuesta
        message: Mensaje descriptivo (opcional)
        metadata: Metadatos adicionales (opcional)
    
    Returns:
        Dict con la estructura de éxito estandarizada
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": str(datetime.now().isoformat())
    }
    
    if message:
        response["message"] = message
    
    if metadata:
        response["metadata"] = metadata
    
    return response

def validate_required_fields(
    arguments: Dict[str, Any], 
    required_fields: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Valida que los campos requeridos estén presentes en los argumentos
    
    Args:
        arguments: Diccionario de argumentos a validar
        required_fields: Lista de campos requeridos
    
    Returns:
        None si la validación es exitosa, o Dict con error si falla
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in arguments or arguments[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        return create_error_response(
            ErrorTypeEnum.VALIDATION_ERROR,
            f"Campos requeridos faltantes: {', '.join(missing_fields)}",
            {"missing_fields": missing_fields}
        )
    
    return None

def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitiza una cadena de texto para uso seguro
    
    Args:
        value: Cadena a sanitizar
        max_length: Longitud máxima permitida
    
    Returns:
        Cadena sanitizada
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Remover caracteres de control y espacios extra
    sanitized = ' '.join(value.strip().split())
    
    # Truncar si es necesario
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip()
    
    return sanitized

def format_datetime(dt) -> str:
    """
    Formatea un objeto datetime para respuestas consistentes
    
    Args:
        dt: Objeto datetime o string
    
    Returns:
        String formateado en ISO format
    """
    if dt is None:
        return None
    
    if isinstance(dt, str):
        return dt
    
    try:
        return dt.isoformat()
    except AttributeError:
        return str(dt)