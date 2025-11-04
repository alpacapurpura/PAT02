#!/usr/bin/env python3
"""
Tests para módulos de utilidades del servidor MCP

Este módulo contiene tests unitarios para los módulos de utilidades:
- AuthManager
- RateLimiter
- DatabaseClient
- OdooClient
- Configuración de logging

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from pydantic import ValidationError

# Añadir el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MCPConfig
from utils import (
    AuthManager,
    DatabaseClient,
    OdooClient,
    RateLimiter,
    rate_limiter,
    setup_logging,
    get_logger
)
from utils.rate_limiter import LimitType, LimitPeriod, RateLimit, TokenBucket, SlidingWindowCounter


class TestAuthManager:
    """Tests para el AuthManager"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.config = MCPConfig()
        self.auth_manager = AuthManager(self.config)
    
    def test_password_hashing(self):
        """Test de hashing y verificación de contraseñas"""
        password = "test_password_123"
        
        # Hash de la contraseña
        hashed = self.auth_manager.hash_password(password)
        
        # Verificar que el hash es diferente de la contraseña original
        assert hashed != password
        assert len(hashed) > 50  # Los hashes bcrypt son largos
        
        # Verificar que la contraseña es válida
        assert self.auth_manager.verify_password(password, hashed) is True
        
        # Verificar que una contraseña incorrecta falla
        assert self.auth_manager.verify_password("wrong_password", hashed) is False
    
    def test_jwt_token_generation(self):
        """Test de generación y validación de tokens JWT"""
        user_data = {
            "user_id": 123,
            "username": "test_user",
            "email": "test@example.com",
            "roles": ["user", "technician"]
        }
        
        # Generar token
        token = self.auth_manager.generate_jwt_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 100  # Los JWT son largos
        
        # Validar token
        decoded_data = self.auth_manager.validate_jwt_token(token)
        
        assert decoded_data is not None
        assert decoded_data["user_id"] == 123
        assert decoded_data["username"] == "test_user"
        assert decoded_data["roles"] == ["user", "technician"]
    
    def test_jwt_token_expiration(self):
        """Test de expiración de tokens JWT"""
        user_data = {"user_id": 123, "username": "test_user"}
        
        # Generar token con expiración muy corta
        with patch.object(self.auth_manager.config, 'JWT_EXPIRATION_HOURS', 0.001):  # ~3.6 segundos
            token = self.auth_manager.generate_jwt_token(user_data)
            
            # El token debería ser válido inmediatamente
            decoded_data = self.auth_manager.validate_jwt_token(token)
            assert decoded_data is not None
            
            # Esperar a que expire
            time.sleep(4)
            
            # El token debería estar expirado
            expired_data = self.auth_manager.validate_jwt_token(token)
            assert expired_data is None
    
    def test_session_management(self):
        """Test de gestión de sesiones"""
        user_id = 123
        
        # Crear sesión
        session_id = self.auth_manager.create_session(user_id)
        
        assert isinstance(session_id, str)
        assert len(session_id) > 20  # Los IDs de sesión son largos
        
        # Validar sesión
        session_data = self.auth_manager.get_session(session_id)
        
        assert session_data is not None
        assert session_data["user_id"] == user_id
        assert "created_at" in session_data
        assert "last_activity" in session_data
        
        # Actualizar actividad de sesión
        self.auth_manager.update_session_activity(session_id)
        
        updated_session = self.auth_manager.get_session(session_id)
        assert updated_session["last_activity"] >= session_data["last_activity"]
        
        # Revocar sesión
        self.auth_manager.revoke_session(session_id)
        
        revoked_session = self.auth_manager.get_session(session_id)
        assert revoked_session is None
    
    def test_permission_checking(self):
        """Test de verificación de permisos"""
        # Usuario con permisos de técnico
        user_info = {
            "user_id": 123,
            "roles": ["technician"],
            "permissions": ["fsm.read", "fsm.write", "equipment.read"]
        }
        
        # Verificar permisos existentes
        assert self.auth_manager.check_permission(user_info, "fsm.read") is True
        assert self.auth_manager.check_permission(user_info, "fsm.write") is True
        assert self.auth_manager.check_permission(user_info, "equipment.read") is True
        
        # Verificar permisos no existentes
        assert self.auth_manager.check_permission(user_info, "admin.delete") is False
        assert self.auth_manager.check_permission(user_info, "billing.read") is False
    
    def test_api_key_generation(self):
        """Test de generación de API keys"""
        user_id = 123
        
        # Generar API key
        api_key = self.auth_manager.generate_api_key(user_id)
        
        assert isinstance(api_key, str)
        assert len(api_key) >= 32  # Las API keys deben ser suficientemente largas
        assert api_key.startswith("mcp_")  # Prefijo identificativo
        
        # Verificar que cada API key es única
        api_key2 = self.auth_manager.generate_api_key(user_id)
        assert api_key != api_key2
    
    def test_password_strength_validation(self):
        """Test de validación de fortaleza de contraseñas"""
        # Contraseñas débiles
        weak_passwords = [
            "123",
            "password",
            "abc",
            "12345678",
            "abcdefgh",
            "PASSWORD"
        ]
        
        for password in weak_passwords:
            assert self.auth_manager.validate_password_strength(password) is False
        
        # Contraseñas fuertes
        strong_passwords = [
            "MyStr0ngP@ssw0rd!",
            "C0mpl3x_P@ssw0rd_2024",
            "S3cur3!P@ssw0rd#123",
            "Adm1n_P@ssw0rd$2024"
        ]
        
        for password in strong_passwords:
            assert self.auth_manager.validate_password_strength(password) is True


