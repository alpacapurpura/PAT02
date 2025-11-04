#!/usr/bin/env python3
"""
Esquemas para herramientas de base de conocimiento (RAG)
Definición de requests y responses para búsqueda semántica
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseRequest, BaseResponse, BaseConfig, StatusEnum

class DocumentType(str, Enum):
    """Tipos de documentos en la base de conocimiento"""
    MANUAL = "manual"
    PROCEDURE = "procedure"
    TROUBLESHOOTING = "troubleshooting"
    FAQ = "faq"
    SPECIFICATION = "specification"
    TRAINING = "training"
    POLICY = "policy"
    OTHER = "other"

class DocumentStatus(str, Enum):
    """Estados de documentos"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class SearchType(str, Enum):
    """Tipos de búsqueda"""
    SEMANTIC = "semantic"  # Búsqueda semántica con embeddings
    KEYWORD = "keyword"    # Búsqueda por palabras clave
    HYBRID = "hybrid"      # Combinación de ambas

class RelevanceLevel(str, Enum):
    """Niveles de relevancia"""
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.6 - 0.8
    LOW = "low"        # < 0.6

class KnowledgeDocument(BaseModel, BaseConfig):
    """Documento de la base de conocimiento"""
    id: int = Field(description="ID del documento")
    name: str = Field(description="Nombre del documento")
    
    # Contenido
    content: Optional[str] = Field(None, description="Contenido del documento")
    summary: Optional[str] = Field(None, description="Resumen del documento")
    keywords: Optional[List[str]] = Field(None, description="Palabras clave")
    
    # Metadatos
    document_type: DocumentType = Field(description="Tipo de documento")
    status: DocumentStatus = Field(description="Estado del documento")
    language: Optional[str] = Field(None, description="Idioma del documento")
    version: Optional[str] = Field(None, description="Versión del documento")
    
    # Fechas
    create_date: Optional[datetime] = Field(None, description="Fecha de creación")
    write_date: Optional[datetime] = Field(None, description="Fecha de modificación")
    publish_date: Optional[datetime] = Field(None, description="Fecha de publicación")
    expiry_date: Optional[datetime] = Field(None, description="Fecha de expiración")
    
    # Relaciones
    author_id: Optional[int] = Field(None, description="ID del autor")
    author_name: Optional[str] = Field(None, description="Nombre del autor")
    category_id: Optional[int] = Field(None, description="ID de categoría")
    category_name: Optional[str] = Field(None, description="Nombre de categoría")
    
    # Archivo
    file_name: Optional[str] = Field(None, description="Nombre del archivo")
    file_size: Optional[int] = Field(None, description="Tamaño del archivo")
    mimetype: Optional[str] = Field(None, description="Tipo MIME")
    file_url: Optional[str] = Field(None, description="URL del archivo")
    
    # Estadísticas
    view_count: Optional[int] = Field(None, description="Número de visualizaciones")
    download_count: Optional[int] = Field(None, description="Número de descargas")
    rating: Optional[float] = Field(None, description="Calificación promedio")
    
    # Campos personalizados
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Campos personalizados")
    
    # Metadatos del sistema
    company_id: Optional[int] = Field(None, description="ID de la compañía")
    active: bool = Field(default=True, description="Documento activo")

class KnowledgeChunk(BaseModel, BaseConfig):
    """Fragmento de documento para RAG"""
    id: int = Field(description="ID del fragmento")
    document_id: int = Field(description="ID del documento padre")
    document_name: Optional[str] = Field(None, description="Nombre del documento")
    
    # Contenido del fragmento
    content: str = Field(description="Contenido del fragmento")
    chunk_index: int = Field(description="Índice del fragmento en el documento")
    chunk_size: Optional[int] = Field(None, description="Tamaño del fragmento en caracteres")
    
    # Metadatos del fragmento
    start_position: Optional[int] = Field(None, description="Posición inicial en el documento")
    end_position: Optional[int] = Field(None, description="Posición final en el documento")
    page_number: Optional[int] = Field(None, description="Número de página")
    section: Optional[str] = Field(None, description="Sección del documento")
    
    # Embedding
    embedding_model: Optional[str] = Field(None, description="Modelo usado para el embedding")
    embedding_date: Optional[datetime] = Field(None, description="Fecha del embedding")
    
    # Metadatos heredados del documento
    document_type: Optional[DocumentType] = Field(None, description="Tipo de documento")
    category_name: Optional[str] = Field(None, description="Categoría del documento")
    author_name: Optional[str] = Field(None, description="Autor del documento")
    
    # Campos personalizados
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Campos personalizados")

