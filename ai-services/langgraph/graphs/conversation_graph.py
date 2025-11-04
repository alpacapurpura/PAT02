#!/usr/bin/env python3
"""
Grafo de Conversación para LangGraph Server

Implementa el grafo principal de conversación usando LangGraph
para orquestación del agente IA de PATCO Suite.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
from typing import Dict, Any, List, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import structlog

from schemas import ConversationState, CONVERSATION_STATES
from nodes.message_processor import MessageProcessorNode
from nodes.context_retriever import ContextRetrieverNode
from nodes.rag_search import RAGSearchNode
from nodes.action_planner import ActionPlannerNode
from nodes.response_generator import ResponseGeneratorNode
from nodes.action_executor import ActionExecutorNode
from utils.logging_config import LoggingMixin
from utils.mcp_client import MCPClient

logger = structlog.get_logger(__name__)


class ConversationGraph(LoggingMixin):
    """Grafo principal de conversación usando LangGraph."""
    
    def __init__(self, database_url: str, mcp_client: MCPClient):
        """
        Inicializa el grafo de conversación.
        
        Args:
            database_url: URL de conexión a PostgreSQL
            mcp_client: Cliente MCP para herramientas
        """
        self.database_url = database_url
        self.mcp_client = mcp_client
        self.checkpointer: Optional[AsyncPostgresSaver] = None
        self.graph = None
        self._ready = False
        
        # Inicializar nodos
        self.nodes = {
            "message_processor": MessageProcessorNode(mcp_client),
            "context_retriever": ContextRetrieverNode(mcp_client),
            "rag_search": RAGSearchNode(mcp_client),
            "action_planner": ActionPlannerNode(mcp_client),
            "response_generator": ResponseGeneratorNode(mcp_client),
            "action_executor": ActionExecutorNode(mcp_client)
        }
        
        self.logger.info(
            "🏗️ Grafo de conversación inicializado",
            nodes_count=len(self.nodes)
        )
    
    async def initialize(self) -> None:
        """Inicializa el grafo y sus componentes."""
        
        try:
            self.log_method_call("initialize")
            
            # Configurar checkpointer con PostgreSQL
            self.checkpointer = AsyncPostgresSaver.from_conn_string(self.database_url)
            async with self.checkpointer as checkpointer:
                await checkpointer.setup()
            
            # Construir grafo
            self._build_graph()
            
            # Inicializar nodos
            for node_name, node in self.nodes.items():
                await node.initialize()
                self.logger.debug(f"✅ Nodo {node_name} inicializado")
            
            self._ready = True
            self.log_method_result("initialize")
            
        except Exception as e:
            self.log_error("initialize", e)
            raise
    
    def _build_graph(self) -> None:
        """Construye el grafo de conversación."""
        
        try:
            self.log_method_call("_build_graph")
            
            # Crear grafo de estados
            workflow = StateGraph(ConversationState)
            
            # Agregar nodos
            workflow.add_node("message_processor", self.nodes["message_processor"].process)
            workflow.add_node("context_retriever", self.nodes["context_retriever"].process)
            workflow.add_node("rag_search", self.nodes["rag_search"].process)
            workflow.add_node("action_planner", self.nodes["action_planner"].process)
            workflow.add_node("response_generator", self.nodes["response_generator"].process)
            workflow.add_node("action_executor", self.nodes["action_executor"].process)
            
            # Definir punto de entrada
            workflow.add_edge(START, "message_processor")
            
            # Definir edges condicionales
            workflow.add_conditional_edges(
                "message_processor",
                self._route_by_intent,
                {
                    "question": "rag_search",
                    "action": "action_planner",
                    "status_update": "context_retriever",
                    "greeting": "response_generator",
                    "confirmation": "action_executor",
                    "default": "response_generator"
                }
            )
            
            # Edges desde RAG search
            workflow.add_edge("rag_search", "response_generator")
            
            # Edges desde context retriever
            workflow.add_edge("context_retriever", "response_generator")
            
            # Edges desde action planner
            workflow.add_conditional_edges(
                "action_planner",
                self._route_actions,
                {
                    "execute": "action_executor",
                    "confirm": "response_generator"
                }
            )
            
            # Edges desde action executor
            workflow.add_edge("action_executor", "response_generator")
            
            # Edge final
            workflow.add_edge("response_generator", END)
            
            # Compilar grafo con checkpointer
            self.graph = workflow.compile(checkpointer=self.checkpointer)
            
            self.log_method_result("_build_graph")
            
        except Exception as e:
            self.log_error("_build_graph", e)
            raise
    
    def _route_by_intent(self, state: ConversationState) -> str:
        """
        Enruta el flujo basado en la intención detectada.
        
        Args:
            state: Estado actual de la conversación
            
        Returns:
            Nombre del siguiente nodo
        """
        
        intent = state.current_intent
        
        # Mapeo de intenciones a nodos
        intent_routing = {
            "question": "rag_search",
            "action": "action_planner",
            "status_update": "context_retriever",
            "greeting": "response_generator",
            "confirmation": "action_executor",
            "complaint": "rag_search",
            "request_help": "rag_search"
        }
        
        next_node = intent_routing.get(intent, "response_generator")
        
        self.logger.debug(
            "🔀 Enrutando por intención",
            intent=intent,
            next_node=next_node
        )
        
        return next_node
    
    def _route_actions(self, state: ConversationState) -> str:
        """
        Enruta basado en las acciones planificadas.
        
        Args:
            state: Estado actual de la conversación
            
        Returns:
            Nombre del siguiente nodo
        """
        
        actions = state.actions
        
        # Si hay acciones que requieren confirmación, ir a response_generator
        if any(action.requires_confirmation for action in actions):
            return "confirm"
        
        # Si hay acciones para ejecutar, ir a action_executor
        if actions:
            return "execute"
        
        # Por defecto, generar respuesta
        return "confirm"
    
    async def process_message(self, state_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje a través del grafo.
        
        Args:
            state_dict: Estado de la conversación como diccionario
            config: Configuración del grafo (incluye thread_id)
            
        Returns:
            Estado actualizado después del procesamiento
        """
        
        try:
            self.log_method_call(
                "process_message",
                thread_id=config.get("configurable", {}).get("thread_id"),
                messages_count=len(state_dict.get("messages", []))
            )
            
            if not self._ready:
                raise RuntimeError("Grafo no está listo")
            
            # Ejecutar grafo
            result = await self.graph.ainvoke(state_dict, config=config)
            
            self.log_method_result(
                "process_message",
                thread_id=config.get("configurable", {}).get("thread_id"),
                has_response=bool(result.get("response")),
                actions_count=len(result.get("actions", []))
            )
            
            return result
            
        except Exception as e:
            self.log_error("process_message", e)
            raise
    
    async def get_conversation_history(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene el historial de una conversación.
        
        Args:
            config: Configuración con thread_id
            
        Returns:
            Historial de la conversación
        """
        
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            self.log_method_call("get_conversation_history", thread_id=thread_id)
            
            if not self.checkpointer:
                raise RuntimeError("Checkpointer no inicializado")
            
            # Obtener checkpoint actual
            checkpoint = await self.checkpointer.aget(config)
            
            if not checkpoint:
                return {
                    "messages": [],
                    "conversation_state": "not_found",
                    "context": {}
                }
            
            # Extraer datos del checkpoint
            channel_values = checkpoint.channel_values
            
            history = {
                "messages": channel_values.get("messages", []),
                "conversation_state": channel_values.get("conversation_state", "unknown"),
                "context": channel_values.get("context", {})
            }
            
            self.log_method_result(
                "get_conversation_history",
                thread_id=thread_id,
                messages_count=len(history["messages"])
            )
            
            return history
            
        except Exception as e:
            self.log_error("get_conversation_history", e)
            raise
    
    async def reset_conversation(self, config: Dict[str, Any]) -> None:
        """
        Reinicia una conversación específica.
        
        Args:
            config: Configuración con thread_id
        """
        
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            self.log_method_call("reset_conversation", thread_id=thread_id)
            
            if not self.checkpointer:
                raise RuntimeError("Checkpointer no inicializado")
            
            # Eliminar checkpoint
            await self.checkpointer.adelete(config)
            
            self.log_method_result("reset_conversation", thread_id=thread_id)
            
        except Exception as e:
            self.log_error("reset_conversation", e)
            raise
    
    async def get_active_conversations(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de conversaciones activas.
        
        Returns:
            Lista de conversaciones activas
        """
        
        try:
            self.log_method_call("get_active_conversations")
            
            if not self.checkpointer:
                raise RuntimeError("Checkpointer no inicializado")
            
            # Por ahora retornamos lista vacía
            # En implementación completa, consultaríamos la BD
            active_conversations = []
            
            self.log_method_result(
                "get_active_conversations",
                count=len(active_conversations)
            )
            
            return active_conversations
            
        except Exception as e:
            self.log_error("get_active_conversations", e)
            raise
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del grafo.
        
        Returns:
            Métricas del grafo
        """
        
        try:
            metrics = {
                "graph_ready": self._ready,
                "nodes_count": len(self.nodes),
                "checkpointer_ready": self.checkpointer is not None
            }
            
            # Agregar métricas de nodos
            for node_name, node in self.nodes.items():
                if hasattr(node, 'get_metrics'):
                    node_metrics = await node.get_metrics()
                    metrics[f"node_{node_name}"] = node_metrics
            
            return metrics
            
        except Exception as e:
            self.log_error("get_metrics", e)
            return {"error": str(e)}
    
    def is_ready(self) -> bool:
        """Verifica si el grafo está listo para procesar mensajes."""
        return self._ready and self.graph is not None and self.checkpointer is not None
    
    async def cleanup(self) -> None:
        """Limpia recursos del grafo."""
        
        try:
            self.log_method_call("cleanup")
            
            # Limpiar nodos
            for node in self.nodes.values():
                if hasattr(node, 'cleanup'):
                    await node.cleanup()
            
            # Limpiar checkpointer
            if self.checkpointer:
                # El checkpointer se limpia automáticamente
                pass
            
            self._ready = False
            self.log_method_result("cleanup")
            
        except Exception as e:
            self.log_error("cleanup", e)