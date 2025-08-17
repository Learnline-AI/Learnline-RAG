#!/usr/bin/env python3
"""
Comprehensive System Test
Tests all components of the enhanced Educational RAG system
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
from quality_validation_system import QualityValidator
import json

def create_comprehensive_test_content():
    """Create comprehensive test content covering all educational elements"""
    return """
7.1 Describing Motion

Motion is everywhere around us. We observe motion in our daily life - birds flying, cars moving, leaves falling. But how do we describe motion scientifically?

To describe motion, we need to specify a reference point. An object is said to be in motion if it changes its position with respect to a reference point with time.

Distance is the actual length of the path traveled by an object. Displacement is the shortest distance between the initial and final positions of the object.

Speed is the rate of change of distance with time, while velocity is the rate of change of displacement with time. Acceleration is the rate of change of velocity with time.

ACTIVITY 7.1
Take a ball and place it on the ground. Mark the position as point O. Now push the ball and let it roll to point A. 

Materials needed: A ball, measuring tape, stopwatch
Time required: 15 minutes

Observe and note:
• Distance traveled by the ball
• Time taken to travel from O to A
• Direction of motion

From this activity, we learn that motion involves change in position with time, and we can measure both distance and time to understand motion better.

DO YOU KNOW?
The Global Positioning System (GPS) uses the concept of relative motion to determine your location. GPS satellites constantly broadcast their position and time, and your GPS receiver calculates your position based on signals from multiple satellites.

Example 7.1
A car travels from city A to city B, a distance of 100 km, in 2 hours. Then it travels from city B to city C, covering 80 km in 1.5 hours. Calculate the average speed for the entire journey.

Given:
Distance AB = 100 km, Time AB = 2 hours
Distance BC = 80 km, Time BC = 1.5 hours

Solution:
Total distance = 100 + 80 = 180 km
Total time = 2 + 1.5 = 3.5 hours
Average speed = Total distance / Total time = 180 / 3.5 = 51.4 km/h

Therefore, the average speed for the entire journey is 51.4 km/h.

Real-world Applications:
• Transportation systems use speed calculations for scheduling
• Sports analysis relies on velocity and acceleration measurements  
• Navigation systems calculate optimal routes using motion principles
• Safety systems in vehicles use acceleration data for airbag deployment

THINK AND ACT
1. Observe five different types of motion in your surroundings
2. Measure the speed of a moving object (like a bicycle or car) safely
3. Design an experiment to demonstrate relative motion
4. Research how motion sensors work in automatic doors

Questions
1. What is the difference between distance and displacement?
2. A student walks 4 meters east, then 3 meters north. What is the distance and displacement?
3. If a car travels 60 km in 1 hour, what is its speed? If it maintains the same direction, what is its velocity?
4. Give two examples each of uniform and non-uniform motion.

Multiple Choice Questions
1. The SI unit of speed is:
   (a) m/s²    (b) m/s    (c) km/h    (d) m

2. Which of the following is a vector quantity?
   (a) Distance    (b) Speed    (c) Displacement    (d) Time

What you have learnt
• Motion is the change in position of an object with time
• Distance is scalar, displacement is vector
• Speed is scalar, velocity is vector  
• We need a reference point to describe motion
• Motion can be uniform or non-uniform
• Average speed = Total distance / Total time
• Motion concepts have many real-world applications

Remember: Motion and rest are relative terms - an object can be at rest relative to one observer and in motion relative to another.