class SearchResult(BaseModel, BaseConfig):
    """Resultado de búsqueda"""
    chunk: KnowledgeChunk = Field(description="Fragmento encontrado")
    score: float = Field(description="Puntuación de relevancia (0-1)")
    relevance_level: RelevanceLevel = Field(description="Nivel de relevancia")
    
    # Información adicional
    matched_keywords: Optional[List[str]] = Field(None, description="Palabras clave coincidentes")
    context_before: Optional[str] = Field(None, description="Contexto anterior")
    context_after: Optional[str] = Field(None, description="Contexto posterior")
    
    # Metadatos de la búsqueda
    search_type: Optional[SearchType] = Field(None, description="Tipo de búsqueda usado")
    distance: Optional[float] = Field(None, description="Distancia del embedding")

class SearchSummary(BaseModel, BaseConfig):
    """Resumen de búsqueda"""
    total_results: int = Field(description="Total de resultados encontrados")
    high_relevance_count: int = Field(description="Resultados de alta relevancia")
    medium_relevance_count: int = Field(description="Resultados de relevancia media")
    low_relevance_count: int = Field(description="Resultados de baja relevancia")
    
    # Estadísticas
    avg_score: float = Field(description="Puntuación promedio")
    max_score: float = Field(description="Puntuación máxima")
    min_score: float = Field(description="Puntuación mínima")
    
    # Distribución por tipo de documento
    document_types: Dict[str, int] = Field(description="Distribución por tipo de documento")
    categories: Dict[str, int] = Field(description="Distribución por categoría")
    
    # Tiempo de búsqueda
    search_time_ms: Optional[float] = Field(None, description="Tiempo de búsqueda en ms")
    embedding_time_ms: Optional[float] = Field(None, description="Tiempo de embedding en ms")

# Requests

class KnowledgeSearchRequest(BaseRequest):
    """Request para búsqueda en base de conocimiento"""
    query: str = Field(
        description="Consulta de búsqueda",
        min_length=3,
        max_length=1000
    )
    
    # Configuración de búsqueda
    search_type: SearchType = Field(
        default=SearchType.SEMANTIC,
        description="Tipo de búsqueda"
    )
    limit: int = Field(
        default=10,
        description="Número máximo de resultados",
        ge=1,
        le=50
    )
    min_score: float = Field(
        default=0.3,
        description="Puntuación mínima de relevancia",
        ge=0.0,
        le=1.0
    )
    
    # Filtros
    document_types: Optional[List[DocumentType]] = Field(
        None,
        description="Filtrar por tipos de documento"
    )
    categories: Optional[List[str]] = Field(
        None,
        description="Filtrar por categorías"
    )
    languages: Optional[List[str]] = Field(
        None,
        description="Filtrar por idiomas"
    )
    authors: Optional[List[str]] = Field(
        None,
        description="Filtrar por autores"
    )
    
    # Filtros por fecha
    date_from: Optional[date] = Field(
        None,
        description="Fecha de publicación desde"
    )
    date_to: Optional[date] = Field(
        None,
        description="Fecha de publicación hasta"
    )
    
    # Configuración de contexto
    include_context: bool = Field(
        default=False,
        description="Incluir contexto antes y después"
    )
    context_size: int = Field(
        default=200,
        description="Tamaño del contexto en caracteres",
        ge=50,
        le=500
    )
    
    # Configuración de embedding
    embedding_model: Optional[str] = Field(
        None,
        description="Modelo de embedding específico a usar"
    )
    
    # Metadatos
    user_id: Optional[int] = Field(
        None,
        description="ID del usuario que realiza la búsqueda"
    )
    session_id: Optional[str] = Field(
        None,
        description="ID de sesión para tracking"
    )

