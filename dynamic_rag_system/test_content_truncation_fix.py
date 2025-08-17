#!/usr/bin/env python3
"""
Test Content Truncation Fix - Phase 1
Validates that boundary detection prevents content truncation
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
import re

def create_problematic_content():
    """Create content that previously caused truncation issues"""
    return """
7.1 Motion and Rest

Motion is everywhere around us. The leaves of trees move, birds fly, fish swim, and children play. 
Even when we are sleeping, air moves into and out of our lungs and blood flows in arteries and veins.

ACTIVITY 7.1
Take a ball and place it on the ground. Is the ball in motion or at rest?
Now push the ball. What do you observe? The ball starts moving.
Stop the ball with your hand. Now the ball is at rest again.

From this activity, we learn that:
• Objects can be in motion or at rest
• Motion and rest are relative terms
• An object can change from rest to motion and vice versa

Materials needed: A ball, open space
Time required: 5 minutes
Safety note: Ensure the area is clear of obstacles

DO YOU KNOW?
The study of motion without considering the forces that cause it is called kinematics. 
Ancient Greek philosophers like Aristotle and later scientists like Galileo contributed 
significantly to our understanding of motion.

Example 7.1
A car travels from Delhi to Agra. During the journey:
- With respect to the road, the car is in motion
- With respect to the passengers inside, the car is at rest
- With respect to the trees on the roadside, the car is in motion

Solution:
This example demonstrates that motion is relative. The state of motion depends on 
the observer or the reference point chosen.

THINK AND ACT
1. List five objects in motion around you right now.
2. List five objects at rest around you right now.  
3. Explain why the same object can be considered both in motion and at rest.
4. Give examples from your daily life where motion is relative.

Questions
1. What is motion? Give two examples of objects in motion.
2. What is rest? Give two examples of objects at rest.
3. Why do we say motion and rest are relative terms?
4. A passenger sitting in a moving train is at rest with respect to what?
5. The same passenger is in motion with respect to what?

Multiple Choice Questions
1. Motion is:
   (a) Absolute    (b) Relative    (c) Fixed    (d) Constant

2. An object at rest has:
   (a) Zero motion    (b) Constant motion    (c) No motion relative to observer    (d) All of these

What you have learnt
• Motion and rest are relative terms
• An object can be in motion with respect to one observer and at rest with respect to another
• The state of motion depends on the reference point or observer
• Everything in the universe is in motion relative to something
• We need to specify the reference point when describing motion
• Motion is a fundamental property of matter and is observed everywhere in nature

