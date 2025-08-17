#!/usr/bin/env python3
"""
Semantic Chunking Quality Test - 10 Comprehensive Questions
Tests semantic understanding, content separation, and educational coherence
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
from semantic_chunker import SemanticEducationalChunker, ChunkType

def create_semantic_chunking_questions():
    """
    Create 10 comprehensive questions to test semantic chunking quality
    Each question tests different aspects of semantic understanding and content separation
    """
    return [
        {
            'id': 'SEMANTIC_Q1',
            'question': 'How does the semantic chunker separate activities from explanations in educational content?',
            'concepts': ['semantic separation', 'activity detection', 'content classification', 'educational structure'],
            'expected_chunk_types': [ChunkType.ACTIVITY, ChunkType.CONTENT],
            'difficulty': 'advanced',
            'type': 'system_understanding',
            'learning_objectives': ['understand semantic chunking', 'identify content types'],
            'semantic_aspects': ['content_type_detection', 'boundary_identification', 'educational_structure']
        },
        {
            'id': 'SEMANTIC_Q2', 
            'question': 'What happens when a single paragraph contains both an example and an explanation?',
            'concepts': ['mixed_content', 'example_extraction', 'explanation_separation', 'content_boundaries'],
            'expected_chunk_types': [ChunkType.EXAMPLE, ChunkType.CONTENT],
            'difficulty': 'intermediate',
            'type': 'boundary_testing',
            'learning_objectives': ['handle mixed content', 'maintain semantic coherence'],
            'semantic_aspects': ['content_separation', 'semantic_coherence', 'boundary_detection']
        },
        {
            'id': 'SEMANTIC_Q3',
            'question': 'How does the system maintain relationships between related concepts across different chunks?',
            'concepts': ['concept_relationships', 'cross_chunk_connections', 'semantic_links', 'knowledge_graph'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.EXAMPLE],
            'difficulty': 'advanced',
            'type': 'relationship_mapping',
            'learning_objectives': ['understand concept relationships', 'maintain knowledge continuity'],
            'semantic_aspects': ['relationship_mapping', 'concept_linking', 'semantic_continuity']
        },
        {
            'id': 'SEMANTIC_Q4',
            'question': 'Can the chunker identify when an activity demonstrates a specific concept?',
            'concepts': ['activity_concept_mapping', 'demonstration_identification', 'practical_application'],
            'expected_chunk_types': [ChunkType.ACTIVITY],
            'difficulty': 'intermediate',
            'type': 'concept_demonstration',
            'learning_objectives': ['link activities to concepts', 'identify practical demonstrations'],
            'semantic_aspects': ['concept_detection', 'activity_analysis', 'demonstration_mapping']
        },
        {
            'id': 'SEMANTIC_Q5',
            'question': 'How does the system handle questions that require understanding from multiple chunks?',
            'concepts': ['multi_chunk_queries', 'cross_reference_handling', 'comprehensive_understanding'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.EXAMPLE, ChunkType.ACTIVITY],
            'difficulty': 'advanced',
            'type': 'multi_chunk_integration',
            'learning_objectives': ['integrate information across chunks', 'build comprehensive understanding'],
            'semantic_aspects': ['cross_chunk_retrieval', 'information_integration', 'comprehensive_answers']
        },
        {
            'id': 'SEMANTIC_Q6',
            'question': 'What happens when content has ambiguous boundaries between different educational elements?',
            'concepts': ['ambiguous_boundaries', 'content_disambiguation', 'semantic_clarity'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.SPECIAL_BOX],
            'difficulty': 'intermediate',
            'type': 'boundary_ambiguity',
            'learning_objectives': ['handle ambiguous content', 'maintain semantic clarity'],
            'semantic_aspects': ['ambiguity_resolution', 'boundary_clarification', 'semantic_precision']
        },
        {
            'id': 'SEMANTIC_Q7',
            'question': 'How does the chunker preserve the educational flow and sequence of learning?',
            'concepts': ['educational_sequence', 'learning_progression', 'pedagogical_flow'],
            'expected_chunk_types': [ChunkType.INTRO, ChunkType.CONTENT, ChunkType.SUMMARY],
            'difficulty': 'intermediate',
            'type': 'pedagogical_structure',
            'learning_objectives': ['maintain learning sequence', 'preserve educational flow'],
            'semantic_aspects': ['sequence_preservation', 'pedagogical_structure', 'learning_progression']
        },
        {
            'id': 'SEMANTIC_Q8',
            'question': 'Can the system identify when content builds upon previously introduced concepts?',
            'concepts': ['prerequisite_detection', 'concept_building', 'knowledge_dependencies'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.EXAMPLE],
            'difficulty': 'advanced',
            'type': 'prerequisite_mapping',
            'learning_objectives': ['identify concept dependencies', 'map knowledge building'],
            'semantic_aspects': ['prerequisite_analysis', 'dependency_mapping', 'concept_relationships']
        },
        {
            'id': 'SEMANTIC_Q9',
            'question': 'How does the chunker handle content that contains both theoretical and practical elements?',
            'concepts': ['theoretical_practical_mix', 'content_hybridization', 'dual_nature_content'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.ACTIVITY],
            'difficulty': 'intermediate',
            'type': 'hybrid_content',
            'learning_objectives': ['separate theoretical from practical', 'maintain content integrity'],
            'semantic_aspects': ['content_hybridization', 'theoretical_practical_separation', 'content_integrity']
        },
        {
            'id': 'SEMANTIC_Q10',
            'question': 'What happens when the same concept is explained in multiple ways across different chunks?',
            'concepts': ['concept_redundancy', 'multiple_explanations', 'semantic_consistency'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.EXAMPLE, ChunkType.ACTIVITY],
            'difficulty': 'advanced',
            'type': 'concept_redundancy',
            'learning_objectives': ['handle concept redundancy', 'maintain semantic consistency'],
            'semantic_aspects': ['redundancy_detection', 'consistency_maintenance', 'concept_unification']
        }
    ]

def calculate_semantic_relevance(chunk, question: Dict[str, Any]) -> float:
    """
    Calculate semantic relevance score for a chunk against a question
    Considers chunk type, concepts, and semantic aspects
    """
    relevance_score = 0.0
    
    # Check chunk type match
    expected_types = question.get('expected_chunk_types', [])
    if hasattr(chunk, 'chunk_type') and chunk.chunk_type in expected_types:
        relevance_score += 2.0
    
    # Check concept matches
    question_concepts = question.get('concepts', [])
    chunk_concepts = []
    
    # Extract concepts from chunk metadata
    if hasattr(chunk, 'metadata'):
        concepts_data = chunk.metadata.get('concepts_and_skills', {})
        chunk_concepts.extend(concepts_data.get('main_concepts', []))
        chunk_concepts.extend(concepts_data.get('keywords', []))
    
    # Calculate concept overlap
    for q_concept in question_concepts:
        for c_concept in chunk_concepts:
            if q_concept.lower() in c_concept.lower() or c_concept.lower() in q_concept.lower():
                relevance_score += 1.0
    
    # Check semantic aspects
    semantic_aspects = question.get('semantic_aspects', [])
    content_lower = chunk.content.lower()
    
    for aspect in semantic_aspects:
        if aspect.replace('_', ' ') in content_lower:
            relevance_score += 0.5
    
    # Check content quality
    if hasattr(chunk, 'quality_score'):
        quality_score = chunk.quality_score
        if isinstance(quality_score, dict):
            # If quality_score is a dict, use a default value or extract a specific field
            relevance_score += 0.5  # Default quality contribution
        else:
            relevance_score += quality_score * 0.5
    
    return relevance_score

def test_semantic_chunking_quality():
    """
    Run comprehensive semantic chunking quality test
    """
    print("🧠 SEMANTIC CHUNKING QUALITY TEST")
    print("=" * 70)
    
    # Test with sample educational content
    sample_content = """
    11.1 Production of Sound
    
    Sound is produced by vibrating objects. When an object vibrates, it causes the air around it to vibrate, creating sound waves.
    
    Activity 11.1
    Take a tuning fork and strike it gently against a rubber pad. Hold it near your ear. You will hear a sound. Now touch the tuning fork to a glass of water. You will see ripples in the water. This shows that the tuning fork is vibrating.
    
    Example 11.1
    A guitar string when plucked vibrates and produces sound. The frequency of vibration determines the pitch of the sound.
    
    What you have learnt
    • Sound is produced by vibrating objects
    • The frequency of vibration affects the pitch
    • Sound travels through different media
    
    Questions
    1. How is sound produced?
    2. Give examples of vibrating objects that produce sound.
    """
    
    print("📖 Processing sample educational content...")
    
    # Create semantic chunker
    semantic_chunker = SemanticEducationalChunker()
    
    try:
        # Create semantic chunks
        chunks, relationships = semantic_chunker.create_semantic_chunks(sample_content)
        print(f"✅ Created {len(chunks)} semantic chunks")
        print(f"✅ Created {len(relationships)} relationships")
        
        # Create test questions
        questions = create_semantic_chunking_questions()
        
        # Test each question
        print(f"\n❓ Testing 10 Semantic Chunking Questions...")
        print("=" * 70)
        
        results = []
        total_semantic_score = 0
        
        for question in questions:
            print(f"\n🔍 {question['id']}: {question['question']}")
            print(f"   Type: {question['type']}, Difficulty: {question['difficulty']}")
            print(f"   Expected Chunk Types: {[t.value for t in question['expected_chunk_types']]}")
            print(f"   Semantic Aspects: {', '.join(question['semantic_aspects'])}")
            
            # Find relevant chunks
            relevant_chunks = []
            
            for chunk in chunks:
                relevance_score = calculate_semantic_relevance(chunk, question)
                
                if relevance_score > 0:
                    relevant_chunks.append({
                        'chunk': chunk,
                        'score': relevance_score,
                        'chunk_type': chunk.chunk_type.value if hasattr(chunk, 'chunk_type') else 'unknown',
                        'content_preview': chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
                    })
            
            # Sort by relevance score
            relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
            
            # Take top 3 results
            top_results = relevant_chunks[:3]
            
            result = {
                'question': question,
                'total_relevant': len(relevant_chunks),
                'top_results': top_results,
                'max_score': max([r['score'] for r in relevant_chunks]) if relevant_chunks else 0
            }
            
            results.append(result)
            total_semantic_score += result['max_score']
            
            # Print results
            if top_results:
                print(f"   📊 Found {len(relevant_chunks)} relevant chunks")
                print(f"   🏆 Top 3 Results:")
                
                for i, chunk_info in enumerate(top_results):
                    chunk = chunk_info['chunk']
                    print(f"      {i+1}. Score: {chunk_info['score']:.2f}, Type: {chunk_info['chunk_type']}")
                    print(f"         Preview: {chunk_info['content_preview']}")
                    print()
            else:
                print(f"   ❌ No relevant chunks found")
        
        # Analyze results
        print(f"\n📈 SEMANTIC CHUNKING QUALITY ANALYSIS")
        print("=" * 70)
        
        avg_semantic_score = total_semantic_score / len(questions)
        questions_with_matches = sum(1 for r in results if r['total_relevant'] > 0)
        
        print(f"📊 Overall Results:")
        print(f"   • Questions with matches: {questions_with_matches}/{len(questions)} ({questions_with_matches/len(questions)*100:.1f}%)")
        print(f"   • Average semantic score: {avg_semantic_score:.2f}")
        print(f"   • Total relationships created: {len(relationships)}")
        
        # Quality assessment
        if avg_semantic_score >= 3.0:
            quality_grade = "A+ (Excellent)"
        elif avg_semantic_score >= 2.5:
            quality_grade = "A (Very Good)"
        elif avg_semantic_score >= 2.0:
            quality_grade = "B (Good)"
        elif avg_semantic_score >= 1.5:
            quality_grade = "C (Fair)"
        else:
            quality_grade = "D (Poor)"
        
        print(f"   • Semantic Quality Grade: {quality_grade}")
        
        # Detailed analysis by question type
        print(f"\n📋 Analysis by Question Type:")
        type_analysis = {}
        
        for result in results:
            q_type = result['question']['type']
            if q_type not in type_analysis:
                type_analysis[q_type] = {'count': 0, 'total_score': 0}
            
            type_analysis[q_type]['count'] += 1
            type_analysis[q_type]['total_score'] += result['max_score']
        
        for q_type, data in type_analysis.items():
            avg_score = data['total_score'] / data['count']
            print(f"   • {q_type}: {avg_score:.2f} avg score ({data['count']} questions)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("=" * 70)
        
        if avg_semantic_score < 2.0:
            print("⚠️  SEMANTIC CHUNKING NEEDS IMPROVEMENT:")
            print("   • Enhance concept detection algorithms")
            print("   • Improve content type classification")
            print("   • Strengthen relationship mapping")
        elif avg_semantic_score < 2.5:
            print("✅  GOOD SEMANTIC CHUNKING WITH ROOM FOR IMPROVEMENT:")
            print("   • Fine-tune concept extraction")
            print("   • Optimize boundary detection")
            print("   • Enhance cross-chunk relationships")
        else:
            print("🏆  EXCELLENT SEMANTIC CHUNKING QUALITY:")
            print("   • System demonstrates strong semantic understanding")
            print("   • Content separation is working effectively")
            print("   • Relationships are being properly mapped")
        
        return {
            'overall_score': avg_semantic_score,
            'quality_grade': quality_grade,
            'questions_tested': len(questions),
            'questions_with_matches': questions_with_matches,
            'relationships_created': len(relationships),
            'detailed_results': results
        }
        
    except Exception as e:
        print(f"❌ Error during semantic chunking test: {e}")
        return None

def save_semantic_test_results(results: Dict[str, Any]):
    """Save semantic test results to file"""
    if not results:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"semantic_chunking_test_results_{timestamp}.json"
    
    # Convert results to serializable format
    serializable_results = {
        'test_date': datetime.now().isoformat(),
        'overall_score': results['overall_score'],
        'quality_grade': results['quality_grade'],
        'questions_tested': results['questions_tested'],
        'questions_with_matches': results['questions_with_matches'],
        'relationships_created': results['relationships_created'],
        'detailed_results': []
    }
    
    for result in results['detailed_results']:
        serializable_result = {
            'question_id': result['question']['id'],
            'question_text': result['question']['question'],
            'question_type': result['question']['type'],
            'difficulty': result['question']['difficulty'],
            'total_relevant_chunks': result['total_relevant'],
            'max_score': result['max_score'],
            'top_results': []
        }
        
        for chunk_info in result['top_results']:
            serializable_result['top_results'].append({
                'score': chunk_info['score'],
                'chunk_type': chunk_info['chunk_type'],
                'content_preview': chunk_info['content_preview']
            })
        
        serializable_results['detailed_results'].append(serializable_result)
    
    with open(filename, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"💾 Results saved to: {filename}")

if __name__ == "__main__":
    # Run semantic chunking quality test
    results = test_semantic_chunking_quality()
    
    if results:
        # Save results
        save_semantic_test_results(results)
        
        print(f"\n🎯 SEMANTIC CHUNKING QUALITY TEST COMPLETED")
        print(f"   Overall Score: {results['overall_score']:.2f}")
        print(f"   Quality Grade: {results['quality_grade']}")
        print(f"   Success Rate: {results['questions_with_matches']}/{results['questions_tested']}")
    else:
        print("❌ Semantic chunking quality test failed")
