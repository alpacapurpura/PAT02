#!/usr/bin/env python3
"""
Esquemas para autenticación y seguridad
Definición de requests y responses para autenticación con Odoo
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum

from .base import BaseRequest, BaseResponse, BaseConfig, StatusEnum

class AuthMethod(str, Enum):
    """Métodos de autenticación"""
    PASSWORD = "password"       # Usuario y contraseña
    API_KEY = "api_key"         # Clave API
    JWT_TOKEN = "jwt_token"     # Token JWT
    OAUTH2 = "oauth2"           # OAuth2
    SESSION = "session"         # Sesión de Odoo

class UserRole(str, Enum):
    """Roles de usuario"""
    ADMIN = "admin"             # Administrador del sistema
    MANAGER = "manager"         # Gerente/Supervisor
    USER = "user"               # Usuario estándar
    TECHNICIAN = "technician"   # Técnico de campo
    CUSTOMER = "customer"       # Cliente
    READONLY = "readonly"       # Solo lectura
    GUEST = "guest"             # Invitado

class PermissionType(str, Enum):
    """Tipos de permisos"""
    READ = "read"               # Lectura
    WRITE = "write"             # Escritura
    CREATE = "create"           # Creación
    DELETE = "delete"           # Eliminación
    EXECUTE = "execute"         # Ejecución
    ADMIN = "admin"             # Administración

class ResourceType(str, Enum):
    """Tipos de recursos"""
    FSM_ORDER = "fsm_order"     # Órdenes FSM
    EQUIPMENT = "equipment"     # Equipos
    KNOWLEDGE = "knowledge"     # Base de conocimiento
    CONVERSATION = "conversation" # Conversaciones
    USER = "user"               # Usuarios
    COMPANY = "company"         # Compañías
    REPORT = "report"           # Reportes
    SYSTEM = "system"           # Sistema

class SessionStatus(str, Enum):
    """Estados de sesión"""
    ACTIVE = "active"           # Sesión activa
    EXPIRED = "expired"         # Sesión expirada
    REVOKED = "revoked"         # Sesión revocada
    SUSPENDED = "suspended"     # Sesión suspendida

class TokenType(str, Enum):
    """Tipos de token"""
    ACCESS = "access"           # Token de acceso
    REFRESH = "refresh"         # Token de renovación
    API = "api"                 # Token de API
    TEMPORARY = "temporary"     # Token temporal

class Permission(BaseModel, BaseConfig):
    """Permiso de usuario"""
    resource_type: ResourceType = Field(description="Tipo de recurso")
    permission_type: PermissionType = Field(description="Tipo de permiso")
    resource_id: Optional[int] = Field(None, description="ID específico del recurso (opcional)")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Condiciones adicionales")
    
    # Metadatos
    granted_by: Optional[int] = Field(None, description="ID del usuario que otorgó el permiso")
    granted_date: Optional[datetime] = Field(None, description="Fecha de otorgamiento")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
    
    def is_expired(self) -> bool:
        """Verificar si el permiso ha expirado"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def matches_resource(self, resource_type: ResourceType, resource_id: Optional[int] = None) -> bool:
        """Verificar si el permiso aplica al recurso especificado"""
        if self.resource_type != resource_type:
            return False
        
        # Si el permiso no especifica un recurso específico, aplica a todos
        if self.resource_id is None:
            return True
        
        # Si especifica un recurso, debe coincidir
        return self.resource_id == resource_id

