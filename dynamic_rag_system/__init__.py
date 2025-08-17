"""
Dynamic Educational RAG System

A sophisticated, modular RAG system specifically designed for educational content.
"""

__version__ = "1.0.0"
__author__ = "Dynamic RAG System"

# Make key components available at package level
from .core.config import get_config
from .core.models import (
    SourceDocument, BabyChunk, MotherSection, 
    ContentType, ChunkType, ProcessingStatus
)

__all__ = [
    "get_config",
    "SourceDocument", 
    "BabyChunk", 
    "MotherSection",
    "ContentType", 
    "ChunkType", 
    "ProcessingStatus"
]