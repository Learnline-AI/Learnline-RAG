#!/usr/bin/env python3
"""
Semantic Educational Chunker - Advanced content separation and relationship mapping

This system addresses the fundamental flaw in current chunking:
- Separates activities, explanations, and questions into distinct chunks
- Creates metadata relationships between related content
- Maintains educational flow while enabling precise retrieval
"""

import re
import json
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime

# Add current directory to Python path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Simplified imports for testing
from enum import Enum
from dataclasses import dataclass, field as dataclass_field

class ChunkType(Enum):
    ACTIVITY = "activity"
    EXAMPLE = "example"
    CONTENT = "content"
    SPECIAL_BOX = "special_box"
    INTRO = "intro"
    SUMMARY = "summary"
    EXERCISES = "exercises"

@dataclass
class BabyChunk:
    chunk_id: str
    chunk_type: ChunkType = ChunkType.CONTENT
    content: str = ""
    mother_section: str = ""
    mother_section_title: str = ""
    sequence_in_mother: int = 1
    activity_metadata: Optional[Dict] = None
    example_metadata: Optional[Dict] = None
    content_metadata: Optional[Dict] = None
    concept_tags: List[str] = dataclass_field(default_factory=list)
    quality_score: Optional[Dict] = None
    position_in_document: Dict[str, int] = dataclass_field(default_factory=dict)

logger = logging.getLogger(__name__)


@dataclass
class ContentSegment:
    """Individual content segment with type and boundaries"""
    segment_id: str
    content_type: str  # 'explanation', 'activity', 'example', 'question', 'figure'
    content: str
    start_pos: int
    end_pos: int
    identifier: Optional[str] = None  # e.g., "1.9", "Example 2.1"
    title: Optional[str] = None
    concepts: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipMap:
    """Defines relationships between chunks"""
    source_chunk_id: str
    target_chunk_id: str
    relationship_type: str  # 'explains', 'demonstrates', 'requires_prior', 'follows'
    strength: float  # 0.0 to 1.0
    description: str = ""


