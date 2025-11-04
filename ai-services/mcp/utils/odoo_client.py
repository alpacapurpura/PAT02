#!/usr/bin/env python3
"""
Cliente para comunicación con Odoo via XML-RPC
Maneja autenticación, llamadas a métodos y gestión de sesiones
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import xmlrpc.client
import ssl
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class OdooConnectionError(Exception):
    """Excepción para errores de conexión con Odoo"""
    pass

class OdooAuthenticationError(Exception):
    """Excepción para errores de autenticación con Odoo"""
    pass

class OdooAPIError(Exception):
    """Excepción para errores de API de Odoo"""
    pass

class OdooClient:
    """Cliente asíncrono para comunicación con Odoo"""
    
    def __init__(
        self, 
        url: str, 
        db: str, 
        username: str, 
        password: str,
        timeout: int = 30,
        use_ssl: bool = False
    ):
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.timeout = timeout
        self.use_ssl = use_ssl
        
        # Estado de la conexión
        self.uid = None
        self.session_id = None
        self.is_authenticated = False
        self.last_activity = None
        
        # Clientes XML-RPC
        self._common = None
        self._object = None
        
        # Cache de metadatos
        self._model_cache = {}
        self._field_cache = {}
        
        logger.info(f"Cliente Odoo inicializado para {url} - DB: {db}")
    
    async def _get_xmlrpc_client(self, endpoint: str):
        """Obtener cliente XML-RPC para un endpoint específico"""
        url = urljoin(self.url, f'/xmlrpc/2/{endpoint}')
        
        # Configurar SSL si es necesario
        if self.use_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return xmlrpc.client.ServerProxy(url, context=context)
        else:
            return xmlrpc.client.ServerProxy(url)
    
    async def authenticate(self) -> bool:
        """Autenticar con Odoo y obtener UID"""
        try:
            logger.info(f"Autenticando con Odoo: {self.username}@{self.db}")
            
            # Obtener cliente common
            if not self._common:
                self._common = await self._get_xmlrpc_client('common')
            
            # Verificar versión de Odoo
            version_info = self._common.version()
            logger.info(f"Versión de Odoo: {version_info.get('server_version', 'unknown')}")
            
            # Autenticar y obtener UID
            self.uid = self._common.authenticate(
                self.db, 
                self.username, 
                self.password, 
                {}
            )
            
            if not self.uid:
                raise OdooAuthenticationError(
                    f"Falló la autenticación para {self.username}@{self.db}"
                )
            
            # Obtener cliente object
            self._object = await self._get_xmlrpc_client('object')
            
            self.is_authenticated = True
            self.last_activity = datetime.utcnow()
            
            logger.info(f"Autenticación exitosa - UID: {self.uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            self.is_authenticated = False
            raise OdooConnectionError(f"Error de conexión con Odoo: {str(e)}")
    
    async def call(
        self, 
        model: str, 
        method: str, 
        args: List[Any] = None, 
        kwargs: Dict[str, Any] = None
    ) -> Any:
        """Realizar llamada a método de Odoo"""
        if not self.is_authenticated:
            await self.authenticate()
        
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        
        try:
            logger.debug(f"Llamada Odoo: {model}.{method}({args}, {kwargs})")
            
            result = self._object.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs
            )
            
            self.last_activity = datetime.utcnow()
            return result
            
        except Exception as e:
            logger.error(f"Error en llamada Odoo {model}.{method}: {e}")
            
            # Intentar reautenticar si el error parece ser de sesión
            if "session" in str(e).lower() or "authentication" in str(e).lower():
                logger.info("Intentando reautenticación...")
                self.is_authenticated = False
                await self.authenticate()
                
                # Reintentar la llamada
                result = self._object.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model,
                    method,
                    args,
                    kwargs
                )
                return result
            
            raise OdooAPIError(f"Error en API de Odoo: {str(e)}")
    
    async def search(
        self, 
        model: str, 
        domain: List[Any] = None, 
        offset: int = 0, 
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[int]:
        """Buscar registros en Odoo"""
        if domain is None:
            domain = []
        
        kwargs = {'offset': offset}
        if limit is not None:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order
        
        return await self.call(model, 'search', [domain], kwargs)
    
    async def read(
        self, 
        model: str, 
        ids: Union[int, List[int]], 
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Leer registros de Odoo"""
        if isinstance(ids, int):
            ids = [ids]
        
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        
        return await self.call(model, 'read', [ids], kwargs)
    
    async def search_read(
        self, 
        model: str, 
        domain: List[Any] = None, 
        fields: Optional[List[str]] = None,
        offset: int = 0, 
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Buscar y leer registros en una sola llamada"""
        if domain is None:
            domain = []
        
        kwargs = {'offset': offset}
        if fields:
            kwargs['fields'] = fields
        if limit is not None:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order
        
        return await self.call(model, 'search_read', [domain], kwargs)
    
    async def create(
        self, 
        model: str, 
        values: Dict[str, Any]
    ) -> int:
        """Crear registro en Odoo"""
        return await self.call(model, 'create', [values])
    
    async def write(
        self, 
        model: str, 
        ids: Union[int, List[int]], 
        values: Dict[str, Any]
    ) -> bool:
        """Actualizar registros en Odoo"""
        if isinstance(ids, int):
            ids = [ids]
        
        return await self.call(model, 'write', [ids, values])
    
    async def unlink(
        self, 
        model: str, 
        ids: Union[int, List[int]]
    ) -> bool:
        """Eliminar registros en Odoo"""
        if isinstance(ids, int):
            ids = [ids]
        
        return await self.call(model, 'unlink', [ids])
    
    async def get_model_fields(
        self, 
        model: str, 
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Obtener campos de un modelo"""
        if use_cache and model in self._field_cache:
            return self._field_cache[model]
        
        fields = await self.call(model, 'fields_get')
        
        if use_cache:
            self._field_cache[model] = fields
        
        return fields
    
    async def check_access_rights(
        self, 
        model: str, 
        operation: str = 'read'
    ) -> bool:
        """Verificar derechos de acceso para un modelo"""
        try:
            return await self.call(
                model, 
                'check_access_rights', 
                [operation], 
                {'raise_exception': False}
            )
        except Exception:
            return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Obtener información del usuario actual"""
        if not self.uid:
            raise OdooAuthenticationError("Usuario no autenticado")
        
        user_info = await self.read(
            'res.users', 
            self.uid, 
            ['name', 'login', 'email', 'company_id', 'groups_id']
        )
        
        return user_info[0] if user_info else {}
    
    async def get_company_info(self) -> Dict[str, Any]:
        """Obtener información de la compañía actual"""
        user_info = await self.get_user_info()
        company_id = user_info.get('company_id')
        
        if not company_id:
            return {}
        
        if isinstance(company_id, list):
            company_id = company_id[0]
        
        company_info = await self.read(
            'res.company',
            company_id,
            ['name', 'email', 'phone', 'website', 'currency_id']
        )
        
        return company_info[0] if company_info else {}
    
    async def execute_workflow(
        self, 
        model: str, 
        record_id: int, 
        signal: str
    ) -> bool:
        """Ejecutar workflow en un registro"""
        try:
            return await self.call(
                'workflow', 
                'trg_validate', 
                [self.uid, model, record_id, signal, {}]
            )
        except Exception as e:
            logger.warning(f"Error ejecutando workflow {signal} en {model}:{record_id}: {e}")
            return False
    
    async def get_server_version(self) -> Dict[str, Any]:
        """Obtener información de versión del servidor"""
        if not self._common:
            self._common = await self._get_xmlrpc_client('common')
        
        return self._common.version()
    
    def is_session_valid(self) -> bool:
        """Verificar si la sesión sigue siendo válida"""
        if not self.is_authenticated or not self.last_activity:
            return False
        
        # Considerar sesión válida por 30 minutos
        session_timeout = timedelta(minutes=30)
        return datetime.utcnow() - self.last_activity < session_timeout
    
    async def refresh_session(self) -> bool:
        """Refrescar sesión si es necesario"""
        if not self.is_session_valid():
            logger.info("Sesión expirada, reautenticando...")
            self.is_authenticated = False
            return await self.authenticate()
        return True
    
    async def close(self):
        """Cerrar conexión"""
        self.is_authenticated = False
        self.uid = None
        self._common = None
        self._object = None
        self._model_cache.clear()
        self._field_cache.clear()
        
        logger.info("Cliente Odoo cerrado")
    
    def __str__(self) -> str:
        return f"OdooClient({self.url}, {self.db}, {self.username})"
    
    def __repr__(self) -> str:
        return (
            f"OdooClient(url='{self.url}', db='{self.db}', "
            f"username='{self.username}', authenticated={self.is_authenticated})"
        )

# Funciones de utilidad

async def test_odoo_connection(
    url: str, 
    db: str, 
    username: str, 
    password: str
) -> Dict[str, Any]:
    """Probar conexión con Odoo"""
    client = OdooClient(url, db, username, password)
    
    try:
        await client.authenticate()
        
        user_info = await client.get_user_info()
        server_version = await client.get_server_version()
        
        result = {
            "success": True,
            "user": user_info,
            "server_version": server_version,
            "connection_time": datetime.utcnow().isoformat()
        }
        
        await client.close()
        return result
        
    except Exception as e:
        await client.close()
        return {
            "success": False,
            "error": str(e),
            "connection_time": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio
    
    async def main():
        client = OdooClient(
            url="http://localhost:8069",
            db="odoo_patco",
            username="admin",
            password="admin"
        )
        
        try:
            await client.authenticate()
            print(f"✅ Conectado como UID: {client.uid}")
            
            # Obtener información del usuario
            user_info = await client.get_user_info()
            print(f"Usuario: {user_info.get('name')}")
            
            # Probar búsqueda
            partners = await client.search_read(
                'res.partner',
                [('is_company', '=', True)],
                ['name', 'email'],
                limit=5
            )
            print(f"Encontradas {len(partners)} compañías")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()
    
    asyncio.run(main())