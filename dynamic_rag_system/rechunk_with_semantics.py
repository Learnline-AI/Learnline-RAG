#!/usr/bin/env python3
"""
Semantic Rechunking Script - Rechunk entire database with semantic separation

This script:
1. Reads existing chunks from class9_science_simple.db
2. Applies semantic separation to create properly separated chunks
3. Creates a new database with semantic chunks and relationships
4. Preserves original data while providing enhanced chunking
"""

import os
import sys
import sqlite3
import json
import logging
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from semantic_chunker import SemanticEducationalChunker, RelationshipMap

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SemanticRechunker:
    """
    Rechunks entire database with semantic separation
    """
    
    def __init__(self, 
                 source_db_path: str = "production_rag_output/class9_science_simple.db",
                 target_db_path: str = "production_rag_output/class9_science_semantic.db"):
        self.source_db_path = source_db_path
        self.target_db_path = target_db_path
        self.semantic_chunker = SemanticEducationalChunker()
        
        # Statistics
        self.stats = {
            'original_chunks': 0,
            'semantic_chunks': 0,
            'relationships_created': 0,
            'chapters_processed': 0,
            'processing_time': 0.0
        }
    
    def setup_target_database(self):
        """Create target database with enhanced schema"""
        os.makedirs(os.path.dirname(self.target_db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.target_db_path)
        cursor = conn.cursor()
        
        # Enhanced chunks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semantic_chunks (
                chunk_id TEXT PRIMARY KEY,
                original_chunk_id TEXT,
                chunk_type TEXT NOT NULL,
                content TEXT NOT NULL,
                chapter_title TEXT,
                chapter_number INTEGER,
                subject_area TEXT,
                mother_section TEXT,
                mother_section_title TEXT,
                sequence_in_section INTEGER,
                quality_score REAL,
                confidence REAL,
                
                -- Position information
                start_position INTEGER,
                end_position INTEGER,
                
                -- Content-specific metadata
                activity_metadata TEXT,  -- JSON
                example_metadata TEXT,   -- JSON 
                content_metadata TEXT,   -- JSON
                question_metadata TEXT,  -- JSON
                
                -- Semantic information
                concepts TEXT,           -- JSON array
                estimated_duration INTEGER,
                difficulty_level TEXT,
                
                -- Processing metadata
                created_at TEXT,
                semantic_version TEXT
            )
        ''')
        
        # Relationships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunk_relationships (
                relationship_id TEXT PRIMARY KEY,
                source_chunk_id TEXT NOT NULL,
                target_chunk_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL NOT NULL,
                description TEXT,
                created_at TEXT,
                
                FOREIGN KEY (source_chunk_id) REFERENCES semantic_chunks (chunk_id),
                FOREIGN KEY (target_chunk_id) REFERENCES semantic_chunks (chunk_id)
            )
        ''')
        
        # Chapter processing log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_title TEXT,
                original_chunks INTEGER,
                semantic_chunks INTEGER,
                relationships INTEGER,
                processing_time REAL,
                processed_at TEXT,
                status TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_semantic_chapter ON semantic_chunks (chapter_title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_semantic_type ON semantic_chunks (chunk_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships_source ON chunk_relationships (source_chunk_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships_target ON chunk_relationships (target_chunk_id)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Target database created at: {self.target_db_path}")
    
    def get_chapters_to_process(self) -> List[Dict[str, Any]]:
        """Get list of chapters from source database"""
        conn = sqlite3.connect(self.source_db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('''
            SELECT DISTINCT chapter_title, chapter_number, subject_area,
                   COUNT(*) as chunk_count
            FROM processed_chunks 
            GROUP BY chapter_title, chapter_number, subject_area
            ORDER BY chapter_number
        ''')
        
        chapters = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return chapters
    
    def get_chapter_chunks(self, chapter_title: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific chapter"""
        conn = sqlite3.connect(self.source_db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('''
            SELECT * FROM processed_chunks 
            WHERE chapter_title = ?
            ORDER BY chunk_id
        ''', (chapter_title,))
        
        chunks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return chunks
    
    def process_chapter(self, chapter_info: Dict[str, Any]) -> Tuple[List[Dict], List[RelationshipMap]]:
        """Process a single chapter with semantic separation"""
        chapter_title = chapter_info['chapter_title']
        logger.info(f"Processing chapter: {chapter_title}")
        
        # Get original chunks for this chapter
        original_chunks = self.get_chapter_chunks(chapter_title)
        
        # Combine content from original chunks to get full chapter text
        full_chapter_content = ""
        chunk_positions = {}
        current_pos = 0
        
        for chunk in original_chunks:
            content = chunk['content']
            chunk_positions[chunk['chunk_id']] = {
                'start': current_pos,
                'end': current_pos + len(content)
            }
            full_chapter_content += content + "\n\n"
            current_pos = len(full_chapter_content)
        
        # Apply semantic separation
        section_info = {
            'chapter_title': chapter_title,
            'chapter_number': chapter_info['chapter_number'],
            'subject_area': chapter_info['subject_area']
        }
        
        semantic_chunks, relationships = self.semantic_chunker.create_semantic_chunks(
            full_chapter_content, section_info
        )
        
        # Convert to storage format
        stored_chunks = []
        for i, chunk in enumerate(semantic_chunks):
            stored_chunk = {
                'chunk_id': chunk.chunk_id,
                'original_chunk_id': self._find_original_chunk_id(chunk, original_chunks, chunk_positions),
                'chunk_type': chunk.chunk_type.value,
                'content': chunk.content,
                'chapter_title': chapter_title,
                'chapter_number': chapter_info['chapter_number'],
                'subject_area': chapter_info['subject_area'],
                'mother_section': chunk.mother_section,
                'mother_section_title': chunk.mother_section_title,
                'sequence_in_section': i + 1,
                'quality_score': chunk.quality_score.get('overall', 0.0) if chunk.quality_score else 0.0,
                'confidence': chunk.quality_score.get('semantic_separation', 0.0) if chunk.quality_score else 0.0,
                'start_position': chunk.position_in_document.get('start_pos', 0),
                'end_position': chunk.position_in_document.get('end_pos', len(chunk.content)),
                'activity_metadata': json.dumps(chunk.activity_metadata) if chunk.activity_metadata else None,
                'example_metadata': json.dumps(chunk.example_metadata) if chunk.example_metadata else None,
                'content_metadata': json.dumps(chunk.content_metadata) if chunk.content_metadata else None,
                'concepts': json.dumps(chunk.concept_tags),
                'estimated_duration': self._estimate_duration(chunk),
                'difficulty_level': self._estimate_difficulty(chunk),
                'created_at': datetime.now().isoformat(),
                'semantic_version': '1.0'
            }
            stored_chunks.append(stored_chunk)
        
        logger.info(f"Chapter {chapter_title}: {len(original_chunks)} -> {len(stored_chunks)} chunks, {len(relationships)} relationships")
        
        return stored_chunks, relationships
    
    def _find_original_chunk_id(self, semantic_chunk, original_chunks, chunk_positions) -> str:
        """Find which original chunk this semantic chunk came from"""
        chunk_start = semantic_chunk.position_in_document.get('start_pos', 0)
        
        for orig_chunk in original_chunks:
            orig_id = orig_chunk['chunk_id']
            if orig_id in chunk_positions:
                pos_info = chunk_positions[orig_id]
                if pos_info['start'] <= chunk_start <= pos_info['end']:
                    return orig_id
        
        # Fallback to first chunk if no match found
        return original_chunks[0]['chunk_id'] if original_chunks else 'unknown'
    
    def _estimate_duration(self, chunk) -> int:
        """Estimate reading/activity duration in minutes"""
        word_count = len(chunk.content.split())
        
        if chunk.chunk_type.value == 'activity':
            # Activities take longer
            return max(10, min(30, word_count // 50))
        elif chunk.chunk_type.value == 'example':
            # Examples need working time
            return max(5, min(15, word_count // 100))
        else:
            # Reading time
            return max(2, min(10, word_count // 200))
    
    def _estimate_difficulty(self, chunk) -> str:
        """Estimate difficulty level"""
        content = chunk.content.lower()
        
        # Count complexity indicators
        math_terms = len(re.findall(r'\b(equation|formula|calculate|solve|derive)\b', content))
        complex_words = len(re.findall(r'\b\w{10,}\b', content))
        technical_terms = len(re.findall(r'\b(molecular|atomic|chemical|physical|biological)\b', content))
        
        score = math_terms + (complex_words // 5) + technical_terms
        
        if score >= 5:
            return 'advanced'
        elif score >= 2:
            return 'intermediate'
        else:
            return 'beginner'
    
    def store_semantic_chunks(self, chunks: List[Dict], relationships: List[RelationshipMap]):
        """Store semantic chunks and relationships in target database"""
        conn = sqlite3.connect(self.target_db_path)
        
        try:
            # Store chunks
            for chunk in chunks:
                conn.execute('''
                    INSERT OR REPLACE INTO semantic_chunks (
                        chunk_id, original_chunk_id, chunk_type, content, chapter_title,
                        chapter_number, subject_area, mother_section, mother_section_title,
                        sequence_in_section, quality_score, confidence, start_position,
                        end_position, activity_metadata, example_metadata, content_metadata,
                        concepts, estimated_duration, difficulty_level, created_at, semantic_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chunk['chunk_id'], chunk['original_chunk_id'], chunk['chunk_type'],
                    chunk['content'], chunk['chapter_title'], chunk['chapter_number'],
                    chunk['subject_area'], chunk['mother_section'], chunk['mother_section_title'],
                    chunk['sequence_in_section'], chunk['quality_score'], chunk['confidence'],
                    chunk['start_position'], chunk['end_position'], chunk['activity_metadata'],
                    chunk['example_metadata'], chunk['content_metadata'], chunk['concepts'],
                    chunk['estimated_duration'], chunk['difficulty_level'], chunk['created_at'],
                    chunk['semantic_version']
                ))
            
            # Store relationships
            for rel in relationships:
                relationship_id = f"rel_{rel.source_chunk_id}_{rel.target_chunk_id}_{rel.relationship_type}"
                conn.execute('''
                    INSERT OR REPLACE INTO chunk_relationships (
                        relationship_id, source_chunk_id, target_chunk_id,
                        relationship_type, strength, description, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    relationship_id, rel.source_chunk_id, rel.target_chunk_id,
                    rel.relationship_type, rel.strength, rel.description,
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def log_chapter_processing(self, chapter_info: Dict, chunks_count: int, relationships_count: int, processing_time: float):
        """Log chapter processing results"""
        conn = sqlite3.connect(self.target_db_path)
        
        conn.execute('''
            INSERT INTO processing_log (
                chapter_title, original_chunks, semantic_chunks, relationships,
                processing_time, processed_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            chapter_info['chapter_title'], chapter_info['chunk_count'],
            chunks_count, relationships_count, processing_time,
            datetime.now().isoformat(), 'completed'
        ))
        
        conn.commit()
        conn.close()
    
    def rechunk_all(self):
        """Main method to rechunk entire database"""
        start_time = datetime.now()
        
        logger.info("Starting semantic rechunking process")
        logger.info(f"Source: {self.source_db_path}")
        logger.info(f"Target: {self.target_db_path}")
        
        # Setup target database
        self.setup_target_database()
        
        # Get chapters to process
        chapters = self.get_chapters_to_process()
        logger.info(f"Found {len(chapters)} chapters to process")
        
        # Process each chapter
        for chapter_info in chapters:
            chapter_start_time = datetime.now()
            
            try:
                semantic_chunks, relationships = self.process_chapter(chapter_info)
                
                # Store results
                self.store_semantic_chunks(semantic_chunks, relationships)
                
                # Update statistics
                chapter_processing_time = (datetime.now() - chapter_start_time).total_seconds()
                self.stats['semantic_chunks'] += len(semantic_chunks)
                self.stats['relationships_created'] += len(relationships)
                self.stats['chapters_processed'] += 1
                
                # Log chapter processing
                self.log_chapter_processing(
                    chapter_info, len(semantic_chunks), 
                    len(relationships), chapter_processing_time
                )
                
                logger.info(f"✅ Completed {chapter_info['chapter_title']} in {chapter_processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Error processing {chapter_info['chapter_title']}: {e}")
                continue
        
        # Final statistics
        total_time = (datetime.now() - start_time).total_seconds()
        self.stats['processing_time'] = total_time
        
        logger.info("=" * 60)
        logger.info("SEMANTIC RECHUNKING COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Chapters processed: {self.stats['chapters_processed']}")
        logger.info(f"Semantic chunks created: {self.stats['semantic_chunks']}")
        logger.info(f"Relationships created: {self.stats['relationships_created']}")
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        if self.stats['chapters_processed'] > 0:
            logger.info(f"Average per chapter: {total_time/self.stats['chapters_processed']:.2f} seconds")
        else:
            logger.info("No chapters were successfully processed")
        logger.info(f"New database: {self.target_db_path}")
    
    def get_rechunking_summary(self) -> Dict[str, Any]:
        """Get summary of rechunking results"""
        conn = sqlite3.connect(self.target_db_path)
        conn.row_factory = sqlite3.Row
        
        # Get chunk statistics
        cursor = conn.execute('''
            SELECT chunk_type, COUNT(*) as count,
                   AVG(LENGTH(content)) as avg_length,
                   AVG(estimated_duration) as avg_duration
            FROM semantic_chunks 
            GROUP BY chunk_type
        ''')
        chunk_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get relationship statistics
        cursor = conn.execute('''
            SELECT relationship_type, COUNT(*) as count,
                   AVG(strength) as avg_strength
            FROM chunk_relationships
            GROUP BY relationship_type
        ''')
        rel_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get processing log
        cursor = conn.execute('''
            SELECT * FROM processing_log 
            ORDER BY processed_at
        ''')
        processing_log = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'chunk_statistics': chunk_stats,
            'relationship_statistics': rel_stats,
            'processing_log': processing_log,
            'total_stats': self.stats
        }


def main():
    """Main execution function"""
    import re
    
    rechunker = SemanticRechunker()
    
    # Check if source database exists
    if not os.path.exists(rechunker.source_db_path):
        logger.error(f"Source database not found: {rechunker.source_db_path}")
        return
    
    # Run semantic rechunking
    rechunker.rechunk_all()
    
    # Display summary
    summary = rechunker.get_rechunking_summary()
    
    print("\n" + "=" * 60)
    print("📊 SEMANTIC RECHUNKING SUMMARY")
    print("=" * 60)
    
    print("\n🧩 Chunk Statistics:")
    for stat in summary['chunk_statistics']:
        print(f"  {stat['chunk_type']}: {stat['count']} chunks, "
              f"avg {stat['avg_length']:.0f} chars, "
              f"avg {stat['avg_duration']:.1f} min duration")
    
    print("\n🔗 Relationship Statistics:")
    for stat in summary['relationship_statistics']:
        print(f"  {stat['relationship_type']}: {stat['count']} relationships, "
              f"avg strength {stat['avg_strength']:.2f}")
    
    print(f"\n✅ Successfully created semantic database: {rechunker.target_db_path}")


if __name__ == "__main__":
    main()