class SemanticContentSeparator:
    """
    Advanced content separator that identifies and extracts different educational content types
    """
    
    def __init__(self):
        self._activity_patterns = self._compile_activity_patterns()
        self._example_patterns = self._compile_example_patterns()
        self._question_patterns = self._compile_question_patterns()
        self._section_patterns = self._compile_section_patterns()
        
    def _compile_activity_patterns(self) -> List[re.Pattern]:
        """Compile activity detection patterns"""
        patterns = [
            r'Activity\s*[_\-–—\s]*(\d+\.\d+)(.*?)(?=Activity\s*[_\-–—\s]*\d+\.\d+|Example\s+\d+\.\d+|\d+\.\d+\s+[A-Z][a-z]|$)',
            r'ACTIVITY\s+(\d+\.\d+)(.*?)(?=ACTIVITY\s+\d+\.\d+|Example\s+\d+\.\d+|\d+\.\d+\s+[A-Z][a-z]|$)',
            r'गतिविधि\s+(\d+\.\d+)(.*?)(?=गतिविधि\s+\d+\.\d+|उदाहरण\s+\d+\.\d+|\d+\.\d+\s+[A-Z][a-z]|$)',
            r'(Try\s+this|Let\s+us\s+try|Do\s+it\s+yourself)(.*?)(?=Try\s+this|Let\s+us\s+try|Example\s+\d+\.\d+|\d+\.\d+\s+[A-Z][a-z]|$)',
        ]
        return [re.compile(pattern, re.MULTILINE | re.DOTALL | re.IGNORECASE) for pattern in patterns]
    
    def _compile_example_patterns(self) -> List[re.Pattern]:
        """Compile example detection patterns"""
        patterns = [
            r'Example\s+(\d+\.\d+)(.*?)(?=Example\s+\d+\.\d+|Activity\s*[_\-–—\s]*\d+\.\d+|\d+\.\d+\s+[A-Z][a-z]|$)',
            r'EXAMPLE\s+(\d+\.\d+)(.*?)(?=EXAMPLE\s+\d+\.\d+|ACTIVITY\s+\d+\.\d+|\d+\.\d+\s+[A-Z][a-z]|$)',
            r'उदाहरण\s+(\d+\.\d+)(.*?)(?=उदाहरण\s+\d+\.\d+|गतिविधि\s+\d+\.\d+|\d+\.\d+\s+[A-Z][a-z]|$)',
            r'(Solved\s+Example|Problem|Worked\s+Example|Sample\s+Problem)\s+(\d+\.\d+)(.*?)(?=Example\s+\d+\.\d+|Activity\s*[_\-–—\s]*\d+\.\d+|\d+\.\d+\s+[A-Z][a-z]|$)',
        ]
        return [re.compile(pattern, re.MULTILINE | re.DOTALL | re.IGNORECASE) for pattern in patterns]
    
    def _compile_question_patterns(self) -> List[re.Pattern]:
        """Compile question detection patterns"""
        patterns = [
            r'(Questions?|Q\s*u\s*e\s*s\s*t\s*i\s*o\s*n\s*s?)\s*\n(.*?)(?=\d+\.\d+\s+[A-Z][a-z]|Activity\s*[_\-–—\s]*\d+\.\d+|Example\s+\d+\.\d+|$)',
            r'(\d+\.\s+.*?\?)(.*?)(?=\d+\.\s+.*?\?|\d+\.\d+\s+[A-Z][a-z]|Activity\s*[_\-–—\s]*\d+\.\d+|$)',
            r'(What\s+you\s+have\s+learnt)(.*?)(?=\d+\.\d+\s+[A-Z][a-z]|Activity\s*[_\-–—\s]*\d+\.\d+|$)',
            r'(Exercises?)\s*\n(.*?)(?=\d+\.\d+\s+[A-Z][a-z]|Activity\s*[_\-–—\s]*\d+\.\d+|$)',
        ]
        return [re.compile(pattern, re.MULTILINE | re.DOTALL | re.IGNORECASE) for pattern in patterns]
    
    def _compile_section_patterns(self) -> List[re.Pattern]:
        """Compile section header patterns"""
        patterns = [
            r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]{3,60})\n(.*?)(?=\d+\.\d+\s+[A-Z][A-Za-z]|Activity\s*[_\-–—\s]*\d+\.\d+|Example\s+\d+\.\d+|$)',
            r'^(\d+\.\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,8})\n(.*?)(?=\d+\.\d+\s+[A-Z][A-Za-z]|Activity\s*[_\-–—\s]*\d+\.\d+|Example\s+\d+\.\d+|$)',
        ]
        return [re.compile(pattern, re.MULTILINE | re.DOTALL) for pattern in patterns]
    
    def separate_content(self, text: str, section_info: Dict[str, Any] = None) -> List[ContentSegment]:
        """
        Main method to separate educational content into semantic segments
        """
        segments = []
        processed_positions = set()
        
        logger.info(f"Starting semantic content separation for {len(text)} characters")
        
        # 1. Extract Activities
        activity_segments = self._extract_activities(text)
        segments.extend(activity_segments)
        for seg in activity_segments:
            processed_positions.update(range(seg.start_pos, seg.end_pos))
        
        # 2. Extract Examples
        example_segments = self._extract_examples(text)
        segments.extend(example_segments)
        for seg in example_segments:
            processed_positions.update(range(seg.start_pos, seg.end_pos))
        
        # 3. Extract Questions
        question_segments = self._extract_questions(text)
        segments.extend(question_segments)
        for seg in question_segments:
            processed_positions.update(range(seg.start_pos, seg.end_pos))
        
        # 4. Extract Section Headers and Explanations
        explanation_segments = self._extract_explanations(text, processed_positions)
        segments.extend(explanation_segments)
        
        # 5. Sort by position and validate
        segments.sort(key=lambda x: x.start_pos)
        
        logger.info(f"Extracted {len(segments)} semantic segments: "
                   f"Activities: {sum(1 for s in segments if s.content_type == 'activity')}, "
                   f"Examples: {sum(1 for s in segments if s.content_type == 'example')}, "
                   f"Questions: {sum(1 for s in segments if s.content_type == 'question')}, "
                   f"Explanations: {sum(1 for s in segments if s.content_type == 'explanation')}")
        
        return segments
    
    def _extract_activities(self, text: str) -> List[ContentSegment]:
        """Extract activity segments"""
        segments = []
        
        for pattern in self._activity_patterns:
            for match in pattern.finditer(text):
                # Extract activity number if present
                activity_num = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                content = match.group(0).strip()
                
                if len(content) < 50:  # Too short to be a meaningful activity
                    continue
                
                segment = ContentSegment(
                    segment_id=str(uuid.uuid4()),
                    content_type='activity',
                    content=content,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    identifier=activity_num,
                    confidence=0.9,
                    metadata={
                        'activity_number': activity_num,
                        'pattern_matched': pattern.pattern,
                        'estimated_duration': self._estimate_activity_duration(content)
                    }
                )
                segments.append(segment)
        
        return segments
    
    def _extract_examples(self, text: str) -> List[ContentSegment]:
        """Extract example segments"""
        segments = []
        
        for pattern in self._example_patterns:
            for match in pattern.finditer(text):
                example_num = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                content = match.group(0).strip()
                
                if len(content) < 30:  # Too short
                    continue
                
                segment = ContentSegment(
                    segment_id=str(uuid.uuid4()),
                    content_type='example',
                    content=content,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    identifier=example_num,
                    confidence=0.85,
                    metadata={
                        'example_number': example_num,
                        'pattern_matched': pattern.pattern,
                        'has_solution': 'Solution:' in content or 'Answer:' in content,
                        'mathematical_content': bool(re.search(r'[=+\-*/^]|\d+', content))
                    }
                )
                segments.append(segment)
        
        return segments
    
    def _extract_questions(self, text: str) -> List[ContentSegment]:
        """Extract question segments"""
        segments = []
        
        for pattern in self._question_patterns:
            for match in pattern.finditer(text):
                content = match.group(0).strip()
                
                if len(content) < 20:  # Too short
                    continue
                
                # Count individual questions
                question_count = len(re.findall(r'\d+\.\s+', content))
                
                segment = ContentSegment(
                    segment_id=str(uuid.uuid4()),
                    content_type='question',
                    content=content,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.8,
                    metadata={
                        'question_count': question_count,
                        'pattern_matched': pattern.pattern,
                        'question_types': self._classify_questions(content)
                    }
                )
                segments.append(segment)
        
        return segments
    
    def _extract_explanations(self, text: str, processed_positions: Set[int]) -> List[ContentSegment]:
        """Extract explanatory content that hasn't been processed yet"""
        segments = []
        
        # First try to extract section-based explanations
        for pattern in self._section_patterns:
            for match in pattern.finditer(text):
                # Check if this content overlaps with already processed content
                if any(pos in processed_positions for pos in range(match.start(), match.end())):
                    continue
                
                section_num = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                section_title = match.group(2) if match.lastindex and match.lastindex >= 2 else None
                content = match.group(0).strip()
                
                if len(content) < 100:  # Too short for explanation
                    continue
                
                segment = ContentSegment(
                    segment_id=str(uuid.uuid4()),
                    content_type='explanation',
                    content=content,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    identifier=section_num,
                    title=section_title,
                    confidence=0.75,
                    metadata={
                        'section_number': section_num,
                        'section_title': section_title,
                        'pattern_matched': pattern.pattern
                    }
                )
                segments.append(segment)
                
                # Mark as processed
                for pos in range(match.start(), match.end()):
                    processed_positions.add(pos)
        
        # Extract remaining unprocessed text as generic explanations
        unprocessed_text = self._extract_unprocessed_text(text, processed_positions)
        if unprocessed_text:
            for chunk in unprocessed_text:
                if len(chunk['content']) > 200:  # Minimum size for explanation
                    segment = ContentSegment(
                        segment_id=str(uuid.uuid4()),
                        content_type='explanation',
                        content=chunk['content'],
                        start_pos=chunk['start_pos'],
                        end_pos=chunk['end_pos'],
                        confidence=0.6,
                        metadata={
                            'extraction_method': 'residual_content',
                            'word_count': len(chunk['content'].split())
                        }
                    )
                    segments.append(segment)
        
        return segments
    
    def _extract_unprocessed_text(self, text: str, processed_positions: Set[int]) -> List[Dict]:
        """Extract text that hasn't been processed yet"""
        unprocessed_chunks = []
        current_chunk = ""
        chunk_start = 0
        
        for i, char in enumerate(text):
            if i not in processed_positions:
                if not current_chunk:  # Starting new chunk
                    chunk_start = i
                current_chunk += char
            else:
                if current_chunk.strip():  # End current chunk
                    unprocessed_chunks.append({
                        'content': current_chunk.strip(),
                        'start_pos': chunk_start,
                        'end_pos': i
                    })
                    current_chunk = ""
        
        # Handle remaining chunk
        if current_chunk.strip():
            unprocessed_chunks.append({
                'content': current_chunk.strip(),
                'start_pos': chunk_start,
                'end_pos': len(text)
            })
        
        return unprocessed_chunks
    
    def _estimate_activity_duration(self, content: str) -> int:
        """Estimate activity duration in minutes based on content"""
        word_count = len(content.split())
        if word_count < 100:
            return 10
        elif word_count < 300:
            return 20
        else:
            return 30
    
    def _classify_questions(self, content: str) -> List[str]:
        """Classify types of questions in content"""
        question_types = []
        
        if re.search(r'\b(why|how|what|when|where)\b', content, re.IGNORECASE):
            question_types.append('open_ended')
        if re.search(r'\b(true|false|correct|incorrect)\b', content, re.IGNORECASE):
            question_types.append('true_false')
        if re.search(r'\b(choose|select|option)\b', content, re.IGNORECASE):
            question_types.append('multiple_choice')
        if re.search(r'\b(calculate|solve|find)\b', content, re.IGNORECASE):
            question_types.append('computational')
        
        return question_types if question_types else ['general']