class UserInfo(BaseModel, BaseConfig):
    """Información del usuario autenticado"""
    id: int = Field(description="ID del usuario")
    login: str = Field(description="Login del usuario")
    name: str = Field(description="Nombre completo")
    email: Optional[EmailStr] = Field(None, description="Email del usuario")
    
    # Información de la compañía
    company_id: int = Field(description="ID de la compañía")
    company_name: str = Field(description="Nombre de la compañía")
    
    # Roles y permisos
    roles: List[UserRole] = Field(description="Roles del usuario")
    permissions: List[Permission] = Field(description="Permisos específicos")
    
    # Información adicional
    language: Optional[str] = Field(None, description="Idioma preferido")
    timezone: Optional[str] = Field(None, description="Zona horaria")
    avatar_url: Optional[str] = Field(None, description="URL del avatar")
    
    # Metadatos de sesión
    last_login: Optional[datetime] = Field(None, description="Último login")
    login_count: Optional[int] = Field(None, description="Número de logins")
    
    # Estado
    active: bool = Field(default=True, description="Usuario activo")
    is_admin: bool = Field(default=False, description="Es administrador")
    
    def has_role(self, role: UserRole) -> bool:
        """Verificar si el usuario tiene un rol específico"""
        return role in self.roles
    
    def has_permission(
        self, 
        resource_type: ResourceType, 
        permission_type: PermissionType,
        resource_id: Optional[int] = None
    ) -> bool:
        """Verificar si el usuario tiene un permiso específico"""
        
        # Los administradores tienen todos los permisos
        if self.is_admin or UserRole.ADMIN in self.roles:
            return True
        
        # Buscar permiso específico
        for permission in self.permissions:
            if permission.is_expired():
                continue
            
            if (permission.resource_type == resource_type and 
                permission.permission_type == permission_type and
                permission.matches_resource(resource_type, resource_id)):
                return True
        
        return False
    
    def get_accessible_resources(
        self, 
        resource_type: ResourceType, 
        permission_type: PermissionType
    ) -> List[int]:
        """Obtener lista de IDs de recursos accesibles"""
        
        # Los administradores tienen acceso a todo
        if self.is_admin or UserRole.ADMIN in self.roles:
            return []  # Lista vacía significa acceso a todo
        
        accessible_ids = []
        
        for permission in self.permissions:
            if permission.is_expired():
                continue
            
            if (permission.resource_type == resource_type and 
                permission.permission_type == permission_type):
                
                if permission.resource_id is None:
                    return []  # Acceso a todo
                else:
                    accessible_ids.append(permission.resource_id)
        
        return accessible_ids

class AuthToken(BaseModel, BaseConfig):
    """Token de autenticación"""
    token: str = Field(description="Token de acceso")
    token_type: TokenType = Field(description="Tipo de token")
    expires_at: datetime = Field(description="Fecha de expiración")
    
    # Información del usuario
    user_id: int = Field(description="ID del usuario")
    user_login: str = Field(description="Login del usuario")
    
    # Metadatos del token
    issued_at: datetime = Field(description="Fecha de emisión")
    issuer: str = Field(description="Emisor del token")
    audience: Optional[str] = Field(None, description="Audiencia del token")
    
    # Alcance y permisos
    scopes: Optional[List[str]] = Field(None, description="Alcances del token")
    permissions: Optional[List[str]] = Field(None, description="Permisos codificados")
    
    # Información de sesión
    session_id: Optional[str] = Field(None, description="ID de sesión")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Información del cliente")
    
    def is_expired(self) -> bool:
        """Verificar si el token ha expirado"""
        return datetime.utcnow() > self.expires_at
    
    def time_to_expiry(self) -> timedelta:
        """Tiempo restante hasta la expiración"""
        return self.expires_at - datetime.utcnow()
    
    def has_scope(self, scope: str) -> bool:
        """Verificar si el token tiene un alcance específico"""
        if not self.scopes:
            return False
        return scope in self.scopes

