#!/usr/bin/env python3
"""
Test comprehensive NCERT elements detection including figures, formulas, special boxes, etc.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
import json

def test_comprehensive_ncert_content():
    """Test with comprehensive NCERT content containing all element types"""
    print("🔍 TESTING COMPREHENSIVE NCERT ELEMENT DETECTION")
    print("=" * 80)
    
    # Comprehensive NCERT content with all elements
    comprehensive_content = """
8.1 Force and Motion

Force is a push or a pull. When we push or pull an object, we are applying a force on it. 
Force can change the state of motion of an object. It can also change the shape of an object.

In our daily life, we apply force in many activities. When we open a door, we apply a push 
or pull force. When we ride a bicycle, we apply force on the pedals.

ACTIVITY 8.1
Take a ball and place it on a table. Push the ball gently with your finger. What do you observe?
The ball starts moving in the direction of the push. This shows that force can set a stationary 
object in motion.

Now, while the ball is moving, give it another push in the same direction. What happens? 
The ball moves faster. This demonstrates that force can increase the speed of a moving object.

Materials needed: A ball, a flat table
Time required: 10 minutes

From this activity, we learn important concepts about force and motion. These observations 
form the foundation for understanding Newton's laws of motion.

DO YOU KNOW?
The concept of force was first formalized by Sir Isaac Newton in the 17th century. 
Newton's laws of motion form the foundation of classical mechanics and are still 
used today to understand motion in our everyday world.

Fig. 8.1: Effect of force on motion
The diagram shows a ball being pushed by a finger. The ball moves in the direction 
of the applied force, demonstrating that force can cause motion.

Example 8.1
A force of 10 N is applied to a box of mass 2 kg resting on a smooth surface. 
Calculate the acceleration of the box.

Solution:
We know from Newton's second law that:
F = ma

Where:
F = force applied = 10 N
m = mass of object = 2 kg
a = acceleration = ?

Therefore:
a = F/m = 10/2 = 5 m/s²

The acceleration of the box is 5 m/s².

This example shows how we can quantify the effect of force on motion using mathematical 
relationships. The same principle applies whether we're analyzing the motion of a cricket 
ball, a car, or a spacecraft.

THINK AND ACT
1. List five examples of forces you observe in your daily life.
2. Explain how force affects the motion of objects around you.
3. Design an experiment to demonstrate that force can change the direction of motion.

Questions
1. What is force? Give two examples of forces.
2. How does force affect the motion of an object?
3. A car of mass 1000 kg accelerates at 2 m/s². What force is applied?
4. State Newton's second law of motion.

Figure 8.2: Types of forces
This diagram illustrates different types of forces: contact forces (friction, normal force) 
and non-contact forces (gravitational, magnetic, electrical).

The mathematical relationship between force, mass, and acceleration can be expressed as:

F = ma

This is Newton's second law of motion, one of the most fundamental equations in physics.

8.2 Types of Forces

Forces can be broadly classified into two categories based on whether the objects 
need to be in contact or not.

What you have learnt
• Force is a push or a pull that can change the state of motion of an object
• Force can also change the shape of an object
• Newton's second law states that F = ma
• The SI unit of force is Newton (N)
• Forces can be classified as contact and non-contact forces
• Motion is always relative to a reference frame

