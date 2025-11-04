"""
PATCO AI Agent - Document Processors
Procesadores especializados para diferentes tipos de documentos

Módulos disponibles:
- text_processor: Procesamiento de archivos de texto plano
- pdf_processor: Procesamiento de documentos PDF
- image_processor: Procesamiento de imágenes con OCR
"""

from .text_processor import TextProcessor
from .pdf_processor import PDFProcessor
from .image_processor import ImageProcessor

__all__ = ['TextProcessor', 'PDFProcessor', 'ImageProcessor']