"""
Chunk Manager - Handles chunk versioning, relationships, and lifecycle management.

Provides advanced chunk management capabilities:
- Version tracking and comparison
- Relationship mapping between chunks
- Concept tagging and knowledge graph building
- Chunk update and migration strategies
"""

import hashlib
import json
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import sqlite3
import logging

from ..core.models import (
    BabyChunk, ChunkID, DocumentID, ConceptID, 
    ChunkType, ChunkCollection
)
from ..core.config import get_config
from ..core.exceptions import DatabaseError, DataIntegrityError
from ..storage.file_registry import FileRegistry

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between chunks"""
    PREREQUISITE = "prerequisite"  # Chunk A is prerequisite for B
    RELATED = "related"           # Chunks are topically related
    CONTINUATION = "continuation"  # Chunk B continues from A
    EXAMPLE_OF = "example_of"     # Chunk A is example of concept in B
    EXPLAINS = "explains"         # Chunk A explains concept in B
    CONTRADICTS = "contradicts"   # Chunks present conflicting information
    BUILDS_ON = "builds_on"      # Chunk B builds upon concepts in A


@dataclass
class ChunkRelationship:
    """Represents a relationship between two chunks"""
    relationship_id: str
    source_chunk_id: ChunkID
    target_chunk_id: ChunkID
    relationship_type: RelationshipType
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]
    created_at: datetime
    created_by: str  # 'system' or user_id
    validated: bool = False


@dataclass 
class ChunkVersion:
    """Represents a version of a chunk"""
    version_id: str
    chunk_id: ChunkID
    version_number: int
    content_hash: str
    content: str
    metadata_hash: str
    ai_metadata: Optional[Dict]
    created_at: datetime
    changes_summary: str
    previous_version_id: Optional[str] = None


@dataclass
class ConceptMapping:
    """Maps concepts to chunks"""
    concept_id: ConceptID
    concept_name: str
    chunk_ids: Set[ChunkID]
    confidence: float
    evidence: List[str]  # Text snippets that support this mapping
    created_at: datetime
    last_updated: datetime


class ChunkManager:
    """
    Advanced chunk management with versioning and relationships.
    
    Handles:
    - Chunk versioning and change tracking
    - Relationship mapping and validation
    - Concept extraction and tagging
    - Knowledge graph construction
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.config = get_config()
        self.db_path = db_path or "chunk_manager.db"
        self._connection = None
        
        # Caches for performance
        self._chunk_cache: Dict[ChunkID, BabyChunk] = {}
        self._relationship_cache: Dict[ChunkID, List[ChunkRelationship]] = {}
        self._concept_cache: Dict[ConceptID, ConceptMapping] = {}
        
        # Initialize database
        self._initialize_database()
        
        logger.info("Chunk manager initialized with versioning and relationship tracking")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection
    
    def _initialize_database(self):
        """Create database tables for chunk management"""
        conn = self._get_connection()
        
        try:
            # Chunk versions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_versions (
                    version_id TEXT PRIMARY KEY,
                    chunk_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_hash TEXT NOT NULL,
                    ai_metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    changes_summary TEXT,
                    previous_version_id TEXT,
                    UNIQUE(chunk_id, version_number),
                    FOREIGN KEY (previous_version_id) REFERENCES chunk_versions (version_id)
                )
            """)
            
            # Chunk relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_relationships (
                    relationship_id TEXT PRIMARY KEY,
                    source_chunk_id TEXT NOT NULL,
                    target_chunk_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    confidence REAL NOT NULL,
                    metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT NOT NULL,
                    validated BOOLEAN DEFAULT FALSE,
                    UNIQUE(source_chunk_id, target_chunk_id, relationship_type)
                )
            """)
            
            # Concept mappings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS concept_mappings (
                    concept_id TEXT NOT NULL,
                    concept_name TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (concept_id, chunk_id)
                )
            """)
            
            # Chunk metadata index for fast lookups
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_metadata_index (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_type TEXT NOT NULL,
                    mother_section TEXT,
                    subject TEXT,
                    grade_level TEXT,
                    concepts TEXT,  -- JSON array
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_versions_chunk_id ON chunk_versions (chunk_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON chunk_relationships (source_chunk_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON chunk_relationships (target_chunk_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_concepts_chunk ON concept_mappings (chunk_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_concepts_name ON concept_mappings (concept_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metadata_document ON chunk_metadata_index (document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metadata_type ON chunk_metadata_index (chunk_type)")
            
            conn.commit()
            logger.info("Chunk manager database initialized")
            
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to initialize chunk manager database: {e}")
    
    def store_chunk_version(self, 
                           chunk: BabyChunk, 
                           changes_summary: str = "") -> ChunkVersion:
        """
        Store a new version of a chunk.
        
        Args:
            chunk: BabyChunk to store
            changes_summary: Description of what changed
            
        Returns:
            ChunkVersion object for the stored version
        """
        conn = self._get_connection()
        
        try:
            # Calculate content and metadata hashes
            content_hash = self._calculate_content_hash(chunk.content)
            metadata_hash = self._calculate_metadata_hash(chunk)
            
            # Check if this exact version already exists
            existing_version = self._get_version_by_hashes(chunk.chunk_id, content_hash, metadata_hash)
            if existing_version:
                logger.debug(f"Chunk {chunk.chunk_id} unchanged, returning existing version")
                return existing_version
            
            # Get next version number
            version_number = self._get_next_version_number(chunk.chunk_id)
            
            # Get previous version ID
            previous_version = self._get_latest_version(chunk.chunk_id)
            previous_version_id = previous_version.version_id if previous_version else None
            
            # Create new version
            version = ChunkVersion(
                version_id=f"{chunk.chunk_id}_v{version_number}",
                chunk_id=chunk.chunk_id,
                version_number=version_number,
                content_hash=content_hash,
                content=chunk.content,
                metadata_hash=metadata_hash,
                ai_metadata=chunk.ai_metadata,
                created_at=datetime.now(),
                changes_summary=changes_summary,
                previous_version_id=previous_version_id
            )
            
            # Store in database
            conn.execute("""
                INSERT INTO chunk_versions (
                    version_id, chunk_id, version_number, content_hash, content,
                    metadata_hash, ai_metadata, created_at, changes_summary, previous_version_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version.version_id, version.chunk_id, version.version_number,
                version.content_hash, version.content, version.metadata_hash,
                json.dumps(version.ai_metadata) if version.ai_metadata else None,
                version.created_at, version.changes_summary, version.previous_version_id
            ))
            
            # Update metadata index
            self._update_metadata_index(chunk)
            
            conn.commit()
            
            # Update cache
            self._chunk_cache[chunk.chunk_id] = chunk
            
            logger.info(f"Stored chunk version {version.version_id}")
            return version
            
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to store chunk version: {e}")
    
    def get_chunk_history(self, chunk_id: ChunkID) -> List[ChunkVersion]:
        """Get all versions of a chunk, ordered by version number"""
        conn = self._get_connection()
        
        try:
            cursor = conn.execute("""
                SELECT * FROM chunk_versions 
                WHERE chunk_id = ? 
                ORDER BY version_number DESC
            """, (chunk_id,))
            
            versions = []
            for row in cursor.fetchall():
                version = ChunkVersion(
                    version_id=row["version_id"],
                    chunk_id=row["chunk_id"],
                    version_number=row["version_number"],
                    content_hash=row["content_hash"],
                    content=row["content"],
                    metadata_hash=row["metadata_hash"],
                    ai_metadata=json.loads(row["ai_metadata"]) if row["ai_metadata"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    changes_summary=row["changes_summary"],
                    previous_version_id=row["previous_version_id"]
                )
                versions.append(version)
            
            return versions
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get chunk history: {e}")
    
    def add_relationship(self, 
                        source_chunk_id: ChunkID,
                        target_chunk_id: ChunkID,
                        relationship_type: RelationshipType,
                        strength: float = 1.0,
                        confidence: float = 1.0,
                        metadata: Dict[str, Any] = None,
                        created_by: str = "system") -> ChunkRelationship:
        """Add a relationship between two chunks"""
        conn = self._get_connection()
        
        try:
            # Validate inputs
            if source_chunk_id == target_chunk_id:
                raise ValueError("Cannot create relationship from chunk to itself")
            
            if not (0.0 <= strength <= 1.0):
                raise ValueError("Strength must be between 0.0 and 1.0")
            
            if not (0.0 <= confidence <= 1.0):
                raise ValueError("Confidence must be between 0.0 and 1.0")
            
            # Create relationship
            relationship = ChunkRelationship(
                relationship_id=f"rel_{source_chunk_id}_{target_chunk_id}_{relationship_type.value}",
                source_chunk_id=source_chunk_id,
                target_chunk_id=target_chunk_id,
                relationship_type=relationship_type,
                strength=strength,
                confidence=confidence,
                metadata=metadata or {},
                created_at=datetime.now(),
                created_by=created_by
            )
            
            # Store in database
            conn.execute("""
                INSERT OR REPLACE INTO chunk_relationships (
                    relationship_id, source_chunk_id, target_chunk_id, relationship_type,
                    strength, confidence, metadata, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                relationship.relationship_id, relationship.source_chunk_id,
                relationship.target_chunk_id, relationship.relationship_type.value,
                relationship.strength, relationship.confidence,
                json.dumps(relationship.metadata), relationship.created_at,
                relationship.created_by
            ))
            
            conn.commit()
            
            # Update cache
            if source_chunk_id in self._relationship_cache:
                del self._relationship_cache[source_chunk_id]
            if target_chunk_id in self._relationship_cache:
                del self._relationship_cache[target_chunk_id]
            
            logger.info(f"Added relationship: {source_chunk_id} -> {target_chunk_id} ({relationship_type.value})")
            return relationship
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                # Relationship already exists, update it
                return self._update_existing_relationship(
                    source_chunk_id, target_chunk_id, relationship_type,
                    strength, confidence, metadata, created_by
                )
            else:
                raise DatabaseError(f"Failed to add relationship: {e}")
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to add relationship: {e}")
    
    def get_chunk_relationships(self, 
                               chunk_id: ChunkID,
                               relationship_type: Optional[RelationshipType] = None,
                               direction: str = "both") -> List[ChunkRelationship]:
        """
        Get relationships for a chunk.
        
        Args:
            chunk_id: Chunk to get relationships for
            relationship_type: Filter by relationship type (optional)
            direction: 'outgoing', 'incoming', or 'both'
        """
        # Check cache first
        cache_key = f"{chunk_id}_{relationship_type}_{direction}"
        if cache_key in self._relationship_cache:
            return self._relationship_cache[cache_key]
        
        conn = self._get_connection()
        
        try:
            where_clauses = []
            params = []
            
            if direction in ["outgoing", "both"]:
                where_clauses.append("source_chunk_id = ?")
                params.append(chunk_id)
            
            if direction in ["incoming", "both"]:
                if where_clauses:
                    where_clauses.append("OR")
                where_clauses.append("target_chunk_id = ?")
                params.append(chunk_id)
            
            if relationship_type:
                where_clauses.append("AND relationship_type = ?")
                params.append(relationship_type.value)
            
            where_clause = " ".join(where_clauses)
            
            cursor = conn.execute(f"""
                SELECT * FROM chunk_relationships 
                WHERE {where_clause}
                ORDER BY confidence DESC, strength DESC
            """, params)
            
            relationships = []
            for row in cursor.fetchall():
                rel = ChunkRelationship(
                    relationship_id=row["relationship_id"],
                    source_chunk_id=row["source_chunk_id"],
                    target_chunk_id=row["target_chunk_id"],
                    relationship_type=RelationshipType(row["relationship_type"]),
                    strength=row["strength"],
                    confidence=row["confidence"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                    created_by=row["created_by"],
                    validated=bool(row["validated"])
                )
                relationships.append(rel)
            
            # Cache result
            self._relationship_cache[cache_key] = relationships
            
            return relationships
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get chunk relationships: {e}")
    
    def add_concept_mapping(self, 
                           concept_name: str,
                           chunk_id: ChunkID,
                           confidence: float,
                           evidence: List[str] = None) -> ConceptMapping:
        """Map a concept to a chunk"""
        conn = self._get_connection()
        
        try:
            concept_id = self._generate_concept_id(concept_name)
            
            # Check if mapping already exists
            existing = self._get_concept_mapping(concept_id, chunk_id)
            if existing:
                # Update existing mapping
                existing.confidence = max(existing.confidence, confidence)
                if evidence:
                    existing.evidence.extend(evidence)
                existing.last_updated = datetime.now()
                
                conn.execute("""
                    UPDATE concept_mappings 
                    SET confidence = ?, evidence = ?, last_updated = ?
                    WHERE concept_id = ? AND chunk_id = ?
                """, (
                    existing.confidence, json.dumps(existing.evidence),
                    existing.last_updated, concept_id, chunk_id
                ))
                
                conn.commit()
                return existing
            
            # Create new mapping
            mapping = ConceptMapping(
                concept_id=concept_id,
                concept_name=concept_name,
                chunk_ids={chunk_id},
                confidence=confidence,
                evidence=evidence or [],
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            conn.execute("""
                INSERT INTO concept_mappings (
                    concept_id, concept_name, chunk_id, confidence, evidence,
                    created_at, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                mapping.concept_id, mapping.concept_name, chunk_id,
                mapping.confidence, json.dumps(mapping.evidence),
                mapping.created_at, mapping.last_updated
            ))
            
            conn.commit()
            
            logger.info(f"Added concept mapping: {concept_name} -> {chunk_id}")
            return mapping
            
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to add concept mapping: {e}")
    
    def get_chunks_by_concept(self, 
                             concept_name: str,
                             min_confidence: float = 0.5) -> List[Tuple[ChunkID, float]]:
        """Get chunks associated with a concept"""
        concept_id = self._generate_concept_id(concept_name)
        conn = self._get_connection()
        
        try:
            cursor = conn.execute("""
                SELECT chunk_id, confidence FROM concept_mappings 
                WHERE concept_id = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (concept_id, min_confidence))
            
            return [(row["chunk_id"], row["confidence"]) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get chunks by concept: {e}")
    
    def get_chunk_concepts(self, chunk_id: ChunkID) -> List[Tuple[str, float]]:
        """Get concepts associated with a chunk"""
        conn = self._get_connection()
        
        try:
            cursor = conn.execute("""
                SELECT concept_name, confidence FROM concept_mappings 
                WHERE chunk_id = ?
                ORDER BY confidence DESC
            """, (chunk_id,))
            
            return [(row["concept_name"], row["confidence"]) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get chunk concepts: {e}")
    
    def find_related_chunks(self, 
                           chunk_id: ChunkID,
                           max_distance: int = 2,
                           min_strength: float = 0.5) -> List[Tuple[ChunkID, float, List[str]]]:
        """
        Find chunks related to the given chunk through relationship paths.
        
        Returns:
            List of (chunk_id, combined_strength, path) tuples
        """
        visited = set()
        results = []
        
        def traverse(current_id: ChunkID, distance: int, strength: float, path: List[str]):
            if distance > max_distance or current_id in visited:
                return
            
            visited.add(current_id)
            
            if distance > 0 and strength >= min_strength:
                results.append((current_id, strength, path.copy()))
            
            # Get outgoing relationships
            relationships = self.get_chunk_relationships(current_id, direction="outgoing")
            
            for rel in relationships:
                if rel.strength >= min_strength:
                    new_strength = strength * rel.strength
                    new_path = path + [f"{rel.relationship_type.value}({rel.strength:.2f})"]
                    traverse(rel.target_chunk_id, distance + 1, new_strength, new_path)
        
        traverse(chunk_id, 0, 1.0, [])
        
        # Sort by strength and remove duplicates
        unique_results = {}
        for chunk_id_result, strength, path in results:
            if chunk_id_result not in unique_results or strength > unique_results[chunk_id_result][0]:
                unique_results[chunk_id_result] = (strength, path)
        
        return [(cid, strength, path) for cid, (strength, path) in unique_results.items()]
    
    def detect_prerequisite_relationships(self, chunks: ChunkCollection) -> List[ChunkRelationship]:
        """Automatically detect prerequisite relationships between chunks"""
        relationships = []
        
        # Group chunks by subject and grade level
        chunks_by_subject = {}
        for chunk in chunks:
            key = f"{chunk.mother_section}_{chunk.chunk_type.value}"
            if key not in chunks_by_subject:
                chunks_by_subject[key] = []
            chunks_by_subject[key].append(chunk)
        
        # For each subject group, detect prerequisites based on:
        # 1. Sequence in mother sections
        # 2. Concept dependencies in AI metadata
        # 3. Mathematical complexity progression
        
        for subject_key, subject_chunks in chunks_by_subject.items():
            # Sort by mother section and sequence
            sorted_chunks = sorted(subject_chunks, 
                                 key=lambda c: (c.mother_section, c.sequence_in_mother))
            
            # Sequential prerequisites
            for i in range(1, len(sorted_chunks)):
                prev_chunk = sorted_chunks[i-1]
                curr_chunk = sorted_chunks[i]
                
                # Simple sequential relationship
                if self._is_sequential_prerequisite(prev_chunk, curr_chunk):
                    rel = self.add_relationship(
                        prev_chunk.chunk_id,
                        curr_chunk.chunk_id,
                        RelationshipType.PREREQUISITE,
                        strength=0.7,
                        confidence=0.8,
                        metadata={"detection_method": "sequential"},
                        created_by="system_prerequisite_detector"
                    )
                    relationships.append(rel)
        
        logger.info(f"Detected {len(relationships)} prerequisite relationships")
        return relationships
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _calculate_metadata_hash(self, chunk: BabyChunk) -> str:
        """Calculate hash of chunk metadata"""
        # Include key metadata fields that affect chunk semantics
        metadata_dict = {
            "chunk_type": chunk.chunk_type.value,
            "mother_section": chunk.mother_section,
            "activity_metadata": chunk.activity_metadata,
            "example_metadata": chunk.example_metadata,
            "content_metadata": chunk.content_metadata,
            "special_box_metadata": chunk.special_box_metadata
        }
        
        metadata_str = json.dumps(metadata_dict, sort_keys=True)
        return hashlib.sha256(metadata_str.encode('utf-8')).hexdigest()
    
    def _get_next_version_number(self, chunk_id: ChunkID) -> int:
        """Get the next version number for a chunk"""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT MAX(version_number) FROM chunk_versions WHERE chunk_id = ?
        """, (chunk_id,))
        
        max_version = cursor.fetchone()[0]
        return (max_version or 0) + 1
    
    def _get_latest_version(self, chunk_id: ChunkID) -> Optional[ChunkVersion]:
        """Get the latest version of a chunk"""
        versions = self.get_chunk_history(chunk_id)
        return versions[0] if versions else None
    
    def _get_version_by_hashes(self, 
                              chunk_id: ChunkID, 
                              content_hash: str, 
                              metadata_hash: str) -> Optional[ChunkVersion]:
        """Check if a version with these hashes already exists"""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM chunk_versions 
            WHERE chunk_id = ? AND content_hash = ? AND metadata_hash = ?
            ORDER BY version_number DESC LIMIT 1
        """, (chunk_id, content_hash, metadata_hash))
        
        row = cursor.fetchone()
        if row:
            return ChunkVersion(
                version_id=row["version_id"],
                chunk_id=row["chunk_id"],
                version_number=row["version_number"],
                content_hash=row["content_hash"],
                content=row["content"],
                metadata_hash=row["metadata_hash"],
                ai_metadata=json.loads(row["ai_metadata"]) if row["ai_metadata"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
                changes_summary=row["changes_summary"],
                previous_version_id=row["previous_version_id"]
            )
        return None
    
    def _update_metadata_index(self, chunk: BabyChunk):
        """Update the metadata index for fast lookups"""
        conn = self._get_connection()
        
        # Extract concepts from AI metadata
        concepts = []
        if chunk.ai_metadata:
            if "key_concepts" in chunk.ai_metadata:
                concepts.extend(chunk.ai_metadata["key_concepts"])
            if "main_concepts" in chunk.ai_metadata:
                concepts.extend([c.get("concept", "") for c in chunk.ai_metadata["main_concepts"]])
        
        conn.execute("""
            INSERT OR REPLACE INTO chunk_metadata_index (
                chunk_id, document_id, chunk_type, mother_section,
                subject, grade_level, concepts, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk.chunk_id, chunk.document_id, chunk.chunk_type.value,
            chunk.mother_section, "", "",  # Would get from document
            json.dumps(concepts), datetime.now()
        ))
    
    def _generate_concept_id(self, concept_name: str) -> ConceptID:
        """Generate a stable concept ID from concept name"""
        normalized_name = concept_name.lower().strip().replace(" ", "_")
        return f"concept_{hashlib.md5(normalized_name.encode()).hexdigest()[:8]}"
    
    def _get_concept_mapping(self, concept_id: ConceptID, chunk_id: ChunkID) -> Optional[ConceptMapping]:
        """Get existing concept mapping"""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM concept_mappings 
            WHERE concept_id = ? AND chunk_id = ?
        """, (concept_id, chunk_id))
        
        row = cursor.fetchone()
        if row:
            return ConceptMapping(
                concept_id=row["concept_id"],
                concept_name=row["concept_name"],
                chunk_ids={row["chunk_id"]},
                confidence=row["confidence"],
                evidence=json.loads(row["evidence"]) if row["evidence"] else [],
                created_at=datetime.fromisoformat(row["created_at"]),
                last_updated=datetime.fromisoformat(row["last_updated"])
            )
        return None
    
    def _update_existing_relationship(self, 
                                    source_chunk_id: ChunkID,
                                    target_chunk_id: ChunkID,
                                    relationship_type: RelationshipType,
                                    strength: float,
                                    confidence: float,
                                    metadata: Dict[str, Any],
                                    created_by: str) -> ChunkRelationship:
        """Update an existing relationship"""
        conn = self._get_connection()
        
        # Get existing relationship
        cursor = conn.execute("""
            SELECT * FROM chunk_relationships 
            WHERE source_chunk_id = ? AND target_chunk_id = ? AND relationship_type = ?
        """, (source_chunk_id, target_chunk_id, relationship_type.value))
        
        row = cursor.fetchone()
        if row:
            # Update with higher confidence/strength
            new_strength = max(strength, row["strength"])
            new_confidence = max(confidence, row["confidence"])
            
            conn.execute("""
                UPDATE chunk_relationships 
                SET strength = ?, confidence = ?, metadata = ?, created_by = ?
                WHERE relationship_id = ?
            """, (
                new_strength, new_confidence, json.dumps(metadata),
                created_by, row["relationship_id"]
            ))
            
            conn.commit()
            
            return ChunkRelationship(
                relationship_id=row["relationship_id"],
                source_chunk_id=source_chunk_id,
                target_chunk_id=target_chunk_id,
                relationship_type=relationship_type,
                strength=new_strength,
                confidence=new_confidence,
                metadata=metadata,
                created_at=datetime.fromisoformat(row["created_at"]),
                created_by=created_by
            )
        
        # Should not reach here, but create new if not found
        return self.add_relationship(source_chunk_id, target_chunk_id, relationship_type,
                                   strength, confidence, metadata, created_by)
    
    def _is_sequential_prerequisite(self, prev_chunk: BabyChunk, curr_chunk: BabyChunk) -> bool:
        """Determine if prev_chunk is a prerequisite for curr_chunk"""
        # Same mother section and sequential
        if prev_chunk.mother_section == curr_chunk.mother_section:
            return curr_chunk.sequence_in_mother > prev_chunk.sequence_in_mother
        
        # Different sections - check if section numbers suggest prerequisite
        try:
            prev_section_num = float(prev_chunk.mother_section)
            curr_section_num = float(curr_chunk.mother_section)
            return prev_section_num < curr_section_num
        except ValueError:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get chunk management statistics"""
        conn = self._get_connection()
        
        try:
            stats = {}
            
            # Version statistics
            cursor = conn.execute("SELECT COUNT(*) FROM chunk_versions")
            stats["total_versions"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT chunk_id) FROM chunk_versions")
            stats["unique_chunks"] = cursor.fetchone()[0]
            
            # Relationship statistics
            cursor = conn.execute("SELECT COUNT(*) FROM chunk_relationships")
            stats["total_relationships"] = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT relationship_type, COUNT(*) as count 
                FROM chunk_relationships 
                GROUP BY relationship_type
            """)
            stats["relationships_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Concept statistics
            cursor = conn.execute("SELECT COUNT(DISTINCT concept_id) FROM concept_mappings")
            stats["unique_concepts"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM concept_mappings")
            stats["total_concept_mappings"] = cursor.fetchone()[0]
            
            return stats
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get statistics: {e}")
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self.close()