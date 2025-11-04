#!/usr/bin/env python3
"""
Nodo Generador de Respuestas para LangGraph

Genera respuestas finales para el usuario basándose en el contexto,
resultados RAG y acciones ejecutadas.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

from typing import Dict, Any

import google.generativeai as genai
import structlog

from schemas import ConversationState, ConversationMessage
from utils.logging_config import LoggingMixin
from utils.mcp_client import MCPClient
from config import settings

logger = structlog.get_logger(__name__)


class ResponseGeneratorNode(LoggingMixin):
    """Nodo para generación de respuestas finales al usuario."""
    
    def __init__(self, mcp_client: MCPClient):
        """
        Inicializa el nodo generador de respuestas.
        
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
                self.logger.warning("⚠️ Modelo Gemini no disponible para generación")
            
            self._initialized = True
            self.log_method_result("initialize")
            
        except Exception as e:
            self.log_error("initialize", e)
            raise
    
    async def process(self, state: ConversationState) -> ConversationState:
        """
        Genera respuesta final para el usuario.
        
        Args:
            state: Estado actual de la conversación
            
        Returns:
            Estado actualizado con respuesta final
        """
        
        try:
            self.log_method_call(
                "process",
                intent=state.current_intent,
                has_rag_results=bool(state.rag_results),
                actions_count=len(state.actions)
            )
            
            # Si ya hay una respuesta (ej. desde RAG), verificar si necesita mejora
            if state.response and not self._needs_enhancement(state):
                self.logger.debug("✅ Respuesta existente es suficiente")
                return state
            
            # Generar respuesta según el contexto
            response = await self._generate_contextual_response(state)
            
            # Actualizar estado
            state.response = response
            
            # Agregar metadatos de procesamiento
            state.processing_metadata.update({
                "response_generator": {
                    "response_length": len(response) if response else 0,
                    "generation_method": self._get_generation_method(state),
                    "enhanced_existing": bool(state.response and self._needs_enhancement(state))
                }
            })
            
            self.log_method_result(
                "process",
                response_length=len(response) if response else 0
            )
            
            return state
            
        except Exception as e:
            self.log_error("process", e)
            state.error_message = f"Error generando respuesta: {str(e)}"
            state.response = "Lo siento, tuve un problema generando la respuesta. ¿Puedes intentar de nuevo?"
            return state
    
    def _needs_enhancement(self, state: ConversationState) -> bool:
        """
        Determina si una respuesta existente necesita mejora.
        
        Args:
            state: Estado de la conversación
            
        Returns:
            True si necesita mejora
        """
        
        if not state.response:
            return True
        
        # Si hay acciones ejecutadas, agregar información sobre ellas
        if state.actions:
            return True
        
        # Si la respuesta es muy corta y hay contexto adicional
        if len(state.response) < 50 and (state.context or state.rag_results):
            return True
        
        return False
    
    def _get_generation_method(self, state: ConversationState) -> str:
        """Determina el método de generación usado."""
        
        if state.rag_results:
            return "rag_enhanced"
        elif state.actions:
            return "action_based"
        elif state.current_intent == "greeting":
            return "greeting"
        elif state.current_intent == "confirmation":
            return "confirmation"
        else:
            return "contextual"
    
    async def _generate_contextual_response(self, state: ConversationState) -> str:
        """
        Genera respuesta contextual basada en el estado.
        
        Args:
            state: Estado de la conversación
            
        Returns:
            Respuesta generada
        """
        
        try:
            # Determinar tipo de respuesta según intención
            if state.current_intent == "greeting":
                return self._generate_greeting_response(state)
            
            elif state.current_intent == "confirmation":
                return self._generate_confirmation_response(state)
            
            elif state.actions:
                return await self._generate_action_response(state)
            
            elif state.rag_results:
                # Si ya hay respuesta RAG, mejorarla si es necesario
                if state.response:
                    return await self._enhance_rag_response(state)
                else:
                    return "Encontré información relevante, pero hubo un problema procesándola."
            
            else:
                return await self._generate_general_response(state)
                
        except Exception as e:
            self.log_error("_generate_contextual_response", e)
            return "Lo siento, tuve un problema generando la respuesta."
    
    def _generate_greeting_response(self, state: ConversationState) -> str:
        """Genera respuesta de saludo."""
        
        context = state.context
        
        # Información básica del servicio
        service_info = []
        if context.fsm_order_id:
            service_info.append(f"📋 Orden de servicio: {context.fsm_order_id}")
        
        if context.equipment_ids:
            equipment_count = len(context.equipment_ids)
            service_info.append(f"🔧 Equipos asignados: {equipment_count} equipo{'s' if equipment_count > 1 else ''}")
        
        if context.location:
            service_info.append(f"📍 Ubicación: {context.location}")
        
        # Construir respuesta
        response_parts = [
            "¡Hola! 👋 Soy tu asistente IA para el servicio técnico.",
            ""
        ]
        
        if service_info:
            response_parts.append("**Información del servicio:**")
            response_parts.extend(service_info)
            response_parts.append("")
        
        response_parts.extend([
            "Estoy aquí para ayudarte durante todo el proceso:",
            "• Responder preguntas técnicas",
            "• Buscar información en manuales y procedimientos", 
            "• Ayudarte con checklists y verificaciones",
            "• Registrar el progreso del trabajo",
            "",
            "¿Has llegado al sitio y estás listo para comenzar? 🚀"
        ])
        
        return "\n".join(response_parts)
    
    def _generate_confirmation_response(self, state: ConversationState) -> str:
        """Genera respuesta de confirmación."""
        
        last_message = state.messages[-1] if state.messages else None
        if not last_message:
            return "Entendido. ¿En qué más puedo ayudarte?"
        
        message_lower = last_message.content.lower()
        
        # Respuestas según el tipo de confirmación
        if any(word in message_lower for word in ["sí", "si", "yes", "ok", "correcto"]):
            return "Perfecto. ¿Cuál es el siguiente paso?"
        
        elif any(word in message_lower for word in ["no", "nope", "incorrecto"]):
            return "Entendido. ¿Puedes explicarme qué necesitas corregir o cambiar?"
        
        else:
            return "Entendido. ¿Hay algo más en lo que pueda ayudarte?"
    
    async def _generate_action_response(self, state: ConversationState) -> str:
        """Genera respuesta basada en acciones ejecutadas."""
        
        if not state.actions:
            return "No hay acciones pendientes. ¿En qué más puedo ayudarte?"
        
        # Agrupar acciones por tipo
        action_groups = {}
        for action in state.actions:
            action_type = action.action_type
            if action_type not in action_groups:
                action_groups[action_type] = []
            action_groups[action_type].append(action)
        
        response_parts = ["He procesado las siguientes acciones:", ""]
        
        # Describir acciones ejecutadas
        for action_type, actions in action_groups.items():
            if action_type == "update_fsm_order":
                response_parts.append("✅ **Orden FSM actualizada**")
                for action in actions:
                    if "stage" in action.parameters:
                        response_parts.append(f"   • Estado cambiado a: {action.parameters['stage']}")
                    if "notes" in action.parameters:
                        response_parts.append(f"   • Notas agregadas")
            
            elif action_type == "create_checklist":
                response_parts.append("📋 **Checklist creado**")
                response_parts.append("   • Lista de verificación lista para usar")
            
            elif action_type == "generate_report":
                response_parts.append("📄 **Reporte generado**")
                response_parts.append("   • Documento técnico creado automáticamente")
            
            else:
                response_parts.append(f"✅ **{action_type.replace('_', ' ').title()}**")
        
        response_parts.extend([
            "",
            "¿Necesitas realizar alguna otra acción o tienes alguna pregunta?"
        ])
        
        return "\n".join(response_parts)
    
    async def _enhance_rag_response(self, state: ConversationState) -> str:
        """Mejora una respuesta RAG existente."""
        
        if not self.model:
            return state.response  # Retornar respuesta original si no hay Gemini
        
        try:
            # Información adicional del contexto
            context_info = []
            if state.actions:
                context_info.append(f"Acciones ejecutadas: {len(state.actions)}")
            
            if state.entities.equipment_mentioned:
                context_info.append(f"Equipo mencionado: {state.entities.equipment_mentioned}")
            
            # Prompt para mejorar respuesta
            enhancement_prompt = f"""
            Mejora la siguiente respuesta técnica agregando información contextual útil.
            
            Respuesta original:
            {state.response}
            
            Contexto adicional:
            {'; '.join(context_info) if context_info else 'Ninguno'}
            
            Instrucciones:
            - Mantén el contenido técnico original
            - Agrega información contextual relevante al final
            - Usa un tono profesional pero amigable
            - Incluye una pregunta de seguimiento apropiada
            - Mantén la respuesta concisa
            
            Respuesta mejorada:
            """
            
            response = self.model.generate_content(enhancement_prompt)
            return response.text
            
        except Exception as e:
            self.log_error("_enhance_rag_response", e)
            return state.response  # Retornar original en caso de error
    
    async def _generate_general_response(self, state: ConversationState) -> str:
        """Genera respuesta general cuando no hay contexto específico."""
        
        last_message = state.messages[-1] if state.messages else None
        if not last_message:
            return "¿En qué puedo ayudarte?"
        
        # Respuestas según entidades detectadas
        if state.entities.equipment_mentioned:
            return f"""
            Veo que mencionas {state.entities.equipment_mentioned}. 
            
            Puedo ayudarte con:
            • Información técnica y especificaciones
            • Procedimientos de mantenimiento
            • Solución de problemas comunes
            • Checklists de verificación
            
            ¿Qué necesitas saber específicamente?
            """.strip()
        
        elif state.entities.problems:
            problems = ", ".join(state.entities.problems)
            return f"""
            Entiendo que hay problemas con: {problems}
            
            Para ayudarte mejor, necesito más información:
            • ¿Qué equipo está presentando el problema?
            • ¿Cuándo comenzó el problema?
            • ¿Has notado algún patrón o síntoma específico?
            
            Con estos detalles podré buscar la solución más apropiada.
            """.strip()
        
        elif state.entities.action:
            action = state.entities.action
            return f"""
            Entiendo que quieres {action}. 
            
            ¿Puedes ser más específico sobre:
            • ¿Qué equipo o componente?
            • ¿Necesitas un procedimiento específico?
            • ¿Hay algún problema particular?
            
            Así podré darte la información más precisa.
            """.strip()
        
        else:
            return """
            Estoy aquí para ayudarte con el servicio técnico.
            
            Puedo asistirte con:
            • Preguntas técnicas sobre equipos
            • Búsqueda de manuales y procedimientos
            • Solución de problemas
            • Registro de actividades y progreso
            
            ¿Qué necesitas?
            """.strip()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del nodo."""
        
        return {
            "initialized": self._initialized,
            "gemini_available": self.model is not None
        }