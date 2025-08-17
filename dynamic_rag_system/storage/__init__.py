"""
Storage module for the Dynamic Educational RAG System.

Handles all data persistence including:
- File registry and metadata
- Vector database operations
- Chunk storage and versioning
- Index management
"""

from .file_registry import FileRegistry
from .metadata_store import MetadataStore
from .vector_db import VectorDatabase
from .index_manager import IndexManager

__all__ = [
    "FileRegistry",
    "MetadataStore", 
    "VectorDatabase",
    "IndexManager"
]