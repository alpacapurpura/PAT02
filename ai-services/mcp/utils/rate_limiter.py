#!/usr/bin/env python3
"""
Rate Limiter para Servidor MCP

Este módulo proporciona funcionalidades de limitación de tasa (rate limiting)
para el servidor MCP, incluyendo límites por usuario, por IP, por herramienta
y límites globales del sistema.

Autor: PATCO Development Team
Versión: 1.0.0
Fecha: Enero 2025
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from config import settings


class LimitType(Enum):
    """Tipos de límites de tasa."""
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_TOOL = "per_tool"
    GLOBAL = "global"


class LimitPeriod(Enum):
    """Períodos de tiempo para límites."""
    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 86400


@dataclass
class RateLimit:
    """Configuración de límite de tasa."""
    max_requests: int
    period: LimitPeriod
    burst_allowance: int = 0  # Requests adicionales permitidos en ráfaga
    
    def __post_init__(self):
        """Validar configuración después de inicialización."""
        if self.max_requests <= 0:
            raise ValueError("max_requests debe ser mayor a 0")
        if self.burst_allowance < 0:
            raise ValueError("burst_allowance no puede ser negativo")


@dataclass
class RequestRecord:
    """Registro de una request."""
    timestamp: float
    user_id: Optional[int] = None
    client_ip: Optional[str] = None
    tool_name: Optional[str] = None
    endpoint: Optional[str] = None


@dataclass
class LimitStatus:
    """Estado actual de un límite."""
    requests_made: int
    requests_remaining: int
    reset_time: float
    is_exceeded: bool
    retry_after: Optional[float] = None


class TokenBucket:
    """Implementación de Token Bucket para rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float, refill_period: float = 1.0):
        """
        Args:
            capacity: Capacidad máxima del bucket
            refill_rate: Tokens agregados por período
            refill_period: Período de recarga en segundos
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """Intentar consumir tokens del bucket.
        
        Args:
            tokens: Número de tokens a consumir
            
        Returns:
            True si se pudieron consumir los tokens, False si no
        """
        async with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Rellenar el bucket con tokens."""
        now = time.time()
        time_passed = now - self.last_refill
        
        if time_passed >= self.refill_period:
            periods_passed = time_passed / self.refill_period
            tokens_to_add = int(periods_passed * self.refill_rate)
            
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del bucket."""
        self._refill()
        return {
            "tokens_available": self.tokens,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "next_refill": self.last_refill + self.refill_period
        }


class SlidingWindowCounter:
    """Implementación de Sliding Window Counter para rate limiting."""
    
    def __init__(self, max_requests: int, window_size: int):
        """
        Args:
            max_requests: Máximo número de requests en la ventana
            window_size: Tamaño de la ventana en segundos
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests: deque = deque()
        self._lock = asyncio.Lock()
    
    async def is_allowed(self) -> Tuple[bool, LimitStatus]:
        """Verificar si una request está permitida.
        
        Returns:
            Tuple[bool, LimitStatus]: (permitida, estado_del_límite)
        """
        async with self._lock:
            now = time.time()
            
            # Limpiar requests fuera de la ventana
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()
            
            requests_in_window = len(self.requests)
            is_allowed = requests_in_window < self.max_requests
            
            if is_allowed:
                self.requests.append(now)
                requests_in_window += 1
            
            # Calcular tiempo de reset
            reset_time = now + self.window_size
            if self.requests:
                reset_time = self.requests[0] + self.window_size
            
            status = LimitStatus(
                requests_made=requests_in_window,
                requests_remaining=max(0, self.max_requests - requests_in_window),
                reset_time=reset_time,
                is_exceeded=not is_allowed,
                retry_after=reset_time - now if not is_allowed else None
            )
            
            return is_allowed, status


