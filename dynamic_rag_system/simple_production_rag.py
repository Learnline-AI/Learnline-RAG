#!/usr/bin/env python3
"""
Simplified Production RAG Builder for NCERT Class 9 Science
Processes PDF files to create a comprehensive educational knowledge base
"""

import os
import sys
import json
import logging
import asyncio
import fitz  # PyMuPDF
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker, HolisticChunk
from embeddings.vector_embedding_engine import VectorEmbeddingEngine, create_embeddings_for_chunks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleProductionRAG:
    """
    Simplified production RAG builder for NCERT Class 9 Science
    """
    
    def __init__(self):
        self.pdf_directory = '/Users/umangagarwal/Downloads/iesc1dd/'
        self.output_directory = 'production_rag_output/'
        self.database_path = 'production_rag_output/class9_science_simple.db'
        
        # Chapter mapping
        self.subject_mapping = {
            'iesc1an': 'Table of Contents',
            'iesc1ps': 'Preface/Introduction', 
            'iesc101': 'Matter in Our Surroundings',
            'iesc102': 'Is Matter Around Us Pure',
            'iesc103': 'Atoms and Molecules',
            'iesc104': 'Structure of the Atom',
            'iesc105': 'The Fundamental Unit of Life',
            'iesc106': 'Tissues',
            'iesc107': 'Diversity in Living Organisms',
            'iesc108': 'Motion',
            'iesc109': 'Force and Laws of Motion',
            'iesc110': 'Gravitation',
            'iesc111': 'Sound',
            'iesc112': 'Why Do We Fall Ill'
        }
        
        # Initialize components
        self.chunker = HolisticRAGChunker()
        self.embedding_engine = VectorEmbeddingEngine()
        
        # Setup
        os.makedirs(self.output_directory, exist_ok=True)
        self.setup_database()
        
    def setup_database(self):
        """Setup simple database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE,
                filename TEXT,
                chapter_title TEXT,
                content TEXT,
                content_length INTEGER,
                chunk_type TEXT,
                quality_score REAL,
                subject_area TEXT,
                chapter_number INTEGER,
                metadata TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def get_available_pdfs(self) -> List[Dict]:
        """Get list of available PDF files"""
        pdf_files = [
            'iesc101.pdf', 'iesc102.pdf', 'iesc103.pdf', 'iesc104.pdf',
            'iesc105.pdf', 'iesc106.pdf', 'iesc107.pdf', 'iesc108.pdf', 
            'iesc109.pdf', 'iesc110.pdf', 'iesc111.pdf', 'iesc112.pdf'
        ]  # Skip table of contents and preface for now
        
        available_files = []
        
        for filename in pdf_files:
            file_path = os.path.join(self.pdf_directory, filename)
            
            if os.path.exists(file_path):
                base_name = filename.replace('.pdf', '')
                chapter_title = self.subject_mapping.get(base_name, 'Unknown')
                
                # Extract chapter number
                chapter_number = 0
                if base_name.startswith('iesc1') and base_name[5:].isdigit():
                    chapter_number = int(base_name[5:])
                
                # Determine subject
                subject_mapping = {
                    101: 'Chemistry', 102: 'Chemistry', 103: 'Chemistry', 104: 'Chemistry',
                    105: 'Biology', 106: 'Biology', 107: 'Biology', 112: 'Biology',
                    108: 'Physics', 109: 'Physics', 110: 'Physics', 111: 'Physics'
                }
                subject_area = subject_mapping.get(chapter_number, 'Science')
                
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                
                available_files.append({
                    'filename': filename,
                    'file_path': file_path,
                    'chapter_title': chapter_title,
                    'chapter_number': chapter_number,
                    'subject_area': subject_area,
                    'file_size_mb': round(file_size, 1)
                })
        
        return available_files
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(file_path)
            full_text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                full_text += page_text + "\n"
            
            doc.close()
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def create_sections_from_text(self, text: str, file_info: Dict) -> List[Dict]:
        """Create sections from extracted text"""
        # Simple approach: create sections based on patterns
        section_patterns = [
            r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]{3,60})(?:\n|$)',
            r'^(\d+)\s+([A-Z][A-Za-z\s]{3,60})(?:\n|$)',
        ]
        
        sections = []
        section_matches = []
        
        for pattern in section_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                section_matches.append({
                    'position': match.start(),
                    'number': match.group(1),
                    'title': match.group(2).strip()
                })
        
        # Sort by position
        section_matches.sort(key=lambda x: x['position'])
        
        if section_matches:
            # Create sections based on detected boundaries
            for i, section_match in enumerate(section_matches):
                start_pos = section_match['position']
                
                if i + 1 < len(section_matches):
                    end_pos = section_matches[i + 1]['position']
                else:
                    end_pos = len(text)
                
                section_content = text[start_pos:end_pos]
                
                sections.append({
                    'section_number': section_match['number'],
                    'title': section_match['title'],
                    'content': section_content,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'grade_level': 9,
                    'subject': file_info['subject_area'],
                    'chapter': file_info['chapter_number']
                })
        else:
            # No sections detected, create single section
            sections.append({
                'section_number': '1',
                'title': file_info['chapter_title'],
                'content': text,
                'start_pos': 0,
                'end_pos': len(text),
                'grade_level': 9,
                'subject': file_info['subject_area'],
                'chapter': file_info['chapter_number']
            })
        
        return sections
    
    def process_pdf_file(self, file_info: Dict) -> List[HolisticChunk]:
        """Process a single PDF file"""
        logger.info(f"Processing: {file_info['filename']} - {file_info['chapter_title']}")
        
        # Extract text
        text = self.extract_text_from_pdf(file_info['file_path'])
        
        if not text.strip():
            logger.warning(f"No text extracted from {file_info['filename']}")
            return []
        
        # Create sections
        sections = self.create_sections_from_text(text, file_info)
        
        # Process sections with chunker
        all_chunks = []
        
        for section in sections:
            try:
                # Create a simple character-to-page mapping
                char_to_page_map = {i: 1 for i in range(len(text))}  # Simple mapping
                
                chunks = self.chunker.process_mother_section(section, text, char_to_page_map)
                
                if chunks:
                    all_chunks.extend(chunks)
                    logger.info(f"  Created {len(chunks)} chunks for section: {section['title']}")
                
            except Exception as e:
                logger.error(f"  Error processing section {section['title']}: {e}")
        
        return all_chunks
    
    def store_chunks(self, chunks: List[HolisticChunk], file_info: Dict):
        """Store chunks in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        for chunk in chunks:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO processed_chunks 
                    (chunk_id, filename, chapter_title, content, content_length, 
                     chunk_type, quality_score, subject_area, chapter_number, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chunk.chunk_id,
                    file_info['filename'],
                    file_info['chapter_title'],
                    chunk.content,
                    len(chunk.content),
                    chunk.metadata.get('type', 'unknown'),
                    chunk.quality_score,
                    file_info['subject_area'],
                    file_info['chapter_number'],
                    json.dumps(chunk.metadata),
                    chunk.created_at
                ))
            except Exception as e:
                logger.error(f"Error storing chunk {chunk.chunk_id}: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(chunks)} chunks for {file_info['filename']}")
    
    async def process_all_files(self) -> List[HolisticChunk]:
        """Process all available PDF files"""
        available_files = self.get_available_pdfs()
        
        if not available_files:
            logger.error("No PDF files available")
            return []
        
        logger.info(f"Found {len(available_files)} PDF files to process")
        
        all_chunks = []
        
        for i, file_info in enumerate(available_files):
            logger.info(f"Processing file {i+1}/{len(available_files)}: {file_info['filename']}")
            
            try:
                chunks = self.process_pdf_file(file_info)
                
                if chunks:
                    self.store_chunks(chunks, file_info)
                    all_chunks.extend(chunks)
                    
                    # Process all files now
                    # if i >= 2:  # Process first 3 files for testing
                    #     logger.info("Processing first 3 files for testing...")
                    #     break
                
            except Exception as e:
                logger.error(f"Error processing {file_info['filename']}: {e}")
        
        logger.info(f"Successfully processed {len(all_chunks)} chunks total")
        return all_chunks
    
    async def create_embeddings(self, chunks: List[HolisticChunk]) -> Dict:
        """Create embeddings for chunks"""
        logger.info(f"Creating embeddings for {len(chunks)} chunks...")
        
        if not self.embedding_engine.is_available():
            logger.error("Embedding engine not available")
            return {}
        
        # Convert chunks to format expected by embedding engine
        chunk_data = []
        for chunk in chunks:
            chunk_data.append({
                'chunk_id': chunk.chunk_id,
                'content': chunk.content,
                'metadata': chunk.metadata,
                'quality_score': chunk.quality_score
            })
        
        # Create embeddings
        embeddings = create_embeddings_for_chunks(chunk_data, self.embedding_engine)
        
        logger.info(f"Created embeddings for {len(embeddings)} chunks")
        
        return {
            'total_embeddings': len(embeddings),
            'embedding_model': self.embedding_engine.config['embedding_model'],
            'embedding_dimensions': self.embedding_engine.config['embedding_dimensions']
        }
    
    def generate_report(self, chunks: List[HolisticChunk], embeddings_info: Dict) -> str:
        """Generate summary report"""
        if not chunks:
            return "No chunks processed"
        
        # Basic statistics
        total_chunks = len(chunks)
        avg_quality = sum(chunk.quality_score for chunk in chunks) / total_chunks
        
        # Performance distribution
        excellent = sum(1 for chunk in chunks if chunk.quality_score >= 0.8)
        good = sum(1 for chunk in chunks if 0.6 <= chunk.quality_score < 0.8)
        
        report = f"""
# 🚀 Simple Production RAG - NCERT Class 9 Science Test Build

## 📊 Build Summary
- **Build Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Total Chunks:** {total_chunks}
- **Average Quality:** {avg_quality:.2f}/1.00
- **Performance:** Excellent({excellent}) Good({good})

## 🧠 Embeddings
- **Total Embeddings:** {embeddings_info.get('total_embeddings', 0)}
- **Model:** {embeddings_info.get('embedding_model', 'Unknown')}
- **Dimensions:** {embeddings_info.get('embedding_dimensions', 0)}

## 📚 Processed Content
"""
        
        # Group by subject
        subjects = {}
        for chunk in chunks:
            subject = chunk.metadata.get('basic_info', {}).get('subject', 'Unknown')
            subjects[subject] = subjects.get(subject, 0) + 1
        
        for subject, count in subjects.items():
            report += f"- **{subject}:** {count} chunks\n"
        
        report += f"\n✅ **Status:** Production RAG system successfully initialized!\n"
        
        # Save report
        report_path = os.path.join(self.output_directory, 'SIMPLE_RAG_REPORT.md')
        with open(report_path, 'w') as f:
            f.write(report)
        
        return report

async def main():
    """Main function"""
    print("🚀 Simple Production RAG Builder - NCERT Class 9 Science")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    try:
        rag = SimpleProductionRAG()
        
        # Process files
        print(f"📚 Processing PDF files...")
        chunks = await rag.process_all_files()
        
        if not chunks:
            print("❌ No chunks created")
            return
        
        # Create embeddings
        print(f"🧠 Creating embeddings...")
        embeddings_info = await rag.create_embeddings(chunks)
        
        # Generate report
        report = rag.generate_report(chunks, embeddings_info)
        
        print(f"\n{'='*30} SUCCESS {'='*30}")
        print(f"🎉 Processed {len(chunks)} chunks successfully!")
        print(f"📊 Average quality: {sum(c.quality_score for c in chunks)/len(chunks):.2f}")
        print(f"🧠 Embeddings: {embeddings_info.get('total_embeddings', 0)}")
        print(f"📋 Report saved to: production_rag_output/SIMPLE_RAG_REPORT.md")
        
        return True
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(main())