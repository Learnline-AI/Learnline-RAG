"""
File Registry - Tracks all documents in the system.

Maintains a database of all processed and queued files with metadata,
processing status, relationships, and change detection.
"""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import json
import logging

from ..core.models import (
    SourceDocument, ProcessingJob, ProcessingStatus, 
    ContentType, ChunkID, DocumentID
)
from ..core.config import get_config
from ..core.exceptions import (
    DatabaseError, ConnectionError, DataIntegrityError,
    FileProcessingError
)

logger = logging.getLogger(__name__)


class FileRegistry:
    """
    Manages the registry of all files in the RAG system.
    
    Provides functionality for:
    - Tracking file processing status
    - Detecting file changes
    - Managing relationships between files
    - Queuing processing jobs
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize file registry with database"""
        self.config = get_config()
        self.db_path = db_path or self.config.database.registry_db_url.replace("sqlite:///", "")
        self._connection = None
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(
                    self.db_path,
                    timeout=self.config.database.connection_timeout,
                    check_same_thread=False
                )
                self._connection.row_factory = sqlite3.Row  # Enable dict-like access
                # Enable foreign keys
                self._connection.execute("PRAGMA foreign_keys = ON")
            except sqlite3.Error as e:
                raise ConnectionError("file_registry", self.db_path) from e
        
        return self._connection
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        
        try:
            # Source documents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS source_documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    file_path TEXT UNIQUE NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_hash TEXT NOT NULL,
                    subject TEXT,
                    grade_level TEXT,
                    curriculum TEXT,
                    language TEXT DEFAULT 'en',
                    status TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    total_pages INTEGER DEFAULT 0,
                    total_characters INTEGER DEFAULT 0,
                    total_words INTEGER DEFAULT 0,
                    source_metadata TEXT  -- JSON
                )
            """)
            
            # Processing jobs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_jobs (
                    job_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    job_type TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    status TEXT NOT NULL,
                    progress_percentage REAL DEFAULT 0.0,
                    current_stage TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    error_messages TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    estimated_completion TIMESTAMP,
                    estimated_cost REAL DEFAULT 0.0,
                    actual_cost REAL DEFAULT 0.0,
                    processing_time_seconds REAL DEFAULT 0.0,
                    processing_config TEXT,  -- JSON
                    FOREIGN KEY (document_id) REFERENCES source_documents (document_id)
                )
            """)
            
            # File relationships table (for tracking dependencies)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_document_id TEXT NOT NULL,
                    child_document_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,  -- 'prerequisite', 'related', 'continuation'
                    strength REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_document_id) REFERENCES source_documents (document_id),
                    FOREIGN KEY (child_document_id) REFERENCES source_documents (document_id),
                    UNIQUE(parent_document_id, child_document_id, relationship_type)
                )
            """)
            
            # Change log table (for tracking modifications)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,  -- 'created', 'updated', 'deleted', 'processed'
                    old_values TEXT,  -- JSON
                    new_values TEXT,  -- JSON
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered_by TEXT,  -- user_id or 'system'
                    FOREIGN KEY (document_id) REFERENCES source_documents (document_id)
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON source_documents (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_content_type ON source_documents (content_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_subject_grade ON source_documents (subject, grade_level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_priority ON processing_jobs (priority DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_parent ON file_relationships (parent_document_id)")
            
            conn.commit()
            logger.info("File registry database initialized successfully")
            
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to initialize file registry database: {e}")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for change detection"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (IOError, OSError) as e:
            raise FileProcessingError(f"Cannot calculate hash for file: {e}", file_path)
    
    def register_document(self, 
                         file_path: str, 
                         title: str = None,
                         content_type: ContentType = None,
                         educational_metadata: Dict[str, str] = None) -> SourceDocument:
        """
        Register a new document in the system.
        
        Args:
            file_path: Path to the file
            title: Document title (extracted from file if not provided)
            content_type: Type of content
            educational_metadata: Subject, grade level, etc.
            
        Returns:
            SourceDocument object with assigned document_id
        """
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise FileProcessingError(f"File does not exist: {file_path}", file_path)
        
        # Auto-detect content type if not provided
        if content_type is None:
            content_type = self._detect_content_type(path.suffix.lower())
        
        # Extract basic file information
        file_size = path.stat().st_size
        file_hash = self.calculate_file_hash(file_path)
        
        # Set default title if not provided
        if title is None:
            title = path.stem
        
        # Create document object
        doc = SourceDocument(
            title=title,
            content_type=content_type,
            file_path=str(path.absolute()),
            file_size=file_size,
            file_hash=file_hash,
            subject=educational_metadata.get("subject", "") if educational_metadata else "",
            grade_level=educational_metadata.get("grade_level", "") if educational_metadata else "",
            curriculum=educational_metadata.get("curriculum", "") if educational_metadata else "",
            language=educational_metadata.get("language", "en") if educational_metadata else "en",
            status=ProcessingStatus.QUEUED,
            source_metadata=educational_metadata or {}
        )
        
        # Insert into database
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO source_documents (
                    document_id, title, content_type, file_path, file_size, file_hash,
                    subject, grade_level, curriculum, language, status, version,
                    created_at, updated_at, source_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.document_id, doc.title, doc.content_type.value, doc.file_path,
                doc.file_size, doc.file_hash, doc.subject, doc.grade_level,
                doc.curriculum, doc.language, doc.status.value, doc.version,
                doc.created_at, doc.updated_at, json.dumps(doc.source_metadata)
            ))
            
            # Log the registration
            self._log_change(doc.document_id, "created", {}, {
                "title": doc.title,
                "file_path": doc.file_path,
                "status": doc.status.value
            })
            
            conn.commit()
            logger.info(f"Registered document {doc.document_id}: {doc.title}")
            return doc
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: source_documents.file_path" in str(e):
                # File already registered, return existing document
                return self.get_document_by_path(file_path)
            else:
                raise DataIntegrityError(f"Failed to register document: {e}")
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Database error during document registration: {e}")
    
    def get_document(self, document_id: DocumentID) -> Optional[SourceDocument]:
        """Get document by ID"""
        conn = self._get_connection()
        
        try:
            cursor = conn.execute("""
                SELECT * FROM source_documents WHERE document_id = ?
            """, (document_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_document(row)
            return None
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve document {document_id}: {e}")
    
    def get_document_by_path(self, file_path: str) -> Optional[SourceDocument]:
        """Get document by file path"""
        conn = self._get_connection()
        
        try:
            cursor = conn.execute("""
                SELECT * FROM source_documents WHERE file_path = ?
            """, (str(Path(file_path).absolute()),))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_document(row)
            return None
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve document by path {file_path}: {e}")
    
    def check_file_changes(self, document_id: DocumentID) -> bool:
        """
        Check if file has changed since last processing.
        
        Returns True if file has changed, False otherwise.
        """
        doc = self.get_document(document_id)
        if not doc:
            raise FileProcessingError(f"Document {document_id} not found")
        
        if not Path(doc.file_path).exists():
            logger.warning(f"File no longer exists: {doc.file_path}")
            return True
        
        current_hash = self.calculate_file_hash(doc.file_path)
        return current_hash != doc.file_hash
    
    def update_document_status(self, 
                              document_id: DocumentID, 
                              status: ProcessingStatus,
                              processing_stats: Dict[str, Any] = None):
        """Update document processing status and stats"""
        conn = self._get_connection()
        
        try:
            # Get current document for change logging
            old_doc = self.get_document(document_id)
            if not old_doc:
                raise FileProcessingError(f"Document {document_id} not found")
            
            # Update document
            update_fields = ["status = ?", "updated_at = ?"]
            update_values = [status.value, datetime.now()]
            
            if status == ProcessingStatus.COMPLETED:
                update_fields.append("processed_at = ?")
                update_values.append(datetime.now())
            
            if processing_stats:
                if "total_pages" in processing_stats:
                    update_fields.append("total_pages = ?")
                    update_values.append(processing_stats["total_pages"])
                if "total_characters" in processing_stats:
                    update_fields.append("total_characters = ?")
                    update_values.append(processing_stats["total_characters"])
                if "total_words" in processing_stats:
                    update_fields.append("total_words = ?")
                    update_values.append(processing_stats["total_words"])
            
            update_values.append(document_id)
            
            conn.execute(f"""
                UPDATE source_documents 
                SET {', '.join(update_fields)}
                WHERE document_id = ?
            """, update_values)
            
            # Log the change
            self._log_change(document_id, "updated", 
                           {"status": old_doc.status.value},
                           {"status": status.value})
            
            conn.commit()
            logger.info(f"Updated document {document_id} status to {status.value}")
            
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to update document status: {e}")
    
    def create_processing_job(self, 
                             document_id: DocumentID,
                             job_type: str = "full_processing",
                             priority: int = 5,
                             processing_config: Dict[str, Any] = None) -> ProcessingJob:
        """Create a new processing job"""
        job = ProcessingJob(
            document_id=document_id,
            job_type=job_type,
            priority=priority,
            processing_config=processing_config or {}
        )
        
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO processing_jobs (
                    job_id, document_id, job_type, priority, status,
                    processing_config, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, job.document_id, job.job_type, job.priority,
                job.status.value, json.dumps(job.processing_config), job.created_at
            ))
            
            conn.commit()
            logger.info(f"Created processing job {job.job_id} for document {document_id}")
            return job
            
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to create processing job: {e}")
    
    def get_next_job(self) -> Optional[ProcessingJob]:
        """Get the next job to process (highest priority, oldest first)"""
        conn = self._get_connection()
        
        try:
            cursor = conn.execute("""
                SELECT * FROM processing_jobs 
                WHERE status = 'queued'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return self._row_to_job(row)
            return None
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get next job: {e}")
    
    def update_job_status(self, 
                         job_id: str,
                         status: ProcessingStatus,
                         progress: float = None,
                         current_stage: str = None,
                         error_message: str = None):
        """Update processing job status"""
        conn = self._get_connection()
        
        try:
            update_fields = ["status = ?", "updated_at = ?"]
            update_values = [status.value, datetime.now()]
            
            if progress is not None:
                update_fields.append("progress_percentage = ?")
                update_values.append(progress)
            
            if current_stage:
                update_fields.append("current_stage = ?")
                update_values.append(current_stage)
            
            if status == ProcessingStatus.PROCESSING and not self._job_has_started(job_id):
                update_fields.append("started_at = ?")
                update_values.append(datetime.now())
            
            if status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                update_fields.append("completed_at = ?")
                update_values.append(datetime.now())
            
            if error_message:
                # Get existing errors and append new one
                existing_errors = self._get_job_errors(job_id)
                existing_errors.append(error_message)
                update_fields.append("error_messages = ?")
                update_values.append(json.dumps(existing_errors))
            
            update_values.append(job_id)
            
            conn.execute(f"""
                UPDATE processing_jobs 
                SET {', '.join(update_fields)}
                WHERE job_id = ?
            """, update_values)
            
            conn.commit()
            logger.info(f"Updated job {job_id} status to {status.value}")
            
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to update job status: {e}")
    
    def get_documents_by_criteria(self,
                                 status: ProcessingStatus = None,
                                 content_type: ContentType = None,
                                 subject: str = None,
                                 grade_level: str = None,
                                 limit: int = None) -> List[SourceDocument]:
        """Get documents matching specified criteria"""
        conn = self._get_connection()
        
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("status = ?")
            params.append(status.value)
        
        if content_type:
            where_clauses.append("content_type = ?")
            params.append(content_type.value)
        
        if subject:
            where_clauses.append("subject = ?")
            params.append(subject)
        
        if grade_level:
            where_clauses.append("grade_level = ?")
            params.append(grade_level)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        limit_clause = f" LIMIT {limit}" if limit else ""
        
        try:
            cursor = conn.execute(f"""
                SELECT * FROM source_documents 
                WHERE {where_clause}
                ORDER BY created_at DESC
                {limit_clause}
            """, params)
            
            return [self._row_to_document(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to query documents: {e}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics for monitoring"""
        conn = self._get_connection()
        
        try:
            # Document statistics
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM source_documents 
                GROUP BY status
            """)
            doc_stats = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            # Job statistics
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM processing_jobs 
                GROUP BY status
            """)
            job_stats = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            # Recent activity
            cursor = conn.execute("""
                SELECT COUNT(*) as count 
                FROM source_documents 
                WHERE created_at > datetime('now', '-24 hours')
            """)
            recent_docs = cursor.fetchone()["count"]
            
            cursor = conn.execute("""
                SELECT COUNT(*) as count 
                FROM processing_jobs 
                WHERE created_at > datetime('now', '-24 hours')
            """)
            recent_jobs = cursor.fetchone()["count"]
            
            return {
                "document_counts": doc_stats,
                "job_counts": job_stats,
                "recent_activity": {
                    "documents_added_24h": recent_docs,
                    "jobs_created_24h": recent_jobs
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get processing statistics: {e}")
    
    def _detect_content_type(self, file_extension: str) -> ContentType:
        """Auto-detect content type from file extension"""
        type_mapping = {
            ".pdf": ContentType.PDF,
            ".txt": ContentType.TEXT_FILE,
            ".md": ContentType.TEXT_FILE,
            ".docx": ContentType.TEXT_FILE,
            ".html": ContentType.WEB_CONTENT,
            ".htm": ContentType.WEB_CONTENT,
            ".jpg": ContentType.IMAGE,
            ".jpeg": ContentType.IMAGE,
            ".png": ContentType.IMAGE,
            ".mp3": ContentType.AUDIO,
            ".wav": ContentType.AUDIO,
            ".mp4": ContentType.AUDIO  # Video with audio
        }
        
        return type_mapping.get(file_extension, ContentType.TEXT_FILE)
    
    def _row_to_document(self, row: sqlite3.Row) -> SourceDocument:
        """Convert database row to SourceDocument object"""
        return SourceDocument(
            document_id=row["document_id"],
            title=row["title"],
            content_type=ContentType(row["content_type"]),
            file_path=row["file_path"],
            file_size=row["file_size"],
            file_hash=row["file_hash"],
            subject=row["subject"],
            grade_level=row["grade_level"],
            curriculum=row["curriculum"],
            language=row["language"],
            status=ProcessingStatus(row["status"]),
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
            total_pages=row["total_pages"],
            total_characters=row["total_characters"],
            total_words=row["total_words"],
            source_metadata=json.loads(row["source_metadata"]) if row["source_metadata"] else {}
        )
    
    def _row_to_job(self, row: sqlite3.Row) -> ProcessingJob:
        """Convert database row to ProcessingJob object"""
        return ProcessingJob(
            job_id=row["job_id"],
            document_id=row["document_id"],
            job_type=row["job_type"],
            priority=row["priority"],
            status=ProcessingStatus(row["status"]),
            progress_percentage=row["progress_percentage"],
            current_stage=row["current_stage"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            error_messages=json.loads(row["error_messages"]) if row["error_messages"] else [],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            estimated_completion=datetime.fromisoformat(row["estimated_completion"]) if row["estimated_completion"] else None,
            estimated_cost=row["estimated_cost"],
            actual_cost=row["actual_cost"],
            processing_time_seconds=row["processing_time_seconds"],
            processing_config=json.loads(row["processing_config"]) if row["processing_config"] else {}
        )
    
    def _log_change(self, 
                   document_id: DocumentID, 
                   change_type: str, 
                   old_values: Dict[str, Any], 
                   new_values: Dict[str, Any],
                   triggered_by: str = "system"):
        """Log document changes for audit trail"""
        conn = self._get_connection()
        
        try:
            conn.execute("""
                INSERT INTO change_log (
                    document_id, change_type, old_values, new_values, triggered_by
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                document_id, change_type, 
                json.dumps(old_values), json.dumps(new_values), triggered_by
            ))
        except sqlite3.Error as e:
            logger.warning(f"Failed to log change for document {document_id}: {e}")
    
    def _job_has_started(self, job_id: str) -> bool:
        """Check if job has already been marked as started"""
        conn = self._get_connection()
        cursor = conn.execute("SELECT started_at FROM processing_jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        return row and row["started_at"] is not None
    
    def _get_job_errors(self, job_id: str) -> List[str]:
        """Get existing error messages for a job"""
        conn = self._get_connection()
        cursor = conn.execute("SELECT error_messages FROM processing_jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if row and row["error_messages"]:
            return json.loads(row["error_messages"])
        return []
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("File registry database connection closed")
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close()