class AuthSession(BaseModel, BaseConfig):
    """Sesión de autenticación"""
    id: str = Field(description="ID único de la sesión")
    user_id: int = Field(description="ID del usuario")
    status: SessionStatus = Field(description="Estado de la sesión")
    
    # Fechas
    created_at: datetime = Field(description="Fecha de creación")
    last_activity: datetime = Field(description="Última actividad")
    expires_at: datetime = Field(description="Fecha de expiración")
    
    # Información del cliente
    client_ip: Optional[str] = Field(None, description="IP del cliente")
    user_agent: Optional[str] = Field(None, description="User agent")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Información adicional del cliente")
    
    # Tokens asociados
    access_token: Optional[str] = Field(None, description="Token de acceso actual")
    refresh_token: Optional[str] = Field(None, description="Token de renovación")
    
    # Metadatos
    auth_method: AuthMethod = Field(description="Método de autenticación usado")
    login_location: Optional[str] = Field(None, description="Ubicación del login")
    
    def is_active(self) -> bool:
        """Verificar si la sesión está activa"""
        return (self.status == SessionStatus.ACTIVE and 
                not self.is_expired())
    
    def is_expired(self) -> bool:
        """Verificar si la sesión ha expirado"""
        return datetime.utcnow() > self.expires_at
    
    def update_activity(self):
        """Actualizar última actividad"""
        self.last_activity = datetime.utcnow()

# Requests

class LoginRequest(BaseRequest):
    """Request para login"""
    login: str = Field(
        description="Login del usuario",
        min_length=3,
        max_length=100
    )
    password: str = Field(
        description="Contraseña del usuario",
        min_length=1,
        max_length=200
    )
    
    # Información del cliente
    client_ip: Optional[str] = Field(
        None,
        description="IP del cliente"
    )
    user_agent: Optional[str] = Field(
        None,
        description="User agent del cliente"
    )
    
    # Configuración de sesión
    remember_me: bool = Field(
        default=False,
        description="Recordar sesión por más tiempo"
    )
    session_duration: Optional[int] = Field(
        None,
        description="Duración de sesión en segundos",
        ge=300,  # Mínimo 5 minutos
        le=86400 * 30  # Máximo 30 días
    )
    
    # Metadatos adicionales
    client_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Información adicional del cliente"
    )

class ApiKeyAuthRequest(BaseRequest):
    """Request para autenticación con API Key"""
    api_key: str = Field(
        description="Clave API",
        min_length=10,
        max_length=500
    )
    
    # Información del cliente
    client_ip: Optional[str] = Field(
        None,
        description="IP del cliente"
    )
    user_agent: Optional[str] = Field(
        None,
        description="User agent del cliente"
    )
    
    # Metadatos
    client_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Información adicional del cliente"
    )

class TokenValidationRequest(BaseRequest):
    """Request para validar token"""
    token: str = Field(
        description="Token a validar",
        min_length=10
    )
    token_type: TokenType = Field(
        default=TokenType.ACCESS,
        description="Tipo de token"
    )
    
    # Validaciones adicionales
    required_scopes: Optional[List[str]] = Field(
        None,
        description="Alcances requeridos"
    )
    required_permissions: Optional[List[str]] = Field(
        None,
        description="Permisos requeridos"
    )

class RefreshTokenRequest(BaseRequest):
    """Request para renovar token"""
    refresh_token: str = Field(
        description="Token de renovación",
        min_length=10
    )
    
    # Configuración del nuevo token
    extend_expiry: bool = Field(
        default=False,
        description="Extender tiempo de expiración"
    )
    new_scopes: Optional[List[str]] = Field(
        None,
        description="Nuevos alcances para el token"
    )

class LogoutRequest(BaseRequest):
    """Request para logout"""
    session_id: Optional[str] = Field(
        None,
        description="ID de sesión específica (opcional)"
    )
    revoke_all_sessions: bool = Field(
        default=False,
        description="Revocar todas las sesiones del usuario"
    )
    revoke_tokens: bool = Field(
        default=True,
        description="Revocar tokens asociados"
    )

class PermissionCheckRequest(BaseRequest):
    """Request para verificar permisos"""
    resource_type: ResourceType = Field(
        description="Tipo de recurso"
    )
    permission_type: PermissionType = Field(
        description="Tipo de permiso requerido"
    )
    resource_id: Optional[int] = Field(
        None,
        description="ID específico del recurso"
    )
    
    # Usuario específico (opcional, por defecto el usuario actual)
    user_id: Optional[int] = Field(
        None,
        description="ID del usuario a verificar"
    )

