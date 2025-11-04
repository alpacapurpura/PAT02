#!/usr/bin/env python3
"""
Nodo de Búsqueda RAG para LangGraph

Realiza búsquedas semánticas en la base de conocimiento usando
el servidor MCP y genera respuestas contextualizadas.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

from typing import Dict, Any, List

import google.generativeai as genai
import structlog

from schemas import ConversationState, RAGResult
from utils.logging_config import LoggingMixin
from utils.mcp_client import MCPClient
from config import settings

logger = structlog.get_logger(__name__)


class RAGSearchNode(LoggingMixin):
    """Nodo para búsqueda RAG y generación de respuestas contextualizadas."""
    
    def __init__(self, mcp_client: MCPClient):
        """
        Inicializa el nodo de búsqueda RAG.
        
        Args:
            mcp_client: Cliente MCP para herramientas
        """
        self.mcp_client = mcp_client
        self._initialized = False
        
        # Configurar Gemini API
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            self.logger.warning("⚠️ GEMINI_API_KEY no configurada")
    
    async def initialize(self) -> None:
        """Inicializa el nodo."""
        
        try:
            self.log_method_call("initialize")
            
            # Verificar configuración
            if not self.model:
                self.logger.warning("⚠️ Modelo Gemini no disponible para RAG")
            
            self._initialized = True
            self.log_method_result("initialize")
            
        except Exception as e:
            self.log_error("initialize", e)
            raise
    
    async def process(self, state: ConversationState) -> ConversationState:
        """
        Procesa búsqueda RAG y genera respuesta.
        
        Args:
            state: Estado actual de la conversación
            
        Returns:
            Estado actualizado con resultados RAG y respuesta
        """
        
        try:
            self.log_method_call(
                "process",
                messages_count=len(state.messages),
                intent=state.current_intent
            )
            
            if not state.messages:
                self.logger.warning("⚠️ No hay mensajes para procesar")
                return state
            
            # Obtener consulta del último mensaje
            last_message = state.messages[-1]
            query = last_message.content
            
            # Realizar búsqueda RAG
            rag_results = await self._perform_rag_search(query, state.context)
            
            # Generar respuesta usando RAG
            response = await self._generate_rag_response(query, rag_results, state.context)
            
            # Actualizar estado
            state.rag_results = rag_results
            state.response = response
            
            # Agregar metadatos de procesamiento
            state.processing_metadata.update({
                "rag_search": {
                    "query_length": len(query),
                    "results_count": len(rag_results),
                    "avg_similarity": sum(r.similarity for r in rag_results) / len(rag_results) if rag_results else 0,
                    "response_generated": bool(response)
                }
            })
            
            self.log_method_result(
                "process",
                results_count=len(rag_results),
                response_length=len(response) if response else 0
            )
            
            return state
            
        except Exception as e:
            self.log_error("process", e)
            state.error_message = f"Error en búsqueda RAG: {str(e)}"
            state.response = "Lo siento, tuve problemas accediendo a la base de conocimiento. ¿Puedes reformular tu pregunta?"
            return state
    
    async def _perform_rag_search(self, query: str, context: Dict[str, Any]) -> List[RAGResult]:
        """
        Realiza búsqueda RAG usando el servidor MCP con filtros contextuales avanzados.
        
        Args:
            query: Consulta de búsqueda
            context: Contexto de la conversación
            
        Returns:
            Lista de resultados RAG
        """
        
        try:
            self.log_method_call("_perform_rag_search", query_length=len(query))
            
            # Preparar parámetros de búsqueda con filtros contextuales avanzados
            search_params = {
                "query": query,
                "max_results": 8,  # Aumentado para mejor cobertura
                "similarity_threshold": 0.65,  # Reducido para más resultados
                "search_type": "hybrid"  # Búsqueda híbrida por defecto
            }
            
            # Agregar filtros contextuales avanzados
            if context.get("equipment_category_id"):
                search_params["equipment_category_id"] = context["equipment_category_id"]
            
            if context.get("equipment_ids"):
                search_params["equipment_ids"] = context["equipment_ids"]
            
            if context.get("service_nature_id"):
                search_params["service_nature_id"] = context["service_nature_id"]
            
            if context.get("service_area_id"):
                search_params["service_area_id"] = context["service_area_id"]
            
            if context.get("service_complexity_id"):
                search_params["service_complexity_id"] = context["service_complexity_id"]
            
            # Determinar tipos de documentos según la consulta y contexto
            document_types = self._determine_document_types_advanced(query, context)
            if document_types:
                search_params["document_types"] = document_types
            
            # Agregar boost para documentos recientes
            search_params["boost_recent"] = True
            
            # Incluir metadatos para scoring avanzado
            search_params["include_metadata"] = True
            
            self.logger.info(f"🔍 Búsqueda RAG avanzada con filtros: {search_params}")
            
            # Llamar al servidor MCP
            mcp_result = await self.mcp_client.search_knowledge_base(**search_params)
            
            # Convertir resultados a objetos RAGResult
            rag_results = []
            if mcp_result and "results" in mcp_result:
                for result in mcp_result["results"]:
                    rag_result = RAGResult(
                        attachment_id=result.get("attachment_id", 0),
                        content=result.get("content", ""),
                        similarity=result.get("final_score", result.get("similarity", 0.0)),
                        metadata=result.get("metadata", {}),
                        document_name=result.get("document_name"),
                        document_type=result.get("document_type")
                    )
                    
                    # Agregar información de scoring avanzado
                    if "scoring_factors" in result:
                        rag_result.metadata["scoring_factors"] = result["scoring_factors"]
                    
                    if "context_match" in result:
                        rag_result.metadata["context_match"] = result["context_match"]
                    
                    if "relevance_score" in result:
                        rag_result.metadata["relevance_score"] = result["relevance_score"]
                    
                    rag_results.append(rag_result)
            
            # Aplicar post-procesamiento para mejorar relevancia
            rag_results = self._post_process_results(rag_results, query, context)
            
            self.log_method_result(
                "_perform_rag_search",
                results_count=len(rag_results),
                avg_similarity=sum(r.similarity for r in rag_results) / len(rag_results) if rag_results else 0
            )
            
            return rag_results
            
        except Exception as e:
            self.log_error("_perform_rag_search", e)
            return []
    
    def _determine_document_types_advanced(self, query: str, context: Dict[str, Any]) -> List[str]:
        """
        Determina tipos de documentos relevantes según la consulta y contexto avanzado.
        
        Args:
            query: Consulta de búsqueda
            context: Contexto de la conversación
            
        Returns:
            Lista de tipos de documentos priorizados
        """
        
        query_lower = query.lower()
        document_types = []
        
        # Análisis de palabras clave en la consulta
        manual_keywords = [
            "manual", "instrucciones", "especificaciones", "características",
            "funcionamiento", "operación", "descripción", "qué es", "cómo funciona"
        ]
        
        procedure_keywords = [
            "procedimiento", "pasos", "cómo", "proceso", "método", "técnica",
            "instalación", "configuración", "calibración", "ajuste", "reparación"
        ]
        
        checklist_keywords = [
            "checklist", "lista", "verificar", "revisar", "comprobar", "inspeccionar",
            "antes de", "después de", "entrada", "salida", "control"
        ]
        
        troubleshooting_keywords = [
            "problema", "error", "falla", "no funciona", "diagnóstico", "solución",
            "reparar", "arreglar", "troubleshooting", "qué hacer si"
        ]
        
        # Determinar tipos basados en palabras clave
        if any(keyword in query_lower for keyword in procedure_keywords):
            document_types.append("procedure")
        
        if any(keyword in query_lower for keyword in manual_keywords):
            document_types.append("manual")
        
        if any(keyword in query_lower for keyword in checklist_keywords):
            document_types.append("checklist")
        
        if any(keyword in query_lower for keyword in troubleshooting_keywords):
            document_types.extend(["procedure", "manual"])
        
        # Análisis contextual basado en estado FSM
        fsm_state = context.get("fsm_state")
        if fsm_state:
            if fsm_state in ["new", "assigned"]:
                # Al inicio: priorizar manuales y procedimientos de preparación
                if "manual" not in document_types:
                    document_types.append("manual")
                if "checklist" not in document_types:
                    document_types.append("checklist")
            
            elif fsm_state == "in_progress":
                # Durante trabajo: priorizar procedimientos y troubleshooting
                if "procedure" not in document_types:
                    document_types.insert(0, "procedure")
                if "manual" not in document_types:
                    document_types.append("manual")
            
            elif fsm_state in ["done", "completed"]:
                # Al final: priorizar checklists de salida y reportes
                if "checklist" not in document_types:
                    document_types.insert(0, "checklist")
        
        # Análisis por tipo de equipo
        equipment_category_id = context.get("equipment_category_id")
        if equipment_category_id:
            # Para equipos complejos, priorizar manuales
            if equipment_category_id in [1, 2, 3]:  # IDs de equipos complejos
                if "manual" not in document_types:
                    document_types.insert(0, "manual")
        
        # Análisis por naturaleza de servicio
        service_nature_id = context.get("service_nature_id")
        if service_nature_id:
            if service_nature_id == 1:  # Mantenimiento preventivo
                if "checklist" not in document_types:
                    document_types.insert(0, "checklist")
            elif service_nature_id == 2:  # Mantenimiento correctivo
                if "procedure" not in document_types:
                    document_types.insert(0, "procedure")
            elif service_nature_id == 3:  # Instalación
                if "manual" not in document_types:
                    document_types.insert(0, "manual")
        
        # Si no se determinaron tipos específicos, usar orden por defecto
        if not document_types:
            document_types = ["procedure", "manual", "checklist"]
        
        # Limitar a máximo 4 tipos para eficiencia
        return document_types[:4]
    
    def _post_process_results(
        self, 
        results: List[RAGResult], 
        query: str, 
        context: Dict[str, Any]
    ) -> List[RAGResult]:
        """
        Post-procesa resultados para mejorar relevancia y diversidad.
        
        Args:
            results: Resultados RAG originales
            query: Consulta original
            context: Contexto de la conversación
            
        Returns:
            Resultados optimizados
        """
        
        if not results:
            return results
        
        # 1. Filtrar resultados con similitud muy baja
        filtered_results = [r for r in results if r.similarity > 0.3]
        
        # 2. Diversificar por tipo de documento
        diversified_results = self._diversify_by_document_type(filtered_results)
        
        # 3. Boost por coincidencia exacta de palabras clave
        boosted_results = self._boost_keyword_matches(diversified_results, query)
        
        # 4. Reordenar por similitud final
        boosted_results.sort(key=lambda x: x.similarity, reverse=True)
        
        # 5. Limitar a top 5 para respuesta final
        return boosted_results[:5]
    
    def _diversify_by_document_type(self, results: List[RAGResult]) -> List[RAGResult]:
        """Diversifica resultados para incluir diferentes tipos de documentos"""
        
        if len(results) <= 3:
            return results
        
        # Agrupar por tipo de documento
        by_type = {}
        for result in results:
            doc_type = result.document_type or "other"
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(result)
        
        # Seleccionar máximo 2 resultados por tipo
        diversified = []
        for doc_type, type_results in by_type.items():
            # Ordenar por similitud y tomar los mejores
            type_results.sort(key=lambda x: x.similarity, reverse=True)
            diversified.extend(type_results[:2])
        
        # Ordenar resultado final por similitud
        diversified.sort(key=lambda x: x.similarity, reverse=True)
        
        return diversified
    
    def _boost_keyword_matches(self, results: List[RAGResult], query: str) -> List[RAGResult]:
        """Aplica boost a resultados con coincidencias exactas de palabras clave"""
        
        # Extraer palabras clave de la consulta
        import re
        query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
        
        for result in results:
            content_words = set(re.findall(r'\b\w{3,}\b', result.content.lower()))
            
            # Calcular intersección de palabras
            common_words = query_words & content_words
            
            if common_words:
                # Boost proporcional al número de palabras coincidentes
                boost_factor = 1 + (len(common_words) / len(query_words)) * 0.2
                result.similarity *= boost_factor
                
                # Agregar información de boost a metadatos
                if not result.metadata:
                    result.metadata = {}
                result.metadata["keyword_boost"] = {
                    "common_words": list(common_words),
                    "boost_factor": boost_factor
                }
        
        return results

    def _determine_document_types_advanced(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Determina tipos de documentos avanzados basado en análisis de consulta"""
        query_lower = query.lower()
        document_types = []
        
        # Palabras clave para diferentes tipos de documentos
        manual_keywords = [
            "manual", "guía", "instructivo", "documentación", "especificación"
        ]
        
        procedure_keywords = [
            "procedimiento", "proceso", "pasos", "cómo", "método",
            "instalación", "reparación", "mantenimiento", "calibración"
        ]
        
        checklist_keywords = [
            "checklist", "lista", "verificar", "revisar", "comprobar",
            "inspección", "control", "validación"
        ]
        
        # Verificar tipos de documentos
        if any(keyword in query_lower for keyword in manual_keywords):
            document_types.append("manual")
        
        if any(keyword in query_lower for keyword in procedure_keywords):
            document_types.append("procedure")
        
        if any(keyword in query_lower for keyword in checklist_keywords):
            document_types.append("checklist")
        
        # Si no se detecta tipo específico, usar todos los principales
        if not document_types:
            document_types = ["manual", "procedure", "checklist"]
        
        return document_types
    
    async def _generate_rag_response(
        self, 
        query: str, 
        rag_results: List[RAGResult], 
        context: Dict[str, Any]
    ) -> str:
        """
        Genera respuesta usando resultados RAG.
        
        Args:
            query: Consulta original
            rag_results: Resultados de búsqueda RAG
            context: Contexto de la conversación
            
        Returns:
            Respuesta generada
        """
        
        try:
            self.log_method_call(
                "_generate_rag_response",
                query_length=len(query),
                results_count=len(rag_results)
            )
            
            # Si no hay resultados, respuesta genérica
            if not rag_results:
                return self._generate_no_results_response(query)
            
            # Si Gemini no está disponible, respuesta básica
            if not self.model:
                return self._generate_basic_response(query, rag_results)
            
            # Generar respuesta con Gemini
            return await self._generate_gemini_response(query, rag_results, context)
            
        except Exception as e:
            self.log_error("_generate_rag_response", e)
            return "Lo siento, tuve problemas generando la respuesta. ¿Puedes ser más específico en tu pregunta?"
    
    def _generate_no_results_response(self, query: str) -> str:
        """Genera respuesta cuando no hay resultados RAG."""
        
        return f"""
        No encontré información específica sobre "{query}" en la base de conocimiento.
        
        Te sugiero:
        • Reformular la pregunta con términos más específicos
        • Mencionar el modelo o tipo de equipo
        • Describir el problema con más detalle
        
        ¿Puedes proporcionar más contexto sobre lo que necesitas?
        """.strip()
    
    def _generate_basic_response(self, query: str, rag_results: List[RAGResult]) -> str:
        """Genera respuesta básica sin Gemini."""
        
        # Tomar los mejores resultados
        top_results = sorted(rag_results, key=lambda x: x.similarity, reverse=True)[:3]
        
        response_parts = [
            f"Encontré información relevante sobre tu consulta:",
            ""
        ]
        
        for i, result in enumerate(top_results, 1):
            # Truncar contenido si es muy largo
            content = result.content
            if len(content) > 300:
                content = content[:300] + "..."
            
            response_parts.append(f"**{i}. {result.document_name or 'Documento'}**")
            response_parts.append(content)
            response_parts.append("")
        
        response_parts.append("¿Te ayuda esta información? ¿Necesitas algo más específico?")
        
        return "\n".join(response_parts)
    
    async def _generate_gemini_response(
        self, 
        query: str, 
        rag_results: List[RAGResult], 
        context: Dict[str, Any]
    ) -> str:
        """Genera respuesta usando Gemini API."""
        
        try:
            # Construir contexto desde documentos
            context_parts = []
            for result in rag_results[:3]:  # Usar top 3 resultados
                doc_info = f"Documento: {result.document_name or 'Sin nombre'}"
                if result.document_type:
                    doc_info += f" (Tipo: {result.document_type})"
                
                context_parts.append(f"{doc_info}\nContenido: {result.content[:500]}...")
            
            knowledge_context = "\n\n".join(context_parts)
            
            # Construir información del servicio
            service_info = ""
            if context.get("fsm_order_id"):
                service_info += f"- Orden de servicio: {context['fsm_order_id']}\n"
            if context.get("equipment_ids"):
                service_info += f"- Equipos involucrados: {len(context['equipment_ids'])} equipos\n"
            if context.get("service_nature_id"):
                service_info += f"- Tipo de servicio: {context['service_nature_id']}\n"
            
            # Prompt para generar respuesta
            response_prompt = f"""
            Eres un asistente técnico especializado que ayuda a técnicos de campo durante servicios de mantenimiento.
            
            Contexto del servicio actual:
            {service_info}
            
            Pregunta del técnico: "{query}"
            
            Información técnica disponible:
            {knowledge_context}
            
            Instrucciones para tu respuesta:
            - Responde de manera clara, concisa y práctica
            - Usa un tono profesional pero amigable
            - Incluye pasos específicos cuando sea apropiado
            - Si la información no es suficiente, dilo claramente y sugiere alternativas
            - Prioriza la seguridad en todas las recomendaciones
            - Usa viñetas o numeración para pasos o listas
            - Mantén la respuesta enfocada en la pregunta específica
            
            Respuesta:
            """
            
            # Llamar a Gemini
            response = self.model.generate_content(response_prompt)
            
            self.log_method_result(
                "_generate_gemini_response",
                response_length=len(response.text)
            )
            
            return response.text
            
        except Exception as e:
            self.log_error("_generate_gemini_response", e)
            return self._generate_basic_response(query, rag_results)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del nodo."""
        
        return {
            "initialized": self._initialized,
            "gemini_available": self.model is not None,
            "mcp_client_connected": await self.mcp_client.is_connected() if self.mcp_client else False
        }