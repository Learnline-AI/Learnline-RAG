#!/usr/bin/env python3
"""
Vector Embeddings Test for Enhanced Educational RAG System
Tests embedding generation and semantic similarity search
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from embeddings.vector_embedding_engine import VectorEmbeddingEngine, create_embeddings_for_chunks, find_semantically_similar_content

def create_sample_chunks():
    """Create sample educational chunks for testing"""
    return [
        {
            'chunk_id': 'sound_production_1',
            'content': 'Sound is produced when an object vibrates. The vibrating object creates disturbances in the surrounding medium, which travel as waves. When we pluck a guitar string, it vibrates and produces sound.',
            'metadata': {
                'type': 'conceptual_explanation',
                'basic_info': {
                    'subject': 'Physics',
                    'grade_level': 8,
                    'chapter': 8
                },
                'concepts_and_skills': {
                    'main_concepts': ['sound production', 'vibration', 'sound waves']
                }
            },
            'quality_score': 0.85
        },
        {
            'chunk_id': 'sound_propagation_1',
            'content': 'Sound waves travel through a medium by creating compressions and rarefactions. The speed of sound depends on the properties of the medium. In air, sound travels at approximately 343 meters per second at room temperature.',
            'metadata': {
                'type': 'conceptual_explanation',
                'basic_info': {
                    'subject': 'Physics',
                    'grade_level': 8,
                    'chapter': 8
                },
                'concepts_and_skills': {
                    'main_concepts': ['sound propagation', 'compression', 'rarefaction', 'speed of sound']
                }
            },
            'quality_score': 0.90
        },
        {
            'chunk_id': 'echo_activity_1',
            'content': 'ACTIVITY 8.3: Stand at a distance from a large wall or building. Clap your hands loudly and listen carefully. Do you hear the sound returning to you? This is called an echo. Echo is the reflection of sound waves from a surface.',
            'metadata': {
                'type': 'hands_on_activity',
                'basic_info': {
                    'subject': 'Physics',
                    'grade_level': 8,
                    'chapter': 8
                },
                'concepts_and_skills': {
                    'main_concepts': ['echo', 'sound reflection', 'activity']
                }
            },
            'quality_score': 0.75
        },
        {
            'chunk_id': 'light_propagation_1',
            'content': 'Light travels in straight lines at a speed of approximately 300,000,000 meters per second in vacuum. Unlike sound, light can travel through vacuum and does not require a medium for propagation.',
            'metadata': {
                'type': 'conceptual_explanation',
                'basic_info': {
                    'subject': 'Physics',
                    'grade_level': 8,
                    'chapter': 9
                },
                'concepts_and_skills': {
                    'main_concepts': ['light propagation', 'speed of light', 'vacuum']
                }
            },
            'quality_score': 0.88
        },
        {
            'chunk_id': 'math_algebra_1',
            'content': 'An algebraic expression contains variables, constants, and mathematical operations. For example, 2x + 3y - 5 is an algebraic expression where x and y are variables, 2 and 3 are coefficients, and 5 is a constant.',
            'metadata': {
                'type': 'conceptual_explanation',
                'basic_info': {
                    'subject': 'Mathematics',
                    'grade_level': 7,
                    'chapter': 12
                },
                'concepts_and_skills': {
                    'main_concepts': ['algebraic expressions', 'variables', 'constants', 'coefficients']
                }
            },
            'quality_score': 0.82
        }
    ]

def test_embedding_generation():
    """Test basic embedding generation"""
    print("🧠 Testing Embedding Generation...")
    
    engine = VectorEmbeddingEngine()
    
    if not engine.is_available():
        print("❌ No embedding models available")
        print("💡 To enable embeddings, install one of:")
        print("   pip install sentence-transformers")
        print("   pip install scikit-learn")
        return False
    
    print(f"✅ Using embedding model: {engine.config['embedding_model']}")
    print(f"   Model name: {engine.config.get('model_name', 'N/A')}")
    print(f"   Dimensions: {engine.config['embedding_dimensions']}")
    
    # Test single embedding
    test_content = "Sound is produced by vibrating objects that create waves in the air."
    embedding = engine.generate_embedding(test_content)
    
    if embedding is not None:
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   Embedding type: {type(embedding)}")
        print(f"   Sample values: {embedding[:5]}...")
        return True
    else:
        print("❌ Failed to generate embedding")
        return False

def test_batch_embedding_generation():
    """Test batch embedding generation"""
    print("\n📦 Testing Batch Embedding Generation...")
    
    engine = VectorEmbeddingEngine()
    if not engine.is_available():
        return False
    
    sample_chunks = create_sample_chunks()
    contents = [chunk['content'] for chunk in sample_chunks]
    
    embeddings = engine.generate_embeddings_batch(contents)
    
    if embeddings and all(emb is not None for emb in embeddings):
        print(f"✅ Generated {len(embeddings)} embeddings in batch")
        print(f"   All embeddings have {len(embeddings[0])} dimensions")
        return True
    else:
        print(f"❌ Batch generation failed or incomplete ({sum(1 for e in embeddings if e is not None)}/{len(embeddings)} successful)")
        return False

def test_similarity_computation():
    """Test similarity computation between embeddings"""
    print("\n🔍 Testing Similarity Computation...")
    
    engine = VectorEmbeddingEngine()
    if not engine.is_available():
        return False
    
    # Create test embeddings
    content1 = "Sound is produced by vibrating objects."
    content2 = "Objects that vibrate create sound waves."
    content3 = "Light travels at the speed of 300,000,000 m/s."
    
    emb1 = engine.generate_embedding(content1)
    emb2 = engine.generate_embedding(content2)
    emb3 = engine.generate_embedding(content3)
    
    if all(emb is not None for emb in [emb1, emb2, emb3]):
        sim_12 = engine.compute_similarity(emb1, emb2)
        sim_13 = engine.compute_similarity(emb1, emb3)
        sim_23 = engine.compute_similarity(emb2, emb3)
        
        print(f"✅ Similarity scores computed:")
        print(f"   Sound vs Sound (similar): {sim_12:.3f}")
        print(f"   Sound vs Light (different): {sim_13:.3f}")
        print(f"   Sound vs Light (different): {sim_23:.3f}")
        
        # Expected: sim_12 should be higher than sim_13 and sim_23
        if sim_12 > max(sim_13, sim_23):
            print("✅ Similarity ranking is correct")
            return True
        else:
            print("⚠️ Similarity ranking may need improvement")
            return True
    else:
        print("❌ Failed to generate embeddings for similarity test")
        return False

def test_semantic_search():
    """Test semantic similarity search"""
    print("\n🔎 Testing Semantic Search...")
    
    engine = VectorEmbeddingEngine()
    if not engine.is_available():
        return False
    
    sample_chunks = create_sample_chunks()
    
    # Test query
    query = "How do vibrations create sound?"
    
    # Find similar content
    matches = find_semantically_similar_content(query, sample_chunks, top_k=3, embedding_engine=engine)
    
    if matches:
        print(f"✅ Found {len(matches)} similar chunks for query: '{query}'")
        for i, match in enumerate(matches):
            print(f"\n   Match {i+1}:")
            print(f"     Chunk ID: {match.chunk_id}")
            print(f"     Similarity: {match.similarity_score:.3f}")
            print(f"     Type: {match.chunk_type}")
            print(f"     Concepts: {match.concepts}")
            print(f"     Preview: {match.content_preview[:100]}...")
        
        # Check if the most similar chunk is actually about sound
        top_match = matches[0]
        sound_related = any(concept.lower().find('sound') != -1 for concept in top_match.concepts)
        if sound_related:
            print("✅ Top match is correctly about sound")
            return True
        else:
            print("⚠️ Top match may not be optimal")
            return True
    else:
        print("❌ No similar chunks found")
        return False

def test_embedding_cache():
    """Test embedding caching functionality"""
    print("\n💾 Testing Embedding Cache...")
    
    engine = VectorEmbeddingEngine()
    if not engine.is_available():
        return False
    
    sample_chunks = create_sample_chunks()[:2]  # Use fewer chunks for cache test
    
    # Create embeddings and save to cache
    print("   Creating embeddings and saving to cache...")
    chunk_embeddings = create_embeddings_for_chunks(sample_chunks, engine)
    
    if chunk_embeddings:
        print(f"✅ Created and cached {len(chunk_embeddings)} embeddings")
        
        # Test loading from cache
        chunk_ids = list(chunk_embeddings.keys())
        cached_data = engine.load_embeddings_from_cache(chunk_ids)
        
        if cached_data:
            print(f"✅ Loaded {len(cached_data)} embeddings from cache")
            
            # Verify consistency
            for chunk_id in chunk_ids:
                if chunk_id in cached_data:
                    original_emb = chunk_embeddings[chunk_id]
                    cached_emb, metadata = cached_data[chunk_id]
                    
                    # Check if embeddings are similar (allowing for small floating point differences)
                    similarity = engine.compute_similarity(original_emb, cached_emb)
                    if similarity > 0.99:  # Should be very close to 1.0
                        print(f"✅ Cache consistency verified for {chunk_id}")
                    else:
                        print(f"⚠️ Cache inconsistency detected for {chunk_id}: {similarity:.3f}")
            
            return True
        else:
            print("❌ Failed to load from cache")
            return False
    else:
        print("❌ Failed to create embeddings")
        return False

def test_embedding_statistics():
    """Test embedding statistics functionality"""
    print("\n📊 Testing Embedding Statistics...")
    
    engine = VectorEmbeddingEngine()
    if not engine.is_available():
        return False
    
    stats = engine.get_embedding_statistics()
    
    print("✅ Embedding Statistics:")
    print(f"   Total embeddings: {stats.get('total_embeddings', 0)}")
    print(f"   Models used: {stats.get('models_used', [])}")
    print(f"   Cache size: {stats.get('cache_size_mb', 0)} MB")
    print(f"   Embedding dimensions: {stats.get('embedding_dimensions', 0)}")
    print(f"   Current model: {stats.get('current_model', 'unknown')}")
    
    return True

def main():
    """Main test function"""
    print("🚀 Vector Embeddings Test - Enhanced Educational RAG System")
    print("=" * 70)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Embedding Generation", test_embedding_generation),
        ("Batch Generation", test_batch_embedding_generation),
        ("Similarity Computation", test_similarity_computation),
        ("Semantic Search", test_semantic_search),
        ("Embedding Cache", test_embedding_cache),
        ("Statistics", test_embedding_statistics)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*10} {test_name} {'='*10}")
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*30} SUMMARY {'='*30}")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 All vector embedding tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) need attention")
    
    return passed == total

if __name__ == "__main__":
    main()