"""
Configuration management for the Dynamic Educational RAG System.

Provides centralized configuration with environment-specific overrides,
validation, and educational domain-specific defaults.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    # File Registry Database (SQLite for development, PostgreSQL for production)
    registry_db_url: str = "sqlite:///file_registry.db"
    
    # Vector Database Settings
    vector_db_type: str = "faiss"  # faiss, pinecone, weaviate
    vector_db_path: str = "./vector_indexes"
    
    # Metadata Store
    metadata_db_url: str = "sqlite:///metadata.db"
    
    # Connection settings
    connection_pool_size: int = 10
    connection_timeout: int = 30


@dataclass
class ProcessingConfig:
    """Content processing configuration"""
    # Chunking settings
    min_chunk_size: int = 800
    max_chunk_size: int = 1200
    target_chunk_size: int = 1000
    overlap_percentage: int = 15
    
    # Section detection
    confidence_threshold: float = 0.7
    pattern_matching_threshold: float = 0.8
    
    # Quality control
    min_quality_score: float = 0.6
    require_human_review_threshold: float = 0.5
    
    # Batch processing
    default_batch_size: int = 10
    max_batch_size: int = 50
    processing_timeout_minutes: int = 60
    
    # Error handling
    max_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Educational validation
    validate_learning_objectives: bool = True
    validate_difficulty_progression: bool = True
    check_prerequisite_alignment: bool = True


@dataclass
class AIConfig:
    """AI service configuration"""
    # Primary AI provider
    primary_provider: str = "openai"  # openai, anthropic, cohere
    
    # API settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 2000
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    request_delay_seconds: float = 1.0
    
    # Cost management
    daily_budget_usd: float = 50.0
    cost_alert_threshold: float = 0.8
    
    # Quality settings
    require_confidence_score: bool = True
    min_extraction_confidence: float = 0.7
    enable_hallucination_detection: bool = True
    
    # Prompt management
    prompt_version: str = "1.0"
    enable_prompt_caching: bool = True
    prompt_optimization: bool = False


@dataclass
class EmbeddingConfig:
    """Embedding generation configuration"""
    # Primary embedding provider
    embedding_provider: str = "openai"  # openai, sentence_transformers, cohere
    
    # OpenAI embeddings
    openai_embedding_model: str = "text-embedding-3-large"
    openai_embedding_dimensions: int = 3072
    
    # Sentence Transformers
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    
    # Text preprocessing
    max_text_length: int = 8000
    preprocessing_strategy: str = "content_plus_metadata"  # content_only, metadata_only, content_plus_metadata
    
    # Embedding optimization
    normalize_embeddings: bool = True
    enable_dimensionality_reduction: bool = False
    target_dimensions: Optional[int] = None
    
    # Caching
    cache_embeddings: bool = True
    embedding_cache_ttl_hours: int = 24 * 7  # 1 week
    
    # Batch processing
    embedding_batch_size: int = 100
    max_concurrent_requests: int = 5


@dataclass
class SearchConfig:
    """Search and retrieval configuration"""
    # Default search parameters
    default_max_results: int = 10
    default_similarity_threshold: float = 0.7
    
    # Ranking weights
    similarity_weight: float = 0.4
    pedagogical_weight: float = 0.3
    quality_weight: float = 0.2
    freshness_weight: float = 0.1
    
    # Educational filtering
    enable_grade_level_filtering: bool = True
    enable_prerequisite_checking: bool = True
    enable_difficulty_matching: bool = True
    
    # Performance optimization
    enable_result_caching: bool = True
    cache_ttl_minutes: int = 30
    max_cache_size: int = 1000
    
    # Search expansion
    enable_concept_expansion: bool = True
    enable_synonym_expansion: bool = False
    max_expanded_terms: int = 5


@dataclass
class StorageConfig:
    """Storage configuration"""
    # Base directories
    base_data_dir: str = "./data"
    original_files_dir: str = "./data/original_files"
    processed_files_dir: str = "./data/processed"
    temp_dir: str = "./data/temp"
    backup_dir: str = "./data/backups"
    
    # File management
    max_file_size_mb: int = 100
    allowed_file_types: List[str] = field(default_factory=lambda: [
        ".pdf", ".txt", ".docx", ".html", ".md"
    ])
    
    # Backup settings
    enable_automatic_backup: bool = True
    backup_frequency_hours: int = 24
    max_backup_retention_days: int = 30
    
    # Cleanup settings
    temp_file_retention_hours: int = 2
    log_retention_days: int = 90


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_structured_logging: bool = True
    
    # Metrics
    enable_metrics: bool = True
    metrics_export_interval_seconds: int = 60
    
    # Health checks
    enable_health_checks: bool = True
    health_check_interval_seconds: int = 30
    
    # Alerting
    enable_alerting: bool = False
    alert_email: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    
    # Performance tracking
    track_processing_time: bool = True
    track_memory_usage: bool = True
    track_api_costs: bool = True


@dataclass
class SystemConfig:
    """Main system configuration"""
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # System metadata
    version: str = "1.0.0"
    system_name: str = "Dynamic Educational RAG"
    
    def __post_init__(self):
        """Validate configuration and set environment-specific defaults"""
        self._load_environment_variables()
        self._validate_configuration()
        self._ensure_directories()
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        # Database
        if os.getenv("REGISTRY_DB_URL"):
            self.database.registry_db_url = os.getenv("REGISTRY_DB_URL")
        
        # AI configuration
        if os.getenv("OPENAI_API_KEY"):
            self.ai.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Environment
        if os.getenv("ENVIRONMENT"):
            self.environment = Environment(os.getenv("ENVIRONMENT"))
            
        # Adjust settings based on environment
        if self.environment == Environment.PRODUCTION:
            self.debug = False
            self.database.registry_db_url = os.getenv("PRODUCTION_DB_URL", self.database.registry_db_url)
            self.ai.daily_budget_usd = float(os.getenv("AI_DAILY_BUDGET", "100.0"))
            self.monitoring.enable_alerting = True
        elif self.environment == Environment.DEVELOPMENT:
            self.debug = True
            self.ai.daily_budget_usd = 10.0  # Lower budget for development
    
    def _validate_configuration(self):
        """Validate configuration settings"""
        # Validate chunk sizes
        if self.processing.min_chunk_size >= self.processing.max_chunk_size:
            raise ValueError("min_chunk_size must be less than max_chunk_size")
        
        if not (self.processing.min_chunk_size <= self.processing.target_chunk_size <= self.processing.max_chunk_size):
            raise ValueError("target_chunk_size must be between min and max chunk sizes")
        
        # Validate overlap percentage
        if not (0 <= self.processing.overlap_percentage <= 50):
            raise ValueError("overlap_percentage must be between 0 and 50")
        
        # Validate threshold values
        if not (0 <= self.processing.confidence_threshold <= 1):
            raise ValueError("confidence_threshold must be between 0 and 1")
        
        # Validate AI budget
        if self.ai.daily_budget_usd <= 0:
            raise ValueError("daily_budget_usd must be positive")
        
        # Validate embedding dimensions
        if self.embedding.openai_embedding_dimensions <= 0:
            raise ValueError("embedding_dimensions must be positive")
    
    def _ensure_directories(self):
        """Create necessary directories"""
        directories = [
            self.storage.base_data_dir,
            self.storage.original_files_dir,
            self.storage.processed_files_dir,
            self.storage.temp_dir,
            self.storage.backup_dir,
            self.database.vector_db_path
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_file(cls, config_path: str) -> "SystemConfig":
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # TODO: Implement proper deserialization from dict
        # For now, return default config
        return cls()
    
    def to_file(self, config_path: str):
        """Save configuration to JSON file"""
        # TODO: Implement proper serialization to dict
        config_dict = {
            "environment": self.environment.value,
            "debug": self.debug,
            "version": self.version
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def get_educational_subjects(self) -> List[str]:
        """Get list of supported educational subjects"""
        return [
            "Physics", "Chemistry", "Biology", "Mathematics",
            "English", "Hindi", "Social Science", "Geography",
            "History", "Political Science", "Economics"
        ]
    
    def get_grade_levels(self) -> List[str]:
        """Get list of supported grade levels"""
        return [
            "6", "7", "8", "9", "10", "11", "12"
        ]
    
    def get_curricula(self) -> List[str]:
        """Get list of supported curricula"""
        return ["NCERT", "CBSE", "ICSE", "State Board"]


# Global configuration instance
_config_instance: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SystemConfig()
    return _config_instance


def set_config(config: SystemConfig):
    """Set the global configuration instance"""
    global _config_instance
    _config_instance = config


def load_config_from_file(config_path: str) -> SystemConfig:
    """Load and set configuration from file"""
    config = SystemConfig.from_file(config_path)
    set_config(config)
    return config


# Educational defaults for NCERT content
NCERT_DEFAULTS = {
    "subjects": ["Physics", "Chemistry", "Biology", "Mathematics"],
    "grade_levels": ["6", "7", "8", "9", "10", "11", "12"],
    "curriculum": "NCERT",
    "language": "en",
    "section_patterns": {
        "main_sections": r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]{8,60})(?:\n|$)',
        "activities": r'Activity\s*[_\-–—\s]*\s*(\d+\.\d+)',
        "examples": r'Example\s+(\d+\.\d+)',
        "figures": r'Fig\.\s*(\d+\.\d+):\s*(.+?)(?=\n(?:Fig\.|Activity|\d+\.\d+|$))'
    }
}