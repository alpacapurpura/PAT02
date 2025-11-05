-- init-pgvector.sql
-- Inicialización de extensión PGVector y estructura básica para embeddings
-- Este script se ejecuta automáticamente cuando se inicializa el contenedor

-- Crear extensión PGVector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla principal para almacenar embeddings de documentos
CREATE TABLE IF NOT EXISTS ai_document_embeddings (
    id BIGSERIAL PRIMARY KEY,
    attachment_id INTEGER NOT NULL, -- ID del documento/adjunto en Odoo
    chunk_index INTEGER NOT NULL,   -- Índice del fragmento
    content TEXT,                   -- Contenido textual del fragmento
    embedding vector(768) NOT NULL, -- Embedding (por defecto 768 dimensiones: Gemini)
    metadata JSONB,                 -- Metadatos adicionales
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice por documento para acelerar búsquedas por attachment_id
CREATE INDEX IF NOT EXISTS ai_document_embeddings_attachment_idx
ON ai_document_embeddings (attachment_id);

-- Índice vectorial HNSW para similitud (coseno)
CREATE INDEX IF NOT EXISTS ai_document_embeddings_embedding_hnsw_idx
ON ai_document_embeddings USING hnsw (embedding vector_cosine_ops);

-- Función para buscar documentos similares basado en embeddings
-- Nota: Usa distancia euclidiana por defecto si el índice no aplica coseno
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    attachment_id INTEGER,
    chunk_index INTEGER,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE SQL STABLE AS $$
    SELECT
        e.attachment_id,
        e.chunk_index,
        e.content,
        -- Similitud aproximada basada en distancia (convertida a [0,1])
        1.0 / (1.0 + (e.embedding <-> query_embedding)) AS similarity,
        e.metadata
    FROM ai_document_embeddings e
    WHERE 1.0 / (1.0 + (e.embedding <-> query_embedding)) >= similarity_threshold
    ORDER BY e.embedding <-> query_embedding ASC
    LIMIT max_results;
$$;

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION