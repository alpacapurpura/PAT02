"""
PATCO AI Agent - PDF Processor
Procesador especializado para documentos PDF

Funcionalidades:
- Extracción de texto desde PDF usando PyPDF2
- División por páginas y chunks
- Preservación de números de página
- Manejo de PDFs con múltiples páginas
"""

import base64
import io
from typing import List, Dict
import logging

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Procesador para documentos PDF
    
    Características:
    - Extracción de texto página por página
    - División inteligente en chunks
    - Preservación de metadatos de página
    - Manejo robusto de errores de PDF
    """
    
    def __init__(self):
        """Inicializa el procesador PDF"""
        
        self.chunk_size = 1000
        self.overlap = 200
        self.min_chunk_size = 100
        
        if PyPDF2 is None:
            logger.error("PyPDF2 no está instalado. Instalar con: pip install PyPDF2")
            raise ImportError("PyPDF2 es requerido para procesar PDFs")
        
        logger.debug("PDFProcessor inicializado")
    
    async def extract_text(self, document: Dict) -> List[Dict]:
        """
        Extrae texto de documento PDF
        
        Args:
            document: Diccionario con datos del documento desde Odoo
            
        Returns:
            List[Dict]: Lista de chunks con contenido y metadatos
        """
        
        try:
            # Decodificar PDF desde base64
            pdf_bytes = base64.b64decode(document['datas'])
            pdf_file = io.BytesIO(pdf_bytes)
            
            # Leer PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            if len(pdf_reader.pages) == 0:
                logger.warning(f"PDF {document['id']} no tiene páginas")
                return []
            
            chunks = []
            total_pages = len(pdf_reader.pages)
            
            logger.info(f"Procesando PDF {document['id']} con {total_pages} páginas")
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    # Extraer texto de la página
                    page_text = page.extract_text()
                    
                    if not page_text.strip():
                        logger.debug(f"Página {page_num + 1} del PDF {document['id']} está vacía")
                        continue
                    
                    # Limpiar y normalizar texto de la página
                    page_text = self._clean_pdf_text(page_text)
                    
                    if len(page_text.strip()) < self.min_chunk_size:
                        logger.debug(f"Página {page_num + 1} del PDF {document['id']} tiene muy poco texto")
                        continue
                    
                    # Dividir página en chunks si es necesario
                    page_chunks = self._split_text(page_text)
                    
                    for chunk_idx, chunk in enumerate(page_chunks):
                        if len(chunk.strip()) >= self.min_chunk_size:
                            chunks.append({
                                'content': chunk,
                                'page_number': page_num + 1,
                                'chunk_type': 'pdf_page',
                                'page_chunk_index': chunk_idx,
                                'total_pages': total_pages,
                                'char_count': len(chunk),
                                'word_count': len(chunk.split())
                            })
                
                except Exception as e:
                    logger.error(f"Error procesando página {page_num + 1} del PDF {document['id']}: {e}")
                    continue
            
            logger.info(f"Extraídos {len(chunks)} chunks del PDF {document['id']}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error procesando PDF {document['id']}: {e}")
            return []
    
    def _clean_pdf_text(self, text: str) -> str:
        """
        Limpia texto extraído de PDF
        
        Args:
            text: Texto extraído del PDF
            
        Returns:
            str: Texto limpio
        """
        
        import re
        
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Remover caracteres de control extraños
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remover espacios al inicio y final
        text = text.strip()
        
        return text
    
    def _split_text(self, text: str) -> List[str]:
        """
        Divide texto en chunks con solapamiento
        Implementación similar a TextProcessor pero optimizada para PDF
        
        Args:
            text: Texto a dividir
            
        Returns:
            List[str]: Lista de chunks
        """
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Si no es el último chunk, buscar un punto de corte natural
            if end < len(text):
                # Buscar el mejor punto de corte
                cut_points = [
                    (r'\n\n', 2),  # Párrafos
                    (r'\. ', 2),   # Oraciones
                    (r'[.!?] ', 2), # Puntuación
                    (r', ', 2),    # Comas
                    (r' ', 1)      # Espacios
                ]
                
                best_cut = end
                search_start = max(start + self.chunk_size - 200, start)
                
                for pattern, offset in cut_points:
                    import re
                    search_text = text[search_start:end]
                    matches = list(re.finditer(pattern, search_text))
                    
                    if matches:
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
            
            # Solapamiento inteligente
            overlap_start = max(start, end - self.overlap)
            
            # Buscar un buen punto de inicio
            next_start = end
            if overlap_start < end:
                import re
                search_text = text[overlap_start:end]
                space_match = re.search(r'\s', search_text)
                if space_match:
                    next_start = overlap_start + space_match.start()
            
            start = next_start
            
            # Evitar bucles infinitos
            if start >= end:
                start = end
        
        return chunks