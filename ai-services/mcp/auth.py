#!/usr/bin/env python3
"""
Módulo de autenticación y seguridad para el servidor MCP PATCO
Maneja la autenticación con Odoo y la validación de tokens
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings
from utils.odoo_client import OdooClient

logger = logging.getLogger(__name__)

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Cache de usuarios autenticados (en producción usar Redis)
user_cache: Dict[str, Dict[str, Any]] = {}
cache_ttl = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

class AuthenticationError(Exception):
    """Excepción personalizada para errores de autenticación"""
    pass

class AuthManager:
    """Gestor de autenticación"""
    
    def __init__(self):
        self.odoo_client = None
    
    async def initialize(self):
        """Inicializar cliente Odoo para autenticación"""
        try:
            self.odoo_client = OdooClient(
                url=settings.ODOO_URL,
                db=settings.ODOO_DB,
                username=settings.ODOO_USERNAME,
                password=settings.ODOO_PASSWORD
            )
            await self.odoo_client.authenticate()
            logger.info("AuthManager inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar AuthManager: {e}")
            raise
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Autenticar usuario contra Odoo"""
        try:
            # Crear cliente temporal para autenticación
            temp_client = OdooClient(
                url=settings.ODOO_URL,
                db=settings.ODOO_DB,
                username=username,
                password=password
            )
            
            # Intentar autenticación
            await temp_client.authenticate()
            
            # Obtener información del usuario
            user_info = await temp_client.call(
                'res.users',
                'search_read',
                [[('login', '=', username)]],
                {
                    'fields': [
                        'id', 'name', 'login', 'email', 
                        'groups_id', 'company_id', 'active'
                    ],
                    'limit': 1
                }
            )
            
            if not user_info:
                raise AuthenticationError("Usuario no encontrado")
            
            user = user_info[0]
            
            # Verificar que el usuario esté activo
            if not user.get('active', False):
                raise AuthenticationError("Usuario inactivo")
            
            # Obtener grupos del usuario
            groups = await temp_client.call(
                'res.groups',
                'search_read',
                [[('id', 'in', user['groups_id'])]],
                {'fields': ['name', 'category_id']}
            )
            
            # Cerrar cliente temporal
            await temp_client.close()
            
            return {
                'id': user['id'],
                'name': user['name'],
                'login': user['login'],
                'email': user['email'],
                'company_id': user['company_id'],
                'groups': [g['name'] for g in groups],
                'permissions': await self._get_user_permissions(user['id'])
            }
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error en autenticación de usuario {username}: {e}")
            raise AuthenticationError(f"Error de autenticación: {str(e)}")
    
    async def _get_user_permissions(self, user_id: int) -> Dict[str, bool]:
        """Obtener permisos específicos del usuario para MCP"""
        try:
            if not self.odoo_client:
                return {}
            
            # Verificar permisos específicos
            permissions = {
                'can_read_fsm': False,
                'can_write_fsm': False,
                'can_read_equipment': False,
                'can_write_equipment': False,
                'can_search_knowledge': False,
                'can_create_conversations': False
            }
            
            # Obtener grupos del usuario
            user_groups = await self.odoo_client.call(
                'res.users',
                'read',
                [user_id],
                {'fields': ['groups_id']}
            )
            
            if user_groups:
                group_ids = user_groups[0]['groups_id']
                
                # Mapear grupos a permisos
                group_permissions = {
                    'field_service.group_fsm_user': ['can_read_fsm'],
                    'field_service.group_fsm_manager': ['can_read_fsm', 'can_write_fsm'],
                    'maintenance.group_equipment_user': ['can_read_equipment'],
                    'maintenance.group_equipment_manager': ['can_read_equipment', 'can_write_equipment'],
                    'base.group_user': ['can_search_knowledge', 'can_create_conversations']
                }
                
                # Obtener nombres de grupos
                groups = await self.odoo_client.call(
                    'res.groups',
                    'search_read',
                    [[('id', 'in', group_ids)]],
                    {'fields': ['name', 'full_name']}
                )
                
                group_names = [g.get('full_name', g['name']) for g in groups]
                
                # Asignar permisos basados en grupos
                for group_name, perms in group_permissions.items():
                    if any(group_name in gn for gn in group_names):
                        for perm in perms:
                            permissions[perm] = True
            
            return permissions
            
        except Exception as e:
            logger.warning(f"Error al obtener permisos para usuario {user_id}: {e}")
            return {}

# Instancia global del gestor de autenticación
auth_manager = AuthManager()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crear token de acceso JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verificar y decodificar token JWT"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        username: str = payload.get("sub")
        if username is None:
            raise JWTError("Token inválido")
        
        return payload
        
    except JWTError as e:
        logger.warning(f"Error al verificar token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def authenticate_request(token: str) -> Dict[str, Any]:
    """Autenticar request usando token"""
    try:
        # Verificar token
        payload = verify_token(token)
        username = payload.get("sub")
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Verificar cache de usuario
        cache_key = f"user_{username}"
        if cache_key in user_cache:
            cached_user = user_cache[cache_key]
            if datetime.utcnow() < cached_user['expires']:
                return cached_user['data']
            else:
                # Limpiar cache expirado
                del user_cache[cache_key]
        
        # Obtener información del usuario desde Odoo
        if not auth_manager.odoo_client:
            await auth_manager.initialize()
        
        user_info = await auth_manager.odoo_client.call(
            'res.users',
            'search_read',
            [[('login', '=', username)]],
            {
                'fields': ['id', 'name', 'login', 'email', 'active'],
                'limit': 1
            }
        )
        
        if not user_info or not user_info[0].get('active'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo"
            )
        
        user = user_info[0]
        user['permissions'] = await auth_manager._get_user_permissions(user['id'])
        
        # Actualizar cache
        user_cache[cache_key] = {
            'data': user,
            'expires': datetime.utcnow() + cache_ttl
        }
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en autenticación de request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno de autenticación"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency para obtener usuario actual"""
    return await authenticate_request(credentials.credentials)

def require_permission(permission: str):
    """Decorator para requerir permisos específicos"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Obtener usuario del contexto
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )
            
            # Verificar permiso
            permissions = current_user.get('permissions', {})
            if not permissions.get(permission, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permiso requerido: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def check_user_permission(user: Dict[str, Any], permission: str) -> bool:
    """Verificar si el usuario tiene un permiso específico"""
    permissions = user.get('permissions', {})
    return permissions.get(permission, False)

async def login_user(username: str, password: str) -> Dict[str, Any]:
    """Login de usuario y generación de token"""
    try:
        # Autenticar usuario
        user = await auth_manager.authenticate_user(username, password)
        
        # Crear token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user['login']},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "login": user['login'],
                "email": user['email']
            }
        }
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

def clear_user_cache(username: str = None):
    """Limpiar cache de usuarios"""
    global user_cache
    
    if username:
        cache_key = f"user_{username}"
        if cache_key in user_cache:
            del user_cache[cache_key]
    else:
        user_cache.clear()
    
    logger.info(f"Cache de usuarios limpiado: {username or 'todos'}")

# Limpiar cache expirado periódicamente
async def cleanup_expired_cache():
    """Limpiar entradas expiradas del cache"""
    global user_cache
    
    now = datetime.utcnow()
    expired_keys = [
        key for key, value in user_cache.items()
        if now >= value['expires']
    ]
    
    for key in expired_keys:
        del user_cache[key]
    
    if expired_keys:
        logger.debug(f"Limpiadas {len(expired_keys)} entradas expiradas del cache")