#!/usr/bin/env python3
"""
Semantic Vector Test - Test retrieval with semantically separated chunks
"""

import os
import sys
import json
import sqlite3
import numpy as np
from datetime import datetime
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from embeddings.vector_embedding_engine import VectorEmbeddingEngine

def load_semantic_chunks_from_database(db_path='production_rag_output/class9_science_semantic.db'):
    """Load semantic chunks from the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT chunk_id, chunk_type, content, chapter_title, 
               mother_section, mother_section_title, confidence,
               estimated_duration, difficulty_level, concepts
        FROM semantic_chunks
        ORDER BY chapter_number, sequence_in_section
    ''')
    
    chunks = []
    for row in cursor.fetchall():
        chunk_id, chunk_type, content, chapter_title, mother_section, mother_section_title, confidence, estimated_duration, difficulty_level, concepts_str = row
        
        try:
            concepts = json.loads(concepts_str) if concepts_str else []
        except:
            concepts = []
            
        chunks.append({
            'chunk_id': chunk_id,
            'chunk_type': chunk_type,
            'content': content,
            'chapter_title': chapter_title,
            'mother_section': mother_section,
            'mother_section_title': mother_section_title,
            'confidence': confidence,
            'estimated_duration': estimated_duration,
            'difficulty_level': difficulty_level,
            'concepts': concepts
        })
    
    conn.close()
    return chunks

def find_most_similar_semantic_chunk(query_sentence, chunks, embedding_engine):
    """Find the most similar semantic chunk to the query sentence"""
    
    print(f"🔄 Converting sentence to vector...")
    query_embedding = embedding_engine.generate_embedding(query_sentence)
    
    if query_embedding is None:
        return None, None, None
    
    print(f"🔍 Searching through {len(chunks)} semantic chunks...")
    
    best_chunk = None
    best_similarity = -1
    best_embedding = None
    
    for chunk in chunks:
        # Generate embedding for chunk
        chunk_embedding = embedding_engine.generate_embedding(chunk['content'])
        
        if chunk_embedding is not None:
            # Calculate similarity
            similarity = embedding_engine.compute_similarity(query_embedding, chunk_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_chunk = chunk
                best_embedding = chunk_embedding
    
    return best_chunk, best_similarity, query_embedding

def save_semantic_results_to_file(query_sentence, query_vector, best_chunk, similarity, output_file='semantic_vector_test_result.txt'):
    """Save the test results to a file"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("🔍 SEMANTIC VECTOR SEARCH TEST RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Input sentence
        f.write("📝 INPUT SENTENCE:\n")
        f.write("-" * 40 + "\n")
        f.write(f"{query_sentence}\n\n")
        
        # Vector representation (show first 10 values)
        f.write("🔢 VECTOR REPRESENTATION:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Dimensions: {len(query_vector)}\n")
        f.write(f"First 10 values: {query_vector[:10].tolist()}\n")
        f.write(f"Vector statistics:\n")
        f.write(f"  - Mean: {np.mean(query_vector):.6f}\n")
        f.write(f"  - Std Dev: {np.std(query_vector):.6f}\n")
        f.write(f"  - Min: {np.min(query_vector):.6f}\n")
        f.write(f"  - Max: {np.max(query_vector):.6f}\n\n")
        
        if best_chunk:
            # Similarity score
            f.write("📊 SIMILARITY SCORE:\n")
            f.write("-" * 40 + "\n")
            f.write(f"{similarity:.1%} match\n\n")
            
            # Best matching chunk with semantic details
            f.write("📚 MOST RELEVANT SEMANTIC CHUNK:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Chapter: {best_chunk['chapter_title']}\n")
            f.write(f"Section: {best_chunk['mother_section']} - {best_chunk['mother_section_title']}\n")
            f.write(f"Content Type: {best_chunk['chunk_type']} 🎯\n")
            f.write(f"Confidence: {best_chunk['confidence']:.2f}/1.00\n")
            f.write(f"Estimated Duration: {best_chunk['estimated_duration']} minutes\n")
            f.write(f"Difficulty: {best_chunk['difficulty_level']}\n")
            f.write(f"Chunk ID: {best_chunk['chunk_id']}\n\n")
            
            # Concepts
            if best_chunk['concepts']:
                f.write("KEY CONCEPTS:\n")
                f.write("-" * 40 + "\n")
                for concept in best_chunk['concepts'][:5]:
                    f.write(f"• {concept}\n")
                f.write("\n")
            
            f.write("CONTENT:\n")
            f.write("-" * 40 + "\n")
            content = best_chunk['content']
            f.write(content[:1500])  # First 1500 characters
            if len(content) > 1500:
                f.write("\n\n[... content truncated, showing first 1500 characters ...]")
            f.write("\n\n")
            
        else:
            f.write("\n❌ No matching semantic chunk found!\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("✅ Semantic test completed successfully!\n")
    
    print(f"\n✅ Results saved to: {output_file}")

def compare_with_original(query_sentence, embedding_engine):
    """Compare semantic results with original chunking"""
    print("\n🔄 Loading original chunks for comparison...")
    
    # Load original chunks
    conn = sqlite3.connect('production_rag_output/class9_science_simple.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chunk_id, content, chapter_title FROM processed_chunks')
    original_chunks = [{'chunk_id': row[0], 'content': row[1], 'chapter_title': row[2]} for row in cursor.fetchall()]
    conn.close()
    
    # Find best original chunk
    original_best, original_similarity, _ = find_most_similar_semantic_chunk(query_sentence, original_chunks, embedding_engine)
    
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"Original chunking best match: {original_similarity:.1%} similarity")
    
    return original_best, original_similarity

