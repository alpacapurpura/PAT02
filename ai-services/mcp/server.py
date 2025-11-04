#!/usr/bin/env python3
"""
Servidor MCP (Model Context Protocol) para PATCO Suite

Este servidor implementa el protocolo MCP usando JSON-RPC 2.0 para proporcionar
herramientas de FSM, equipos, RAG y conversaciones IA a través de una API unificada.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import json
import logging
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from config import settings
from schemas.base import ErrorResponse, HealthResponse, SuccessResponse, ErrorTypeEnum, ErrorDetail, create_error_response
from schemas.mcp import (
    MCPError,
    MCPErrorCode,
    MCPMethodEnum,
    MCPRequest,
    MCPResponse,
    create_mcp_error_response,
    create_mcp_success_response,
    validate_mcp_request,
)
from tools import TOOL_REGISTRY, get_tool_function
from utils.auth import AuthManager
from utils.db_client import DatabaseClient
from utils.logging_config import setup_logging
from utils.odoo_client import OdooClient
from utils.rate_limiter import RateLimiter

# Configurar logging
logger = setup_logging(__name__)

# Encoder JSON personalizado para datetime
class CustomJSONEncoder(json.JSONEncoder):
    """Encoder JSON personalizado que maneja objetos datetime."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def create_json_response(content: Any, status_code: int = 200) -> JSONResponse:
    """Crear respuesta JSON con encoder personalizado."""
    return JSONResponse(
        status_code=status_code,
        content=json.loads(json.dumps(content, cls=CustomJSONEncoder))
    )

