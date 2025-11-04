#!/usr/bin/env python3
"""
Tests de integración para el servidor MCP

Este módulo contiene tests de integración completa que validan
el funcionamiento del sistema MCP en conjunto con Odoo y PostgreSQL.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Añadir el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MCPConfig
from server import app


class TestMCPIntegration:
    """Tests de integración completa del servidor MCP"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = TestClient(app)
        self.base_request = {
            "jsonrpc": "2.0",
            "id": 1
        }
    
    def test_full_fsm_workflow(self):
        """Test de flujo completo FSM: obtener orden -> actualizar -> verificar"""
        # 1. Obtener orden FSM
        get_request = {
            **self.base_request,
            "method": "get_fsm_order",
            "params": {"order_id": 1}
        }
        
        with patch('tools.fsm_tools.get_odoo_client') as mock_client:
            # Mock para obtener orden
            mock_client.return_value.search_read.return_value = [{
                'id': 1,
                'name': 'ORD-001',
                'stage_id': [1, 'Nuevo'],
                'description': 'Orden inicial'
            }]
            
            response = self.client.post("/mcp", json=get_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data['result']['success'] is True
            assert data['result']['order']['name'] == 'ORD-001'
            
            # 2. Actualizar orden FSM
            update_request = {
                **self.base_request,
                "id": 2,
                "method": "update_fsm_order",
                "params": {
                    "order_id": 1,
                    "stage_id": 2,
                    "description": "Orden actualizada"
                }
            }
            
            # Mock para actualizar orden
            mock_client.return_value.write.return_value = True
            
            response = self.client.post("/mcp", json=update_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data['result']['success'] is True
            
            # Verificar que se llamaron los métodos correctos
            assert mock_client.return_value.search_read.called
            assert mock_client.return_value.write.called
    
    def test_equipment_knowledge_integration(self):
        """Test de integración entre equipos y base de conocimiento"""
        # 1. Obtener información de equipo
        equipment_request = {
            **self.base_request,
            "method": "get_equipment_info",
            "params": {"equipment_id": 1}
        }
        
        with patch('tools.equipment_tools.get_odoo_client') as mock_odoo:
            mock_odoo.return_value.search_read.return_value = [{
                'id': 1,
                'name': 'Bomba Centrífuga BC-100',
                'model': 'BC-100',
                'equipment_type': 'Bomba'
            }]
            
            response = self.client.post("/mcp", json=equipment_request)
            assert response.status_code == 200
            
            data = response.json()
            equipment_name = data['result']['equipment']['name']
            
            # 2. Buscar documentación relacionada
            knowledge_request = {
                **self.base_request,
                "id": 2,
                "method": "search_knowledge_base",
                "params": {
                    "query": f"manual {equipment_name}",
                    "limit": 5
                }
            }
            
            with patch('tools.knowledge_tools.get_db_client') as mock_db:
                mock_db.return_value.execute_query.return_value = [{
                    'id': 1,
                    'title': f'Manual de {equipment_name}',
                    'content': 'Procedimientos de mantenimiento',
                    'similarity_score': 0.95
                }]
                
                response = self.client.post("/mcp", json=knowledge_request)
                assert response.status_code == 200
                
                data = response.json()
                assert data['result']['success'] is True
                assert len(data['result']['documents']) > 0
    
    def test_ai_conversation_workflow(self):
        """Test de flujo completo de conversación IA"""
        # 1. Crear conversación
        create_request = {
            **self.base_request,
            "method": "create_ai_conversation",
            "params": {
                "title": "Consulta técnica",
                "user_id": 1,
                "context_type": "fsm_order",
                "context_id": 123
            }
        }
        
        with patch('tools.conversation_tools.get_odoo_client') as mock_client:
            mock_client.return_value.create.return_value = [1]
            
            response = self.client.post("/mcp", json=create_request)
            assert response.status_code == 200
            
            data = response.json()
            conversation_id = data['result']['conversation_id']
            
            # 2. Enviar mensaje
            message_request = {
                **self.base_request,
                "id": 2,
                "method": "send_ai_message",
                "params": {
                    "conversation_id": conversation_id,
                    "message": "¿Cómo resolver problema X?",
                    "user_id": 1
                }
            }
            
            # Mock para crear mensaje y respuesta IA
            mock_client.return_value.create.return_value = [1]
            
            with patch('tools.conversation_tools.ConversationToolsManager._simulate_ai_response') as mock_ai:
                mock_ai.return_value = "Respuesta técnica detallada"
                
                response = self.client.post("/mcp", json=message_request)
                assert response.status_code == 200
                
                data = response.json()
                assert data['result']['success'] is True
                assert 'ai_response' in data['result']
            
            # 3. Obtener conversación completa
            get_request = {
                **self.base_request,
                "id": 3,
                "method": "get_ai_conversation",
                "params": {"conversation_id": conversation_id}
            }
            
            mock_client.return_value.search_read.return_value = [{
                'id': conversation_id,
                'title': 'Consulta técnica',
                'status': 'active'
            }]
            
            response = self.client.post("/mcp", json=get_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data['result']['success'] is True
    
    def test_multiple_tools_sequence(self):
        """Test de secuencia de múltiples herramientas"""
        requests_sequence = [
            {
                "jsonrpc": "2.0",
                "method": "get_fsm_order",
                "params": {"order_id": 1},
                "id": 1
            },
            {
                "jsonrpc": "2.0",
                "method": "get_equipment_info",
                "params": {"equipment_id": 1},
                "id": 2
            },
            {
                "jsonrpc": "2.0",
                "method": "search_knowledge_base",
                "params": {"query": "mantenimiento preventivo", "limit": 3},
                "id": 3
            },
            {
                "jsonrpc": "2.0",
                "method": "list_ai_conversations",
                "params": {"user_id": 1, "limit": 5},
                "id": 4
            }
        ]
        
        # Configurar mocks para todas las herramientas
        with patch('tools.fsm_tools.get_odoo_client') as mock_fsm, \
             patch('tools.equipment_tools.get_odoo_client') as mock_eq, \
             patch('tools.knowledge_tools.get_db_client') as mock_db, \
             patch('tools.conversation_tools.get_odoo_client') as mock_conv:
            
            # Configurar respuestas mock
            mock_fsm.return_value.search_read.return_value = [{'id': 1, 'name': 'ORD-001'}]
            mock_eq.return_value.search_read.return_value = [{'id': 1, 'name': 'Equipo Test'}]
            mock_db.return_value.execute_query.return_value = [{'id': 1, 'title': 'Manual Test'}]
            mock_conv.return_value.search_read.return_value = [{'id': 1, 'title': 'Conversación Test'}]
            
            # Ejecutar secuencia de requests
            responses = []
            for request in requests_sequence:
                response = self.client.post("/mcp", json=request)
                assert response.status_code == 200
                responses.append(response.json())
            
            # Verificar que todas las respuestas son exitosas
            for i, response_data in enumerate(responses):
                assert 'result' in response_data
                assert response_data['id'] == i + 1
                # Verificar estructura básica de respuesta exitosa
                if 'success' in response_data['result']:
                    assert response_data['result']['success'] is True
    
    def test_error_handling_integration(self):
        """Test de manejo de errores en integración"""
        # Test con herramienta que falla
        error_request = {
            **self.base_request,
            "method": "get_fsm_order",
            "params": {"order_id": 1}
        }
        
        with patch('tools.fsm_tools.get_odoo_client') as mock_client:
            # Simular error de conexión
            mock_client.side_effect = Exception("Error de conexión a Odoo")
            
            response = self.client.post("/mcp", json=error_request)
            assert response.status_code == 500
            
            data = response.json()
            assert 'error' in data
    
    def test_concurrent_requests(self):
        """Test de requests concurrentes"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                request = {
                    "jsonrpc": "2.0",
                    "method": "get_fsm_order",
                    "params": {"order_id": request_id},
                    "id": request_id
                }
                
                with patch('tools.fsm_tools.get_odoo_client') as mock_client:
                    mock_client.return_value.search_read.return_value = [{
                        'id': request_id,
                        'name': f'ORD-{request_id:03d}'
                    }]
                    
                    response = self.client.post("/mcp", json=request)
                    results.append((request_id, response.status_code))
            except Exception as e:
                errors.append((request_id, str(e)))
        
        # Crear múltiples threads para requests concurrentes
        threads = []
        for i in range(1, 6):  # 5 requests concurrentes
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que terminen
        for thread in threads:
            thread.join(timeout=10)
        
        # Verificar resultados
        assert len(errors) == 0, f"Errores en requests concurrentes: {errors}"
        assert len(results) == 5, f"Se esperaban 5 resultados, se obtuvieron {len(results)}"
        
        # Verificar que todos los requests fueron exitosos
        for request_id, status_code in results:
            assert status_code == 200, f"Request {request_id} falló con código {status_code}"


class TestMCPPerformance:
    """Tests de rendimiento del servidor MCP"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = TestClient(app)
    
    def test_response_time_health_check(self):
        """Test de tiempo de respuesta del health check"""
        start_time = time.time()
        response = self.client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0, f"Health check tardó {response_time:.3f}s (máximo 1.0s)"
    
    def test_response_time_tools_list(self):
        """Test de tiempo de respuesta del listado de herramientas"""
        start_time = time.time()
        response = self.client.get("/tools")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Listado de herramientas tardó {response_time:.3f}s (máximo 2.0s)"
    
    def test_memory_usage_multiple_requests(self):
        """Test básico de uso de memoria con múltiples requests"""
        import psutil
        import os
        
        # Obtener uso de memoria inicial
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Hacer múltiples requests
        for i in range(50):
            response = self.client.get("/health")
            assert response.status_code == 200
        
        # Obtener uso de memoria final
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Verificar que el aumento de memoria sea razonable
        assert memory_increase < 50, f"Aumento de memoria excesivo: {memory_increase:.2f}MB"


class TestMCPSecurity:
    """Tests de seguridad del servidor MCP"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = TestClient(app)
    
    def test_malformed_json_handling(self):
        """Test de manejo de JSON malformado"""
        malformed_requests = [
            '{"jsonrpc": "2.0", "method": "test", "id": 1',  # JSON incompleto
            '{"jsonrpc": "2.0", "method": "test", "id": 1, "extra": }',  # Sintaxis inválida
            '{{"jsonrpc": "2.0"}}',  # Llaves dobles
            '',  # Vacío
            'null',  # Null
            '[]',  # Array en lugar de objeto
        ]
        
        for malformed_json in malformed_requests:
            response = self.client.post(
                "/mcp",
                content=malformed_json,
                headers={"Content-Type": "application/json"}
            )
            # Debería devolver error 400 para JSON malformado
            assert response.status_code == 400
    
    def test_large_payload_handling(self):
        """Test de manejo de payloads grandes"""
        # Crear un payload muy grande
        large_payload = {
            "jsonrpc": "2.0",
            "method": "search_knowledge_base",
            "params": {
                "query": "x" * 10000,  # Query muy larga
                "limit": 1000
            },
            "id": 1
        }
        
        response = self.client.post("/mcp", json=large_payload)
        # El servidor debería manejar el payload grande apropiadamente
        assert response.status_code in [200, 400, 413, 422]
    
    def test_sql_injection_prevention(self):
        """Test de prevención de inyección SQL"""
        # Intentos de inyección SQL en parámetros
        injection_attempts = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; DELETE FROM orders; --",
            "UNION SELECT * FROM sensitive_data"
        ]
        
        for injection in injection_attempts:
            request = {
                "jsonrpc": "2.0",
                "method": "get_fsm_order",
                "params": {"order_id": injection},
                "id": 1
            }
            
            response = self.client.post("/mcp", json=request)
            # El servidor debería rechazar o manejar seguramente estos intentos
            assert response.status_code in [200, 400, 422]
            
            # Si la respuesta es 200, verificar que no hay datos sensibles
            if response.status_code == 200:
                data = response.json()
                response_str = json.dumps(data).lower()
                # No debería contener indicios de inyección exitosa
                assert "drop table" not in response_str
                assert "delete from" not in response_str
    
    def test_xss_prevention(self):
        """Test de prevención de XSS"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for xss in xss_attempts:
            request = {
                "jsonrpc": "2.0",
                "method": "search_knowledge_base",
                "params": {"query": xss},
                "id": 1
            }
            
            response = self.client.post("/mcp", json=request)
            # Verificar que la respuesta no contiene scripts sin escapar
            if response.status_code == 200:
                response_text = response.text
                assert "<script>" not in response_text
                assert "javascript:" not in response_text
                assert "onerror=" not in response_text


if __name__ == "__main__":
    print("Tests de integración del servidor MCP")
    print("=====================================")
    
    # Información sobre los tests disponibles
    test_classes = [
        (TestMCPIntegration, "Tests de integración completa"),
        (TestMCPPerformance, "Tests de rendimiento"),
        (TestMCPSecurity, "Tests de seguridad")
    ]
    
    total_tests = 0
    for test_class, description in test_classes:
        methods = [method for method in dir(test_class) if method.startswith('test_')]
        total_tests += len(methods)
        print(f"\n{description}:")
        print(f"  Clase: {test_class.__name__}")
        print(f"  Tests: {len(methods)}")
        for method in methods:
            print(f"    - {method}")
    
    print(f"\nTotal de tests de integración: {total_tests}")
    print("\nPara ejecutar todos los tests:")
    print("  pytest test_integration.py -v")
    print("\nPara ejecutar tests específicos:")
    print("  pytest test_integration.py::TestMCPIntegration::test_full_fsm_workflow -v")
    print("  pytest test_integration.py::TestMCPPerformance -v")
    print("  pytest test_integration.py::TestMCPSecurity -v")