class UserInfoRequest(BaseRequest):
    """Request para obtener información del usuario"""
    user_id: Optional[int] = Field(
        None,
        description="ID del usuario (opcional, por defecto el usuario actual)"
    )
    include_permissions: bool = Field(
        default=True,
        description="Incluir permisos detallados"
    )
    include_sessions: bool = Field(
        default=False,
        description="Incluir sesiones activas"
    )

# Responses

class LoginResponse(BaseResponse):
    """Response de login exitoso"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    user: UserInfo = Field(
        description="Información del usuario"
    )
    session: AuthSession = Field(
        description="Información de la sesión"
    )
    access_token: AuthToken = Field(
        description="Token de acceso"
    )
    refresh_token: Optional[AuthToken] = Field(
        None,
        description="Token de renovación"
    )

class TokenValidationResponse(BaseResponse):
    """Response de validación de token"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    valid: bool = Field(
        description="Token válido"
    )
    user: Optional[UserInfo] = Field(
        None,
        description="Información del usuario (si el token es válido)"
    )
    token_info: Optional[AuthToken] = Field(
        None,
        description="Información del token"
    )
    expires_in: Optional[int] = Field(
        None,
        description="Segundos hasta la expiración"
    )

class RefreshTokenResponse(BaseResponse):
    """Response de renovación de token"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    access_token: AuthToken = Field(
        description="Nuevo token de acceso"
    )
    refresh_token: Optional[AuthToken] = Field(
        None,
        description="Nuevo token de renovación (si se renovó)"
    )

class LogoutResponse(BaseResponse):
    """Response de logout"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    sessions_revoked: int = Field(
        description="Número de sesiones revocadas"
    )
    tokens_revoked: int = Field(
        description="Número de tokens revocados"
    )

class PermissionCheckResponse(BaseResponse):
    """Response de verificación de permisos"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    has_permission: bool = Field(
        description="Usuario tiene el permiso"
    )
    permission_details: Optional[Permission] = Field(
        None,
        description="Detalles del permiso (si existe)"
    )
    reason: Optional[str] = Field(
        None,
        description="Razón si no tiene permiso"
    )

class UserInfoResponse(BaseResponse):
    """Response de información del usuario"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    user: UserInfo = Field(
        description="Información del usuario"
    )
    active_sessions: Optional[List[AuthSession]] = Field(
        None,
        description="Sesiones activas (si se solicitó)"
    )

# Funciones de utilidad

def create_user_info_from_odoo_data(
    odoo_data: Dict[str, Any]
) -> UserInfo:
    """Crear UserInfo desde datos de Odoo"""
    
    # Mapear roles desde grupos de Odoo
    roles = []
    if odoo_data.get('groups_id'):
        group_names = odoo_data.get('group_names', [])
        
        # Mapeo de grupos de Odoo a roles
        role_mapping = {
            'base.group_system': UserRole.ADMIN,
            'base.group_erp_manager': UserRole.MANAGER,
            'base.group_user': UserRole.USER,
            'fieldservice.group_fsm_user': UserRole.TECHNICIAN,
            'base.group_portal': UserRole.CUSTOMER,
            'base.group_public': UserRole.READONLY
        }
        
        for group_name in group_names:
            if group_name in role_mapping:
                roles.append(role_mapping[group_name])
    
    # Si no hay roles específicos, asignar USER por defecto
    if not roles:
        roles = [UserRole.USER]
    
    # Crear permisos básicos basados en roles
    permissions = []
    for role in roles:
        if role == UserRole.ADMIN:
            # Los admins tienen todos los permisos
            for resource_type in ResourceType:
                for permission_type in PermissionType:
                    permissions.append(Permission(
                        resource_type=resource_type,
                        permission_type=permission_type
                    ))
        elif role == UserRole.MANAGER:
            # Los managers tienen permisos de lectura y escritura
            for resource_type in ResourceType:
                for permission_type in [PermissionType.READ, PermissionType.WRITE, PermissionType.CREATE]:
                    permissions.append(Permission(
                        resource_type=resource_type,
                        permission_type=permission_type
                    ))
        elif role == UserRole.TECHNICIAN:
            # Los técnicos tienen permisos sobre FSM y equipos
            for resource_type in [ResourceType.FSM_ORDER, ResourceType.EQUIPMENT, ResourceType.KNOWLEDGE]:
                for permission_type in [PermissionType.READ, PermissionType.WRITE]:
                    permissions.append(Permission(
                        resource_type=resource_type,
                        permission_type=permission_type
                    ))
        elif role == UserRole.USER:
            # Los usuarios tienen permisos básicos de lectura
            for resource_type in ResourceType:
                permissions.append(Permission(
                    resource_type=resource_type,
                    permission_type=PermissionType.READ
                ))
    
    return UserInfo(
        id=odoo_data.get('id'),
        login=odoo_data.get('login', ''),
        name=odoo_data.get('name', ''),
        email=odoo_data.get('email'),
        company_id=odoo_data.get('company_id', 1),
        company_name=odoo_data.get('company_name', ''),
        roles=roles,
        permissions=permissions,
        language=odoo_data.get('lang'),
        timezone=odoo_data.get('tz'),
        avatar_url=odoo_data.get('avatar_url'),
        last_login=odoo_data.get('login_date'),
        active=odoo_data.get('active', True),
        is_admin=UserRole.ADMIN in roles
    )