class RateLimiter:
    """Rate limiter principal para el servidor MCP."""
    
    def __init__(self):
        """Inicializar el rate limiter."""
        self.limits: Dict[str, RateLimit] = {}
        self.counters: Dict[str, SlidingWindowCounter] = {}
        self.buckets: Dict[str, TokenBucket] = {}
        self.request_history: List[RequestRecord] = []
        self._setup_default_limits()
    
    def _setup_default_limits(self):
        """Configurar límites por defecto desde settings."""
        # Límites globales
        self.add_limit(
            "global",
            RateLimit(
                max_requests=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                period=LimitPeriod.MINUTE
            )
        )
        
        # Límites por usuario
        self.add_limit(
            "user_per_minute",
            RateLimit(
                max_requests=settings.RATE_LIMIT_REQUESTS_PER_MINUTE // 10,  # 10% del global
                period=LimitPeriod.MINUTE,
                burst_allowance=5
            )
        )
        
        # Límites por IP
        self.add_limit(
            "ip_per_minute",
            RateLimit(
                max_requests=settings.RATE_LIMIT_REQUESTS_PER_MINUTE // 5,  # 20% del global
                period=LimitPeriod.MINUTE
            )
        )
        
        # Límites específicos por herramienta
        tool_limits = {
            "search_knowledge_base": 30,  # Búsquedas RAG más limitadas
            "create_ai_conversation": 10,  # Conversaciones IA limitadas
            "get_fsm_order": 60,  # Consultas FSM más frecuentes
            "update_fsm_order": 20,  # Actualizaciones FSM moderadas
            "get_equipment_info": 60,  # Consultas equipos frecuentes
        }
        
        for tool_name, limit in tool_limits.items():
            self.add_limit(
                f"tool_{tool_name}",
                RateLimit(max_requests=limit, period=LimitPeriod.MINUTE)
            )
    
    def add_limit(self, key: str, limit: RateLimit):
        """Agregar un nuevo límite.
        
        Args:
            key: Clave única para el límite
            limit: Configuración del límite
        """
        self.limits[key] = limit
        
        # Crear contador de ventana deslizante
        self.counters[key] = SlidingWindowCounter(
            max_requests=limit.max_requests + limit.burst_allowance,
            window_size=limit.period.value
        )
        
        # Crear token bucket si hay burst allowance
        if limit.burst_allowance > 0:
            self.buckets[key] = TokenBucket(
                capacity=limit.burst_allowance,
                refill_rate=limit.burst_allowance / limit.period.value
            )
    
    async def check_limits(
        self,
        user_id: Optional[int] = None,
        client_ip: Optional[str] = None,
        tool_name: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Tuple[bool, Dict[str, LimitStatus]]:
        """Verificar todos los límites aplicables.
        
        Args:
            user_id: ID del usuario
            client_ip: IP del cliente
            tool_name: Nombre de la herramienta
            endpoint: Endpoint solicitado
            
        Returns:
            Tuple[bool, Dict[str, LimitStatus]]: (permitido, estados_de_límites)
        """
        statuses = {}
        all_allowed = True
        
        # Verificar límite global
        allowed, status = await self.counters["global"].is_allowed()
        statuses["global"] = status
        if not allowed:
            all_allowed = False
        
        # Verificar límite por usuario
        if user_id:
            user_key = f"user_{user_id}"
            if user_key not in self.counters:
                self.add_limit(
                    user_key,
                    self.limits["user_per_minute"]
                )
            
            allowed, status = await self.counters[user_key].is_allowed()
            statuses[f"user_{user_id}"] = status
            if not allowed:
                all_allowed = False
        
        # Verificar límite por IP
        if client_ip:
            ip_key = f"ip_{client_ip}"
            if ip_key not in self.counters:
                self.add_limit(
                    ip_key,
                    self.limits["ip_per_minute"]
                )
            
            allowed, status = await self.counters[ip_key].is_allowed()
            statuses[f"ip_{client_ip}"] = status
            if not allowed:
                all_allowed = False
        
        # Verificar límite por herramienta
        if tool_name:
            tool_key = f"tool_{tool_name}"
            if tool_key in self.counters:
                allowed, status = await self.counters[tool_key].is_allowed()
                statuses[tool_key] = status
                if not allowed:
                    all_allowed = False
        
        # Registrar la request si está permitida
        if all_allowed:
            self.request_history.append(RequestRecord(
                timestamp=time.time(),
                user_id=user_id,
                client_ip=client_ip,
                tool_name=tool_name,
                endpoint=endpoint
            ))
            
            # Limpiar historial antiguo (mantener solo últimas 1000 requests)
            if len(self.request_history) > 1000:
                self.request_history = self.request_history[-1000:]
        
        return all_allowed, statuses
    
    async def consume_burst_tokens(
        self,
        user_id: Optional[int] = None,
        tokens: int = 1
    ) -> bool:
        """Consumir tokens de burst para un usuario.
        
        Args:
            user_id: ID del usuario
            tokens: Número de tokens a consumir
            
        Returns:
            True si se pudieron consumir los tokens
        """
        if not user_id:
            return False
        
        user_key = f"user_{user_id}"
        bucket = self.buckets.get(user_key)
        
        if bucket:
            return await bucket.consume(tokens)
        
        return False
    
    def get_limit_headers(self, statuses: Dict[str, LimitStatus]) -> Dict[str, str]:
        """Generar headers HTTP para límites de tasa.
        
        Args:
            statuses: Estados de los límites
            
        Returns:
            Headers HTTP para incluir en la respuesta
        """
        headers = {}
        
        # Usar el límite más restrictivo para los headers principales
        most_restrictive = None
        min_remaining = float('inf')
        
        for key, status in statuses.items():
            if status.requests_remaining < min_remaining:
                min_remaining = status.requests_remaining
                most_restrictive = status
        
        if most_restrictive:
            headers.update({
                "X-RateLimit-Limit": str(most_restrictive.requests_made + most_restrictive.requests_remaining),
                "X-RateLimit-Remaining": str(most_restrictive.requests_remaining),
                "X-RateLimit-Reset": str(int(most_restrictive.reset_time))
            })
            
            if most_restrictive.is_exceeded and most_restrictive.retry_after:
                headers["Retry-After"] = str(int(most_restrictive.retry_after))
        
        return headers
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del rate limiter.
        
        Returns:
            Estadísticas de uso y límites
        """
        now = time.time()
        
        # Estadísticas de requests recientes
        recent_requests = [
            req for req in self.request_history
            if now - req.timestamp <= 3600  # Última hora
        ]
        
        # Contar por usuario
        user_counts = defaultdict(int)
        ip_counts = defaultdict(int)
        tool_counts = defaultdict(int)
        
        for req in recent_requests:
            if req.user_id:
                user_counts[req.user_id] += 1
            if req.client_ip:
                ip_counts[req.client_ip] += 1
            if req.tool_name:
                tool_counts[req.tool_name] += 1
        
        # Estados de contadores
        counter_states = {}
        for key, counter in self.counters.items():
            counter_states[key] = {
                "requests_in_window": len(counter.requests),
                "max_requests": counter.max_requests,
                "window_size": counter.window_size
            }
        
        # Estados de buckets
        bucket_states = {}
        for key, bucket in self.buckets.items():
            bucket_states[key] = bucket.get_status()
        
        return {
            "total_requests_last_hour": len(recent_requests),
            "unique_users_last_hour": len(user_counts),
            "unique_ips_last_hour": len(ip_counts),
            "top_users": dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_ips": dict(sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_tools": dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "counter_states": counter_states,
            "bucket_states": bucket_states,
            "active_limits": list(self.limits.keys())
        }
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Limpiar datos antiguos.
        
        Args:
            max_age_hours: Edad máxima de los datos en horas
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Limpiar historial de requests
        self.request_history = [
            req for req in self.request_history
            if req.timestamp > cutoff_time
        ]
        
        # Limpiar contadores inactivos (excepto los globales)
        inactive_keys = []
        for key in self.counters.keys():
            if key.startswith(("user_", "ip_")) and key not in ["user_per_minute", "ip_per_minute"]:
                counter = self.counters[key]
                if not counter.requests or max(counter.requests) < cutoff_time:
                    inactive_keys.append(key)
        
        for key in inactive_keys:
            del self.counters[key]
            if key in self.buckets:
                del self.buckets[key]
            if key in self.limits:
                del self.limits[key]
    
    async def reset_limits(self, pattern: Optional[str] = None):
        """Resetear límites que coincidan con un patrón.
        
        Args:
            pattern: Patrón para filtrar límites (opcional)
        """
        keys_to_reset = []
        
        if pattern:
            keys_to_reset = [key for key in self.counters.keys() if pattern in key]
        else:
            keys_to_reset = list(self.counters.keys())
        
        for key in keys_to_reset:
            if key in self.counters:
                # Recrear el contador
                limit = self.limits.get(key)
                if limit:
                    self.counters[key] = SlidingWindowCounter(
                        max_requests=limit.max_requests + limit.burst_allowance,
                        window_size=limit.period.value
                    )
            
            if key in self.buckets:
                # Recrear el bucket
                limit = self.limits.get(key)
                if limit and limit.burst_allowance > 0:
                    self.buckets[key] = TokenBucket(
                        capacity=limit.burst_allowance,
                        refill_rate=limit.burst_allowance / limit.period.value
                    )


# Instancia global del rate limiter
rate_limiter = RateLimiter()