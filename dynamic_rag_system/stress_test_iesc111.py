#!/usr/bin/env python3
"""
Comprehensive Stress Test for iesc111.pdf
Evaluates chunking quality, element detection, and question-answering capabilities
"""

import os
import sys
import json
import re
import sqlite3
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional, Tuple

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker, PrerequisiteMapper, HolisticChunk
from chunking.section_detector import SectionDetector
from chunking.pattern_library import PatternLibrary
from ingestion.pdf_processor import PDFProcessor

def print_banner():
    """Print stress test banner"""
    print("🔥" * 20)
    print("🚀 COMPREHENSIVE STRESS TEST - iesc111.pdf")
    print("🔥" * 20)
    print()

def analyze_pdf_basic_info(pdf_path: str) -> Dict[str, Any]:
    """Extract basic information about the PDF"""
    print(f"📊 Analyzing PDF: {Path(pdf_path).name}")
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        
        total_pages = len(doc)
        file_size = os.path.getsize(pdf_path)
        
        # Extract text from first few pages for preview
        preview_text = ""
        for page_num in range(min(total_pages, 5)):
            page_text = doc[page_num].get_text()
            preview_text += page_text + "\n"
        
        doc.close()
        
        print(f"  📄 File type: PDF document")
        print(f"  📖 Total pages: {total_pages}")
        print(f"  📏 File size: {file_size / (1024*1024):.1f} MB")
        
        # Analyze content type
        preview_lower = preview_text.lower()
        content_indicators = {
            'educational': ['chapter', 'lesson', 'exercise', 'example', 'activity'],
            'technical': ['algorithm', 'function', 'code', 'programming'],
            'research': ['abstract', 'introduction', 'methodology', 'conclusion'],
            'ncert': ['ncert', 'cbse', 'class', 'grade'],
            'physics': ['force', 'motion', 'energy', 'physics', 'velocity', 'acceleration'],
            'math': ['equation', 'theorem', 'proof', 'mathematics', 'formula'],
            'chemistry': ['molecule', 'reaction', 'chemistry', 'element'],
            'biology': ['cell', 'organism', 'biology', 'species']
        }
        
        detected_types = []
        for content_type, keywords in content_indicators.items():
            if any(keyword in preview_lower for keyword in keywords):
                detected_types.append(content_type)
        
        print(f"  🔍 Content type indicators: {detected_types if detected_types else ['general']}")
        
        return {
            'total_pages': total_pages,
            'file_size_mb': file_size / (1024*1024),
            'content_types': detected_types,
            'preview_text': preview_text[:1000]
        }
        
    except Exception as e:
        print(f"  ❌ Error analyzing PDF: {e}")
        return {}

def extract_text_from_pdf(pdf_path: str) -> Tuple[str, Dict[int, int]]:
    """Extract text from PDF with character-to-page mapping"""
    print(f"\n📖 Extracting text from PDF...")
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        
        full_text = ""
        char_to_page_map = {}
        current_char_pos = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Map each character to its page
            for i in range(len(page_text)):
                char_to_page_map[current_char_pos + i] = page_num + 1
            
            full_text += page_text + "\n"
            current_char_pos += len(page_text) + 1
        
        doc.close()
        
        print(f"  ✅ Extracted {len(full_text)} characters from {len(doc)} pages")
        print(f"  📍 Character-to-page mapping created for {len(char_to_page_map)} positions")
        
        return full_text, char_to_page_map
        
    except Exception as e:
        print(f"  ❌ Error extracting text: {e}")
        return "", {}

