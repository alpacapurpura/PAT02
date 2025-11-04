#!/usr/bin/env python3
"""
Herramientas de Base de Conocimiento (Knowledge Base / RAG)
Implementación de herramientas para búsqueda semántica y gestión de documentos
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, date
import json
import re

from schemas.knowledge import (
    KnowledgeDocument, DocumentType, DocumentStatus, KnowledgeChunk,
    SearchType, RelevanceLevel, SearchResult,
    KnowledgeSearchRequest, KnowledgeSearchResponse,
    DocumentRequest, DocumentResponse,
    DocumentListRequest, DocumentListResponse,
    SimilarDocumentsRequest, SimilarDocumentsResponse,
    # create_knowledge_document_from_odoo_data,  # TODO: Implementar esta función
    # validate_document_status_transition,  # TODO: Implementar esta función
    # calculate_document_metrics,  # TODO: Implementar esta función
    determine_relevance_level,
    extract_keywords_from_query
)
from schemas.base import ErrorResponse, ErrorTypeEnum, create_error_response, create_success_response
from utils.odoo_client import OdooClient
from utils.db_client import DatabaseClient
from config import get_settings

_logger = logging.getLogger(__name__)
settings = get_settings()

class KnowledgeToolsManager:
    """Manager para herramientas de base de conocimiento"""
    
    def __init__(self, odoo_client: OdooClient, db_client: DatabaseClient):
        self.odoo_client = odoo_client
        self.db_client = db_client
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Configuración de embeddings
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embedding_dimension = settings.PGVECTOR_DIMENSION
        self.similarity_threshold = settings.PGVECTOR_SIMILARITY_THRESHOLD
        self.max_results = settings.PGVECTOR_MAX_RESULTS
    
    async def search_knowledge_base(self, request: KnowledgeSearchRequest) -> Union[KnowledgeSearchResponse, ErrorResponse]:
        """Buscar en la base de conocimiento usando embeddings y búsqueda semántica"""
        try:
            self._logger.info(f"Buscando en base de conocimiento: '{request.query}'")
            
            # Verificar que el cliente de base de datos esté disponible
            if not await self.db_client.health_check():
                return create_error_response(
                    ErrorTypeEnum.DATABASE_ERROR,
                    "database_unavailable",
                    "Base de datos no disponible"
                )
            search_results = []
            total_results = 0
            
            # Realizar búsqueda según el tipo
            if request.search_type == SearchType.SEMANTIC:
                # Búsqueda semántica usando embeddings
                results = await self._semantic_search(
                    query=request.query,
                    limit=request.limit,
                    threshold=request.similarity_threshold or self.similarity_threshold,
                    document_types=request.document_types,
                    date_from=request.date_from,
                    date_to=request.date_to,
                    include_metadata=request.include_metadata
                )
                search_results = results
                total_results = len(results)
                
            elif request.search_type == SearchType.KEYWORD:
                # Búsqueda por palabras clave
                results = await self._keyword_search(
                    query=request.query,
                    limit=request.limit,
                    document_types=request.document_types,
                    date_from=request.date_from,
                    date_to=request.date_to,
                    include_metadata=request.include_metadata
                )
                search_results = results
                total_results = len(results)
                
            elif request.search_type == SearchType.HYBRID:
                # Búsqueda híbrida (semántica + palabras clave)
                semantic_results = await self._semantic_search(
                    query=request.query,
                    limit=request.limit // 2,
                    threshold=request.similarity_threshold or self.similarity_threshold,
                    document_types=request.document_types,
                    date_from=request.date_from,
                    date_to=request.date_to,
                    include_metadata=request.include_metadata
                )
                
                keyword_results = await self._keyword_search(
                    query=request.query,
                    limit=request.limit // 2,
                    document_types=request.document_types,
                    date_from=request.date_from,
                    date_to=request.date_to,
                    include_metadata=request.include_metadata
                )
                
                # Combinar y deduplicar resultados
                search_results = self._merge_search_results(
                    semantic_results, keyword_results, request.limit
                )
                total_results = len(search_results)
            
            # Crear resumen de búsqueda
            summary = create_search_summary(
                query=request.query,
                total_results=total_results,
                search_type=request.search_type,
                keywords=extract_keywords(request.query)
            )
            
            return KnowledgeSearchResponse(
                results=search_results,
                summary=summary,
                total_results=total_results,
                search_type=request.search_type,
                message=f"Se encontraron {total_results} resultados para '{request.query}'"
            )
            
        except Exception as e:
            self._logger.error(f"Error en búsqueda de conocimiento: {str(e)}")
            return create_error_response(
                "search_error",
                f"Error en búsqueda: {str(e)}"
            )
    
    async def _semantic_search(
        self,
        query: str,
        limit: int,
        threshold: float,
        document_types: Optional[List[DocumentType]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_metadata: bool = False
    ) -> List[SearchResult]:
        """Realizar búsqueda semántica usando embeddings"""
        try:
            # Generar embedding para la consulta
            query_embedding = await self._generate_embedding(query)
            
            if not query_embedding:
                self._logger.warning("No se pudo generar embedding para la consulta")
                return []
            
            # Construir filtros adicionales
            filters = {}
            if document_types:
                filters['document_type'] = [dt.value for dt in document_types]
            if date_from:
                filters['date_from'] = date_from
            if date_to:
                filters['date_to'] = date_to
            
            # Buscar embeddings similares
            similar_chunks = await self.db_client.search_similar_embeddings(
                query_embedding=query_embedding,
                limit=limit,
                threshold=threshold,
                filters=filters
            )
            
            # Convertir a SearchResult
            search_results = []
            for chunk_data in similar_chunks:
                try:
                    # Obtener información del documento desde Odoo si es necesario
                    document_info = None
                    if include_metadata and chunk_data.get('document_id'):
                        document_info = await self._get_document_info(chunk_data['document_id'])
                    
                    # Crear SearchResult
                    search_result = create_search_result(
                        chunk_id=chunk_data.get('id'),
                        document_id=chunk_data.get('document_id'),
                        title=chunk_data.get('title', 'Sin título'),
                        content=chunk_data.get('content', ''),
                        similarity_score=chunk_data.get('similarity', 0.0),
                        document_type=DocumentType(chunk_data.get('document_type', 'other')),
                        metadata=document_info if include_metadata else None
                    )
                    
                    search_results.append(search_result)
                    
                except Exception as e:
                    self._logger.warning(f"Error procesando chunk {chunk_data.get('id')}: {str(e)}")
                    continue
            
            return search_results
            
        except Exception as e:
            self._logger.error(f"Error en búsqueda semántica: {str(e)}")
            return []
    
    async def _keyword_search(
        self,
        query: str,
        limit: int,
        document_types: Optional[List[DocumentType]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_metadata: bool = False
    ) -> List[SearchResult]:
        """Realizar búsqueda por palabras clave"""
        try:
            # Extraer palabras clave de la consulta
            keywords = extract_keywords(query)
            
            if not keywords:
                return []
            
            # Construir filtros
            filters = build_document_filters(
                document_types=document_types,
                date_from=date_from,
                date_to=date_to
            )
            
            # Buscar en la base de datos usando texto completo
            keyword_results = await self.db_client.search_by_keywords(
                keywords=keywords,
                limit=limit,
                filters=filters
            )
            
            # Convertir a SearchResult
            search_results = []
            for result_data in keyword_results:
                try:
                    # Obtener información del documento si es necesario
                    document_info = None
                    if include_metadata and result_data.get('document_id'):
                        document_info = await self._get_document_info(result_data['document_id'])
                    
                    # Calcular score basado en coincidencias de palabras clave
                    keyword_score = self._calculate_keyword_score(
                        content=result_data.get('content', ''),
                        keywords=keywords
                    )
                    
                    # Crear SearchResult
                    search_result = create_search_result(
                        chunk_id=result_data.get('id'),
                        document_id=result_data.get('document_id'),
                        title=result_data.get('title', 'Sin título'),
                        content=result_data.get('content', ''),
                        similarity_score=keyword_score,
                        document_type=DocumentType(result_data.get('document_type', 'other')),
                        metadata=document_info if include_metadata else None
                    )
                    
                    search_results.append(search_result)
                    
                except Exception as e:
                    self._logger.warning(f"Error procesando resultado: {str(e)}")
                    continue
            
            # Ordenar por score descendente
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return search_results
            
        except Exception as e:
            self._logger.error(f"Error en búsqueda por palabras clave: {str(e)}")
            return []
    
    def _merge_search_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        limit: int
    ) -> List[SearchResult]:
        """Combinar y deduplicar resultados de búsqueda semántica y por palabras clave"""
        try:
            # Crear diccionario para deduplicar por chunk_id
            merged_results = {}
            
            # Agregar resultados semánticos con peso mayor
            for result in semantic_results:
                if result.chunk_id:
                    # Dar mayor peso a resultados semánticos
                    result.similarity_score *= 1.2
                    merged_results[result.chunk_id] = result
            
            # Agregar resultados de palabras clave
            for result in keyword_results:
                if result.chunk_id:
                    if result.chunk_id in merged_results:
                        # Si ya existe, combinar scores
                        existing = merged_results[result.chunk_id]
                        combined_score = (existing.similarity_score + result.similarity_score) / 2
                        existing.similarity_score = combined_score
                    else:
                        merged_results[result.chunk_id] = result
            
            # Convertir a lista y ordenar por score
            final_results = list(merged_results.values())
            final_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Limitar resultados
            return final_results[:limit]
            
        except Exception as e:
            self._logger.error(f"Error combinando resultados: {str(e)}")
            return semantic_results + keyword_results
    
    def _calculate_keyword_score(self, content: str, keywords: List[str]) -> float:
        """Calcular score basado en coincidencias de palabras clave"""
        try:
            if not content or not keywords:
                return 0.0
            
            content_lower = content.lower()
            total_matches = 0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                matches = len(re.findall(re.escape(keyword_lower), content_lower))
                total_matches += matches
            
            # Normalizar score (0.0 - 1.0)
            max_possible_matches = len(keywords) * 3  # Asumiendo máximo 3 coincidencias por palabra
            score = min(total_matches / max_possible_matches, 1.0) if max_possible_matches > 0 else 0.0
            
            return score
            
        except Exception as e:
            self._logger.error(f"Error calculando keyword score: {str(e)}")
            return 0.0
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generar embedding para un texto"""
        try:
            # Aquí se implementaría la generación de embeddings
            # Por ahora, retornamos None para indicar que no está implementado
            # En una implementación real, se usaría un modelo como OpenAI, Sentence Transformers, etc.
            
            self._logger.warning("Generación de embeddings no implementada")
            return None
            
        except Exception as e:
            self._logger.error(f"Error generando embedding: {str(e)}")
            return None
    
    async def _get_document_info(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Obtener información de un documento desde Odoo"""
        try:
            if not self.odoo_client.is_authenticated():
                return None
            
            # Buscar en diferentes modelos de Odoo que podrían contener documentos
            models_to_search = [
                'ir.attachment',
                'knowledge.article',
                'documents.document',
                'mail.message'
            ]
            
            for model in models_to_search:
                try:
                    document_data = await self.odoo_client.search_read(
                        model,
                        domain=[('id', '=', document_id)],
                        fields=['id', 'name', 'create_date', 'write_date', 'create_uid'],
                        limit=1
                    )
                    
                    if document_data:
                        return {
                            'model': model,
                            'data': document_data[0]
                        }
                        
                except Exception:
                    # Continuar con el siguiente modelo si este falla
                    continue
            
            return None
            
        except Exception as e:
            self._logger.error(f"Error obteniendo documento {request.document_id}: {str(e)}")
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    async def get_document(self, request: DocumentRequest) -> Union[DocumentResponse, ErrorResponse]:
        """Obtener un documento específico"""
        try:
            self._logger.info(f"Obteniendo documento {request.document_id}")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    ErrorTypeEnum.AUTHENTICATION_ERROR,
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Buscar el documento en Odoo
            document_data = await self.odoo_client.search_read(
                'ir.attachment',
                domain=[('id', '=', request.document_id)],
                fields=[
                    'id', 'name', 'description', 'mimetype', 'file_size',
                    'create_date', 'write_date', 'create_uid', 'res_model',
                    'res_id', 'url', 'type', 'datas_fname'
                ],
                limit=1
            )
            
            if not document_data:
                return create_error_response(
                    "not_found",
                    f"Documento {request.document_id} no encontrado"
                )
            
            doc_info = document_data[0]
            
            # Obtener chunks del documento si se solicita
            chunks = []
            if request.include_chunks:
                chunk_data = await self.db_client.get_document_chunks(request.document_id)
                
                for chunk in chunk_data:
                    try:
                        knowledge_chunk = KnowledgeChunk(
                            id=chunk.get('id'),
                            document_id=chunk.get('document_id'),
                            content=chunk.get('content', ''),
                            chunk_index=chunk.get('chunk_index', 0),
                            start_char=chunk.get('start_char', 0),
                            end_char=chunk.get('end_char', 0),
                            metadata=chunk.get('metadata', {})
                        )
                        chunks.append(knowledge_chunk)
                    except Exception as e:
                        self._logger.warning(f"Error procesando chunk: {str(e)}")
                        continue
            
            # Crear objeto KnowledgeDocument
            document = KnowledgeDocument(
                id=doc_info['id'],
                title=doc_info['name'] or 'Sin título',
                content='',  # El contenido completo no se almacena en ir.attachment
                document_type=DocumentType.OTHER,  # Determinar tipo basado en mimetype
                state=DocumentState.ACTIVE,
                created_at=datetime.fromisoformat(doc_info['create_date'].replace('Z', '+00:00')) if doc_info['create_date'] else datetime.now(),
                updated_at=datetime.fromisoformat(doc_info['write_date'].replace('Z', '+00:00')) if doc_info['write_date'] else datetime.now(),
                author_id=doc_info['create_uid'][0] if doc_info['create_uid'] else None,
                file_size=doc_info.get('file_size', 0),
                mime_type=doc_info.get('mimetype', ''),
                url=doc_info.get('url', ''),
                metadata={
                    'res_model': doc_info.get('res_model', ''),
                    'res_id': doc_info.get('res_id', 0),
                    'datas_fname': doc_info.get('datas_fname', '')
                },
                chunks=chunks if request.include_chunks else []
            )
            
            return DocumentResponse(
                document=document,
                message=f"Documento {request.document_id} obtenido exitosamente"
            )
            
        except Exception as e:
            self._logger.error(f"Error obteniendo documento {request.document_id}: {str(e)}")
            return create_error_response(
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    async def list_documents(self, request: DocumentListRequest) -> Union[DocumentListResponse, ErrorResponse]:
        """Listar documentos con filtros"""
        try:
            self._logger.info("Listando documentos")
            
            # Verificar que el cliente Odoo esté autenticado
            if not self.odoo_client.is_authenticated():
                return create_error_response(
                    ErrorTypeEnum.AUTHENTICATION_ERROR,
                    "authentication_required",
                    "Cliente Odoo no autenticado"
                )
            
            # Construir dominio de búsqueda
            domain = []
            
            # Filtros por tipo de documento
            if request.document_types:
                # Mapear tipos a mimetypes (simplificado)
                mimetype_filters = []
                for doc_type in request.document_types:
                    if doc_type == DocumentType.PDF:
                        mimetype_filters.append(('mimetype', '=', 'application/pdf'))
                    elif doc_type == DocumentType.TEXT:
                        mimetype_filters.append(('mimetype', 'in', ['text/plain', 'text/html']))
                    elif doc_type == DocumentType.WORD:
                        mimetype_filters.append(('mimetype', 'in', ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']))
                
                if mimetype_filters:
                    domain.extend(['|'] * (len(mimetype_filters) - 1))
                    domain.extend(mimetype_filters)
            
            # Filtros por fecha
            if request.date_from:
                domain.append(('create_date', '>=', request.date_from.isoformat()))
            
            if request.date_to:
                domain.append(('create_date', '<=', request.date_to.isoformat()))
            
            # Filtro por autor
            if request.author_ids:
                domain.append(('create_uid', 'in', request.author_ids))
            
            # Filtro de búsqueda de texto
            if request.search_text:
                domain.append('|')
                domain.append(('name', 'ilike', request.search_text))
                domain.append(('description', 'ilike', request.search_text))
            
            # Campos a obtener
            fields = [
                'id', 'name', 'description', 'mimetype', 'file_size',
                'create_date', 'write_date', 'create_uid', 'res_model',
                'res_id', 'type'
            ]
            
            # Realizar búsqueda
            documents_data = await self.odoo_client.search_read(
                'ir.attachment',
                domain=domain,
                fields=fields,
                order=request.order_by or 'create_date desc',
                limit=request.limit,
                offset=request.offset
            )
            
            # Obtener conteo total
            total_count = await self.odoo_client.search_count(
                'ir.attachment',
                domain=domain
            )
            
            # Convertir a objetos KnowledgeDocument
            documents = []
            for doc_data in documents_data:
                try:
                    document = KnowledgeDocument(
                        id=doc_data['id'],
                        title=doc_data['name'] or 'Sin título',
                        content='',  # No incluir contenido completo en listado
                        document_type=self._determine_document_type(doc_data.get('mimetype', '')),
                        state=DocumentState.ACTIVE,
                        created_at=datetime.fromisoformat(doc_data['create_date'].replace('Z', '+00:00')) if doc_data['create_date'] else datetime.now(),
                        updated_at=datetime.fromisoformat(doc_data['write_date'].replace('Z', '+00:00')) if doc_data['write_date'] else datetime.now(),
                        author_id=doc_data['create_uid'][0] if doc_data['create_uid'] else None,
                        file_size=doc_data.get('file_size', 0),
                        mime_type=doc_data.get('mimetype', ''),
                        metadata={
                            'res_model': doc_data.get('res_model', ''),
                            'res_id': doc_data.get('res_id', 0),
                            'description': doc_data.get('description', '')
                        }
                    )
                    documents.append(document)
                except Exception as e:
                    self._logger.warning(f"Error procesando documento {doc_data.get('id')}: {str(e)}")
                    continue
            
            return DocumentListResponse(
                documents=documents,
                total_count=total_count,
                offset=request.offset,
                limit=request.limit,
                message=f"Se encontraron {len(documents)} documentos"
            )
            
        except Exception as e:
            self._logger.error(f"Error listando documentos: {str(e)}")
            return create_error_response(
                "internal_error",
                f"Error interno: {str(e)}"
            )
    
    def _determine_document_type(self, mimetype: str) -> DocumentType:
        """Determinar el tipo de documento basado en el mimetype"""
        if not mimetype:
            return DocumentType.OTHER
        
        mimetype_lower = mimetype.lower()
        
        if 'pdf' in mimetype_lower:
            return DocumentType.PDF
        elif 'text' in mimetype_lower or 'html' in mimetype_lower:
            return DocumentType.TEXT
        elif 'word' in mimetype_lower or 'msword' in mimetype_lower:
            return DocumentType.WORD
        elif 'excel' in mimetype_lower or 'spreadsheet' in mimetype_lower:
            return DocumentType.SPREADSHEET
        elif 'powerpoint' in mimetype_lower or 'presentation' in mimetype_lower:
            return DocumentType.PRESENTATION
        elif 'image' in mimetype_lower:
            return DocumentType.IMAGE
        else:
            return DocumentType.OTHER
    
    async def search_similar_documents(self, request: SimilarDocumentsRequest) -> Union[SimilarDocumentsResponse, ErrorResponse]:
        """Buscar documentos similares a uno dado"""
        try:
            self._logger.info(f"Buscando documentos similares a {request.document_id}")
            
            # Verificar que la base de datos esté disponible
            if not await self.db_client.health_check():
                return create_error_response(
                    "database_unavailable",
                    "Base de datos no disponible"
                )
            
            # Obtener el embedding del documento de referencia
            reference_embedding = await self.db_client.get_document_embedding(request.document_id)
            
            if not reference_embedding:
                return create_error_response(
                    "no_embedding",
                    f"No se encontró embedding para el documento {request.document_id}"
                )
            
            # Buscar documentos similares
            similar_docs = await self.db_client.search_similar_embeddings(
                query_embedding=reference_embedding,
                limit=request.limit + 1,  # +1 para excluir el documento original
                threshold=request.similarity_threshold or self.similarity_threshold,
                filters={
                    'exclude_document_id': request.document_id
                }
            )
            
            # Convertir a SearchResult
            search_results = []
            for doc_data in similar_docs:
                if doc_data.get('document_id') == request.document_id:
                    continue  # Excluir el documento original
                
                try:
                    # Obtener información del documento si se solicita
                    document_info = None
                    if request.include_metadata and doc_data.get('document_id'):
                        document_info = await self._get_document_info(doc_data['document_id'])
                    
                    search_result = create_search_result(
                        chunk_id=doc_data.get('id'),
                        document_id=doc_data.get('document_id'),
                        title=doc_data.get('title', 'Sin título'),
                        content=doc_data.get('content', ''),
                        similarity_score=doc_data.get('similarity', 0.0),
                        document_type=DocumentType(doc_data.get('document_type', 'other')),
                        metadata=document_info if request.include_metadata else None
                    )
                    
                    search_results.append(search_result)
                    
                except Exception as e:
                    self._logger.warning(f"Error procesando documento similar: {str(e)}")
                    continue
            
            # Limitar resultados
            search_results = search_results[:request.limit]
            
            return SimilarDocumentsResponse(
                similar_documents=search_results,
                reference_document_id=request.document_id,
                total_found=len(search_results),
                similarity_threshold=request.similarity_threshold or self.similarity_threshold,
                message=f"Se encontraron {len(search_results)} documentos similares"
            )
            
        except Exception as e:
            self._logger.error(f"Error buscando documentos similares: {str(e)}")
            return create_error_response(
                "internal_error",
                f"Error interno: {str(e)}"
            )

# Funciones de herramientas individuales

async def search_knowledge_base(
    query: str,
    search_type: SearchType = SearchType.SEMANTIC,
    limit: int = 10,
    similarity_threshold: Optional[float] = None,
    document_types: Optional[List[DocumentType]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    include_metadata: bool = False,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[KnowledgeSearchResponse, ErrorResponse]:
    """Buscar en la base de conocimiento"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = KnowledgeToolsManager(odoo_client, db_client)
    request = KnowledgeSearchRequest(
        query=query,
        search_type=search_type,
        limit=limit,
        similarity_threshold=similarity_threshold,
        document_types=document_types,
        date_from=date_from,
        date_to=date_to,
        include_metadata=include_metadata
    )
    
    return await manager.search_knowledge_base(request)

async def get_document(
    document_id: int,
    include_chunks: bool = False,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[DocumentResponse, ErrorResponse]:
    """Obtener un documento específico"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = KnowledgeToolsManager(odoo_client, db_client)
    request = DocumentRequest(
        document_id=document_id,
        include_chunks=include_chunks
    )
    
    return await manager.get_document(request)

async def list_documents(
    document_types: Optional[List[DocumentType]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    author_ids: Optional[List[int]] = None,
    search_text: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    order_by: Optional[str] = None,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[DocumentListResponse, ErrorResponse]:
    """Listar documentos con filtros"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = KnowledgeToolsManager(odoo_client, db_client)
    request = DocumentListRequest(
        document_types=document_types,
        date_from=date_from,
        date_to=date_to,
        author_ids=author_ids,
        search_text=search_text,
        limit=limit,
        offset=offset,
        order_by=order_by
    )
    
    return await manager.list_documents(request)

async def search_similar_documents(
    document_id: int,
    limit: int = 10,
    similarity_threshold: Optional[float] = None,
    include_metadata: bool = False,
    odoo_client: OdooClient = None,
    db_client: DatabaseClient = None
) -> Union[SimilarDocumentsResponse, ErrorResponse]:
    """Buscar documentos similares"""
    
    if not odoo_client or not db_client:
        return create_error_response(
            "missing_clients",
            "Clientes Odoo y DB requeridos"
        )
    
    manager = KnowledgeToolsManager(odoo_client, db_client)
    request = SimilarDocumentsRequest(
        document_id=document_id,
        limit=limit,
        similarity_threshold=similarity_threshold,
        include_metadata=include_metadata
    )
    
    return await manager.search_similar_documents(request)