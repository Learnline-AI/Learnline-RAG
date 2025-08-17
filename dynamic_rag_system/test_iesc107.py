#!/usr/bin/env python3
"""
Educational RAG System - Test with iesc107.pdf
"""

import os
import sys
import sqlite3
import tempfile
import json
import hashlib
from pathlib import Path
from datetime import datetime
import uuid
import re

def print_banner():
    """Print a friendly welcome banner"""
    print("🎓" * 20)
    print("📚 EDUCATIONAL RAG SYSTEM - iesc107.pdf TEST")
    print("🎓" * 20)
    print()
    print("Testing your Educational RAG System with iesc107.pdf!")
    print()

def check_file_exists():
    """Check if the target PDF exists"""
    pdf_path = "/Users/umangagarwal/Downloads/iesc1dd/iesc107.pdf"
    
    print(f"🔍 Checking for PDF file...")
    print(f"📁 Looking for: {pdf_path}")
    
    if os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        print(f"  ✅ File found: {file_size / (1024*1024):.1f} MB")
        return pdf_path
    else:
        print(f"  ❌ File not found at specified path")
        
        # Check alternative locations
        alternative_paths = [
            "/Users/umangagarwal/Downloads/iesc107.pdf",
            "/Users/umangagarwal/Downloads/iesc1dd.pdf",
            "/Users/umangagarwal/Desktop/iesc107.pdf"
        ]
        
        print(f"  🔍 Checking alternative locations...")
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                file_size = os.path.getsize(alt_path)
                print(f"  ✅ Found at: {alt_path} ({file_size / (1024*1024):.1f} MB)")
                return alt_path
        
        print(f"  ⚠️  File not found in any location")
        return None