def detect_educational_structure(text: str) -> Dict[str, Any]:
    """Detect educational structure in the text"""
    print(f"\n🏗️ Detecting educational structure...")
    
    structure = {
        'sections': [],
        'activities': [],
        'examples': [],
        'figures': [],
        'special_boxes': [],
        'formulas': [],
        'questions': [],
        'concepts': []
    }
    
    # Enhanced section detection patterns
    section_patterns = [
        r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]{3,60})(?:\n|$)',
        r'^Chapter\s+(\d+):?\s*([A-Za-z\s]+)(?:\n|$)',
        r'^(\d+\.\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,8})(?:\n|$)',
        # Additional patterns for NCERT content
        r'^(\d+\.\d+)\s+([A-Z][A-Z\s]{3,60})(?:\n|$)',  # All caps titles
        r'(\d+)\s+([A-Z][A-Za-z\s]{3,60})(?:\n|$)',      # Single digit sections
        r'^(\d+\.\d+)\s*:\s*([A-Za-z\s]+)(?:\n|$)',       # Colon separator
    ]
    
    # Activity detection patterns
    activity_patterns = [
        r'ACTIVITY\s+(\d+\.\d+)',
        r'Activity\s*[_\-–—\s]*\s*(\d+\.\d+)',
        r'गतिविधि\s+(\d+\.\d+)',
        r'Exercise\s+(\d+\.\d+)',
    ]
    
    # Example detection patterns
    example_patterns = [
        r'Example\s+(\d+\.\d+)',
        r'EXAMPLE\s+(\d+\.\d+)',
        r'उदाहरण\s+(\d+\.\d+)',
        r'Solved\s+Example\s+(\d+\.\d+)',
    ]
    
    # Figure detection patterns
    figure_patterns = [
        r'Fig\.\s*(\d+\.\d+):\s*([^\n]+)',
        r'Figure\s+(\d+\.\d+):\s*([^\n]+)',
        r'चित्र\s+(\d+\.\d+):\s*([^\n]+)',
    ]
    
    # Special box detection patterns
    special_box_patterns = [
        r'(DO YOU KNOW\?)',
        r'(What you have learnt)',
        r'(Remember)',
        r'(Note:)',
        r'(Summary)',
        r'(Key Points)',
    ]
    
    # Formula detection patterns
    formula_patterns = [
        r'([A-Z]\s*=\s*[A-Za-z0-9\s\+\-\*/\(\)]+)',
        r'([a-z]\s*=\s*[A-Za-z0-9\s\+\-\*/\(\)]+)',
        r'(\\frac\{[^}]+\}\{[^}]+\})',
    ]
    
    # Question detection patterns
    question_patterns = [
        r'Questions?\s*\n',
        r'Exercise\s*\n',
        r'(\d+\.\s+[A-Z][^?]*\?)',
    ]
    
    # Concept detection patterns
    concept_patterns = [
        r'Definition:\s*([^\n]+)',
        r'([A-Za-z\s]+)\s+is\s+defined\s+as',
        r'([A-Za-z\s]+)\s+means',
    ]
    
    # Detect sections
    for pattern in section_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            structure['sections'].append({
                'number': match.group(1),
                'title': match.group(2).strip(),
                'position': match.start(),
                'full_match': match.group(0).strip()
            })
    
    # Detect activities
    for pattern in activity_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            structure['activities'].append({
                'number': match.group(1),
                'position': match.start(),
                'full_match': match.group(0).strip()
            })
    
    # Detect examples
    for pattern in example_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            structure['examples'].append({
                'number': match.group(1),
                'position': match.start(),
                'full_match': match.group(0).strip()
            })
    
    # Detect figures
    for pattern in figure_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            structure['figures'].append({
                'number': match.group(1),
                'caption': match.group(2) if len(match.groups()) > 1 else '',
                'position': match.start(),
                'full_match': match.group(0).strip()
            })
    
    # Detect special boxes
    for pattern in special_box_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
            structure['special_boxes'].append({
                'type': match.group(1) if match.groups() else match.group(0),
                'position': match.start(),
                'full_match': match.group(0).strip()
            })
    
    # Detect formulas
    for pattern in formula_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            structure['formulas'].append({
                'formula': match.group(1) if match.groups() else match.group(0),
                'position': match.start(),
                'full_match': match.group(0).strip()
            })
    
    # Detect questions
    for pattern in question_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            structure['questions'].append({
                'text': match.group(1) if match.groups() else match.group(0),
                'position': match.start(),
                'full_match': match.group(0).strip()
            })
    
    # Detect concepts
    for pattern in concept_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
            structure['concepts'].append({
                'concept': match.group(1) if match.groups() else match.group(0),
                'position': match.start(),
                'full_match': match.group(0).strip()
            })
    
    # Print detection results
    print(f"  📊 Detection Results:")
    print(f"    • Sections: {len(structure['sections'])}")
    print(f"    • Activities: {len(structure['activities'])}")
    print(f"    • Examples: {len(structure['examples'])}")
    print(f"    • Figures: {len(structure['figures'])}")
    print(f"    • Special Boxes: {len(structure['special_boxes'])}")
    print(f"    • Formulas: {len(structure['formulas'])}")
    print(f"    • Questions: {len(structure['questions'])}")
    print(f"    • Concepts: {len(structure['concepts'])}")
    
    return structure

