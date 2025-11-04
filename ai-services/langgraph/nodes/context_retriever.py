#!/usr/bin/env python3
"""
Nodo Recuperador de Contexto para LangGraph

Obtiene información contextual adicional del servicio, equipos
y estado actual usando el servidor MCP.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

from typing import Dict, Any

import structlog

from schemas import ConversationState, ConversationContext
from utils.logging_config import LoggingMixin
from utils.mcp_client import MCPClient

logger = structlog.get_logger(__name__)


class ContextRetrieverNode(LoggingMixin):
    """Nodo para recuperación de contexto adicional del servicio."""
    
    def __init__(self, mcp_client: MCPClient):
        """
        Inicializa el nodo recuperador de contexto.
        
        Args:
            mcp_client: Cliente MCP para herramientas
        """
        self.mcp_client = mcp_client
        self._initialized = False
    
    async def initialize(self) -> None:
        """Inicializa el nodo."""
        
        try:
            self.log_method_call("initialize")
            
            self._initialized = True
            self.log_method_result("initialize")
            
        except Exception as e:
            self.log_error("initialize", e)
            raise
    
    async def process(self, state: ConversationState) -> ConversationState:
        """
        Recupera contexto adicional del servicio.
        
        Args:
            state: Estado actual de la conversación
            
        Returns:
            Estado actualizado con contexto enriquecido
        """
        
        try:
            self.log_method_call(
                "process",
                has_fsm_order=bool(state.context.fsm_order_id),
                equipment_count=len(state.context.equipment_ids)
            )
            
            # Enriquecer contexto según lo disponible
            enriched_context = await self._enrich_context(state.context)
            
            # Obtener información de la orden FSM si está disponible
            fsm_info = None
            if state.context.fsm_order_id:
                fsm_info = await self._get_fsm_order_info(state.context.fsm_order_id)
            
            # Obtener información de equipos
            equipment_info = []
            if state.context.equipment_ids:
                equipment_info = await self._get_equipment_info(state.context.equipment_ids)
            
            # Actualizar contexto del estado
            state.context = enriched_context
            
            # Generar respuesta contextual
            response = self._generate_context_response(fsm_info, equipment_info, state)
            state.response = response
            
            # Agregar metadatos de procesamiento
            state.processing_metadata.update({
                "context_retriever": {
                    "fsm_info_retrieved": fsm_info is not None,
                    "equipment_count": len(equipment_info),
                    "context_enriched": True
                }
            })
            
            self.log_method_result(
                "process",
                fsm_info_available=fsm_info is not None,
                equipment_info_count=len(equipment_info)
            )
            
            return state
            
        except Exception as e:
            self.log_error("process", e)
            state.error_message = f"Error recuperando contexto: {str(e)}"
            state.response = "Obtuve información básica del servicio. ¿En qué puedo ayudarte específicamente?"
            return state
    
    async def _enrich_context(self, context: ConversationContext) -> ConversationContext:
        """
        Enriquece el contexto con información adicional.
        
        Args:
            context: Contexto actual
            
        Returns:
            Contexto enriquecido
        """
        
        try:
            # Por ahora retornamos el contexto tal como está
            # En implementación futura se podría agregar más información
            return context
            
        except Exception as e:
            self.log_error("_enrich_context", e)
            return context
    
    async def _get_fsm_order_info(self, fsm_order_id: int) -> Dict[str, Any]:
        """
        Obtiene información de la orden FSM.
        
        Args:
            fsm_order_id: ID de la orden FSM
            
        Returns:
            Información de la orden FSM
        """
        
        try:
            self.log_method_call("_get_fsm_order_info", fsm_order_id=fsm_order_id)
            
            # Llamar al servidor MCP para obtener información de la orden
            fsm_info = await self.mcp_client.get_fsm_order(
                order_id=fsm_order_id,
                include_tasks=True,
                include_materials=True
            )
            
            self.log_method_result(
                "_get_fsm_order_info",
                fsm_order_id=fsm_order_id,
                info_retrieved=bool(fsm_info)
            )
            
            return fsm_info
            
        except Exception as e:
            self.log_error("_get_fsm_order_info", e, fsm_order_id=fsm_order_id)
            return {}
    
    async def _get_equipment_info(self, equipment_ids: list) -> list:
        """
        Obtiene información de los equipos.
        
        Args:
            equipment_ids: Lista de IDs de equipos
            
        Returns:
            Lista con información de equipos
        """
        
        equipment_info = []
        
        try:
            self.log_method_call("_get_equipment_info", equipment_count=len(equipment_ids))
            
            # Obtener información de cada equipo
            for equipment_id in equipment_ids:
                try:
                    info = await self.mcp_client.get_equipment_info(
                        equipment_id=equipment_id,
                        include_maintenance_history=False  # Para respuesta rápida
                    )
                    if info:
                        equipment_info.append(info)
                        
                except Exception as e:
                    self.logger.warning(
                        f"⚠️ Error obteniendo info de equipo {equipment_id}",
                        equipment_id=equipment_id,
                        error=str(e)
                    )
                    continue
            
            self.log_method_result(
                "_get_equipment_info",
                requested_count=len(equipment_ids),
                retrieved_count=len(equipment_info)
            )
            
            return equipment_info
            
        except Exception as e:
            self.log_error("_get_equipment_info", e)
            return []
    
    def _generate_context_response(
        self, 
        fsm_info: Dict[str, Any], 
        equipment_info: list, 
        state: ConversationState
    ) -> str:
        """
        Genera respuesta con información contextual.
        
        Args:
            fsm_info: Información de la orden FSM
            equipment_info: Información de equipos
            state: Estado de la conversación
            
        Returns:
            Respuesta con contexto
        """
        
        try:
            response_parts = []
            
            # Información de la orden FSM
            if fsm_info:
                response_parts.append("📋 **Estado actual del servicio:**")
                
                if fsm_info.get("name"):
                    response_parts.append(f"• Orden: {fsm_info['name']}")
                
                if fsm_info.get("stage_id"):
                    stage_name = fsm_info["stage_id"][1] if isinstance(fsm_info["stage_id"], list) else fsm_info["stage_id"]
                    response_parts.append(f"• Estado: {stage_name}")
                
                if fsm_info.get("partner_id"):
                    partner_name = fsm_info["partner_id"][1] if isinstance(fsm_info["partner_id"], list) else fsm_info["partner_id"]
                    response_parts.append(f"• Cliente: {partner_name}")
                
                if fsm_info.get("location_id"):
                    location_name = fsm_info["location_id"][1] if isinstance(fsm_info["location_id"], list) else fsm_info["location_id"]
                    response_parts.append(f"• Ubicación: {location_name}")
                
                response_parts.append("")
            
            # Información de equipos
            if equipment_info:
                response_parts.append("🔧 **Equipos asignados:**")
                
                for i, equipment in enumerate(equipment_info[:3], 1):  # Mostrar máximo 3
                    name = equipment.get("name", f"Equipo {i}")
                    category = ""
                    if equipment.get("category_id"):
                        category_name = equipment["category_id"][1] if isinstance(equipment["category_id"], list) else equipment["category_id"]
                        category = f" ({category_name})"
                    
                    response_parts.append(f"• {name}{category}")
                
                if len(equipment_info) > 3:
                    response_parts.append(f"• ... y {len(equipment_info) - 3} equipos más")
                
                response_parts.append("")
            
            # Mensaje de seguimiento según la intención
            if state.current_intent == "status_update":
                response_parts.extend([
                    "¿Qué progreso quieres reportar?",
                    "Puedo ayudarte a:",
                    "• Actualizar el estado de la orden",
                    "• Registrar trabajo completado",
                    "• Anotar observaciones importantes"
                ])
            else:
                response_parts.extend([
                    "¿En qué puedo ayudarte con este servicio?",
                    "Puedo asistirte con información técnica, procedimientos o registro de actividades."
                ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            self.log_error("_generate_context_response", e)
            return "Tengo información del servicio disponible. ¿En qué puedo ayudarte?"
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del nodo."""
        
        return {
            "initialized": self._initialized,
            "mcp_client_connected": await self.mcp_client.is_connected() if self.mcp_client else False
        }