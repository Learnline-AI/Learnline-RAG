"""
Custom exceptions for the Dynamic Educational RAG System.

Provides specific exception types for different system components
with educational context and recovery guidance.
"""

from typing import List, Optional, Dict, Any


class RAGSystemException(Exception):
    """Base exception for all RAG system errors"""
    
    def __init__(self, message: str, error_code: str = None, context: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "RAG_ERROR"
        self.context = context or {}
        super().__init__(self.message)


# Configuration Exceptions
class ConfigurationError(RAGSystemException):
    """Raised when there's a configuration error"""
    
    def __init__(self, message: str, config_section: str = None, **kwargs):
        self.config_section = config_section
        super().__init__(message, "CONFIG_ERROR", kwargs)


class ValidationError(RAGSystemException):
    """Raised when validation fails"""
    
    def __init__(self, message: str, validation_type: str = None, **kwargs):
        self.validation_type = validation_type
        super().__init__(message, "VALIDATION_ERROR", kwargs)


# File Processing Exceptions
class FileProcessingError(RAGSystemException):
    """Base class for file processing errors"""
    
    def __init__(self, message: str, file_path: str = None, **kwargs):
        self.file_path = file_path
        super().__init__(message, "FILE_PROCESSING_ERROR", kwargs)


class UnsupportedFileTypeError(FileProcessingError):
    """Raised when file type is not supported"""
    
    def __init__(self, file_path: str, file_type: str, supported_types: List[str] = None):
        self.file_type = file_type
        self.supported_types = supported_types or []
        message = f"Unsupported file type '{file_type}' for file '{file_path}'. Supported types: {self.supported_types}"
        super().__init__(message, file_path, error_code="UNSUPPORTED_FILE_TYPE")


class CorruptedFileError(FileProcessingError):
    """Raised when file is corrupted or unreadable"""
    
    def __init__(self, file_path: str, corruption_details: str = None):
        self.corruption_details = corruption_details
        message = f"File '{file_path}' is corrupted or unreadable"
        if corruption_details:
            message += f": {corruption_details}"
        super().__init__(message, file_path, error_code="CORRUPTED_FILE")


class FileSizeError(FileProcessingError):
    """Raised when file size exceeds limits"""
    
    def __init__(self, file_path: str, file_size: int, max_size: int):
        self.file_size = file_size
        self.max_size = max_size
        message = f"File '{file_path}' size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        super().__init__(message, file_path, error_code="FILE_TOO_LARGE")


# Educational Content Exceptions
class EducationalContentError(RAGSystemException):
    """Base class for educational content errors"""
    
    def __init__(self, message: str, content_type: str = None, **kwargs):
        self.content_type = content_type
        super().__init__(message, "EDUCATIONAL_CONTENT_ERROR", kwargs)


class SectionDetectionError(EducationalContentError):
    """Raised when section detection fails"""
    
    def __init__(self, message: str, document_id: str = None, confidence: float = None):
        self.document_id = document_id
        self.confidence = confidence
        super().__init__(message, "section_detection", error_code="SECTION_DETECTION_FAILED")


class ChunkingError(EducationalContentError):
    """Raised when chunking process fails"""
    
    def __init__(self, message: str, section_id: str = None, chunk_type: str = None):
        self.section_id = section_id
        self.chunk_type = chunk_type
        super().__init__(message, "chunking", error_code="CHUNKING_FAILED")


class MetadataExtractionError(EducationalContentError):
    """Raised when AI metadata extraction fails"""
    
    def __init__(self, message: str, chunk_id: str = None, extraction_type: str = None, retry_count: int = 0):
        self.chunk_id = chunk_id
        self.extraction_type = extraction_type
        self.retry_count = retry_count
        super().__init__(message, "metadata_extraction", error_code="METADATA_EXTRACTION_FAILED")


class QualityValidationError(EducationalContentError):
    """Raised when quality validation fails"""
    
    def __init__(self, message: str, quality_score: float = None, validation_issues: List[str] = None):
        self.quality_score = quality_score
        self.validation_issues = validation_issues or []
        super().__init__(message, "quality_validation", error_code="QUALITY_VALIDATION_FAILED")


# AI Service Exceptions
class AIServiceError(RAGSystemException):
    """Base class for AI service errors"""
    
    def __init__(self, message: str, provider: str = None, **kwargs):
        self.provider = provider
        super().__init__(message, "AI_SERVICE_ERROR", kwargs)


class APIRateLimitError(AIServiceError):
    """Raised when API rate limit is exceeded"""
    
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {provider}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, provider, error_code="RATE_LIMIT_EXCEEDED")


