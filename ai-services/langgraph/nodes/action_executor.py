#!/usr/bin/env python3
"""
Nodo Ejecutor de Acciones para LangGraph

Ejecuta las acciones planificadas usando el servidor MCP
y actualiza el estado con los resultados.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

from typing import Dict, Any, List

import structlog

from schemas import ConversationState, ConversationAction
from utils.logging_config import LoggingMixin
from utils.mcp_client import MCPClient

logger = structlog.get_logger(__name__)


class ActionExecutorNode(LoggingMixin):
    """Nodo para ejecución de acciones planificadas."""
    
    def __init__(self, mcp_client: MCPClient):
        """
        Inicializa el nodo ejecutor de acciones.
        
        Args:
            mcp_client: Cliente MCP para herramientas
        """
        self.mcp_client = mcp_client
        self._initialized = False
        self._execution_results = {}
    
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
        Ejecuta las acciones planificadas.
        
        Args:
            state: Estado actual de la conversación
            
        Returns:
            Estado actualizado con resultados de ejecución
        """
        
        try:
            self.log_method_call(
                "process",
                actions_count=len(state.actions)
            )
            
            if not state.actions:
                self.logger.debug("✅ No hay acciones para ejecutar")
                return state
            
            # Ejecutar cada acción
            execution_results = []
            successful_actions = 0
            failed_actions = 0
            
            for action in state.actions:
                try:
                    result = await self._execute_action(action, state)
                    execution_results.append({
                        "action": action,
                        "result": result,
                        "success": True
                    })
                    successful_actions += 1
                    
                except Exception as e:
                    self.logger.error(
                        f"❌ Error ejecutando acción {action.action_type}",
                        action_type=action.action_type,
                        error=str(e)
                    )
                    execution_results.append({
                        "action": action,
                        "result": {"error": str(e)},
                        "success": False
                    })
                    failed_actions += 1
            
            # Almacenar resultados para uso posterior
            self._execution_results = execution_results
            
            # Agregar metadatos de procesamiento
            state.processing_metadata.update({
                "action_executor": {
                    "total_actions": len(state.actions),
                    "successful_actions": successful_actions,
                    "failed_actions": failed_actions,
                    "execution_results": len(execution_results)
                }
            })
            
            self.log_method_result(
                "process",
                successful=successful_actions,
                failed=failed_actions
            )
            
            return state
            
        except Exception as e:
            self.log_error("process", e)
            state.error_message = f"Error ejecutando acciones: {str(e)}"
            return state
    
    async def _execute_action(self, action: ConversationAction, state: ConversationState) -> Dict[str, Any]:
        """
        Ejecuta una acción específica.
        
        Args:
            action: Acción a ejecutar
            state: Estado de la conversación
            
        Returns:
            Resultado de la ejecución
        """
        
        try:
            self.log_method_call(
                "_execute_action",
                action_type=action.action_type,
                target=action.target
            )
            
            # Ejecutar según el tipo de acción
            if action.action_type == "update_fsm_order":
                result = await self._execute_update_fsm_order(action)
            
            elif action.action_type == "get_equipment_info":
                result = await self._execute_get_equipment_info(action)
            
            elif action.action_type == "create_maintenance_request":
                result = await self._execute_create_maintenance_request(action)
            
            elif action.action_type == "generate_report":
                result = await self._execute_generate_report(action, state)
            
            elif action.action_type == "send_notification":
                result = await self._execute_send_notification(action)
            
            elif action.action_type == "schedule_task":
                result = await self._execute_schedule_task(action)
            
            else:
                raise ValueError(f"Tipo de acción no soportado: {action.action_type}")
            
            self.log_method_result(
                "_execute_action",
                action_type=action.action_type,
                success=True
            )
            
            return result
            
        except Exception as e:
            self.log_error("_execute_action", e, action_type=action.action_type)
            raise
    
    async def _execute_update_fsm_order(self, action: ConversationAction) -> Dict[str, Any]:
        """Ejecuta actualización de orden FSM."""
        
        try:
            order_id = action.parameters.get("order_id")
            if not order_id:
                raise ValueError("order_id requerido para update_fsm_order")
            
            # Preparar valores para actualizar
            update_values = {}
            
            if "stage" in action.parameters:
                update_values["stage"] = action.parameters["stage"]
            
            if "notes" in action.parameters:
                update_values["notes"] = action.parameters["notes"]
            
            if "completion_percentage" in action.parameters:
                update_values["completion_percentage"] = action.parameters["completion_percentage"]
            
            # Llamar al servidor MCP
            result = await self.mcp_client.update_fsm_order(order_id, update_values)
            
            return {
                "action_type": "update_fsm_order",
                "order_id": order_id,
                "updated_fields": list(update_values.keys()),
                "mcp_result": result
            }
            
        except Exception as e:
            self.log_error("_execute_update_fsm_order", e)
            raise
    
    async def _execute_get_equipment_info(self, action: ConversationAction) -> Dict[str, Any]:
        """Ejecuta obtención de información de equipos."""
        
        try:
            equipment_ids = action.parameters.get("equipment_ids", [])
            include_maintenance_history = action.parameters.get("include_maintenance_history", False)
            
            equipment_info = []
            
            # Obtener información de cada equipo
            for equipment_id in equipment_ids:
                try:
                    info = await self.mcp_client.get_equipment_info(
                        equipment_id=equipment_id,
                        include_maintenance_history=include_maintenance_history
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
            
            return {
                "action_type": "get_equipment_info",
                "equipment_count": len(equipment_info),
                "equipment_info": equipment_info
            }
            
        except Exception as e:
            self.log_error("_execute_get_equipment_info", e)
            raise
    
    async def _execute_create_maintenance_request(self, action: ConversationAction) -> Dict[str, Any]:
        """Ejecuta creación de solicitud de mantenimiento."""
        
        try:
            # Por ahora simulamos la creación
            # En implementación real se usaría una herramienta MCP específica
            
            equipment_ids = action.parameters.get("equipment_ids", [])
            description = action.parameters.get("description", "Solicitud de mantenimiento")
            
            return {
                "action_type": "create_maintenance_request",
                "equipment_ids": equipment_ids,
                "description": description,
                "status": "simulated",  # En implementación real sería "created"
                "message": "Solicitud de mantenimiento creada (simulado)"
            }
            
        except Exception as e:
            self.log_error("_execute_create_maintenance_request", e)
            raise
    
    async def _execute_generate_report(self, action: ConversationAction, state: ConversationState) -> Dict[str, Any]:
        """Ejecuta generación de reporte."""
        
        try:
            fsm_order_id = action.parameters.get("fsm_order_id")
            conversation_id = action.parameters.get("conversation_id", "unknown")
            
            # Por ahora simulamos la generación de reporte
            # En implementación real se integraría con el generador de reportes
            
            return {
                "action_type": "generate_report",
                "fsm_order_id": fsm_order_id,
                "conversation_id": conversation_id,
                "status": "simulated",  # En implementación real sería "generated"
                "report_url": f"https://docs.google.com/document/simulated_{fsm_order_id}",
                "message": "Reporte técnico generado (simulado)"
            }
            
        except Exception as e:
            self.log_error("_execute_generate_report", e)
            raise
    
    async def _execute_send_notification(self, action: ConversationAction) -> Dict[str, Any]:
        """Ejecuta envío de notificación."""
        
        try:
            recipient = action.parameters.get("recipient", "supervisor")
            message = action.parameters.get("message", "Notificación desde servicio")
            priority = action.parameters.get("priority", "normal")
            
            # Por ahora simulamos el envío
            # En implementación real se integraría con sistema de notificaciones
            
            return {
                "action_type": "send_notification",
                "recipient": recipient,
                "message": message,
                "priority": priority,
                "status": "simulated",  # En implementación real sería "sent"
                "notification_id": f"notif_{hash(message) % 10000}"
            }
            
        except Exception as e:
            self.log_error("_execute_send_notification", e)
            raise
    
    async def _execute_schedule_task(self, action: ConversationAction) -> Dict[str, Any]:
        """Ejecuta programación de tarea."""
        
        try:
            task_type = action.parameters.get("task_type", "follow_up")
            related_order = action.parameters.get("related_order")
            description = action.parameters.get("description", "Tarea programada")
            
            # Por ahora simulamos la programación
            # En implementación real se integraría con sistema de tareas
            
            return {
                "action_type": "schedule_task",
                "task_type": task_type,
                "related_order": related_order,
                "description": description,
                "status": "simulated",  # En implementación real sería "scheduled"
                "task_id": f"task_{hash(description) % 10000}"
            }
            
        except Exception as e:
            self.log_error("_execute_schedule_task", e)
            raise
    
    def get_execution_results(self) -> List[Dict[str, Any]]:
        """
        Obtiene los resultados de la última ejecución.
        
        Returns:
            Lista de resultados de ejecución
        """
        return self._execution_results
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del nodo."""
        
        total_executions = len(self._execution_results)
        successful_executions = sum(1 for result in self._execution_results if result.get("success", False))
        
        return {
            "initialized": self._initialized,
            "mcp_client_connected": await self.mcp_client.is_connected() if self.mcp_client else False,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0
        }