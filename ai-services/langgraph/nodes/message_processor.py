#!/usr/bin/env python3
"""
Nodo Procesador de Mensajes para LangGraph

Procesa mensajes del técnico, determina intenciones y extrae entidades
usando Google Gemini API.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import re
from typing import Dict, Any, List

import google.generativeai as genai
import structlog

from schemas import ConversationState, ExtractedEntities, VALID_INTENTS
from utils.logging_config import LoggingMixin
from utils.mcp_client import MCPClient
from config import settings

logger = structlog.get_logger(__name__)


class MessageProcessorNode(LoggingMixin):
    """Nodo para procesamiento de mensajes y análisis de intenciones."""
    
    def __init__(self, mcp_client: MCPClient):
        """
        Inicializa el nodo procesador de mensajes.
        
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
            self.logger.warning("⚠️ GEMINI_API_KEY no configurada, usando análisis básico")
    
    async def initialize(self) -> None:
        """Inicializa el nodo."""
        
        try:
            self.log_method_call("initialize")
            
            # Verificar configuración
            if not self.model:
                self.logger.warning("⚠️ Modelo Gemini no disponible")
            
            self._initialized = True
            self.log_method_result("initialize")
            
        except Exception as e:
            self.log_error("initialize", e)
            raise
    
    async def process(self, state: ConversationState) -> ConversationState:
        """
        Procesa el mensaje y determina la intención.
        
        Args:
            state: Estado actual de la conversación
            
        Returns:
            Estado actualizado con intención y entidades
        """
        
        try:
            self.log_method_call(
                "process",
                messages_count=len(state.messages),
                current_state=state.conversation_state
            )
            
            if not state.messages:
                self.logger.warning("⚠️ No hay mensajes para procesar")
                return state
            
            # Obtener último mensaje
            last_message = state.messages[-1]
            message_content = last_message.content
            
            # Analizar intención
            intent = await self._analyze_intent(message_content, state.context.dict())
            
            # Extraer entidades
            entities = await self._extract_entities(message_content, state.context.dict())
            
            # Actualizar estado
            state.current_intent = intent
            state.entities = entities
            
            # Agregar metadatos de procesamiento
            state.processing_metadata.update({
                "message_processor": {
                    "intent_detected": intent,
                    "entities_count": len(entities.dict()),
                    "message_length": len(message_content)
                }
            })
            
            self.log_method_result(
                "process",
                intent=intent,
                entities_count=len(entities.dict())
            )
            
            return state
            
        except Exception as e:
            self.log_error("process", e)
            state.error_message = f"Error procesando mensaje: {str(e)}"
            state.current_intent = "other"
            return state
    
    async def _analyze_intent(self, message: str, context: Dict[str, Any]) -> str:
        """
        Analiza la intención del mensaje.
        
        Args:
            message: Contenido del mensaje
            context: Contexto de la conversación
            
        Returns:
            Intención detectada
        """
        
        try:
            # Si Gemini está disponible, usar análisis avanzado
            if self.model:
                return await self._analyze_intent_with_gemini(message, context)
            else:
                return self._analyze_intent_basic(message)
                
        except Exception as e:
            self.logger.error("❌ Error analizando intención", error=str(e))
            return "other"
    
    async def _analyze_intent_with_gemini(self, message: str, context: Dict[str, Any]) -> str:
        """Análisis de intención usando Gemini API."""
        
        try:
            # Construir contexto para el prompt
            context_info = ""
            if context.get("fsm_order_id"):
                context_info += f"- Orden FSM: {context['fsm_order_id']}\n"
            if context.get("equipment_ids"):
                context_info += f"- Equipos: {len(context['equipment_ids'])} equipos\n"
            if context.get("service_nature_id"):
                context_info += f"- Tipo de servicio: {context['service_nature_id']}\n"
            
            # Prompt para análisis de intención
            intent_prompt = f"""
            Analiza el siguiente mensaje de un técnico de campo durante un servicio técnico y determina la intención principal.
            
            Contexto del servicio:
            {context_info}
            
            Mensaje del técnico: "{message}"
            
            Intenciones posibles:
            - question: El técnico hace una pregunta técnica o solicita información
            - action: El técnico quiere realizar una acción (actualizar estado, registrar datos, etc.)
            - status_update: El técnico reporta el estado actual o progreso del trabajo
            - greeting: Saludo inicial o mensaje de cortesía
            - confirmation: El técnico confirma algo o responde sí/no
            - complaint: El técnico reporta un problema o dificultad
            - request_help: El técnico solicita ayuda específica
            - other: Otro tipo de mensaje que no encaja en las categorías anteriores
            
            Instrucciones:
            - Responde SOLO con una palabra: la intención detectada
            - Considera el contexto del servicio técnico
            - Si hay duda, usa "other"
            
            Intención:
            """
            
            # Llamar a Gemini
            response = self.model.generate_content(intent_prompt)
            intent = response.text.strip().lower()
            
            # Validar que la intención sea válida
            if intent not in VALID_INTENTS:
                self.logger.warning(f"⚠️ Intención inválida detectada: {intent}, usando 'other'")
                intent = "other"
            
            return intent
            
        except Exception as e:
            self.logger.error("❌ Error en análisis Gemini", error=str(e))
            return self._analyze_intent_basic(message)
    
    def _analyze_intent_basic(self, message: str) -> str:
        """Análisis básico de intención usando reglas."""
        
        message_lower = message.lower()
        
        # Patrones para diferentes intenciones
        question_patterns = [
            r'\?', r'cómo', r'qué', r'cuál', r'dónde', r'cuándo', r'por qué',
            r'help', r'ayuda', r'no sé', r'no entiendo'
        ]
        
        action_patterns = [
            r'actualizar', r'cambiar', r'modificar', r'registrar', r'anotar',
            r'completar', r'terminar', r'finalizar', r'marcar'
        ]
        
        status_patterns = [
            r'terminé', r'completé', r'listo', r'hecho', r'finalizado',
            r'en progreso', r'trabajando', r'revisando'
        ]
        
        greeting_patterns = [
            r'hola', r'buenos días', r'buenas tardes', r'saludos',
            r'hello', r'hi'
        ]
        
        confirmation_patterns = [
            r'^sí$', r'^si$', r'^yes$', r'^ok$', r'^okay$', r'^correcto$',
            r'^no$', r'^nope$', r'^incorrecto$'
        ]
        
        complaint_patterns = [
            r'problema', r'error', r'falla', r'no funciona', r'roto',
            r'dañado', r'defectuoso'
        ]
        
        # Verificar patrones en orden de prioridad
        if any(re.search(pattern, message_lower) for pattern in greeting_patterns):
            return "greeting"
        
        if any(re.search(pattern, message_lower) for pattern in confirmation_patterns):
            return "confirmation"
        
        if any(re.search(pattern, message_lower) for pattern in complaint_patterns):
            return "complaint"
        
        if any(re.search(pattern, message_lower) for pattern in question_patterns):
            return "question"
        
        if any(re.search(pattern, message_lower) for pattern in action_patterns):
            return "action"
        
        if any(re.search(pattern, message_lower) for pattern in status_patterns):
            return "status_update"
        
        return "other"
    
    async def _extract_entities(self, message: str, context: Dict[str, Any]) -> ExtractedEntities:
        """
        Extrae entidades del mensaje.
        
        Args:
            message: Contenido del mensaje
            context: Contexto de la conversación
            
        Returns:
            Entidades extraídas
        """
        
        entities = ExtractedEntities()
        
        try:
            # Extraer números (mediciones, IDs, etc.)
            numbers = re.findall(r'\d+\.?\d*', message)
            entities.numbers = numbers
            
            # Extraer menciones de equipos
            equipment_keywords = [
                "equipo", "horno", "refrigerador", "aire acondicionado", "aire", 
                "cocina", "lavadora", "secadora", "bomba", "motor", "compresor",
                "válvula", "sensor", "termostato", "filtro"
            ]
            
            message_lower = message.lower()
            for keyword in equipment_keywords:
                if keyword in message_lower:
                    entities.equipment_mentioned = keyword
                    break
            
            # Extraer acciones/estados
            action_keywords = {
                "iniciar": "start", "comenzar": "start", "empezar": "start",
                "terminar": "finish", "completar": "complete", "finalizar": "finish",
                "problema": "issue", "error": "error", "falla": "issue",
                "funciona": "working", "funcionando": "working",
                "reparado": "fixed", "arreglado": "fixed",
                "limpio": "cleaned", "limpieza": "cleaning",
                "calibrado": "calibrated", "calibración": "calibration",
                "instalado": "installed", "instalación": "installation"
            }
            
            for keyword, action in action_keywords.items():
                if keyword in message_lower:
                    entities.action = action
                    break
            
            # Extraer mediciones
            measurement_patterns = [
                r'(\d+\.?\d*)\s*(grados?|°c|°f|celsius|fahrenheit)',
                r'(\d+\.?\d*)\s*(psi|bar|pascal|pa)',
                r'(\d+\.?\d*)\s*(voltios?|v|volts?)',
                r'(\d+\.?\d*)\s*(amperios?|a|amps?)',
                r'(\d+\.?\d*)\s*(rpm|revoluciones)',
                r'(\d+\.?\d*)\s*(litros?|l|galones?)',
                r'(\d+\.?\d*)\s*(metros?|m|cm|mm)'
            ]
            
            measurements = []
            for pattern in measurement_patterns:
                matches = re.finditer(pattern, message_lower)
                for match in matches:
                    measurements.append({
                        "value": match.group(1),
                        "unit": match.group(2),
                        "full_match": match.group(0)
                    })
            
            entities.measurements = measurements
            
            # Extraer problemas mencionados
            problem_keywords = [
                "no funciona", "roto", "dañado", "defectuoso", "averiado",
                "fuga", "ruido", "vibración", "sobrecalentamiento", "frío",
                "caliente", "lento", "rápido", "atascado", "bloqueado"
            ]
            
            problems = []
            for keyword in problem_keywords:
                if keyword in message_lower:
                    problems.append(keyword)
            
            entities.problems = problems
            
            # Extraer ubicaciones mencionadas
            location_keywords = [
                "cocina", "baño", "sala", "comedor", "oficina", "almacén",
                "sótano", "azotea", "terraza", "patio", "entrada", "salida",
                "primer piso", "segundo piso", "planta baja"
            ]
            
            locations = []
            for keyword in location_keywords:
                if keyword in message_lower:
                    locations.append(keyword)
            
            entities.locations = locations
            
            return entities
            
        except Exception as e:
            self.logger.error("❌ Error extrayendo entidades", error=str(e))
            return ExtractedEntities()  # Retornar entidades vacías en caso de error
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del nodo."""
        
        return {
            "initialized": self._initialized,
            "gemini_available": self.model is not None,
            "valid_intents": len(VALID_INTENTS)
        }