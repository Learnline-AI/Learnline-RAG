#!/usr/bin/env python3
"""
Enhanced Semantic Chunking Quality Test - Real PDF Content
Tests semantic understanding with actual educational content from PDFs
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
# Simplified PDF text extraction
def extract_text_from_pdf(pdf_path):
    """Simple PDF text extraction for testing"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except ImportError:
        print("PyPDF2 not available, using fallback")
        return None
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

def create_enhanced_semantic_questions():
    """
    Create enhanced semantic questions specifically for real educational content
    """
    return [
        {
            'id': 'REAL_Q1',
            'question': 'How does sound production work through vibrating objects?',
            'concepts': ['sound', 'vibration', 'production', 'objects', 'tuning fork'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.ACTIVITY],
            'difficulty': 'intermediate',
            'type': 'concept_explanation',
            'learning_objectives': ['understand sound production', 'identify vibrating objects'],
            'semantic_aspects': ['concept_explanation', 'practical_demonstration', 'scientific_principle']
        },
        {
            'id': 'REAL_Q2',
            'question': 'What happens when sound waves travel through different media?',
            'concepts': ['sound', 'propagation', 'medium', 'waves', 'travel'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.EXAMPLE],
            'difficulty': 'intermediate',
            'type': 'phenomenon_explanation',
            'learning_objectives': ['understand sound propagation', 'identify different media'],
            'semantic_aspects': ['wave_propagation', 'medium_effects', 'physical_phenomenon']
        },
        {
            'id': 'REAL_Q3',
            'question': 'How do activities demonstrate sound concepts?',
            'concepts': ['activity', 'demonstration', 'sound', 'concepts', 'practical'],
            'expected_chunk_types': [ChunkType.ACTIVITY],
            'difficulty': 'intermediate',
            'type': 'activity_concept_link',
            'learning_objectives': ['link activities to concepts', 'understand practical applications'],
            'semantic_aspects': ['activity_analysis', 'concept_demonstration', 'practical_application']
        },
        {
            'id': 'REAL_Q4',
            'question': 'What are the different types of sound reflection?',
            'concepts': ['sound', 'reflection', 'echo', 'surfaces', 'bounce'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.EXAMPLE],
            'difficulty': 'intermediate',
            'type': 'classification_understanding',
            'learning_objectives': ['classify sound reflection types', 'understand echo formation'],
            'semantic_aspects': ['classification', 'phenomenon_types', 'scientific_categorization']
        },
        {
            'id': 'REAL_Q5',
            'question': 'How does frequency affect sound perception?',
            'concepts': ['frequency', 'sound', 'perception', 'pitch', 'hearing'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.EXAMPLE],
            'difficulty': 'advanced',
            'type': 'relationship_understanding',
            'learning_objectives': ['understand frequency-pitch relationship', 'explain hearing range'],
            'semantic_aspects': ['causal_relationship', 'sensory_perception', 'physical_parameter']
        },
        {
            'id': 'REAL_Q6',
            'question': 'What practical applications use ultrasound technology?',
            'concepts': ['ultrasound', 'applications', 'technology', 'practical', 'medical'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.EXAMPLE, ChunkType.ACTIVITY],
            'difficulty': 'intermediate',
            'type': 'application_understanding',
            'learning_objectives': ['identify ultrasound applications', 'understand technology uses'],
            'semantic_aspects': ['technology_applications', 'practical_uses', 'real_world_examples']
        },
        {
            'id': 'REAL_Q7',
            'question': 'How do examples illustrate sound principles?',
            'concepts': ['examples', 'illustration', 'sound', 'principles', 'demonstration'],
            'expected_chunk_types': [ChunkType.EXAMPLE, ChunkType.CONTENT],
            'difficulty': 'intermediate',
            'type': 'example_analysis',
            'learning_objectives': ['analyze examples', 'understand principle illustration'],
            'semantic_aspects': ['example_analysis', 'principle_illustration', 'concept_demonstration']
        },
        {
            'id': 'REAL_Q8',
            'question': 'What questions test understanding of sound concepts?',
            'concepts': ['questions', 'testing', 'understanding', 'sound', 'concepts'],
            'expected_chunk_types': [ChunkType.EXERCISES],
            'difficulty': 'basic',
            'type': 'assessment_analysis',
            'learning_objectives': ['identify assessment questions', 'understand concept testing'],
            'semantic_aspects': ['assessment_questions', 'concept_testing', 'learning_evaluation']
        },
        {
            'id': 'REAL_Q9',
            'question': 'How do different sections build upon each other in sound learning?',
            'concepts': ['sections', 'building', 'learning', 'progression', 'sound'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.INTRO, ChunkType.SUMMARY],
            'difficulty': 'advanced',
            'type': 'learning_progression',
            'learning_objectives': ['understand learning progression', 'identify concept building'],
            'semantic_aspects': ['learning_sequence', 'concept_progression', 'educational_structure']
        },
        {
            'id': 'REAL_Q10',
            'question': 'What misconceptions might students have about sound?',
            'concepts': ['misconceptions', 'students', 'sound', 'common_errors', 'learning'],
            'expected_chunk_types': [ChunkType.CONTENT, ChunkType.SPECIAL_BOX],
            'difficulty': 'advanced',
            'type': 'misconception_analysis',
            'learning_objectives': ['identify common misconceptions', 'address learning challenges'],
            'semantic_aspects': ['misconception_detection', 'learning_challenges', 'educational_insights']
        }
    ]

