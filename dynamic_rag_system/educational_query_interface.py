#!/usr/bin/env python3
"""
Educational Query Interface for NCERT Class 9 Science RAG System
Provides intelligent query processing and response generation
"""

import os
import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from embeddings.vector_embedding_engine import VectorEmbeddingEngine, find_semantically_similar_content

class EducationalQueryInterface:
    """
    Intelligent query interface for educational content retrieval
    """
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or 'production_rag_output/class9_science_simple.db'
        self.embedding_engine = VectorEmbeddingEngine()
        
        # Verify database exists
        if not os.path.exists(self.database_path):
            raise FileNotFoundError(f"Database not found: {self.database_path}")
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Retrieve all processed chunks from database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT chunk_id, filename, chapter_title, content, chunk_type, 
                   quality_score, subject_area, chapter_number, metadata
            FROM processed_chunks
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        chunks = []
        for row in results:
            chunk_id, filename, chapter_title, content, chunk_type, quality_score, subject_area, chapter_number, metadata_str = row
            
            try:
                metadata = json.loads(metadata_str) if metadata_str else {}
            except:
                metadata = {}
            
            chunks.append({
                'chunk_id': chunk_id,
                'filename': filename,
                'chapter_title': chapter_title,
                'content': content,
                'chunk_type': chunk_type,
                'quality_score': quality_score,
                'subject_area': subject_area,
                'chapter_number': chapter_number,
                'metadata': metadata
            })
        
        return chunks
    
    def search_similar_content(self, query: str, top_k: int = 5, min_quality: float = 0.5) -> List[Dict]:
        """Search for content similar to the query"""
        if not self.embedding_engine.is_available():
            return []
        
        # Get all chunks
        all_chunks = self.get_all_chunks()
        
        # Filter by quality
        quality_chunks = [chunk for chunk in all_chunks if chunk['quality_score'] >= min_quality]
        
        # Find similar content using embeddings
        matches = find_semantically_similar_content(
            query, quality_chunks, top_k=top_k, embedding_engine=self.embedding_engine
        )
        
        # Enhance matches with database information
        enhanced_matches = []
        for match in matches:
            # Find the original chunk data
            original_chunk = next((c for c in quality_chunks if c['chunk_id'] == match.chunk_id), None)
            
            if original_chunk:
                enhanced_match = {
                    'chunk_id': match.chunk_id,
                    'similarity_score': match.similarity_score,
                    'quality_score': match.metadata.get('quality_score', 0),
                    'content': match.content_preview,
                    'full_content': original_chunk['content'],
                    'chapter_title': original_chunk['chapter_title'],
                    'subject_area': original_chunk['subject_area'],
                    'chapter_number': original_chunk['chapter_number'],
                    'chunk_type': match.chunk_type,
                    'concepts': match.concepts,
                    'filename': original_chunk['filename']
                }
                enhanced_matches.append(enhanced_match)
        
        return enhanced_matches
    
    def format_educational_response(self, query: str, matches: List[Dict]) -> str:
        """Format matches into a comprehensive educational response"""
        if not matches:
            return f"I couldn't find specific information about '{query}' in the NCERT Class 9 Science textbook. Please try rephrasing your question or ask about a different topic."
        
        response = f"# 📚 Educational Response: {query}\n\n"
        
        # Group matches by subject area
        by_subject = {}
        for match in matches:
            subject = match['subject_area']
            if subject not in by_subject:
                by_subject[subject] = []
            by_subject[subject].append(match)
        
        for subject, subject_matches in by_subject.items():
            response += f"## 🧪 From {subject}:\n\n"
            
            for i, match in enumerate(subject_matches):
                response += f"### {i+1}. {match['chapter_title']} (Chapter {match['chapter_number']})\n"
                response += f"**Relevance:** {match['similarity_score']:.1%} | **Quality:** {match['quality_score']:.2f}/1.00\n\n"
                
                # Show key concepts if available
                if match['concepts']:
                    response += f"**Key Concepts:** {', '.join(match['concepts'][:3])}\n\n"
                
                # Show content preview
                content_preview = match['content'][:500].strip()
                if len(match['full_content']) > 500:
                    content_preview += "..."
                
                response += f"{content_preview}\n\n"
                response += f"*Source: {match['filename']}*\n\n"
                response += "---\n\n"
        
        return response
    
    def answer_educational_query(self, query: str, top_k: int = 3, min_quality: float = 0.5) -> Dict[str, Any]:
        """Answer an educational query with comprehensive information"""
        print(f"🔍 Processing query: '{query}'")
        
        # Search for similar content
        matches = self.search_similar_content(query, top_k=top_k, min_quality=min_quality)
        
        if not matches:
            return {
                'query': query,
                'response': f"No relevant content found for '{query}'",
                'matches': [],
                'confidence': 0.0
            }
        
        # Format response
        formatted_response = self.format_educational_response(query, matches)
        
        # Calculate average confidence
        avg_confidence = sum(m['similarity_score'] for m in matches) / len(matches)
        
        return {
            'query': query,
            'response': formatted_response,
            'matches': matches,
            'confidence': avg_confidence,
            'sources': [f"Chapter {m['chapter_number']}: {m['chapter_title']}" for m in matches]
        }
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """Get statistics about the available content"""
        all_chunks = self.get_all_chunks()
        
        if not all_chunks:
            return {}
        
        # Subject distribution
        subjects = {}
        for chunk in all_chunks:
            subject = chunk['subject_area']
            subjects[subject] = subjects.get(subject, 0) + 1
        
        # Chapter distribution  
        chapters = {}
        for chunk in all_chunks:
            chapter = f"Chapter {chunk['chapter_number']}: {chunk['chapter_title']}"
            chapters[chapter] = chapters.get(chapter, 0) + 1
        
        # Quality distribution
        quality_scores = [chunk['quality_score'] for chunk in all_chunks]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        excellent = sum(1 for q in quality_scores if q >= 0.8)
        good = sum(1 for q in quality_scores if 0.6 <= q < 0.8)
        fair = sum(1 for q in quality_scores if 0.4 <= q < 0.6)
        poor = sum(1 for q in quality_scores if q < 0.4)
        
        return {
            'total_chunks': len(all_chunks),
            'average_quality': avg_quality,
            'quality_distribution': {
                'excellent': excellent,
                'good': good, 
                'fair': fair,
                'poor': poor
            },
            'subject_distribution': subjects,
            'chapter_distribution': chapters,
            'embedding_available': self.embedding_engine.is_available()
        }

