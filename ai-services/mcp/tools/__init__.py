#!/usr/bin/env python3
"""
Herramientas MCP para el servidor
Este módulo contiene todas las herramientas disponibles para el protocolo MCP
"""

from .fsm_tools import (
    get_fsm_order,
    update_fsm_order,
    list_fsm_orders,
    create_fsm_task,
    FSMToolsManager
)

from .equipment_tools import (
    get_equipment_info,
    search_equipment,
    # update_equipment,  # Comentado temporalmente - no implementado
    # create_maintenance_request,  # Comentado temporalmente - no implementado
    EquipmentToolsManager
)

from .knowledge_tools import (
    search_knowledge_base,
    get_document,
    list_documents,
    search_similar_documents,
    KnowledgeToolsManager
)

from .conversation_tools import (
    create_ai_conversation,
    send_message_to_conversation,
    get_conversation,
    list_conversations,
    ConversationToolsManager
)

from .report_tools import *

# Lista de todas las herramientas disponibles
ALL_TOOLS = [
    # FSM Tools
    'get_fsm_order',
    'update_fsm_order', 
    'list_fsm_orders',
    # 'create_fsm_task',  # Comentado temporalmente - no implementado
    
    # Equipment Tools
    'get_equipment_info',
    'search_equipment',
    # 'update_equipment',  # Comentado temporalmente - no implementado
    # 'create_maintenance_request',  # Comentado temporalmente - no implementado
    
    # Knowledge Tools
    'search_knowledge_base',
    'get_document',
    'list_documents',
    'search_similar_documents',
    
    # Conversation Tools
    'create_ai_conversation',
    'send_message',
    'get_conversation',
    'list_conversations'
]

# Mapeo de herramientas a sus funciones (usando nombres de MCPMethodEnum)
TOOL_REGISTRY = {
    # FSM Tools (coinciden con MCPMethodEnum)
    'fsm/get_order': get_fsm_order,
    'fsm/update_order': update_fsm_order,
    'fsm/list_orders': list_fsm_orders,
    # 'create_fsm_task': create_fsm_task,  # Comentado temporalmente - no implementado
    
    # Equipment Tools (coinciden con MCPMethodEnum)
    'equipment/get_info': get_equipment_info,
    'equipment/search': search_equipment,
    'equipment/list': search_equipment,  # Alias para búsqueda general
    # 'update_equipment': update_equipment,  # Comentado temporalmente - no implementado
    # 'create_maintenance_request': create_maintenance_request,  # Comentado temporalmente - no implementado
    
    # Knowledge Tools (coinciden con MCPMethodEnum)
    'knowledge/search': search_knowledge_base,
    'knowledge/get_document': get_document,
    # Aliases para compatibilidad
    'list_documents': list_documents,
    'search_similar_documents': search_similar_documents,
    
    # Conversation Tools (coinciden con MCPMethodEnum)
    'conversation/create': create_ai_conversation,
    'conversation/message': send_message_to_conversation,
    'conversation/list': list_conversations,
    # Alias para compatibilidad
    'get_conversation': get_conversation
}

# Managers para cada categoría de herramientas
TOOL_MANAGERS = {
    'fsm': FSMToolsManager,
    'equipment': EquipmentToolsManager,
    'knowledge': KnowledgeToolsManager,
    'conversation': ConversationToolsManager
}

def get_tool_function(tool_name: str):
    """Obtener función de herramienta por nombre"""
    return TOOL_REGISTRY.get(tool_name)

def get_available_tools() -> list:
    """Obtener lista de herramientas disponibles"""
    return ALL_TOOLS.copy()

def is_tool_available(tool_name: str) -> bool:
    """Verificar si una herramienta está disponible"""
    return tool_name in TOOL_REGISTRY

def get_tool_manager(category: str):
    """Obtener manager de herramientas por categoría"""
    return TOOL_MANAGERS.get(category)

__all__ = [
    # Funciones de herramientas FSM
    'get_fsm_order',
    'update_fsm_order',
    'list_fsm_orders',
    'create_fsm_task',
    
    # Funciones de herramientas de equipos
    'get_equipment_info',
    'search_equipment',
    'update_equipment',
    'create_maintenance_request',
    
    # Funciones de herramientas de conocimiento
    'search_knowledge_base',
    'get_document',
    'list_documents',
    'search_similar_documents',
    
    # Funciones de herramientas de conversación
    'create_ai_conversation',
    'send_message',
    'get_conversation',
    'list_conversations',
    
    # Managers
    'FSMToolsManager',
    'EquipmentToolsManager',
    'KnowledgeToolsManager',
    'ConversationToolsManager',
    
    # Utilidades
    'ALL_TOOLS',
    'TOOL_REGISTRY',
    'TOOL_MANAGERS',
    'get_tool_function',
    'get_available_tools',
    'is_tool_available',
    'get_tool_manager'
]