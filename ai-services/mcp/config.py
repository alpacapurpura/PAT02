#!/usr/bin/env python3
"""
Configuración del Servidor MCP para PATCO Suite

Este módulo centraliza la configuración esencial del servidor MCP.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración principal del servidor MCP."""
    
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
    
    # ===== CONFIGURACIÓN DE ODOO =====
    ODOO_URL: str = Field(
        default="http://odoo:8069",
        description="URL del servidor Odoo"
    )
    ODOO_DB: str = Field(default="odoo_patco", description="Base de datos de Odoo")
    ODOO_USERNAME: str = Field(default="admin", description="Usuario de Odoo")
    ODOO_PASSWORD: str = Field(default="admin", description="Contraseña de Odoo")
    ODOO_TIMEOUT: int = Field(default=30, description="Timeout para requests a Odoo")
    
    # ===== CONFIGURACIÓN DEL SERVIDOR MCP =====
    MCP_HOST: str = Field(default="0.0.0.0", description="Host del servidor MCP")
    MCP_PORT: int = Field(default=8080, description="Puerto del servidor MCP")
    MCP_DEBUG: bool = Field(default=False, description="Modo debug")
    MCP_LOG_LEVEL: str = Field(default="INFO", description="Nivel de logging")
    
    # ===== CONFIGURACIÓN DE ENTORNO =====
    ENVIRONMENT: str = Field(
        default="development",
        description="Entorno de ejecución: development, production, testing"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Nivel de logging global"
    )
    
    # ===== CONFIGURACIÓN DE AUTENTICACIÓN JWT =====
    JWT_SECRET_KEY: str = Field(
        default="patco-mcp-secret-key-2025",
        description="Clave secreta para JWT"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="Algoritmo JWT")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Expiración del token de acceso en minutos"
    )
    
    # ===== CONFIGURACIÓN DE APIs EXTERNAS =====
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
    SIMILARITY_THRESHOLD: float = Field(
        default=0.7,
        description="Umbral de similitud para búsquedas"
    )
    
    # ===== CONFIGURACIÓN DE RATE LIMITING =====
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Número máximo de requests por ventana"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        description="Ventana de tiempo para rate limiting en segundos"
    )
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=100,
        description="Número máximo de requests por minuto"
    )
    
    # ===== CONFIGURACIÓN DE CORS =====
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8069",
        description="Orígenes permitidos para CORS (separados por coma)"
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
    
    # ===== CONFIGURACIÓN DE ARCHIVOS =====
    UPLOAD_DIR: str = Field(
        default="/app/uploads",
        description="Directorio para archivos subidos"
    )
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
    
    def get_odoo_url(self) -> str:
        """Obtener URL de Odoo."""
        return self.ODOO_URL


# Instancia global de configuración
settings = Settings()

# Función para obtener configuración (compatibilidad)
def get_settings() -> Settings:
    """Obtener instancia de configuración."""
    return settings

# Crear directorios necesarios
for directory in [settings.UPLOAD_DIR, settings.DATA_DIR, settings.CACHE_DIR, settings.LOG_DIR]:
    os.makedirs(directory, exist_ok=True)