class APIQuotaExceededError(AIServiceError):
    """Raised when API quota is exceeded"""
    
    def __init__(self, provider: str, quota_type: str = "daily"):
        self.quota_type = quota_type
        message = f"{quota_type.title()} quota exceeded for {provider}"
        super().__init__(message, provider, error_code="QUOTA_EXCEEDED")


class InvalidAPIKeyError(AIServiceError):
    """Raised when API key is invalid"""
    
    def __init__(self, provider: str):
        message = f"Invalid API key for {provider}"
        super().__init__(message, provider, error_code="INVALID_API_KEY")


class AIResponseError(AIServiceError):
    """Raised when AI response is invalid or unusable"""
    
    def __init__(self, message: str, provider: str, response_content: str = None):
        self.response_content = response_content
        super().__init__(message, provider, error_code="INVALID_AI_RESPONSE")


# Database Exceptions
class DatabaseError(RAGSystemException):
    """Base class for database errors"""
    
    def __init__(self, message: str, database_type: str = None, **kwargs):
        self.database_type = database_type
        super().__init__(message, "DATABASE_ERROR", kwargs)


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""
    
    def __init__(self, database_type: str, connection_string: str = None):
        self.connection_string = connection_string
        message = f"Failed to connect to {database_type} database"
        super().__init__(message, database_type, error_code="CONNECTION_FAILED")


class DataIntegrityError(DatabaseError):
    """Raised when data integrity is compromised"""
    
    def __init__(self, message: str, table_name: str = None, record_id: str = None):
        self.table_name = table_name
        self.record_id = record_id
        super().__init__(message, error_code="DATA_INTEGRITY_ERROR")


# Embedding Exceptions
class EmbeddingError(RAGSystemException):
    """Base class for embedding errors"""
    
    def __init__(self, message: str, embedding_provider: str = None, **kwargs):
        self.embedding_provider = embedding_provider
        super().__init__(message, "EMBEDDING_ERROR", kwargs)


class EmbeddingGenerationError(EmbeddingError):
    """Raised when embedding generation fails"""
    
    def __init__(self, message: str, text_length: int = None, **kwargs):
        self.text_length = text_length
        super().__init__(message, error_code="EMBEDDING_GENERATION_FAILED", **kwargs)


class VectorDatabaseError(EmbeddingError):
    """Raised when vector database operations fail"""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        self.operation = operation
        super().__init__(message, error_code="VECTOR_DB_ERROR", **kwargs)


# Search and Retrieval Exceptions
class SearchError(RAGSystemException):
    """Base class for search errors"""
    
    def __init__(self, message: str, query: str = None, **kwargs):
        self.query = query
        super().__init__(message, "SEARCH_ERROR", kwargs)


class InvalidQueryError(SearchError):
    """Raised when search query is invalid"""
    
    def __init__(self, query: str, validation_issues: List[str]):
        self.validation_issues = validation_issues
        message = f"Invalid query: {', '.join(validation_issues)}"
        super().__init__(message, query, error_code="INVALID_QUERY")


class NoResultsError(SearchError):
    """Raised when search returns no results"""
    
    def __init__(self, query: str, filters_applied: Dict[str, Any] = None):
        self.filters_applied = filters_applied or {}
        message = f"No results found for query: '{query}'"
        super().__init__(message, query, error_code="NO_RESULTS")


