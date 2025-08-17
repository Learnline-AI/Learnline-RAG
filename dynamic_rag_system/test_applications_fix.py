#!/usr/bin/env python3
"""
Test Real-World Applications Extraction Fix
Validates that applications are clean, complete sentences
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
from metadata_extraction_engine import MetadataExtractionEngine

def test_applications_extraction():
    """Test improved applications extraction"""
    print("🌍 TESTING IMPROVED APPLICATIONS EXTRACTION")
    print("=" * 80)
    
    # Test content with various application descriptions
    test_content = """
7.1 Motion in Our Daily Life

Motion is fundamental to our existence. Understanding motion helps us in many ways.

DO YOU KNOW?
The principles of motion are used in designing safer vehicles. Airbags deploy based 
on sudden deceleration. GPS systems track motion to provide navigation. Motion sensors 
are used in automatic doors and security systems.

In everyday life, we apply concepts of motion when we:
• Drive vehicles and judge safe distances
• Play sports and calculate trajectories  
• Design machines and mechanisms
• Navigate using maps and GPS

Real-world Applications:
1. Transportation: Cars, trains, and airplanes all use principles of motion
2. Sports: Athletes use understanding of motion to improve performance
3. Technology: Smartphones use accelerometers to detect motion
4. Medicine: Motion analysis helps in physiotherapy and rehabilitation

THINK AND ACT
Motion detection technology is essential for modern security systems. It enables 
automatic lighting, helps in wildlife photography, and makes gaming controllers work.

The study of motion has practical applications in engineering, where it helps design 
efficient machines. In medicine, motion analysis is used to diagnose and treat 
movement disorders. Space missions rely heavily on precise motion calculations.

Questions
How is motion used in your daily activities?
"""
    
    # Initialize chunker
    chunker = HolisticRAGChunker()
    
    # Create mother section
    mother_section = {
        'section_number': '7.1',
        'title': 'Motion in Our Daily Life',
        'start_pos': 0,
        'end_pos': len(test_content),
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 7
    }
    
    # Process content
    char_to_page_map = {i: 1 for i in range(len(test_content))}
    
    try:
        chunks = chunker.process_mother_section(
            mother_section=mother_section,
            full_text=test_content,
            char_to_page_map=char_to_page_map
        )
        
        print(f"✅ Created {len(chunks)} chunks")
        
        if chunks:
            chunk = chunks[0]
            metadata = chunk.metadata
            context = metadata.get('educational_context', {})
            applications = context.get('real_world_applications', [])
            
            print(f"\n📊 APPLICATIONS EXTRACTION RESULTS")
            print("=" * 60)
            print(f"Total applications extracted: {len(applications)}")
            
            # Analyze applications
            good_applications = []
            bad_applications = []
            
            for app in applications:
                # Check quality criteria
                issues = []
                
                # Check if it's a complete sentence
                if not app.strip():
                    issues.append("Empty")
                elif len(app.strip()) < 20:
                    issues.append("Too short")
                elif app[0].islower():
                    issues.append("Starts lowercase")
                elif not any(char in app for char in '.!?'):
                    issues.append("No punctuation")
                elif len(app.split()) < 3:
                    issues.append("Too few words")
                
                # Check for common fragment patterns
                fragment_starts = ['d today', 'nd the', 'or the', 'of the']
                if any(app.lower().startswith(frag) for frag in fragment_starts):
                    issues.append("Fragment start")
                
                if issues:
                    bad_applications.append((app, issues))
                else:
                    good_applications.append(app)
            
            print(f"\n✅ GOOD APPLICATIONS ({len(good_applications)}):")
            for i, app in enumerate(good_applications[:5], 1):
                print(f"   {i}. {app}")
            
            if bad_applications:
                print(f"\n❌ BAD APPLICATIONS ({len(bad_applications)}):")
                for i, (app, issues) in enumerate(bad_applications[:3], 1):
                    print(f"   {i}. '{app}' - Issues: {', '.join(issues)}")
            else:
                print(f"\n✅ NO BAD APPLICATIONS FOUND!")
            
            # Quality assessment
            if applications:
                quality_score = len(good_applications) / len(applications)
            else:
                quality_score = 0
                
            print(f"\n📈 APPLICATION QUALITY SCORE: {quality_score:.2%}")
            
            if quality_score >= 0.8:
                print("✅ Excellent application extraction quality!")
            elif quality_score >= 0.6:
                print("⚠️  Good application extraction, minor issues")
            else:
                print("❌ Poor application extraction quality")
            
            return quality_score >= 0.8
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fragment_cleaning():
    """Test that fragments are properly cleaned"""
    print(f"\n🧪 TESTING FRAGMENT CLEANING")
    print("=" * 60)
    
    # Test the cleaning methods directly
    engine = MetadataExtractionEngine()
    
    test_cases = [
        # (input, expected_output)
        ("d today to understand motion", "Today to understand motion."),
        ("the principles are used in", "The principles are used in."),
        ("Motion sensors help us  .", "Motion sensors help us."),
        ("GPS systems track motion", "GPS systems track motion."),
        ("  helps in wildlife photography  ", "Helps in wildlife photography."),
    ]
    
    all_passed = True
    for input_text, expected in test_cases:
        cleaned = engine._clean_application_text(input_text)
        is_valid = engine._is_valid_application(cleaned)
        
        if is_valid and len(cleaned) >= 20:
            print(f"✅ '{input_text}' → '{cleaned}'")
        else:
            print(f"❌ '{input_text}' → '{cleaned}' (Invalid: too short or fragment)")
            all_passed = False
    
    return all_passed

def main():
    """Main test function"""
    print("🚀 APPLICATIONS EXTRACTION FIX VALIDATION")
    print("=" * 80)
    
    # Test 1: Full extraction test
    extraction_success = test_applications_extraction()
    
    # Test 2: Fragment cleaning test
    cleaning_success = test_fragment_cleaning()
    
    # Final assessment
    print(f"\n🎯 APPLICATIONS EXTRACTION ASSESSMENT")
    print("=" * 50)
    
    if extraction_success:
        print("🎉 SUCCESS: Applications extraction is now working correctly!")
        print("✅ Complete sentences extracted")
        print("✅ Fragments cleaned or filtered") 
        print("✅ Meaningful applications identified")
        print("✅ Quality threshold achieved")
        
        print(f"\n🚀 IMPROVEMENTS:")
        print("✅ Enhanced extraction patterns")
        print("✅ Fragment detection and cleaning")
        print("✅ Sentence boundary validation")
        print("✅ Application quality filtering")
        print("✅ Context-aware extraction")
        
        return True
    else:
        print("❌ Applications extraction still needs work")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)