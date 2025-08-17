"""
Ingestion module for the Dynamic Educational RAG System.

Handles content ingestion from multiple sources:
- PDF documents (NCERT and other educational materials)
- YouTube transcripts with timing information
- Web content extraction and cleaning
- General text file processing
"""

from .pdf_processor import PDFProcessor
from .youtube_processor import YouTubeProcessor
from .web_scraper import WebScraper
from .file_registry import FileRegistryClient

__all__ = [
    "PDFProcessor",
    "YouTubeProcessor", 
    "WebScraper",
    "FileRegistryClient"
]