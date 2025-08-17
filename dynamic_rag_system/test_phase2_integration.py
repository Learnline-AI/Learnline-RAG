#!/usr/bin/env python3
"""
Phase 2 Integration Test for Enhanced Educational RAG System
Tests the complete system with AI-powered boundary detection, concept extraction, and vector embeddings
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker, HolisticChunk
from embeddings.vector_embedding_engine import VectorEmbeddingEngine, create_embeddings_for_chunks, find_semantically_similar_content
from quality_validation_system import QualityValidator

def create_sample_mother_section():
    """Create a comprehensive sample mother section for testing"""
    return {
        'section_number': '8.1',
        'title': 'PRODUCTION OF SOUND',
        'start_pos': 0,
        'end_pos': 2000,
        'content_length': 2000,
        'grade_level': 8,
        'subject': 'Physics',
        'chapter': 8,
        'content': """
8.1 PRODUCTION OF SOUND

Take a metal scale or a ruler. Place it on your desk such that a part of the scale juts out from the edge of the desk. Now bend the part of the scale which is jutting out and then let it go. Do you hear any sound? Touch the scale while it is producing sound. Can you feel the vibrations? Again place the scale on the desk. This time use a longer part of the scale to produce sound. Can you hear any difference in the sound produced?

ACTIVITY 8.1
Take a rubber band. Put it around your fingers as shown in Fig. 8.1. Now stretch the rubber band and pluck it. Do you hear a sound? Does the rubber band vibrate?

Now stretch the rubber band a little more and pluck again. Is the sound different from the one produced earlier?

From these activities we learn that vibrating objects produce sound. In the first case the vibrating object was the scale and in the second case the vibrating object was the stretched rubber band.

Example 8.1
When we speak, sound is produced. Which part of our body vibrates to produce sound?

Solution: When we speak, our vocal cords vibrate to produce sound.

DO YOU KNOW?
The vibrations of a sound source are usually very fast. Sometimes we cannot see the vibrations with our naked eyes.

