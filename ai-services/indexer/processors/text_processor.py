"""
PATCO AI Agent - Text Processor
Procesador especializado para documentos de texto plano y HTML

Funcionalidades:
- Extracción de texto desde base64
- División inteligente en chunks con solapamiento
- Soporte para texto plano y HTML básico
"""

import base64
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """
    Procesador para documentos de texto plano y HTML
    
    Características:
    - Chunks de tamaño configurable con solapamiento
    - Puntos de corte inteligentes (espacios, puntuación)
    - Limpieza básica de HTML
    - Preservación de estructura de párrafos
    """
    
    def __init__(self):
        """Inicializa el procesador con configuración por defecto"""
        
        self.chunk_size = 1000  # Caracteres por chunk
        self.overlap = 200      # Solapamiento entre chunks
        self.min_chunk_size = 100  # Tamaño mínimo de chunk
        
        logger.debug("TextProcessor inicializado")
    
    async def extract_text(self, document: Dict) -> List[Dict]:
        """
        Extrae texto de documento de texto plano o HTML
        
        Args:
            document: Diccionario con datos del documento desde Odoo
            
        Returns:
            List[Dict]: Lista de chunks con contenido y metadatos
        """
        
        try:
            # Decodificar contenido base64
            content_bytes = base64.b64decode(document['datas'])
            
            # Intentar decodificar con diferentes encodings
            text = self._decode_text(content_bytes)
            
            if not text.strip():
                logger.warning(f"Documento {document['id']} está vacío después de decodificar")
                return []
            
            # Limpiar texto si es HTML
            if document.get('mimetype') == 'text/html':
                text = self._clean_html(text)
            
            # Normalizar texto
            text = self._normalize_text(text)
            
            # Dividir en chunks
            chunks = self._split_text(text)
            
            # Filtrar chunks muy pequeños
            chunks = [chunk for chunk in chunks if len(chunk.strip()) >= self.min_chunk_size]
            
            # Crear estructura de retorno
            result = []
            for i, chunk in enumerate(chunks):
                result.append({
                    'content': chunk,
                    'page_number': None,  # No aplica para texto plano
                    'chunk_type': 'text',
                    'char_count': len(chunk),
                    'word_count': len(chunk.split())
                })
            
            logger.info(f"Extraídos {len(result)} chunks de documento de texto {document['id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error extrayendo texto del documento {document['id']}: {e}")
            return []
    
    def _decode_text(self, content_bytes: bytes) -> str:
        """
        Decodifica bytes a texto probando diferentes encodings
        
        Args:
            content_bytes: Contenido en bytes
            
        Returns:
            str: Texto decodificado
        """
        
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                return content_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # Si ningún encoding funciona, usar utf-8 con errores ignorados
        logger.warning("No se pudo decodificar con encodings estándar, usando utf-8 con errores ignorados")
        return content_bytes.decode('utf-8', errors='ignore')
    
    def _clean_html(self, html_text: str) -> str:
        """
        Limpia HTML básico para extraer solo texto
        
        Args:
            html_text: Texto HTML
            
        Returns:
            str: Texto limpio sin tags HTML
        """
        
        # Remover scripts y styles
        html_text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        html_text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Convertir algunos tags a saltos de línea
        html_text = re.sub(r'<(br|p|div|h[1-6])[^>]*>', '\n', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</(p|div|h[1-6])>', '\n', html_text, flags=re.IGNORECASE)
        
        # Remover todos los tags HTML restantes
        html_text = re.sub(r'<[^>]+>', '', html_text)
        
        # Decodificar entidades HTML básicas
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, char in html_entities.items():
            html_text = html_text.replace(entity, char)
        
        return html_text
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza el texto para mejorar la calidad de los chunks
        
        Args:
            text: Texto a normalizar
            
        Returns:
            str: Texto normalizado
        """
        
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Normalizar saltos de línea múltiples
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remover espacios al inicio y final
        text = text.strip()
        
        return text
    
    def _split_text(self, text: str) -> List[str]:
        """
        Divide texto en chunks con solapamiento inteligente
        
        Args:
            text: Texto a dividir
            
        Returns:
            List[str]: Lista de chunks de texto
        """
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Si no es el último chunk, buscar un punto de corte natural
            if end < len(text):
                # Buscar el mejor punto de corte en orden de preferencia
                cut_points = [
                    (r'\n\n', 2),  # Párrafos
                    (r'\. ', 2),   # Oraciones
                    (r'[.!?] ', 2), # Puntuación
                    (r', ', 2),    # Comas
                    (r' ', 1)      # Espacios
                ]
                
                best_cut = end
                for pattern, offset in cut_points:
                    # Buscar hacia atrás desde el final del chunk
                    search_start = max(start + self.chunk_size - 200, start)
                    search_text = text[search_start:end]
                    
                    matches = list(re.finditer(pattern, search_text))
                    if matches:
                        # Tomar el último match
                        last_match = matches[-1]
                        best_cut = search_start + last_match.end()
                        break
                
                end = best_cut
            
            # Extraer chunk
            chunk = text[start:end].strip()
            
            if chunk and len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
            
            # Calcular siguiente posición con solapamiento
            if end >= len(text):
                break
            
            # Buscar inicio del siguiente chunk con solapamiento
            overlap_start = max(start, end - self.overlap)
            
            # Buscar un buen punto de inicio (evitar cortar palabras)
            next_start = end
            if overlap_start < end:
                # Buscar hacia adelante desde overlap_start
                search_text = text[overlap_start:end]
                space_match = re.search(r'\s', search_text)
                if space_match:
                    next_start = overlap_start + space_match.start()
            
            start = next_start
            
            # Evitar bucles infinitos
            if start >= end:
                start = end
        
        return chunks