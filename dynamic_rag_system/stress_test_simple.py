#!/usr/bin/env python3
"""
Simple Stress Test for iesc111.pdf
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker

def test_iesc111_pdf():
    """Test iesc111.pdf with comprehensive analysis"""
    print("🔥 STRESS TEST: iesc111.pdf")
    print("=" * 60)
    
    pdf_path = "/Users/umangagarwal/Downloads/iesc1dd/iesc111.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Analyze PDF
    print(f"📊 Analyzing PDF: {Path(pdf_path).name}")
    file_size = os.path.getsize(pdf_path) / (1024*1024)
    print(f"   Size: {file_size:.1f} MB")
    
    # Extract text
    print(f"\n📖 Extracting text...")
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        total_pages = len(doc)
        
        for page_num in range(total_pages):
            page = doc[page_num]
            page_text = page.get_text()
            text += page_text + "\n"
        
        doc.close()
        print(f"   ✅ Extracted {len(text)} characters from {total_pages} pages")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Create test sections
    print(f"\n🏗️ Creating test sections...")
    
    # Find section headers
    section_pattern = r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]{3,60})(?:\n|$)'
    sections = []
    
    for match in re.finditer(section_pattern, text, re.MULTILINE):
        sections.append({
            'number': match.group(1),
            'title': match.group(2).strip(),
            'position': match.start()
        })
    
    print(f"   Found {len(sections)} sections")
    
    if not sections:
        print("   ⚠️ No sections found, using alternative pattern...")
        # Try alternative pattern
        alt_pattern = r'^(\d+\.\d+)\s+([A-Za-z\s]+)(?:\n|$)'
        for match in re.finditer(alt_pattern, text, re.MULTILINE):
            sections.append({
                'number': match.group(1),
                'title': match.group(2).strip(),
                'position': match.start()
            })
        print(f"   Found {len(sections)} sections with alternative pattern")
    
    if not sections:
        print("   ❌ No sections detected, creating manual sections...")
        # Create manual sections based on content length
        section_size = len(text) // 3
        sections = [
            {'number': '1.1', 'title': 'First Section', 'position': 0},
            {'number': '1.2', 'title': 'Second Section', 'position': section_size},
            {'number': '1.3', 'title': 'Third Section', 'position': section_size * 2}
        ]
    
    # Create mother sections
    mother_sections = []
    for i, section in enumerate(sections):
        start_pos = section['position']
        if i < len(sections) - 1:
            end_pos = sections[i + 1]['position']
        else:
            end_pos = len(text)
        
        mother_sections.append({
            'section_number': section['number'],
            'title': section['title'],
            'start_pos': start_pos,
            'end_pos': end_pos,
            'grade_level': 9,
            'subject': 'Physics',
            'chapter': int(section['number'].split('.')[0]) if '.' in section['number'] else 1
        })
    
    # Process with chunker
    print(f"\n🧠 Processing with Holistic Chunker...")
    chunker = HolisticRAGChunker()
    all_chunks = []
    
    for section in mother_sections[:3]:  # Test first 3 sections
        print(f"   📚 Section {section['section_number']}: {section['title']}")
        
        try:
            chunks = chunker.process_mother_section(
                mother_section=section,
                full_text=text,
                char_to_page_map={i: 1 for i in range(len(text))}
            )
            all_chunks.extend(chunks)
            print(f"      ✅ Created {len(chunks)} chunks")
            
            # Show chunk details
            for j, chunk in enumerate(chunks):
                print(f"         Chunk {j+1}: {len(chunk.content)} chars, quality: {chunk.quality_score:.2f}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Analyze chunks
    print(f"\n🔍 Analyzing {len(all_chunks)} chunks...")
    
    if not all_chunks:
        print("   ❌ No chunks created")
        return
    
    total_length = sum(len(chunk.content) for chunk in all_chunks)
    avg_length = total_length / len(all_chunks)
    avg_quality = sum(chunk.quality_score for chunk in all_chunks) / len(all_chunks)
    
    print(f"   📊 Average chunk length: {avg_length:.0f} characters")
    print(f"   📊 Average quality score: {avg_quality:.2f}")
    
    # Analyze chunk sizes
    small_chunks = sum(1 for chunk in all_chunks if len(chunk.content) < 1000)
    medium_chunks = sum(1 for chunk in all_chunks if 1000 <= len(chunk.content) < 2000)
    large_chunks = sum(1 for chunk in all_chunks if len(chunk.content) >= 2000)
    
    print(f"   📊 Size distribution: Small({small_chunks}), Medium({medium_chunks}), Large({large_chunks})")
    
    # Analyze quality scores
    low_quality = sum(1 for chunk in all_chunks if chunk.quality_score < 0.6)
    medium_quality = sum(1 for chunk in all_chunks if 0.6 <= chunk.quality_score < 0.8)
    high_quality = sum(1 for chunk in all_chunks if chunk.quality_score >= 0.8)
    
    print(f"   📊 Quality distribution: Low({low_quality}), Medium({medium_quality}), High({high_quality})")
    
    # Test question answering
    print(f"\n❓ Testing Question Answering...")
    
    test_questions = [
        "What is the relationship between force and acceleration?",
        "How do we calculate velocity?",
        "What are the different types of forces?",
        "Explain the concept of motion.",
        "What is the formula for work done?"
    ]
    
    for i, question in enumerate(test_questions):
        print(f"   🔍 Q{i+1}: {question}")
        
        # Find relevant chunks
        relevant_chunks = []
        keywords = question.lower().split()
        
        for chunk in all_chunks:
            score = 0
            content_lower = chunk.content.lower()
            
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
            
            # Check metadata
            concepts = chunk.metadata.get('concepts_and_skills', {}).get('main_concepts', [])
            for concept in concepts:
                if any(keyword in concept.lower() for keyword in keywords):
                    score += 2
            
            if score > 0:
                relevant_chunks.append((chunk, score))
        
        # Sort by relevance
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        
        if relevant_chunks:
            top_chunk = relevant_chunks[0][0]
            print(f"      🏆 Top match: {top_chunk.chunk_id[:20]}... (score: {relevant_chunks[0][1]})")
            print(f"      📝 Preview: {top_chunk.content[:100]}...")
            print(f"      📊 Quality: {top_chunk.quality_score:.2f}")
        else:
            print(f"      ❌ No relevant chunks found")
    
    # Test metadata completeness
    print(f"\n📊 Testing Metadata Completeness...")
    
    metadata_fields = ['basic_info', 'content_composition', 'pedagogical_elements', 'concepts_and_skills', 'quality_indicators']
    
    for chunk in all_chunks[:3]:  # Test first 3 chunks
        print(f"   📋 Chunk {chunk.chunk_id[:20]}...")
        missing_fields = []
        
        for field in metadata_fields:
            if field not in chunk.metadata:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"      ❌ Missing: {', '.join(missing_fields)}")
        else:
            print(f"      ✅ All metadata fields present")
    
    print(f"\n✅ Stress test completed!")
    print(f"📊 Processed {len(all_chunks)} chunks from {len(mother_sections[:3])} sections")

if __name__ == "__main__":
    test_iesc111_pdf() 