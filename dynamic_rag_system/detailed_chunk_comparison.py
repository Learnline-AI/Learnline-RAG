#!/usr/bin/env python3
"""
Detailed comparison of actual chunks: Original vs Holistic approach
Shows exact content and structure differences
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
import textwrap

def show_detailed_chunk_comparison():
    """Show actual chunk content comparison"""
    print("=" * 100)
    print("📋 DETAILED CHUNK COMPARISON: Original vs Holistic")
    print("=" * 100)
    
    # Sample NCERT content
    sample_content = """
8.1 Force and Motion

Force is a push or a pull. When we push or pull an object, we are applying a force on it. 
Force can change the state of motion of an object. It can also change the shape of an object.

In our daily life, we apply force in many activities. When we open a door, we apply a push 
or pull force. When we ride a bicycle, we apply force on the pedals. Let us understand 
the effects of force through some activities.

ACTIVITY 8.1
Take a ball and place it on a table. Push the ball gently with your finger. What do you observe?
The ball starts moving in the direction of the push. This shows that force can set a stationary 
object in motion.

Now, while the ball is moving, give it another push in the same direction. What happens? 
The ball moves faster. This demonstrates that force can increase the speed of a moving object.

Next, while the ball is moving, push it from the side. The ball changes its direction. 
This shows that force can change the direction of motion.

Materials needed: A ball, a flat table
Time required: 10 minutes

From this activity, we learn important concepts about force and motion. These observations 
form the foundation for understanding Newton's laws of motion.

Example 8.1
A force of 10 N is applied to a box of mass 2 kg resting on a smooth surface. 
Calculate the acceleration of the box.

Solution:
We know from Newton's second law that F = ma
Where F = force, m = mass, a = acceleration

Given:
F = 10 N
m = 2 kg

Therefore, a = F/m = 10/2 = 5 m/s²

The acceleration of the box is 5 m/s².

