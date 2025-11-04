#!/usr/bin/env python3
"""
Configuración de Logging para Servidor MCP

Este módulo proporciona configuración centralizada de logging para el servidor MCP,
incluyendo formatters personalizados, handlers para diferentes niveles de log,
y configuración específica para desarrollo y producción.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger

from config import settings


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para desarrollo."""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Formatear el registro con colores."""
        if not hasattr(record, 'color'):
            record.color = self.COLORS.get(record.levelname, '')
            record.reset = self.COLORS['RESET']
        
        return super().format(record)


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON estructurado para producción."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """Agregar campos adicionales al log."""
        super().add_fields(log_record, record, message_dict)
        
        # Agregar timestamp ISO
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Agregar información del servidor
        log_record['service'] = 'mcp-server'
        log_record['version'] = getattr(settings, 'VERSION', '1.0.0')
        
        # Agregar información del proceso
        log_record['process_id'] = os.getpid()
        
        # Agregar información de contexto si está disponible
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        if hasattr(record, 'session_id'):
            log_record['session_id'] = record.session_id
        
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        if hasattr(record, 'tool_name'):
            log_record['tool_name'] = record.tool_name
        
        if hasattr(record, 'execution_time'):
            log_record['execution_time_ms'] = record.execution_time


class MCPLoggerAdapter(logging.LoggerAdapter):
    """Adapter para agregar contexto automáticamente a los logs."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Procesar el mensaje y kwargs antes del logging."""
        # Agregar contexto del adapter
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        
        return msg, kwargs


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    enable_json_logging: bool = False,
    enable_file_logging: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Configurar el sistema de logging.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directorio para archivos de log
        enable_json_logging: Habilitar logging JSON estructurado
        enable_file_logging: Habilitar logging a archivos
        max_file_size: Tamaño máximo de archivo de log en bytes
        backup_count: Número de archivos de backup a mantener
    
    Returns:
        Logger configurado
    """
    # Configurar nivel de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Crear directorio de logs si no existe
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    else:
        log_dir = settings.LOG_DIR
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # === CONFIGURAR HANDLER DE CONSOLA ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    if enable_json_logging:
        # Formato JSON para producción
        console_formatter = StructuredFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Formato con colores para desarrollo
        console_formatter = ColoredFormatter(
            fmt='%(color)s%(asctime)s [%(levelname)8s] %(name)s: %(message)s%(reset)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # === CONFIGURAR HANDLER DE ARCHIVO ===
    if enable_file_logging:
        # Log general
        general_log_file = os.path.join(log_dir, 'mcp-server.log')
        file_handler = logging.handlers.RotatingFileHandler(
            general_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        if enable_json_logging:
            file_formatter = StructuredFormatter(
                fmt='%(timestamp)s %(level)s %(name)s %(message)s'
            )
        else:
            file_formatter = logging.Formatter(
                fmt='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Log de errores separado
        error_log_file = os.path.join(log_dir, 'mcp-server-errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        
        # Log de acceso/audit
        access_log_file = os.path.join(log_dir, 'mcp-server-access.log')
        access_handler = logging.handlers.RotatingFileHandler(
            access_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(file_formatter)
        
        # Crear logger específico para acceso
        access_logger = logging.getLogger('mcp.access')
        access_logger.addHandler(access_handler)
        access_logger.propagate = False
    
    # === CONFIGURAR LOGGERS ESPECÍFICOS ===
    
    # Reducir verbosidad de librerías externas
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Configurar logger principal del MCP
    mcp_logger = logging.getLogger('mcp')
    mcp_logger.setLevel(numeric_level)
    
    return mcp_logger


def setup_structlog():
    """Configurar structlog para logging estructurado."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str, **context) -> MCPLoggerAdapter:
    """Obtener un logger con contexto.
    
    Args:
        name: Nombre del logger
        **context: Contexto adicional para incluir en todos los logs
    
    Returns:
        Logger adapter con contexto
    """
    logger = logging.getLogger(name)
    return MCPLoggerAdapter(logger, context)


