#!/usr/bin/env python3
"""
Comprehensive Semantic Chunk Retrieval Test

Tests whether our semantic chunking system provides educationally complete 
content by creating complex questions and validating retrieval results.
"""

import os
import sys
import json
import sqlite3
import numpy as np
from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from embeddings.vector_embedding_engine import VectorEmbeddingEngine

@dataclass
class RetrievalResult:
    """Result of chunk retrieval with metadata"""
    chunk_id: str
    chunk_type: str
    content: str
    similarity_score: float
    chapter_title: str
    mother_section: str
    concepts: List[str] = field(default_factory=list)
    estimated_duration: int = 0
    difficulty_level: str = "beginner"
    confidence: float = 0.0

@dataclass
class EducationalCompleteness:
    """Measures educational completeness of retrieved chunks"""
    has_theory: bool = False
    has_examples: bool = False
    has_activities: bool = False
    has_exercises: bool = False
    concept_coverage: float = 0.0
    relationship_density: float = 0.0
    learning_flow_score: float = 0.0
    total_duration: int = 0
    difficulty_range: List[str] = field(default_factory=list)

class SemanticRetrievalSystem:
    """Advanced retrieval system with relationship awareness"""
    
    def __init__(self, db_path: str = "production_rag_output/class9_science_semantic.db"):
        self.db_path = db_path
        self.embedding_engine = VectorEmbeddingEngine()
        
        # Load chunks and relationships
        self.chunks = self._load_semantic_chunks()
        self.relationships = self._load_relationships()
        self.relationship_map = self._build_relationship_map()
        
    def _load_semantic_chunks(self) -> List[Dict[str, Any]]:
        """Load all semantic chunks from database"""
        conn = sqlite3.connect(self.db_path)
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
                'confidence': confidence or 0.0,
                'estimated_duration': estimated_duration or 0,
                'difficulty_level': difficulty_level or 'beginner',
                'concepts': concepts
            })
        
        conn.close()
        return chunks
    
    def _load_relationships(self) -> List[Dict[str, Any]]:
        """Load chunk relationships"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT source_chunk_id, target_chunk_id, relationship_type, 
                   strength, description
            FROM chunk_relationships
        ''')
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'source_chunk_id': row[0],
                'target_chunk_id': row[1],
                'relationship_type': row[2],
                'strength': row[3],
                'description': row[4]
            })
        
        conn.close()
        return relationships
    
    def _build_relationship_map(self) -> Dict[str, List[Dict]]:
        """Build map of chunk relationships"""
        relationship_map = {}
        
        for rel in self.relationships:
            source_id = rel['source_chunk_id']
            target_id = rel['target_chunk_id']
            
            # Source -> Target relationships
            if source_id not in relationship_map:
                relationship_map[source_id] = []
            relationship_map[source_id].append({
                'target_id': target_id,
                'type': rel['relationship_type'],
                'strength': rel['strength'],
                'description': rel['description']
            })
            
            # Target -> Source relationships (bidirectional)
            if target_id not in relationship_map:
                relationship_map[target_id] = []
            relationship_map[target_id].append({
                'target_id': source_id,
                'type': f"inverse_{rel['relationship_type']}",
                'strength': rel['strength'],
                'description': rel['description']
            })
        
        return relationship_map
    
    def retrieve_with_relationships(self, query: str, top_k: int = 10, expand_related: bool = True) -> List[RetrievalResult]:
        """Retrieve chunks with relationship expansion"""
        # Step 1: Get initial top-k matches
        initial_results = self._get_top_k_chunks(query, top_k)
        
        if not expand_related:
            return initial_results
        
        # Step 2: Expand with related chunks
        related_chunk_ids = set()
        for result in initial_results:
            related_ids = self._get_related_chunk_ids(result.chunk_id, max_depth=2)
            related_chunk_ids.update(related_ids)
        
        # Step 3: Add high-quality related chunks
        expanded_results = list(initial_results)
        for chunk_id in related_chunk_ids:
            if chunk_id not in [r.chunk_id for r in expanded_results]:
                chunk = self._get_chunk_by_id(chunk_id)
                if chunk and len(expanded_results) < top_k * 2:  # Limit expansion
                    # Calculate relationship-based score
                    rel_score = self._calculate_relationship_score(chunk_id, [r.chunk_id for r in initial_results])
                    expanded_results.append(RetrievalResult(
                        chunk_id=chunk_id,
                        chunk_type=chunk['chunk_type'],
                        content=chunk['content'],
                        similarity_score=rel_score,
                        chapter_title=chunk['chapter_title'],
                        mother_section=chunk['mother_section'],
                        concepts=chunk['concepts'],
                        estimated_duration=chunk['estimated_duration'],
                        difficulty_level=chunk['difficulty_level'],
                        confidence=chunk['confidence']
                    ))
        
        # Step 4: Sort by combined score
        expanded_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return expanded_results[:top_k * 2]  # Return expanded set
    
    def _get_top_k_chunks(self, query: str, k: int) -> List[RetrievalResult]:
        """Get top-k chunks using vector similarity"""
        query_embedding = self.embedding_engine.generate_embedding(query)
        if query_embedding is None:
            return []
        
        similarities = []
        for chunk in self.chunks:
            chunk_embedding = self.embedding_engine.generate_embedding(chunk['content'])
            if chunk_embedding is not None:
                similarity = self.embedding_engine.compute_similarity(query_embedding, chunk_embedding)
                similarities.append((chunk, similarity))
        
        # Sort by similarity and take top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for chunk, similarity in similarities[:k]:
            results.append(RetrievalResult(
                chunk_id=chunk['chunk_id'],
                chunk_type=chunk['chunk_type'],
                content=chunk['content'],
                similarity_score=similarity,
                chapter_title=chunk['chapter_title'],
                mother_section=chunk['mother_section'],
                concepts=chunk['concepts'],
                estimated_duration=chunk['estimated_duration'],
                difficulty_level=chunk['difficulty_level'],
                confidence=chunk['confidence']
            ))
        
        return results
    
    def _get_related_chunk_ids(self, chunk_id: str, max_depth: int = 2) -> Set[str]:
        """Get related chunk IDs up to max_depth"""
        related_ids = set()
        to_explore = [(chunk_id, 0)]
        explored = set()
        
        while to_explore:
            current_id, depth = to_explore.pop(0)
            
            if current_id in explored or depth >= max_depth:
                continue
                
            explored.add(current_id)
            
            if current_id in self.relationship_map:
                for rel in self.relationship_map[current_id]:
                    target_id = rel['target_id']
                    if target_id != chunk_id:  # Don't include original chunk
                        related_ids.add(target_id)
                        if depth < max_depth - 1:
                            to_explore.append((target_id, depth + 1))
        
        return related_ids
    
    def _get_chunk_by_id(self, chunk_id: str) -> Dict[str, Any]:
        """Get chunk by ID"""
        for chunk in self.chunks:
            if chunk['chunk_id'] == chunk_id:
                return chunk
        return None
    
    def _calculate_relationship_score(self, chunk_id: str, primary_chunk_ids: List[str]) -> float:
        """Calculate relationship-based relevance score"""
        score = 0.0
        
        if chunk_id in self.relationship_map:
            for rel in self.relationship_map[chunk_id]:
                if rel['target_id'] in primary_chunk_ids:
                    # Different relationship types have different weights
                    type_weights = {
                        'explains': 0.9,
                        'demonstrates': 0.8,
                        'related': 0.6,
                        'follows': 0.4
                    }
                    weight = type_weights.get(rel['type'], 0.3)
                    score += weight * rel['strength']
        
        return min(score, 1.0)  # Cap at 1.0

class EducationalCompletenessEvaluator:
    """Evaluates educational completeness of retrieved chunks"""
    
    def evaluate_completeness(self, results: List[RetrievalResult]) -> EducationalCompleteness:
        """Evaluate educational completeness of retrieval results"""
        completeness = EducationalCompleteness()
        
        # Check content type coverage
        chunk_types = [r.chunk_type for r in results]
        completeness.has_theory = 'content' in chunk_types
        completeness.has_examples = 'example' in chunk_types
        completeness.has_activities = 'activity' in chunk_types
        completeness.has_exercises = 'exercises' in chunk_types
        
        # Calculate concept coverage
        all_concepts = []
        for result in results:
            all_concepts.extend(result.concepts)
        unique_concepts = set(all_concepts)
        completeness.concept_coverage = len(unique_concepts) / max(len(all_concepts), 1)
        
        # Calculate total duration and difficulty range
        completeness.total_duration = sum(r.estimated_duration for r in results)
        difficulty_levels = [r.difficulty_level for r in results if r.difficulty_level]
        completeness.difficulty_range = list(set(difficulty_levels))
        
        # Calculate learning flow score (simplified)
        type_order = ['content', 'example', 'activity', 'exercises']
        type_positions = {}
        for i, result in enumerate(results):
            if result.chunk_type not in type_positions:
                type_positions[result.chunk_type] = []
            type_positions[result.chunk_type].append(i)
        
        # Check if content types appear in logical order
        flow_score = 0.0
        for i, expected_type in enumerate(type_order):
            if expected_type in type_positions:
                avg_position = sum(type_positions[expected_type]) / len(type_positions[expected_type])
                expected_position = i / len(type_order)
                # Score higher if actual position is close to expected
                position_score = 1.0 - abs(avg_position / len(results) - expected_position)
                flow_score += position_score
        
        completeness.learning_flow_score = flow_score / len(type_order)
        
        return completeness

class ComprehensiveRetrievalTester:
    """Main tester for comprehensive retrieval evaluation"""
    
    def __init__(self):
        self.retrieval_system = SemanticRetrievalSystem()
        self.completeness_evaluator = EducationalCompletenessEvaluator()
        
        # Test questions covering different complexity levels
        self.test_questions = [
            {
                "id": "physics_motion_complex",
                "question": "A student pushes a heavy box across the floor. Explain why the box eventually stops moving, relate this to Newton's laws, and describe an experiment to demonstrate this concept.",
                "expected_topics": ["friction", "newton's laws", "force", "motion", "inertia"],
                "expected_types": ["content", "example", "activity", "exercises"],
                "complexity": "high"
            },
            {
                "id": "chemistry_states_matter",
                "question": "How does heating ice change it to water and then to steam? What happens to the particles during these changes?",
                "expected_topics": ["states of matter", "melting", "evaporation", "particle theory"],
                "expected_types": ["content", "activity", "exercises"],
                "complexity": "medium"
            },
            {
                "id": "biology_cell_structure",
                "question": "What are the main parts of a plant cell and how do they work together?",
                "expected_topics": ["cell structure", "organelles", "plant cell", "cell wall"],
                "expected_types": ["content", "example", "exercises"],
                "complexity": "low"
            }
        ]
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive retrieval test"""
        print("🧪 Starting Comprehensive Semantic Retrieval Test")
        print("=" * 60)
        
        test_results = {}
        
        for test_case in self.test_questions:
            print(f"\n📋 Testing: {test_case['id']}")
            print(f"❓ Question: {test_case['question']}")
            print(f"🎯 Complexity: {test_case['complexity']}")
            
            # Test retrieval
            results = self.retrieval_system.retrieve_with_relationships(
                test_case['question'], 
                top_k=8, 
                expand_related=True
            )
            
            # Evaluate completeness
            completeness = self.completeness_evaluator.evaluate_completeness(results)
            
            # Calculate scores
            scores = self._calculate_test_scores(results, completeness, test_case)
            
            test_results[test_case['id']] = {
                'question': test_case['question'],
                'results': results,
                'completeness': completeness,
                'scores': scores,
                'expected_topics': test_case['expected_topics'],
                'expected_types': test_case['expected_types']
            }
            
            # Display results
            self._display_test_results(test_case, results, completeness, scores)
        
        # Generate summary
        summary = self._generate_test_summary(test_results)
        print(f"\n{'=' * 60}")
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print(f"{'=' * 60}")
        self._display_summary(summary)
        
        return {
            'test_results': test_results,
            'summary': summary
        }
    
    def _calculate_test_scores(self, results: List[RetrievalResult], completeness: EducationalCompleteness, test_case: Dict) -> Dict[str, float]:
        """Calculate various test scores"""
        scores = {}
        
        # Content type coverage score
        expected_types = set(test_case['expected_types'])
        actual_types = set(r.chunk_type for r in results)
        type_coverage = len(expected_types.intersection(actual_types)) / len(expected_types)
        scores['type_coverage'] = type_coverage
        
        # Topic relevance score (simplified keyword matching)
        all_content = ' '.join(r.content.lower() for r in results)
        expected_topics = test_case['expected_topics']
        topic_hits = sum(1 for topic in expected_topics if topic in all_content)
        scores['topic_relevance'] = topic_hits / len(expected_topics)
        
        # Quality score (average similarity)
        scores['avg_similarity'] = np.mean([r.similarity_score for r in results]) if results else 0.0
        
        # Completeness score
        completeness_factors = [
            completeness.has_theory,
            completeness.has_examples,
            completeness.has_activities,
            completeness.has_exercises
        ]
        scores['completeness'] = sum(completeness_factors) / 4.0
        
        # Overall score
        scores['overall'] = np.mean([
            scores['type_coverage'],
            scores['topic_relevance'],
            scores['avg_similarity'],
            scores['completeness']
        ])
        
        return scores
    
    def _display_test_results(self, test_case: Dict, results: List[RetrievalResult], completeness: EducationalCompleteness, scores: Dict):
        """Display test results"""
        print(f"\n📊 Results ({len(results)} chunks retrieved):")
        
        # Group by chunk type
        by_type = {}
        for result in results:
            if result.chunk_type not in by_type:
                by_type[result.chunk_type] = []
            by_type[result.chunk_type].append(result)
        
        for chunk_type, chunks in by_type.items():
            print(f"   📚 {chunk_type}: {len(chunks)} chunks")
            for chunk in chunks[:2]:  # Show top 2 per type
                print(f"      • {chunk.similarity_score:.1%} - {chunk.chapter_title} - {chunk.content[:80]}...")
        
        print(f"\n🎯 Completeness Analysis:")
        print(f"   Theory: {'✅' if completeness.has_theory else '❌'}")
        print(f"   Examples: {'✅' if completeness.has_examples else '❌'}")
        print(f"   Activities: {'✅' if completeness.has_activities else '❌'}")
        print(f"   Exercises: {'✅' if completeness.has_exercises else '❌'}")
        print(f"   Total Duration: {completeness.total_duration} minutes")
        print(f"   Difficulty Range: {', '.join(completeness.difficulty_range)}")
        
        print(f"\n📈 Scores:")
        for score_name, score_value in scores.items():
            print(f"   {score_name}: {score_value:.1%}")
    
    def _generate_test_summary(self, test_results: Dict) -> Dict[str, Any]:
        """Generate overall test summary"""
        all_scores = []
        type_coverage_scores = []
        completeness_scores = []
        
        for test_id, result in test_results.items():
            scores = result['scores']
            all_scores.append(scores['overall'])
            type_coverage_scores.append(scores['type_coverage'])
            completeness_scores.append(scores['completeness'])
        
        return {
            'avg_overall_score': np.mean(all_scores),
            'avg_type_coverage': np.mean(type_coverage_scores),
            'avg_completeness': np.mean(completeness_scores),
            'total_tests': len(test_results),
            'perfect_completeness_tests': sum(1 for _, result in test_results.items() 
                                           if result['scores']['completeness'] == 1.0)
        }
    
    def _display_summary(self, summary: Dict):
        """Display test summary"""
        print(f"🎯 Overall Performance: {summary['avg_overall_score']:.1%}")
        print(f"📚 Average Type Coverage: {summary['avg_type_coverage']:.1%}")
        print(f"🔬 Average Completeness: {summary['avg_completeness']:.1%}")
        print(f"✅ Perfect Completeness: {summary['perfect_completeness_tests']}/{summary['total_tests']} tests")
        
        if summary['avg_overall_score'] >= 0.8:
            print("🎉 Excellent! Semantic chunking provides comprehensive educational content.")
        elif summary['avg_overall_score'] >= 0.6:
            print("👍 Good! Semantic chunking shows strong educational completeness.")
        else:
            print("⚠️  Needs improvement in educational content completeness.")