# Instancias globales
auth_manager: Optional[AuthManager] = None
db_client: Optional[DatabaseClient] = None
odoo_client: Optional[OdooClient] = None
rate_limiter: Optional[RateLimiter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación."""
    global auth_manager, db_client, odoo_client, rate_limiter
    
    logger.info("🚀 Iniciando servidor MCP...")
    
    try:
        # Inicializar clientes
        logger.info("📊 Inicializando cliente de base de datos...")
        db_client = DatabaseClient(settings.get_database_url())
        await db_client.connect()
        
        logger.info("🔗 Inicializando cliente Odoo...")
        odoo_client = OdooClient(
            url=settings.ODOO_URL,
            db=settings.ODOO_DB,
            username=settings.ODOO_USERNAME,
            password=settings.ODOO_PASSWORD
        )
        await odoo_client.authenticate()
        
        logger.info("🔐 Inicializando gestor de autenticación...")
        auth_manager = AuthManager()
        
        logger.info("⏱️ Inicializando rate limiter...")
        rate_limiter = RateLimiter()
        
        logger.info("✅ Servidor MCP iniciado correctamente")
        logger.info(f"🌐 Servidor disponible en: http://{settings.MCP_HOST}:{settings.MCP_PORT}")
        logger.info(f"📋 Herramientas disponibles: {len(TOOL_REGISTRY)}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error durante la inicialización: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🔄 Cerrando conexiones...")
        
        if db_client:
            await db_client.disconnect()
            
        if odoo_client:
            # OdooClient no tiene método disconnect, solo necesita limpiar estado
            odoo_client.is_authenticated = False
            
        logger.info("👋 Servidor MCP detenido")


# Crear aplicación FastAPI
app = FastAPI(
    title="PATCO MCP Server",
    description="Servidor MCP (Model Context Protocol) para herramientas FSM, equipos, RAG y conversaciones IA",
    version="1.0.0",
    docs_url="/docs" if settings.MCP_DEBUG else None,
    redoc_url="/redoc" if settings.MCP_DEBUG else None,
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware de hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.MCP_DEBUG else ["localhost", "127.0.0.1"]
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware para rate limiting."""
    if rate_limiter:
        client_ip = str(request.client.host) if request.client else None
        allowed, statuses = await rate_limiter.check_limits(client_ip=client_ip)
        
        if not allowed:
            # Obtener headers de rate limiting
            headers = rate_limiter.get_limit_headers(statuses)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded", "details": statuses},
                headers=headers
            )
    
    response = await call_next(request)
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware para logging de requests."""
    start_time = asyncio.get_event_loop().time()
    
    # Log request
    logger.info(
        f"📥 {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = asyncio.get_event_loop().time() - start_time
    logger.info(
        f"📤 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Manejador de errores de validación."""
    logger.error(f"❌ Error de validación: {exc}")
    error_response = ErrorResponse(
        error_type=ErrorTypeEnum.VALIDATION_ERROR,
        error_code="VALIDATION_FAILED",
        message=str(exc),
        errors=[ErrorDetail(code="validation_error", message=str(error)) for error in exc.errors()]
    )
    return create_json_response(error_response.model_dump(), status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador general de excepciones."""
    logger.error(f"❌ Error interno del servidor: {exc}", exc_info=True)
    error_response = create_error_response(
        error_type=ErrorTypeEnum.INTERNAL_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message="Ha ocurrido un error interno del servidor"
    )
    return create_json_response(error_response.model_dump(), status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===== ENDPOINTS DE SALUD Y ESTADO =====

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de health check."""
    try:
        # Verificar conexiones
        db_status = "connected" if db_client and db_client.is_connected else "disconnected"
        odoo_status = "connected" if odoo_client and odoo_client.is_authenticated else "disconnected"
        
        health_response = HealthResponse(
            status="healthy",
            services={
                "database": {"status": db_status, "type": "postgresql"},
                "odoo": {"status": odoo_status, "type": "xmlrpc"},
                "auth": {"status": "active" if auth_manager else "inactive", "type": "jwt"},
                "rate_limiter": {"status": "active" if rate_limiter else "inactive", "type": "sliding_window"}
            },
            version="1.0.0"
        )
        return create_json_response(health_response.model_dump())
    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        error_response = HealthResponse(
            status="unhealthy",
            services={"error": {"status": "error", "message": str(e), "type": "exception"}},
            version="1.0.0"
        )
        return create_json_response(error_response.model_dump())


@app.get("/tools", response_model=SuccessResponse)
async def list_tools():
    """Listar todas las herramientas MCP disponibles."""
    try:
        tools_info = []
        for tool_name in TOOL_REGISTRY.keys():
            tools_info.append({
                "name": tool_name,
                "description": f"Herramienta {tool_name}",
                "category": "general",
                "available": True
            })
        
        success_response = SuccessResponse(
            message="Herramientas MCP obtenidas correctamente",
            data={
                "tools": tools_info,
                "total": len(tools_info)
            }
        )
        return create_json_response(success_response.model_dump())
    except Exception as e:
        logger.error(f"❌ Error al listar herramientas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener las herramientas"
        )


# ===== ENDPOINT PRINCIPAL MCP =====

@app.post("/mcp", response_model=MCPResponse)
async def mcp_endpoint(request: MCPRequest) -> MCPResponse:
    """Endpoint principal para el protocolo MCP usando JSON-RPC 2.0."""
    try:
        # El request ya está validado por FastAPI/Pydantic
        # No necesitamos validación adicional aquí
        
        # Log del request
        logger.info(f"🔧 Ejecutando herramienta MCP: {request.method}")
        
        # Obtener función de la herramienta
        tool_function = get_tool_function(request.method)
        if not tool_function:
            error_response = create_mcp_error_response(
                request_id=request.id,
                error_code=MCPErrorCode.METHOD_NOT_FOUND,
                message=f"Método no encontrado: {request.method}"
            )
            return create_json_response(error_response.model_dump())
        
        # Ejecutar herramienta
        try:
            # Preparar parámetros para la función
            params = request.params or {}
            
            # Agregar clientes como parámetros
            params['odoo_client'] = odoo_client
            params['db_client'] = db_client
            
            # Ejecutar función con parámetros desempaquetados
            result = await tool_function(**params)
            
            success_response = create_mcp_success_response(
                request_id=request.id,
                result=result
            )
            return create_json_response(success_response.model_dump())
            
        except Exception as tool_error:
            logger.error(f"❌ Error en herramienta {request.method}: {tool_error}")
            error_response = create_mcp_error_response(
                request_id=request.id,
                error_code=MCPErrorCode.TOOL_EXECUTION_ERROR,
                message=f"Error ejecutando {request.method}: {str(tool_error)}"
            )
            return create_json_response(error_response.model_dump())
    
    except Exception as e:
        logger.error(f"❌ Error en endpoint MCP: {e}", exc_info=True)
        error_response = create_mcp_error_response(
            request_id=getattr(request, 'id', None),
            error_code=MCPErrorCode.INTERNAL_ERROR,
            message="Error interno del servidor"
        )
        return create_json_response(error_response.model_dump())


# ===== MANEJO DE SEÑALES =====

def signal_handler(signum, frame):
    """Manejador de señales para graceful shutdown."""
    logger.info(f"📡 Señal recibida: {signum}")
    logger.info("🔄 Iniciando graceful shutdown...")
    sys.exit(0)


# Registrar manejadores de señales
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ===== FUNCIÓN PRINCIPAL =====

def main():
    """Función principal para iniciar el servidor."""
    logger.info("🎯 Iniciando servidor MCP PATCO...")
    logger.info(f"📍 Host: {settings.MCP_HOST}")
    logger.info(f"🔌 Puerto: {settings.MCP_PORT}")
    logger.info(f"🐛 Debug: {settings.MCP_DEBUG}")
    logger.info(f"📊 Log Level: {settings.MCP_LOG_LEVEL}")
    
    try:
        uvicorn.run(
            "server:app",
            host=settings.MCP_HOST,
            port=settings.MCP_PORT,
            log_level=settings.MCP_LOG_LEVEL.lower(),
            reload=settings.MCP_DEBUG,
            workers=1,  # MCP requiere un solo worker para mantener estado
            access_log=settings.MCP_DEBUG,
            server_header=False,
            date_header=False
        )
    except Exception as e:
        logger.error(f"❌ Error al iniciar el servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()