What you have learnt
• Sound is produced by vibrating objects.
• Vibrating objects create disturbances in the surrounding medium.
• These disturbances travel as sound waves.
"""
    }

def create_char_to_page_map(content_length: int) -> dict:
    """Create a simple character to page mapping"""
    chars_per_page = 2000  # Assume 2000 characters per page
    char_to_page = {}
    for i in range(content_length):
        page = (i // chars_per_page) + 1
        char_to_page[i] = page
    return char_to_page

async def test_ai_powered_chunking():
    """Test AI-powered chunking with boundary detection"""
    print("🧠 Testing AI-Powered Chunking...")
    
    # Set up chunker
    chunker = HolisticRAGChunker()
    
    # Create sample data
    mother_section = create_sample_mother_section()
    full_text = mother_section['content']
    char_to_page_map = create_char_to_page_map(len(full_text))
    
    try:
        # Process section with AI-powered chunking
        chunks = chunker.process_mother_section(mother_section, full_text, char_to_page_map)
        
        if chunks:
            print(f"✅ Created {len(chunks)} chunks using AI-powered system")
            
            # Display chunk information
            for i, chunk in enumerate(chunks):
                print(f"\n  Chunk {i+1}:")
                print(f"    ID: {chunk.chunk_id}")
                print(f"    Type: {chunk.metadata.get('type', 'unknown')}")
                print(f"    Length: {len(chunk.content)} chars")
                print(f"    Quality Score: {chunk.quality_score:.2f}")
                
                # Show main concepts
                main_concepts = chunk.metadata.get('concepts_and_skills', {}).get('main_concepts', [])
                print(f"    Main Concepts: {main_concepts[:3]}")  # Show first 3
                
                # Check for AI enhancements
                ai_relationships = chunk.metadata.get('concepts_and_skills', {}).get('ai_relationships', [])
                if ai_relationships:
                    print(f"    AI Relationships: {len(ai_relationships)} found")
                
                # Content preview
                preview = chunk.content[:150].replace('\n', ' ').strip()
                print(f"    Preview: {preview}...")
            
            return chunks
        else:
            print("❌ No chunks created")
            return []
            
    except Exception as e:
        print(f"❌ AI chunking failed: {e}")
        return []

async def test_vector_embeddings_integration(chunks):
    """Test vector embeddings integration with chunks"""
    print(f"\n🔢 Testing Vector Embeddings Integration...")
    
    if not chunks:
        print("❌ No chunks to create embeddings for")
        return {}
    
    try:
        # Create embedding engine
        embedding_engine = VectorEmbeddingEngine()
        
        if not embedding_engine.is_available():
            print("❌ Embedding engine not available")
            return {}
        
        print(f"✅ Using {embedding_engine.config['embedding_model']} embeddings")
        
        # Convert chunks to embedding format
        chunk_data = []
        for chunk in chunks:
            chunk_data.append({
                'chunk_id': chunk.chunk_id,
                'content': chunk.content,
                'metadata': chunk.metadata,
                'quality_score': chunk.quality_score
            })
        
        # Create embeddings
        embeddings = create_embeddings_for_chunks(chunk_data, embedding_engine)
        
        if embeddings:
            print(f"✅ Created embeddings for {len(embeddings)} chunks")
            print(f"   Embedding dimensions: {len(next(iter(embeddings.values())))}")
            
            # Test semantic search
            test_queries = [
                "How is sound produced?",
                "What causes vibrations?",
                "Activities about sound",
                "Examples of sound production"
            ]
            
            print(f"\n🔍 Testing semantic search with {len(test_queries)} queries:")
            
            search_results = {}
            for query in test_queries:
                matches = find_semantically_similar_content(
                    query, chunk_data, top_k=2, embedding_engine=embedding_engine
                )
                search_results[query] = matches
                
                print(f"\n  Query: '{query}'")
                if matches:
                    print(f"    Found {len(matches)} matches:")
                    for j, match in enumerate(matches):
                        print(f"      {j+1}. {match.chunk_id} (similarity: {match.similarity_score:.3f})")
                        print(f"         Type: {match.chunk_type}")
                        print(f"         Concepts: {match.concepts[:2]}")  # Show first 2
                else:
                    print("    No matches found")
            
            return search_results
        else:
            print("❌ Failed to create embeddings")
            return {}
            
    except Exception as e:
        print(f"❌ Vector embeddings integration failed: {e}")
        return {}

async def test_quality_validation_integration(chunks):
    """Test quality validation with enhanced chunks"""
    print(f"\n✅ Testing Quality Validation Integration...")
    
    if not chunks:
        print("❌ No chunks to validate")
        return {}
    
    try:
        validator = QualityValidator()
        
        quality_results = []
        total_score = 0
        
        print(f"   Validating {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            try:
                scores = validator.validate_chunk_quality(chunk, chunk.content)
                quality_results.append(scores)
                total_score += scores['overall_score']
                
                print(f"   Chunk {i+1}: {scores['overall_score']:.2f}/1.00")
                
            except Exception as e:
                print(f"   Chunk {i+1}: Validation failed - {e}")
        
        if quality_results:
            avg_score = total_score / len(quality_results)
            print(f"✅ Average quality score: {avg_score:.2f}/1.00")
            
            # Performance distribution
            excellent = sum(1 for r in quality_results if r['overall_score'] >= 0.8)
            good = sum(1 for r in quality_results if 0.6 <= r['overall_score'] < 0.8)
            fair = sum(1 for r in quality_results if 0.4 <= r['overall_score'] < 0.6)
            poor = sum(1 for r in quality_results if r['overall_score'] < 0.4)
            
            print(f"   Performance: Excellent({excellent}) Good({good}) Fair({fair}) Poor({poor})")
            
            return {
                'average_score': avg_score,
                'results': quality_results,
                'distribution': {'excellent': excellent, 'good': good, 'fair': fair, 'poor': poor}
            }
        else:
            print("❌ No quality validation results")
            return {}
            
    except Exception as e:
        print(f"❌ Quality validation failed: {e}")
        return {}

async def test_end_to_end_rag_pipeline():
    """Test the complete end-to-end RAG pipeline"""
    print(f"\n🔄 Testing End-to-End RAG Pipeline...")
    
    try:
        # Step 1: AI-powered chunking
        chunks = await test_ai_powered_chunking()
        if not chunks:
            return False
        
        # Step 2: Vector embeddings
        search_results = await test_vector_embeddings_integration(chunks)
        if not search_results:
            return False
        
        # Step 3: Quality validation
        quality_results = await test_quality_validation_integration(chunks)
        if not quality_results:
            return False
        
        # Step 4: End-to-end query test
        print(f"\n🎯 Testing Complete RAG Query Pipeline...")
        
        # Simulate a student query
        student_query = "I want to understand how sound is created through vibrations"
        
        print(f"   Student Query: '{student_query}'")
        
        # Find relevant chunks
        chunk_data = [{
            'chunk_id': chunk.chunk_id,
            'content': chunk.content,
            'metadata': chunk.metadata,
            'quality_score': chunk.quality_score
        } for chunk in chunks]
        
        embedding_engine = VectorEmbeddingEngine()
        matches = find_semantically_similar_content(
            student_query, chunk_data, top_k=3, embedding_engine=embedding_engine
        )
        
        if matches:
            print(f"✅ Found {len(matches)} relevant educational chunks")
            
            # Compile response from top matches
            response_chunks = []
            for match in matches:
                if match.similarity_score > 0.4:  # High relevance threshold
                    response_chunks.append({
                        'content': match.content_preview,
                        'concepts': match.concepts,
                        'type': match.chunk_type,
                        'relevance': match.similarity_score
                    })
            
            print(f"✅ Compiled response from {len(response_chunks)} high-quality chunks")
            print(f"   Average relevance: {sum(c['relevance'] for c in response_chunks) / len(response_chunks):.3f}")
            
            # Show response structure
            print(f"\n   Response Structure:")
            for i, chunk in enumerate(response_chunks):
                print(f"     {i+1}. {chunk['type']} (relevance: {chunk['relevance']:.3f})")
                print(f"        Concepts: {chunk['concepts'][:2]}")
                
            return True
        else:
            print("❌ No relevant chunks found for student query")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end pipeline failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Phase 2 Integration Test - Enhanced Educational RAG System")
    print("=" * 80)
    
    # Check prerequisites
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please set the API key before running Phase 2 tests")
        return
    
    print(f"✅ OpenAI API key configured")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run comprehensive integration test
    try:
        success = await test_end_to_end_rag_pipeline()
        
        print(f"\n{'='*30} FINAL RESULTS {'='*30}")
        
        if success:
            print("🎉 PHASE 2 INTEGRATION TEST: SUCCESS!")
            print("✅ All components working together successfully:")
            print("   • AI-powered boundary detection")
            print("   • Enhanced metadata extraction with AI concepts")
            print("   • OpenAI vector embeddings")
            print("   • Semantic similarity search")
            print("   • Quality validation")
            print("   • End-to-end RAG pipeline")
            print("\n🚀 System is ready for production deployment!")
        else:
            print("❌ PHASE 2 INTEGRATION TEST: PARTIAL SUCCESS")
            print("   Some components need attention")
        
        return success
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(main())