def calculate_enhanced_semantic_relevance(chunk, question: Dict[str, Any]) -> float:
    """
    Enhanced semantic relevance calculation for real educational content
    """
    relevance_score = 0.0
    
    # Check chunk type match
    expected_types = question.get('expected_chunk_types', [])
    if hasattr(chunk, 'chunk_type') and chunk.chunk_type in expected_types:
        relevance_score += 2.0
    
    # Check concept matches with enhanced matching
    question_concepts = question.get('concepts', [])
    chunk_concepts = []
    
    # Extract concepts from chunk metadata
    if hasattr(chunk, 'metadata'):
        concepts_data = chunk.metadata.get('concepts_and_skills', {})
        chunk_concepts.extend(concepts_data.get('main_concepts', []))
        chunk_concepts.extend(concepts_data.get('keywords', []))
    
    # Enhanced concept matching
    for q_concept in question_concepts:
        for c_concept in chunk_concepts:
            # Exact match
            if q_concept.lower() == c_concept.lower():
                relevance_score += 2.0
            # Partial match
            elif q_concept.lower() in c_concept.lower() or c_concept.lower() in q_concept.lower():
                relevance_score += 1.0
            # Word similarity
            elif any(word in c_concept.lower() for word in q_concept.lower().split()):
                relevance_score += 0.5
    
    # Check content for concept mentions
    content_lower = chunk.content.lower()
    for concept in question_concepts:
        if concept.lower() in content_lower:
            relevance_score += 0.5
    
    # Check semantic aspects
    semantic_aspects = question.get('semantic_aspects', [])
    for aspect in semantic_aspects:
        aspect_words = aspect.replace('_', ' ').split()
        if any(word in content_lower for word in aspect_words):
            relevance_score += 0.3
    
    # Check content quality
    if hasattr(chunk, 'quality_score'):
        quality_score = chunk.quality_score
        if isinstance(quality_score, dict):
            relevance_score += 0.5
        else:
            relevance_score += quality_score * 0.5
    
    # Bonus for educational content types
    if hasattr(chunk, 'chunk_type'):
        if chunk.chunk_type in [ChunkType.ACTIVITY, ChunkType.EXAMPLE, ChunkType.EXERCISES]:
            relevance_score += 0.3
    
    return relevance_score

def test_with_real_pdf_content():
    """
    Test semantic chunking quality with real PDF content
    """
    print("🧠 ENHANCED SEMANTIC CHUNKING QUALITY TEST")
    print("=" * 70)
    
    # Try to find a real PDF file
    pdf_paths = [
        "/Users/umangagarwal/Downloads/iesc1dd/iesc111.pdf",
        "data/original_files/iesc111.pdf",
        "iesc111.pdf"
    ]
    
    pdf_path = None
    for path in pdf_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        print("❌ No PDF file found. Using sample content instead.")
        return test_with_sample_content()
    
    print(f"📖 Processing real PDF: {pdf_path}")
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print("❌ Failed to extract text from PDF")
            return test_with_sample_content()
        
        print(f"✅ Extracted {len(text)} characters from PDF")
        
        # Create semantic chunker
        semantic_chunker = SemanticEducationalChunker()
        
        # Create semantic chunks
        chunks, relationships = semantic_chunker.create_semantic_chunks(text)
        print(f"✅ Created {len(chunks)} semantic chunks")
        print(f"✅ Created {len(relationships)} relationships")
        
        # Create test questions
        questions = create_enhanced_semantic_questions()
        
        # Test each question
        print(f"\n❓ Testing 10 Enhanced Semantic Questions...")
        print("=" * 70)
        
        results = []
        total_semantic_score = 0
        
        for question in questions:
            print(f"\n🔍 {question['id']}: {question['question']}")
            print(f"   Type: {question['type']}, Difficulty: {question['difficulty']}")
            print(f"   Expected Chunk Types: {[t.value for t in question['expected_chunk_types']]}")
            
            # Find relevant chunks
            relevant_chunks = []
            
            for chunk in chunks:
                relevance_score = calculate_enhanced_semantic_relevance(chunk, question)
                
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
        print(f"\n📈 ENHANCED SEMANTIC CHUNKING QUALITY ANALYSIS")
        print("=" * 70)
        
        avg_semantic_score = total_semantic_score / len(questions)
        questions_with_matches = sum(1 for r in results if r['total_relevant'] > 0)
        
        print(f"📊 Overall Results:")
        print(f"   • Questions with matches: {questions_with_matches}/{len(questions)} ({questions_with_matches/len(questions)*100:.1f}%)")
        print(f"   • Average semantic score: {avg_semantic_score:.2f}")
        print(f"   • Total relationships created: {len(relationships)}")
        
        # Quality assessment
        if avg_semantic_score >= 4.0:
            quality_grade = "A+ (Excellent)"
        elif avg_semantic_score >= 3.0:
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
            print("⚠️  SEMANTIC CHUNKING NEEDS SIGNIFICANT IMPROVEMENT:")
            print("   • Enhance concept detection algorithms")
            print("   • Improve content type classification")
            print("   • Strengthen relationship mapping")
            print("   • Optimize for real educational content")
        elif avg_semantic_score < 3.0:
            print("✅  GOOD SEMANTIC CHUNKING WITH ROOM FOR IMPROVEMENT:")
            print("   • Fine-tune concept extraction for real content")
            print("   • Optimize boundary detection")
            print("   • Enhance cross-chunk relationships")
            print("   • Improve educational content understanding")
        else:
            print("🏆  EXCELLENT SEMANTIC CHUNKING QUALITY:")
            print("   • System demonstrates strong semantic understanding")
            print("   • Content separation is working effectively")
            print("   • Relationships are being properly mapped")
            print("   • Excellent handling of real educational content")
        
        return {
            'overall_score': avg_semantic_score,
            'quality_grade': quality_grade,
            'questions_tested': len(questions),
            'questions_with_matches': questions_with_matches,
            'relationships_created': len(relationships),
            'detailed_results': results,
            'pdf_processed': True
        }
        
    except Exception as e:
        print(f"❌ Error during enhanced semantic chunking test: {e}")
        return test_with_sample_content()

