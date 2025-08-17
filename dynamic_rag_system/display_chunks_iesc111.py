#!/usr/bin/env python3
"""
Display Comprehensive Chunks from iesc111.pdf
Shows all chunks with detailed metadata and analysis
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import traceback

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
from quality_validation_system import QualityValidator

def process_iesc111_and_show_chunks():
    """Process iesc111.pdf and show all chunks with detailed analysis"""
    print("🚀" * 25)
    print("📚 COMPLETE CHUNK DISPLAY: iesc111.pdf")  
    print("🚀" * 25)
    print()
    
    pdf_path = "/Users/umangagarwal/Downloads/iesc1dd/iesc111.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"📁 Processing: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path) / (1024*1024):.1f} MB")
    print()
    
    try:
        # Extract text from PDF
        import fitz
        doc = fitz.open(pdf_path)
        full_text = ""
        for page_num in range(len(doc)):
            page_text = doc[page_num].get_text()
            full_text += page_text + "\n"
        doc.close()
        
        print(f"📝 Extracted {len(full_text):,} characters from PDF")
        
        # Create structure detection
        import re
        sections = []
        section_pattern = r'(\d+\.\d+)\s+([A-Z][^\.]+)'
        section_matches = list(re.finditer(section_pattern, full_text))
        
        print(f"🔍 Found {len(section_matches)} sections")
        
        # Create mother sections
        chunker = HolisticRAGChunker()
        all_chunks = []
        
        for i, section_match in enumerate(section_matches):
            section_number = section_match.group(1)
            section_title = section_match.group(2).strip()
            start_pos = section_match.start()
            
            # Determine end position
            if i + 1 < len(section_matches):
                end_pos = section_matches[i + 1].start()
            else:
                end_pos = len(full_text)
            
            # Extract section content
            section_content = full_text[start_pos:end_pos].strip()
            
            # Create mother section
            mother_section = {
                'section_number': section_number,
                'title': section_title,
                'content': section_content,
                'full_content': section_content,
                'start_pos': start_pos,
                'end_pos': end_pos,
                'page_number': 1,
                'activities': [],
                'examples': [],
                'figures': [],
                'special_content': []
            }
            
            # Process section
            try:
                chunks = chunker.process_mother_section(mother_section, full_text, pdf_path)
                all_chunks.extend(chunks)
                print(f"✅ Section {section_number}: {len(chunks)} chunks")
            except Exception as e:
                print(f"❌ Error in section {section_number}: {e}")
                continue
        
        print(f"\\n🎉 TOTAL CHUNKS GENERATED: {len(all_chunks)}")
        print("=" * 80)
        
        # Display each chunk with comprehensive details
        for i, chunk in enumerate(all_chunks):
            print(f"\\n{'='*60}")
            print(f"🧩 CHUNK {i+1} of {len(all_chunks)}")
            print(f"{'='*60}")
            
            print(f"📝 ID: {chunk.chunk_id}")
            print(f"📊 Size: {len(chunk.content):,} characters")
            print(f"⭐ Quality Score: {chunk.quality_score:.2f}/1.00")
            
            # Content preview
            content_preview = chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content
            print(f"\\n📄 CONTENT PREVIEW:")
            print("-" * 40)
            print(content_preview)
            print("-" * 40)
            
            # Metadata analysis
            if hasattr(chunk, 'metadata') and chunk.metadata:
                metadata = chunk.metadata
                print(f"\\n📋 METADATA ANALYSIS:")
                print(f"   Type: {metadata.get('type', 'unknown')}")
                print(f"   Source: Section {metadata.get('source_section', {}).get('section', 'unknown')}")
                
                # Educational elements
                if 'educational_elements' in metadata:
                    elements = metadata['educational_elements']
                    print(f"\\n🎓 EDUCATIONAL ELEMENTS:")
                    for element_type, items in elements.items():
                        if items and len(items) > 0:
                            print(f"   {element_type.title()}: {len(items)}")
                            if element_type == 'activities' and len(items) > 0:
                                for act in items[:2]:  # Show first 2
                                    print(f"     - {act.get('identifier', 'N/A')}: {act.get('text_preview', '')[:50]}...")
                            elif element_type == 'figures' and len(items) > 0:
                                for fig in items[:2]:  # Show first 2
                                    print(f"     - Fig {fig.get('identifier', 'N/A')}: {fig.get('caption', 'No caption')[:50]}...")
                            elif element_type == 'examples' and len(items) > 0:
                                for ex in items[:2]:  # Show first 2
                                    print(f"     - Example {ex.get('identifier', 'N/A')}: {ex.get('text_preview', '')[:50]}...")
                
                # AI Metadata
                if 'ai_metadata' in metadata and metadata['ai_metadata']:
                    ai_meta = metadata['ai_metadata']
                    print(f"\\n🤖 AI-EXTRACTED METADATA:")
                    
                    # Concepts
                    if 'main_concepts' in ai_meta and ai_meta['main_concepts']:
                        concepts = ai_meta['main_concepts'][:5]  # Show first 5
                        print(f"   Main Concepts: {', '.join(concepts)}")
                    
                    # Learning objectives
                    if 'learning_objectives' in ai_meta and ai_meta['learning_objectives']:
                        objectives = ai_meta['learning_objectives'][:3]  # Show first 3
                        print(f"   Learning Objectives:")
                        for obj in objectives:
                            print(f"     - {obj[:60]}...")
                    
                    # Real-world applications
                    if 'real_world_applications' in ai_meta and ai_meta['real_world_applications']:
                        apps = ai_meta['real_world_applications'][:3]  # Show first 3
                        print(f"   Applications:")
                        for app in apps:
                            print(f"     - {app[:60]}...")
                    
                    # Skills developed
                    if 'skills_developed' in ai_meta and ai_meta['skills_developed']:
                        skills = ai_meta['skills_developed'][:3]  # Show first 3
                        print(f"   Skills: {', '.join(skills)}")
                
                # Content composition
                if 'content_composition' in metadata:
                    comp = metadata['content_composition']
                    print(f"\\n📈 CONTENT COMPOSITION:")
                    for key, value in comp.items():
                        if isinstance(value, (int, float)) and value > 0:
                            print(f"   {key.replace('_', ' ').title()}: {value}")
            
            print()
        
        # Overall statistics
        print("\\n" + "="*80)
        print("📊 OVERALL STATISTICS")
        print("="*80)
        
        total_chars = sum(len(chunk.content) for chunk in all_chunks)
        avg_quality = sum(chunk.quality_score for chunk in all_chunks) / len(all_chunks) if all_chunks else 0
        
        print(f"📚 Total Chunks: {len(all_chunks)}")
        print(f"📄 Total Content: {total_chars:,} characters")
        print(f"📏 Average Chunk Size: {total_chars // len(all_chunks):,} characters")
        print(f"⭐ Average Quality Score: {avg_quality:.2f}/1.00")
        
        # Quality distribution
        quality_ranges = {
            'Excellent (0.8+)': sum(1 for c in all_chunks if c.quality_score >= 0.8),
            'Good (0.6-0.79)': sum(1 for c in all_chunks if 0.6 <= c.quality_score < 0.8),
            'Fair (0.4-0.59)': sum(1 for c in all_chunks if 0.4 <= c.quality_score < 0.6),
            'Needs Work (<0.4)': sum(1 for c in all_chunks if c.quality_score < 0.4)
        }
        
        print(f"\\n📈 QUALITY DISTRIBUTION:")
        for quality_range, count in quality_ranges.items():
            if count > 0:
                print(f"   {quality_range}: {count} chunks")
        
        # Content type analysis
        chunk_types = {}
        for chunk in all_chunks:
            if hasattr(chunk, 'metadata') and chunk.metadata:
                chunk_type = chunk.metadata.get('type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        if chunk_types:
            print(f"\\n🏷️ CHUNK TYPES:")
            for chunk_type, count in chunk_types.items():
                print(f"   {chunk_type.title()}: {count} chunks")
        
        print("\\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
        print(f"✅ Status: {'EXCELLENT' if avg_quality >= 0.8 else 'GOOD' if avg_quality >= 0.6 else 'NEEDS IMPROVEMENT'}")
        
        return all_chunks
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    chunks = process_iesc111_and_show_chunks()