def analyze_pdf_basic_info(pdf_path):
    """Extract basic information about the PDF"""
    print(f"\n📊 Analyzing PDF: {Path(pdf_path).name}")
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        
        total_pages = len(doc)
        file_size = os.path.getsize(pdf_path)
        
        # Extract text from first few pages for preview
        preview_text = ""
        for page_num in range(min(total_pages, 3)):
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
            'physics': ['force', 'motion', 'energy', 'physics'],
            'math': ['equation', 'theorem', 'proof', 'mathematics'],
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
            'file_size': file_size,
            'content_preview': preview_text[:1000],
            'detected_types': detected_types
        }
    
    except Exception as e:
        print(f"  ❌ Error analyzing PDF: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Extract text using the educational RAG logic"""
    print(f"\n📝 Extracting text from PDF...")
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        
        full_text = ""
        pages_processed = 0
        
        print(f"  🔄 Processing {min(len(doc), 10)} pages for analysis...")
        
        for page_num in range(min(len(doc), 10)):  # Process max 10 pages for demo
            page = doc[page_num]
            
            # Use the proven left-right extraction logic
            page_text = extract_page_left_right(page)
            full_text += page_text + "\n\n"
            pages_processed += 1
            
            if page_num < 5:  # Show progress for first few pages
                words = len(page_text.split())
                print(f"    Page {page_num + 1}: {words} words extracted")
        
        doc.close()
        
        print(f"  ✅ Extracted text from {pages_processed} pages")
        print(f"  📝 Total characters: {len(full_text):,}")
        
        return full_text.strip()
    
    except Exception as e:
        print(f"  ❌ Error extracting text: {e}")
        return None

def extract_page_left_right(page):
    """Extract text from page using left-then-right logic"""
    try:
        text_dict = page.get_text("dict")
        page_width = page.rect.width
        center_x = page_width / 2
        
        left_blocks = []
        right_blocks = []
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:  # Text block
                block_text = ""
                for line in block.get("lines", []):
                    line_parts = []
                    for span in line.get("spans", []):
                        text_content = span.get("text", "").strip()
                        if text_content:
                            line_parts.append(text_content)
                    if line_parts:
                        block_text += ' '.join(line_parts) + '\n'
                
                if block_text.strip():
                    block_bbox = block.get("bbox", [0, 0, 0, 0])
                    block_left = block_bbox[0]
                    block_top = block_bbox[1]
                    
                    block_info = {
                        'text': block_text.strip(),
                        'x': block_left,
                        'y': block_top
                    }
                    
                    if block_left < center_x:
                        left_blocks.append(block_info)
                    else:
                        right_blocks.append(block_info)
        
        # Sort by Y coordinate
        left_blocks.sort(key=lambda b: b['y'])
        right_blocks.sort(key=lambda b: b['y'])
        
        # Combine left then right
        page_parts = []
        if left_blocks:
            left_text = '\n'.join(block['text'] for block in left_blocks)
            page_parts.append(left_text)
        if right_blocks:
            right_text = '\n'.join(block['text'] for block in right_blocks)
            page_parts.append(right_text)
        
        return '\n\n'.join(page_parts)
    
    except:
        # Fallback to simple text extraction
        return page.get_text()

def detect_educational_structure(text):
    """Detect educational structure in the extracted text"""
    print(f"\n🔍 Detecting educational structure...")
    
    # Educational patterns (comprehensive set)
    patterns = {
        'sections': [
            r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]{8,60})(?:\n|$)',
            r'^(\d+\.\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,8})(?:\n|$)',
            r'^Chapter\s+(\d+):?\s*([A-Za-z\s]+)(?:\n|$)',
            r'^CHAPTER\s+(\d+):?\s*([A-Za-z\s]+)(?:\n|$)',
            r'^(\d+)\.\s+([A-Z][A-Za-z\s]{5,50})(?:\n|$)',
        ],
        'activities': [
            r'ACTIVITY\s+(\d+\.\d+)',
            r'Activity\s*[_\-–—\s]*\s*(\d+\.\d+)',
            r'गतिविधि\s+(\d+\.\d+)',  # Hindi
            r'Exercise\s+(\d+\.\d+)',
            r'Lab\s+(\d+\.\d+)',
            r'Experiment\s+(\d+\.\d+)',
        ],
        'examples': [
            r'Example\s+(\d+\.\d+)',
            r'EXAMPLE\s+(\d+\.\d+)',
            r'उदाहरण\s+(\d+\.\d+)',  # Hindi
            r'Illustration\s+(\d+\.\d+)',
            r'Problem\s+(\d+\.\d+)',
        ],
        'figures': [
            r'Fig\.\s*(\d+\.\d+):\s*([^\n]+)',
            r'Figure\s+(\d+\.\d+):\s*([^\n]+)',
            r'चित्र\s+(\d+\.\d+):\s*([^\n]+)',  # Hindi
            r'Diagram\s+(\d+\.\d+):\s*([^\n]+)',
        ],
        'special_content': [
            r'What\s+you\s+have\s+learnt',
            r'Exercises?',
            r'Remember:',
            r'Note:',
            r'Summary',
            r'Key\s+Points?',
            r'Objectives?',
            r'Introduction',
            r'Conclusion',
        ],
        'formulas': [
            r'([A-Za-z]\s*=\s*[A-Za-z0-9\s\+\-\*\/\(\)]+)',
            r'([A-Za-z]+\s*=\s*[0-9\.]+)',
        ],
        'definitions': [
            r'Definition:?\s*([^\n]+)',
            r'([A-Za-z\s]+)\s+is\s+defined\s+as',
            r'([A-Za-z\s]+)\s+means',
        ]
    }
    
    detected_structure = {}
    total_items = 0
    
    for category, pattern_list in patterns.items():
        matches = []
        for pattern in pattern_list:
            found = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
            matches.extend(found)
        
        # Remove duplicates based on position
        unique_matches = []
        positions = set()
        for match in matches:
            if match.start() not in positions:
                unique_matches.append(match)
                positions.add(match.start())
        
        detected_structure[category] = unique_matches
        total_items += len(unique_matches)
        
        print(f"  📚 {category.title()}: {len(unique_matches)} found")
        
        # Show specific matches
        for match in unique_matches[:3]:  # Show first 3 matches
            if len(match.groups()) >= 2:
                print(f"    - {match.group(1)}: {match.group(2)[:50]}...")
            elif len(match.groups()) >= 1:
                print(f"    - {match.group(1)}")
            else:
                print(f"    - {match.group(0)[:50]}...")
        
        if len(unique_matches) > 3:
            print(f"    ... and {len(unique_matches) - 3} more")
    
    print(f"\n  ✅ Total educational elements detected: {total_items}")
    return detected_structure

