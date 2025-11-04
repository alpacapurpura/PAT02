# ai-services/langgraph/tests/test_report_generation.py
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Importar el módulo a testear
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from nodes.report_generator import (
    generate_report,
    extract_structured_info,
    determine_template_type,
    create_onlyoffice_document,
    generate_filename,
    store_document_in_odoo
)

class TestReportGeneration:
    """Tests para la generación de reportes con OnlyOffice"""
    
    @pytest.fixture
    def sample_conversation_data(self):
        """Datos de conversación de ejemplo"""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": "Hola, necesito revisar el horno de la cocina",
                    "timestamp": "2025-01-27T10:00:00Z"
                },
                {
                    "role": "assistant", 
                    "content": "Hola! Te ayudo con la revisión del horno. ¿Cuál es el problema específico?",
                    "timestamp": "2025-01-27T10:00:30Z"
                },
                {
                    "role": "user",
                    "content": "No está calentando bien, la temperatura no sube de 150°C",
                    "timestamp": "2025-01-27T10:01:00Z"
                },
                {
                    "role": "assistant",
                    "content": "Entiendo. Vamos a revisar el termostato y las resistencias. ¿Has notado algún ruido extraño?",
                    "timestamp": "2025-01-27T10:01:30Z"
                },
                {
                    "role": "user",
                    "content": "No, no hay ruidos. Revisé el termostato y estaba descalibrado. Lo ajusté y ahora funciona correctamente.",
                    "timestamp": "2025-01-27T10:15:00Z"
                }
            ],
            "context": {
                "fsm_order_id": 123,
                "fsm_order": {
                    "name": "FSM/2025/001",
                    "partner_id": "Restaurante El Buen Sabor",
                    "location_id": "Cocina Principal",
                    "service_nature": "Mantenimiento Correctivo",
                    "service_area": "Cocina",
                    "equipment_ids": [456]
                },
                "technician_id": 789,
                "technician_name": "Juan Pérez",
                "conversation_id": 101,
                "template_type": "mantenimiento_correctivo",
                "equipment_category": "Hornos"
            }
        }
    
    @pytest.fixture
    def expected_structured_data(self):
        """Datos estructurados esperados"""
        return {
            "servicio": {
                "fecha_inicio": "2025-01-27 10:00",
                "fecha_fin": "2025-01-27 10:15",
                "tecnico": "Juan Pérez",
                "cliente": "Restaurante El Buen Sabor",
                "ubicacion": "Cocina Principal"
            },
            "equipos": [
                {
                    "nombre": "Horno de Cocina",
                    "modelo": "N/A",
                    "problema_reportado": "No está calentando bien, la temperatura no sube de 150°C",
                    "diagnostico": "Termostato descalibrado",
                    "acciones_realizadas": ["Revisión del termostato", "Ajuste de calibración"],
                    "estado_final": "funcionando"
                }
            ],
            "repuestos_utilizados": [],
            "mediciones": [
                {
                    "parametro": "Temperatura máxima",
                    "valor": "150",
                    "unidad": "°C",
                    "estado": "anormal"
                }
            ],
            "observaciones_tecnicas": "Termostato descalibrado causaba limitación de temperatura",
            "recomendaciones": "Realizar calibración periódica del termostato",
            "trabajo_completado": True,
            "cliente_satisfecho": True,
            "proxima_visita_requerida": False
        }

    def test_determine_template_type(self, sample_conversation_data):
        """Test de determinación de tipo de plantilla"""
        context = sample_conversation_data["context"]
        structured_data = {}
        
        # Test con servicio correctivo
        template_type = determine_template_type(context, structured_data)
        assert template_type == "mantenimiento_correctivo"
        
        # Test con servicio preventivo
        context["service_nature"] = "Mantenimiento Preventivo"
        template_type = determine_template_type(context, structured_data)
        assert template_type == "mantenimiento_preventivo"
        
        # Test con servicio desconocido (debe usar plantilla por defecto)
        context["service_nature"] = "Servicio Desconocido"
        template_type = determine_template_type(context, structured_data)
        assert template_type == "servicio_general"

    @patch('nodes.report_generator.genai')
    @pytest.mark.asyncio
    async def test_extract_structured_info(self, mock_genai, sample_conversation_data, expected_structured_data):
        """Test de extracción de información estructurada"""
        # Mock de la respuesta de Gemini
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(expected_structured_data)
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Ejecutar extracción
        result = await extract_structured_info(
            sample_conversation_data["messages"],
            sample_conversation_data["context"]
        )
        
        # Verificar resultado
        assert result == expected_structured_data
        assert result["servicio"]["tecnico"] == "Juan Pérez"
        assert len(result["equipos"]) == 1
        assert result["trabajo_completado"] == True

    def test_generate_filename(self, sample_conversation_data):
        """Test de generación de nombres de archivo"""
        context = sample_conversation_data["context"]
        structured_data = {}
        
        filename = generate_filename(context, structured_data)
        
        # Verificar formato del nombre
        assert filename.startswith("Reporte_Servicio_FSM_2025_001_")
        assert filename.endswith(".docx")
        assert "/" not in filename  # No debe contener caracteres problemáticos

    @patch('nodes.report_generator.call_document_builder_api')
    @pytest.mark.asyncio
    async def test_create_onlyoffice_document_success(self, mock_api_call, sample_conversation_data, expected_structured_data):
        """Test de creación exitosa de documento OnlyOffice"""
        # Mock de respuesta exitosa de OnlyOffice
        mock_api_call.return_value = {
            "success": True,
            "document_content": "base64_encoded_document_content",
            "download_url": "http://onlyoffice/download/123"
        }
        
        result = await create_onlyoffice_document(
            expected_structured_data,
            sample_conversation_data["context"],
            "mantenimiento_correctivo"
        )
        
        # Verificar resultado
        assert result["content"] == "base64_encoded_document_content"
        assert result["format"] == "docx"
        assert result["filename"].endswith(".docx")

    @patch('nodes.report_generator.call_document_builder_api')
    @patch('nodes.report_generator.create_fallback_document')
    @pytest.mark.asyncio
    async def test_create_onlyoffice_document_fallback(self, mock_fallback, mock_api_call, sample_conversation_data, expected_structured_data):
        """Test de fallback cuando OnlyOffice falla"""
        # Mock de fallo de OnlyOffice
        mock_api_call.return_value = {
            "success": False,
            "error": "OnlyOffice server unavailable"
        }
        
        # Mock de documento de fallback
        mock_fallback.return_value = {
            "content": "fallback_content_base64",
            "filename": "reporte_fallback.txt",
            "format": "txt"
        }
        
        result = await create_onlyoffice_document(
            expected_structured_data,
            sample_conversation_data["context"],
            "mantenimiento_correctivo"
        )
        
        # Verificar que se usó el fallback
        mock_fallback.assert_called_once()
        assert result["content"] == "fallback_content_base64"
        assert result["format"] == "txt"

    @patch('nodes.report_generator.requests.post')
    @pytest.mark.asyncio
    async def test_store_document_in_odoo_success(self, mock_post, sample_conversation_data):
        """Test de almacenamiento exitoso en Odoo"""
        # Mock de respuesta exitosa de MCP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "success": True,
                "attachment_id": 789
            }
        }
        mock_post.return_value = mock_response
        
        result = await store_document_in_odoo(
            "base64_document_content",
            "test_report.docx",
            sample_conversation_data["context"]
        )
        
        # Verificar resultado
        assert result == 789
        
        # Verificar que se llamó a MCP correctamente
        mock_post.assert_called()
        call_args = mock_post.call_args
        assert "create_attachment" in str(call_args)

    @patch('nodes.report_generator.extract_structured_info')
    @patch('nodes.report_generator.create_onlyoffice_document')
    @patch('nodes.report_generator.store_document_in_odoo')
    @pytest.mark.asyncio
    async def test_generate_report_complete_flow(self, mock_store, mock_create_doc, mock_extract, sample_conversation_data, expected_structured_data):
        """Test del flujo completo de generación de reportes"""
        # Configurar mocks
        mock_extract.return_value = expected_structured_data
        mock_create_doc.return_value = {
            "content": "base64_document",
            "filename": "reporte_test.docx",
            "format": "docx"
        }
        mock_store.return_value = 456
        
        # Ejecutar generación de reporte
        result = await generate_report(sample_conversation_data)
        
        # Verificar resultado
        assert result["report_generated"] == True
        assert result["report_attachment_id"] == 456
        assert result["report_filename"] == "reporte_test.docx"
        assert result["structured_data"] == expected_structured_data
        assert result["template_type"] == "mantenimiento_correctivo"
        
        # Verificar que se llamaron todos los pasos
        mock_extract.assert_called_once()
        mock_create_doc.assert_called_once()
        mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_report_no_messages(self):
        """Test de generación de reporte sin mensajes"""
        state = {
            "messages": [],
            "context": {}
        }
        
        result = await generate_report(state)
        
        # Verificar que se maneja correctamente la ausencia de mensajes
        assert result["report_generated"] == False
        assert "messages" in result  # El estado original se mantiene

    @patch('nodes.report_generator.extract_structured_info')
    @pytest.mark.asyncio
    async def test_generate_report_extraction_error(self, mock_extract, sample_conversation_data):
        """Test de manejo de errores en extracción"""
        # Mock de error en extracción
        mock_extract.side_effect = Exception("Error en extracción de datos")
        
        result = await generate_report(sample_conversation_data)
        
        # Verificar manejo de error
        assert result["report_generated"] == False
        assert "Error en extracción de datos" in result["report_error"]

