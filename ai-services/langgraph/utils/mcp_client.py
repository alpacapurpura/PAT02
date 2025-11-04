#!/usr/bin/env python3
"""
Cliente MCP para LangGraph Server

Cliente para comunicación con el servidor MCP de PATCO Suite.
Proporciona acceso a herramientas FSM, equipos, RAG y conversaciones.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import aiohttp
import structlog

from .logging_config import LoggingMixin

logger = structlog.get_logger(__name__)


class MCPClientError(Exception):
    """Excepción personalizada para errores del cliente MCP."""
    pass


class MCPClient(LoggingMixin):
    """Cliente para comunicación con servidor MCP."""
    
    def __init__(self, mcp_server_url: str, timeout: int = 30):
        """
        Inicializa el cliente MCP.
        
        Args:
            mcp_server_url: URL del servidor MCP
            timeout: Timeout para requests en segundos
        """
        self.mcp_server_url = mcp_server_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        
        self.logger.info(
            "🔧 Cliente MCP inicializado",
            mcp_server_url=self.mcp_server_url,
            timeout=self.timeout
        )
    
    async def connect(self) -> None:
        """Establece conexión con el servidor MCP."""
        
        try:
            self.log_method_call("connect")
            
            # Crear sesión HTTP
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "PATCO-LangGraph-Client/1.0.0"
                }
            )
            
            # Verificar conectividad
            await self._health_check()
            
            self._connected = True
            self.log_method_result("connect")
            
        except Exception as e:
            self.log_error("connect", e)
            if self.session:
                await self.session.close()
                self.session = None
            raise MCPClientError(f"Error conectando con servidor MCP: {e}")
    
    async def disconnect(self) -> None:
        """Cierra la conexión con el servidor MCP."""
        
        try:
            self.log_method_call("disconnect")
            
            if self.session:
                await self.session.close()
                self.session = None
            
            self._connected = False
            self.log_method_result("disconnect")
            
        except Exception as e:
            self.log_error("disconnect", e)
    
    async def is_connected(self) -> bool:
        """Verifica si el cliente está conectado."""
        
        if not self._connected or not self.session:
            return False
        
        try:
            # Verificar con health check rápido
            await self._health_check()
            return True
        except:
            self._connected = False
            return False
    
    async def _health_check(self) -> None:
        """Realiza health check del servidor MCP."""
        
        try:
            url = f"{self.mcp_server_url}/health"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise MCPClientError(f"Health check failed: {response.status}")
                
                data = await response.json()
                if data.get("status") != "healthy":
                    raise MCPClientError("MCP server not healthy")
                    
        except aiohttp.ClientError as e:
            raise MCPClientError(f"Health check error: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Llama a una herramienta del servidor MCP.
        
        Args:
            tool_name: Nombre de la herramienta
            arguments: Argumentos para la herramienta
            
        Returns:
            Resultado de la herramienta
            
        Raises:
            MCPClientError: Si hay error en la llamada
        """
        
        try:
            self.log_method_call(
                "call_tool",
                tool_name=tool_name,
                arguments_keys=list(arguments.keys())
            )
            
            if not self.is_connected():
                raise MCPClientError("Cliente MCP no conectado")
            
            # Preparar payload JSON-RPC 2.0
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": f"langgraph-{asyncio.current_task().get_name() if asyncio.current_task() else 'unknown'}"
            }
            
            # Realizar llamada
            url = f"{self.mcp_server_url}/mcp"
            
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise MCPClientError(f"HTTP {response.status}: {error_text}")
                
                result = await response.json()
                
                # Verificar respuesta JSON-RPC
                if "error" in result:
                    error = result["error"]
                    raise MCPClientError(f"MCP Error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}")
                
                if "result" not in result:
                    raise MCPClientError("Invalid JSON-RPC response: missing result")
                
                self.log_method_result(
                    "call_tool",
                    tool_name=tool_name,
                    success=True
                )
                
                return result["result"]
                
        except Exception as e:
            self.log_error("call_tool", e, tool_name=tool_name)
            if isinstance(e, MCPClientError):
                raise
            raise MCPClientError(f"Error calling tool {tool_name}: {e}")
    
    # Métodos específicos para herramientas FSM
    
    async def get_fsm_order(self, order_id: int, include_tasks: bool = True, include_materials: bool = True) -> Dict[str, Any]:
        """Obtiene información de orden FSM."""
        
        return await self.call_tool("get_fsm_order", {
            "order_id": order_id,
            "include_tasks": include_tasks,
            "include_materials": include_materials
        })
    
    async def update_fsm_order(self, order_id: int, values: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza orden FSM."""
        
        return await self.call_tool("update_fsm_order", {
            "order_id": order_id,
            "values": values
        })
    
    async def list_fsm_orders(self, filters: Dict[str, Any] = None, limit: int = 50) -> Dict[str, Any]:
        """Lista órdenes FSM con filtros."""
        
        return await self.call_tool("list_fsm_orders", {
            "filters": filters or {},
            "limit": limit
        })
    
    # Métodos específicos para herramientas de equipos
    
    async def get_equipment_info(self, equipment_id: int, include_maintenance_history: bool = True) -> Dict[str, Any]:
        """Obtiene información de equipo."""
        
        return await self.call_tool("get_equipment_info", {
            "equipment_id": equipment_id,
            "include_maintenance_history": include_maintenance_history
        })
    
    async def search_equipment(self, query: str, category_id: int = None, limit: int = 10) -> Dict[str, Any]:
        """Busca equipos."""
        
        return await self.call_tool("search_equipment", {
            "query": query,
            "category_id": category_id,
            "limit": limit
        })
    
    # Métodos específicos para herramientas RAG
    
    async def search_knowledge_base(
        self, 
        query: str, 
        max_results: int = 5,
        similarity_threshold: float = 0.7,
        equipment_category_id: int = None,
        document_types: List[str] = None
    ) -> Dict[str, Any]:
        """Busca en la base de conocimiento usando RAG."""
        
        return await self.call_tool("search_knowledge_base", {
            "query": query,
            "max_results": max_results,
            "similarity_threshold": similarity_threshold,
            "equipment_category_id": equipment_category_id,
            "document_types": document_types or ["manual", "procedure", "checklist"]
        })
    
    # Métodos específicos para conversaciones IA
    
    async def create_ai_conversation(self, fsm_order_id: int, technician_id: int) -> Dict[str, Any]:
        """Crea conversación IA."""
        
        return await self.call_tool("create_ai_conversation", {
            "fsm_order_id": fsm_order_id,
            "technician_id": technician_id
        })
    
    async def get_conversation_context(self, conversation_id: int) -> Dict[str, Any]:
        """Obtiene contexto de conversación."""
        
        return await self.call_tool("get_conversation_context", {
            "conversation_id": conversation_id
        })
    
    # Método genérico para herramientas personalizadas
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """Lista herramientas disponibles en el servidor MCP."""
        
        try:
            url = f"{self.mcp_server_url}/tools"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise MCPClientError(f"Error listing tools: {response.status}")
                
                return await response.json()
                
        except Exception as e:
            self.log_error("list_available_tools", e)
            raise MCPClientError(f"Error listing tools: {e}")
    
    def __repr__(self) -> str:
        """Representación string del cliente."""
        return f"MCPClient(url={self.mcp_server_url}, connected={self._connected})"