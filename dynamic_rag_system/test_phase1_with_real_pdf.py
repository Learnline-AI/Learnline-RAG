#!/usr/bin/env python3
"""
Test Phase 1 Content Truncation Fix with Real NCERT PDF Content
Validates the fix works with actual Chapter 7 Motion content
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
import fitz  # PyMuPDF
import re

def extract_pdf_content():
    """Extract content from the real NCERT PDF"""
    pdf_path = "/Users/umangagarwal/Downloads/iesc1dd/iesc107.pdf"
    
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        char_to_page_map = {}
        
        # Extract text from first few pages (Chapter 7 content)
        for page_num in range(min(8, len(doc))):  # First 8 pages should cover Chapter 7
            page = doc[page_num]
            page_text = page.get_text()
            
            # Map characters to page numbers
            start_char = len(full_text)
            for i, char in enumerate(page_text):
                char_to_page_map[start_char + i] = page_num + 1
            
            full_text += page_text + "\n"
        
        doc.close()
        return full_text, char_to_page_map
        
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None, None

def find_chapter7_sections(content):
    """Find Chapter 7 sections in the PDF content"""
    sections = []
    
    # Look for section patterns in Chapter 7
    section_patterns = [
        r'7\.1\s+[A-Z][^.]*',  # 7.1 Describing Motion
        r'7\.2\s+[A-Z][^.]*',  # 7.2 Measuring the Rate of Motion
        r'7\.3\s+[A-Z][^.]*',  # 7.3 Rate of Change of Velocity
        r'7\.4\s+[A-Z][^.]*',  # 7.4 Graphical Representation
    ]
    
    for pattern in section_patterns:
        matches = list(re.finditer(pattern, content, re.MULTILINE))
        for match in matches:
            section_text = match.group(0).strip()
            sections.append({
                'text': section_text,
                'start_pos': match.start(),
                'number': section_text.split()[0]  # e.g., "7.1"
            })
    
    return sorted(sections, key=lambda x: x['start_pos'])

def extract_section_content(content, section_start, next_section_start=None):
    """Extract content for a specific section"""
    if next_section_start:
        section_content = content[section_start:next_section_start]
    else:
        # For the last section, extract reasonable amount
        section_content = content[section_start:section_start + 5000]
    
    return section_content.strip()

def test_with_real_pdf_content():
    """Test truncation fix with real NCERT PDF content"""
    print("🔬 TESTING PHASE 1 FIX WITH REAL NCERT PDF CONTENT")
    print("=" * 80)
    
    # Extract PDF content
    print("📖 Extracting content from NCERT PDF...")
    full_content, char_to_page_map = extract_pdf_content()
    
    if not full_content:
        print("❌ Could not extract PDF content")
        return False
    
    print(f"✅ Extracted {len(full_content)} characters from PDF")
    
    # Find Chapter 7 sections
    sections = find_chapter7_sections(full_content)
    print(f"🔍 Found {len(sections)} Chapter 7 sections:")
    for section in sections:
        print(f"   📚 {section['number']}: {section['text']}")
    
    if not sections:
        print("❌ No Chapter 7 sections found in PDF")
        return False
    
    # Test with first section (7.1)
    first_section = sections[0]
    next_section_start = sections[1]['start_pos'] if len(sections) > 1 else None
    
    section_content = extract_section_content(
        full_content, 
        first_section['start_pos'], 
        next_section_start
    )
    
    print(f"\n📄 Testing with Section {first_section['number']}")
    print(f"   Content length: {len(section_content)} characters")
    print(f"   Preview: {section_content[:200]}...")
    
    return test_section_processing(section_content, first_section, char_to_page_map)

def test_section_processing(section_content, section_info, char_to_page_map):
    """Test processing of a specific section"""
    print(f"\n🔄 PROCESSING SECTION {section_info['number']} WITH ENHANCED CHUNKER")
    print("=" * 60)
    
    # Initialize chunker
    chunker = HolisticRAGChunker()
    
    # Create mother section
    mother_section = {
        'section_number': section_info['number'],
        'title': section_info['text'].split(None, 1)[1] if len(section_info['text'].split()) > 1 else 'Motion',
        'start_pos': 0,
        'end_pos': len(section_content),
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 7
    }
    
    # Create character mapping for this section
    section_char_map = {i: 1 for i in range(len(section_content))}
    
    # Process with enhanced system
    try:
        chunks = chunker.process_mother_section(
            mother_section=mother_section,
            full_text=section_content,
            char_to_page_map=section_char_map
        )
        
        print(f"✅ Successfully created {len(chunks)} chunks")
        return validate_real_content_quality(chunks, section_content)
        
    except Exception as e:
        print(f"❌ Error processing section: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_real_content_quality(chunks, original_content):
    """Validate the quality of chunks created from real PDF content"""
    print(f"\n🔍 VALIDATING REAL CONTENT QUALITY")
    print("=" * 50)
    
    all_issues = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n📋 CHUNK {i}: {chunk.chunk_id}")
        print("─" * 40)
        
        content = chunk.content
        issues = []
        
        # Quality Check 1: Content length and completeness
        if len(content) < 50:
            issues.append(f"❌ Too short: {len(content)} characters")
        else:
            print(f"✅ Adequate length: {len(content)} characters")
        
        # Quality Check 2: Sentence completeness
        if content.strip() and not content.strip()[-1] in '.!?':
            # Check if it ends with a natural boundary
            natural_endings = ['What you have learnt', 'Summary', 'Questions', 'Exercises']
            if not any(ending in content[-100:] for ending in natural_endings):
                issues.append(f"❌ Incomplete sentence ending")
        else:
            print("✅ Complete sentence ending")
        
        # Quality Check 3: Educational element completeness
        if 'Activity' in content:
            # Check if activity is complete
            if 'Activity' in content and not any(word in content for word in ['observe', 'learn', 'demonstrates']):
                issues.append("❌ Incomplete activity (missing conclusion)")
            else:
                print("✅ Complete activity detected")
        
        # Quality Check 4: Example completeness
        if 'Example' in content:
            if 'Example' in content and 'Solution' in content:
                solution_part = content.split('Solution')[1] if 'Solution' in content else ""
                if len(solution_part.strip()) < 20:
                    issues.append("❌ Incomplete example solution")
                else:
                    print("✅ Complete example with solution")
        
        # Quality Check 5: No repeated content patterns
        lines = content.split('\n')
        repeated_lines = []
        for line in lines:
            if line.strip() and lines.count(line) > 2:
                repeated_lines.append(line.strip()[:50])
        
        if repeated_lines:
            issues.append(f"❌ Repeated content: {len(repeated_lines)} instances")
        else:
            print("✅ No excessive repetition")
        
        # Quality Check 6: Metadata quality
        metadata = chunk.metadata
        concepts = metadata.get('concepts_and_skills', {})
        main_concepts = concepts.get('main_concepts', [])
        
        if len(main_concepts) == 0:
            issues.append("❌ No main concepts extracted")
        elif any(len(concept) < 3 or concept.lower() in ['the', 'and', 'new', 'example'] for concept in main_concepts):
            issues.append("❌ Poor quality concepts extracted")
        else:
            print(f"✅ Quality concepts: {len(main_concepts)} main concepts")
        
        # Report issues
        if issues:
            print(f"\n❌ ISSUES IN CHUNK {i}:")
            for issue in issues:
                print(f"   {issue}")
            all_issues.extend(issues)
        else:
            print(f"\n✅ CHUNK {i}: HIGH QUALITY")
        
        # Show sample content
        print(f"\n📝 Content Preview:")
        print(f"   Start: {content[:150]}...")
        print(f"   End: ...{content[-150:]}")
    
    return len(all_issues) == 0

def test_specific_ncert_patterns():
    """Test specific NCERT content patterns that were problematic"""
    print(f"\n🎯 TESTING SPECIFIC NCERT PATTERNS")
    print("=" * 50)
    
    # Test problematic content from Chapter 7
    test_content = """
