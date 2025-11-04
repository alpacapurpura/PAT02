#!/usr/bin/env python3
"""
Esquemas de datos para el servidor MCP
Validación de requests y responses usando Pydantic
"""

from .base import (
    BaseResponse,
    ErrorResponse,
    SuccessResponse,
    PaginatedResponse
)

from .mcp import (
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPToolCall,
    MCPResult
)

from .fsm import (
    FSMOrderRequest,
    FSMOrderResponse,
    FSMOrderUpdateRequest,
    FSMOrderUpdateResponse,
    FSMOrderListRequest,
    FSMOrderListResponse
)

from .equipment import (
    EquipmentRequest,
    EquipmentResponse,
    EquipmentSearchRequest,
    EquipmentSearchResponse,
    EquipmentUpdateRequest,
    EquipmentUpdateResponse,
    MaintenanceRequestCreateRequest,
    MaintenanceRequestResponse
)

from .knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeChunk,
    SearchResult
)

from .conversation import (
    CreateConversationRequest,
    CreateConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
    GetConversationRequest,
    GetConversationResponse,
    ListConversationsRequest,
    ListConversationsResponse,
    UpdateConversationRequest,
    UpdateConversationResponse
)

from .auth import (
    LoginRequest,
    LoginResponse,
    ApiKeyAuthRequest,
    TokenValidationRequest,
    TokenValidationResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    LogoutResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    UserInfoRequest,
    UserInfoResponse,
    UserInfo
)

__all__ = [
    # Base
    'BaseResponse',
    'ErrorResponse', 
    'SuccessResponse',
    'PaginatedResponse',
    
    # MCP
    'MCPRequest',
    'MCPResponse',
    'MCPTool',
    'MCPToolCall',
    'MCPResult',
    
    # FSM
    'FSMOrderRequest',
    'FSMOrderResponse',
    'FSMOrderUpdateRequest',
    'FSMOrderUpdateResponse',
    'FSMOrderListRequest',
    'FSMOrderListResponse',
    
    # Equipment
    'EquipmentRequest',
    'EquipmentResponse',
    'EquipmentSearchRequest',
    'EquipmentSearchResponse',
    'EquipmentUpdateRequest',
    'EquipmentUpdateResponse',
    'MaintenanceRequestCreateRequest',
    'MaintenanceRequestResponse',
    
    # Knowledge
    'KnowledgeSearchRequest',
    'KnowledgeSearchResponse',
    'KnowledgeChunk',
    'SearchResult',
    
    # Conversation
    'CreateConversationRequest',
    'CreateConversationResponse',
    'SendMessageRequest',
    'SendMessageResponse',
    'GetConversationRequest',
    'GetConversationResponse',
    'ListConversationsRequest',
    'ListConversationsResponse',
    'UpdateConversationRequest',
    'UpdateConversationResponse',
    
    # Auth
    'LoginRequest',
    'LoginResponse',
    'ApiKeyAuthRequest',
    'TokenValidationRequest',
    'TokenValidationResponse',
    'RefreshTokenRequest',
    'RefreshTokenResponse',
    'LogoutRequest',
    'LogoutResponse',
    'PermissionCheckRequest',
    'PermissionCheckResponse',
    'UserInfoRequest',
    'UserInfoResponse',
    'UserInfo'
]