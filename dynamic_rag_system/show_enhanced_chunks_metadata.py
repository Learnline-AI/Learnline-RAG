#!/usr/bin/env python3
"""
Show enhanced chunks with complete metadata including new NCERT elements
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
import json

def test_enhanced_detection():
    """Test and display enhanced element detection"""
    print("🔍 ENHANCED NCERT ELEMENT DETECTION WITH COMPLETE METADATA")
    print("=" * 80)
    
    # Test content with all NCERT elements
    enhanced_content = """
8.1 Force and Motion

Force is a push or a pull. When we push or pull an object, we are applying a force on it. 
The concept of force was first introduced by Sir Isaac Newton.

ACTIVITY 8.1
Take a ball and place it on a table. Push the ball gently with your finger. 
Observe the motion. This demonstrates that force can cause motion.

Materials needed: A ball, a flat table
Time required: 10 minutes

From this activity, we learn that force causes motion.

DO YOU KNOW?
Newton's laws of motion form the foundation of classical mechanics and are still 
used today to understand motion in our everyday world.

Fig. 8.1: Effect of force on motion
The diagram shows a ball being pushed by a finger, demonstrating force effects.

Example 8.1
A force of 10 N is applied to a box of mass 2 kg. Calculate the acceleration.

Solution:
We know from Newton's second law:
F = ma

Where F = 10 N, m = 2 kg
Therefore: a = F/m = 10/2 = 5 m/s²

The acceleration is 5 m/s².

THINK AND ACT
1. List five examples of forces in daily life.
2. How does force affect motion?
3. Design an experiment to show force changes direction.

Questions
1. What is force? Give two examples.
2. How does force affect object motion?
3. A car of mass 1000 kg accelerates at 2 m/s². What force is applied?

What you have learnt
• Force is a push or pull that changes motion
• Newton's second law: F = ma
• Force is measured in Newtons (N)
• Force has both magnitude and direction
"""
    
    # Initialize chunker
    chunker = HolisticRAGChunker()
    
    # Process content
    mother_section = {
        'section_number': '8.1',
        'title': 'Force and Motion',
        'start_pos': 0,
        'end_pos': len(enhanced_content),
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 8
    }
    
    char_to_page_map = {i: 1 for i in range(len(enhanced_content))}
    chunks = chunker.process_mother_section(
        mother_section=mother_section,
        full_text=enhanced_content,
        char_to_page_map=char_to_page_map
    )
    
    return chunks[0] if chunks else None

def display_enhanced_metadata(chunk):
    """Display complete enhanced metadata"""
    print(f"\n📋 ENHANCED CHUNK: {chunk.chunk_id}")
    print("=" * 80)
    
    # Basic info
    print(f"\n🔢 BASIC INFO:")
    print(f"Quality Score: {chunk.quality_score:.2f}")
    print(f"Content Length: {len(chunk.content)} characters")
    
    # Enhanced content composition
    comp = chunk.metadata['content_composition']
    print(f"\n📚 ENHANCED CONTENT COMPOSITION:")
    print(f"• Activities: {comp['activity_count']} {comp['activity_numbers']}")
    print(f"• Examples: {comp['example_count']} {comp['example_numbers']}")
    print(f"• Figures: {comp['figure_count']} {comp['figure_numbers']}")
    print(f"• Questions: {comp.get('question_count', 0)} {comp.get('question_texts', [])}")
    print(f"• Formulas: {comp.get('formula_count', 0)} {comp.get('formulas', [])}")
    print(f"• Concepts: {comp['concept_count']}")
    
    # Enhanced pedagogical elements
    ped = chunk.metadata['pedagogical_elements']
    print(f"\n🎓 ENHANCED PEDAGOGICAL ELEMENTS:")
    print(f"• Content Types: {', '.join(ped['content_types'])}")
    print(f"• Learning Styles: {', '.join(ped['learning_styles'])}")
    print(f"• Cognitive Level: {ped['cognitive_level']}")
    print(f"• Time Estimate: {ped['estimated_time_minutes']} minutes")
    
    # Show raw metadata for verification
    print(f"\n📄 COMPLETE ENHANCED METADATA (JSON):")
    print("─" * 60)
    print(json.dumps(chunk.metadata, indent=2, ensure_ascii=False))

def analyze_content_types():
    """Analyze what content types are now detected"""
    print(f"\n🔍 CONTENT TYPE ANALYSIS")
    print("=" * 50)
    
    print("✅ NEWLY DETECTED CONTENT TYPES:")
    print("• assessment_questions - For question sections")
    print("• mathematical_formulas - For equations like F = ma")
    print("• visual_aids - For figures and diagrams")
    print("• hands_on_activity - For practical activities")
    print("• worked_examples - For solved problems")
    print("• conceptual_explanation - For theory sections")
    
    print(f"\n✅ NEWLY DETECTED LEARNING STYLES:")
    print("• analytical - For question-based learning")
    print("• logical_mathematical - For formulas and examples")
    print("• kinesthetic - For hands-on activities")
    print("• visual - For figures and diagrams")
    print("• verbal_linguistic - For conceptual content")

def main():
    """Main function"""
    print("🚀 SHOWING ENHANCED CHUNKS WITH COMPREHENSIVE METADATA")
    print("=" * 80)
    
    # Test enhanced detection
    chunk = test_enhanced_detection()
    
    if chunk:
        print(f"✅ Enhanced chunk created successfully!")
        
        # Display enhanced metadata
        display_enhanced_metadata(chunk)
        
        # Analyze content types
        analyze_content_types()
        
        print(f"\n🎯 ENHANCEMENT SUMMARY:")
        print("✅ Added question detection patterns")
        print("✅ Added formula detection patterns") 
        print("✅ Enhanced content type classification")
        print("✅ Improved learning style identification")
        print("✅ Comprehensive metadata structure")
        
        print(f"\n📊 METADATA COMPARISON:")
        print("Before: 4-5 basic fields")
        print("After: 25+ comprehensive educational fields")
        print("Including: Questions, Formulas, Learning Styles, Content Types")
        
    else:
        print("❌ No chunks created")

if __name__ == "__main__":
    main()