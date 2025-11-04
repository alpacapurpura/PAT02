#!/usr/bin/env python3
"""
Cliente para comunicación con PostgreSQL y PGVector
Maneja conexiones, consultas y operaciones de embeddings
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import json

import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector

logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Excepción para errores de conexión a la base de datos"""
    pass

class DatabaseQueryError(Exception):
    """Excepción para errores de consulta a la base de datos"""
    pass

class DatabaseClient:
    """Cliente asíncrono para PostgreSQL con soporte PGVector"""
    
    def __init__(
        self, 
        database_url: str,
        min_connections: int = 5,
        max_connections: int = 20,
        command_timeout: int = 30
    ):
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.command_timeout = command_timeout
        
        # Pool de conexiones
        self.pool = None
        self.is_connected = False
        
        logger.info(f"Cliente de base de datos inicializado")
    
    async def connect(self) -> bool:
        """Establecer pool de conexiones"""
        try:
            logger.info("Conectando a PostgreSQL...")
            
            # Crear pool de conexiones
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=self.command_timeout,
                init=self._init_connection
            )
            
            # Verificar conexión
            async with self.pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                logger.info(f"Conectado a: {version}")
                
                # Verificar PGVector
                try:
                    await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                    logger.info("✅ Extensión PGVector disponible")
                except Exception:
                    logger.warning("⚠️ Extensión PGVector no encontrada")
            
            self.is_connected = True
            logger.info("✅ Pool de conexiones establecido")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            self.is_connected = False
            raise DatabaseConnectionError(f"Error de conexión: {str(e)}")
    
    async def _init_connection(self, conn):
        """Inicializar conexión individual"""
        # Registrar tipo vector para PGVector
        await register_vector(conn)
        
        # Configurar timezone
        await conn.execute("SET timezone = 'UTC'")
    
    async def disconnect(self):
        """Cerrar pool de conexiones"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self.is_connected = False
            logger.info("Pool de conexiones cerrado")
    
    async def execute(
        self, 
        query: str, 
        *args, 
        fetch: bool = False,
        fetch_one: bool = False
    ) -> Optional[Union[List[Dict], Dict, Any]]:
        """Ejecutar consulta SQL"""
        if not self.is_connected:
            raise DatabaseConnectionError("No hay conexión a la base de datos")
        
        try:
            async with self.pool.acquire() as conn:
                logger.debug(f"Ejecutando: {query[:100]}...")
                
                if fetch_one:
                    result = await conn.fetchrow(query, *args)
                    return dict(result) if result else None
                elif fetch:
                    rows = await conn.fetch(query, *args)
                    return [dict(row) for row in rows]
                else:
                    return await conn.execute(query, *args)
                    
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            raise DatabaseQueryError(f"Error en consulta: {str(e)}")
    
    async def search_embeddings(
        self, 
        query_embedding: List[float],
        table: str = "ai_document_embeddings",
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Buscar documentos similares usando embeddings"""
        try:
            # Construir consulta base
            base_query = f"""
                SELECT 
                    id,
                    document_id,
                    chunk_text,
                    chunk_index,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {table}
                WHERE 1 - (embedding <=> $1::vector) > $2
            """
            
            params = [query_embedding, similarity_threshold]
            param_count = 2
            
            # Agregar filtros si se proporcionan
            if filters:
                for key, value in filters.items():
                    param_count += 1
                    if key == 'document_types':
                        base_query += f" AND metadata->>'document_type' = ANY(${param_count})"
                        params.append(value)
                    elif key == 'equipment_category_ids':
                        base_query += f" AND (metadata->>'equipment_category_id')::int = ANY(${param_count})"
                        params.append(value)
                    elif key == 'created_after':
                        base_query += f" AND created_at > ${param_count}"
                        params.append(value)
                    else:
                        base_query += f" AND metadata->>'{key}' = ${param_count}"
                        params.append(str(value))
            
            # Ordenar y limitar
            base_query += f"""
                ORDER BY similarity DESC
                LIMIT ${param_count + 1}
            """
            params.append(max_results)
            
            results = await self.execute(base_query, *params, fetch=True)
            
            logger.info(f"Encontrados {len(results)} documentos similares")
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda de embeddings: {e}")
            raise DatabaseQueryError(f"Error en búsqueda semántica: {str(e)}")
    
    async def insert_embedding(
        self, 
        document_id: int,
        chunk_text: str,
        chunk_index: int,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        table: str = "ai_document_embeddings"
    ) -> int:
        """Insertar embedding en la base de datos"""
        try:
            query = f"""
                INSERT INTO {table} (
                    document_id, chunk_text, chunk_index, 
                    embedding, metadata, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
            
            result = await self.execute(
                query,
                document_id,
                chunk_text,
                chunk_index,
                embedding,
                json.dumps(metadata or {}),
                datetime.utcnow(),
                fetch_one=True
            )
            
            embedding_id = result['id']
            logger.debug(f"Embedding insertado con ID: {embedding_id}")
            return embedding_id
            
        except Exception as e:
            logger.error(f"Error insertando embedding: {e}")
            raise DatabaseQueryError(f"Error insertando embedding: {str(e)}")
    
    async def get_document_embeddings(
        self, 
        document_id: int,
        table: str = "ai_document_embeddings"
    ) -> List[Dict[str, Any]]:
        """Obtener todos los embeddings de un documento"""
        try:
            query = f"""
                SELECT id, chunk_text, chunk_index, metadata, created_at
                FROM {table}
                WHERE document_id = $1
                ORDER BY chunk_index
            """
            
            results = await self.execute(query, document_id, fetch=True)
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo embeddings del documento {document_id}: {e}")
            raise DatabaseQueryError(f"Error obteniendo embeddings: {str(e)}")
    
    async def delete_document_embeddings(
        self, 
        document_id: int,
        table: str = "ai_document_embeddings"
    ) -> int:
        """Eliminar todos los embeddings de un documento"""
        try:
            query = f"DELETE FROM {table} WHERE document_id = $1"
            result = await self.execute(query, document_id)
            
            # Extraer número de filas afectadas
            deleted_count = int(result.split()[-1]) if result else 0
            logger.info(f"Eliminados {deleted_count} embeddings del documento {document_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error eliminando embeddings del documento {document_id}: {e}")
            raise DatabaseQueryError(f"Error eliminando embeddings: {str(e)}")
    
    async def get_embedding_stats(
        self, 
        table: str = "ai_document_embeddings"
    ) -> Dict[str, Any]:
        """Obtener estadísticas de embeddings"""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_embeddings,
                    COUNT(DISTINCT document_id) as unique_documents,
                    AVG(LENGTH(chunk_text)) as avg_chunk_length,
                    MIN(created_at) as oldest_embedding,
                    MAX(created_at) as newest_embedding
                FROM {table}
            """
            
            result = await self.execute(query, fetch_one=True)
            return result or {}
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    async def create_embedding_index(
        self, 
        table: str = "ai_document_embeddings",
        index_type: str = "ivfflat",
        lists: int = 100
    ) -> bool:
        """Crear índice para búsquedas de embeddings"""
        try:
            index_name = f"idx_{table}_embedding_{index_type}"
            
            if index_type == "ivfflat":
                query = f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table} 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {lists})
                """
            elif index_type == "hnsw":
                query = f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table} 
                    USING hnsw (embedding vector_cosine_ops)
                """
            else:
                raise ValueError(f"Tipo de índice no soportado: {index_type}")
            
            await self.execute(query)
            logger.info(f"✅ Índice {index_name} creado")
            return True
            
        except Exception as e:
            logger.error(f"Error creando índice: {e}")
            return False
    
    async def vacuum_analyze(
        self, 
        table: str = "ai_document_embeddings"
    ) -> bool:
        """Optimizar tabla de embeddings"""
        try:
            await self.execute(f"VACUUM ANALYZE {table}")
            logger.info(f"✅ Tabla {table} optimizada")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizando tabla: {e}")
            return False
    
    async def check_table_exists(
        self, 
        table_name: str, 
        schema: str = "public"
    ) -> bool:
        """Verificar si una tabla existe"""
        try:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = $1 AND table_name = $2
                )
            """
            
            result = await self.execute(query, schema, table_name, fetch_one=True)
            return result['exists'] if result else False
            
        except Exception as e:
            logger.error(f"Error verificando tabla {table_name}: {e}")
            return False
    
    async def get_table_info(
        self, 
        table_name: str, 
        schema: str = "public"
    ) -> Dict[str, Any]:
        """Obtener información de una tabla"""
        try:
            # Información básica de la tabla
            table_query = """
                SELECT 
                    schemaname,
                    tablename,
                    tableowner,
                    hasindexes,
                    hasrules,
                    hastriggers
                FROM pg_tables 
                WHERE schemaname = $1 AND tablename = $2
            """
            
            table_info = await self.execute(table_query, schema, table_name, fetch_one=True)
            
            if not table_info:
                return {}
            
            # Información de columnas
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
            """
            
            columns = await self.execute(columns_query, schema, table_name, fetch=True)
            
            # Estadísticas de la tabla
            stats_query = f"""
                SELECT 
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = $1 AND relname = $2
            """
            
            stats = await self.execute(stats_query, schema, table_name, fetch_one=True)
            
            return {
                'table': table_info,
                'columns': columns,
                'statistics': stats or {}
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información de tabla {table_name}: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud de la conexión"""
        try:
            start_time = datetime.utcnow()
            
            # Consulta simple
            result = await self.execute("SELECT 1 as test", fetch_one=True)
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Información del pool
            pool_info = {
                'size': self.pool.get_size(),
                'min_size': self.pool.get_min_size(),
                'max_size': self.pool.get_max_size(),
                'idle_connections': self.pool.get_idle_size()
            }
            
            return {
                'status': 'healthy',
                'connected': self.is_connected,
                'response_time_ms': response_time,
                'pool': pool_info,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def __str__(self) -> str:
        return f"DatabaseClient(connected={self.is_connected})"
    
    def __repr__(self) -> str:
        return (
            f"DatabaseClient(connected={self.is_connected}, "
            f"pool_size={self.pool.get_size() if self.pool else 0})"
        )

# Funciones de utilidad

async def test_database_connection(database_url: str) -> Dict[str, Any]:
    """Probar conexión a la base de datos"""
    client = DatabaseClient(database_url)
    
    try:
        await client.connect()
        health = await client.health_check()
        
        # Verificar tabla de embeddings
        embeddings_table_exists = await client.check_table_exists('ai_document_embeddings')
        
        result = {
            'success': True,
            'health': health,
            'embeddings_table_exists': embeddings_table_exists
        }
        
        if embeddings_table_exists:
            stats = await client.get_embedding_stats()
            result['embedding_stats'] = stats
        
        await client.disconnect()
        return result
        
    except Exception as e:
        await client.disconnect()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio
    
    async def main():
        client = DatabaseClient("postgresql://odoo:odoo@localhost:5432/odoo_patco")
        
        try:
            await client.connect()
            print("✅ Conectado a PostgreSQL")
            
            # Health check
            health = await client.health_check()
            print(f"Estado: {health['status']}")
            
            # Verificar tabla de embeddings
            exists = await client.check_table_exists('ai_document_embeddings')
            print(f"Tabla embeddings existe: {exists}")
            
            if exists:
                stats = await client.get_embedding_stats()
                print(f"Estadísticas: {stats}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.disconnect()
    
    asyncio.run(main())