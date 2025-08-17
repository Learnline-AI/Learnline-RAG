#!/usr/bin/env python3
"""
Comprehensive Quality Validation System for Educational RAG
Validates all aspects of the enhanced system with top-class thresholds
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
from metadata_extraction_engine import MetadataExtractionEngine
import re
import json
from typing import Dict, List, Any, Tuple

class QualityValidator:
    """Comprehensive quality validation for educational chunks"""
    
    def __init__(self):
        self.thresholds = {
            'content_completeness': 0.95,  # 95% - very high standard
            'concept_quality': 0.85,      # 85% - good physics concepts
            'application_quality': 0.80,   # 80% - meaningful applications
            'metadata_richness': 0.90,     # 90% - comprehensive metadata
            'educational_soundness': 0.85,  # 85% - pedagogically sound
            'sentence_completeness': 0.95,  # 95% - proper endings
            'content_coherence': 0.80,     # 80% - logical flow
        }
    
    def validate_chunk_quality(self, chunk, original_content: str) -> Dict[str, Any]:
        """Comprehensive quality validation of a chunk"""
        validation_results = {
            'overall_score': 0.0,
            'individual_scores': {},
            'issues': [],
            'recommendations': [],
            'passed': False
        }
        
        # 1. Content Completeness Validation
        completeness_score, completeness_issues = self._validate_content_completeness(
            chunk, original_content
        )
        validation_results['individual_scores']['content_completeness'] = completeness_score
        validation_results['issues'].extend(completeness_issues)
        
        # 2. Concept Quality Validation
        concept_score, concept_issues = self._validate_concept_quality(chunk)
        validation_results['individual_scores']['concept_quality'] = concept_score
        validation_results['issues'].extend(concept_issues)
        
        # 3. Application Quality Validation
        app_score, app_issues = self._validate_application_quality(chunk)
        validation_results['individual_scores']['application_quality'] = app_score
        validation_results['issues'].extend(app_issues)
        
        # 4. Metadata Richness Validation
        metadata_score, metadata_issues = self._validate_metadata_richness(chunk)
        validation_results['individual_scores']['metadata_richness'] = metadata_score
        validation_results['issues'].extend(metadata_issues)
        
        # 5. Educational Soundness Validation
        edu_score, edu_issues = self._validate_educational_soundness(chunk)
        validation_results['individual_scores']['educational_soundness'] = edu_score
        validation_results['issues'].extend(edu_issues)
        
        # 6. Sentence Completeness Validation
        sentence_score, sentence_issues = self._validate_sentence_completeness(chunk)
        validation_results['individual_scores']['sentence_completeness'] = sentence_score
        validation_results['issues'].extend(sentence_issues)
        
        # 7. Content Coherence Validation
        coherence_score, coherence_issues = self._validate_content_coherence(chunk)
        validation_results['individual_scores']['content_coherence'] = coherence_score
        validation_results['issues'].extend(coherence_issues)
        
        # Calculate overall score
        scores = validation_results['individual_scores']
        overall_score = sum(scores.values()) / len(scores)
        validation_results['overall_score'] = overall_score
        
        # Generate recommendations
        validation_results['recommendations'] = self._generate_recommendations(
            validation_results['individual_scores'], validation_results['issues']
        )
        
        # Determine if passed
        validation_results['passed'] = self._determine_pass_status(scores)
        
        return validation_results
    
    def _validate_content_completeness(self, chunk, original_content: str) -> Tuple[float, List[str]]:
        """Validate that content is complete without truncation"""
        issues = []
        score = 1.0
        
        content = chunk.content
        
        # Check for truncation indicators
        if content.strip() and not content.strip()[-1] in '.!?':
            # Check if it's a natural ending
            natural_endings = [
                'What you have learnt', 'Summary', 'Questions', 'Exercises',
                'Key Points', 'Remember', 'Note:'
            ]
            if not any(ending in content[-100:] for ending in natural_endings):
                issues.append("Content appears truncated - incomplete sentence ending")
                score -= 0.3
        
        # Check for common truncation patterns
        truncation_patterns = [
            r'the distance covered$',  # Incomplete phrase
            r'we learn that$',        # Incomplete conclusion
            r'is used in$',          # Incomplete application
            r'helps us$',            # Incomplete description
        ]
        
        for pattern in truncation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Found truncation pattern: {pattern}")
                score -= 0.2
        
        # Check minimum content length
        if len(content) < 500:
            issues.append("Content too short - may be incomplete")
            score -= 0.1
        
        return max(0.0, score), issues
    
    def _validate_concept_quality(self, chunk) -> Tuple[float, List[str]]:
        """Validate quality of extracted concepts"""
        issues = []
        score = 1.0
        
        metadata = chunk.metadata
        concepts = metadata.get('concepts_and_skills', {})
        main_concepts = concepts.get('main_concepts', [])
        
        if not main_concepts:
            issues.append("No main concepts extracted")
            return 0.0, issues
        
        # Check for bad concepts
        bad_concepts = []
        stop_words = {'the', 'new', 'example', 'given', 'which', 'a', 'an', 'this', 'that'}
        
        for concept in main_concepts:
            if isinstance(concept, str):
                if concept.lower() in stop_words:
                    bad_concepts.append(concept)
                elif len(concept) < 3:
                    bad_concepts.append(concept)
                elif not any(char.isalpha() for char in concept):
                    bad_concepts.append(concept)
        
        if bad_concepts:
            issues.append(f"Found {len(bad_concepts)} poor quality concepts: {bad_concepts}")
            score -= 0.2 * len(bad_concepts) / len(main_concepts)
        
        # Check for physics relevance
        physics_terms = {
            'motion', 'force', 'velocity', 'acceleration', 'distance', 'displacement',
            'speed', 'time', 'mass', 'energy', 'power', 'work', 'pressure',
            'scalar', 'vector', 'position', 'rest'
        }
        
        relevant_concepts = 0
        for concept in main_concepts:
            if any(term in concept.lower() for term in physics_terms):
                relevant_concepts += 1
        
        relevance_ratio = relevant_concepts / len(main_concepts) if main_concepts else 0
        if relevance_ratio < 0.3:  # At least 30% should be physics-related
            issues.append(f"Low physics relevance: only {relevance_ratio:.1%} of concepts are physics-related")
            score -= 0.3
        
        return max(0.0, score), issues
    
    def _validate_application_quality(self, chunk) -> Tuple[float, List[str]]:
        """Validate quality of real-world applications"""
        issues = []
        score = 1.0
        
        metadata = chunk.metadata
        context = metadata.get('educational_context', {})
        applications = context.get('real_world_applications', [])
        
        if not applications:
            issues.append("No real-world applications found")
            return 0.3, issues  # Not critical, but reduces score
        
        # Check application quality
        bad_applications = []
        for app in applications:
            # Check for fragments
            if len(app) < 20:
                bad_applications.append(f"Too short: '{app}'")
            elif app[0].islower():
                bad_applications.append(f"Starts lowercase: '{app}'")
            elif not app.strip().endswith(('.', '!', '?')):
                bad_applications.append(f"No proper ending: '{app}'")
            # Check for common fragment patterns
            elif any(app.lower().startswith(frag) for frag in ['d today', 'nd the', 'of the']):
                bad_applications.append(f"Fragment pattern: '{app}'")
        
        if bad_applications:
            issues.append(f"Found {len(bad_applications)} poor quality applications")
            issues.extend(bad_applications[:3])  # Show first 3 examples
            score -= 0.3 * len(bad_applications) / len(applications)
        
        return max(0.0, score), issues
    
    def _validate_metadata_richness(self, chunk) -> Tuple[float, List[str]]:
        """Validate richness and completeness of metadata"""
        issues = []
        score = 1.0
        
        metadata = chunk.metadata
        
        # Required metadata fields
        required_sections = {
            'basic_info': ['grade_level', 'subject', 'chapter'],
            'content_composition': ['activity_count', 'example_count'],
            'concepts_and_skills': ['main_concepts', 'skills_developed'],
            'educational_context': ['real_world_applications']
        }
        
        missing_sections = []
        for section_name, required_fields in required_sections.items():
            if section_name not in metadata:
                missing_sections.append(section_name)
                continue
            
            section_data = metadata[section_name]
            for field in required_fields:
                if field not in section_data or not section_data[field]:
                    missing_sections.append(f"{section_name}.{field}")
        
        if missing_sections:
            issues.append(f"Missing metadata fields: {missing_sections}")
            score -= 0.1 * len(missing_sections)
        
        # Check metadata depth
        concepts_skills = metadata.get('concepts_and_skills', {})
        if len(concepts_skills.get('main_concepts', [])) < 3:
            issues.append("Insufficient main concepts (less than 3)")
            score -= 0.1
        
        if len(concepts_skills.get('skills_developed', [])) < 2:
            issues.append("Insufficient skills identified (less than 2)")
            score -= 0.1
        
        return max(0.0, score), issues
    
    def _validate_educational_soundness(self, chunk) -> Tuple[float, List[str]]:
        """Validate pedagogical soundness"""
        issues = []
        score = 1.0
        
        content = chunk.content
        
        # Check for educational elements
        educational_elements = {
            'Activity': r'(?:ACTIVITY|Activity)\s+\d+',
            'Example': r'(?:EXAMPLE|Example)\s+\d+', 
            'Questions': r'(?:Questions?|QUESTIONS?)',
            'Summary': r'(?:What you have learnt|Summary|SUMMARY)',
        }
        
        elements_found = []
        for element_name, pattern in educational_elements.items():
            if re.search(pattern, content, re.IGNORECASE):
                elements_found.append(element_name)
        
        if not elements_found:
            issues.append("No clear educational elements identified")
            score -= 0.3
        elif len(elements_found) == 1:
            issues.append("Only one type of educational element found")
            score -= 0.1
        
        # Check pedagogical flow
        if 'Activity' in content and 'learn' not in content.lower():
            issues.append("Activity present but no learning outcome mentioned")
            score -= 0.2
        
        return max(0.0, score), issues
    
    def _validate_sentence_completeness(self, chunk) -> Tuple[float, List[str]]:
        """Validate sentence completeness and proper formatting"""
        issues = []
        score = 1.0
        
        content = chunk.content
        sentences = re.split(r'[.!?]+', content)
        
        incomplete_sentences = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:  # Meaningful sentence
                # Check if it starts properly
                if sentence[0].islower() and not sentence.startswith(('and', 'or', 'but')):
                    incomplete_sentences += 1
        
        if incomplete_sentences > 0:
            issues.append(f"Found {incomplete_sentences} potentially incomplete sentences")
            score -= 0.1 * incomplete_sentences / len(sentences)
        
        return max(0.0, score), issues
    
    def _validate_content_coherence(self, chunk) -> Tuple[float, List[str]]:
        """Validate logical flow and coherence"""
        issues = []
        score = 1.0
        
        content = chunk.content
        
        # Check for excessive repetition
        lines = content.split('\n')
        line_counts = {}
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                line_counts[line] = line_counts.get(line, 0) + 1
        
        repeated_lines = [line for line, count in line_counts.items() if count > 2]
        if repeated_lines:
            issues.append(f"Found {len(repeated_lines)} excessively repeated lines")
            score -= 0.1
        
        # Check for logical flow (basic)
        if 'Activity' in content and 'Example' in content:
            activity_pos = content.find('Activity')
            example_pos = content.find('Example') 
            if example_pos < activity_pos:
                issues.append("Educational flow issue: Example appears before Activity")
                score -= 0.1
        
        return max(0.0, score), issues
    
    def _generate_recommendations(self, scores: Dict[str, float], issues: List[str]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        for metric, score in scores.items():
            threshold = self.thresholds.get(metric, 0.8)
            if score < threshold:
                if metric == 'content_completeness':
                    recommendations.append("Improve boundary detection to prevent content truncation")
                elif metric == 'concept_quality':
                    recommendations.append("Enhance concept extraction with better filtering")
                elif metric == 'application_quality':
                    recommendations.append("Improve application extraction and cleaning")
                elif metric == 'metadata_richness':
                    recommendations.append("Increase metadata coverage and depth")
        
        # Add specific recommendations based on issues
        if any('truncated' in issue.lower() for issue in issues):
            recommendations.append("Review and fix boundary detection algorithms")
        
        if any('concept' in issue.lower() for issue in issues):
            recommendations.append("Refine concept extraction with domain-specific patterns")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _determine_pass_status(self, scores: Dict[str, float]) -> bool:
        """Determine if the chunk passes quality validation"""
        # Must meet all critical thresholds
        critical_metrics = ['content_completeness', 'sentence_completeness']
        for metric in critical_metrics:
            if scores.get(metric, 0) < self.thresholds.get(metric, 0.8):
                return False
        
        # Must have good average score
        avg_score = sum(scores.values()) / len(scores)
        return avg_score >= 0.8  # 80% overall threshold
    
    def validate_system_performance(self, test_results: List[Dict]) -> Dict[str, Any]:
        """Validate overall system performance across multiple tests"""
        if not test_results:
            return {'overall_grade': 'F', 'summary': 'No test results provided'}
        
        # Calculate aggregate metrics
        all_scores = {}
        all_passed = 0
        
        for result in test_results:
            for metric, score in result['individual_scores'].items():
                if metric not in all_scores:
                    all_scores[metric] = []
                all_scores[metric].append(score)
            
            if result['passed']:
                all_passed += 1
        
        # Calculate averages
        avg_scores = {metric: sum(scores)/len(scores) for metric, scores in all_scores.items()}
        overall_avg = sum(avg_scores.values()) / len(avg_scores)
        pass_rate = all_passed / len(test_results)
        
        # Determine grade
        if overall_avg >= 0.9 and pass_rate >= 0.9:
            grade = 'A+'
        elif overall_avg >= 0.85 and pass_rate >= 0.8:
            grade = 'A'
        elif overall_avg >= 0.8 and pass_rate >= 0.7:
            grade = 'B+'
        elif overall_avg >= 0.75 and pass_rate >= 0.6:
            grade = 'B'
        elif overall_avg >= 0.7 and pass_rate >= 0.5:
            grade = 'C'
        else:
            grade = 'F'
        
        return {
            'overall_grade': grade,
            'overall_score': overall_avg,
            'pass_rate': pass_rate,
            'avg_scores': avg_scores,
            'total_tests': len(test_results),
            'passed_tests': all_passed,
            'summary': f"Grade {grade}: {overall_avg:.1%} average, {pass_rate:.1%} pass rate"
        }