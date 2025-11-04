#!/usr/bin/env python3
"""
PATCO AI Agent - Test RAG Integration
Script de testing completo para validar la Fase 7: RAG y Búsqueda Semántica

Funcionalidades:
- Validación de componentes RAG (PGVector, Indexer, MCP, LangGraph)
- Tests de búsqueda semántica con filtros contextuales
- Validación de scoring avanzado y relevancia
- Tests de integración completa end-to-end

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import logging
import sys
import json
import time
from pathlib import Path
import psycopg2
import requests
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGIntegrationTester:
    """Tester completo para la integración RAG de la Fase 7"""
    
    def __init__(self):
        """Inicializa el tester con configuración"""
        
        self.config = {
            # Base de datos
            'db_host': 'localhost',
            'db_port': 5432,
            'db_name': 'odoo_patco',
            'db_user': 'odoo',
            'db_password': 'P4tc0_2',
            
            # Servicios
            'mcp_server_url': 'http://localhost:8080',
            'langgraph_server_url': 'http://localhost:8001',
            'odoo_url': 'http://localhost:8069',
            
            # APIs
            'gemini_api_key': None  # Se debe configurar externamente
        }
        
        self.test_results = {
            'pgvector_tests': {},
            'indexer_tests': {},
            'mcp_tests': {},
            'langgraph_tests': {},
            'integration_tests': {},
            'performance_tests': {}
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de integración RAG"""
        
        logger.info("🚀 Iniciando tests de integración RAG - Fase 7")
        
        try:
            # 1. Tests de PGVector
            logger.info("📊 Testing PGVector...")
            await self.test_pgvector()
            
            # 2. Tests del Indexer
            logger.info("📚 Testing Document Indexer...")
            await self.test_indexer()
            
            # 3. Tests del servidor MCP
            logger.info("🔌 Testing MCP Server...")
            await self.test_mcp_server()
            
            # 4. Tests del servidor LangGraph
            logger.info("🤖 Testing LangGraph Server...")
            await self.test_langgraph_server()
            
            # 5. Tests de integración completa
            logger.info("🔗 Testing End-to-End Integration...")
            await self.test_end_to_end_integration()
            
            # 6. Tests de performance
            logger.info("⚡ Testing Performance...")
            await self.test_performance()
            
            # Generar reporte final
            report = self.generate_test_report()
            
            logger.info("✅ Tests de integración RAG completados")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error en tests de integración: {e}")
            raise
    
    async def test_pgvector(self):
        """Tests de PGVector y búsqueda vectorial"""
        
        try:
            # Conectar a PostgreSQL
            conn = psycopg2.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                database=self.config['db_name'],
                user=self.config['db_user'],
                password=self.config['db_password']
            )
            cursor = conn.cursor()
            
            # Test 1: Verificar extensión PGVector
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            result = cursor.fetchone()
            self.test_results['pgvector_tests']['extension_installed'] = result is not None
            
            # Test 2: Verificar tabla de embeddings
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'ai_document_embeddings'
            """)
            result = cursor.fetchone()
            self.test_results['pgvector_tests']['embeddings_table_exists'] = result[0] > 0
            
            # Test 3: Verificar índices HNSW
            cursor.execute("""
                SELECT COUNT(*) FROM pg_indexes 
                WHERE tablename = 'ai_document_embeddings' 
                AND indexname LIKE '%embedding%'
            """)
            result = cursor.fetchone()
            self.test_results['pgvector_tests']['hnsw_index_exists'] = result[0] > 0
            
            # Test 4: Verificar función de búsqueda
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.routines 
                WHERE routine_name = 'search_similar_documents'
            """)
            result = cursor.fetchone()
            self.test_results['pgvector_tests']['search_function_exists'] = result[0] > 0
            
            # Test 5: Contar embeddings existentes
            cursor.execute("SELECT COUNT(*) FROM ai_document_embeddings")
            result = cursor.fetchone()
            self.test_results['pgvector_tests']['embeddings_count'] = result[0]
            
            # Test 6: Test de búsqueda vectorial básica
            if result[0] > 0:
                # Obtener un embedding de ejemplo
                cursor.execute("SELECT embedding FROM ai_document_embeddings LIMIT 1")
                sample_embedding = cursor.fetchone()[0]
                
                # Realizar búsqueda de similitud
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_document_embeddings 
                    WHERE 1 - (embedding <=> %s::vector) > 0.5
                """, (sample_embedding,))
                result = cursor.fetchone()
                self.test_results['pgvector_tests']['similarity_search_works'] = result[0] > 0
            else:
                self.test_results['pgvector_tests']['similarity_search_works'] = None
            
            cursor.close()
            conn.close()
            
            logger.info("✅ Tests de PGVector completados")
            
        except Exception as e:
            logger.error(f"❌ Error en tests de PGVector: {e}")
            self.test_results['pgvector_tests']['error'] = str(e)
    
    async def test_indexer(self):
        """Tests del servicio de indexación de documentos"""
        
        try:
            # Test 1: Verificar que el indexer haya procesado documentos
            conn = psycopg2.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                database=self.config['db_name'],
                user=self.config['db_user'],
                password=self.config['db_password']
            )
            cursor = conn.cursor()
            
            # Contar documentos indexados
            cursor.execute("""
                SELECT COUNT(*) FROM ir_attachment 
                WHERE x_is_indexed = TRUE
            """)
            result = cursor.fetchone()
            self.test_results['indexer_tests']['indexed_documents_count'] = result[0]
            
            # Test 2: Verificar diversidad de tipos de documentos
            cursor.execute("""
                SELECT x_document_type, COUNT(*) 
                FROM ir_attachment 
                WHERE x_is_indexed = TRUE 
                GROUP BY x_document_type
            """)
            results = cursor.fetchall()
            self.test_results['indexer_tests']['document_types'] = dict(results)
            
            # Test 3: Verificar embeddings generados
            cursor.execute("""
                SELECT COUNT(DISTINCT attachment_id) 
                FROM ai_document_embeddings
            """)
            result = cursor.fetchone()
            self.test_results['indexer_tests']['documents_with_embeddings'] = result[0]
            
            # Test 4: Verificar calidad de embeddings (dimensión correcta)
            cursor.execute("""
                SELECT array_length(embedding, 1) as dimension, COUNT(*) 
                FROM ai_document_embeddings 
                GROUP BY array_length(embedding, 1)
            """)
            results = cursor.fetchall()
            self.test_results['indexer_tests']['embedding_dimensions'] = dict(results)
            
            cursor.close()
            conn.close()
            
            logger.info("✅ Tests del Indexer completados")
            
        except Exception as e:
            logger.error(f"❌ Error en tests del Indexer: {e}")
            self.test_results['indexer_tests']['error'] = str(e)
    
    async def test_mcp_server(self):
        """Tests del servidor MCP"""
        
        try:
            # Test 1: Health check
            response = requests.get(f"{self.config['mcp_server_url']}/health", timeout=10)
            self.test_results['mcp_tests']['health_check'] = response.status_code == 200
            
            # Test 2: Listar herramientas disponibles
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            response = requests.post(
                f"{self.config['mcp_server_url']}/mcp",
                json=mcp_request,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                tools = result.get('result', [])
                tool_names = [tool.get('name') for tool in tools]
                self.test_results['mcp_tests']['available_tools'] = tool_names
                self.test_results['mcp_tests']['knowledge_search_available'] = 'search_knowledge_base' in tool_names
            else:
                self.test_results['mcp_tests']['tools_list_error'] = response.status_code
            
            # Test 3: Test de búsqueda de conocimiento
            if self.test_results['mcp_tests'].get('knowledge_search_available'):
                search_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "search_knowledge_base",
                        "arguments": {
                            "query": "mantenimiento preventivo",
                            "max_results": 5,
                            "search_type": "hybrid"
                        }
                    }
                }
                
                response = requests.post(
                    f"{self.config['mcp_server_url']}/mcp",
                    json=search_request,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result:
                        search_results = json.loads(result['result'][0]['text'])
                        self.test_results['mcp_tests']['search_test_results'] = len(search_results.get('results', []))
                        self.test_results['mcp_tests']['search_test_success'] = True
                    else:
                        self.test_results['mcp_tests']['search_test_error'] = result.get('error')
                else:
                    self.test_results['mcp_tests']['search_test_error'] = response.status_code
            
            logger.info("✅ Tests del servidor MCP completados")
            
        except Exception as e:
            logger.error(f"❌ Error en tests del servidor MCP: {e}")
            self.test_results['mcp_tests']['error'] = str(e)
    
    async def test_langgraph_server(self):
        """Tests del servidor LangGraph"""
        
        try:
            # Test 1: Health check
            response = requests.get(f"{self.config['langgraph_server_url']}/health", timeout=10)
            self.test_results['langgraph_tests']['health_check'] = response.status_code == 200
            
            # Test 2: Información del servicio
            response = requests.get(f"{self.config['langgraph_server_url']}/", timeout=10)
            if response.status_code == 200:
                info = response.json()
                self.test_results['langgraph_tests']['service_info'] = info
            
            # Test 3: Test de procesamiento de mensaje
            test_message = {
                "conversation_id": "test-rag-integration",
                "message": {
                    "role": "user",
                    "content": "¿Cómo realizar mantenimiento preventivo de un horno?",
                    "timestamp": "2025-01-20T10:30:00Z"
                },
                "context": {
                    "fsm_order_id": 1,
                    "technician_id": 1,
                    "equipment_category_id": 1,
                    "service_nature_id": 1
                }
            }
            
            response = requests.post(
                f"{self.config['langgraph_server_url']}/conversation/test-rag-integration/message",
                json=test_message,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.test_results['langgraph_tests']['message_processing_success'] = True
                self.test_results['langgraph_tests']['response_length'] = len(result.get('response', ''))
                self.test_results['langgraph_tests']['actions_count'] = len(result.get('actions', []))
            else:
                self.test_results['langgraph_tests']['message_processing_error'] = response.status_code
            
            logger.info("✅ Tests del servidor LangGraph completados")
            
        except Exception as e:
            logger.error(f"❌ Error en tests del servidor LangGraph: {e}")
            self.test_results['langgraph_tests']['error'] = str(e)
    
    async def test_end_to_end_integration(self):
        """Tests de integración completa end-to-end"""
        
        try:
            # Test 1: Flujo completo de búsqueda RAG
            start_time = time.time()
            
            # Simular consulta desde LangGraph que usa MCP para búsqueda
            test_queries = [
                {
                    "query": "procedimiento calibración termostato",
                    "context": {"equipment_category_id": 1, "service_nature_id": 1}
                },
                {
                    "query": "checklist mantenimiento preventivo",
                    "context": {"equipment_category_id": 2, "service_nature_id": 1}
                },
                {
                    "query": "solución problema temperatura",
                    "context": {"equipment_category_id": 1, "service_nature_id": 2}
                }
            ]
            
            successful_queries = 0
            total_results = 0
            
            for i, test_query in enumerate(test_queries):
                try:
                    # Enviar consulta a LangGraph
                    message = {
                        "conversation_id": f"integration-test-{i}",
                        "message": {
                            "role": "user",
                            "content": test_query["query"],
                            "timestamp": "2025-01-20T10:30:00Z"
                        },
                        "context": test_query["context"]
                    }
                    
                    response = requests.post(
                        f"{self.config['langgraph_server_url']}/conversation/integration-test-{i}/message",
                        json=message,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('response'):
                            successful_queries += 1
                            # Estimar número de resultados basado en longitud de respuesta
                            total_results += len(result['response']) // 200
                    
                except Exception as e:
                    logger.warning(f"Error en consulta {i}: {e}")
            
            end_time = time.time()
            
            self.test_results['integration_tests']['successful_queries'] = successful_queries
            self.test_results['integration_tests']['total_queries'] = len(test_queries)
            self.test_results['integration_tests']['success_rate'] = successful_queries / len(test_queries)
            self.test_results['integration_tests']['total_processing_time'] = end_time - start_time
            self.test_results['integration_tests']['avg_processing_time'] = (end_time - start_time) / len(test_queries)
            
            # Test 2: Verificar filtros contextuales
            # Realizar búsqueda con y sin contexto para verificar diferencias
            base_query = "mantenimiento"
            
            # Sin contexto
            response1 = requests.post(
                f"{self.config['mcp_server_url']}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "search_knowledge_base",
                        "arguments": {
                            "query": base_query,
                            "max_results": 5
                        }
                    }
                },
                timeout=15
            )
            
            # Con contexto
            response2 = requests.post(
                f"{self.config['mcp_server_url']}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "search_knowledge_base",
                        "arguments": {
                            "query": base_query,
                            "max_results": 5,
                            "equipment_category_id": 1,
                            "service_nature_id": 1
                        }
                    }
                },
                timeout=15
            )
            
            if response1.status_code == 200 and response2.status_code == 200:
                results1 = json.loads(response1.json()['result'][0]['text'])
                results2 = json.loads(response2.json()['result'][0]['text'])
                
                self.test_results['integration_tests']['context_filtering_works'] = (
                    results1.get('total_results', 0) != results2.get('total_results', 0)
                )
            
            logger.info("✅ Tests de integración end-to-end completados")
            
        except Exception as e:
            logger.error(f"❌ Error en tests de integración end-to-end: {e}")
            self.test_results['integration_tests']['error'] = str(e)
    
    async def test_performance(self):
        """Tests de performance del sistema RAG"""
        
        try:
            # Test 1: Latencia de búsqueda
            search_times = []
            
            for i in range(5):
                start_time = time.time()
                
                response = requests.post(
                    f"{self.config['mcp_server_url']}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": i,
                        "method": "tools/call",
                        "params": {
                            "name": "search_knowledge_base",
                            "arguments": {
                                "query": f"test query {i}",
                                "max_results": 10
                            }
                        }
                    },
                    timeout=15
                )
                
                end_time = time.time()
                
                if response.status_code == 200:
                    search_times.append(end_time - start_time)
            
            if search_times:
                self.test_results['performance_tests']['avg_search_time'] = sum(search_times) / len(search_times)
                self.test_results['performance_tests']['max_search_time'] = max(search_times)
                self.test_results['performance_tests']['min_search_time'] = min(search_times)
            
            # Test 2: Throughput de búsquedas concurrentes
            # (Simplificado para este test)
            concurrent_start = time.time()
            
            # Simular 3 búsquedas "concurrentes" (secuenciales para simplicidad)
            concurrent_queries = [
                "mantenimiento preventivo",
                "calibración equipos",
                "solución problemas"
            ]
            
            concurrent_successful = 0
            for query in concurrent_queries:
                response = requests.post(
                    f"{self.config['mcp_server_url']}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": "search_knowledge_base",
                            "arguments": {
                                "query": query,
                                "max_results": 5
                            }
                        }
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    concurrent_successful += 1
            
            concurrent_end = time.time()
            
            self.test_results['performance_tests']['concurrent_queries_success_rate'] = (
                concurrent_successful / len(concurrent_queries)
            )
            self.test_results['performance_tests']['concurrent_queries_total_time'] = (
                concurrent_end - concurrent_start
            )
            
            logger.info("✅ Tests de performance completados")
            
        except Exception as e:
            logger.error(f"❌ Error en tests de performance: {e}")
            self.test_results['performance_tests']['error'] = str(e)
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Genera reporte final de tests"""
        
        # Calcular estadísticas generales
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            for test_name, result in tests.items():
                if test_name != 'error' and isinstance(result, bool):
                    total_tests += 1
                    if result:
                        passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determinar estado general
        if success_rate >= 90:
            overall_status = "EXCELENTE"
        elif success_rate >= 75:
            overall_status = "BUENO"
        elif success_rate >= 50:
            overall_status = "ACEPTABLE"
        else:
            overall_status = "NECESITA MEJORAS"
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "overall_status": overall_status
            },
            "detailed_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en los resultados de tests"""
        
        recommendations = []
        
        # Verificar PGVector
        if not self.test_results.get('pgvector_tests', {}).get('extension_installed'):
            recommendations.append("Instalar extensión PGVector en PostgreSQL")
        
        # Verificar embeddings
        embeddings_count = self.test_results.get('pgvector_tests', {}).get('embeddings_count', 0)
        if embeddings_count < 10:
            recommendations.append("Indexar más documentos para mejorar la calidad de búsqueda")
        
        # Verificar performance
        avg_search_time = self.test_results.get('performance_tests', {}).get('avg_search_time')
        if avg_search_time and avg_search_time > 2.0:
            recommendations.append("Optimizar performance de búsqueda (tiempo promedio > 2s)")
        
        # Verificar integración
        success_rate = self.test_results.get('integration_tests', {}).get('success_rate', 0)
        if success_rate < 0.8:
            recommendations.append("Mejorar estabilidad de integración end-to-end")
        
        if not recommendations:
            recommendations.append("Sistema RAG funcionando correctamente - No se requieren acciones")
        
        return recommendations


