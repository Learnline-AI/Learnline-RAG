"""
Core data models for the Dynamic Educational RAG System.

These models preserve the educational intelligence from the original system
while adding support for dynamic content management and multi-source ingestion.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class ContentType(Enum):
    """Types of content the system can process"""
    PDF = "pdf"
    YOUTUBE_TRANSCRIPT = "youtube_transcript"
    WEB_CONTENT = "web_content"
    TEXT_FILE = "text_file"
    IMAGE = "image"
    AUDIO = "audio"


class ChunkType(Enum):
    """Types of educational chunks"""
    ACTIVITY = "activity"
    EXAMPLE = "example"
    CONTENT = "content"
    SPECIAL_BOX = "special_box"
    INTRO = "intro"
    SUMMARY = "summary"
    EXERCISES = "exercises"


class ProcessingStatus(Enum):
    """Status of file processing"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UPDATING = "updating"
    ARCHIVED = "archived"


class DifficultyLevel(Enum):
    """Educational difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CognitiveLevel(Enum):
    """Bloom's taxonomy cognitive levels"""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


@dataclass
class SourceDocument:
    """Represents a source document in the system"""
    
    # Identity
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content_type: ContentType = ContentType.PDF
    
    # File information
    file_path: str = ""
    file_size: int = 0
    file_hash: str = ""  # For detecting changes
    
    # Educational metadata
    subject: str = ""
    grade_level: str = ""
    curriculum: str = ""  # e.g., "NCERT", "CBSE"
    language: str = "en"
    
    # Processing information
    status: ProcessingStatus = ProcessingStatus.QUEUED
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    # Source-specific metadata
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing statistics
    total_pages: int = 0
    total_characters: int = 0
    total_words: int = 0
    
    def __post_init__(self):
        """Validate and set defaults"""
        if not self.document_id:
            self.document_id = str(uuid.uuid4())


@dataclass
class MotherSection:
    """Represents a major section (e.g., 8.1, 8.2) in educational content"""
    
    # Identity
    section_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    
    # Section information
    section_number: str = ""  # e.g., "8.1", "Chapter_Intro"
    section_title: str = ""
    
    # Position in document
    start_pos: int = 0
    end_pos: int = 0
    page_number: int = 1
    
    # Content metrics
    content_length: int = 0
    word_count: int = 0
    confidence: float = 0.0
    
    # Educational structure
    special_content: Dict[str, List[Dict]] = field(default_factory=lambda: {
        'activities': [],
        'figures': [],
        'examples': [],
        'special_boxes': [],
        'mathematical_content': []
    })
    
    # Content preview
    content_preview: str = ""
    
    # Versioning
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BabyChunk:
    """Enhanced baby chunk with relationship tracking and versioning"""
    
    # Identity
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chunk_type: ChunkType = ChunkType.CONTENT
    
    # Relationships
    document_id: str = ""
    mother_section_id: str = ""
    mother_section: str = ""  # For backward compatibility
    mother_section_title: str = ""
    sequence_in_mother: int = 1
    
    # Content
    content: str = ""
    content_hash: str = ""  # For detecting changes
    
    # Position tracking
    position_in_document: Dict[str, int] = field(default_factory=dict)
    page_numbers: List[int] = field(default_factory=list)
    
    # Educational metadata (type-specific)
    activity_metadata: Optional[Dict] = None
    example_metadata: Optional[Dict] = None
    special_box_metadata: Optional[Dict] = None
    content_metadata: Optional[Dict] = None
    
    # AI-extracted metadata
    ai_metadata: Optional[Dict] = None
    
    # Quality and validation
    quality_score: Optional[Dict] = None
    validation_status: str = "pending"  # pending, validated, needs_review
    
    # Relationships to other chunks
    prerequisite_chunks: List[str] = field(default_factory=list)
    related_chunks: List[str] = field(default_factory=list)
    concept_tags: List[str] = field(default_factory=list)
    
    # Versioning and tracking
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_ai_analysis: Optional[datetime] = None
    
    # Embedding information
    embedding_id: Optional[str] = None
    embedding_version: int = 0
    
    def __post_init__(self):
        """Validate and set defaults"""
        if not self.chunk_id:
            self.chunk_id = str(uuid.uuid4())
        
        # Convert string chunk_type to enum if needed
        if isinstance(self.chunk_type, str):
            self.chunk_type = ChunkType(self.chunk_type)


@dataclass
class EmbeddingRecord:
    """Represents an embedding in the vector database"""
    
    # Identity
    embedding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chunk_id: str = ""
    
    # Embedding data
    embedding_vector: List[float] = field(default_factory=list)
    embedding_model: str = ""
    embedding_dimension: int = 0
    
    # Text that was embedded
    embedded_text: str = ""
    text_preprocessing_strategy: str = ""
    
    # Metadata for search
    search_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Versioning
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    
    # Quality metrics
    embedding_confidence: float = 1.0
    text_quality_score: float = 1.0


@dataclass
class ProcessingJob:
    """Represents a file processing job in the queue"""
    
    # Identity
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    
    # Job configuration
    job_type: str = "full_processing"  # full_processing, update, reindex
    priority: int = 5  # 1-10, higher is more urgent
    
    # Processing parameters
    processing_config: Dict[str, Any] = field(default_factory=dict)
    
    # Status tracking
    status: ProcessingStatus = ProcessingStatus.QUEUED
    progress_percentage: float = 0.0
    current_stage: str = ""
    
    # Error handling
    retry_count: int = 0
    max_retries: int = 3
    error_messages: List[str] = field(default_factory=list)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    # Resource usage
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    processing_time_seconds: float = 0.0


@dataclass
class SearchQuery:
    """Represents a search query with educational context"""
    
    # Query information
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_text: str = ""
    
    # Educational context
    grade_level: Optional[str] = None
    subject: Optional[str] = None
    curriculum: Optional[str] = None
    learning_objective: Optional[str] = None
    
    # Search parameters
    chunk_types: List[ChunkType] = field(default_factory=list)
    difficulty_levels: List[DifficultyLevel] = field(default_factory=list)
    cognitive_levels: List[CognitiveLevel] = field(default_factory=list)
    
    # Retrieval settings
    max_results: int = 10
    similarity_threshold: float = 0.7
    
    # Query metadata
    created_at: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class SearchResult:
    """Represents a search result with educational relevance"""
    
    # Result information
    chunk: BabyChunk
    similarity_score: float = 0.0
    relevance_score: float = 0.0
    
    # Educational relevance
    pedagogical_fit: float = 0.0  # How well it fits the educational context
    prerequisite_alignment: float = 0.0
    difficulty_match: float = 0.0
    
    # Ranking factors
    content_quality: float = 0.0
    freshness_score: float = 0.0
    usage_popularity: float = 0.0
    
    # Explanation
    match_explanation: str = ""
    educational_rationale: str = ""


@dataclass
class ConceptNode:
    """Represents a concept in the educational knowledge graph"""
    
    # Identity
    concept_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    concept_name: str = ""
    
    # Educational properties
    definition: str = ""
    grade_levels: List[str] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    
    # Relationships
    prerequisite_concepts: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    child_concepts: List[str] = field(default_factory=list)
    
    # Associated chunks
    chunks: List[str] = field(default_factory=list)  # chunk_ids
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0


# Type aliases for convenience
ChunkID = str
DocumentID = str
EmbeddingID = str
ConceptID = str

# Collection types
ChunkCollection = List[BabyChunk]
EmbeddingCollection = List[EmbeddingRecord]
SearchResults = List[SearchResult]