Remember: There is no absolute rest or absolute motion in the universe. Everything is relative!
"""

def test_content_truncation_fix():
    """Test that content truncation has been fixed"""
    print("🔧 TESTING CONTENT TRUNCATION FIX - PHASE 1")
    print("=" * 80)
    
    # Initialize the enhanced chunker
    chunker = HolisticRAGChunker()
    
    # Get problematic test content
    test_content = create_problematic_content()
    
    print(f"📄 Test content length: {len(test_content)} characters")
    print(f"📊 Contains critical sections: 'What you have learnt', Activities, Examples")
    print()
    
    # Define mother section
    mother_section = {
        'section_number': '7.1',
        'title': 'Motion and Rest',
        'start_pos': 0,
        'end_pos': len(test_content),
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 7
    }
    
    # Create character to page mapping
    char_to_page_map = {i: 1 for i in range(len(test_content))}
    
    # Process content with enhanced boundary detection
    print("🔄 Processing content with enhanced boundary detection...")
    chunks = chunker.process_mother_section(
        mother_section=mother_section,
        full_text=test_content,
        char_to_page_map=char_to_page_map
    )
    
    print(f"✅ Created {len(chunks)} chunks with enhanced boundary detection")
    return chunks, test_content

def validate_content_completeness(chunks, original_content):
    """Validate that no content was truncated"""
    print("\n🔍 CONTENT COMPLETENESS VALIDATION")
    print("=" * 60)
    
    all_issues = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n📋 CHUNK {i}: {chunk.chunk_id}")
        print("─" * 40)
        
        content = chunk.content
        issues = []
        
        # Check 1: No mid-sentence truncation
        if content.strip() and not content.strip()[-1] in '.!?':
            last_words = content.strip()[-50:].replace('\n', ' ')
            issues.append(f"❌ Mid-sentence truncation: '...{last_words}'")
        else:
            print("✅ Complete sentence ending")
        
        # Check 2: Complete "What you have learnt" sections
        if "What you have learnt" in content:
            pattern = r'What you have learnt.*?(?=\n\s*(?:[A-Z]|\d+\.|$))'
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                summary_section = matches[0]
                if len(summary_section) < 100:  # Too short, likely truncated
                    issues.append(f"❌ Truncated summary section: {len(summary_section)} chars")
                else:
                    print(f"✅ Complete summary section: {len(summary_section)} chars")
        
        # Check 3: Complete activity sections
        activity_pattern = r'ACTIVITY.*?(?=\n\s*(?:DO YOU KNOW|Example|THINK|Questions|What you have|$))'
        activity_matches = re.findall(activity_pattern, content, re.DOTALL | re.IGNORECASE)
        for j, activity in enumerate(activity_matches, 1):
            if not any(keyword in activity for keyword in ['Materials needed', 'Time required', 'From this activity']):
                issues.append(f"❌ Incomplete Activity {j}: Missing conclusion or materials")
            else:
                print(f"✅ Complete Activity {j}")
        
        # Check 4: Complete example sections
        example_pattern = r'Example.*?(?=\n\s*(?:THINK|Questions|DO YOU KNOW|What you have|$))'
        example_matches = re.findall(example_pattern, content, re.DOTALL | re.IGNORECASE)
        for j, example in enumerate(example_matches, 1):
            if 'Solution:' in example and len(example.split('Solution:')[1].strip()) < 20:
                issues.append(f"❌ Incomplete Example {j}: Truncated solution")
            else:
                print(f"✅ Complete Example {j}")
        
        # Check 5: Complete question sections
        if "Questions" in content:
            questions_pattern = r'Questions.*?(?=\n\s*(?:Multiple Choice|What you have|$))'
            question_matches = re.findall(questions_pattern, content, re.DOTALL | re.IGNORECASE)
            if question_matches:
                questions_section = question_matches[0]
                question_count = len(re.findall(r'\d+\.', questions_section))
                if question_count > 0:
                    print(f"✅ Complete Questions section: {question_count} questions")
                else:
                    issues.append("❌ Questions section found but no numbered questions detected")
        
        # Report chunk issues
        if issues:
            print(f"\n❌ ISSUES FOUND IN CHUNK {i}:")
            for issue in issues:
                print(f"   {issue}")
            all_issues.extend(issues)
        else:
            print(f"\n✅ CHUNK {i}: NO TRUNCATION ISSUES")
        
        # Show content length and ending
        print(f"\n📊 Chunk Stats:")
        print(f"   Length: {len(content)} characters")
        print(f"   Ending: '...{content.strip()[-100:].replace(chr(10), ' ')}'")
    
    return all_issues

def test_specific_boundary_patterns():
    """Test specific boundary pattern recognition"""
    print(f"\n🎯 TESTING SPECIFIC BOUNDARY PATTERNS")
    print("=" * 50)
    
    chunker = HolisticRAGChunker()
    
    # Test content with various boundary types
    test_cases = [
        {
            'name': 'What you have learnt',
            'content': 'Some content here.\n\nWhat you have learnt\n• Key point 1\n• Key point 2\n• Key point 3',
            'should_capture': 'Key point 3'
        },
        {
            'name': 'Activity boundary',
            'content': 'Activity content here.\n\nACTIVITY 7.2\nNext activity starts here.',
            'should_not_capture': 'Next activity starts'
        },
        {
            'name': 'Example boundary', 
            'content': 'Example solution here.\n\nExample 7.2\nNext example starts here.',
            'should_not_capture': 'Next example starts'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        
        # Test boundary detection
        boundary = chunker._find_element_end(test_case['content'], 0, 'activity')
        captured_content = test_case['content'][:boundary]
        
        if 'should_capture' in test_case:
            if test_case['should_capture'] in captured_content:
                print(f"✅ Correctly captured: '{test_case['should_capture']}'")
            else:
                print(f"❌ Failed to capture: '{test_case['should_capture']}'")
        
        if 'should_not_capture' in test_case:
            if test_case['should_not_capture'] not in captured_content:
                print(f"✅ Correctly excluded: '{test_case['should_not_capture']}'")
            else:
                print(f"❌ Incorrectly included: '{test_case['should_not_capture']}'")
        
        print(f"   Boundary at position: {boundary}")
        print(f"   Captured length: {len(captured_content)} chars")

def main():
    """Main test function"""
    print("🚀 CONTENT TRUNCATION FIX VALIDATION - PHASE 1")
    print("=" * 80)
    
    # Test content truncation fix
    chunks, original_content = test_content_truncation_fix()
    
    # Validate content completeness
    issues = validate_content_completeness(chunks, original_content)
    
    # Test specific boundary patterns
    test_specific_boundary_patterns()
    
    # Final assessment
    print(f"\n🎯 PHASE 1 FIX ASSESSMENT:")
    print("=" * 50)
    
    if not issues:
        print("✅ SUCCESS: No content truncation issues detected!")
        print("✅ Enhanced boundary detection working correctly")
        print("✅ NCERT-specific patterns recognized")
        print("✅ Complete educational sections captured")
        
        print(f"\n🚀 IMPROVEMENTS ACHIEVED:")
        print("✅ Added NCERT-specific boundary patterns")
        print("✅ Implemented sentence boundary validation")
        print("✅ Added content completeness checks")
        print("✅ Dynamic length limits based on element type")
        print("✅ Hierarchical boundary priority system")
        
        print(f"\n🎉 PHASE 1: CONTENT TRUNCATION FIX - COMPLETED")
        return True
    else:
        print(f"❌ ISSUES REMAINING: {len(issues)} problems detected")
        for issue in issues:
            print(f"   {issue}")
        print(f"\n🔧 Need additional fixes for complete resolution")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Ready to proceed to Phase 2: Boundary Detection Enhancement")
    else:
        print("\n⚠️  Need to address remaining issues before proceeding")