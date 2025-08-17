"""
Chunking module for the Dynamic Educational RAG System.

Handles the intelligent chunking of educational content:
- Pattern-based section detection
- Hierarchical structure analysis  
- Baby chunk creation with educational metadata
- Chunk relationship tracking and versioning
"""

from .pattern_library import PatternLibrary
from .section_detector import SectionDetector
from .chunk_creator import ChunkCreator
from .chunk_manager import ChunkManager

__all__ = [
    "PatternLibrary",
    "SectionDetector",
    "ChunkCreator", 
    "ChunkManager"
]