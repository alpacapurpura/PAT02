"""
PATCO AI Agent - Image Processor
Procesador especializado para imágenes con OCR

Funcionalidades:
- Extracción de texto desde imágenes usando OCR
- Soporte para JPEG y PNG
- Procesamiento básico de imágenes técnicas
- Fallback cuando OCR no está disponible
"""

import base64
import io
from typing import List, Dict
import logging

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

logger = logging.getLogger(__name__)

class ImageProcessor:
    """
    Procesador para imágenes con capacidades OCR
    
    Características:
    - OCR usando Tesseract (si está disponible)
    - Soporte para JPEG y PNG
    - Preprocesamiento básico de imágenes
    - Fallback descriptivo cuando OCR no funciona
    """
    
    def __init__(self):
        """Inicializa el procesador de imágenes"""
        
        self.chunk_size = 1000
        self.min_chunk_size = 50
        
        # Verificar dependencias
        self.ocr_available = pytesseract is not None and Image is not None
        
        if not self.ocr_available:
            logger.warning("OCR no disponible. Instalar con: pip install pytesseract pillow")
            logger.warning("También se requiere Tesseract instalado en el sistema")
        
        logger.debug(f"ImageProcessor inicializado (OCR disponible: {self.ocr_available})")
    
    async def extract_text(self, document: Dict) -> List[Dict]:
        """
        Extrae texto de imagen usando OCR
        
        Args:
            document: Diccionario con datos del documento desde Odoo
            
        Returns:
            List[Dict]: Lista de chunks con contenido extraído
        """
        
        try:
            # Decodificar imagen desde base64
            image_bytes = base64.b64decode(document['datas'])
            
            if not self.ocr_available:
                # Fallback: crear descripción básica
                return self._create_fallback_description(document, image_bytes)
            
            # Procesar imagen con OCR
            return await self._process_with_ocr(document, image_bytes)
            
        except Exception as e:
            logger.error(f"Error procesando imagen {document['id']}: {e}")
            return []
    
    async def _process_with_ocr(self, document: Dict, image_bytes: bytes) -> List[Dict]:
        """
        Procesa imagen usando OCR
        
        Args:
            document: Datos del documento
            image_bytes: Bytes de la imagen
            
        Returns:
            List[Dict]: Chunks con texto extraído
        """
        
        try:
            # Cargar imagen
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Preprocesar imagen para mejorar OCR
            image = self._preprocess_image(image)
            
            # Extraer texto con OCR
            extracted_text = pytesseract.image_to_string(image, lang='spa+eng')
            
            if not extracted_text.strip():
                logger.info(f"No se extrajo texto de la imagen {document['id']}")
                return self._create_fallback_description(document, image_bytes)
            
            # Limpiar texto extraído
            cleaned_text = self._clean_ocr_text(extracted_text)
            
            if len(cleaned_text.strip()) < self.min_chunk_size:
                logger.info(f"Texto extraído de imagen {document['id']} es muy corto")
                return self._create_fallback_description(document, image_bytes)
            
            # Dividir en chunks si es necesario
            chunks = self._split_text(cleaned_text)
            
            result = []
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) >= self.min_chunk_size:
                    result.append({
                        'content': chunk,
                        'page_number': None,
                        'chunk_type': 'image_ocr',
                        'image_format': document.get('mimetype', 'unknown'),
                        'ocr_confidence': 'medium',  # Podríamos mejorar esto
                        'char_count': len(chunk),
                        'word_count': len(chunk.split())
                    })
            
            logger.info(f"Extraídos {len(result)} chunks de imagen {document['id']} usando OCR")
            return result
            
        except Exception as e:
            logger.error(f"Error en OCR para imagen {document['id']}: {e}")
            return self._create_fallback_description(document, image_bytes)
    
    def _preprocess_image(self, image: 'Image.Image') -> 'Image.Image':
        """
        Preprocesa imagen para mejorar OCR
        
        Args:
            image: Imagen PIL
            
        Returns:
            Image.Image: Imagen procesada
        """
        
        try:
            # Redimensionar si es muy grande (mejora velocidad OCR)
            max_size = 2000
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convertir a escala de grises para mejorar OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            return image
            
        except Exception as e:
            logger.warning(f"Error preprocesando imagen: {e}")
            return image
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Limpia texto extraído por OCR
        
        Args:
            text: Texto crudo del OCR
            
        Returns:
            str: Texto limpio
        """
        
        import re
        
        # Remover caracteres extraños comunes en OCR
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\/\\\n]', ' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remover líneas muy cortas (probablemente ruido OCR)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) >= 3:  # Mínimo 3 caracteres por línea
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        return text.strip()
    
    def _create_fallback_description(self, document: Dict, image_bytes: bytes) -> List[Dict]:
        """
        Crea descripción básica cuando OCR no está disponible o falla
        
        Args:
            document: Datos del documento
            image_bytes: Bytes de la imagen
            
        Returns:
            List[Dict]: Chunk con descripción básica
        """
        
        try:
            # Información básica de la imagen
            description_parts = [
                f"Imagen técnica: {document.get('name', 'Sin nombre')}",
                f"Formato: {document.get('mimetype', 'Desconocido')}",
                f"Tamaño del archivo: {len(image_bytes)} bytes"
            ]
            
            # Intentar obtener dimensiones si PIL está disponible
            if Image is not None:
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    description_parts.append(f"Dimensiones: {image.size[0]}x{image.size[1]} píxeles")
                    description_parts.append(f"Modo de color: {image.mode}")
                except:
                    pass
            
            # Agregar contexto si está disponible
            if document.get('x_document_type'):
                description_parts.append(f"Tipo de documento: {document['x_document_type']}")
            
            description_parts.append("Nota: Contenido visual no procesado por OCR")
            
            description = ". ".join(description_parts)
            
            return [{
                'content': description,
                'page_number': None,
                'chunk_type': 'image_description',
                'image_format': document.get('mimetype', 'unknown'),
                'ocr_available': False,
                'char_count': len(description),
                'word_count': len(description.split())
            }]
            
        except Exception as e:
            logger.error(f"Error creando descripción fallback: {e}")
            return []
    
    def _split_text(self, text: str) -> List[str]:
        """
        Divide texto en chunks (implementación básica)
        
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
            
            if end < len(text):
                # Buscar punto de corte natural
                import re
                search_text = text[max(start, end - 100):end]
                
                # Buscar último punto, salto de línea o espacio
                for pattern in [r'\. ', r'\n', r' ']:
                    matches = list(re.finditer(pattern, search_text))
                    if matches:
                        last_match = matches[-1]
                        end = max(start, end - 100) + last_match.end()
                        break
            
            chunk = text[start:end].strip()
            if chunk and len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
            
            start = end
        
        return chunks