def log_request(logger: logging.Logger, method: str, path: str, status_code: int, 
                execution_time: float, user_id: Optional[int] = None,
                session_id: Optional[str] = None, request_id: Optional[str] = None):
    """Log de request HTTP/MCP.
    
    Args:
        logger: Logger a usar
        method: Método HTTP o nombre de herramienta MCP
        path: Path del endpoint o nombre de la herramienta
        status_code: Código de estado HTTP o código de resultado MCP
        execution_time: Tiempo de ejecución en milisegundos
        user_id: ID del usuario (opcional)
        session_id: ID de sesión (opcional)
        request_id: ID de request (opcional)
    """
    extra = {
        'method': method,
        'path': path,
        'status_code': status_code,
        'execution_time': execution_time
    }
    
    if user_id:
        extra['user_id'] = user_id
    if session_id:
        extra['session_id'] = session_id
    if request_id:
        extra['request_id'] = request_id
    
    # Determinar nivel de log basado en status code
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO
    
    logger.log(
        level,
        f"{method} {path} - {status_code} ({execution_time:.2f}ms)",
        extra=extra
    )


def log_tool_execution(logger: logging.Logger, tool_name: str, success: bool,
                      execution_time: float, user_id: Optional[int] = None,
                      error: Optional[str] = None, **kwargs):
    """Log de ejecución de herramienta MCP.
    
    Args:
        logger: Logger a usar
        tool_name: Nombre de la herramienta
        success: Si la ejecución fue exitosa
        execution_time: Tiempo de ejecución en milisegundos
        user_id: ID del usuario (opcional)
        error: Mensaje de error (opcional)
        **kwargs: Contexto adicional
    """
    extra = {
        'tool_name': tool_name,
        'success': success,
        'execution_time': execution_time
    }
    
    if user_id:
        extra['user_id'] = user_id
    if error:
        extra['error'] = error
    
    extra.update(kwargs)
    
    if success:
        logger.info(
            f"Tool '{tool_name}' executed successfully ({execution_time:.2f}ms)",
            extra=extra
        )
    else:
        logger.error(
            f"Tool '{tool_name}' failed: {error} ({execution_time:.2f}ms)",
            extra=extra
        )


def log_auth_event(logger: logging.Logger, event_type: str, user_id: Optional[int] = None,
                  username: Optional[str] = None, success: bool = True,
                  client_ip: Optional[str] = None, error: Optional[str] = None):
    """Log de evento de autenticación.
    
    Args:
        logger: Logger a usar
        event_type: Tipo de evento (login, logout, token_refresh, etc.)
        user_id: ID del usuario (opcional)
        username: Nombre de usuario (opcional)
        success: Si el evento fue exitoso
        client_ip: IP del cliente (opcional)
        error: Mensaje de error (opcional)
    """
    extra = {
        'event_type': event_type,
        'success': success
    }
    
    if user_id:
        extra['user_id'] = user_id
    if username:
        extra['username'] = username
    if client_ip:
        extra['client_ip'] = client_ip
    if error:
        extra['error'] = error
    
    level = logging.INFO if success else logging.WARNING
    message = f"Auth event '{event_type}'"
    
    if username:
        message += f" for user '{username}'"
    if not success and error:
        message += f": {error}"
    
    logger.log(level, message, extra=extra)


def configure_logging_for_environment():
    """Configurar logging basado en el entorno."""
    if settings.ENVIRONMENT == "development":
        # Desarrollo: logs coloridos en consola, archivos opcionales
        setup_logging(
            log_level=settings.LOG_LEVEL,
            log_dir=settings.LOG_DIR,
            enable_json_logging=False,
            enable_file_logging=True
        )
    elif settings.ENVIRONMENT == "production":
        # Producción: logs JSON estructurados
        setup_logging(
            log_level=settings.LOG_LEVEL,
            log_dir=settings.LOG_DIR,
            enable_json_logging=True,
            enable_file_logging=True
        )
        setup_structlog()
    else:
        # Testing u otros: logs mínimos
        setup_logging(
            log_level="WARNING",
            enable_file_logging=False
        )


# Configurar logging al importar el módulo
if __name__ != "__main__":
    configure_logging_for_environment()


# Logger principal del módulo
_logger = get_logger(__name__)