# Pipeline Exceptions
class PipelineError(RAGSystemException):
    """Base class for pipeline errors"""
    
    def __init__(self, message: str, pipeline_stage: str = None, **kwargs):
        self.pipeline_stage = pipeline_stage
        super().__init__(message, "PIPELINE_ERROR", kwargs)


class JobExecutionError(PipelineError):
    """Raised when job execution fails"""
    
    def __init__(self, message: str, job_id: str, stage: str = None, retry_count: int = 0):
        self.job_id = job_id
        self.retry_count = retry_count
        super().__init__(message, stage, error_code="JOB_EXECUTION_FAILED")


class ResourceExhaustionError(PipelineError):
    """Raised when system resources are exhausted"""
    
    def __init__(self, resource_type: str, current_usage: str = None):
        self.resource_type = resource_type
        self.current_usage = current_usage
        message = f"Resource exhausted: {resource_type}"
        if current_usage:
            message += f" (current usage: {current_usage})"
        super().__init__(message, error_code="RESOURCE_EXHAUSTED")


# Recovery suggestions
RECOVERY_SUGGESTIONS = {
    "CONFIG_ERROR": [
        "Check configuration file syntax and values",
        "Verify environment variables are set correctly",
        "Ensure all required configuration sections are present"
    ],
    "UNSUPPORTED_FILE_TYPE": [
        "Convert file to a supported format",
        "Check if file extension matches content type",
        "Add support for new file type if needed"
    ],
    "RATE_LIMIT_EXCEEDED": [
        "Wait for rate limit reset",
        "Reduce batch size",
        "Implement exponential backoff",
        "Consider upgrading API plan"
    ],
    "QUOTA_EXCEEDED": [
        "Wait for quota reset",
        "Upgrade API plan",
        "Optimize prompts to reduce token usage",
        "Implement cost monitoring"
    ],
    "SECTION_DETECTION_FAILED": [
        "Review document structure",
        "Adjust pattern matching thresholds",
        "Add custom patterns for document type",
        "Consider manual section annotation"
    ],
    "QUALITY_VALIDATION_FAILED": [
        "Review extraction quality",
        "Adjust quality thresholds",
        "Improve prompt templates",
        "Enable human review workflow"
    ]
}


def get_recovery_suggestions(error_code: str) -> List[str]:
    """Get recovery suggestions for an error code"""
    return RECOVERY_SUGGESTIONS.get(error_code, [
        "Check system logs for more details",
        "Retry the operation",
        "Contact system administrator if problem persists"
    ])


class ErrorRecoveryHelper:
    """Helper class for error recovery and troubleshooting"""
    
    @staticmethod
    def format_error_message(exception: RAGSystemException) -> str:
        """Format a comprehensive error message with context and suggestions"""
        message = f"Error: {exception.message}\n"
        message += f"Error Code: {exception.error_code}\n"
        
        if exception.context:
            message += f"Context: {exception.context}\n"
        
        suggestions = get_recovery_suggestions(exception.error_code)
        if suggestions:
            message += "\nRecovery Suggestions:\n"
            for i, suggestion in enumerate(suggestions, 1):
                message += f"  {i}. {suggestion}\n"
        
        return message
    
    @staticmethod
    def should_retry(exception: RAGSystemException, current_retry: int, max_retries: int) -> bool:
        """Determine if an operation should be retried based on the exception type"""
        if current_retry >= max_retries:
            return False
        
        # Retry for temporary errors
        retryable_errors = [
            "RATE_LIMIT_EXCEEDED",
            "CONNECTION_FAILED",
            "EMBEDDING_GENERATION_FAILED",
            "AI_SERVICE_ERROR"
        ]
        
        return exception.error_code in retryable_errors
    
    @staticmethod
    def get_retry_delay(exception: RAGSystemException, retry_count: int) -> int:
        """Get appropriate retry delay based on exception type and retry count"""
        if isinstance(exception, APIRateLimitError) and exception.retry_after:
            return exception.retry_after
        
        # Exponential backoff with jitter
        base_delay = 2 ** retry_count
        return min(base_delay + (base_delay * 0.1), 300)  # Max 5 minutes