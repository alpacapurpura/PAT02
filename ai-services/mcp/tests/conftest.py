#!/usr/bin/env python3
"""
Configuración compartida para tests de pytest

Este módulo contiene fixtures y configuraciones compartidas
para todos los tests del servidor MCP.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import os
import sys
import tempfile
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Añadir el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MCPConfig
from server import app
from utils import AuthManager, DatabaseClient, OdooClient, RateLimiter


# Configuración de pytest
pytest_plugins = []


@pytest.fixture(scope="session")
def event_loop():
    """Fixture para el event loop de asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Fixture para directorio temporal"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def test_config(temp_dir):
    """Fixture para configuración de test"""
    # Variables de entorno para testing
    test_env = {
        "MCP_ENVIRONMENT": "testing",
        "MCP_DEBUG": "true",
        "MCP_LOG_LEVEL": "DEBUG",
        "MCP_LOG_DIR": temp_dir,
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "test_db",
        "ODOO_USERNAME": "test_user",
        "ODOO_PASSWORD": "test_password",
        "JWT_SECRET_KEY": "test_secret_key_for_testing_only",
        "JWT_EXPIRATION_HOURS": "24",
        "RATE_LIMIT_ENABLED": "true",
        "RATE_LIMIT_GLOBAL_REQUESTS_PER_MINUTE": "100",
        "RATE_LIMIT_PER_USER_REQUESTS_PER_MINUTE": "50",
        "CORS_ENABLED": "true",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:8080"
    }
    
    # Aplicar variables de entorno temporalmente
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    # Crear configuración
    config = MCPConfig()
    
    yield config
    
    # Restaurar variables de entorno originales
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def test_client():
    """Fixture para cliente de test de FastAPI"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_auth_manager(test_config):
    """Fixture para AuthManager mockeado"""
    auth_manager = AuthManager(test_config)
    
    # Mock de métodos que requieren conexiones externas
    auth_manager.validate_with_odoo = MagicMock(return_value={
        "user_id": 123,
        "username": "test_user",
        "email": "test@example.com",
        "roles": ["user", "technician"],
        "permissions": ["fsm.read", "fsm.write", "equipment.read"]
    })
    
    return auth_manager


@pytest.fixture
def mock_database_client(test_config):
    """Fixture para DatabaseClient mockeado"""
    db_client = DatabaseClient(test_config)
    
    # Mock del pool de conexiones
    mock_pool = AsyncMock()
    mock_connection = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
    
    # Mock de métodos de consulta
    mock_connection.fetch.return_value = [
        {"id": 1, "title": "Test Document", "content": "Test content"}
    ]
    mock_connection.fetchval.return_value = 1
    mock_connection.execute.return_value = "SELECT 1"
    
    db_client.pool = mock_pool
    
    return db_client


@pytest.fixture
def mock_odoo_client(test_config):
    """Fixture para OdooClient mockeado"""
    odoo_client = OdooClient(test_config)
    
    # Mock de autenticación exitosa
    odoo_client.uid = 123
    odoo_client.authenticated = True
    
    # Mock de métodos de Odoo
    odoo_client.search_read = MagicMock(return_value=[
        {"id": 1, "name": "Test Record", "state": "draft"}
    ])
    odoo_client.create = MagicMock(return_value=[456])
    odoo_client.write = MagicMock(return_value=True)
    odoo_client.unlink = MagicMock(return_value=True)
    
    return odoo_client


@pytest.fixture
def mock_rate_limiter():
    """Fixture para RateLimiter mockeado"""
    rate_limiter = RateLimiter()
    
    # Mock para permitir todas las requests por defecto
    rate_limiter.check_rate_limit = MagicMock(return_value=MagicMock(
        allowed=True,
        retry_after=0,
        remaining=100
    ))
    
    return rate_limiter


@pytest.fixture
def sample_fsm_order():
    """Fixture con datos de ejemplo de orden FSM"""
    return {
        "id": 1,
        "name": "ORD-001",
        "description": "Mantenimiento preventivo bomba centrífuga",
        "stage_id": [1, "Nuevo"],
        "person_id": [123, "Juan Pérez"],
        "location_id": [456, "Planta Principal"],
        "equipment_id": [789, "Bomba BC-100"],
        "priority": "1",
        "date_start": "2025-01-15 08:00:00",
        "date_end": "2025-01-15 12:00:00",
        "state": "draft",
        "notes": "Revisar rodamientos y sellos",
        "create_date": "2025-01-14 10:30:00",
        "write_date": "2025-01-14 10:30:00"
    }


@pytest.fixture
def sample_equipment():
    """Fixture con datos de ejemplo de equipo"""
    return {
        "id": 789,
        "name": "Bomba Centrífuga BC-100",
        "model": "BC-100",
        "serial_no": "BC100-2024-001",
        "equipment_type": "Bomba",
        "manufacturer": "Grundfos",
        "location_id": [456, "Planta Principal"],
        "maintenance_team_id": [10, "Equipo Mecánico"],
        "maintenance_duration": 4.0,
        "maintenance_count": 5,
        "next_action_date": "2025-02-15",
        "maintenance_state": "normal",
        "active": True,
        "notes": "Bomba para sistema de refrigeración principal",
        "specifications": {
            "power": "15 kW",
            "flow_rate": "500 L/min",
            "pressure": "8 bar",
            "temperature_range": "-10°C a 80°C"
        }
    }


@pytest.fixture
def sample_knowledge_documents():
    """Fixture con documentos de ejemplo para la base de conocimiento"""
    return [
        {
            "id": 1,
            "title": "Manual de Mantenimiento - Bomba Centrífuga BC-100",
            "content": "Procedimientos detallados para el mantenimiento preventivo y correctivo de bombas centrífugas modelo BC-100. Incluye inspección de rodamientos, cambio de sellos y calibración de presión.",
            "category": "manual",
            "equipment_type": "bomba",
            "tags": ["mantenimiento", "bomba", "preventivo"],
            "similarity_score": 0.95,
            "created_date": "2024-12-01",
            "updated_date": "2025-01-10"
        },
        {
            "id": 2,
            "title": "Guía de Solución de Problemas - Sistemas de Bombeo",
            "content": "Diagnóstico y solución de problemas comunes en sistemas de bombeo: ruidos anómalos, pérdida de presión, sobrecalentamiento y vibraciones excesivas.",
            "category": "troubleshooting",
            "equipment_type": "bomba",
            "tags": ["diagnóstico", "problemas", "bomba"],
            "similarity_score": 0.87,
            "created_date": "2024-11-15",
            "updated_date": "2024-12-20"
        },
        {
            "id": 3,
            "title": "Especificaciones Técnicas - Grundfos BC Series",
            "content": "Especificaciones técnicas completas de la serie BC de Grundfos: rangos de operación, materiales de construcción, dimensiones y requisitos de instalación.",
            "category": "specifications",
            "equipment_type": "bomba",
            "tags": ["especificaciones", "grundfos", "técnico"],
            "similarity_score": 0.82,
            "created_date": "2024-10-01",
            "updated_date": "2024-10-01"
        }
    ]


@pytest.fixture
def sample_ai_conversation():
    """Fixture con conversación de IA de ejemplo"""
    return {
        "id": 1,
        "title": "Consulta sobre mantenimiento de bomba",
        "user_id": 123,
        "context_type": "fsm_order",
        "context_id": 1,
        "status": "active",
        "created_date": "2025-01-14 14:30:00",
        "updated_date": "2025-01-14 15:45:00",
        "messages": [
            {
                "id": 1,
                "conversation_id": 1,
                "sender_type": "user",
                "sender_id": 123,
                "message": "¿Cuáles son los pasos para el mantenimiento preventivo de la bomba BC-100?",
                "timestamp": "2025-01-14 14:30:00"
            },
            {
                "id": 2,
                "conversation_id": 1,
                "sender_type": "ai",
                "sender_id": None,
                "message": "Para el mantenimiento preventivo de la bomba BC-100, sigue estos pasos: 1) Apagar y desconectar la bomba, 2) Inspeccionar rodamientos, 3) Verificar sellos, 4) Revisar alineación, 5) Comprobar presión de operación.",
                "timestamp": "2025-01-14 14:31:00",
                "metadata": {
                    "model_used": "gpt-4",
                    "confidence": 0.92,
                    "sources": ["Manual BC-100", "Guía de mantenimiento"]
                }
            }
        ]
    }


@pytest.fixture
def valid_mcp_request():
    """Fixture con request MCP válido"""
    return {
        "jsonrpc": "2.0",
        "method": "get_fsm_order",
        "params": {"order_id": 1},
        "id": 1
    }


@pytest.fixture
def invalid_mcp_requests():
    """Fixture con requests MCP inválidos para testing"""
    return [
        # Falta jsonrpc
        {
            "method": "get_fsm_order",
            "params": {"order_id": 1},
            "id": 1
        },
        # Versión jsonrpc incorrecta
        {
            "jsonrpc": "1.0",
            "method": "get_fsm_order",
            "params": {"order_id": 1},
            "id": 1
        },
        # Falta method
        {
            "jsonrpc": "2.0",
            "params": {"order_id": 1},
            "id": 1
        },
        # Method inválido
        {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "params": {"order_id": 1},
            "id": 1
        },
        # Params inválidos
        {
            "jsonrpc": "2.0",
            "method": "get_fsm_order",
            "params": "invalid_params",
            "id": 1
        }
    ]


@pytest.fixture
def mock_external_apis():
    """Fixture para mockear APIs externas"""
    mocks = {
        "openai": MagicMock(),
        "anthropic": MagicMock(),
        "gemini": MagicMock()
    }
    
    # Configurar respuestas mock para APIs de IA
    mocks["openai"].chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content="Respuesta generada por OpenAI para testing"
            )
        )]
    )
    
    return mocks


# Configuración de marcadores de pytest
def pytest_configure(config):
    """Configuración de pytest"""
    config.addinivalue_line(
        "markers", "slow: marca tests como lentos"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "unit: marca tests unitarios"
    )
    config.addinivalue_line(
        "markers", "security: marca tests de seguridad"
    )
    config.addinivalue_line(
        "markers", "performance: marca tests de rendimiento"
    )


# Configuración de colección de tests
def pytest_collection_modifyitems(config, items):
    """Modificar items de colección de tests"""
    # Marcar tests automáticamente basado en el nombre del archivo
    for item in items:
        # Tests de integración
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Tests unitarios
        elif any(name in item.nodeid for name in ["test_server", "test_tools", "test_utils"]):
            item.add_marker(pytest.mark.unit)
        
        # Tests de seguridad
        if "security" in item.name.lower() or "auth" in item.name.lower():
            item.add_marker(pytest.mark.security)
        
        # Tests de rendimiento
        if "performance" in item.name.lower() or "speed" in item.name.lower():
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


# Hooks de pytest
@pytest.fixture(autouse=True)
def setup_test_environment(test_config):
    """Configuración automática del entorno de test"""
    # Configurar logging para tests
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Configurar variables de entorno específicas para tests
    os.environ["TESTING"] = "true"
    
    yield
    
    # Limpieza después del test
    os.environ.pop("TESTING", None)


@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """Configuración de sesión de tests"""
    print("\n=== Iniciando sesión de tests del servidor MCP ===")
    
    yield
    
    print("\n=== Finalizando sesión de tests del servidor MCP ===")


if __name__ == "__main__":
    print("Configuración de tests para el servidor MCP")
    print("============================================")
    print("\nFixtures disponibles:")
    print("  - test_config: Configuración de test")
    print("  - test_client: Cliente de test de FastAPI")
    print("  - mock_auth_manager: AuthManager mockeado")
    print("  - mock_database_client: DatabaseClient mockeado")
    print("  - mock_odoo_client: OdooClient mockeado")
    print("  - mock_rate_limiter: RateLimiter mockeado")
    print("  - sample_fsm_order: Datos de ejemplo de orden FSM")
    print("  - sample_equipment: Datos de ejemplo de equipo")
    print("  - sample_knowledge_documents: Documentos de ejemplo")
    print("  - sample_ai_conversation: Conversación de IA de ejemplo")
    print("  - valid_mcp_request: Request MCP válido")
    print("  - invalid_mcp_requests: Requests MCP inválidos")
    print("  - mock_external_apis: APIs externas mockeadas")
    
    print("\nMarcadores disponibles:")
    print("  - @pytest.mark.unit: Tests unitarios")
    print("  - @pytest.mark.integration: Tests de integración")
    print("  - @pytest.mark.security: Tests de seguridad")
    print("  - @pytest.mark.performance: Tests de rendimiento")
    print("  - @pytest.mark.slow: Tests lentos")
    
    print("\nEjemplos de uso:")
    print("  pytest -m unit                    # Solo tests unitarios")
    print("  pytest -m integration             # Solo tests de integración")
    print("  pytest -m 'not slow'              # Excluir tests lentos")
    print("  pytest --tb=short -v              # Output verboso con traceback corto")