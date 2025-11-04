# PostgreSQL + PGVector - Imagen Personalizada

## 📋 Descripción

Este módulo contiene una imagen personalizada de PostgreSQL 15 con la extensión **PGVector** preinstalada, optimizada para aplicaciones de IA que requieren búsqueda vectorial y almacenamiento de embeddings.

## 🎯 Propósito

- **Búsqueda Semántica**: Permite realizar búsquedas por similitud en documentos usando embeddings
- **Almacenamiento de Vectores**: Soporte nativo para vectores de alta dimensión (768D para Gemini)
- **Integración con IA**: Base de datos optimizada para servicios de IA del proyecto PATCO

## 📁 Estructura del Módulo

```
postgres-pgvector/
├── Dockerfile              # Imagen personalizada PostgreSQL + PGVector
├── init-pgvector.sql       # Script de inicialización automática
└── README.md              # Este archivo
```

## 🔧 Componentes

### 1. **Dockerfile**
- **Base**: `postgres:15`
- **Extensión**: PGVector v0.5.1
- **Dependencias**: build-essential, git, postgresql-server-dev-15
- **Compilación**: Desde código fuente para máxima compatibilidad

### 2. **init-pgvector.sql**
- **Extensión**: Creación automática de `vector`
- **Tabla**: `ai_document_embeddings` para almacenar embeddings
- **Índices**: Optimizados para búsqueda HNSW (Hierarchical Navigable Small World)
- **Función**: `search_similar_documents()` para búsquedas de similitud

## 🗄️ Esquema de Base de Datos

### Tabla: `ai_document_embeddings`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | Clave primaria |
| `attachment_id` | INTEGER | ID del documento en Odoo |
| `chunk_index` | INTEGER | Índice del fragmento del documento |
| `content` | TEXT | Contenido textual del fragmento |
| `embedding` | vector(768) | Vector de embedding (Gemini) |
| `metadata` | JSONB | Metadatos adicionales |
| `created_at` | TIMESTAMP | Fecha de creación |
| `updated_at` | TIMESTAMP | Fecha de actualización |

### Índices Optimizados

```sql
-- Índice para búsqueda por documento
CREATE INDEX ai_document_embeddings_attachment_idx 
ON ai_document_embeddings(attachment_id);

-- Índice vectorial HNSW para similitud coseno
CREATE INDEX ai_document_embeddings_embedding_idx 
ON ai_document_embeddings USING hnsw (embedding vector_cosine_ops);
```

## 🚀 Uso en Docker Compose

### Configuración en `docker-compose.yml`

```yaml
services:
  db:
    build:
      context: ./ai-services/postgres-pgvector
      dockerfile: Dockerfile
    container_name: odoo-patco-db
    environment:
      - POSTGRES_DB=odoo_patco
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=P4tc0_2
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - odoo-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U odoo -d odoo_patco"]
      interval: 30s
      timeout: 10s
      retries: 5
```

### Comandos de Construcción

```bash
# Construir la imagen
docker compose build db

# Iniciar con la nueva imagen
docker compose up -d db
```

## 🔍 Funciones Disponibles

### `search_similar_documents()`

Busca documentos similares basándose en embeddings vectoriales.

**Parámetros:**
- `query_embedding`: vector(768) - Vector de consulta
- `similarity_threshold`: float - Umbral de similitud (default: 0.7)
- `max_results`: integer - Máximo número de resultados (default: 10)

**Retorna:**
- `attachment_id`: ID del documento
- `chunk_index`: Índice del fragmento
- `content`: Contenido textual
- `similarity`: Puntuación de similitud (0-1)
- `metadata`: Metadatos JSONB

**Ejemplo de uso:**

```sql
-- Buscar documentos similares
SELECT * FROM search_similar_documents(
    '[0.1, 0.2, 0.3, ...]'::vector(768),
    0.8,
    5
);
```

## 🔧 Verificación de Instalación

### Comandos de Validación

```bash
# Verificar que PGVector está disponible
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# Verificar que la extensión está creada
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Verificar tablas creadas
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "\dt ai_*"

# Probar función de búsqueda
docker exec odoo-patco-db psql -U odoo -d odoo_patco -c "SELECT search_similar_documents('[0.1]'::vector(768));"
```

## 📊 Especificaciones Técnicas

### Versiones
- **PostgreSQL**: 15
- **PGVector**: v0.5.1
- **Dimensión de vectores**: 768 (compatible con Gemini)
- **Algoritmo de índice**: HNSW (Hierarchical Navigable Small World)

### Métricas de Similitud
- **Distancia coseno**: `vector_cosine_ops`
- **Fórmula de similitud**: `1 - (embedding <=> query_embedding)`
- **Rango**: 0.0 (sin similitud) a 1.0 (idéntico)

## 🔗 Integración con Servicios IA

### Servicios Compatibles
- **Document Indexer**: Almacena embeddings automáticamente
- **MCP Server**: Consulta vectores para búsquedas semánticas
- **Odoo AI Agent**: Utiliza búsquedas para contexto de conversaciones

### Variables de Entorno Requeridas
```bash
PGHOST=db
PGPORT=5432
PGUSER=odoo
PGPASSWORD=P4tc0_2
PGDATABASE=odoo_patco
```

## 🛠️ Mantenimiento

### Limpieza de Datos
```sql
-- Eliminar embeddings antiguos
DELETE FROM ai_document_embeddings 
WHERE created_at < NOW() - INTERVAL '30 days';

-- Reindexar para optimizar performance
REINDEX INDEX ai_document_embeddings_embedding_idx;
```

### Monitoreo de Performance
```sql
-- Verificar tamaño de la tabla
SELECT pg_size_pretty(pg_total_relation_size('ai_document_embeddings'));

-- Estadísticas de índices
SELECT * FROM pg_stat_user_indexes WHERE relname = 'ai_document_embeddings';
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **Extensión no disponible**
   ```bash
   # Verificar compilación
   docker exec odoo-patco-db ls -la /usr/share/postgresql/15/extension/ | grep vector
   ```

2. **Error de permisos**
   ```bash
   # Verificar permisos del script
   docker exec odoo-patco-db ls -la /docker-entrypoint-initdb.d/
   ```

3. **Índice HNSW lento**
   ```sql
   -- Ajustar parámetros del índice
   SET hnsw.ef_construction = 200;
   SET hnsw.m = 16;
   ```

## 📝 Notas de Desarrollo

- La imagen se construye automáticamente al ejecutar `docker compose build db`
- El script `init-pgvector.sql` se ejecuta solo en la primera inicialización
- Los embeddings se almacenan en formato binario optimizado
- La búsqueda vectorial utiliza aproximación HNSW para mejor performance

## 🔄 Actualizaciones

Para actualizar PGVector:
1. Modificar la versión en el `Dockerfile`
2. Reconstruir la imagen: `docker compose build db --no-cache`
3. Recrear el contenedor: `docker compose up -d db`

---

**Autor**: PATCO AI Team  
**Versión**: 1.0  
**Última actualización**: Diciembre 2024