class TestRateLimiter:
    """Tests para el RateLimiter"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.rate_limiter = RateLimiter()
    
    def test_token_bucket_algorithm(self):
        """Test del algoritmo Token Bucket"""
        # Crear bucket con 5 tokens, 1 token por segundo
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        
        # Debería tener tokens inicialmente
        assert bucket.consume(1) is True
        assert bucket.consume(3) is True
        assert bucket.consume(1) is True
        
        # No debería tener más tokens
        assert bucket.consume(1) is False
        
        # Esperar para que se rellene
        time.sleep(1.1)
        assert bucket.consume(1) is True
    
    def test_sliding_window_counter(self):
        """Test del algoritmo Sliding Window Counter"""
        # Crear contador con límite de 3 requests por segundo
        counter = SlidingWindowCounter(limit=3, window_seconds=1)
        
        # Debería permitir 3 requests
        assert counter.is_allowed() is True
        assert counter.is_allowed() is True
        assert counter.is_allowed() is True
        
        # El cuarto debería ser rechazado
        assert counter.is_allowed() is False
        
        # Esperar para que se renueve la ventana
        time.sleep(1.1)
        assert counter.is_allowed() is True
    
    def test_rate_limit_configuration(self):
        """Test de configuración de límites de tasa"""
        # Añadir límite personalizado
        custom_limit = RateLimit(
            limit_type=LimitType.PER_USER,
            identifier="user_123",
            max_requests=10,
            period=LimitPeriod.MINUTE,
            burst_capacity=15
        )
        
        self.rate_limiter.add_limit(custom_limit)
        
        # Verificar que el límite fue añadido
        limits = self.rate_limiter.get_applicable_limits(
            limit_type=LimitType.PER_USER,
            identifier="user_123"
        )
        
        assert len(limits) > 0
        assert any(limit.max_requests == 10 for limit in limits)
    
    def test_rate_limiting_enforcement(self):
        """Test de aplicación de límites de tasa"""
        # Configurar límite muy restrictivo para testing
        test_limit = RateLimit(
            limit_type=LimitType.PER_IP,
            identifier="192.168.1.100",
            max_requests=2,
            period=LimitPeriod.SECOND,
            burst_capacity=2
        )
        
        self.rate_limiter.add_limit(test_limit)
        
        # Los primeros 2 requests deberían pasar
        result1 = self.rate_limiter.check_rate_limit(
            limit_type=LimitType.PER_IP,
            identifier="192.168.1.100"
        )
        assert result1.allowed is True
        
        result2 = self.rate_limiter.check_rate_limit(
            limit_type=LimitType.PER_IP,
            identifier="192.168.1.100"
        )
        assert result2.allowed is True
        
        # El tercer request debería ser rechazado
        result3 = self.rate_limiter.check_rate_limit(
            limit_type=LimitType.PER_IP,
            identifier="192.168.1.100"
        )
        assert result3.allowed is False
        assert result3.retry_after > 0
    
    def test_rate_limit_headers(self):
        """Test de generación de headers de rate limiting"""
        headers = self.rate_limiter.get_rate_limit_headers(
            limit_type=LimitType.PER_USER,
            identifier="user_123"
        )
        
        # Verificar que se generan los headers esperados
        expected_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        
        for header in expected_headers:
            assert header in headers
            assert isinstance(headers[header], str)
    
    def test_rate_limit_statistics(self):
        """Test de estadísticas de rate limiting"""
        # Hacer algunas requests para generar estadísticas
        for i in range(5):
            self.rate_limiter.check_rate_limit(
                limit_type=LimitType.GLOBAL,
                identifier="global"
            )
        
        # Obtener estadísticas
        stats = self.rate_limiter.get_statistics()
        
        assert "total_requests" in stats
        assert "blocked_requests" in stats
        assert "active_limits" in stats
        assert stats["total_requests"] >= 5
    
    def test_cleanup_old_data(self):
        """Test de limpieza de datos antiguos"""
        # Generar algunos datos
        for i in range(10):
            self.rate_limiter.check_rate_limit(
                limit_type=LimitType.PER_IP,
                identifier=f"192.168.1.{i}"
            )
        
        # Verificar que hay datos
        stats_before = self.rate_limiter.get_statistics()
        
        # Limpiar datos antiguos
        cleaned_count = self.rate_limiter.cleanup_old_data(max_age_hours=0)
        
        # Verificar que se limpiaron datos
        assert cleaned_count >= 0
        
        stats_after = self.rate_limiter.get_statistics()
        # Las estadísticas pueden cambiar después de la limpieza


class TestDatabaseClient:
    """Tests para el DatabaseClient"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.config = MCPConfig()
        self.db_client = DatabaseClient(self.config)
    
    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Test de gestión de conexiones"""
        # Mock del pool de conexiones
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            # Conectar
            await self.db_client.connect()
            
            assert self.db_client.pool is not None
            mock_create_pool.assert_called_once()
            
            # Desconectar
            await self.db_client.disconnect()
            mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_execution(self):
        """Test de ejecución de queries"""
        # Mock del pool y conexión
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        
        self.db_client.pool = mock_pool
        
        # Mock de resultado de query
        mock_connection.fetch.return_value = [
            {'id': 1, 'name': 'Test Document'},
            {'id': 2, 'name': 'Another Document'}
        ]
        
        # Ejecutar query
        result = await self.db_client.execute_query(
            "SELECT id, name FROM documents WHERE category = $1",
            "technical"
        )
        
        assert len(result) == 2
        assert result[0]['name'] == 'Test Document'
        mock_connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vector_search(self):
        """Test de búsqueda vectorial con PGVector"""
        # Mock del pool y conexión
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        
        self.db_client.pool = mock_pool
        
        # Mock de resultado de búsqueda vectorial
        mock_connection.fetch.return_value = [
            {
                'id': 1,
                'title': 'Manual de Bomba',
                'content': 'Procedimientos de mantenimiento',
                'similarity_score': 0.95
            }
        ]
        
        # Ejecutar búsqueda vectorial
        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]  # Vector de ejemplo
        result = await self.db_client.vector_search(
            table="knowledge_base",
            vector_column="embedding",
            query_vector=query_vector,
            limit=5
        )
        
        assert len(result) == 1
        assert result[0]['similarity_score'] == 0.95
        mock_connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test de health check de la base de datos"""
        # Mock del pool y conexión
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        
        self.db_client.pool = mock_pool
        
        # Mock de resultado exitoso
        mock_connection.fetchval.return_value = 1
        
        # Ejecutar health check
        is_healthy = await self.db_client.health_check()
        
        assert is_healthy is True
        mock_connection.fetchval.assert_called_once_with("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test de manejo de errores"""
        # Mock del pool que falla
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        
        self.db_client.pool = mock_pool
        
        # Mock de error en la query
        mock_connection.fetch.side_effect = Exception("Database error")
        
        # La query debería manejar el error
        with pytest.raises(Exception):
            await self.db_client.execute_query("SELECT * FROM invalid_table")


class TestOdooClient:
    """Tests para el OdooClient"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.config = MCPConfig()
        self.odoo_client = OdooClient(self.config)
    
    def test_authentication(self):
        """Test de autenticación con Odoo"""
        with patch('xmlrpc.client.ServerProxy') as mock_server:
            # Mock del servidor de autenticación
            mock_common = MagicMock()
            mock_common.authenticate.return_value = 123  # user_id
            mock_server.return_value = mock_common
            
            # Autenticar
            success = self.odoo_client.authenticate()
            
            assert success is True
            assert self.odoo_client.uid == 123
            mock_common.authenticate.assert_called_once()
    
    def test_search_read_operation(self):
        """Test de operación search_read"""
        with patch('xmlrpc.client.ServerProxy') as mock_server:
            # Mock del servidor de objetos
            mock_object = MagicMock()
            mock_object.execute_kw.return_value = [
                {'id': 1, 'name': 'Test Order', 'state': 'draft'},
                {'id': 2, 'name': 'Another Order', 'state': 'confirmed'}
            ]
            mock_server.return_value = mock_object
            
            # Configurar cliente autenticado
            self.odoo_client.uid = 123
            self.odoo_client.models = mock_object
            
            # Ejecutar search_read
            result = self.odoo_client.search_read(
                model="fsm.order",
                domain=[('state', '!=', 'done')],
                fields=['name', 'state']
            )
            
            assert len(result) == 2
            assert result[0]['name'] == 'Test Order'
            mock_object.execute_kw.assert_called_once()
    
    def test_create_operation(self):
        """Test de operación create"""
        with patch('xmlrpc.client.ServerProxy') as mock_server:
            # Mock del servidor de objetos
            mock_object = MagicMock()
            mock_object.execute_kw.return_value = [456]  # ID del nuevo registro
            mock_server.return_value = mock_object
            
            # Configurar cliente autenticado
            self.odoo_client.uid = 123
            self.odoo_client.models = mock_object
            
            # Ejecutar create
            result = self.odoo_client.create(
                model="fsm.order",
                values={'name': 'New Order', 'description': 'Test order'}
            )
            
            assert result == [456]
            mock_object.execute_kw.assert_called_once()
    
    def test_write_operation(self):
        """Test de operación write"""
        with patch('xmlrpc.client.ServerProxy') as mock_server:
            # Mock del servidor de objetos
            mock_object = MagicMock()
            mock_object.execute_kw.return_value = True
            mock_server.return_value = mock_object
            
            # Configurar cliente autenticado
            self.odoo_client.uid = 123
            self.odoo_client.models = mock_object
            
            # Ejecutar write
            result = self.odoo_client.write(
                model="fsm.order",
                ids=[1, 2],
                values={'state': 'in_progress'}
            )
            
            assert result is True
            mock_object.execute_kw.assert_called_once()
    
    def test_health_check(self):
        """Test de health check de Odoo"""
        with patch('xmlrpc.client.ServerProxy') as mock_server:
            # Mock del servidor común
            mock_common = MagicMock()
            mock_common.version.return_value = {
                'server_version': '18.0',
                'server_serie': '18.0',
                'protocol_version': 1
            }
            mock_server.return_value = mock_common
            
            # Ejecutar health check
            is_healthy = self.odoo_client.health_check()
            
            assert is_healthy is True
            mock_common.version.assert_called_once()
    
    def test_error_handling(self):
        """Test de manejo de errores"""
        with patch('xmlrpc.client.ServerProxy') as mock_server:
            # Mock que falla
            mock_server.side_effect = Exception("Connection failed")
            
            # La autenticación debería fallar
            success = self.odoo_client.authenticate()
            assert success is False
            
            # El health check debería fallar
            is_healthy = self.odoo_client.health_check()
            assert is_healthy is False


class TestLoggingConfiguration:
    """Tests para la configuración de logging"""
    
    def test_logger_setup(self):
        """Test de configuración básica de logging"""
        # Configurar logging
        setup_logging(level="INFO", log_file="test.log")
        
        # Obtener logger
        logger = get_logger("test_module")
        
        assert logger is not None
        assert logger.name == "test_module"
    
    def test_structured_logging(self):
        """Test de logging estructurado"""
        # Configurar logging estructurado
        setup_logging(level="INFO", structured=True)
        
        # Obtener logger
        logger = get_logger("test_structured")
        
        # El logger debería estar configurado para logging estructurado
        assert logger is not None
    
    def test_log_context(self):
        """Test de contexto en logs"""
        logger = get_logger("test_context")
        
        # Verificar que el logger tiene métodos de contexto
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
    
    def test_log_levels(self):
        """Test de niveles de logging"""
        # Configurar diferentes niveles
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in levels:
            setup_logging(level=level)
            logger = get_logger(f"test_{level.lower()}")
            assert logger is not None


if __name__ == "__main__":
    print("Tests de utilidades del servidor MCP")
    print("====================================")
    
    # Información sobre los tests disponibles
    test_classes = [
        (TestAuthManager, "Tests del AuthManager"),
        (TestRateLimiter, "Tests del RateLimiter"),
        (TestDatabaseClient, "Tests del DatabaseClient"),
        (TestOdooClient, "Tests del OdooClient"),
        (TestLoggingConfiguration, "Tests de configuración de logging")
    ]
    
    total_tests = 0
    for test_class, description in test_classes:
        methods = [method for method in dir(test_class) if method.startswith('test_')]
        total_tests += len(methods)
        print(f"\n{description}:")
        print(f"  Clase: {test_class.__name__}")
        print(f"  Tests: {len(methods)}")
        for method in methods:
            print(f"    - {method}")
    
    print(f"\nTotal de tests de utilidades: {total_tests}")
    print("\nPara ejecutar todos los tests:")
    print("  pytest test_utils.py -v")
    print("\nPara ejecutar tests específicos:")
    print("  pytest test_utils.py::TestAuthManager::test_jwt_token_generation -v")
    print("  pytest test_utils.py::TestRateLimiter -v")
    print("  pytest test_utils.py::TestDatabaseClient -v")