def test_with_sample_content():
    """
    Fallback test with sample content
    """
    print("📝 Using sample content for testing...")
    
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
    
    # Create semantic chunker
    semantic_chunker = SemanticEducationalChunker()
    
    try:
        # Create semantic chunks
        chunks, relationships = semantic_chunker.create_semantic_chunks(sample_content)
        print(f"✅ Created {len(chunks)} semantic chunks")
        print(f"✅ Created {len(relationships)} relationships")
        
        # Create test questions
        questions = create_enhanced_semantic_questions()
        
        # Test each question
        print(f"\n❓ Testing 10 Enhanced Semantic Questions...")
        print("=" * 70)
        
        results = []
        total_semantic_score = 0
        
        for question in questions:
            print(f"\n🔍 {question['id']}: {question['question']}")
            print(f"   Type: {question['type']}, Difficulty: {question['difficulty']}")
            
            # Find relevant chunks
            relevant_chunks = []
            
            for chunk in chunks:
                relevance_score = calculate_enhanced_semantic_relevance(chunk, question)
                
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
        print(f"\n📈 ENHANCED SEMANTIC CHUNKING QUALITY ANALYSIS")
        print("=" * 70)
        
        avg_semantic_score = total_semantic_score / len(questions)
        questions_with_matches = sum(1 for r in results if r['total_relevant'] > 0)
        
        print(f"📊 Overall Results:")
        print(f"   • Questions with matches: {questions_with_matches}/{len(questions)} ({questions_with_matches/len(questions)*100:.1f}%)")
        print(f"   • Average semantic score: {avg_semantic_score:.2f}")
        print(f"   • Total relationships created: {len(relationships)}")
        
        # Quality assessment
        if avg_semantic_score >= 4.0:
            quality_grade = "A+ (Excellent)"
        elif avg_semantic_score >= 3.0:
            quality_grade = "A (Very Good)"
        elif avg_semantic_score >= 2.0:
            quality_grade = "B (Good)"
        elif avg_semantic_score >= 1.5:
            quality_grade = "C (Fair)"
        else:
            quality_grade = "D (Poor)"
        
        print(f"   • Semantic Quality Grade: {quality_grade}")
        
        return {
            'overall_score': avg_semantic_score,
            'quality_grade': quality_grade,
            'questions_tested': len(questions),
            'questions_with_matches': questions_with_matches,
            'relationships_created': len(relationships),
            'detailed_results': results,
            'pdf_processed': False
        }
        
    except Exception as e:
        print(f"❌ Error during sample content test: {e}")
        return None

def save_enhanced_test_results(results: Dict[str, Any]):
    """Save enhanced test results to file"""
    if not results:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enhanced_semantic_chunking_test_results_{timestamp}.json"
    
    # Convert results to serializable format
    serializable_results = {
        'test_date': datetime.now().isoformat(),
        'overall_score': results['overall_score'],
        'quality_grade': results['quality_grade'],
        'questions_tested': results['questions_tested'],
        'questions_with_matches': results['questions_with_matches'],
        'relationships_created': results['relationships_created'],
        'pdf_processed': results.get('pdf_processed', False),
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
    # Run enhanced semantic chunking quality test
    results = test_with_real_pdf_content()
    
    if results:
        # Save results
        save_enhanced_test_results(results)
        
        print(f"\n🎯 ENHANCED SEMANTIC CHUNKING QUALITY TEST COMPLETED")
        print(f"   Overall Score: {results['overall_score']:.2f}")
        print(f"   Quality Grade: {results['quality_grade']}")
        print(f"   Success Rate: {results['questions_with_matches']}/{results['questions_tested']}")
        print(f"   PDF Processed: {results.get('pdf_processed', False)}")
    else:
        print("❌ Enhanced semantic chunking quality test failed")