class TestReportTemplates:
    """Tests para las plantillas de reportes"""
    
    def test_template_types_available(self):
        """Test de tipos de plantillas disponibles"""
        from templates.report_templates import REPORT_TEMPLATES
        
        expected_templates = [
            "servicio_general",
            "mantenimiento_preventivo", 
            "mantenimiento_correctivo",
            "instalacion_equipo",
            "calibracion_tecnica",
            "inspeccion_tecnica"
        ]
        
        for template_type in expected_templates:
            assert template_type in REPORT_TEMPLATES
            assert "name" in REPORT_TEMPLATES[template_type]
            assert "sections" in REPORT_TEMPLATES[template_type]
            assert "styles" in REPORT_TEMPLATES[template_type]

    def test_template_script_generation(self):
        """Test de generación de scripts de plantillas"""
        from templates.report_templates import generateTemplateScript
        
        test_data = {
            "structured_data": {
                "servicio": {"tecnico": "Test Tech"},
                "equipos": [{"nombre": "Test Equipment"}]
            },
            "context": {"fsm_order": {"name": "TEST001"}},
            "filename": "test_report.docx"
        }
        
        script = generateTemplateScript("servicio_general", test_data)
        
        # Verificar que el script contiene elementos esperados
        assert "builder.CreateFile" in script
        assert "builder.SaveFile" in script
        assert "builder.CloseFile" in script
        assert "Test Tech" in script
        assert "TEST001" in script