def main():
    """Main function"""
    print("🚀 Semantic Vector Test for Enhanced RAG System")
    print("=" * 60)
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("Please set it using: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Get input sentence
    if len(sys.argv) > 1:
        query_sentence = ' '.join(sys.argv[1:])
    else:
        query_sentence = "Can matter change its state?"
        print(f"ℹ️ No sentence provided, using test query: '{query_sentence}'")
    
    print(f"\n📝 Input sentence: '{query_sentence}'")
    
    try:
        # Initialize embedding engine
        print("\n🔧 Initializing embedding engine...")
        embedding_engine = VectorEmbeddingEngine()
        
        if not embedding_engine.is_available():
            print("❌ Embedding engine not available!")
            return
        
        print(f"✅ Using {embedding_engine.config['embedding_model']} embeddings")
        
        # Load semantic chunks
        print("\n📚 Loading semantic chunks from database...")
        semantic_chunks = load_semantic_chunks_from_database()
        print(f"✅ Loaded {len(semantic_chunks)} semantic chunks")
        
        # Print chunk distribution
        chunk_types = {}
        for chunk in semantic_chunks:
            chunk_type = chunk['chunk_type']
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        print(f"📊 Chunk distribution:")
        for chunk_type, count in sorted(chunk_types.items()):
            print(f"   {chunk_type}: {count} chunks")
        
        # Find most similar semantic chunk
        best_chunk, similarity, query_vector = find_most_similar_semantic_chunk(query_sentence, semantic_chunks, embedding_engine)
        
        if best_chunk:
            print(f"\n🎯 Found best semantic match with {similarity:.1%} similarity!")
            print(f"📖 From: {best_chunk['chapter_title']}")
            print(f"🎭 Type: {best_chunk['chunk_type']}")
            print(f"📍 Section: {best_chunk['mother_section']} - {best_chunk['mother_section_title']}")
            print(f"⏱️ Duration: {best_chunk['estimated_duration']} minutes")
            print(f"📊 Difficulty: {best_chunk['difficulty_level']}")
            
            # Save results
            save_semantic_results_to_file(query_sentence, query_vector, best_chunk, similarity)
            
            # Brief preview
            print(f"\n📄 Brief preview of matched content:")
            print("-" * 60)
            print(best_chunk['content'][:300] + "...")
            
            # Compare with original
            original_best, original_similarity = compare_with_original(query_sentence, embedding_engine)
            semantic_improvement = ((similarity - original_similarity) / original_similarity) * 100
            
            print(f"Semantic chunking best match: {similarity:.1%} similarity")
            if semantic_improvement > 0:
                print(f"🚀 Improvement: +{semantic_improvement:.1f}% better retrieval!")
            else:
                print(f"📊 Difference: {semantic_improvement:.1f}%")
            
        else:
            print("\n❌ No matching semantic chunk found!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()