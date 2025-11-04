#!/usr/bin/env python3
"""
PATCO AI Agent - Document Indexer Service
Servicio de indexación automática de documentos con embeddings vectoriales

Autor: PATCO Development Team
Versión: 1.0.0
Compatibilidad: Odoo Community 18 + PATCO Suite
"""

import asyncio
import logging
import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import Json, execute_values
import requests
import json
import hashlib
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentIndexer:
    """
    Servicio principal de indexación de documentos
    
    Funcionalidades:
    - Obtiene documentos pendientes desde Odoo
    - Procesa diferentes tipos de archivos (PDF, texto, imágenes)
    - Genera embeddings con Gemini API
    - Almacena vectores en PostgreSQL con PGVector
    """
    
    def __init__(self):
        """Inicializa el indexador con configuración desde variables de entorno"""
        
        # Configuración de base de datos
        self.db_url = os.getenv("DATABASE_URL", "postgresql://odoo:P4tc0_2@db:5432/odoo_patco")
        
        # Configuración de APIs
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        # Configuración de Odoo
        self.odoo_url = os.getenv("ODOO_URL", "http://odoo:8069")
        
        # Configuración de procesamiento
        self.batch_size = int(os.getenv("INDEXING_BATCH_SIZE", "50"))
        self.max_retries = 3
        self.retry_delay = 5  # segundos
        
        # Conexiones
        self.conn = None
        self.cursor = None
        
        logger.info("DocumentIndexer inicializado")
        logger.info(f"Base de datos: {self.db_url}")
        logger.info(f"Odoo URL: {self.odoo_url}")
        logger.info(f"Batch size: {self.batch_size}")
    
    async def connect_db(self):
        """Establece conexión con PostgreSQL"""
        
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.cursor = self.conn.cursor()
            
            # Verificar que PGVector esté disponible
            self.cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            if not self.cursor.fetchone():
                raise Exception("Extensión PGVector no encontrada en la base de datos")
            
            logger.info("Conexión a PostgreSQL establecida correctamente")
            
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise
    
    async def get_pending_documents(self) -> List[Dict]:
        """
        Obtiene documentos pendientes de indexación desde Odoo
        
        Returns:
            List[Dict]: Lista de documentos con metadatos
        """
        
        try:
            # Query para obtener attachments no indexados
            query = """
            SELECT 
                id, name, datas, mimetype, res_model, res_id,
                x_document_type, x_content_hash, x_equipment_category_ids,
                x_service_nature_ids, create_date
            FROM ir_attachment 
            WHERE 
                x_is_indexed = FALSE 
                AND datas IS NOT NULL
                AND mimetype IN ('application/pdf', 'text/plain', 'image/jpeg', 'image/png', 'text/html')
                AND x_indexing_error IS NULL
            ORDER BY create_date DESC
            LIMIT %s
            """
            
            self.cursor.execute(query, (self.batch_size,))
            columns = [desc[0] for desc in self.cursor.description]
            
            documents = []
            for row in self.cursor.fetchall():
                doc = dict(zip(columns, row))
                documents.append(doc)
            
            logger.info(f"Encontrados {len(documents)} documentos pendientes de indexación")
            return documents
            
        except Exception as e:
            logger.error(f"Error obteniendo documentos pendientes: {e}")
            return []
    
    async def process_document(self, document: Dict) -> List[Dict]:
        """
        Procesa un documento y genera chunks con embeddings
        
        Args:
            document: Diccionario con datos del documento
            
        Returns:
            List[Dict]: Lista de chunks con embeddings
        """
        
        try:
            logger.info(f"Procesando documento: {document['name']} (ID: {document['id']})")
            
            # Determinar procesador según tipo MIME
            processor = self._get_processor(document['mimetype'])
            
            # Extraer texto del documento
            text_chunks = await processor.extract_text(document)
            
            if not text_chunks:
                logger.warning(f"No se pudo extraer texto del documento {document['id']}")
                return []
            
            # Generar embeddings para cada chunk
            embeddings_data = []
            for i, chunk in enumerate(text_chunks):
                try:
                    # Validar contenido del chunk
                    if not chunk['content'].strip():
                        continue
                    
                    # Generar embedding
                    embedding = await self._generate_embedding(chunk['content'])
                    
                    embeddings_data.append({
                        'attachment_id': document['id'],
                        'chunk_index': i,
                        'content': chunk['content'][:2000],  # Limitar contenido
                        'embedding': embedding,
                        'metadata': {
                            'document_name': document['name'],
                            'document_type': document['x_document_type'],
                            'mimetype': document['mimetype'],
                            'chunk_length': len(chunk['content']),
                            'page_number': chunk.get('page_number'),
                            'processed_at': datetime.now().isoformat(),
                            'equipment_categories': document.get('x_equipment_category_ids'),
                            'service_natures': document.get('x_service_nature_ids')
                        }
                    })
                    
                    # Pequeña pausa para evitar rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error procesando chunk {i} del documento {document['id']}: {e}")
                    continue
            
            logger.info(f"Generados {len(embeddings_data)} embeddings para documento {document['id']}")
            return embeddings_data
            
        except Exception as e:
            logger.error(f"Error procesando documento {document['id']}: {e}")
            return []
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Genera embedding usando Gemini API
        
        Args:
            text: Texto para generar embedding
            
        Returns:
            List[float]: Vector embedding de 768 dimensiones
        """
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }
        
        data = {
            "model": "models/embedding-001",
            "content": {
                "parts": [{"text": text[:8000]}]  # Limitar texto para API
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                embedding = result['embedding']['values']
                
                # Validar dimensión del embedding
                if len(embedding) != 768:
                    raise ValueError(f"Embedding dimension mismatch: {len(embedding)} != 768")
                
                return embedding
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error en API Gemini (intento {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
            
            except Exception as e:
                logger.error(f"Error generando embedding: {e}")
                raise
    
    def _get_processor(self, mimetype: str):
        """
        Retorna el procesador apropiado según tipo MIME
        
        Args:
            mimetype: Tipo MIME del documento
            
        Returns:
            Procesador apropiado para el tipo de archivo
        """
        
        if mimetype == 'application/pdf':
            from processors.pdf_processor import PDFProcessor
            return PDFProcessor()
        elif mimetype in ['text/plain', 'text/html']:
            from processors.text_processor import TextProcessor
            return TextProcessor()
        elif mimetype in ['image/jpeg', 'image/png']:
            from processors.image_processor import ImageProcessor
            return ImageProcessor()
        else:
            raise ValueError(f"Tipo MIME no soportado: {mimetype}")
    
    async def save_embeddings(self, embeddings_data: List[Dict]):
        """
        Guarda embeddings en PostgreSQL usando PGVector
        
        Args:
            embeddings_data: Lista de embeddings a guardar
        """
        
        if not embeddings_data:
            return
        
        try:
            # Preparar datos para inserción batch
            insert_query = """
            INSERT INTO ai_document_embeddings 
            (attachment_id, chunk_index, content, embedding, metadata, created_at, updated_at)
            VALUES %s
            """
            
            values = []
            for data in embeddings_data:
                values.append((
                    data['attachment_id'],
                    data['chunk_index'],
                    data['content'],
                    data['embedding'],
                    Json(data['metadata']),
                    datetime.now(),
                    datetime.now()
                ))
            
            # Inserción batch usando execute_values
            execute_values(
                self.cursor,
                insert_query,
                values,
                template=None,
                page_size=100
            )
            
            # Marcar documento como indexado en Odoo
            attachment_ids = list(set(data['attachment_id'] for data in embeddings_data))
            update_query = """
            UPDATE ir_attachment 
            SET x_is_indexed = TRUE, x_indexed_date = %s
            WHERE id = ANY(%s)
            """
            
            self.cursor.execute(update_query, (datetime.now(), attachment_ids))
            self.conn.commit()
            
            logger.info(f"Guardados {len(embeddings_data)} embeddings para {len(attachment_ids)} documentos")
            
        except Exception as e:
            logger.error(f"Error guardando embeddings: {e}")
            self.conn.rollback()
            raise
    
    async def mark_document_error(self, document_id: int, error_message: str):
        """
        Marca un documento con error de indexación
        
        Args:
            document_id: ID del documento
            error_message: Mensaje de error
        """
        
        try:
            self.cursor.execute("""
                UPDATE ir_attachment 
                SET x_indexing_error = %s
                WHERE id = %s
            """, (error_message, document_id))
            self.conn.commit()
            
            logger.warning(f"Documento {document_id} marcado con error: {error_message}")
            
        except Exception as e:
            logger.error(f"Error marcando documento con error: {e}")
    
    async def run_indexing_cycle(self):
        """Ejecuta un ciclo completo de indexación"""
        
        cycle_start = time.time()
        
        try:
            await self.connect_db()
            
            # Obtener documentos pendientes
            documents = await self.get_pending_documents()
            
            if not documents:
                logger.info("No hay documentos pendientes de indexación")
                return
            
            # Procesar cada documento
            total_embeddings = 0
            successful_docs = 0
            failed_docs = 0
            
            for document in documents:
                try:
                    embeddings_data = await self.process_document(document)
                    
                    if embeddings_data:
                        await self.save_embeddings(embeddings_data)
                        total_embeddings += len(embeddings_data)
                        successful_docs += 1
                    else:
                        await self.mark_document_error(
                            document['id'], 
                            "No se pudo extraer contenido indexable"
                        )
                        failed_docs += 1
                        
                except Exception as e:
                    logger.error(f"Error procesando documento {document['id']}: {e}")
                    await self.mark_document_error(document['id'], str(e))
                    failed_docs += 1
            
            cycle_time = time.time() - cycle_start
            
            logger.info(f"Ciclo de indexación completado en {cycle_time:.2f}s:")
            logger.info(f"  - Documentos procesados exitosamente: {successful_docs}")
            logger.info(f"  - Documentos con errores: {failed_docs}")
            logger.info(f"  - Total embeddings generados: {total_embeddings}")
            
        except Exception as e:
            logger.error(f"Error en ciclo de indexación: {e}")
            if hasattr(self, 'conn') and self.conn:
                self.conn.rollback()
        
        finally:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()

async def main():
    """Función principal del indexador"""
    
    logger.info("=== PATCO AI Agent - Document Indexer ===")
    logger.info("Iniciando servicio de indexación de documentos...")
    
    indexer = DocumentIndexer()
    
    # Modo watch: ejecutar continuamente
    if "--watch" in sys.argv:
        logger.info("Iniciando indexador en modo watch (continuo)...")
        
        cycle_interval = int(os.getenv("INDEXING_CYCLE_INTERVAL", "300"))  # 5 minutos por defecto
        
        while True:
            try:
                await indexer.run_indexing_cycle()
                logger.info(f"Esperando {cycle_interval} segundos hasta el próximo ciclo...")
                await asyncio.sleep(cycle_interval)
                
            except KeyboardInterrupt:
                logger.info("Deteniendo indexador por interrupción del usuario")
                break
            except Exception as e:
                logger.error(f"Error inesperado en modo watch: {e}")
                logger.info("Reintentando en 60 segundos...")
                await asyncio.sleep(60)
    
    # Modo single: ejecutar una vez
    else:
        logger.info("Ejecutando ciclo único de indexación...")
        await indexer.run_indexing_cycle()
        logger.info("Indexación completada")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Indexador detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal en indexador: {e}")
        sys.exit(1)