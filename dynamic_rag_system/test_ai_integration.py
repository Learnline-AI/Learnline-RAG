#!/usr/bin/env python3
"""
AI Integration Test for Enhanced Educational RAG System
Tests AI-powered boundary detection and concept extraction
"""

import os
import sys
import asyncio
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from ai.ai_integration import get_ai_service, ai_detect_boundaries, ai_extract_concepts

def test_sample_content():
    """Test with sample educational content"""
    sample_content = """
    8.1 PRODUCTION OF SOUND
    
    Take a metal scale or a ruler. Place it on your desk such that a part of the scale juts out from the edge of the desk. Now bend the part of the scale which is jutting out and then let it go. Do you hear any sound? Touch the scale while it is producing sound. Can you feel the vibrations? Again place the scale on the desk. This time use a longer part of the scale to produce sound. Can you hear any difference in the sound produced?
    
    ACTIVITY 8.1
    Take a rubber band. Put it around your fingers as shown in Fig. 8.1. Now stretch the rubber band and pluck it. Do you hear a sound? Does the rubber band vibrate?
    
    Now stretch the rubber band a little more and pluck again. Is the sound different from the one produced earlier?
    
    From these activities we learn that vibrating objects produce sound. In the first case the vibrating object was the scale and in the second case the vibrating object was the stretched rubber band.
    
    Example 8.1
    When we speak, sound is produced. Which part of our body vibrates to produce sound?
    
    Solution: When we speak, our vocal cords vibrate to produce sound.
    """
    
    return sample_content

async def test_ai_boundary_detection():
    """Test AI boundary detection"""
    print("🔍 Testing AI Boundary Detection...")
    
    ai_service = get_ai_service()
    if not ai_service.is_available():
        print("❌ AI service not available (no API keys configured)")
        return
    
    content = test_sample_content()
    
    try:
        boundaries = await ai_detect_boundaries(content)
        
        if boundaries:
            print(f"✅ AI detected {len(boundaries.get('learning_units', []))} learning units")
            
            for i, unit in enumerate(boundaries.get('learning_units', [])):
                print(f"  Unit {i+1}:")
                print(f"    Type: {unit.get('type', 'unknown')}")
                print(f"    Description: {unit.get('description', 'N/A')}")
                print(f"    Elements: {unit.get('educational_elements', [])}")
                print(f"    Position: {unit.get('start', 0)}-{unit.get('end', 0)}")
                print()
        else:
            print("❌ No boundaries detected")
            
    except Exception as e:
        print(f"❌ Boundary detection failed: {e}")

async def test_ai_concept_extraction():
    """Test AI concept extraction"""
    print("🧠 Testing AI Concept Extraction...")
    
    ai_service = get_ai_service()
    if not ai_service.is_available():
        print("❌ AI service not available (no API keys configured)")
        return
    
    content = test_sample_content()
    
    try:
        concepts = await ai_extract_concepts(content, subject="Physics", grade_level=8)
        
        if concepts:
            print("✅ AI extracted concepts:")
            print(f"  Main concepts: {concepts.get('main_concepts', [])}")
            print(f"  Sub-concepts: {concepts.get('sub_concepts', [])}")
            
            relationships = concepts.get('concept_relationships', [])
            if relationships:
                print(f"  Relationships: {len(relationships)} found")
                for rel in relationships[:3]:  # Show first 3
                    print(f"    {rel.get('from', 'unknown')} → {rel.get('to', 'unknown')} ({rel.get('relationship', 'unknown')})")
            
            context = concepts.get('educational_context', {})
            if context:
                print(f"  Applications: {context.get('applications', [])}")
                print(f"  Examples: {context.get('examples', [])}")
                print(f"  Misconceptions: {context.get('misconceptions', [])}")
        else:
            print("❌ No concepts extracted")
            
    except Exception as e:
        print(f"❌ Concept extraction failed: {e}")

async def main():
    """Main test function"""
    print("🚀 AI Integration Test - Enhanced Educational RAG System")
    print("=" * 60)
    
    # Test AI service availability
    ai_service = get_ai_service()
    print(f"AI Service Available: {'✅ Yes' if ai_service.is_available() else '❌ No'}")
    
    if not ai_service.is_available():
        print("\n💡 To enable AI features, set environment variables:")
        print("   export OPENAI_API_KEY='your-key'")
        print("   export ANTHROPIC_API_KEY='your-key'")
        return
    
    print(f"Usage Stats: {ai_service.get_usage_statistics()}")
    print()
    
    # Run tests
    await test_ai_boundary_detection()
    print()
    await test_ai_concept_extraction()
    
    print("\n📊 Final Usage Stats:")
    print(ai_service.get_usage_statistics())
    
    print("\n🎉 AI Integration test completed!")

if __name__ == "__main__":
    asyncio.run(main())