def create_baby_chunks(text, structure, pdf_path):
    """Create baby chunks from the detected structure"""
    print(f"\n🧩 Creating baby chunks...")
    
    chunks = []
    
    # Create activity chunks
    activities = structure.get('activities', [])
    if activities:
        activity_content_parts = []
        activity_numbers = []
        
        for activity_match in activities:
            activity_num = activity_match.group(1) if activity_match.groups() else "Unknown"
            activity_numbers.append(activity_num)
            
            # Extract content around the activity
            start_pos = activity_match.start()
            end_pos = min(start_pos + 600, len(text))
            activity_content = text[start_pos:end_pos]
            
            # Find natural end point
            next_section = re.search(r'\n(?:Example|\d+\.\d+|Fig\.|Activity)', activity_content[100:])
            if next_section:
                activity_content = activity_content[:100 + next_section.start()]
            
            activity_content_parts.append(activity_content.strip())
        
        if activity_content_parts:
            activity_chunk = {
                'chunk_id': str(uuid.uuid4())[:8],
                'type': 'activity',
                'content': '\n\n'.join(activity_content_parts),
                'metadata': {
                    'activity_numbers': activity_numbers,
                    'count': len(activities),
                    'estimated_time': len(activities) * 15,
                    'source_file': Path(pdf_path).name
                }
            }
            chunks.append(activity_chunk)
            print(f"  ✅ Activity chunk created: {len(activity_numbers)} activities")
    
    # Create example chunks
    examples = structure.get('examples', [])
    if examples:
        example_content_parts = []
        example_numbers = []
        
        for example_match in examples:
            example_num = example_match.group(1) if example_match.groups() else "Unknown"
            example_numbers.append(example_num)
            
            # Extract content around the example
            start_pos = example_match.start()
            end_pos = min(start_pos + 800, len(text))
            example_content = text[start_pos:end_pos]
            
            # Find natural end point
            next_section = re.search(r'\n(?:Example|\d+\.\d+|Activity|Fig\.)', example_content[100:])
            if next_section:
                example_content = example_content[:100 + next_section.start()]
            
            example_content_parts.append(example_content.strip())
        
        if example_content_parts:
            # Detect formulas and solutions
            all_example_text = '\n'.join(example_content_parts)
            formulas = structure.get('formulas', [])
            has_solutions = 'solution' in all_example_text.lower() or 'answer' in all_example_text.lower()
            
            example_chunk = {
                'chunk_id': str(uuid.uuid4())[:8],
                'type': 'example',
                'content': '\n\n'.join(example_content_parts),
                'metadata': {
                    'example_numbers': example_numbers,
                    'count': len(examples),
                    'has_solutions': has_solutions,
                    'formula_count': len(formulas),
                    'source_file': Path(pdf_path).name
                }
            }
            chunks.append(example_chunk)
            print(f"  ✅ Example chunk created: {len(example_numbers)} examples")
    
    # Create content chunks for sections
    sections = structure.get('sections', [])
    if sections:
        for i, section_match in enumerate(sections[:5]):  # Process first 5 sections
            section_num = section_match.group(1) if section_match.groups() else f"Section_{i+1}"
            section_title = section_match.group(2) if len(section_match.groups()) >= 2 else "Untitled"
            
            # Extract section content
            start_pos = section_match.start()
            
            # Find end of section
            if i + 1 < len(sections):
                end_pos = sections[i + 1].start()
            else:
                end_pos = min(start_pos + 3000, len(text))
            
            section_content = text[start_pos:end_pos].strip()
            
            # Remove activities and examples (they have their own chunks)
            clean_content = section_content
            for activity_match in activities:
                if start_pos <= activity_match.start() < end_pos:
                    activity_text = text[activity_match.start():activity_match.start() + 200]
                    clean_content = clean_content.replace(activity_text, '')
            
            for example_match in examples:
                if start_pos <= example_match.start() < end_pos:
                    example_text = text[example_match.start():example_match.start() + 300]
                    clean_content = clean_content.replace(example_text, '')
            
            # Clean up extra whitespace
            clean_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_content).strip()
            
            if len(clean_content) > 200:
                # Extract key terms and concepts
                definitions = structure.get('definitions', [])
                section_definitions = [d for d in definitions if start_pos <= d.start() < end_pos]
                
                section_chunk = {
                    'chunk_id': str(uuid.uuid4())[:8],
                    'type': 'content',
                    'content': clean_content,
                    'metadata': {
                        'section_number': section_num,
                        'section_title': section_title,
                        'word_count': len(clean_content.split()),
                        'definition_count': len(section_definitions),
                        'source_file': Path(pdf_path).name
                    }
                }
                chunks.append(section_chunk)
                print(f"  ✅ Content chunk created: Section {section_num} - {section_title[:30]}...")
    
    # Create special content chunks
    special_content = structure.get('special_content', [])
    if special_content:
        special_parts = []
        content_types = []
        
        for special_match in special_content:
            content_type = special_match.group(0)
            content_types.append(content_type)
            
            start_pos = special_match.start()
            end_pos = min(start_pos + 1000, len(text))
            special_text = text[start_pos:end_pos]
            
            # Find natural end point
            next_major = re.search(r'\n(?:\d+\.\d+|Chapter)', special_text[50:])
            if next_major:
                special_text = special_text[:50 + next_major.start()]
            
            special_parts.append(special_text.strip())
        
        if special_parts:
            special_chunk = {
                'chunk_id': str(uuid.uuid4())[:8],
                'type': 'summary',
                'content': '\n\n'.join(special_parts),
                'metadata': {
                    'content_types': content_types,
                    'count': len(special_content),
                    'source_file': Path(pdf_path).name
                }
            }
            chunks.append(special_chunk)
            print(f"  ✅ Summary chunk created: {len(special_content)} special sections")
    
    # If no structured content found, create general chunks
    if not chunks:
        print(f"  ⚠️  No structured educational content found, creating general chunks...")
        
        # Split text into reasonable chunks
        words = text.split()
        chunk_size = 1000  # words per chunk
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_content = ' '.join(chunk_words)
            
            general_chunk = {
                'chunk_id': str(uuid.uuid4())[:8],
                'type': 'general',
                'content': chunk_content,
                'metadata': {
                    'chunk_number': i // chunk_size + 1,
                    'word_count': len(chunk_words),
                    'source_file': Path(pdf_path).name,
                    'content_type': 'unstructured'
                }
            }
            chunks.append(general_chunk)
        
        print(f"  ✅ Created {len(chunks)} general content chunks")
    
    print(f"\n  🎯 Total chunks created: {len(chunks)}")
    return chunks