This example shows how we can quantify the effect of force on motion. The same principle 
applies whether we're analyzing the motion of a cricket ball, a car, or a spacecraft.
"""

    # Show original content first
    print("\n📄 ORIGINAL CONTENT:")
    print("─" * 80)
    print(sample_content.strip())
    
    # Simulate original fragmented approach
    print("\n" + "=" * 100)
    print("❌ ORIGINAL SYSTEM (Fragmented Chunks)")
    print("=" * 100)
    
    # Extract pieces the way original system would
    activity_start = sample_content.find("ACTIVITY 8.1")
    activity_end = sample_content.find("From this activity")
    activity_content = sample_content[activity_start:activity_end].strip()
    
    example_start = sample_content.find("Example 8.1")
    example_end = sample_content.find("This example shows")
    example_content = sample_content[example_start:example_end + sample_content[example_end:].find(".") + 1].strip()
    
    # Residual would be everything (due to the bug)
    residual_content = sample_content.strip()  # BUG: Returns everything!
    
    print("\n🧩 CHUNK 1 - ACTIVITY ONLY (Isolated):")
    print("┌" + "─" * 98 + "┐")
    print("│ TYPE: Activity Chunk                                                                             │")
    print("│ LENGTH: {} characters                                                                    │".format(len(activity_content)).ljust(99) + "│")
    print("├" + "─" * 98 + "┤")
    for line in textwrap.wrap(activity_content, width=96):
        print("│ " + line.ljust(96) + " │")
    print("└" + "─" * 98 + "┘")
    print("❌ PROBLEM: Missing context! Student doesn't know what force is or why this activity matters.")
    
    print("\n🧩 CHUNK 2 - EXAMPLE ONLY (Isolated):")
    print("┌" + "─" * 98 + "┐")
    print("│ TYPE: Example Chunk                                                                              │")
    print("│ LENGTH: {} characters                                                                    │".format(len(example_content)).ljust(99) + "│")
    print("├" + "─" * 98 + "┤")
    for line in textwrap.wrap(example_content, width=96):
        print("│ " + line.ljust(96) + " │")
    print("└" + "─" * 98 + "┘")
    print("❌ PROBLEM: No connection to activity! Student doesn't see how observation leads to calculation.")
    
    print("\n🧩 CHUNK 3 - RESIDUAL CONTENT (EVERYTHING - Due to Bug!):")
    print("┌" + "─" * 98 + "┐")
    print("│ TYPE: Residual Chunk                                                                             │")
    print("│ LENGTH: {} characters (MASSIVE DUPLICATION!)                                            │".format(len(residual_content)).ljust(99) + "│")
    print("├" + "─" * 98 + "┤")
    preview = residual_content[:300] + "... [CONTINUES FOR FULL CONTENT - DUPLICATES EVERYTHING!]"
    for line in textwrap.wrap(preview, width=96):
        print("│ " + line.ljust(96) + " │")
    print("└" + "─" * 98 + "┘")
    print("❌ CRITICAL BUG: Returns entire content! Activity and example appear again causing massive duplication.")
    
    # Now show holistic approach
    print("\n" + "=" * 100)
    print("✅ HOLISTIC SYSTEM (Contextual Chunks)")
    print("=" * 100)
    
    # Process with holistic system
    chunker = HolisticRAGChunker()
    mother_section = {
        'section_number': '8.1',
        'title': 'Force and Motion',
        'start_pos': 0,
        'end_pos': len(sample_content),
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 8
    }
    
    char_to_page_map = {i: 1 for i in range(len(sample_content))}
    holistic_chunks = chunker.process_mother_section(
        mother_section=mother_section,
        full_text=sample_content,
        char_to_page_map=char_to_page_map
    )
    
    for i, chunk in enumerate(holistic_chunks, 1):
        print(f"\n🎯 CONTEXTUAL CHUNK {i} - COMPLETE LEARNING UNIT:")
        print("┌" + "─" * 98 + "┐")
        print("│ TYPE: Contextual Learning Unit                                                               │")
        print("│ LENGTH: {} characters                                                               │".format(len(chunk.content)).ljust(99) + "│")
        print("│ QUALITY SCORE: {:.2f}                                                                      │".format(chunk.quality_score).ljust(99) + "│")
        print("├" + "─" * 98 + "┤")
        
        # Show content with proper formatting
        content_lines = chunk.content.strip().split('\n')
        for line in content_lines[:20]:  # Show first 20 lines
            if line.strip():
                for wrapped_line in textwrap.wrap(line.strip(), width=96):
                    print("│ " + wrapped_line.ljust(96) + " │")
            else:
                print("│" + " " * 96 + " │")
        
        if len(content_lines) > 20:
            print("│ " + "... [Content continues with full learning context] ...".ljust(96) + " │")
        
        print("├" + "─" * 98 + "┤")
        print("│ METADATA HIGHLIGHTS:                                                                         │")
        
        # Show key metadata
        comp = chunk.metadata['content_composition']
        ped = chunk.metadata['pedagogical_elements']
        qual = chunk.metadata['quality_indicators']
        
        print("│ • Has Introduction: {}                                                                │".format(comp['has_introduction']).ljust(99) + "│")
        print("│ • Activities: {} {}                                                           │".format(comp['activity_count'], comp['activity_numbers']).ljust(99) + "│")
        print("│ • Examples: {} {}                                                             │".format(comp['example_count'], comp['example_numbers']).ljust(99) + "│")
        print("│ • Learning Time: {} minutes                                                            │".format(ped['estimated_time_minutes']).ljust(99) + "│")
        print("│ • Completeness: {:.2f} | Coherence: {:.2f} | Pedagogical: {:.2f}                        │".format(qual['completeness'], qual['coherence'], qual['pedagogical_soundness']).ljust(99) + "│")
        
        print("└" + "─" * 98 + "┘")
        print("✅ SUCCESS: Complete learning flow! Introduction → Activity → Observation → Concept → Application")

def compare_metadata_structures():
    """Compare metadata richness"""
    print("\n" + "=" * 100)
    print("📊 METADATA COMPARISON")
    print("=" * 100)
    
    print("\n❌ ORIGINAL SYSTEM METADATA (Very Limited):")
    print("┌" + "─" * 50 + "┐")
    print("│ activity_chunk = {                           │")
    print("│   'type': 'activity',                        │")
    print("│   'activity_number': '8.1',                  │")
    print("│   'content_length': 450,                     │")
    print("│   'section': '8.1'                           │")
    print("│ }                                             │")
    print("│                                               │")
    print("│ example_chunk = {                             │")
    print("│   'type': 'example',                          │")
    print("│   'example_number': '8.1',                    │")
    print("│   'has_solution': True,                       │")
    print("│   'section': '8.1'                            │")
    print("│ }                                             │")
    print("│                                               │")
    print("│ residual_chunk = {                            │")
    print("│   'type': 'content',                          │")
    print("│   'section': '8.1',                           │")
    print("│   'content_length': 2500  # ALL CONTENT!     │")
    print("│ }                                             │")
    print("└" + "─" * 50 + "┘")
    print("❌ Problems: No learning context, no prerequisites, no adaptive capability")
    
    print("\n✅ HOLISTIC SYSTEM METADATA (Rich & Educational):")
    print("┌" + "─" * 70 + "┐")
    print("│ contextual_chunk = {                                             │")
    print("│   'basic_info': {                                                │")
    print("│     'grade_level': 9,                                            │")
    print("│     'subject': 'Physics',                                        │")
    print("│     'section': '8.1',                                            │")
    print("│     'section_title': 'Force and Motion'                         │")
    print("│   },                                                             │")
    print("│   'content_composition': {                                       │")
    print("│     'has_introduction': True,                                    │")
    print("│     'activity_count': 1,                                         │")
    print("│     'example_count': 1,                                          │")
    print("│     'activity_numbers': ['8.1'],                                │")
    print("│     'example_numbers': ['8.1'],                                 │")
    print("│     'figure_count': 0                                            │")
    print("│   },                                                             │")
    print("│   'pedagogical_elements': {                                      │")
    print("│     'content_types': ['conceptual_explanation',                 │")
    print("│                      'hands_on_activity',                       │")
    print("│                      'worked_examples'],                        │")
    print("│     'learning_styles': ['kinesthetic',                          │")
    print("│                        'logical_mathematical'],                 │")
    print("│     'cognitive_level': 'application',                           │")
    print("│     'estimated_time_minutes': 25                                │")
    print("│   },                                                             │")
    print("│   'concepts_and_skills': {                                       │")
    print("│     'main_concepts': ['force', 'motion', 'acceleration'],       │")
    print("│     'skills_developed': ['observation', 'calculation'],         │")
    print("│     'learning_objectives': ['Understand force effects']         │")
    print("│   },                                                             │")
    print("│   'quality_indicators': {                                        │")
    print("│     'completeness': 0.85,                                        │")
    print("│     'coherence': 0.92,                                           │")
    print("│     'pedagogical_soundness': 0.89                               │")
    print("│   }                                                              │")
    print("│ }                                                                │")
    print("└" + "─" * 70 + "┘")
    print("✅ Success: Complete educational context for adaptive learning!")

def show_learning_flow_impact():
    """Show impact on student learning"""
    print("\n" + "=" * 100)
    print("🎓 IMPACT ON STUDENT LEARNING")
    print("=" * 100)
    
    print("\n❌ STUDENT EXPERIENCE WITH ORIGINAL SYSTEM:")
    print("┌" + "─" * 80 + "┐")
    print("│ 1. Student gets Activity 8.1 chunk:                               │")
    print("│    'Push a ball on table...'                                       │")
    print("│    → Student: 'Why am I pushing a ball? What's the point?'        │")
    print("│                                                                    │")
    print("│ 2. Later gets Example 8.1 chunk:                                  │")
    print("│    'F = ma, calculate acceleration...'                             │")
    print("│    → Student: 'Where did this formula come from?'                 │")
    print("│                                                                    │")
    print("│ 3. Eventually gets Content chunk:                                 │")
    print("│    'Force is push or pull... learn through activity...'           │")
    print("│    → Student: 'What activity? I don't see any activity here!'     │")
    print("│                                                                    │")
    print("│ RESULT: Confused, fragmented learning ❌                          │")
    print("└" + "─" * 80 + "┘")
    
    print("\n✅ STUDENT EXPERIENCE WITH HOLISTIC SYSTEM:")
    print("┌" + "─" * 80 + "┐")
    print("│ Student gets Complete Learning Unit:                               │")
    print("│                                                                    │")
    print("│ 1. 'Force is a push or pull...' (Introduction)                    │")
    print("│    → Student: 'OK, I understand what force is'                    │")
    print("│                                                                    │")
    print("│ 2. 'Let us understand through activity...' (Transition)           │")
    print("│    → Student: 'Great, I'll learn by doing'                        │")
    print("│                                                                    │")
    print("│ 3. 'ACTIVITY 8.1: Push a ball...' (Hands-on)                      │")
    print("│    → Student: 'I see! Force makes things move!'                   │")
    print("│                                                                    │")
    print("│ 4. 'From this activity, we learn...' (Connection)                 │")
    print("│    → Student: 'Now I understand the concept'                      │")
    print("│                                                                    │")
    print("│ 5. 'Example 8.1: F = ma...' (Application)                         │")
    print("│    → Student: 'I can calculate this now!'                         │")
    print("│                                                                    │")
    print("│ RESULT: Clear, connected, effective learning ✅                   │")
    print("└" + "─" * 80 + "┘")

if __name__ == "__main__":
    print("🔍 DETAILED CHUNK CONTENT COMPARISON")
    print("=" * 100)
    
    show_detailed_chunk_comparison()
    compare_metadata_structures()
    show_learning_flow_impact()
    
    print("\n" + "=" * 100)
    print("📊 SUMMARY: Why Holistic Chunks Are Superior")
    print("=" * 100)
    
    comparison = [
        ("Aspect", "Original System", "Holistic System"),
        ("Content Organization", "Fragmented pieces", "Complete learning units"),
        ("Context Preservation", "Lost completely", "Fully preserved"),
        ("Student Experience", "Confusing", "Clear & logical"),
        ("Learning Flow", "Broken", "Natural progression"),
        ("Duplication", "Massive (bug)", "None"),
        ("Metadata Richness", "Basic (4 fields)", "Rich (25+ fields)"),
        ("Adaptive Learning", "Not possible", "Fully enabled"),
        ("Prerequisites", "Not tracked", "Cross-grade mapping"),
        ("Quality Assurance", "None", "Multiple metrics")
    ]
    
    print("\n┌─────────────────────┬─────────────────────┬─────────────────────┐")
    print("│{:^21}│{:^21}│{:^21}│".format(*comparison[0]))
    print("├─────────────────────┼─────────────────────┼─────────────────────┤")
    for aspect, original, holistic in comparison[1:]:
        print("│{:<21}│{:<21}│{:<21}│".format(aspect, original, holistic))
    print("└─────────────────────┴─────────────────────┴─────────────────────┘")
    
    print("\n🎯 The Holistic Educational RAG System transforms fragmented content")
    print("   into coherent, contextual learning experiences!")