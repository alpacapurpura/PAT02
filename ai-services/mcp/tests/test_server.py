#!/usr/bin/env python3
"""
Tests para el servidor principal MCP

Este módulo contiene tests para validar el funcionamiento del servidor MCP,
incluyendo endpoints, autenticación, rate limiting y manejo de errores.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Añadir el directorio padre al path para importar el servidor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MCPConfig
from server import app


class TestMCPServer:
    """Tests para el servidor MCP principal"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = TestClient(app)
        self.test_config = MCPConfig(
            # Configuración de prueba
            DATABASE_URL="postgresql://test:test@localhost:5432/test_db",
            ODOO_URL="http://localhost:8069",
            ODOO_DB="test_db",
            ODOO_USERNAME="admin",
            ODOO_PASSWORD="admin",
            JWT_SECRET_KEY="test_secret_key_for_testing_only",
            JWT_ALGORITHM="HS256",
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
            MCP_HOST="127.0.0.1",
            MCP_PORT=8080,
            MCP_DEBUG=True,
            RATE_LIMIT_ENABLED=False,  # Deshabilitado para tests
        )
    
    def test_health_check(self):
        """Test del endpoint de health check"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
    
    def test_list_tools(self):
        """Test del endpoint para listar herramientas MCP"""
        response = self.client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
        
        # Verificar que las herramientas esperadas están presentes
        tool_names = [tool["name"] for tool in data["tools"]]
        expected_tools = [
            "get_fsm_order",
            "update_fsm_order",
            "get_equipment_info",
            "search_knowledge_base",
            "get_knowledge_document",
            "list_knowledge_documents",
            "search_similar_documents",
            "semantic_search_knowledge",
            "keyword_search_knowledge",
            "hybrid_search_knowledge",
            "create_ai_conversation",
            "send_ai_message",
            "get_ai_conversation",
            "list_ai_conversations",
            "update_ai_conversation",
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Herramienta {expected_tool} no encontrada"
    
    def test_mcp_endpoint_invalid_json(self):
        """Test del endpoint MCP con JSON inválido"""
        response = self.client.post(
            "/mcp",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Invalid JSON" in data["error"]
    
    def test_mcp_endpoint_missing_fields(self):
        """Test del endpoint MCP con campos faltantes"""
        invalid_request = {
            "jsonrpc": "2.0",
            # Falta "method" e "id"
        }
        
        response = self.client.post(
            "/mcp",
            json=invalid_request,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_mcp_endpoint_invalid_method(self):
        """Test del endpoint MCP con método inválido"""
        invalid_request = {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "params": {},
            "id": 1
        }
        
        response = self.client.post(
            "/mcp",
            json=invalid_request,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Tool not found" in data["error"]
    
    @patch('server.TOOL_REGISTRY')
    def test_mcp_endpoint_tool_execution_error(self, mock_registry):
        """Test del endpoint MCP con error en la ejecución de herramienta"""
        # Mock de herramienta que lanza excepción
        mock_tool = AsyncMock(side_effect=Exception("Test error"))
        mock_registry.get.return_value = mock_tool
        
        request_data = {
            "jsonrpc": "2.0",
            "method": "test_tool",
            "params": {},
            "id": 1
        }
        
        response = self.client.post(
            "/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "Internal server error" in data["error"]
    
    def test_cors_headers(self):
        """Test de headers CORS"""
        response = self.client.options("/mcp")
        assert response.status_code == 200
        
        # Verificar headers CORS básicos
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers
    
    @pytest.mark.asyncio
    async def test_server_startup_shutdown(self):
        """Test del ciclo de vida del servidor"""
        # Este test verifica que el servidor puede iniciar y cerrar correctamente
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
    
    def test_request_validation_middleware(self):
        """Test del middleware de validación de requests"""
        # Test con Content-Type incorrecto
        response = self.client.post(
            "/mcp",
            data="{\"test\": \"data\"}",
            headers={"Content-Type": "text/plain"}
        )
        # Debería funcionar ya que FastAPI es flexible con Content-Type
        # pero el JSON debería ser válido
        assert response.status_code in [200, 400, 422]
    
    def test_error_handling_middleware(self):
        """Test del middleware de manejo de errores"""
        # Test con endpoint que no existe
        response = self.client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test con método HTTP no permitido
        response = self.client.delete("/health")
        assert response.status_code == 405


class TestMCPProtocol:
    """Tests específicos del protocolo MCP"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = TestClient(app)
    
    def test_jsonrpc_version_validation(self):
        """Test de validación de versión JSON-RPC"""
        # Versión incorrecta
        request_data = {
            "jsonrpc": "1.0",  # Debería ser "2.0"
            "method": "get_fsm_order",
            "params": {"order_id": 1},
            "id": 1
        }
        
        response = self.client.post("/mcp", json=request_data)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_request_id_handling(self):
        """Test del manejo de IDs de request"""
        # Test con ID numérico
        request_data = {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "params": {},
            "id": 123
        }
        
        response = self.client.post("/mcp", json=request_data)
        data = response.json()
        assert "id" in data
        assert data["id"] == 123
        
        # Test con ID string
        request_data["id"] = "test-id-123"
        response = self.client.post("/mcp", json=request_data)
        data = response.json()
        assert data["id"] == "test-id-123"
    
    def test_notification_requests(self):
        """Test de requests de notificación (sin ID)"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "params": {}
            # Sin "id" - es una notificación
        }
        
        response = self.client.post("/mcp", json=request_data)
        # Las notificaciones no deberían devolver respuesta
        # pero nuestro servidor siempre devuelve algo
        assert response.status_code in [200, 400]


if __name__ == "__main__":
    # Ejecutar tests básicos
    import unittest
    
    # Crear una suite de tests básicos
    suite = unittest.TestSuite()
    
    # Añadir tests que no requieren async
    test_cases = [
        TestMCPServer('test_health_check'),
        TestMCPServer('test_list_tools'),
        TestMCPServer('test_mcp_endpoint_invalid_json'),
        TestMCPServer('test_mcp_endpoint_missing_fields'),
        TestMCPServer('test_mcp_endpoint_invalid_method'),
        TestMCPServer('test_cors_headers'),
        TestMCPProtocol('test_jsonrpc_version_validation'),
        TestMCPProtocol('test_request_id_handling'),
        TestMCPProtocol('test_notification_requests'),
    ]
    
    for test_case in test_cases:
        suite.addTest(test_case)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Salir con código de error si hay fallos
    sys.exit(0 if result.wasSuccessful() else 1)