#!/usr/bin/env python3
"""
Simple Vector Test for RAG System
Converts a sentence to vector and finds the most relevant chunk
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

def load_chunks_from_database(db_path='production_rag_output/class9_science_simple.db'):
    """Load all chunks from the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT chunk_id, content, chapter_title, subject_area, 
               chapter_number, quality_score, metadata
        FROM processed_chunks
    ''')
    
    chunks = []
    for row in cursor.fetchall():
        chunk_id, content, chapter_title, subject_area, chapter_number, quality_score, metadata_str = row
        
        try:
            metadata = json.loads(metadata_str) if metadata_str else {}
        except:
            metadata = {}
            
        chunks.append({
            'chunk_id': chunk_id,
            'content': content,
            'chapter_title': chapter_title,
            'subject_area': subject_area,
            'chapter_number': chapter_number,
            'quality_score': quality_score,
            'metadata': metadata
        })
    
    conn.close()
    return chunks

def find_most_similar_chunk(query_sentence, chunks, embedding_engine):
    """Find the most similar chunk to the query sentence"""
    
    # Generate embedding for query sentence
    print(f"🔄 Converting sentence to vector...")
    query_embedding = embedding_engine.generate_embedding(query_sentence)
    
    if query_embedding is None:
        return None, None, None
    
    # Generate embeddings for all chunks
    print(f"🔍 Searching through {len(chunks)} chunks...")
    
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

def save_results_to_file(query_sentence, query_vector, best_chunk, similarity, output_file='vector_test_result.txt'):
    """Save the test results to a file"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("🔍 VECTOR SEARCH TEST RESULTS\n")
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
            
            # Best matching chunk
            f.write("📚 MOST RELEVANT CHUNK:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Chapter: {best_chunk['chapter_title']} (Chapter {best_chunk['chapter_number']})\n")
            f.write(f"Subject: {best_chunk['subject_area']}\n")
            f.write(f"Quality Score: {best_chunk['quality_score']:.2f}/1.00\n")
            f.write(f"Chunk ID: {best_chunk['chunk_id']}\n\n")
            
            f.write("CONTENT:\n")
            f.write("-" * 40 + "\n")
            f.write(best_chunk['content'][:1000])  # First 1000 characters
            if len(best_chunk['content']) > 1000:
                f.write("\n\n[... content truncated, showing first 1000 characters ...]")
            f.write("\n\n")
            
            # Metadata
            f.write("METADATA:\n")
            f.write("-" * 40 + "\n")
            metadata = best_chunk['metadata']
            if metadata:
                # Show key metadata fields
                if 'concepts_and_skills' in metadata:
                    concepts = metadata['concepts_and_skills'].get('main_concepts', [])
                    f.write(f"Main Concepts: {', '.join(concepts[:5])}\n")
                
                if 'pedagogical_elements' in metadata:
                    learning_objectives = metadata['pedagogical_elements'].get('learning_objectives', [])
                    if learning_objectives:
                        f.write(f"Learning Objectives: {learning_objectives[0] if learning_objectives else 'N/A'}\n")
                
                if 'type' in metadata:
                    f.write(f"Content Type: {metadata['type']}\n")
            else:
                f.write("No additional metadata available\n")
        else:
            f.write("\n❌ No matching chunk found!\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("Test completed successfully!\n")
    
    print(f"\n✅ Results saved to: {output_file}")

def main():
    """Main function"""
    print("🚀 Simple Vector Test for RAG System")
    print("=" * 50)
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("Please set it using: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Get input sentence
    if len(sys.argv) > 1:
        # Use command line argument
        query_sentence = ' '.join(sys.argv[1:])
    else:
        # Use default test sentence
        query_sentence = "What are the three states of matter and how do particles behave in each state?"
        print(f"ℹ️ No sentence provided, using default: '{query_sentence}'")
    
    print(f"\n📝 Input sentence: '{query_sentence}'")
    
    try:
        # Initialize embedding engine
        print("\n🔧 Initializing embedding engine...")
        embedding_engine = VectorEmbeddingEngine()
        
        if not embedding_engine.is_available():
            print("❌ Embedding engine not available!")
            return
        
        print(f"✅ Using {embedding_engine.config['embedding_model']} embeddings")
        
        # Load chunks from database
        print("\n📚 Loading chunks from database...")
        chunks = load_chunks_from_database()
        print(f"✅ Loaded {len(chunks)} chunks")
        
        # Find most similar chunk
        best_chunk, similarity, query_vector = find_most_similar_chunk(query_sentence, chunks, embedding_engine)
        
        if best_chunk:
            print(f"\n🎯 Found best match with {similarity:.1%} similarity!")
            print(f"📖 From: {best_chunk['chapter_title']}")
            
            # Save results
            save_results_to_file(query_sentence, query_vector, best_chunk, similarity)
            
            # Also display brief summary
            print(f"\n📄 Brief preview of matched content:")
            print("-" * 50)
            print(best_chunk['content'][:200] + "...")
            
        else:
            print("\n❌ No matching chunk found!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()