7.1 Describing Motion

Motion is everywhere around us. An object is said to be in motion if it changes its position with time. But how do we describe motion? We need some reference point to define motion.

Activity 7.1
Take a ball and place it on the ground. Now walk around the ball. Are you moving? Yes, you are moving with respect to the ball. But is the ball moving? With respect to you, the ball appears to be moving in a circle. But with respect to the ground, the ball is at rest.

From this activity, we understand that motion is relative. The state of motion of an object depends on the observer.

Materials needed: A ball, open space
Time required: 5 minutes

Example 7.1
A car travels from Delhi to Mumbai, a distance of 1400 km, in 20 hours. Calculate the average speed of the car.

Given:
Distance = 1400 km
Time = 20 hours

Solution:
Average speed = Total distance / Total time
Average speed = 1400 km / 20 hours = 70 km/h

Therefore, the average speed of the car is 70 km/h.

Questions
1. What is motion? Give two examples.
2. Why do we say motion is relative?
3. A train travels 300 km in 4 hours. What is its average speed?

What you have learnt
• Motion is the change in position of an object with time
• Motion is relative and depends on the observer
• We need a reference point to describe motion
• The same object can appear to be at rest or in motion depending on the observer
• Average speed is calculated as total distance divided by total time
"""
    
    chunker = HolisticRAGChunker()
    
    # Test boundary detection on this content
    boundary = chunker._find_element_end(test_content, 0, 'activity')
    captured = test_content[:boundary]
    
    print(f"🧪 Testing NCERT Chapter 7 content:")
    print(f"   Original length: {len(test_content)} characters")
    print(f"   Boundary detected at: {boundary}")
    print(f"   Captured length: {len(captured)} characters")
    
    # Check if important sections are captured
    important_sections = ['What you have learnt', 'Questions', 'Example', 'Activity']
    captured_sections = []
    missing_sections = []
    
    for section in important_sections:
        if section in captured:
            captured_sections.append(section)
        else:
            missing_sections.append(section)
    
    print(f"\n✅ Captured sections: {captured_sections}")
    if missing_sections:
        print(f"❌ Missing sections: {missing_sections}")
        return False
    
    # Check sentence completeness
    if captured.strip() and captured.strip()[-1] in '.!?':
        print("✅ Complete sentence ending")
        return True
    else:
        print(f"❌ Incomplete ending: '...{captured.strip()[-50:]}'")
        return False

def main():
    """Main test function"""
    print("🚀 PHASE 1 VALIDATION WITH REAL NCERT PDF CONTENT")
    print("=" * 80)
    
    # Test 1: Real PDF content processing
    pdf_success = test_with_real_pdf_content()
    
    # Test 2: Specific NCERT patterns
    pattern_success = test_specific_ncert_patterns()
    
    # Final assessment
    print(f"\n🎯 PHASE 1 COMPREHENSIVE ASSESSMENT")
    print("=" * 50)
    
    if pdf_success and pattern_success:
        print("🎉 SUCCESS: Phase 1 Content Truncation Fix VERIFIED!")
        print("✅ Real PDF content processing: WORKING")
        print("✅ NCERT pattern recognition: WORKING") 
        print("✅ Boundary detection: ENHANCED")
        print("✅ Content completeness: VALIDATED")
        
        print(f"\n🚀 PHASE 1 ACHIEVEMENTS:")
        print("✅ Fixed content truncation in real NCERT content")
        print("✅ Enhanced boundary detection with NCERT patterns")
        print("✅ Implemented sentence boundary validation")
        print("✅ Added educational element completeness checks")
        print("✅ Validated with Chapter 7 Motion content")
        
        print(f"\n🎯 READY FOR PHASE 2: Boundary Detection Enhancement")
        return True
    else:
        print("❌ PHASE 1 NEEDS MORE WORK")
        if not pdf_success:
            print("❌ PDF content processing issues")
        if not pattern_success:
            print("❌ NCERT pattern recognition issues")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)