class DocumentRequest(BaseRequest):
    """Request para obtener un documento completo"""
    document_id: int = Field(
        description="ID del documento",
        gt=0
    )
    include_content: bool = Field(
        default=True,
        description="Incluir contenido completo"
    )
    include_chunks: bool = Field(
        default=False,
        description="Incluir fragmentos del documento"
    )
    include_statistics: bool = Field(
        default=False,
        description="Incluir estadísticas de uso"
    )

class DocumentListRequest(BaseRequest):
    """Request para listar documentos"""
    # Filtros
    document_type: Optional[DocumentType] = Field(
        None,
        description="Filtrar por tipo de documento"
    )
    status: Optional[DocumentStatus] = Field(
        None,
        description="Filtrar por estado"
    )
    category_id: Optional[int] = Field(
        None,
        description="Filtrar por categoría"
    )
    author_id: Optional[int] = Field(
        None,
        description="Filtrar por autor"
    )
    language: Optional[str] = Field(
        None,
        description="Filtrar por idioma"
    )
    
    # Búsqueda por texto
    search_text: Optional[str] = Field(
        None,
        description="Buscar en nombre y resumen"
    )
    
    # Filtros por fecha
    created_from: Optional[date] = Field(
        None,
        description="Fecha de creación desde"
    )
    created_to: Optional[date] = Field(
        None,
        description="Fecha de creación hasta"
    )
    
    # Paginación
    page: int = Field(
        default=1,
        description="Número de página",
        ge=1
    )
    page_size: int = Field(
        default=20,
        description="Tamaño de página",
        ge=1,
        le=100
    )
    
    # Ordenamiento
    order_by: Optional[str] = Field(
        default="write_date",
        description="Campo para ordenar"
    )
    order_direction: Optional[str] = Field(
        default="desc",
        description="Dirección del ordenamiento (asc/desc)"
    )
    
    @validator('order_direction')
    def validate_order_direction(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("order_direction debe ser 'asc' o 'desc'")
        return v.lower()

class SimilarDocumentsRequest(BaseRequest):
    """Request para encontrar documentos similares"""
    document_id: int = Field(
        description="ID del documento de referencia",
        gt=0
    )
    limit: int = Field(
        default=5,
        description="Número máximo de documentos similares",
        ge=1,
        le=20
    )
    min_similarity: float = Field(
        default=0.5,
        description="Similitud mínima",
        ge=0.0,
        le=1.0
    )
    exclude_same_category: bool = Field(
        default=False,
        description="Excluir documentos de la misma categoría"
    )

# Responses

class KnowledgeSearchResponse(BaseResponse):
    """Response de búsqueda en base de conocimiento"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: List[SearchResult] = Field(
        description="Resultados de búsqueda"
    )
    summary: SearchSummary = Field(
        description="Resumen de la búsqueda"
    )
    query: str = Field(
        description="Consulta original"
    )
    search_id: Optional[str] = Field(
        None,
        description="ID único de la búsqueda"
    )

class DocumentResponse(BaseResponse):
    """Response con información de documento"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: KnowledgeDocument = Field(
        description="Datos del documento"
    )
    chunks: Optional[List[KnowledgeChunk]] = Field(
        None,
        description="Fragmentos del documento"
    )