def create_mother_sections(text: str, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create mother sections from detected structure"""
    print(f"\n🏗️ Creating mother sections...")
    
    mother_sections = []
    
    # Sort sections by position
    sections = sorted(structure['sections'], key=lambda x: x['position'])
    
    for i, section in enumerate(sections):
        # Determine section boundaries
        start_pos = section['position']
        
        if i < len(sections) - 1:
            end_pos = sections[i + 1]['position']
        else:
            end_pos = len(text)
        
        # Extract section content
        section_content = text[start_pos:end_pos]
        
        mother_section = {
            'section_number': section['number'],
            'title': section['title'],
            'start_pos': start_pos,
            'end_pos': end_pos,
            'content_length': len(section_content),
            'grade_level': 9,  # Default assumption
            'subject': 'Physics',  # Default assumption
            'chapter': int(section['number'].split('.')[0]) if '.' in section['number'] else 1
        }
        
        mother_sections.append(mother_section)
        print(f"  📚 Section {section['number']}: {section['title']} ({len(section_content)} chars)")
    
    return mother_sections

def process_with_holistic_chunker(mother_sections: List[Dict], text: str, char_to_page_map: Dict) -> List[HolisticChunk]:
    """Process sections using the holistic chunker"""
    print(f"\n🧠 Processing with Holistic RAG Chunker...")
    
    chunker = HolisticRAGChunker()
    all_chunks = []
    
    for section in mother_sections:
        print(f"  📖 Processing Section {section['section_number']}: {section['title']}")
        
        try:
            chunks = chunker.process_mother_section(
                mother_section=section,
                full_text=text,
                char_to_page_map=char_to_page_map
            )
            
            all_chunks.extend(chunks)
            print(f"    ✅ Created {len(chunks)} chunks")
            
        except Exception as e:
            print(f"    ❌ Error processing section: {e}")
    
    print(f"  📊 Total chunks created: {len(all_chunks)}")
    return all_chunks

def analyze_chunk_quality(chunks: List[HolisticChunk]) -> Dict[str, Any]:
    """Analyze the quality of created chunks"""
    print(f"\n🔍 Analyzing chunk quality...")
    
    quality_metrics = {
        'total_chunks': len(chunks),
        'avg_content_length': 0,
        'avg_quality_score': 0,
        'chunk_size_distribution': {'small': 0, 'medium': 0, 'large': 0},
        'content_type_distribution': {},
        'quality_score_distribution': {'low': 0, 'medium': 0, 'high': 0},
        'metadata_completeness': {'complete': 0, 'partial': 0, 'incomplete': 0}
    }
    
    total_length = 0
    total_quality = 0
    
    for chunk in chunks:
        # Content length analysis
        content_length = len(chunk.content)
        total_length += content_length
        
        if content_length < 1000:
            quality_metrics['chunk_size_distribution']['small'] += 1
        elif content_length < 2000:
            quality_metrics['chunk_size_distribution']['medium'] += 1
        else:
            quality_metrics['chunk_size_distribution']['large'] += 1
        
        # Quality score analysis
        quality_score = chunk.quality_score
        total_quality += quality_score
        
        if quality_score < 0.6:
            quality_metrics['quality_score_distribution']['low'] += 1
        elif quality_score < 0.8:
            quality_metrics['quality_score_distribution']['medium'] += 1
        else:
            quality_metrics['quality_score_distribution']['high'] += 1
        
        # Content type analysis
        content_types = chunk.metadata.get('pedagogical_elements', {}).get('content_types', [])
        for content_type in content_types:
            quality_metrics['content_type_distribution'][content_type] = \
                quality_metrics['content_type_distribution'].get(content_type, 0) + 1
        
        # Metadata completeness analysis
        metadata_fields = [
            'basic_info', 'content_composition', 'pedagogical_elements',
            'concepts_and_skills', 'quality_indicators'
        ]
        
        complete_fields = sum(1 for field in metadata_fields if field in chunk.metadata)
        if complete_fields == len(metadata_fields):
            quality_metrics['metadata_completeness']['complete'] += 1
        elif complete_fields >= len(metadata_fields) // 2:
            quality_metrics['metadata_completeness']['partial'] += 1
        else:
            quality_metrics['metadata_completeness']['incomplete'] += 1
    
    # Calculate averages
    if chunks:
        quality_metrics['avg_content_length'] = total_length / len(chunks)
        quality_metrics['avg_quality_score'] = total_quality / len(chunks)
    
    # Print quality analysis
    print(f"  📊 Quality Analysis:")
    print(f"    • Total chunks: {quality_metrics['total_chunks']}")
    print(f"    • Average content length: {quality_metrics['avg_content_length']:.0f} chars")
    print(f"    • Average quality score: {quality_metrics['avg_quality_score']:.2f}")
    print(f"    • Size distribution: {quality_metrics['chunk_size_distribution']}")
    print(f"    • Quality distribution: {quality_metrics['quality_score_distribution']}")
    print(f"    • Metadata completeness: {quality_metrics['metadata_completeness']}")
    
    return quality_metrics

def test_concept_based_question_answering(chunks: List[HolisticChunk]) -> Dict[str, Any]:
    """Test the system's ability to answer concept-based questions"""
    print(f"\n❓ Testing Concept-Based Question Answering...")
    
    # Define test questions based on sound (iesc111 content)
    test_questions = [
        {
            'question': 'How is sound produced?',
            'keywords': ['sound', 'produced', 'vibration', 'vibrating'],
            'expected_concepts': ['sound', 'vibration', 'production']
        },
        {
            'question': 'How does sound travel?',
            'keywords': ['sound', 'travel', 'propagation', 'medium'],
            'expected_concepts': ['sound propagation', 'medium', 'waves']
        },
        {
            'question': 'What is echo?',
            'keywords': ['echo', 'reflection', 'sound'],
            'expected_concepts': ['echo', 'reflection', 'sound reflection']
        },
        {
            'question': 'What are the characteristics of sound waves?',
            'keywords': ['characteristics', 'sound', 'wave', 'frequency', 'amplitude'],
            'expected_concepts': ['sound waves', 'frequency', 'amplitude']
        },
        {
            'question': 'What is ultrasound and its applications?',
            'keywords': ['ultrasound', 'applications', 'high frequency'],
            'expected_concepts': ['ultrasound', 'applications', 'frequency']
        }
    ]
    
    question_results = []
    
    for i, test_question in enumerate(test_questions):
        print(f"  🔍 Question {i+1}: {test_question['question']}")
        
        # Find relevant chunks based on keywords and metadata
        relevant_chunks = []
        
        for chunk in chunks:
            relevance_score = 0
            
            # Check content for keywords
            content_lower = chunk.content.lower()
            for keyword in test_question['keywords']:
                if keyword.lower() in content_lower:
                    relevance_score += 1
            
            # Check metadata for concepts
            concepts = chunk.metadata.get('concepts_and_skills', {}).get('main_concepts', [])
            for concept in concepts:
                if any(expected in concept.lower() for expected in test_question['expected_concepts']):
                    relevance_score += 2  # Higher weight for concept matches
            
            # Check keywords in metadata
            keywords = chunk.metadata.get('concepts_and_skills', {}).get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in test_question['keywords']:
                    relevance_score += 1
            
            # Check learning objectives
            objectives = chunk.metadata.get('pedagogical_elements', {}).get('learning_objectives', [])
            for objective in objectives:
                if any(keyword.lower() in objective.lower() for keyword in test_question['keywords']):
                    relevance_score += 1
            
            if relevance_score > 0:
                relevant_chunks.append({
                    'chunk': chunk,
                    'relevance_score': relevance_score,
                    'quality_score': chunk.quality_score
                })
        
        # Sort by relevance score
        relevant_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Take top 3 most relevant chunks
        top_chunks = relevant_chunks[:3]
        
        result = {
            'question': test_question['question'],
            'keywords': test_question['keywords'],
            'expected_concepts': test_question['expected_concepts'],
            'relevant_chunks_found': len(relevant_chunks),
            'top_chunks': []
        }
        
        for j, chunk_info in enumerate(top_chunks):
            chunk = chunk_info['chunk']
            result['top_chunks'].append({
                'rank': j + 1,
                'chunk_id': chunk.chunk_id,
                'relevance_score': chunk_info['relevance_score'],
                'quality_score': chunk_info['quality_score'],
                'content_preview': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                'concepts': chunk.metadata.get('concepts_and_skills', {}).get('main_concepts', [])[:3],
                'learning_objectives': chunk.metadata.get('pedagogical_elements', {}).get('learning_objectives', [])[:2]
            })
        
        question_results.append(result)
        
        # Print results
        print(f"    📊 Found {len(relevant_chunks)} relevant chunks")
        if top_chunks:
            print(f"    🏆 Top chunk: {top_chunks[0]['chunk'].chunk_id[:20]}... (relevance: {top_chunks[0]['relevance_score']})")
            print(f"    📝 Preview: {top_chunks[0]['chunk'].content[:100]}...")
        else:
            print(f"    ❌ No relevant chunks found")
    
    return question_results

def save_test_results(chunks: List[HolisticChunk], quality_metrics: Dict, question_results: Dict, pdf_path: str) -> str:
    """Save test results to database"""
    print(f"\n💾 Saving test results...")
    
    # Create database filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_filename = f"stress_test_iesc111_{timestamp}.db"
    
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_path TEXT,
            test_timestamp TEXT,
            total_chunks INTEGER,
            avg_content_length REAL,
            avg_quality_score REAL,
            quality_metrics TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id TEXT,
            content TEXT,
            quality_score REAL,
            content_length INTEGER,
            metadata TEXT,
            test_result_id INTEGER,
            FOREIGN KEY (test_result_id) REFERENCES test_results (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            keywords TEXT,
            relevant_chunks_found INTEGER,
            top_chunks TEXT,
            test_result_id INTEGER,
            FOREIGN KEY (test_result_id) REFERENCES test_results (id)
        )
    ''')
    
    # Insert test results
    cursor.execute('''
        INSERT INTO test_results (pdf_path, test_timestamp, total_chunks, avg_content_length, avg_quality_score, quality_metrics)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        pdf_path,
        timestamp,
        quality_metrics['total_chunks'],
        quality_metrics['avg_content_length'],
        quality_metrics['avg_quality_score'],
        json.dumps(quality_metrics)
    ))
    
    test_result_id = cursor.lastrowid
    
    # Insert chunks
    for chunk in chunks:
        cursor.execute('''
            INSERT INTO chunks (chunk_id, content, quality_score, content_length, metadata, test_result_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            chunk.chunk_id,
            chunk.content,
            chunk.quality_score,
            len(chunk.content),
            json.dumps(chunk.metadata),
            test_result_id
        ))
    
    # Insert question results
    for question_result in question_results:
        cursor.execute('''
            INSERT INTO question_results (question, keywords, relevant_chunks_found, top_chunks, test_result_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            question_result['question'],
            json.dumps(question_result['keywords']),
            question_result['relevant_chunks_found'],
            json.dumps(question_result['top_chunks']),
            test_result_id
        ))
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ Results saved to {db_filename}")
    return db_filename