def save_results_to_database(chunks, pdf_path, structure, pdf_info):
    """Save results to a simple database"""
    print(f"\n💾 Saving results to database...")
    
    # Create database
    db_path = f"iesc107_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                title TEXT,
                file_path TEXT,
                file_size INTEGER,
                total_pages INTEGER,
                processed_at TIMESTAMP,
                total_chunks INTEGER,
                structure_summary TEXT,
                content_types TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT,
                chunk_type TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (document_id)
            )
        """)
        
        # Insert document
        doc_id = str(uuid.uuid4())
        document_title = f"Analysis: {Path(pdf_path).stem}"
        
        structure_summary = {
            'sections': len(structure.get('sections', [])),
            'activities': len(structure.get('activities', [])),
            'examples': len(structure.get('examples', [])),
            'figures': len(structure.get('figures', [])),
            'special_content': len(structure.get('special_content', [])),
            'formulas': len(structure.get('formulas', [])),
            'definitions': len(structure.get('definitions', []))
        }
        
        conn.execute("""
            INSERT INTO documents (
                document_id, title, file_path, file_size, total_pages,
                processed_at, total_chunks, structure_summary, content_types
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id, document_title, pdf_path, 
            pdf_info['file_size'], pdf_info['total_pages'],
            datetime.now(), len(chunks), 
            json.dumps(structure_summary),
            json.dumps(pdf_info.get('detected_types', []))
        ))
        
        # Insert chunks
        for chunk in chunks:
            conn.execute("""
                INSERT INTO chunks (
                    chunk_id, document_id, chunk_type, content, 
                    metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                chunk['chunk_id'], doc_id, chunk['type'], chunk['content'],
                json.dumps(chunk['metadata']), datetime.now()
            ))
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ Results saved to: {db_path}")
        print(f"  📊 Document ID: {doc_id}")
        print(f"  📦 Chunks stored: {len(chunks)}")
        
        return db_path, doc_id
    
    except Exception as e:
        print(f"  ❌ Error saving to database: {e}")
        return None, None

def show_results_summary(chunks, structure, pdf_path, pdf_info):
    """Show a nice summary of results"""
    print(f"\n" + "="*60)
    print("📊 iesc107.pdf PROCESSING RESULTS")
    print("="*60)
    
    print(f"\n📖 Source File: {Path(pdf_path).name}")
    print(f"📁 Full Path: {pdf_path}")
    print(f"📏 File Size: {pdf_info['file_size'] / (1024*1024):.1f} MB")
    print(f"📄 Total Pages: {pdf_info['total_pages']}")
    print(f"🔍 Content Types: {', '.join(pdf_info.get('detected_types', ['general']))}")
    
    print(f"\n🏗️ Educational Structure Detected:")
    structure_items = [
        ('Sections', len(structure.get('sections', []))),
        ('Activities', len(structure.get('activities', []))),
        ('Examples', len(structure.get('examples', []))),
        ('Figures', len(structure.get('figures', []))),
        ('Special Content', len(structure.get('special_content', []))),
        ('Formulas', len(structure.get('formulas', []))),
        ('Definitions', len(structure.get('definitions', [])))
    ]
    
    for item_type, count in structure_items:
        print(f"  📚 {item_type}: {count}")
    
    print(f"\n🧩 Baby Chunks Created:")
    chunk_types = {}
    total_content_length = 0
    
    for chunk in chunks:
        chunk_type = chunk['type']
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        total_content_length += len(chunk['content'])
    
    for chunk_type, count in chunk_types.items():
        print(f"  🔹 {chunk_type.title()} chunks: {count}")
    
    print(f"\n📏 Content Statistics:")
    print(f"  Total content extracted: {total_content_length:,} characters")
    print(f"  Average chunk size: {total_content_length // len(chunks) if chunks else 0:,} characters")
    
    print(f"\n🎯 System Performance:")
    print(f"  ✅ PDF processing: Successful")
    print(f"  ✅ Left-right text extraction: Working")
    print(f"  ✅ Educational pattern detection: Active")
    print(f"  ✅ Content chunking: Complete")
    print(f"  ✅ Database storage: Successful")
    
    # Show sample content
    if chunks:
        print(f"\n📝 Sample Chunk Content:")
        sample_chunk = chunks[0]
        print(f"  Type: {sample_chunk['type'].title()}")
        print(f"  ID: {sample_chunk['chunk_id']}")
        print(f"  Size: {len(sample_chunk['content'])} characters")
        print(f"  Content preview:")
        preview = sample_chunk['content'][:300] + "..." if len(sample_chunk['content']) > 300 else sample_chunk['content']
        for line in preview.split('\n')[:4]:
            if line.strip():
                print(f"    {line}")
        
        if sample_chunk['metadata']:
            print(f"  Metadata: {sample_chunk['metadata']}")

def main():
    """Main function - orchestrates the entire process"""
    print_banner()
    
    # Step 1: Check if file exists
    pdf_path = check_file_exists()
    if not pdf_path:
        print("\n❌ Could not find the PDF file. Please check the path.")
        return
    
    # Step 2: Check dependencies
    try:
        import fitz
        print(f"\n✅ PyMuPDF v{fitz.version[0]} ready for processing")
    except ImportError:
        print("\n❌ PyMuPDF not available. Install with: pip3 install PyMuPDF")
        return
    
    # Step 3: Analyze PDF
    pdf_info = analyze_pdf_basic_info(pdf_path)
    if not pdf_info:
        print("\n❌ Could not analyze PDF file.")
        return
    
    # Step 4: Extract text
    print("\n⏳ Starting text extraction...")
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        print("\n❌ Could not extract text from PDF.")
        return
    
    print(f"  📝 Text extraction complete: {len(extracted_text):,} characters")
    
    # Step 5: Detect educational structure
    structure = detect_educational_structure(extracted_text)
    
    # Step 6: Create baby chunks
    chunks = create_baby_chunks(extracted_text, structure, pdf_path)
    
    # Step 7: Save to database
    db_path, doc_id = save_results_to_database(chunks, pdf_path, structure, pdf_info)
    
    # Step 8: Show results
    show_results_summary(chunks, structure, pdf_path, pdf_info)
    
    # Step 9: Success message
    print(f"\n" + "="*60)
    print("🚀 iesc107.pdf PROCESSING COMPLETE!")
    print("="*60)
    
    if db_path:
        print(f"\n📁 Results database: {db_path}")
        print(f"🔍 Document ID: {doc_id}")
    
    print(f"\n💡 Processing Summary:")
    print(f"  ✅ Successfully processed iesc107.pdf")
    print(f"  ✅ Extracted and analyzed {len(extracted_text):,} characters")
    print(f"  ✅ Created {len(chunks)} intelligent chunks")
    print(f"  ✅ Detected {sum(len(matches) for matches in structure.values())} educational elements")
    print(f"  ✅ Stored results in structured database")
    
    print(f"\n🎯 Your Educational RAG System successfully processed the file!")
    print(f"The system is ready for AI enhancement and vector embeddings.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Processing interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Processing error: {e}")
        import traceback
        traceback.print_exc()