Remember: Force is a vector quantity, which means it has both magnitude and direction. 
The direction of force is as important as its magnitude in determining the effect on motion.
"""
    
    # Initialize chunker
    chunker = HolisticRAGChunker()
    
    # Define mother section
    mother_section = {
        'section_number': '8.1',
        'title': 'Force and Motion',
        'start_pos': 0,
        'end_pos': len(comprehensive_content),
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 8
    }
    
    # Create character to page mapping
    char_to_page_map = {i: (i // 1000) + 1 for i in range(len(comprehensive_content))}
    
    print("📄 PROCESSING COMPREHENSIVE CONTENT...")
    print(f"Content length: {len(comprehensive_content)} characters")
    print("Elements expected:")
    print("• Activities: 1 (Activity 8.1)")
    print("• Examples: 1 (Example 8.1)")
    print("• Figures: 2 (Fig. 8.1, Figure 8.2)")
    print("• Special boxes: 1 (DO YOU KNOW?)")
    print("• Think and Act: 1 section")
    print("• Questions: 4 questions")
    print("• What you have learnt: 1 section")
    print("• Formulas: F = ma")
    print()
    
    # Process the content
    chunks = chunker.process_mother_section(
        mother_section=mother_section,
        full_text=comprehensive_content,
        char_to_page_map=char_to_page_map
    )
    
    return chunks, comprehensive_content

def analyze_detection_results(chunks):
    """Analyze what elements were actually detected"""
    print("\n📊 ELEMENT DETECTION ANALYSIS")
    print("=" * 80)
    
    total_elements = {
        'activities': 0,
        'examples': 0, 
        'figures': 0,
        'special_boxes': 0,
        'formulas': 0,
        'questions': 0
    }
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n📋 CHUNK {i}: {chunk.chunk_id}")
        print("─" * 60)
        
        comp = chunk.metadata['content_composition']
        
        print(f"Activities detected: {comp['activity_count']} {comp['activity_numbers']}")
        print(f"Examples detected: {comp['example_count']} {comp['example_numbers']}")
        print(f"Figures detected: {comp['figure_count']} {comp['figure_numbers']}")
        
        # Check for missing elements
        content = chunk.content.lower()
        
        has_special_box = 'do you know' in content or 'what you have learnt' in content
        has_think_act = 'think and act' in content
        has_questions = 'questions' in content and any(char.isdigit() for char in content)
        has_formula = 'f = ma' in content or 'f=ma' in content
        
        print(f"Special boxes found: {'✅' if has_special_box else '❌'}")
        print(f"Think and Act found: {'✅' if has_think_act else '❌'}")
        print(f"Questions found: {'✅' if has_questions else '❌'}")
        print(f"Formulas found: {'✅' if has_formula else '❌'}")
        
        # Accumulate totals
        total_elements['activities'] += comp['activity_count']
        total_elements['examples'] += comp['example_count']
        total_elements['figures'] += comp['figure_count']
        if has_special_box:
            total_elements['special_boxes'] += 1
        if has_formula:
            total_elements['formulas'] += 1
        if has_questions:
            total_elements['questions'] += 1
    
    print(f"\n📈 TOTAL DETECTION SUMMARY:")
    print("─" * 40)
    expected = {
        'activities': 1,
        'examples': 1,
        'figures': 2,
        'special_boxes': 2,  # DO YOU KNOW + What you have learnt
        'formulas': 1,
        'questions': 1  # Questions section
    }
    
    for element, detected in total_elements.items():
        expected_count = expected.get(element, 0)
        status = "✅" if detected >= expected_count else "❌"
        print(f"{element.replace('_', ' ').title()}: {detected}/{expected_count} {status}")

def show_missing_patterns():
    """Show what patterns might be missing"""
    print(f"\n🔍 MISSING PATTERN ANALYSIS")
    print("=" * 80)
    
    print("If elements are not being detected, possible issues:")
    print()
    print("❌ POTENTIAL MISSING PATTERNS:")
    print("• Think and Act sections: r'THINK AND ACT'")
    print("• Questions sections: r'Questions\\s*\\n'")
    print("• What you have learnt: r'What you have learnt'")
    print("• Formula patterns: r'[A-Z]\\s*=\\s*[A-Za-z0-9]+' for F = ma")
    print("• Numbered questions: r'\\d+\\.\\s+[A-Z].*\\?'")
    print()
    print("✅ ENHANCEMENT NEEDED:")
    print("• Add comprehensive NCERT-specific patterns")
    print("• Improve special content detection")
    print("• Add formula/equation recognition")
    print("• Detect educational section types")

def main():
    """Main test function"""
    print("🧪 COMPREHENSIVE NCERT ELEMENT DETECTION TEST")
    print("=" * 80)
    
    # Test with comprehensive content
    chunks, content = test_comprehensive_ncert_content()
    
    print(f"\n✅ Created {len(chunks)} chunks from comprehensive content")
    
    # Analyze detection results
    analyze_detection_results(chunks)
    
    # Show missing patterns
    show_missing_patterns()
    
    print(f"\n🎯 CONCLUSION:")
    print("The holistic system needs enhanced pattern detection for:")
    print("• Special NCERT boxes (Think and Act, What you have learnt)")
    print("• Question sections and numbered questions")
    print("• Mathematical formulas and equations")
    print("• Educational content types specific to NCERT")

if __name__ == "__main__":
    main()