def run_interactive_session():
    """Run interactive query session"""
    try:
        interface = EducationalQueryInterface()
        
        print("🚀 NCERT Class 9 Science - Educational RAG Query Interface")
        print("=" * 60)
        
        # Show content statistics
        stats = interface.get_content_statistics()
        print(f"📚 Available Content: {stats['total_chunks']} chunks")
        print(f"⭐ Average Quality: {stats['average_quality']:.2f}/1.00")
        print(f"🧠 Embeddings: {'✅ Available' if stats['embedding_available'] else '❌ Not Available'}")
        print()
        
        # Show subject distribution
        print("📊 Subject Distribution:")
        for subject, count in stats['subject_distribution'].items():
            print(f"  • {subject}: {count} chunks")
        print()
        
        print("💡 Ask questions about NCERT Class 9 Science topics!")
        print("   Examples: 'What is matter?', 'How do atoms combine?', 'Explain states of matter'")
        print("   Type 'quit' to exit\n")
        
        while True:
            query = input("🤔 Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Thank you for using the Educational RAG system!")
                break
            
            if not query:
                continue
            
            try:
                result = interface.answer_educational_query(query, top_k=3)
                
                print(f"\n📋 Response (Confidence: {result['confidence']:.1%}):")
                print("=" * 50)
                print(result['response'])
                
                print("📚 Sources:")
                for source in result['sources']:
                    print(f"  • {source}")
                print("\n" + "="*60 + "\n")
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                print()
    
    except Exception as e:
        print(f"❌ Failed to initialize query interface: {e}")

def run_test_queries():
    """Run a set of test queries to demonstrate the system"""
    try:
        interface = EducationalQueryInterface()
        
        print("🧪 Testing Educational RAG System with Sample Queries")
        print("=" * 60)
        
        # Test queries covering different topics
        test_queries = [
            "What is matter and what are its properties?",
            "How do atoms combine to form molecules?",
            "What are the different states of matter?",
            "Explain the concept of evaporation",
            "What is the difference between pure substances and mixtures?",
            "How do you write chemical formulas?",
            "What are the characteristics of particles of matter?"
        ]
        
        results = []
        
        for i, query in enumerate(test_queries):
            print(f"\n🔍 Test Query {i+1}: {query}")
            print("-" * 50)
            
            result = interface.answer_educational_query(query, top_k=2)
            results.append(result)
            
            if result['matches']:
                print(f"✅ Found {len(result['matches'])} relevant matches")
                print(f"📊 Average Confidence: {result['confidence']:.1%}")
                
                for j, match in enumerate(result['matches']):
                    print(f"  {j+1}. {match['chapter_title']} (Relevance: {match['similarity_score']:.1%})")
            else:
                print("❌ No relevant matches found")
        
        # Summary
        print(f"\n{'='*30} TEST SUMMARY {'='*30}")
        successful_queries = sum(1 for r in results if r['matches'])
        avg_confidence = sum(r['confidence'] for r in results if r['matches']) / max(successful_queries, 1)
        
        print(f"📊 Successful Queries: {successful_queries}/{len(test_queries)}")
        print(f"⭐ Average Confidence: {avg_confidence:.1%}")
        print(f"🎯 System Performance: {'Excellent' if avg_confidence > 0.6 else 'Good' if avg_confidence > 0.4 else 'Needs Improvement'}")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return []

async def main():
    """Main function"""
    print("🚀 Educational Query Interface - NCERT Class 9 Science")
    print("Choose an option:")
    print("1. Run interactive query session")
    print("2. Run automated test queries")
    print("3. View content statistics only")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        run_interactive_session()
    elif choice == '2':
        run_test_queries()
    elif choice == '3':
        try:
            interface = EducationalQueryInterface()
            stats = interface.get_content_statistics()
            
            print("\n📊 Content Statistics:")
            print(f"Total Chunks: {stats['total_chunks']}")
            print(f"Average Quality: {stats['average_quality']:.2f}/1.00")
            print(f"Embeddings Available: {stats['embedding_available']}")
            
            print("\nSubject Distribution:")
            for subject, count in stats['subject_distribution'].items():
                print(f"  {subject}: {count} chunks")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())