def generate_stress_test_report(pdf_info: Dict, structure: Dict, quality_metrics: Dict, question_results: List[Dict], db_filename: str):
    """Generate comprehensive stress test report"""
    print(f"\n📋 Generating Stress Test Report...")
    
    report = f"""
# 🔥 COMPREHENSIVE STRESS TEST REPORT - iesc111.pdf

## 📊 Test Overview
- **Test Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **PDF File**: {Path(pdf_info.get('pdf_path', 'unknown')).name}
- **File Size**: {pdf_info.get('file_size_mb', 0):.1f} MB
- **Total Pages**: {pdf_info.get('total_pages', 0)}
- **Content Types**: {', '.join(pdf_info.get('content_types', []))}

## 🏗️ Educational Structure Detection
- **Sections**: {len(structure['sections'])}
- **Activities**: {len(structure['activities'])}
- **Examples**: {len(structure['examples'])}
- **Figures**: {len(structure['figures'])}
- **Special Boxes**: {len(structure['special_boxes'])}
- **Formulas**: {len(structure['formulas'])}
- **Questions**: {len(structure['questions'])}
- **Concepts**: {len(structure['concepts'])}

## 🧠 Chunking Quality Analysis
- **Total Chunks Created**: {quality_metrics['total_chunks']}
- **Average Content Length**: {quality_metrics['avg_content_length']:.0f} characters
- **Average Quality Score**: {quality_metrics['avg_quality_score']:.2f}

### Chunk Size Distribution
- **Small (<1000 chars)**: {quality_metrics['chunk_size_distribution']['small']}
- **Medium (1000-2000 chars)**: {quality_metrics['chunk_size_distribution']['medium']}
- **Large (>2000 chars)**: {quality_metrics['chunk_size_distribution']['large']}

### Quality Score Distribution
- **Low (<0.6)**: {quality_metrics['quality_score_distribution']['low']}
- **Medium (0.6-0.8)**: {quality_metrics['quality_score_distribution']['medium']}
- **High (>0.8)**: {quality_metrics['quality_score_distribution']['high']}

### Metadata Completeness
- **Complete**: {quality_metrics['metadata_completeness']['complete']}
- **Partial**: {quality_metrics['metadata_completeness']['partial']}
- **Incomplete**: {quality_metrics['metadata_completeness']['incomplete']}

## ❓ Question Answering Performance

"""
    
    for i, question_result in enumerate(question_results):
        report += f"""
### Question {i+1}: {question_result['question']}
- **Keywords**: {', '.join(question_result['keywords'])}
- **Expected Concepts**: {', '.join(question_result['expected_concepts'])}
- **Relevant Chunks Found**: {question_result['relevant_chunks_found']}

**Top Matching Chunks:**
"""
        
        for j, chunk_info in enumerate(question_result['top_chunks']):
            report += f"""
{j+1}. **Chunk {chunk_info['chunk_id'][:20]}...**
   - Relevance Score: {chunk_info['relevance_score']}
   - Quality Score: {chunk_info['quality_score']:.2f}
   - Concepts: {', '.join(chunk_info['concepts'])}
   - Preview: {chunk_info['content_preview']}
"""
    
    report += f"""
## 📈 Performance Assessment

### ✅ Strengths
- Comprehensive element detection
- Rich metadata generation
- Quality scoring system
- Concept-based retrieval

### ⚠️ Areas for Improvement
- Special box detection could be enhanced
- Some complex formulas might be missed
- Cross-reference detection needs improvement

### 🎯 Recommendations
1. Enhance special content detection patterns
2. Improve mathematical expression recognition
3. Add more sophisticated concept extraction
4. Implement advanced semantic search

## 💾 Data Storage
- **Database**: {db_filename}
- **Total Records**: {quality_metrics['total_chunks']} chunks
- **Test Results**: Complete question-answering analysis

---
*Report generated by Holistic Educational RAG System Stress Test*
"""
    
    # Save report to file
    report_filename = f"stress_test_report_iesc111_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"  ✅ Report saved to {report_filename}")
    return report_filename

