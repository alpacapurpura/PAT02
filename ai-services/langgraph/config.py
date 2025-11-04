#!/usr/bin/env python3
"""
Configuración del Servidor LangGraph para PATCO Suite

Este módulo centraliza la configuración del servidor LangGraph para
orquestación conversacional del agente IA.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class LangGraphSettings(BaseSettings):
    """Configuración principal del servidor LangGraph."""
    
    # ===== CONFIGURACIÓN DEL SERVIDOR =====
    LANGGRAPH_HOST: str = Field(default="0.0.0.0", description="Host del servidor LangGraph")
    LANGGRAPH_PORT: int = Field(default=8001, description="Puerto del servidor LangGraph")
    LANGGRAPH_DEBUG: bool = Field(default=False, description="Modo debug")
    LANGGRAPH_LOG_LEVEL: str = Field(default="INFO", description="Nivel de logging")
    LANGGRAPH_WORKERS: int = Field(default=1, description="Número de workers")
    
    # ===== CONFIGURACIÓN DE BASE DE DATOS =====
    DATABASE_URL: str = Field(
        default="postgresql://odoo:P4tc0_2@db:5432/odoo_patco",
        description="URL completa de conexión a PostgreSQL"
    )
    DB_HOST: str = Field(default="db", description="Host de PostgreSQL")
    DB_PORT: int = Field(default=5432, description="Puerto de PostgreSQL")
    DB_NAME: str = Field(default="odoo_patco", description="Nombre de la base de datos")
    DB_USER: str = Field(default="odoo", description="Usuario de PostgreSQL")
    DB_PASSWORD: str = Field(default="P4tc0_2", description="Contraseña de PostgreSQL")
    
    # ===== CONFIGURACIÓN DE SERVIDOR MCP =====
    MCP_SERVER_URL: str = Field(
        default="http://mcp-server:8080",
        description="URL del servidor MCP"
    )
    MCP_TIMEOUT: int = Field(default=30, description="Timeout para requests al MCP")
    
    # ===== CONFIGURACIÓN DE APIS EXTERNAS =====
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="API Key de Google Gemini"
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="API Key de OpenAI"
    )
    
    # ===== CONFIGURACIÓN DE EMBEDDINGS =====
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-004",
        description="Modelo de embeddings a usar"
    )
    EMBEDDING_DIMENSION: int = Field(
        default=768,
        description="Dimensión de los vectores de embedding"
    )
    
    # ===== CONFIGURACIÓN DE CONVERSACIONES =====
    MAX_CONVERSATION_HISTORY: int = Field(
        default=50,
        description="Máximo número de mensajes en historial"
    )
    CONVERSATION_TIMEOUT: int = Field(
        default=1800,  # 30 minutos
        description="Timeout de conversación en segundos"
    )
    
    # ===== CONFIGURACIÓN DE CACHE =====
    CACHE_TTL: int = Field(
        default=300,
        description="TTL del cache en segundos"
    )
    CACHE_MAX_SIZE: int = Field(
        default=1000,
        description="Tamaño máximo del cache"
    )
    
    # ===== CONFIGURACIÓN DE CORS =====
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8069",
        description="Orígenes permitidos para CORS (separados por coma)"
    )
    
    # ===== CONFIGURACIÓN DE ARCHIVOS =====
    DATA_DIR: str = Field(
        default="/app/data",
        description="Directorio para datos persistentes"
    )
    CACHE_DIR: str = Field(
        default="/app/cache",
        description="Directorio para cache de archivos"
    )
    LOG_DIR: str = Field(
        default="/app/logs",
        description="Directorio para logs"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    def get_cors_origins(self) -> List[str]:
        """Obtener lista de orígenes CORS."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
    
    def get_database_url(self) -> str:
        """Obtener URL de base de datos."""
        return self.DATABASE_URL
    
    def get_mcp_server_url(self) -> str:
        """Obtener URL del servidor MCP."""
        return self.MCP_SERVER_URL


# Instancia global de configuración
settings = LangGraphSettings()

# Crear directorios necesarios
for directory in [settings.DATA_DIR, settings.CACHE_DIR, settings.LOG_DIR]:
    os.makedirs(directory, exist_ok=True)