class SemanticChunkRelationshipMapper:
    """
    Creates relationships between semantically separated chunks
    """
    
    def __init__(self):
        self.relationship_patterns = self._initialize_relationship_patterns()
    
    def _initialize_relationship_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting relationships"""
        return {
            'explains': [
                r'this\s+(explains|shows|demonstrates|illustrates)',
                r'as\s+(explained|shown|demonstrated)\s+in',
                r'the\s+(explanation|theory|concept)\s+(above|below)'
            ],
            'demonstrates': [
                r'this\s+(activity|experiment)\s+(shows|demonstrates)',
                r'to\s+(demonstrate|show|verify|prove)',
                r'this\s+(proves|verifies|confirms)'
            ],
            'requires_prior': [
                r'as\s+(learned|studied)\s+(earlier|before|previously)',
                r'from\s+(previous|earlier)\s+(chapter|section|lesson)',
                r'building\s+on\s+(previous|earlier)'
            ],
            'follows': [
                r'(next|following|subsequent)\s+(section|chapter|activity)',
                r'in\s+the\s+(next|following)\s+(part|section)',
                r'(after|following)\s+this'
            ]
        }
    
    def create_relationships(self, segments: List[ContentSegment]) -> List[RelationshipMap]:
        """Create relationship mappings between segments"""
        relationships = []
        
        # Create sequential relationships
        for i in range(len(segments) - 1):
            current = segments[i]
            next_seg = segments[i + 1]
            
            # Activity -> Explanation relationships
            if current.content_type == 'activity' and next_seg.content_type == 'explanation':
                relationships.append(RelationshipMap(
                    source_chunk_id=current.segment_id,
                    target_chunk_id=next_seg.segment_id,
                    relationship_type='demonstrates',
                    strength=0.8,
                    description=f"Activity {current.identifier} demonstrates concepts in explanation"
                ))
            
            # Explanation -> Activity relationships
            elif current.content_type == 'explanation' and next_seg.content_type == 'activity':
                relationships.append(RelationshipMap(
                    source_chunk_id=current.segment_id,
                    target_chunk_id=next_seg.segment_id,
                    relationship_type='explains',
                    strength=0.7,
                    description=f"Explanation provides theory for Activity {next_seg.identifier}"
                ))
            
            # Sequential flow
            elif current.content_type == next_seg.content_type:
                relationships.append(RelationshipMap(
                    source_chunk_id=current.segment_id,
                    target_chunk_id=next_seg.segment_id,
                    relationship_type='follows',
                    strength=0.6,
                    description=f"Sequential {current.content_type} content"
                ))
        
        # Create concept-based relationships
        concept_relationships = self._create_concept_relationships(segments)
        relationships.extend(concept_relationships)
        
        return relationships
    
    def _create_concept_relationships(self, segments: List[ContentSegment]) -> List[RelationshipMap]:
        """Create relationships based on shared concepts"""
        relationships = []
        
        # Simple concept overlap detection
        for i, seg1 in enumerate(segments):
            for j, seg2 in enumerate(segments[i+1:], i+1):
                if seg1.content_type != seg2.content_type:
                    # Check for concept overlap
                    overlap_score = self._calculate_concept_overlap(seg1, seg2)
                    if overlap_score > 0.3:
                        relationships.append(RelationshipMap(
                            source_chunk_id=seg1.segment_id,
                            target_chunk_id=seg2.segment_id,
                            relationship_type='related',
                            strength=overlap_score,
                            description=f"Shared conceptual content between {seg1.content_type} and {seg2.content_type}"
                        ))
        
        return relationships
    
    def _calculate_concept_overlap(self, seg1: ContentSegment, seg2: ContentSegment) -> float:
        """Calculate conceptual overlap between two segments"""
        # Simple keyword overlap for now
        words1 = set(re.findall(r'\b\w+\b', seg1.content.lower()))
        words2 = set(re.findall(r'\b\w+\b', seg2.content.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))
        
        return overlap / total if total > 0 else 0.0


class SemanticEducationalChunker:
    """
    Main semantic chunker that orchestrates content separation and chunk creation
    """
    
    def __init__(self):
        self.content_separator = SemanticContentSeparator()
        self.relationship_mapper = SemanticChunkRelationshipMapper()
    
    def create_semantic_chunks(self, text: str, section_info: Dict[str, Any] = None) -> Tuple[List[BabyChunk], List[RelationshipMap]]:
        """
        Main method to create semantically separated chunks with relationships
        """
        logger.info("Starting semantic chunking process")
        
        # 1. Separate content into semantic segments
        segments = self.content_separator.separate_content(text, section_info)
        
        # 2. Convert segments to BabyChunks
        chunks = self._segments_to_chunks(segments, section_info)
        
        # 3. Create relationship mappings
        relationships = self.relationship_mapper.create_relationships(segments)
        
        logger.info(f"Created {len(chunks)} semantic chunks with {len(relationships)} relationships")
        
        return chunks, relationships
    
    def _segments_to_chunks(self, segments: List[ContentSegment], section_info: Dict[str, Any] = None) -> List[BabyChunk]:
        """Convert content segments to BabyChunk objects"""
        chunks = []
        
        for segment in segments:
            # Map content type to ChunkType enum
            chunk_type_mapping = {
                'activity': ChunkType.ACTIVITY,
                'example': ChunkType.EXAMPLE, 
                'explanation': ChunkType.CONTENT,
                'question': ChunkType.EXERCISES
            }
            
            chunk_type = chunk_type_mapping.get(segment.content_type, ChunkType.CONTENT)
            
            # Create metadata specific to content type
            type_specific_metadata = None
            if segment.content_type == 'activity':
                type_specific_metadata = {
                    'activity_number': segment.identifier,
                    'estimated_duration': segment.metadata.get('estimated_duration', 15),
                    'materials_needed': self._extract_materials(segment.content),
                    'steps': self._extract_steps(segment.content)
                }
            elif segment.content_type == 'example':
                type_specific_metadata = {
                    'example_number': segment.identifier,
                    'has_solution': segment.metadata.get('has_solution', False),
                    'mathematical_content': segment.metadata.get('mathematical_content', False),
                    'difficulty_level': self._estimate_difficulty(segment.content)
                }
            elif segment.content_type == 'question':
                type_specific_metadata = {
                    'question_count': segment.metadata.get('question_count', 1),
                    'question_types': segment.metadata.get('question_types', ['general']),
                    'assessment_type': 'formative' if 'exercise' in segment.content.lower() else 'diagnostic'
                }
            
            # Extract key concepts
            concepts = self._extract_concepts(segment.content)
            
            chunk = BabyChunk(
                chunk_id=segment.segment_id,
                chunk_type=chunk_type,
                content=segment.content,
                mother_section=section_info.get('section_number', '') if section_info else '',
                mother_section_title=section_info.get('section_title', '') if section_info else '',
                sequence_in_mother=len(chunks) + 1,
                activity_metadata=type_specific_metadata if segment.content_type == 'activity' else None,
                example_metadata=type_specific_metadata if segment.content_type == 'example' else None,
                content_metadata=type_specific_metadata if segment.content_type == 'explanation' else None,
                concept_tags=concepts,
                quality_score={'overall': segment.confidence, 'semantic_separation': 0.9},
                position_in_document={
                    'start_pos': segment.start_pos,
                    'end_pos': segment.end_pos
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_materials(self, content: str) -> List[str]:
        """Extract materials needed for an activity"""
        materials = []
        # Simple pattern matching for common materials
        material_patterns = [
            r'take\s+(?:a|an|some)?\s*([^,\.\n]+)',
            r'collect\s+(?:the\s+)?(?:following)?\s*([^,\.\n]+)',
            r'you\s+will\s+need\s+([^,\.\n]+)',
            r'materials?\s*:?\s*([^,\.\n]+)'
        ]
        
        for pattern in material_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            materials.extend([m.strip() for m in matches if len(m.strip()) > 2])
        
        return materials[:5]  # Limit to 5 materials
    
    def _extract_steps(self, content: str) -> List[str]:
        """Extract steps from an activity"""
        # Look for bullet points or numbered steps
        step_patterns = [
            r'•\s*([^\n•]+)',
            r'\d+\.\s*([^\n\d]+)',
            r'step\s+\d+\s*:?\s*([^\n]+)',
        ]
        
        steps = []
        for pattern in step_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            steps.extend([s.strip() for s in matches if len(s.strip()) > 10])
        
        return steps[:8]  # Limit to 8 steps
    
    def _estimate_difficulty(self, content: str) -> str:
        """Estimate difficulty level of content"""
        word_count = len(content.split())
        math_indicators = len(re.findall(r'[=+\-*/^]|\b\d+\b', content))
        complex_terms = len(re.findall(r'\b\w{10,}\b', content))  # Long words
        
        score = 0
        if word_count > 500:
            score += 1
        if math_indicators > 5:
            score += 1
        if complex_terms > 10:
            score += 1
        
        if score >= 2:
            return 'advanced'
        elif score == 1:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content"""
        # Simple concept extraction based on common educational patterns
        concept_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+(?:a|an|the)',
            r'concept\s+of\s+([A-Za-z\s]+)',
            r'principle\s+of\s+([A-Za-z\s]+)',
            r'law\s+of\s+([A-Za-z\s]+)',
            r'theory\s+of\s+([A-Za-z\s]+)',
        ]
        
        concepts = []
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.extend([c.strip() for c in matches if len(c.strip()) > 3])
        
        return list(set(concepts))[:5]  # Unique concepts, limit to 5


if __name__ == "__main__":
    # Test the semantic chunker
    chunker = SemanticEducationalChunker()
    
    # Sample text for testing
    sample_text = """
    1.4 Can Matter Change its State?
    We all know from our observation that water can exist in three states of matter–
    solid, as ice, liquid, as the familiar water, and gas, as water vapour.
    
    Activity 1.12
    Take about 150 g of ice in a beaker and suspend a laboratory thermometer so
    that its bulb is in contact with the ice.
    Start heating the beaker on a low flame.
    Note the temperature when the ice starts melting.
    
    Example 1.1
    What is the physical state of water at 250°C?
    Solution: At 250°C, water exists as steam (gas) since this temperature
    is above the boiling point of water (100°C).
    
    Questions
    1. Convert the following temperature to celsius scale: 300 K
    2. What is the physical state of water at 250°C?
    """
    
    chunks, relationships = chunker.create_semantic_chunks(sample_text)
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"- {chunk.chunk_type.value}: {chunk.content[:100]}...")
    
    print(f"\nCreated {len(relationships)} relationships:")
    for rel in relationships:
        print(f"- {rel.relationship_type}: {rel.source_chunk_id} -> {rel.target_chunk_id}")