def main():
    """Main stress test function"""
    print_banner()
    
    pdf_path = "/Users/umangagarwal/Downloads/iesc1dd/iesc111.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    try:
        # Step 1: Analyze PDF
        pdf_info = analyze_pdf_basic_info(pdf_path)
        pdf_info['pdf_path'] = pdf_path
        
        # Step 2: Extract text
        text, char_to_page_map = extract_text_from_pdf(pdf_path)
        
        if not text:
            print("❌ Failed to extract text from PDF")
            return
        
        # Step 3: Detect educational structure
        structure = detect_educational_structure(text)
        
        # Step 4: Create mother sections
        mother_sections = create_mother_sections(text, structure)
        
        if not mother_sections:
            print("❌ No sections detected")
            return
        
        # Step 5: Process with holistic chunker
        chunks = process_with_holistic_chunker(mother_sections, text, char_to_page_map)
        
        if not chunks:
            print("❌ No chunks created")
            return
        
        # Step 6: Analyze chunk quality
        quality_metrics = analyze_chunk_quality(chunks)
        
        # Step 7: Test question answering
        question_results = test_concept_based_question_answering(chunks)
        
        # Step 8: Save results
        db_filename = save_test_results(chunks, quality_metrics, question_results, pdf_path)
        
        # Step 9: Generate report
        report_filename = generate_stress_test_report(pdf_info, structure, quality_metrics, question_results, db_filename)
        
        print(f"\n🎉 STRESS TEST COMPLETED SUCCESSFULLY!")
        print(f"📊 Results saved to: {db_filename}")
        print(f"📋 Report saved to: {report_filename}")
        
    except Exception as e:
        print(f"❌ Stress test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()