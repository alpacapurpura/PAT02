#!/usr/bin/env python3
"""
Tests para las herramientas MCP

Este módulo contiene tests para validar el funcionamiento de todas las
herramientas MCP implementadas, incluyendo FSM, equipos, RAG y conversaciones.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Añadir el directorio padre al path para importar las herramientas
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.conversation_tools import (
    create_ai_conversation,
    get_ai_conversation,
    list_ai_conversations,
    send_ai_message,
    update_ai_conversation,
)
from tools.equipment_tools import get_equipment_info
from tools.fsm_tools import get_fsm_order, update_fsm_order
from tools.knowledge_tools import (
    get_knowledge_document,
    hybrid_search_knowledge,
    keyword_search_knowledge,
    list_knowledge_documents,
    search_knowledge_base,
    search_similar_documents,
    semantic_search_knowledge,
)


class TestFSMTools:
    """Tests para las herramientas FSM"""
    
    @pytest.mark.asyncio
    async def test_get_fsm_order_success(self):
        """Test exitoso de obtención de orden FSM"""
        with patch('tools.fsm_tools.get_odoo_client') as mock_get_client:
            # Mock del cliente Odoo
            mock_client = AsyncMock()
            mock_client.search_read.return_value = [{
                'id': 1,
                'name': 'ORD-001',
                'partner_id': [1, 'Cliente Test'],
                'location_id': [1, 'Ubicación Test'],
                'equipment_id': [1, 'Equipo Test'],
                'stage_id': [1, 'En Progreso'],
                'user_id': [1, 'Técnico Test'],
                'description': 'Orden de prueba',
                'date_start': '2025-01-23 10:00:00',
                'date_end': False,
                'priority': '1',
            }]
            mock_get_client.return_value = mock_client
            
            # Ejecutar función
            result = await get_fsm_order(order_id=1)
            
            # Verificaciones
            assert result['success'] is True
            assert 'order' in result
            assert result['order']['id'] == 1
            assert result['order']['name'] == 'ORD-001'
            
            # Verificar que se llamó al cliente Odoo correctamente
            mock_client.search_read.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_fsm_order_not_found(self):
        """Test de orden FSM no encontrada"""
        with patch('tools.fsm_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_read.return_value = []  # No se encuentra la orden
            mock_get_client.return_value = mock_client
            
            result = await get_fsm_order(order_id=999)
            
            assert result['success'] is False
            assert 'error' in result
            assert 'not found' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_update_fsm_order_success(self):
        """Test exitoso de actualización de orden FSM"""
        with patch('tools.fsm_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.write.return_value = True
            mock_get_client.return_value = mock_client
            
            update_data = {
                'stage_id': 2,
                'description': 'Orden actualizada',
                'user_id': 2
            }
            
            result = await update_fsm_order(order_id=1, **update_data)
            
            assert result['success'] is True
            assert 'message' in result
            
            # Verificar que se llamó al método write
            mock_client.write.assert_called_once_with(
                'fsm.order', [1], update_data
            )
    
    @pytest.mark.asyncio
    async def test_update_fsm_order_error(self):
        """Test de error en actualización de orden FSM"""
        with patch('tools.fsm_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.write.side_effect = Exception("Error de conexión")
            mock_get_client.return_value = mock_client
            
            result = await update_fsm_order(order_id=1, stage_id=2)
            
            assert result['success'] is False
            assert 'error' in result


class TestEquipmentTools:
    """Tests para las herramientas de equipos"""
    
    @pytest.mark.asyncio
    async def test_get_equipment_info_success(self):
        """Test exitoso de obtención de información de equipo"""
        with patch('tools.equipment_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_read.return_value = [{
                'id': 1,
                'name': 'Equipo Test',
                'equipment_type': 'Tipo Test',
                'partner_id': [1, 'Cliente Test'],
                'location': 'Ubicación Test',
                'model': 'Modelo Test',
                'serial_no': 'SN123456',
                'install_date': '2024-01-01',
                'warranty_date': '2025-01-01',
                'maintenance_team_id': [1, 'Equipo Mantenimiento'],
                'category_id': [1, 'Categoría Test'],
                'technician_user_id': [1, 'Técnico Test'],
                'maintenance_count': 5,
                'maintenance_open_count': 2,
            }]
            mock_get_client.return_value = mock_client
            
            result = await get_equipment_info(equipment_id=1)
            
            assert result['success'] is True
            assert 'equipment' in result
            assert result['equipment']['id'] == 1
            assert result['equipment']['name'] == 'Equipo Test'
    
    @pytest.mark.asyncio
    async def test_get_equipment_info_not_found(self):
        """Test de equipo no encontrado"""
        with patch('tools.equipment_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_read.return_value = []
            mock_get_client.return_value = mock_client
            
            result = await get_equipment_info(equipment_id=999)
            
            assert result['success'] is False
            assert 'error' in result
            assert 'not found' in result['error'].lower()


class TestKnowledgeTools:
    """Tests para las herramientas de base de conocimiento"""
    
    @pytest.mark.asyncio
    async def test_search_knowledge_base_success(self):
        """Test exitoso de búsqueda en base de conocimiento"""
        with patch('tools.knowledge_tools.get_db_client') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.execute_query.return_value = [
                {
                    'id': 1,
                    'title': 'Documento Test',
                    'content': 'Contenido de prueba',
                    'document_type': 'manual',
                    'created_date': datetime.now(),
                    'similarity_score': 0.95
                }
            ]
            mock_get_db.return_value = mock_db
            
            result = await search_knowledge_base(
                query="test query",
                limit=10
            )
            
            assert result['success'] is True
            assert 'documents' in result
            assert len(result['documents']) == 1
            assert result['documents'][0]['title'] == 'Documento Test'
    
    @pytest.mark.asyncio
    async def test_semantic_search_knowledge_success(self):
        """Test exitoso de búsqueda semántica"""
        with patch('tools.knowledge_tools.get_db_client') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.execute_query.return_value = [
                {
                    'id': 1,
                    'title': 'Manual Técnico',
                    'content': 'Contenido técnico detallado',
                    'document_type': 'manual',
                    'similarity_score': 0.88
                }
            ]
            mock_get_db.return_value = mock_db
            
            result = await semantic_search_knowledge(
                query="problema técnico",
                limit=5,
                threshold=0.7
            )
            
            assert result['success'] is True
            assert 'documents' in result
            assert result['documents'][0]['similarity_score'] >= 0.7
    
    @pytest.mark.asyncio
    async def test_get_knowledge_document_success(self):
        """Test exitoso de obtención de documento específico"""
        with patch('tools.knowledge_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_read.return_value = [{
                'id': 1,
                'name': 'Manual de Usuario',
                'content': 'Contenido del manual',
                'document_type': 'manual',
                'create_date': '2025-01-01 10:00:00',
                'write_date': '2025-01-23 15:30:00',
                'create_uid': [1, 'Admin'],
                'category_ids': [[1, 'Manuales']],
                'tag_ids': [[1, 'Técnico'], [2, 'Usuario']],
            }]
            mock_get_client.return_value = mock_client
            
            result = await get_knowledge_document(document_id=1)
            
            assert result['success'] is True
            assert 'document' in result
            assert result['document']['name'] == 'Manual de Usuario'
    
    @pytest.mark.asyncio
    async def test_list_knowledge_documents_success(self):
        """Test exitoso de listado de documentos"""
        with patch('tools.knowledge_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_read.return_value = [
                {
                    'id': 1,
                    'name': 'Manual 1',
                    'document_type': 'manual',
                    'create_date': '2025-01-01 10:00:00'
                },
                {
                    'id': 2,
                    'name': 'FAQ 1',
                    'document_type': 'faq',
                    'create_date': '2025-01-02 11:00:00'
                }
            ]
            mock_get_client.return_value = mock_client
            
            result = await list_knowledge_documents(
                document_type="manual",
                limit=10
            )
            
            assert result['success'] is True
            assert 'documents' in result
            assert len(result['documents']) == 2


class TestConversationTools:
    """Tests para las herramientas de conversaciones IA"""
    
    @pytest.mark.asyncio
    async def test_create_ai_conversation_success(self):
        """Test exitoso de creación de conversación IA"""
        with patch('tools.conversation_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create.return_value = [1]  # ID de la conversación creada
            mock_get_client.return_value = mock_client
            
            result = await create_ai_conversation(
                title="Conversación Test",
                user_id=1,
                context_type="fsm_order",
                context_id=123
            )
            
            assert result['success'] is True
            assert 'conversation_id' in result
            assert result['conversation_id'] == 1
    
    @pytest.mark.asyncio
    async def test_send_ai_message_success(self):
        """Test exitoso de envío de mensaje IA"""
        with patch('tools.conversation_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create.return_value = [1]  # ID del mensaje creado
            mock_get_client.return_value = mock_client
            
            # Mock de respuesta IA
            with patch('tools.conversation_tools.ConversationToolsManager._simulate_ai_response') as mock_ai:
                mock_ai.return_value = "Respuesta simulada de IA"
                
                result = await send_ai_message(
                    conversation_id=1,
                    message="Hola, necesito ayuda",
                    user_id=1
                )
                
                assert result['success'] is True
                assert 'message_id' in result
                assert 'ai_response' in result
                assert result['ai_response'] == "Respuesta simulada de IA"
    
    @pytest.mark.asyncio
    async def test_get_ai_conversation_success(self):
        """Test exitoso de obtención de conversación IA"""
        with patch('tools.conversation_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            
            # Mock de conversación
            mock_client.search_read.return_value = [{
                'id': 1,
                'title': 'Conversación Test',
                'user_id': [1, 'Usuario Test'],
                'context_type': 'fsm_order',
                'context_id': 123,
                'status': 'active',
                'create_date': '2025-01-23 10:00:00',
            }]
            
            result = await get_ai_conversation(conversation_id=1)
            
            assert result['success'] is True
            assert 'conversation' in result
            assert result['conversation']['title'] == 'Conversación Test'
    
    @pytest.mark.asyncio
    async def test_list_ai_conversations_success(self):
        """Test exitoso de listado de conversaciones IA"""
        with patch('tools.conversation_tools.get_odoo_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_read.return_value = [
                {
                    'id': 1,
                    'title': 'Conversación 1',
                    'status': 'active',
                    'create_date': '2025-01-23 10:00:00'
                },
                {
                    'id': 2,
                    'title': 'Conversación 2',
                    'status': 'closed',
                    'create_date': '2025-01-22 15:30:00'
                }
            ]
            mock_get_client.return_value = mock_client
            
            result = await list_ai_conversations(
                user_id=1,
                status="active",
                limit=10
            )
            
            assert result['success'] is True
            assert 'conversations' in result
            assert len(result['conversations']) == 2


class TestToolsIntegration:
    """Tests de integración entre herramientas"""
    
    @pytest.mark.asyncio
    async def test_fsm_to_knowledge_integration(self):
        """Test de integración entre FSM y base de conocimiento"""
        # Simular obtención de orden FSM
        with patch('tools.fsm_tools.get_odoo_client') as mock_fsm_client:
            mock_fsm_client.return_value.search_read.return_value = [{
                'id': 1,
                'name': 'ORD-001',
                'equipment_id': [1, 'Bomba Centrífuga'],
                'description': 'Problema con bomba'
            }]
            
            fsm_result = await get_fsm_order(order_id=1)
            
            # Usar información de la orden para buscar en conocimiento
            if fsm_result['success']:
                equipment_name = fsm_result['order']['equipment_id'][1]
                
                with patch('tools.knowledge_tools.get_db_client') as mock_db:
                    mock_db.return_value.execute_query.return_value = [{
                        'id': 1,
                        'title': f'Manual {equipment_name}',
                        'content': 'Procedimientos de mantenimiento',
                        'similarity_score': 0.92
                    }]
                    
                    knowledge_result = await search_knowledge_base(
                        query=f"mantenimiento {equipment_name}"
                    )
                    
                    assert knowledge_result['success'] is True
                    assert len(knowledge_result['documents']) > 0
    
    @pytest.mark.asyncio
    async def test_equipment_to_conversation_integration(self):
        """Test de integración entre equipos y conversaciones IA"""
        # Obtener información de equipo
        with patch('tools.equipment_tools.get_odoo_client') as mock_eq_client:
            mock_eq_client.return_value.search_read.return_value = [{
                'id': 1,
                'name': 'Compresor Industrial',
                'model': 'CI-2000',
                'maintenance_count': 15
            }]
            
            equipment_result = await get_equipment_info(equipment_id=1)
            
            # Crear conversación basada en el equipo
            if equipment_result['success']:
                with patch('tools.conversation_tools.get_odoo_client') as mock_conv_client:
                    mock_conv_client.return_value.create.return_value = [1]
                    
                    conversation_result = await create_ai_conversation(
                        title=f"Consulta sobre {equipment_result['equipment']['name']}",
                        user_id=1,
                        context_type="equipment",
                        context_id=equipment_result['equipment']['id']
                    )
                    
                    assert conversation_result['success'] is True
                    assert conversation_result['conversation_id'] == 1


if __name__ == "__main__":
    # Ejecutar tests básicos sin pytest
    import unittest
    
    print("Ejecutando tests básicos de herramientas MCP...")
    
    # Tests que se pueden ejecutar sin async
    test_classes = [
        TestFSMTools,
        TestEquipmentTools,
        TestKnowledgeTools,
        TestConversationTools,
        TestToolsIntegration
    ]
    
    print(f"Se ejecutarán tests para {len(test_classes)} clases de herramientas")
    
    # Simular ejecución de tests
    total_tests = 0
    for test_class in test_classes:
        methods = [method for method in dir(test_class) if method.startswith('test_')]
        total_tests += len(methods)
        print(f"- {test_class.__name__}: {len(methods)} tests")
    
    print(f"\nTotal de tests disponibles: {total_tests}")
    print("\nNota: Para ejecutar todos los tests, usar: pytest test_tools.py -v")
    print("Para tests específicos, usar: pytest test_tools.py::TestFSMTools::test_get_fsm_order_success -v")