class DocumentListResponse(BaseResponse):
    """Response con lista de documentos"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: List[KnowledgeDocument] = Field(
        description="Lista de documentos"
    )
    total_count: int = Field(
        description="Total de documentos que cumplen los filtros"
    )
    page: int = Field(
        description="Página actual"
    )
    page_size: int = Field(
        description="Tamaño de página"
    )
    total_pages: int = Field(
        description="Total de páginas"
    )

class SimilarDocumentsResponse(BaseResponse):
    """Response con documentos similares"""
    status: StatusEnum = Field(
        default=StatusEnum.SUCCESS,
        description="Estado de la respuesta"
    )
    data: List[SearchResult] = Field(
        description="Documentos similares"
    )
    reference_document_id: int = Field(
        description="ID del documento de referencia"
    )

# Funciones de utilidad

def determine_relevance_level(score: float) -> RelevanceLevel:
    """Determinar nivel de relevancia basado en puntuación"""
    if score >= 0.8:
        return RelevanceLevel.HIGH
    elif score >= 0.6:
        return RelevanceLevel.MEDIUM
    else:
        return RelevanceLevel.LOW

def create_search_result(
    chunk_data: Dict[str, Any],
    score: float,
    search_type: SearchType = SearchType.SEMANTIC,
    include_context: bool = False,
    context_size: int = 200
) -> SearchResult:
    """Crear resultado de búsqueda desde datos de chunk"""
    
    # Crear chunk
    chunk = KnowledgeChunk(**chunk_data)
    
    # Determinar nivel de relevancia
    relevance_level = determine_relevance_level(score)
    
    # Extraer contexto si se solicita
    context_before = None
    context_after = None
    if include_context and chunk.content:
        content_len = len(chunk.content)
        if content_len > context_size * 2:
            mid_point = content_len // 2
            context_before = chunk.content[max(0, mid_point - context_size):mid_point]
            context_after = chunk.content[mid_point:min(content_len, mid_point + context_size)]
    
    return SearchResult(
        chunk=chunk,
        score=score,
        relevance_level=relevance_level,
        context_before=context_before,
        context_after=context_after,
        search_type=search_type,
        distance=1.0 - score if search_type == SearchType.SEMANTIC else None
    )

def create_search_summary(
    results: List[SearchResult],
    search_time_ms: Optional[float] = None,
    embedding_time_ms: Optional[float] = None
) -> SearchSummary:
    """Crear resumen de búsqueda"""
    
    if not results:
        return SearchSummary(
            total_results=0,
            high_relevance_count=0,
            medium_relevance_count=0,
            low_relevance_count=0,
            avg_score=0.0,
            max_score=0.0,
            min_score=0.0,
            document_types={},
            categories={},
            search_time_ms=search_time_ms,
            embedding_time_ms=embedding_time_ms
        )
    
    # Contar por nivel de relevancia
    high_count = sum(1 for r in results if r.relevance_level == RelevanceLevel.HIGH)
    medium_count = sum(1 for r in results if r.relevance_level == RelevanceLevel.MEDIUM)
    low_count = sum(1 for r in results if r.relevance_level == RelevanceLevel.LOW)
    
    # Calcular estadísticas de puntuación
    scores = [r.score for r in results]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    
    # Contar por tipo de documento
    document_types = {}
    for result in results:
        doc_type = result.chunk.document_type
        if doc_type:
            doc_type_str = doc_type.value if isinstance(doc_type, DocumentType) else str(doc_type)
            document_types[doc_type_str] = document_types.get(doc_type_str, 0) + 1
    
    # Contar por categoría
    categories = {}
    for result in results:
        category = result.chunk.category_name
        if category:
            categories[category] = categories.get(category, 0) + 1
    
    return SearchSummary(
        total_results=len(results),
        high_relevance_count=high_count,
        medium_relevance_count=medium_count,
        low_relevance_count=low_count,
        avg_score=avg_score,
        max_score=max_score,
        min_score=min_score,
        document_types=document_types,
        categories=categories,
        search_time_ms=search_time_ms,
        embedding_time_ms=embedding_time_ms
    )

def build_knowledge_search_filters(
    search_request: KnowledgeSearchRequest
) -> Dict[str, Any]:
    """Construir filtros para búsqueda en base de conocimiento"""
    filters = {}
    
    # Filtros básicos
    if search_request.document_types:
        filters['document_types'] = [dt.value for dt in search_request.document_types]
    
    if search_request.categories:
        filters['categories'] = search_request.categories
    
    if search_request.languages:
        filters['languages'] = search_request.languages
    
    if search_request.authors:
        filters['authors'] = search_request.authors
    
    # Filtros por fecha
    if search_request.date_from:
        filters['date_from'] = search_request.date_from
    
    if search_request.date_to:
        filters['date_to'] = search_request.date_to
    
    # Configuración de búsqueda
    filters['min_score'] = search_request.min_score
    filters['limit'] = search_request.limit
    filters['search_type'] = search_request.search_type.value
    
    return filters

def extract_keywords_from_query(query: str) -> List[str]:
    """Extraer palabras clave de una consulta"""
    import re
    
    # Limpiar y dividir la consulta
    words = re.findall(r'\b\w+\b', query.lower())
    
    # Filtrar palabras muy cortas y comunes
    stop_words = {
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
        'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como',
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are'
    }
    
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    return list(set(keywords))  # Eliminar duplicados