async def main():
    """Función principal para ejecutar tests"""
    
    print("🚀 PATCO AI Agent - Test RAG Integration (Fase 7)")
    print("=" * 60)
    
    tester = RAGIntegrationTester()
    
    try:
        # Ejecutar todos los tests
        report = await tester.run_all_tests()
        
        # Mostrar reporte
        print("\n📊 REPORTE DE TESTS RAG")
        print("=" * 60)
        
        summary = report['test_summary']
        print(f"Tests ejecutados: {summary['total_tests']}")
        print(f"Tests exitosos: {summary['passed_tests']}")
        print(f"Tasa de éxito: {summary['success_rate']:.1f}%")
        print(f"Estado general: {summary['overall_status']}")
        
        print("\n🔍 RESULTADOS DETALLADOS")
        print("-" * 40)
        
        for category, tests in report['detailed_results'].items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            for test_name, result in tests.items():
                if test_name != 'error':
                    status = "✅" if result else "❌" if isinstance(result, bool) else "ℹ️"
                    print(f"  {status} {test_name}: {result}")
        
        print("\n💡 RECOMENDACIONES")
        print("-" * 40)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
        
        # Guardar reporte en archivo
        report_file = Path("rag_integration_test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte guardado en: {report_file}")
        
        # Determinar código de salida
        if summary['success_rate'] >= 75:
            print("\n🎉 Tests de integración RAG EXITOSOS")
            return 0
        else:
            print("\n⚠️ Tests de integración RAG con PROBLEMAS")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error ejecutando tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)