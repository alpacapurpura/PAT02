#!/usr/bin/env python3
"""
Nodo Planificador de Acciones para LangGraph

Planifica y determina qué acciones ejecutar basándose en la intención
del usuario y el contexto de la conversación.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

from typing import Dict, Any, List

import structlog

from schemas import ConversationState, ConversationAction, ACTION_TYPES
from utils.logging_config import LoggingMixin
from utils.mcp_client import MCPClient

logger = structlog.get_logger(__name__)


class ActionPlannerNode(LoggingMixin):
    """Nodo para planificación de acciones a ejecutar."""
    
    def __init__(self, mcp_client: MCPClient):
        """
        Inicializa el nodo planificador de acciones.
        
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
        Planifica acciones a ejecutar basándose en el mensaje del usuario.
        
        Args:
            state: Estado actual de la conversación
            
        Returns:
            Estado actualizado con acciones planificadas
        """
        
        try:
            self.log_method_call(
                "process",
                intent=state.current_intent,
                entities_action=state.entities.action if state.entities else None
            )
            
            if not state.messages:
                self.logger.warning("⚠️ No hay mensajes para planificar acciones")
                return state
            
            # Obtener último mensaje
            last_message = state.messages[-1]
            message_content = last_message.content.lower()
            
            # Planificar acciones según el contenido y entidades
            planned_actions = self._plan_actions(message_content, state)
            
            # Actualizar estado
            state.actions = planned_actions
            
            # Agregar metadatos de procesamiento
            state.processing_metadata.update({
                "action_planner": {
                    "actions_planned": len(planned_actions),
                    "requires_confirmation": any(action.requires_confirmation for action in planned_actions),
                    "action_types": [action.action_type for action in planned_actions]
                }
            })
            
            self.log_method_result(
                "process",
                actions_count=len(planned_actions),
                action_types=[action.action_type for action in planned_actions]
            )
            
            return state
            
        except Exception as e:
            self.log_error("process", e)
            state.error_message = f"Error planificando acciones: {str(e)}"
            return state
    
    def _plan_actions(self, message_content: str, state: ConversationState) -> List[ConversationAction]:
        """
        Planifica acciones basándose en el contenido del mensaje.
        
        Args:
            message_content: Contenido del mensaje en minúsculas
            state: Estado de la conversación
            
        Returns:
            Lista de acciones planificadas
        """
        
        actions = []
        
        try:
            # Acciones de actualización de estado FSM
            fsm_actions = self._plan_fsm_actions(message_content, state)
            actions.extend(fsm_actions)
            
            # Acciones de equipos
            equipment_actions = self._plan_equipment_actions(message_content, state)
            actions.extend(equipment_actions)
            
            # Acciones de reportes
            report_actions = self._plan_report_actions(message_content, state)
            actions.extend(report_actions)
            
            # Acciones de notificaciones
            notification_actions = self._plan_notification_actions(message_content, state)
            actions.extend(notification_actions)
            
            return actions
            
        except Exception as e:
            self.log_error("_plan_actions", e)
            return []
    
    def _plan_fsm_actions(self, message_content: str, state: ConversationState) -> List[ConversationAction]:
        """Planifica acciones relacionadas con órdenes FSM."""
        
        actions = []
        
        try:
            # Patrones para actualización de estado
            status_patterns = {
                "iniciar": "in_progress",
                "comenzar": "in_progress", 
                "empezar": "in_progress",
                "terminar": "done",
                "completar": "done",
                "finalizar": "done",
                "pausar": "paused",
                "suspender": "paused"
            }
            
            # Buscar patrones de cambio de estado
            for pattern, new_stage in status_patterns.items():
                if pattern in message_content:
                    action = ConversationAction(
                        action_type="update_fsm_order",
                        target=f"fsm_order_{state.context.fsm_order_id}",
                        parameters={
                            "order_id": state.context.fsm_order_id,
                            "stage": new_stage,
                            "notes": f"Estado actualizado por técnico: {pattern}"
                        },
                        priority="high",
                        requires_confirmation=True
                    )
                    actions.append(action)
                    break
            
            # Patrones para agregar notas/observaciones
            note_patterns = [
                "anotar", "registrar", "observar", "comentar", "reportar"
            ]
            
            if any(pattern in message_content for pattern in note_patterns):
                action = ConversationAction(
                    action_type="update_fsm_order",
                    target=f"fsm_order_{state.context.fsm_order_id}",
                    parameters={
                        "order_id": state.context.fsm_order_id,
                        "notes": "Agregar observaciones del técnico"
                    },
                    priority="medium",
                    requires_confirmation=True
                )
                actions.append(action)
            
            # Patrones para actualizar progreso
            progress_patterns = [
                "progreso", "avance", "completado", "porcentaje"
            ]
            
            if any(pattern in message_content for pattern in progress_patterns):
                # Buscar números que podrían ser porcentajes
                import re
                numbers = re.findall(r'(\d+)%?', message_content)
                
                if numbers:
                    percentage = min(int(numbers[0]), 100)  # Limitar a 100%
                    action = ConversationAction(
                        action_type="update_fsm_order",
                        target=f"fsm_order_{state.context.fsm_order_id}",
                        parameters={
                            "order_id": state.context.fsm_order_id,
                            "completion_percentage": percentage
                        },
                        priority="medium",
                        requires_confirmation=True
                    )
                    actions.append(action)
            
            return actions
            
        except Exception as e:
            self.log_error("_plan_fsm_actions", e)
            return []
    
    def _plan_equipment_actions(self, message_content: str, state: ConversationState) -> List[ConversationAction]:
        """Planifica acciones relacionadas con equipos."""
        
        actions = []
        
        try:
            # Patrones para solicitar información de equipos
            info_patterns = [
                "información", "datos", "especificaciones", "detalles", "características"
            ]
            
            equipment_mentioned = state.entities.equipment_mentioned if state.entities else None
            
            if any(pattern in message_content for pattern in info_patterns) and equipment_mentioned:
                # Si hay equipos en el contexto, buscar información
                if state.context.equipment_ids:
                    action = ConversationAction(
                        action_type="get_equipment_info",
                        target="equipment_info",
                        parameters={
                            "equipment_ids": state.context.equipment_ids,
                            "include_maintenance_history": True
                        },
                        priority="medium",
                        requires_confirmation=False
                    )
                    actions.append(action)
            
            # Patrones para crear solicitud de mantenimiento
            maintenance_patterns = [
                "mantenimiento", "reparar", "arreglar", "revisar", "servicio"
            ]
            
            if any(pattern in message_content for pattern in maintenance_patterns):
                action = ConversationAction(
                    action_type="create_maintenance_request",
                    target="maintenance_request",
                    parameters={
                        "equipment_ids": state.context.equipment_ids,
                        "description": "Solicitud de mantenimiento desde conversación IA"
                    },
                    priority="high",
                    requires_confirmation=True
                )
                actions.append(action)
            
            return actions
            
        except Exception as e:
            self.log_error("_plan_equipment_actions", e)
            return []
    
    def _plan_report_actions(self, message_content: str, state: ConversationState) -> List[ConversationAction]:
        """Planifica acciones relacionadas con reportes."""
        
        actions = []
        
        try:
            # Patrones para generar reportes
            report_patterns = [
                "reporte", "informe", "documento", "generar", "crear reporte"
            ]
            
            if any(pattern in message_content for pattern in report_patterns):
                action = ConversationAction(
                    action_type="generate_report",
                    target="service_report",
                    parameters={
                        "fsm_order_id": state.context.fsm_order_id,
                        "conversation_id": "current",  # Se reemplazará con el ID real
                        "include_photos": True,
                        "include_measurements": True
                    },
                    priority="medium",
                    requires_confirmation=True
                )
                actions.append(action)
            
            return actions
            
        except Exception as e:
            self.log_error("_plan_report_actions", e)
            return []
    
    def _plan_notification_actions(self, message_content: str, state: ConversationState) -> List[ConversationAction]:
        """Planifica acciones de notificación."""
        
        actions = []
        
        try:
            # Patrones para enviar notificaciones
            notification_patterns = [
                "notificar", "avisar", "informar", "comunicar", "alertar"
            ]
            
            if any(pattern in message_content for pattern in notification_patterns):
                action = ConversationAction(
                    action_type="send_notification",
                    target="notification",
                    parameters={
                        "recipient": "supervisor",
                        "message": "Notificación desde servicio de campo",
                        "priority": "normal"
                    },
                    priority="low",
                    requires_confirmation=True
                )
                actions.append(action)
            
            # Patrones para programar tareas
            schedule_patterns = [
                "programar", "agendar", "planificar", "próxima visita"
            ]
            
            if any(pattern in message_content for pattern in schedule_patterns):
                action = ConversationAction(
                    action_type="schedule_task",
                    target="scheduled_task",
                    parameters={
                        "task_type": "follow_up",
                        "related_order": state.context.fsm_order_id,
                        "description": "Tarea programada desde conversación IA"
                    },
                    priority="medium",
                    requires_confirmation=True
                )
                actions.append(action)
            
            return actions
            
        except Exception as e:
            self.log_error("_plan_notification_actions", e)
            return []
    
    def _validate_action(self, action: ConversationAction) -> bool:
        """
        Valida que una acción sea válida.
        
        Args:
            action: Acción a validar
            
        Returns:
            True si la acción es válida
        """
        
        try:
            # Verificar que el tipo de acción sea válido
            if action.action_type not in ACTION_TYPES:
                self.logger.warning(f"⚠️ Tipo de acción inválido: {action.action_type}")
                return False
            
            # Verificar que tenga target
            if not action.target:
                self.logger.warning("⚠️ Acción sin target")
                return False
            
            # Verificar parámetros según el tipo de acción
            if action.action_type == "update_fsm_order":
                if "order_id" not in action.parameters:
                    self.logger.warning("⚠️ update_fsm_order sin order_id")
                    return False
            
            return True
            
        except Exception as e:
            self.log_error("_validate_action", e)
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del nodo."""
        
        return {
            "initialized": self._initialized,
            "available_action_types": len(ACTION_TYPES)
        }