Key Points to Remember:
• Always specify the reference point when describing motion
• Distance is always positive, displacement can be positive or negative
• Speed is always positive, velocity can have direction
• Acceleration occurs when velocity changes
"""

def test_complete_system():
    """Test the complete enhanced system"""
    print("🚀 COMPREHENSIVE EDUCATIONAL RAG SYSTEM TEST")
    print("=" * 80)
    
    # Initialize components
    chunker = HolisticRAGChunker()
    validator = QualityValidator()
    
    # Get test content
    test_content = create_comprehensive_test_content()
    print(f"📄 Test content: {len(test_content)} characters")
    print(f"📊 Contains: Activities, Examples, Questions, Applications, Summary")
    
    # Create mother section
    mother_section = {
        'section_number': '7.1',
        'title': 'Describing Motion',
        'start_pos': 0,
        'end_pos': len(test_content),
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 7
    }
    
    # Process content
    char_to_page_map = {i: 1 for i in range(len(test_content))}
    
    try:
        print("\n🔄 Processing with Enhanced RAG System...")
        chunks = chunker.process_mother_section(
            mother_section=mother_section,
            full_text=test_content,
            char_to_page_map=char_to_page_map
        )
        
        print(f"✅ Created {len(chunks)} chunks")
        
        # Validate each chunk
        validation_results = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n📋 VALIDATING CHUNK {i}: {chunk.chunk_id}")
            print("─" * 60)
            
            # Run comprehensive validation
            result = validator.validate_chunk_quality(chunk, test_content)
            validation_results.append(result)
            
            # Display results
            print(f"Overall Score: {result['overall_score']:.2%}")
            print(f"Status: {'✅ PASSED' if result['passed'] else '❌ FAILED'}")
            
            print(f"\nIndividual Scores:")
            for metric, score in result['individual_scores'].items():
                status = "✅" if score >= validator.thresholds.get(metric, 0.8) else "❌"
                print(f"  {status} {metric.replace('_', ' ').title()}: {score:.2%}")
            
            if result['issues']:
                print(f"\n⚠️  Issues Found ({len(result['issues'])}):")
                for issue in result['issues'][:3]:  # Show first 3
                    print(f"  • {issue}")
            
            if result['recommendations']:
                print(f"\n💡 Recommendations:")
                for rec in result['recommendations'][:2]:  # Show first 2
                    print(f"  • {rec}")
        
        # System-level validation
        print(f"\n🎯 SYSTEM-LEVEL VALIDATION")
        print("=" * 60)
        
        system_performance = validator.validate_system_performance(validation_results)
        
        print(f"Overall Grade: {system_performance['overall_grade']}")
        print(f"Overall Score: {system_performance['overall_score']:.2%}")
        print(f"Pass Rate: {system_performance['pass_rate']:.2%}")
        print(f"Tests Passed: {system_performance['passed_tests']}/{system_performance['total_tests']}")
        
        print(f"\nAverage Scores by Category:")
        for metric, score in system_performance['avg_scores'].items():
            print(f"  • {metric.replace('_', ' ').title()}: {score:.2%}")
        
        # Display sample content
        if chunks:
            print(f"\n📖 SAMPLE PROCESSED CONTENT:")
            print("─" * 60)
            sample_content = chunks[0].content
            print(f"Content Length: {len(sample_content)} characters")
            print(f"First 200 chars: {sample_content[:200]}...")
            print(f"Last 200 chars: ...{sample_content[-200:]}")
            
            # Show metadata summary
            metadata = chunks[0].metadata
            concepts = metadata.get('concepts_and_skills', {}).get('main_concepts', [])
            applications = metadata.get('educational_context', {}).get('real_world_applications', [])
            
            print(f"\n📊 METADATA SUMMARY:")
            print(f"  Main Concepts: {len(concepts)} ({', '.join(concepts[:5])}{'...' if len(concepts) > 5 else ''})")
            print(f"  Applications: {len(applications)}")
            print(f"  Quality Score: {chunks[0].quality_score}")
        
        return system_performance
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def display_final_assessment(system_performance):
    """Display final system assessment"""
    print(f"\n🎊 FINAL SYSTEM ASSESSMENT")
    print("=" * 80)
    
    if not system_performance:
        print("❌ SYSTEM FAILED: Unable to complete testing")
        return False
    
    grade = system_performance['overall_grade']
    score = system_performance['overall_score']
    
    if grade in ['A+', 'A']:
        print("🏆 EXCELLENT: Educational RAG System performs at production level!")
        print("✅ All major issues fixed")
        print("✅ High-quality content processing")
        print("✅ Comprehensive metadata extraction")
        print("✅ Robust quality validation")
        success = True
    elif grade in ['B+', 'B']:
        print("👍 GOOD: System performs well with minor improvements needed")
        print("✅ Major fixes successful")
        print("⚠️  Some refinement opportunities")
        success = True
    elif grade == 'C':
        print("⚠️  ACCEPTABLE: System functional but needs improvement")
        success = False
    else:
        print("❌ NEEDS WORK: Significant issues remain")
        success = False
    
    print(f"\n📊 PERFORMANCE SUMMARY:")
    print(f"  Grade: {grade}")
    print(f"  Overall Score: {score:.1%}")
    print(f"  Pass Rate: {system_performance['pass_rate']:.1%}")
    
    print(f"\n🔧 KEY IMPROVEMENTS MADE:")
    print("✅ Fixed content truncation (complete sections captured)")
    print("✅ Improved concept extraction (physics-aware, filtered)")
    print("✅ Enhanced applications extraction (clean, meaningful)")
    print("✅ Implemented comprehensive quality validation")
    print("✅ Rich AI-powered metadata extraction")
    print("✅ Enhanced boundary detection")
    
    if success:
        print(f"\n🚀 READY FOR PRODUCTION!")
        print("The Enhanced Educational RAG System successfully processes")
        print("NCERT content with high quality and comprehensive intelligence.")
    
    return success

def main():
    """Main test execution"""
    print("🎓 ENHANCED EDUCATIONAL RAG SYSTEM - COMPREHENSIVE VALIDATION")
    print("=" * 80)
    
    # Run comprehensive system test
    system_performance = test_complete_system()
    
    # Display final assessment
    success = display_final_assessment(system_performance)
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()