def generate_jwt_token(
    user_info: UserInfo,
    token_type: TokenType = TokenType.ACCESS,
    expires_in: int = 3600,
    secret_key: str = "your-secret-key",
    algorithm: str = "HS256"
) -> AuthToken:
    """Generar token JWT"""
    import jwt
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=expires_in)
    
    payload = {
        'user_id': user_info.id,
        'login': user_info.login,
        'company_id': user_info.company_id,
        'roles': [role.value for role in user_info.roles],
        'token_type': token_type.value,
        'iat': now,
        'exp': expires_at,
        'iss': 'mcp-server',
        'aud': 'mcp-client'
    }
    
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    
    return AuthToken(
        token=token,
        token_type=token_type,
        expires_at=expires_at,
        user_id=user_info.id,
        user_login=user_info.login,
        issued_at=now,
        issuer='mcp-server',
        audience='mcp-client',
        scopes=[role.value for role in user_info.roles]
    )

def validate_jwt_token(
    token: str,
    secret_key: str = "your-secret-key",
    algorithm: str = "HS256"
) -> Optional[Dict[str, Any]]:
    """Validar token JWT"""
    import jwt
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def check_password_strength(password: str) -> Dict[str, Any]:
    """Verificar fortaleza de contraseña"""
    import re
    
    result = {
        'is_strong': False,
        'score': 0,
        'issues': [],
        'suggestions': []
    }
    
    # Verificar longitud
    if len(password) < 8:
        result['issues'].append('Contraseña muy corta')
        result['suggestions'].append('Use al menos 8 caracteres')
    else:
        result['score'] += 1
    
    # Verificar mayúsculas
    if not re.search(r'[A-Z]', password):
        result['issues'].append('Falta mayúscula')
        result['suggestions'].append('Incluya al menos una letra mayúscula')
    else:
        result['score'] += 1
    
    # Verificar minúsculas
    if not re.search(r'[a-z]', password):
        result['issues'].append('Falta minúscula')
        result['suggestions'].append('Incluya al menos una letra minúscula')
    else:
        result['score'] += 1
    
    # Verificar números
    if not re.search(r'\d', password):
        result['issues'].append('Falta número')
        result['suggestions'].append('Incluya al menos un número')
    else:
        result['score'] += 1
    
    # Verificar caracteres especiales
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['issues'].append('Falta carácter especial')
        result['suggestions'].append('Incluya al menos un carácter especial')
    else:
        result['score'] += 1
    
    # Determinar si es fuerte
    result['is_strong'] = result['score'] >= 4 and len(password) >= 8
    
    return result

def create_session_id() -> str:
    """Crear ID único de sesión"""
    import uuid
    return str(uuid.uuid4())

def hash_password(password: str) -> str:
    """Hash de contraseña usando bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verificar contraseña contra hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))