class TestIntegrationScenarios:
    """Tests de escenarios de integración completos"""
    
    @pytest.mark.integration
    @patch.dict(os.environ, {
        'ONLYOFFICE_SERVER_URL': 'http://test-onlyoffice:80',
        'MCP_SERVER_URL': 'http://test-mcp:8080',
        'GEMINI_API_KEY': 'test-key'
    })
    @patch('nodes.report_generator.requests.post')
    @patch('nodes.report_generator.genai')
    async def test_end_to_end_report_generation(self, mock_genai, mock_requests, sample_conversation_data, expected_structured_data):
        """Test de integración end-to-end"""
        # Mock de Gemini para extracción
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(expected_structured_data)
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock de respuestas HTTP
        def mock_post_side_effect(url, **kwargs):
            mock_resp = Mock()
            mock_resp.status_code = 200
            
            if "docbuilder" in url:
                # Respuesta de OnlyOffice
                mock_resp.json.return_value = {
                    "error": 0,
                    "fileUrl": "http://test/download/doc.docx"
                }
            elif "mcp" in url:
                # Respuesta de MCP
                mock_resp.json.return_value = {
                    "result": {
                        "success": True,
                        "attachment_id": 999
                    }
                }
            
            return mock_resp
        
        mock_requests.side_effect = mock_post_side_effect
        
        # Mock adicional para descarga de documento
        with patch('nodes.report_generator.requests.get') as mock_get:
            mock_get.return_value.content = b"fake_docx_content"
            
            # Ejecutar flujo completo
            result = await generate_report(sample_conversation_data)
            
            # Verificar resultado exitoso
            assert result["report_generated"] == True
            assert result["report_attachment_id"] == 999
            assert "structured_data" in result

if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--tb=short"])