#!/usr/bin/env python3
"""
Utilidades para Servidor MCP

Este paquete contiene módulos de utilidades para el servidor MCP,
incluyendo clientes de base de datos, autenticación, logging y más.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

from .auth import AuthManager
from .db_client import DatabaseClient
from .logging_config import (
    configure_logging_for_environment,
    get_logger,
    log_auth_event,
    log_request,
    log_tool_execution,
    setup_logging,
    setup_structlog,
)
from .odoo_client import OdooClient
from .rate_limiter import RateLimiter, rate_limiter

__all__ = [
    "AuthManager",
    "DatabaseClient",
    "OdooClient",
    "RateLimiter",
    "rate_limiter",
    "configure_logging_for_environment",
    "get_logger",
    "log_auth_event",
    "log_request",
    "log_tool_execution",
    "setup_logging",
    "setup_structlog",
]