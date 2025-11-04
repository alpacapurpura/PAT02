#!/usr/bin/env python3
"""
Gestor de Autenticación para Servidor MCP

Este módulo proporciona funcionalidades de autenticación y autorización
para el servidor MCP, incluyendo validación de tokens JWT, gestión de
sesiones y verificación de permisos.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import bcrypt
import jwt
from pydantic import ValidationError

from config import settings
from schemas.auth import (
    AuthMethod,
    AuthSession,
    AuthToken,
    Permission,
    PermissionType,
    ResourceType,
    SessionStatus,
    TokenType,
    UserInfo,
    UserRole,
)


class AuthManager:
    """Gestor de autenticación y autorización."""
    
    def __init__(self):
        """Inicializar el gestor de autenticación."""
        self.active_sessions: Dict[str, AuthSession] = {}
        self.token_blacklist: set = set()
    
    # ===== GESTIÓN DE TOKENS JWT =====
    
    def generate_token(
        self,
        user_info: UserInfo,
        token_type: TokenType = TokenType.ACCESS,
        expires_delta: Optional[timedelta] = None
    ) -> AuthToken:
        """Generar un token JWT."""
        if expires_delta is None:
            if token_type == TokenType.ACCESS:
                expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            else:  # REFRESH
                expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user_info.user_id),
            "username": user_info.username,
            "email": user_info.email,
            "role": user_info.role.value,
            "permissions": [perm.model_dump() for perm in user_info.permissions],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": token_type.value,
            "jti": secrets.token_urlsafe(32)  # JWT ID único
        }
        
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return AuthToken(
            token=token,
            token_type=token_type,
            expires_at=expire,
            user_id=user_info.user_id
        )
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Validar un token JWT.
        
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (válido, payload, error)
        """
        try:
            # Verificar si el token está en la blacklist
            if token in self.token_blacklist:
                return False, None, "Token revocado"
            
            # Decodificar y validar el token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Verificar expiración
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return False, None, "Token expirado"
            
            return True, payload, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token expirado"
        except jwt.InvalidTokenError as e:
            return False, None, f"Token inválido: {str(e)}"
        except Exception as e:
            return False, None, f"Error validando token: {str(e)}"
    
    def revoke_token(self, token: str) -> bool:
        """Revocar un token agregándolo a la blacklist."""
        try:
            # Validar que el token sea válido antes de revocarlo
            is_valid, payload, _ = self.validate_token(token)
            if is_valid and payload:
                self.token_blacklist.add(token)
                return True
            return False
        except Exception:
            return False
    
    def refresh_token(self, refresh_token: str) -> Optional[AuthToken]:
        """Renovar un token de acceso usando un refresh token."""
        is_valid, payload, error = self.validate_token(refresh_token)
        
        if not is_valid or not payload:
            return None
        
        # Verificar que sea un refresh token
        if payload.get("type") != TokenType.REFRESH.value:
            return None
        
        # Crear nuevo token de acceso
        try:
            user_info = UserInfo(
                user_id=int(payload["sub"]),
                username=payload["username"],
                email=payload["email"],
                role=UserRole(payload["role"]),
                permissions=[
                    Permission(**perm) for perm in payload.get("permissions", [])
                ]
            )
            
            return self.generate_token(user_info, TokenType.ACCESS)
            
        except (ValueError, ValidationError, KeyError):
            return None
    
    # ===== GESTIÓN DE SESIONES =====
    
    def create_session(
        self,
        user_info: UserInfo,
        auth_method: AuthMethod,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuthSession:
        """Crear una nueva sesión de usuario."""
        session_id = self.generate_session_id()
        
        session = AuthSession(
            session_id=session_id,
            user_id=user_info.user_id,
            username=user_info.username,
            auth_method=auth_method,
            status=SessionStatus.ACTIVE,
            client_ip=client_ip,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.active_sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[AuthSession]:
        """Obtener una sesión por ID."""
        session = self.active_sessions.get(session_id)
        if session and session.status == SessionStatus.ACTIVE:
            # Actualizar última actividad
            session.last_activity = datetime.utcnow()
            return session
        return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidar una sesión."""
        session = self.active_sessions.get(session_id)
        if session:
            session.status = SessionStatus.EXPIRED
            session.ended_at = datetime.utcnow()
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Limpiar sesiones expiradas."""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            # Sesiones inactivas por más de 24 horas
            if (current_time - session.last_activity).total_seconds() > 86400:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)
        
        return len(expired_sessions)
    
    # ===== GESTIÓN DE PERMISOS =====
    
    def check_permission(
        self,
        user_permissions: List[Permission],
        required_permission: PermissionType,
        resource_type: ResourceType,
        resource_id: Optional[str] = None
    ) -> bool:
        """Verificar si el usuario tiene un permiso específico."""
        for permission in user_permissions:
            # Verificar tipo de permiso
            if permission.permission_type != required_permission:
                continue
            
            # Verificar tipo de recurso
            if permission.resource_type != resource_type:
                continue
            
            # Si se especifica un recurso específico, verificarlo
            if resource_id and permission.resource_id:
                if permission.resource_id != resource_id:
                    continue
            
            return True
        
        return False
    
    def has_role_permission(
        self,
        user_role: UserRole,
        required_permission: PermissionType,
        resource_type: ResourceType
    ) -> bool:
        """Verificar si un rol tiene un permiso específico."""
        # Administradores tienen todos los permisos
        if user_role == UserRole.ADMIN:
            return True
        
        # Definir permisos por rol
        role_permissions = {
            UserRole.USER: {
                ResourceType.FSM_ORDER: [PermissionType.READ],
                ResourceType.EQUIPMENT: [PermissionType.READ],
                ResourceType.KNOWLEDGE: [PermissionType.READ],
                ResourceType.CONVERSATION: [PermissionType.READ, PermissionType.CREATE]
            },
            UserRole.MANAGER: {
                ResourceType.FSM_ORDER: [PermissionType.READ, PermissionType.UPDATE],
                ResourceType.EQUIPMENT: [PermissionType.READ, PermissionType.UPDATE],
                ResourceType.KNOWLEDGE: [PermissionType.READ],
                ResourceType.CONVERSATION: [PermissionType.READ, PermissionType.CREATE, PermissionType.UPDATE]
            },
            UserRole.TECHNICIAN: {
                ResourceType.FSM_ORDER: [PermissionType.READ, PermissionType.UPDATE],
                ResourceType.EQUIPMENT: [PermissionType.READ, PermissionType.UPDATE],
                ResourceType.KNOWLEDGE: [PermissionType.READ],
                ResourceType.CONVERSATION: [PermissionType.READ, PermissionType.CREATE]
            }
        }
        
        permissions = role_permissions.get(user_role, {})
        allowed_permissions = permissions.get(resource_type, [])
        
        return required_permission in allowed_permissions
    
    # ===== UTILIDADES DE SEGURIDAD =====
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashear una contraseña usando bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verificar una contraseña contra su hash."""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def generate_session_id() -> str:
        """Generar un ID de sesión único."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generar una API key única."""
        return f"patco_mcp_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validar la fortaleza de una contraseña.
        
        Returns:
            Tuple[bool, List[str]]: (es_válida, lista_de_errores)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        if not any(c.isupper() for c in password):
            errors.append("La contraseña debe contener al menos una mayúscula")
        
        if not any(c.islower() for c in password):
            errors.append("La contraseña debe contener al menos una minúscula")
        
        if not any(c.isdigit() for c in password):
            errors.append("La contraseña debe contener al menos un número")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("La contraseña debe contener al menos un carácter especial")
        
        return len(errors) == 0, errors
    
    def get_user_from_token(self, token: str) -> Optional[UserInfo]:
        """Obtener información del usuario desde un token."""
        is_valid, payload, _ = self.validate_token(token)
        
        if not is_valid or not payload:
            return None
        
        try:
            return UserInfo(
                user_id=int(payload["sub"]),
                username=payload["username"],
                email=payload["email"],
                role=UserRole(payload["role"]),
                permissions=[
                    Permission(**perm) for perm in payload.get("permissions", [])
                ]
            )
        except (ValueError, ValidationError, KeyError):
            return None
    
    def create_user_info_from_odoo(self, odoo_user_data: Dict[str, Any]) -> UserInfo:
        """Crear UserInfo desde datos de usuario de Odoo."""
        # Mapear grupos de Odoo a roles
        role_mapping = {
            "base.group_system": UserRole.ADMIN,
            "base.group_user": UserRole.USER,
            "project.group_project_manager": UserRole.MANAGER,
            "maintenance.group_maintenance_user": UserRole.TECHNICIAN
        }
        
        # Determinar rol basado en grupos
        user_role = UserRole.USER
        groups = odoo_user_data.get("groups_id", [])
        
        for group_id in groups:
            # Aquí necesitarías mapear los IDs de grupo a nombres
            # Por simplicidad, usamos el rol por defecto
            pass
        
        # Crear permisos basados en el rol
        permissions = self._get_default_permissions_for_role(user_role)
        
        return UserInfo(
            user_id=odoo_user_data["id"],
            username=odoo_user_data["login"],
            email=odoo_user_data.get("email", ""),
            full_name=odoo_user_data.get("name", ""),
            role=user_role,
            permissions=permissions,
            is_active=odoo_user_data.get("active", True),
            last_login=datetime.utcnow() if odoo_user_data.get("login_date") else None
        )
    
    def _get_default_permissions_for_role(self, role: UserRole) -> List[Permission]:
        """Obtener permisos por defecto para un rol."""
        permissions = []
        
        if role == UserRole.ADMIN:
            # Administradores tienen todos los permisos
            for resource_type in ResourceType:
                for permission_type in PermissionType:
                    permissions.append(Permission(
                        permission_type=permission_type,
                        resource_type=resource_type
                    ))
        
        elif role == UserRole.MANAGER:
            # Managers tienen permisos de lectura y actualización
            for resource_type in [ResourceType.FSM_ORDER, ResourceType.EQUIPMENT, ResourceType.CONVERSATION]:
                for permission_type in [PermissionType.READ, PermissionType.UPDATE]:
                    permissions.append(Permission(
                        permission_type=permission_type,
                        resource_type=resource_type
                    ))
            
            # Solo lectura para knowledge
            permissions.append(Permission(
                permission_type=PermissionType.READ,
                resource_type=ResourceType.KNOWLEDGE
            ))
        
        elif role == UserRole.TECHNICIAN:
            # Técnicos tienen permisos específicos
            for resource_type in [ResourceType.FSM_ORDER, ResourceType.EQUIPMENT]:
                for permission_type in [PermissionType.READ, PermissionType.UPDATE]:
                    permissions.append(Permission(
                        permission_type=permission_type,
                        resource_type=resource_type
                    ))
            
            # Lectura y creación para conversaciones
            for permission_type in [PermissionType.READ, PermissionType.CREATE]:
                permissions.append(Permission(
                    permission_type=permission_type,
                    resource_type=ResourceType.CONVERSATION
                ))
            
            # Solo lectura para knowledge
            permissions.append(Permission(
                permission_type=PermissionType.READ,
                resource_type=ResourceType.KNOWLEDGE
            ))
        
        else:  # USER
            # Usuarios básicos solo lectura
            for resource_type in [ResourceType.FSM_ORDER, ResourceType.EQUIPMENT, ResourceType.KNOWLEDGE]:
                permissions.append(Permission(
                    permission_type=PermissionType.READ,
                    resource_type=resource_type
                ))
            
            # Lectura y creación para conversaciones
            for permission_type in [PermissionType.READ, PermissionType.CREATE]:
                permissions.append(Permission(
                    permission_type=permission_type,
                    resource_type=ResourceType.CONVERSATION
                ))
        
        return permissions