#!/usr/bin/env python3
"""
Debug Content Flow - Check exactly what content is being processed
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
import fitz  # PyMuPDF

def debug_content_extraction():
    """Debug the content extraction pipeline step by step"""
    print("🔍 DEBUGGING CONTENT EXTRACTION PIPELINE")
    print("=" * 80)
    
    # Step 1: Extract raw PDF content
    pdf_path = "/Users/umangagarwal/Downloads/iesc1dd/iesc107.pdf"
    doc = fitz.open(pdf_path)
    
    print(f"📖 PDF opened: {len(doc)} pages")
    
    # Extract first few pages
    full_text = ""
    for page_num in range(min(3, len(doc))):  # Just first 3 pages
        page = doc[page_num]
        page_text = page.get_text()
        print(f"   Page {page_num + 1}: {len(page_text)} characters")
        full_text += page_text + "\n"
    
    doc.close()
    
    print(f"\n📄 Total extracted: {len(full_text)} characters")
    print(f"📄 First 500 chars: {full_text[:500]}")
    print(f"📄 Last 500 chars: {full_text[-500:]}")
    
    # Step 2: Look for section 7.1 specifically
    import re
    section_pattern = r'7\.1\s+[A-Z][^.]*'
    matches = list(re.finditer(section_pattern, full_text, re.MULTILINE))
    
    print(f"\n🔍 Section 7.1 matches found: {len(matches)}")
    for i, match in enumerate(matches):
        print(f"   Match {i+1}: '{match.group(0)}' at position {match.start()}")
    
    if matches:
        # Extract content for first match
        first_match = matches[0]
        start_pos = first_match.start()
        
        # Find next section or reasonable endpoint
        next_section = re.search(r'\n7\.[2-9]\s+', full_text[start_pos + 100:])
        if next_section:
            end_pos = start_pos + 100 + next_section.start()
        else:
            end_pos = min(start_pos + 3000, len(full_text))  # 3000 char limit
        
        section_content = full_text[start_pos:end_pos]
        
        print(f"\n📋 EXTRACTED SECTION 7.1:")
        print(f"   Start position: {start_pos}")
        print(f"   End position: {end_pos}")
        print(f"   Content length: {len(section_content)}")
        print(f"   Content preview: {section_content[:300]}...")
        print(f"   Content ending: ...{section_content[-300:]}")
        
        # Step 3: Test with holistic chunker
        test_with_chunker(section_content)

def test_with_chunker(section_content):
    """Test the section content with our chunker"""
    print(f"\n🔄 TESTING WITH HOLISTIC CHUNKER")
    print("=" * 60)
    
    chunker = HolisticRAGChunker()
    
    # Create mother section
    mother_section = {
        'section_number': '7.1',
        'title': 'Describing Motion',
        'start_pos': 0,
        'end_pos': len(section_content),
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 7
    }
    
    # Create char mapping
    char_to_page_map = {i: 1 for i in range(len(section_content))}
    
    try:
        # Process with chunker
        chunks = chunker.process_mother_section(
            mother_section=mother_section,
            full_text=section_content,
            char_to_page_map=char_to_page_map
        )
        
        print(f"✅ Created {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n📋 CHUNK {i}:")
            print(f"   ID: {chunk.chunk_id}")
            print(f"   Length: {len(chunk.content)} characters")
            print(f"   Quality: {chunk.quality_score}")
            
            # Check for key sections
            content = chunk.content
            has_activity = "Activity" in content
            has_example = "Example" in content
            has_summary = "What you have learnt" in content
            has_questions = "Questions" in content
            
            print(f"   Contains Activity: {has_activity}")
            print(f"   Contains Example: {has_example}")
            print(f"   Contains Summary: {has_summary}")
            print(f"   Contains Questions: {has_questions}")
            
            # Show beginning and end
            print(f"\n   📖 Content Start (200 chars):")
            print(f"   {content[:200]}...")
            print(f"\n   📖 Content End (200 chars):")
            print(f"   ...{content[-200:]}")
            
            # Check sentence ending
            if content.strip() and content.strip()[-1] in '.!?':
                print(f"   ✅ Complete sentence ending")
            else:
                print(f"   ❌ Incomplete sentence ending: '{content.strip()[-50:]}'")
        
    except Exception as e:
        print(f"❌ Error processing: {e}")
        import traceback
        traceback.print_exc()

def test_boundary_detection_directly():
    """Test boundary detection methods directly"""
    print(f"\n🎯 TESTING BOUNDARY DETECTION DIRECTLY")
    print("=" * 60)
    
    # Test content with known endings
    test_content = """
7.1 Describing Motion

Motion is everywhere around us. An object is said to be in motion if it changes its position with time.

Activity 7.1
Take a ball and place it on the ground. Now walk around the ball.
From this activity, we understand that motion is relative.

Example 7.1
A car travels from Delhi to Mumbai. Calculate the average speed.
Solution: Average speed = 70 km/h

Questions
1. What is motion?
2. Give two examples.

What you have learnt
• Motion is relative
• We need reference points
• Speed can be calculated
"""
    
    chunker = HolisticRAGChunker()
    
    # Test boundary detection
    boundary = chunker._find_element_end(test_content, 0, 'default')
    captured = test_content[:boundary]
    
    print(f"🧪 Test content length: {len(test_content)}")
    print(f"🧪 Boundary detected at: {boundary}")
    print(f"🧪 Captured length: {len(captured)}")
    print(f"🧪 Percentage captured: {boundary/len(test_content)*100:.1f}%")
    
    # Check what sections are captured
    sections = ['Activity', 'Example', 'Questions', 'What you have learnt']
    for section in sections:
        if section in captured:
            print(f"   ✅ {section}: Captured")
        else:
            print(f"   ❌ {section}: Missing")
    
    print(f"\n📖 Captured content:")
    print(captured)

def main():
    """Main debug function"""
    print("🐛 DEBUGGING CONTENT TRUNCATION ISSUES")
    print("=" * 80)
    
    # Test 1: Debug content extraction
    debug_content_extraction()
    
    # Test 2: Test boundary detection directly  
    test_boundary_detection_directly()
    
    print(f"\n🎯 DEBUG SUMMARY")
    print("=" * 50)
    print("Use this information to identify where the truncation is happening:")
    print("1. PDF extraction issues")
    print("2. Section boundary detection issues") 
    print("3. Content processing issues")
    print("4. Boundary method issues")

if __name__ == "__main__":
    main()