def main():
    """Main execution function"""
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        return
    
    # Check if semantic database exists
    semantic_db = "production_rag_output/class9_science_semantic.db"
    if not os.path.exists(semantic_db):
        print(f"❌ Error: Semantic database not found: {semantic_db}")
        print("Please run semantic rechunking first.")
        return
    
    # Run comprehensive test
    tester = ComprehensiveRetrievalTester()
    results = tester.run_comprehensive_test()
    
    # Save results
    with open('comprehensive_retrieval_test_results.json', 'w') as f:
        # Convert results to JSON-serializable format
        serializable_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': results['summary'],
            'test_details': {}
        }
        
        for test_id, result in results['test_results'].items():
            serializable_results['test_details'][test_id] = {
                'question': result['question'],
                'scores': result['scores'],
                'chunk_count': len(result['results']),
                'chunk_types': list(set(r.chunk_type for r in result['results'])),
                'chapters_covered': list(set(r.chapter_title for r in result['results'])),
                'completeness': {
                    'has_theory': result['completeness'].has_theory,
                    'has_examples': result['completeness'].has_examples,
                    'has_activities': result['completeness'].has_activities,
                    'has_exercises': result['completeness'].has_exercises,
                    'total_duration': result['completeness'].total_duration,
                    'difficulty_range': result['completeness'].difficulty_range
                }
            }
        
        json.dump(serializable_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: comprehensive_retrieval_test_results.json")

if __name__ == "__main__":
    main()