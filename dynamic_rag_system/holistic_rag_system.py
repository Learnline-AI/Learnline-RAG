#!/usr/bin/env python3
"""
Holistic Educational RAG System for NCERT-based Learning (Grades 4-10)

This implementation fixes critical issues from the original system:
1. Broken residual content extraction
2. Fragmented chunking that loses pedagogical context
3. Missing prerequisite mapping
4. Fragile boundary detection

Author: Educational AI Team
Version: 2.0
"""

import os
import re
import json
import uuid
import logging
import asyncio
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib
from metadata_extraction_engine import MetadataExtractionEngine, EducationalMetadata
from ai.ai_integration import get_ai_service, ai_detect_boundaries, ai_extract_concepts

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class HolisticChunk:
    """Enhanced chunk structure that preserves pedagogical context"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    prerequisites: List[str] = field(default_factory=list)
    related_chunks: List[str] = field(default_factory=list)
    video_connections: List[str] = field(default_factory=list)
    learning_sequence: Dict[str, Any] = field(default_factory=dict)
    pedagogical_context: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return asdict(self)


@dataclass
class LearningUnit:
    """Represents a coherent learning unit with all related content"""
    unit_id: str
    intro_content: str = ""
    activities: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    figures: List[Dict[str, Any]] = field(default_factory=list)
    questions: List[Dict[str, Any]] = field(default_factory=list)
    formulas: List[Dict[str, Any]] = field(default_factory=list)
    special_boxes: List[Dict[str, Any]] = field(default_factory=list)
    mathematical_content: List[Dict[str, Any]] = field(default_factory=list)
    cross_references: List[Dict[str, Any]] = field(default_factory=list)
    assessments: List[Dict[str, Any]] = field(default_factory=list)
    pedagogical_markers: List[Dict[str, Any]] = field(default_factory=list)
    conclusion: str = ""
    concepts: List[str] = field(default_factory=list)
    position_range: Tuple[int, int] = (0, 0)
    educational_flow: str = "intro_activity_example_conclusion"


class HolisticRAGChunker:
    """
    Main class for creating contextual chunks that preserve learning flow.
    Fixes all critical issues from the original implementation.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.pattern_library = self._initialize_pattern_library()
        self.metadata_engine = MetadataExtractionEngine()  # Initialize metadata engine
        self.ai_service = get_ai_service()  # Initialize AI service
        self.concept_hierarchy = {}
        self.prerequisite_map = {}
        self.use_ai_boundaries = self.ai_service.is_available()  # Enable AI if available
        
    def _get_default_config(self) -> Dict:
        """Default configuration for the chunking system"""
        return {
            'min_chunk_size': 500,
            'max_chunk_size': 2000,
            'target_chunk_size': 1200,
            'overlap_percentage': 15,
            'confidence_threshold': 0.7,
            'grade_levels': list(range(4, 11)),  # Grades 4-10
            'subjects': ['Physics', 'Chemistry', 'Biology', 'Mathematics'],
            'curriculum': 'NCERT'
        }
    
    def _initialize_pattern_library(self) -> Dict:
        """Initialize comprehensive pattern library for educational content detection"""
        return {
            'sections': [
                r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]{3,60})(?:\n|$)',
                r'^(\d+\.\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,8})(?:\n|$)',
                r'^Chapter\s+(\d+):?\s*([A-Za-z\s]+)(?:\n|$)',
                r'^Unit\s+(\d+):?\s*([A-Za-z\s]+)(?:\n|$)',
                r'^Part\s+([A-Z]+):?\s*([A-Za-z\s]+)(?:\n|$)',
            ],
            'activities': [
                r'ACTIVITY\s+(\d+\.\d+)',
                r'Activity\s*[_\-–—\s]*\s*(\d+\.\d+)',
                r'Activity\s*[_\-–—\s]+(\d+\.\d+)',  # Enhanced underscore pattern
                r'गतिविधि\s+(\d+\.\d+)',  # Hindi support
                r'Exercise\s+(\d+\.\d+)',
                r'Lab\s+Activity\s+(\d+\.\d+)',
                r'Hands-on\s+Activity\s+(\d+\.\d+)',
                r'Practical\s+(\d+\.\d+)',
                r'Investigation\s+(\d+\.\d+)',
                r'Experiment\s+(\d+\.\d+)',
                # Enhanced patterns for activities hidden in text
                r'Activity\s*[:\-–—]?\s*(\d+\.\d+)',
                r'Try\s+this\s*[:\-–—]?\s*(\d+\.\d+)?',
                r'Let\s+us\s+try\s*[:\-–—]?\s*(\d+\.\d+)?',
                r'Do\s+it\s+yourself\s*[:\-–—]?\s*(\d+\.\d+)?',
                r'Activity\s+_+\s*(\d+\.\d+)',  # Underscore patterns from PDF
            ],
            'examples': [
                r'Example\s+(\d+\.\d+)',
                r'EXAMPLE\s+(\d+\.\d+)',
                r'उदाहरण\s+(\d+\.\d+)',  # Hindi support
                r'Solved\s+Example\s+(\d+\.\d+)',
                r'Problem\s+(\d+\.\d+)',
                r'Worked\s+Example\s+(\d+\.\d+)',
                r'Sample\s+Problem\s+(\d+\.\d+)',
                r'Illustration\s+(\d+\.\d+)',
            ],
            'figures': [
                r'Fig\.\s*(\d+\.\d+):\s*([^\n]+)',
                r'Figure\s+(\d+\.\d+):\s*([^\n]+)',
                r'चित्र\s+(\d+\.\d+):\s*([^\n]+)',  # Hindi support
                r'Diagram\s+(\d+\.\d+):\s*([^\n]+)',
                r'Graph\s+(\d+\.\d+):\s*([^\n]+)',
                r'Chart\s+(\d+\.\d+):\s*([^\n]+)',
                r'Table\s+(\d+\.\d+):\s*([^\n]+)',
                r'Map\s+(\d+\.\d+):\s*([^\n]+)',
                r'Flowchart\s+(\d+\.\d+):\s*([^\n]+)',
            ],
            'special_boxes': [
                # Knowledge boxes
                r'(DO YOU KNOW\?)',
                r'(DID YOU KNOW\?)',
                r'(क्या आप जानते हैं\?)',  # Hindi
                r'(INTERESTING FACT)',
                r'(FUN FACT)',
                
                # Learning aids
                r'(What you have learnt)',
                r'(WHAT YOU HAVE LEARNT)',
                r'(आपने क्या सीखा)',  # Hindi
                r'(Key takeaways)',
                r'(Summary)',
                r'(SUMMARY)',
                
                # Interactive sections
                r'(THINK AND ACT)',
                r'(Think and Act)',
                r'(सोचें और कार्य करें)',  # Hindi
                r'(TRY THIS)',
                r'(CHECK YOUR PROGRESS)',
                
                # Important notes
                r'(Remember)',
                r'(REMEMBER)',
                r'(याद रखें)',  # Hindi
                r'(Note:)',
                r'(NOTE:)',
                r'(Important:)',
                r'(IMPORTANT:)',
                r'(Caution:)',
                r'(WARNING:)',
                
                # Biographical content
                r'(BIOGRAPHY)',
                r'(About the Scientist)',
                r'(Historical Note)',
                r'(Background)',
                
                # Applications
                r'(APPLICATIONS)',
                r'(Real-world Applications)',
                r'(Everyday Examples)',
                
                # Additional NCERT-specific patterns  
                r'(CAN YOU TELL\?)',
                r'(FIND OUT)',
                r'(OBSERVE AND REPORT)',
                r'(THINK ABOUT IT)',
                r'(For Your Information)',
                r'(FYI:)',
                r'(Science Insight)',
                r'(Did You Know That)',
                r'(Quick Facts)',
                r'(CASE STUDY)',
                
                # Additional learning
                r'(EXTENDED LEARNING)',
                r'(Further Reading)',
                r'(More to Explore)',
                r'(ENRICHMENT)',
            ],
            'questions': [
                # Section headers
                r'Questions?\s*\n',
                r'QUESTIONS?\s*\n',
                r'Exercise\s*\n',
                r'EXERCISE\s*\n',
                r'Problems?\s*\n',
                r'PROBLEMS?\s*\n',
                r'प्रश्न\s*\n',  # Hindi
                
                # Individual questions
                r'(\d+\.\s+[A-Z][^?]*\?)',  # Numbered questions ending with ?
                r'(\d+\.\s+[A-Z][^.]*\.)',  # Numbered statements
                r'(\([a-z]\)\s+[A-Z][^?]*\?)',  # (a) style questions
                r'(Q\d+\.\s+[A-Z][^?]*\?)',  # Q1. style questions
                
                # Question types
                r'(Multiple Choice Questions?)',
                r'(MCQ)',
                r'(True or False)',
                r'(Fill in the blanks?)',
                r'(Short Answer Questions?)',
                r'(Long Answer Questions?)',
                r'(Very Short Answer)',
                r'(Assertion and Reason)',
            ],
            'formulas': [
                # Basic equations
                r'([A-Z]\s*=\s*[A-Za-z0-9\s\+\-\*/\(\)]+)',  # F = ma
                r'([a-z]\s*=\s*[A-Za-z0-9\s\+\-\*/\(\)]+)',  # v = u + at
                
                # Complex formulas
                r'(\\frac\{[^}]+\}\{[^}]+\})',  # LaTeX fractions
                r'([A-Za-z]+\s*=\s*\\frac\{[^}]+\}\{[^}]+\})',  # Formula with fractions
                r'([A-Za-z]+\s*=\s*[A-Za-z0-9\s\+\-\*/\(\)]+\s*[±]\s*[A-Za-z0-9\s\+\-\*/\(\)]+)',  # Complex equations
                
                # Scientific notation
                r'(\d+\.\d+\s*×\s*10\^[−\-]?\d+)',
                r'(\d+\.\d+\s*[×*]\s*10\^[−\-]?\d+)',
                
                # Units and measurements
                r'(\d+\s*[a-zA-Z]+/[a-zA-Z]+)',  # m/s, km/h
                r'(\d+\s*[a-zA-Z]+\^?\d*)',  # m², kg, etc.
            ],
            'mathematical_content': [
                # Equations and expressions
                r'([A-Za-z]+\s*=\s*[A-Za-z0-9\s\+\-\*/\(\)π√∆]+)',
                r'([A-Za-z]+\s*∝\s*[A-Za-z0-9\s\+\-\*/\(\)]+)',  # Proportionality
                r'([A-Za-z]+\s*∞\s*[A-Za-z0-9\s\+\-\*/\(\)]+)',  # Infinity
                
                # Mathematical symbols
                r'(≤|≥|≠|≈|∞|∝|±|√|∆|π|θ|α|β|γ)',
                
                # Calculations
                r'(Given:?\s*[A-Za-z0-9\s=,\+\-\*/\(\)]+)',
                r'(Solution:?\s*[A-Za-z0-9\s=,\+\-\*/\(\)]+)',
                r'(Therefore:?\s*[A-Za-z0-9\s=,\+\-\*/\(\)]+)',
            ],
            'concepts': [
                # Definitions
                r'Definition:\s*([^\n]+)',
                r'DEFINITION:\s*([^\n]+)',
                r'परिभाषा:\s*([^\n]+)',  # Hindi
                r'([A-Za-z\s]+)\s+is\s+defined\s+as\s+([^\n]+)',
                r'([A-Za-z\s]+)\s+means\s+([^\n]+)',
                r'Concept:\s*([^\n]+)',
                
                # Properties and characteristics
                r'Properties?\s+of\s+([A-Za-z\s]+):',
                r'Characteristics?\s+of\s+([A-Za-z\s]+):',
                r'Features?\s+of\s+([A-Za-z\s]+):',
                
                # Types and classifications
                r'Types?\s+of\s+([A-Za-z\s]+):',
                r'Classification\s+of\s+([A-Za-z\s]+):',
                r'Categories?\s+of\s+([A-Za-z\s]+):',
            ],
            'cross_references': [
                # Internal references
                r'(see\s+(?:section|chapter|page|figure|table|example|activity)\s+\d+[\.\d]*)',
                r'(refer\s+to\s+(?:section|chapter|page|figure|table|example|activity)\s+\d+[\.\d]*)',
                r'(as\s+discussed\s+in\s+(?:section|chapter|page)\s+\d+[\.\d]*)',
                r'(in\s+the\s+previous\s+(?:section|chapter))',
                r'(in\s+the\s+next\s+(?:section|chapter))',
                
                # Figure/table references
                r'(Fig\.\s*\d+\.\d+)',
                r'(Figure\s+\d+\.\d+)',
                r'(Table\s+\d+\.\d+)',
                r'(Diagram\s+\d+\.\d+)',
                
                # External references
                r'(Class\s+\d+\s+(?:textbook|book))',
                r'(Grade\s+\d+\s+(?:textbook|book))',
                r'(NCERT\s+(?:textbook|book))',
            ],
            'assessment_elements': [
                # Exercise types
                r'(Exercises?)',
                r'(Practice\s+Problems?)',
                r'(Review\s+Questions?)',
                r'(Test\s+Yourself)',
                r'(Self\s+Assessment)',
                
                # Assignment types
                r'(Project\s+Work)',
                r'(Field\s+Work)',
                r'(Research\s+Activity)',
                r'(Group\s+Activity)',
                
                # Evaluation criteria
                r'(Learning\s+Outcomes?)',
                r'(Assessment\s+Criteria)',
                r'(Evaluation)',
                r'(Rubric)',
            ],
            'pedagogical_markers': [
                # Learning objectives
                r'(Objectives?:)',
                r'(Learning\s+Objectives?:)',
                r'(By\s+the\s+end\s+of\s+this\s+(?:chapter|section|lesson))',
                r'(Students?\s+will\s+be\s+able\s+to)',
                r'(You\s+will\s+learn)',
                
                # Prerequisites
                r'(Prerequisites?:)',
                r'(Pre-requisites?:)',
                r'(Before\s+studying\s+this)',
                r'(You\s+should\s+know)',
                
                # Difficulty indicators
                r'(Basic\s+level)',
                r'(Intermediate\s+level)',
                r'(Advanced\s+level)',
                r'(Foundation)',
                r'(Higher\s+Order)',
            ]
        }
    
    def process_mother_section(self, mother_section: Dict, full_text: str, 
                             char_to_page_map: Dict) -> List[HolisticChunk]:
        """
        Process a mother section into contextual chunks.
        This is the main entry point that fixes the fragmented chunking issue.
        """
        logger.info(f"Processing section {mother_section['section_number']}: {mother_section['title']}")
        
        # Extract mother content
        mother_content = full_text[mother_section['start_pos']:mother_section['end_pos']]
        
        # Add full content to mother section for chunk creation
        mother_section['full_content'] = mother_content
        
        # Detect learning units instead of creating separate chunks
        learning_units = self._detect_learning_units(mother_content, mother_section)
        
        # Create contextual chunks from learning units with intelligent size balancing
        contextual_chunks = []
        chunk_sequence = 1
        
        for unit in learning_units:
            # Check if unit should be split for better size balance
            sub_units = self._split_large_chunk_intelligently(unit)
            
            # Create chunks from sub-units
            for sub_unit in sub_units:
                chunk = self._create_contextual_chunk(
                    sub_unit, mother_section, char_to_page_map, chunk_sequence
                )
                contextual_chunks.append(chunk)
                chunk_sequence += 1
            
        logger.info(f"Created {len(contextual_chunks)} contextual chunks for section {mother_section['section_number']}")
        return contextual_chunks
    
    def _detect_learning_units(self, content: str, mother_section: Dict) -> List[LearningUnit]:
        """
        Detect coherent learning units using AI-powered analysis.
        This replaces the fragile regex-based boundary detection.
        """
        if self.use_ai_boundaries and len(content) > 500:
            # Use AI-powered boundary detection for better accuracy
            try:
                # Check if we're already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an event loop, skip AI for now to avoid conflicts
                    logger.info("Already in event loop, using pattern-based detection")
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run
                    ai_boundaries = asyncio.run(self._detect_boundaries_with_ai(content))
                    if ai_boundaries:
                        learning_units = self._create_units_from_ai_boundaries(ai_boundaries, content, mother_section)
                        logger.info(f"AI boundary detection created {len(learning_units)} learning units")
                        return learning_units
            except Exception as e:
                logger.warning(f"AI boundary detection failed, falling back to pattern-based: {e}")
        
        # Fallback to pattern-based detection
        elements = self._identify_educational_elements(content)
        learning_units = self._group_into_learning_units(elements, content)
        validated_units = self._validate_learning_units(learning_units, mother_section)
        
        return validated_units
    
    def _identify_educational_elements(self, content: str) -> List[Dict]:
        """Identify all educational elements with their positions and types"""
        elements = []
        
        # Detect activities with context
        for pattern in self.pattern_library['activities']:
            for match in re.finditer(pattern, content, re.MULTILINE):
                element = {
                    'type': 'activity',
                    'position': match.start(),
                    'match': match,
                    'number': match.group(1) if match.groups() else None,
                    'content_start': match.start(),
                    'content_end': self._find_element_end(content, match.start(), 'activity')
                }
                elements.append(element)
        
        # Detect examples with context
        for pattern in self.pattern_library['examples']:
            for match in re.finditer(pattern, content, re.MULTILINE):
                element = {
                    'type': 'example',
                    'position': match.start(),
                    'match': match,
                    'number': match.group(1) if match.groups() else None,
                    'content_start': match.start(),
                    'content_end': self._find_element_end(content, match.start(), 'example')
                }
                elements.append(element)
        
        # Detect figures
        for pattern in self.pattern_library['figures']:
            for match in re.finditer(pattern, content, re.MULTILINE):
                element = {
                    'type': 'figure',
                    'position': match.start(),
                    'match': match,
                    'number': match.group(1) if match.groups() else None,
                    'caption': match.group(2) if len(match.groups()) > 1 else None
                }
                elements.append(element)
        
        # Detect special boxes
        for pattern in self.pattern_library['special_boxes']:
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                element = {
                    'type': 'special_box',
                    'position': match.start(),
                    'match': match,
                    'box_type': match.group(1) if match.groups() else match.group(0),
                    'content_start': match.start(),
                    'content_end': self._find_element_end(content, match.start(), 'special_box')
                }
                elements.append(element)
        
        # Detect concept definitions
        for pattern in self.pattern_library['concepts']:
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                element = {
                    'type': 'concept',
                    'position': match.start(),
                    'match': match,
                    'concept': match.group(1) if match.groups() else match.group(0)
                }
                elements.append(element)
        
        # Detect questions
        for pattern in self.pattern_library['questions']:
            for match in re.finditer(pattern, content, re.MULTILINE):
                element = {
                    'type': 'question',
                    'position': match.start(),
                    'match': match,
                    'question_text': match.group(1) if match.groups() else match.group(0),
                    'content_start': match.start(),
                    'content_end': self._find_element_end(content, match.start(), 'question')
                }
                elements.append(element)
        
        # Detect formulas
        for pattern in self.pattern_library['formulas']:
            for match in re.finditer(pattern, content, re.MULTILINE):
                element = {
                    'type': 'formula',
                    'position': match.start(),
                    'match': match,
                    'formula': match.group(1) if match.groups() else match.group(0)
                }
                elements.append(element)
        
        # Detect mathematical content
        for pattern in self.pattern_library['mathematical_content']:
            for match in re.finditer(pattern, content, re.MULTILINE):
                element = {
                    'type': 'mathematical_content',
                    'position': match.start(),
                    'match': match,
                    'mathematical_expression': match.group(1) if match.groups() else match.group(0)
                }
                elements.append(element)
        
        # Detect cross-references
        for pattern in self.pattern_library['cross_references']:
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                element = {
                    'type': 'cross_reference',
                    'position': match.start(),
                    'match': match,
                    'reference': match.group(1) if match.groups() else match.group(0)
                }
                elements.append(element)
        
        # Detect assessment elements
        for pattern in self.pattern_library['assessment_elements']:
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                element = {
                    'type': 'assessment',
                    'position': match.start(),
                    'match': match,
                    'assessment_type': match.group(1) if match.groups() else match.group(0),
                    'content_start': match.start(),
                    'content_end': self._find_element_end(content, match.start(), 'assessment')
                }
                elements.append(element)
        
        # Detect pedagogical markers
        for pattern in self.pattern_library['pedagogical_markers']:
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                element = {
                    'type': 'pedagogical_marker',
                    'position': match.start(),
                    'match': match,
                    'marker_type': match.group(1) if match.groups() else match.group(0)
                }
                elements.append(element)
        
        # Sort by position
        elements.sort(key=lambda x: x['position'])
        return elements
    
    def _find_element_end(self, content: str, start_pos: int, element_type: str) -> int:
        """
        Enhanced boundary detection for complete NCERT educational sections.
        Prevents content truncation by recognizing natural educational boundaries.
        """
        # NCERT-specific educational section boundaries
        ncert_section_boundaries = [
            r'\n\s*(?:What you have learnt|WHAT YOU HAVE LEARNT)',
            r'\n\s*(?:Summary|SUMMARY)',
            r'\n\s*(?:Key Points|KEY POINTS)',
            r'\n\s*(?:Exercises|EXERCISES)',
            r'\n\s*(?:Questions|QUESTIONS)',
            r'\n\s*(?:Multiple Choice Questions|MULTIPLE CHOICE QUESTIONS)',
            r'\n\s*(?:Short Answer Questions|SHORT ANSWER QUESTIONS)',
            r'\n\s*(?:Long Answer Questions|LONG ANSWER QUESTIONS)',
            r'\n\s*(?:Numerical Problems|NUMERICAL PROBLEMS)',
            r'\n\s*(?:Project Work|PROJECT WORK)',
            r'\n\s*(?:Extended Learning|EXTENDED LEARNING)',
        ]
        
        # Educational element boundaries  
        element_boundaries = [
            r'\n\s*(?:Activity|ACTIVITY)\s+\d+\.\d+',  # Next activity
            r'\n\s*(?:Example|EXAMPLE)\s+\d+\.\d+',   # Next example
            r'\n\s*(?:Fig\.|Figure|FIGURE)\s+\d+\.\d+', # Next figure
            r'\n\s*(?:DO YOU KNOW\?|DO YOU KNOW)',    # Special boxes
            r'\n\s*(?:THINK AND ACT|Think and Act)',  # Think and act sections
            r'\n\s*(?:BIOGRAPHY|Biography)',          # Biography boxes
            r'\n\s*(?:NOTE|Note):',                   # Note sections
        ]
        
        # Chapter/section boundaries
        major_boundaries = [
            r'\n\s*\d+\.\d+\s+[A-Z][^.]*',  # Next subsection (e.g., "7.2 Velocity")
            r'\n\s*Chapter\s+\d+',           # Next chapter
            r'\n\s*CHAPTER\s+\d+',          # Next chapter (caps)
        ]
        
        # Combine all boundary patterns
        all_boundaries = ncert_section_boundaries + element_boundaries + major_boundaries
        
        # Dynamic length limits based on element type
        element_configs = {
            'activity': {'min_length': 150, 'preferred_max': 1200, 'absolute_max': 2000},
            'example': {'min_length': 100, 'preferred_max': 800, 'absolute_max': 1500},
            'special_box': {'min_length': 50, 'preferred_max': 600, 'absolute_max': 1000},
            'question': {'min_length': 20, 'preferred_max': 400, 'absolute_max': 800},
            'concept': {'min_length': 50, 'preferred_max': 300, 'absolute_max': 600},
            'default': {'min_length': 100, 'preferred_max': 800, 'absolute_max': 1500}
        }
        
        config = element_configs.get(element_type, element_configs['default'])
        min_length = config['min_length']
        preferred_max = config['preferred_max']
        absolute_max = config['absolute_max']
        
        # Search for boundaries in preferred range first
        search_start = start_pos + min_length
        search_end = min(start_pos + preferred_max, len(content))
        
        best_boundary = None
        boundary_priority = 0  # Higher priority = better boundary
        
        # Search in preferred range
        for i, pattern in enumerate(all_boundaries):
            match = re.search(pattern, content[search_start:search_end])
            if match:
                boundary_pos = search_start + match.start()
                # Prioritize NCERT section boundaries
                priority = 3 if i < len(ncert_section_boundaries) else \
                          2 if i < len(ncert_section_boundaries) + len(element_boundaries) else 1
                
                if priority > boundary_priority:
                    best_boundary = boundary_pos
                    boundary_priority = priority
        
        # If no boundary found in preferred range, extend search to absolute max
        if best_boundary is None and search_end < start_pos + absolute_max:
            extended_search_end = min(start_pos + absolute_max, len(content))
            
            for pattern in all_boundaries:
                match = re.search(pattern, content[search_end:extended_search_end])
                if match:
                    best_boundary = search_end + match.start()
                    break
        
        # If still no boundary, find sentence boundary
        if best_boundary is None:
            target_pos = min(start_pos + preferred_max, len(content) - 1)
            best_boundary = self._find_sentence_boundary(content, target_pos)
        
        # Validate the boundary doesn't truncate content
        if best_boundary:
            best_boundary = self._validate_content_completeness(content, start_pos, best_boundary)
        
        # For learning units, ensure we capture complete educational flow
        if element_type in ['activity', 'example', 'default'] and best_boundary:
            best_boundary = self._ensure_complete_learning_unit(content, start_pos, best_boundary)
        
        return best_boundary or min(start_pos + absolute_max, len(content))
    
    def _find_sentence_boundary(self, content: str, target_pos: int) -> int:
        """Find the nearest complete sentence boundary."""
        # Look for sentence endings within reasonable range
        sentence_endings = ['. ', '.\n', '? ', '?\n', '! ', '!\n']
        
        # Search backwards from target position for sentence boundary
        search_start = max(0, target_pos - 100)
        
        for i in range(target_pos, search_start, -1):
            for ending in sentence_endings:
                if content[i:i+len(ending)] == ending:
                    return i + 1  # Return position after the period/punctuation
        
        # If no sentence boundary found, search forward slightly
        search_end = min(len(content), target_pos + 100)
        for i in range(target_pos, search_end):
            for ending in sentence_endings:
                if content[i:i+len(ending)] == ending:
                    return i + 1
        
        # Fallback to original position
        return target_pos
    
    def _validate_content_completeness(self, content: str, start_pos: int, end_pos: int) -> int:
        """Validate that content boundary doesn't truncate important information."""
        section_content = content[start_pos:end_pos]
        
        # Check for incomplete sentences (ends without proper punctuation)
        if section_content.strip() and not section_content.strip()[-1] in '.!?':
            # Try to extend to next sentence boundary
            extended_end = self._find_sentence_boundary(content, end_pos)
            if extended_end > end_pos and extended_end - start_pos < 2500:  # Reasonable limit
                return extended_end
        
        # Check for incomplete educational elements
        incomplete_patterns = [
            r'Solution:\s*$',           # Incomplete solution
            r'Given:\s*$',              # Incomplete given data
            r'Materials needed:\s*$',   # Incomplete materials list
            r'Time required:\s*$',      # Incomplete time info
            r'Safety note:\s*$',        # Incomplete safety info
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, section_content[-50:], re.IGNORECASE):
                # Extend to capture complete element
                extended_end = min(end_pos + 200, len(content))
                next_complete = self._find_sentence_boundary(content, extended_end)
                if next_complete > end_pos:
                    return next_complete
        
        return end_pos
    
    def _ensure_complete_learning_unit(self, content: str, start_pos: int, end_pos: int) -> int:
        """Ensure we capture complete learning units with all educational elements"""
        section_content = content[start_pos:end_pos]
        
        # Check for incomplete educational sections that should be included
        educational_completions = [
            r'What you have learnt.*?(?=\n\s*(?:\d+\.\d+|Chapter|$))',
            r'Summary.*?(?=\n\s*(?:\d+\.\d+|Chapter|$))',
            r'Questions.*?(?=\n\s*(?:Multiple Choice|What you have|Summary|$))',
            r'Multiple Choice Questions.*?(?=\n\s*(?:What you have|Summary|$))',
            r'Exercises.*?(?=\n\s*(?:What you have|Summary|$))',
        ]
        
        # Look ahead to see if there are important educational sections we're missing
        remaining_content = content[end_pos:end_pos + 2000]  # Look ahead 2000 chars
        
        for pattern in educational_completions:
            match = re.search(pattern, remaining_content, re.DOTALL | re.IGNORECASE)
            if match:
                # Found important section - extend boundary to include it
                section_end = end_pos + match.end()
                # Make sure we don't exceed reasonable limits
                if section_end - start_pos < 5000:  # Max 5000 chars for complete unit
                    end_pos = section_end
                    break
        
        # If we have "Activity" but no conclusion, try to find it
        if 'Activity' in section_content and not any(phrase in section_content for phrase in 
            ['From this activity', 'we learn', 'we observe', 'demonstrates', 'shows that']):
            
            activity_conclusion_pattern = r'From this activity.*?(?=\n\s*(?:Activity|Example|Questions|$))'
            match = re.search(activity_conclusion_pattern, content[end_pos:end_pos + 500], re.DOTALL | re.IGNORECASE)
            if match:
                end_pos = end_pos + match.end()
        
        # If we have "Example" but incomplete solution, try to complete it
        if 'Example' in section_content and 'Solution' in section_content:
            solution_part = section_content.split('Solution')[-1]
            if len(solution_part.strip()) < 50:  # Very short solution, likely incomplete
                complete_solution_pattern = r'Solution.*?(?=\n\s*(?:Example|Activity|Questions|$))'
                match = re.search(complete_solution_pattern, content[start_pos:end_pos + 800], re.DOTALL | re.IGNORECASE)
                if match:
                    end_pos = start_pos + match.end()
        
        return end_pos
    
    def _finalize_learning_unit(self, unit: LearningUnit, content: str, last_position: int):
        """Finalize a learning unit by adding any remaining content like summaries"""
        # Get remaining content from last processed position
        remaining_content = content[last_position:].strip()
        
        if remaining_content and len(remaining_content) > 20:
            # Check if this contains important summary sections
            summary_sections = [
                'What you have learnt',
                'Summary', 
                'Key Points',
                'Questions',
                'Exercises'
            ]
            
            has_summary = any(section in remaining_content for section in summary_sections)
            
            if has_summary:
                # This is important concluding content - add as conclusion
                unit.conclusion = remaining_content
            else:
                # Regular content - extend intro or add as conclusion
                if len(remaining_content) > 100:
                    unit.conclusion = remaining_content
                else:
                    # Short content - might be transitional, add to intro if empty
                    if not unit.intro_content:
                        unit.intro_content = remaining_content
        
        # Update position range to include all content
        if unit.position_range:
            start_pos = unit.position_range[0]
            end_pos = len(content)  # Extend to end of content
            unit.position_range = (start_pos, end_pos)
    
    def _create_comprehensive_unit(self, content: str, elements: List[Dict]) -> Optional[LearningUnit]:
        """Create a comprehensive unit when no elements are detected"""
        if len(content.strip()) < 100:
            return None
        
        unit = LearningUnit(
            unit_id=str(uuid.uuid4())[:8],
            position_range=(0, len(content))
        )
        
        # Add all content as intro
        unit.intro_content = content.strip()
        
        # Process any detected elements
        for element in elements:
            self._add_element_to_unit(unit, element, content, 0)
        
        return unit
    
    def _group_into_learning_units(self, elements: List[Dict], content: str) -> List[LearningUnit]:
        """
        Group educational elements into coherent learning units.
        This preserves pedagogical flow.
        """
        units = []
        current_unit = None
        last_position = 0
        
        for element in elements:
            # Check if this element starts a new learning unit
            if self._is_new_learning_unit(element, current_unit, content, last_position):
                if current_unit and self._is_valid_unit(current_unit):
                    units.append(current_unit)
                current_unit = LearningUnit(
                    unit_id=str(uuid.uuid4())[:8],
                    position_range=(element['position'], element['position'])
                )
            
            # Add element to current unit
            if current_unit:
                self._add_element_to_unit(current_unit, element, content, last_position)
                last_position = element.get('content_end', element['position'])
        
        # Add final unit and ensure it includes all remaining content
        if current_unit and self._is_valid_unit(current_unit):
            # Include any remaining content (like "What you have learnt")
            self._finalize_learning_unit(current_unit, content, last_position)
            units.append(current_unit)
        
        # If no units were created, create a comprehensive unit for the entire content
        if not units:
            comprehensive_unit = self._create_comprehensive_unit(content, elements)
            if comprehensive_unit:
                units.append(comprehensive_unit)
        
        return units
    
    def _is_new_learning_unit(self, element: Dict, current_unit: Optional[LearningUnit], 
                             content: str, last_position: int) -> bool:
        """Determine if an element starts a new learning unit"""
        if not current_unit:
            return True
        
        # For single chapter processing, be more conservative about splitting
        # Only create new units for major conceptual boundaries
        
        # Check for major section boundaries (like new numbered sections)
        intervening_text = content[last_position:element['position']]
        if re.search(r'\n\d+\.\d+\s+[A-Z]', intervening_text):  # New section like "7.2 Next Topic"
            return True
        
        # Check for chapter boundaries
        if re.search(r'\nChapter\s+\d+', intervening_text, re.IGNORECASE):
            return True
        
        # Check for very large gaps (more conservative threshold)
        distance = element['position'] - last_position
        if distance > 2000:  # Very significant gap
            return True
        
        # For single chapter processing, prefer keeping elements together
        # unless there's a clear pedagogical boundary
        return False
    
    def _add_element_to_unit(self, unit: LearningUnit, element: Dict, 
                            content: str, last_position: int):
        """Add an educational element to a learning unit with its context"""
        # Get introductory content if this is the first element
        if not unit.intro_content and last_position < element['position']:
            unit.intro_content = content[last_position:element['position']].strip()
        
        # Add element based on type
        if element['type'] == 'activity':
            activity_content = content[element['content_start']:element['content_end']]
            unit.activities.append({
                'number': element['number'],
                'content': activity_content,
                'position': element['position']
            })
        
        elif element['type'] == 'example':
            example_content = content[element['content_start']:element['content_end']]
            unit.examples.append({
                'number': element['number'],
                'content': example_content,
                'position': element['position']
            })
        
        elif element['type'] == 'figure':
            unit.figures.append({
                'number': element['number'],
                'caption': element.get('caption', ''),
                'position': element['position']
            })
        
        elif element['type'] == 'question':
            question_content = content[element['content_start']:element['content_end']]
            unit.questions.append({
                'text': element['question_text'],
                'content': question_content,
                'position': element['position']
            })
        
        elif element['type'] == 'formula':
            unit.formulas.append({
                'formula': element['formula'],
                'position': element['position']
            })
        
        elif element['type'] == 'special_box':
            special_box_content = content[element['content_start']:element['content_end']]
            unit.special_boxes.append({
                'type': element['box_type'],
                'content': special_box_content,
                'position': element['position']
            })
        
        elif element['type'] == 'mathematical_content':
            unit.mathematical_content.append({
                'expression': element['mathematical_expression'],
                'position': element['position']
            })
        
        elif element['type'] == 'cross_reference':
            unit.cross_references.append({
                'reference': element['reference'],
                'position': element['position']
            })
        
        elif element['type'] == 'assessment':
            assessment_content = content[element['content_start']:element['content_end']]
            unit.assessments.append({
                'type': element['assessment_type'],
                'content': assessment_content,
                'position': element['position']
            })
        
        elif element['type'] == 'pedagogical_marker':
            unit.pedagogical_markers.append({
                'type': element['marker_type'],
                'position': element['position']
            })
        
        elif element['type'] == 'concept':
            unit.concepts.append(element['concept'])
        
        # Update position range
        unit.position_range = (
            min(unit.position_range[0], element['position']),
            max(unit.position_range[1], element.get('content_end', element['position']))
        )
    
    def _is_valid_unit(self, unit: LearningUnit) -> bool:
        """Check if a learning unit has sufficient content"""
        total_content = len(unit.intro_content)
        total_content += sum(len(a['content']) for a in unit.activities)
        total_content += sum(len(e['content']) for e in unit.examples)
        
        return total_content >= self.config['min_chunk_size']
    
    async def _detect_boundaries_with_ai(self, content: str) -> Optional[Dict]:
        """Use AI to detect natural learning unit boundaries"""
        try:
            # Truncate content if too long for AI processing
            max_content_length = 4000  # Adjust based on AI model limits
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            ai_response = await ai_detect_boundaries(content)
            
            if ai_response and 'learning_units' in ai_response:
                logger.info(f"AI detected {len(ai_response['learning_units'])} learning units")
                return ai_response
            
        except Exception as e:
            logger.error(f"AI boundary detection error: {e}")
        
        return None
    
    def _create_units_from_ai_boundaries(self, ai_boundaries: Dict, content: str, mother_section: Dict) -> List[LearningUnit]:
        """Create learning units based on AI-detected boundaries"""
        learning_units = []
        
        if 'learning_units' not in ai_boundaries:
            return learning_units
        
        for i, ai_unit in enumerate(ai_boundaries['learning_units']):
            start_pos = ai_unit.get('start', 0)
            end_pos = ai_unit.get('end', len(content))
            unit_type = ai_unit.get('type', 'theory')
            description = ai_unit.get('description', '')
            educational_elements = ai_unit.get('educational_elements', [])
            
            # Extract unit content
            unit_content = content[start_pos:end_pos]
            
            # Create learning unit
            unit = LearningUnit(
                unit_id=f"ai_unit_{mother_section.get('section_number', 'unknown')}_{i+1}",
                position_range=(start_pos, end_pos)
            )
            
            # Classify and organize content based on AI analysis
            if unit_type == 'activity' or 'activity' in educational_elements:
                unit.activities.append({
                    'content': unit_content,
                    'type': 'ai_detected_activity',
                    'description': description,
                    'position': start_pos
                })
            elif unit_type == 'example' or 'example' in educational_elements:
                unit.examples.append({
                    'content': unit_content,
                    'type': 'ai_detected_example',
                    'description': description,
                    'position': start_pos
                })
            elif unit_type == 'assessment' or 'question' in educational_elements:
                unit.assessments.append({
                    'content': unit_content,
                    'type': 'ai_detected_questions',
                    'description': description,
                    'position': start_pos
                })
            else:
                # Default to intro content for theory sections
                unit.intro_content = unit_content
            
            # Extract concepts using AI if content is substantial
            if len(unit_content) > 200:
                try:
                    # Check event loop status
                    try:
                        loop = asyncio.get_running_loop()
                        logger.info("In event loop, skipping AI concept extraction")
                        ai_concepts = None
                    except RuntimeError:
                        ai_concepts = asyncio.run(ai_extract_concepts(
                            unit_content, 
                            subject=mother_section.get('subject', 'Physics'),
                            grade_level=mother_section.get('grade_level', 9)
                        ))
                    
                    if ai_concepts and 'main_concepts' in ai_concepts:
                        unit.concepts.extend(ai_concepts['main_concepts'])
                except Exception as e:
                    logger.warning(f"AI concept extraction failed: {e}")
            
            # Set educational flow based on detected elements
            if educational_elements:
                unit.educational_flow = "_".join(educational_elements)
            
            learning_units.append(unit)
        
        logger.info(f"Created {len(learning_units)} AI-powered learning units")
        return learning_units
    
    def _validate_learning_units(self, units: List[LearningUnit], 
                                mother_section: Dict) -> List[LearningUnit]:
        """Validate and refine learning units for pedagogical completeness"""
        validated_units = []
        
        for unit in units:
            # Check if unit is too small
            if self._calculate_unit_size(unit) < self.config['min_chunk_size']:
                # Try to merge with adjacent unit
                if validated_units and self._can_merge_units(validated_units[-1], unit):
                    self._merge_units(validated_units[-1], unit)
                    continue
            
            # Check if unit is too large
            if self._calculate_unit_size(unit) > self.config['max_chunk_size']:
                # Split into smaller units
                split_units = self._split_large_unit(unit)
                validated_units.extend(split_units)
                continue
            
            # Unit is valid size
            validated_units.append(unit)
        
        return validated_units
    
    def _calculate_unit_size(self, unit: LearningUnit) -> int:
        """Calculate total size of a learning unit"""
        size = len(unit.intro_content) + len(unit.conclusion)
        size += sum(len(a['content']) for a in unit.activities)
        size += sum(len(e['content']) for e in unit.examples)
        return size
    
    def _can_merge_units(self, unit1: LearningUnit, unit2: LearningUnit) -> bool:
        """Check if two units can be merged"""
        combined_size = self._calculate_unit_size(unit1) + self._calculate_unit_size(unit2)
        return combined_size <= self.config['max_chunk_size']
    
    def _merge_units(self, unit1: LearningUnit, unit2: LearningUnit):
        """Merge unit2 into unit1"""
        unit1.activities.extend(unit2.activities)
        unit1.examples.extend(unit2.examples)
        unit1.figures.extend(unit2.figures)
        unit1.questions.extend(unit2.questions)
        unit1.formulas.extend(unit2.formulas)
        unit1.special_boxes.extend(unit2.special_boxes)
        unit1.mathematical_content.extend(unit2.mathematical_content)
        unit1.cross_references.extend(unit2.cross_references)
        unit1.assessments.extend(unit2.assessments)
        unit1.pedagogical_markers.extend(unit2.pedagogical_markers)
        unit1.concepts.extend(unit2.concepts)
        if unit2.conclusion:
            unit1.conclusion = unit2.conclusion
        unit1.position_range = (
            min(unit1.position_range[0], unit2.position_range[0]),
            max(unit1.position_range[1], unit2.position_range[1])
        )
    
    def _split_large_unit(self, unit: LearningUnit) -> List[LearningUnit]:
        """Split a large unit into smaller ones while preserving coherence"""
        # This is a simplified version - in production, use more sophisticated splitting
        split_units = []
        
        # Create first unit with activities
        if unit.activities:
            unit1 = LearningUnit(
                unit_id=str(uuid.uuid4())[:8],
                intro_content=unit.intro_content,
                activities=unit.activities[:len(unit.activities)//2],
                position_range=unit.position_range
            )
            split_units.append(unit1)
        
        # Create second unit with examples
        if unit.examples:
            unit2 = LearningUnit(
                unit_id=str(uuid.uuid4())[:8],
                activities=unit.activities[len(unit.activities)//2:] if unit.activities else [],
                examples=unit.examples,
                conclusion=unit.conclusion,
                position_range=unit.position_range
            )
            split_units.append(unit2)
        
        return split_units if split_units else [unit]
    
    def _assemble_unit_content(self, learning_unit: LearningUnit) -> str:
        """Assemble content from learning unit components"""
        content_parts = []
        
        # Add introduction
        if learning_unit.intro_content:
            content_parts.append(learning_unit.intro_content)
        
        # Add activities with their full context
        for activity in learning_unit.activities:
            content_parts.append(f"\n{activity['content']}\n")
        
        # Add examples with their full context
        for example in learning_unit.examples:
            content_parts.append(f"\n{example['content']}\n")
        
        # Add special boxes
        for box in learning_unit.special_boxes:
            content_parts.append(f"\n{box.get('content', '')}\n")
        
        # Add questions
        for question in learning_unit.questions:
            content_parts.append(f"\n{question.get('text', '')}\n")
        
        # Add conclusion
        if learning_unit.conclusion:
            content_parts.append(learning_unit.conclusion)
        
        return '\n\n'.join(content_parts)
    
    def _should_split_large_chunk(self, content: str) -> bool:
        """Determine if a chunk should be split while maintaining pedagogical context"""
        # Only split if very large and has clear natural boundaries
        if len(content) < self.config['max_chunk_size'] * 1.5:  # 3000 chars
            return False
            
        # Check for natural pedagogical boundaries that allow splitting
        natural_boundaries = [
            r'\n\s*Example\s+\d+\.\d+',     # Example boundaries
            r'\n\s*Activity\s+\d+\.\d+',    # Activity boundaries  
            r'\n\s*Questions?\s*\n',        # Question sections
            r'\n\s*What you have learnt',   # Summary sections
        ]
        
        for pattern in natural_boundaries:
            if re.search(pattern, content, re.IGNORECASE):
                return True
                
        return False
    
    def _split_large_chunk_intelligently(self, learning_unit: LearningUnit) -> List[LearningUnit]:
        """Split large chunks at natural pedagogical boundaries"""
        content = learning_unit.intro_content + " " + learning_unit.conclusion
        
        if not self._should_split_large_chunk(content):
            return [learning_unit]
        
        # Find split points at natural boundaries
        split_candidates = []
        
        # Look for example boundaries
        for example in learning_unit.examples:
            if 'position' in example:
                split_candidates.append(('example', example['position'], example))
        
        # Look for activity boundaries  
        for activity in learning_unit.activities:
            if 'position' in activity:
                split_candidates.append(('activity', activity['position'], activity))
        
        # If no good split points, keep as single chunk
        if len(split_candidates) < 2:
            return [learning_unit]
        
        # Sort by position
        split_candidates.sort(key=lambda x: x[1])
        
        # Create sub-chunks at natural boundaries
        sub_units = []
        current_start = 0
        
        for i, (boundary_type, position, element) in enumerate(split_candidates):
            if i > 0:  # Skip first boundary
                # Create a sub-unit from previous boundary to this one
                sub_unit = LearningUnit(
                    intro_content=content[current_start:position],
                    conclusion="",
                    activities=[element] if boundary_type == 'activity' else [],
                    examples=[element] if boundary_type == 'example' else [],
                    figures=[],
                    questions=[],
                    formulas=[],
                    special_boxes=[],
                    mathematical_content=[],
                    cross_references=[],
                    assessments=[],
                    pedagogical_markers=[],
                    concepts=[],
                    position_range=(current_start, position)
                )
                sub_units.append(sub_unit)
                current_start = position
        
        # Add final sub-unit
        if current_start < len(content):
            final_unit = LearningUnit(
                intro_content=content[current_start:],
                conclusion="",
                activities=learning_unit.activities[-1:],  # Last activity
                examples=learning_unit.examples[-1:],      # Last example
                figures=learning_unit.figures,
                questions=learning_unit.questions,
                formulas=learning_unit.formulas,
                special_boxes=learning_unit.special_boxes,
                mathematical_content=learning_unit.mathematical_content,
                cross_references=learning_unit.cross_references,
                assessments=learning_unit.assessments,
                pedagogical_markers=learning_unit.pedagogical_markers,
                concepts=learning_unit.concepts,
                position_range=(current_start, len(content))
            )
            sub_units.append(final_unit)
        
        return sub_units if len(sub_units) > 1 else [learning_unit]
    
    def _create_contextual_chunk(self, learning_unit: LearningUnit, 
                               mother_section: Dict, char_to_page_map: Dict, 
                               sequence: int) -> HolisticChunk:
        """
        Create a single contextual chunk that preserves pedagogical flow.
        This is the key improvement over the original fragmented approach.
        """
        # Get the full content for this learning unit from the mother section
        if learning_unit.position_range:
            start_pos, end_pos = learning_unit.position_range
            # Extract the complete content for this learning unit
            full_text = mother_section.get('full_content', '')
            if full_text:
                full_unit_content = full_text[start_pos:end_pos]
            else:
                # Fallback to assembled content
                full_unit_content = self._assemble_unit_content(learning_unit)
        else:
            full_unit_content = self._assemble_unit_content(learning_unit)
        
        combined_content = full_unit_content
        
        # Create rich metadata
        metadata = self._create_rich_metadata(learning_unit, mother_section, sequence)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(learning_unit, metadata)
        
        return HolisticChunk(
            chunk_id=f"contextual_{mother_section['section_number']}_{sequence}_{uuid.uuid4().hex[:8]}",
            content=combined_content,
            metadata=metadata,
            prerequisites=[],  # To be populated in Phase 2
            related_chunks=[],  # To be populated based on content analysis
            video_connections=[],  # For future video integration
            learning_sequence={
                'position': sequence,
                'total_in_section': 0,  # To be updated
                'educational_flow': learning_unit.educational_flow
            },
            pedagogical_context={
                'has_activities': len(learning_unit.activities) > 0,
                'has_examples': len(learning_unit.examples) > 0,
                'is_complete_unit': True,
                'learning_objectives': self._extract_learning_objectives(learning_unit)
            },
            quality_score=quality_score
        )
    
    def _classify_chunk_type(self, learning_unit: LearningUnit) -> str:
        """
        Classify the chunk type based on its content composition
        """
        # Get content composition counts
        activity_count = len(learning_unit.activities)
        example_count = len(learning_unit.examples)
        figure_count = len(learning_unit.figures)
        question_count = len(learning_unit.questions)
        formula_count = len(learning_unit.formulas)
        special_box_count = len(learning_unit.special_boxes)
        assessment_count = len(learning_unit.assessments)
        
        # Analyze content text for type indicators
        full_content = (learning_unit.intro_content + " " + learning_unit.conclusion).lower()
        
        # Classification logic based on content composition
        if activity_count >= 2 or (activity_count >= 1 and len(full_content) > 1000):
            return "hands_on_activity"
        elif example_count >= 2 or (example_count >= 1 and "example" in full_content):
            return "worked_examples"
        elif question_count >= 5 or assessment_count >= 1:
            return "assessment_questions"
        elif formula_count >= 10 or "formula" in full_content or "equation" in full_content:
            return "mathematical_formulas"
        elif figure_count >= 3 or "figure" in full_content or "diagram" in full_content:
            return "visual_aids"
        elif special_box_count >= 1 or "do you know" in full_content:
            return "enrichment_content"
        elif "definition" in full_content or "concept" in full_content:
            return "conceptual_explanation"
        else:
            return "mixed_content"
    
    def _create_rich_metadata(self, learning_unit: LearningUnit, 
                            mother_section: Dict, sequence: int) -> Dict[str, Any]:
        """Create comprehensive metadata for holistic learning with advanced AI analysis"""
        
        # Get full content for advanced analysis
        full_content = self._get_full_unit_content(learning_unit)
        grade_level = mother_section.get('grade_level', 9)
        subject = mother_section.get('subject', 'Physics')
        
        # Classify the chunk type based on content composition
        chunk_type = self._classify_chunk_type(learning_unit)
        
        # Extract advanced educational metadata using AI engine
        advanced_metadata = self.metadata_engine.extract_comprehensive_metadata(
            learning_unit, full_content, grade_level, subject
        )
        
        # Enhance with AI-extracted concepts if available
        chunk_content = learning_unit.intro_content + ' '.join(a['content'] for a in learning_unit.activities) + ' '.join(e['content'] for e in learning_unit.examples)
        if self.use_ai_boundaries and len(chunk_content) > 300:
            try:
                # Check if we're in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # Skip AI enhancement if in event loop to avoid conflicts
                    logger.info("In event loop, skipping AI concept enhancement")
                    ai_concepts = None
                except RuntimeError:
                    # Safe to use asyncio.run
                    ai_concepts = asyncio.run(ai_extract_concepts(
                        chunk_content, 
                        subject=subject, 
                        grade_level=grade_level
                    ))
                if ai_concepts:
                    # Merge AI concepts with metadata engine concepts
                    if 'main_concepts' in ai_concepts:
                        existing_concepts = advanced_metadata.concepts_and_skills.get('main_concepts', [])
                        ai_main_concepts = ai_concepts['main_concepts']
                        # Combine and deduplicate concepts
                        all_concepts = list(set(existing_concepts + ai_main_concepts))
                        advanced_metadata.concepts_and_skills['main_concepts'] = all_concepts
                    
                    if 'sub_concepts' in ai_concepts:
                        existing_sub = advanced_metadata.concepts_and_skills.get('sub_concepts', [])
                        ai_sub_concepts = ai_concepts['sub_concepts']
                        all_sub_concepts = list(set(existing_sub + ai_sub_concepts))
                        advanced_metadata.concepts_and_skills['sub_concepts'] = all_sub_concepts
                    
                    # Add AI relationship data
                    if 'concept_relationships' in ai_concepts:
                        advanced_metadata.concepts_and_skills['ai_relationships'] = ai_concepts['concept_relationships']
                    
                    if 'educational_context' in ai_concepts:
                        # Enhance applications and examples with AI data
                        ai_context = ai_concepts['educational_context']
                        if 'applications' in ai_context:
                            existing_apps = advanced_metadata.pedagogical_elements.get('real_world_applications', [])
                            ai_apps = ai_context['applications']
                            all_apps = list(set(existing_apps + ai_apps))
                            advanced_metadata.pedagogical_elements['real_world_applications'] = all_apps
                        
                        if 'misconceptions' in ai_context:
                            advanced_metadata.pedagogical_elements['common_misconceptions'] = ai_context['misconceptions']
                
                logger.info(f"Enhanced metadata with AI concepts for chunk {chunk_id}")
                    
            except Exception as e:
                logger.warning(f"AI concept enhancement failed: {e}")
        
        # Combine basic metadata with advanced AI-extracted metadata
        metadata = {
            "type": chunk_type,  # Top-level type for easy access
            "basic_info": {
                "type": chunk_type,
                "grade_level": grade_level,
                "subject": subject,
                "chapter": mother_section.get('chapter', 8),
                "section": mother_section['section_number'],
                "section_title": mother_section.get('title', ''),
                "curriculum": self.config['curriculum'],
                "sequence_in_section": sequence
            },
            
            "content_composition": {
                "has_introduction": bool(learning_unit.intro_content),
                "activity_count": len(learning_unit.activities),
                "example_count": len(learning_unit.examples),
                "figure_count": len(learning_unit.figures),
                "question_count": len(learning_unit.questions),
                "formula_count": len(learning_unit.formulas),
                "special_box_count": len(learning_unit.special_boxes),
                "mathematical_content_count": len(learning_unit.mathematical_content),
                "cross_reference_count": len(learning_unit.cross_references),
                "assessment_count": len(learning_unit.assessments),
                "pedagogical_marker_count": len(learning_unit.pedagogical_markers),
                "concept_count": len(learning_unit.concepts),
                "activity_numbers": [a['number'] for a in learning_unit.activities if a.get('number')],
                "example_numbers": [e['number'] for e in learning_unit.examples if e.get('number')],
                "figure_numbers": [f['number'] for f in learning_unit.figures if f.get('number')],
                "question_texts": [q['text'][:50] + "..." if len(q['text']) > 50 else q['text'] for q in learning_unit.questions],
                "formulas": [f['formula'] for f in learning_unit.formulas],
                "special_box_types": [sb['type'] for sb in learning_unit.special_boxes],
                "mathematical_expressions": [mc['expression'][:30] + "..." if len(mc['expression']) > 30 else mc['expression'] for mc in learning_unit.mathematical_content],
                "cross_references": [cr['reference'] for cr in learning_unit.cross_references],
                "assessment_types": [a['type'] for a in learning_unit.assessments],
                "pedagogical_markers": [pm['type'] for pm in learning_unit.pedagogical_markers]
            },
            
            # Enhanced pedagogical elements with AI analysis
            "pedagogical_elements": {
                "content_types": self._identify_content_types(learning_unit),
                "learning_styles": self._identify_learning_styles(learning_unit),
                "cognitive_level": self._assess_cognitive_level(learning_unit),
                "difficulty_level": advanced_metadata.difficulty_level,  # AI-powered assessment
                "estimated_time_minutes": self._estimate_learning_time(learning_unit),
                "cognitive_levels": advanced_metadata.cognitive_levels,  # Bloom's taxonomy
                "reading_level": advanced_metadata.reading_level  # Reading complexity
            },
            
            # Enhanced concepts and skills with AI extraction
            "concepts_and_skills": {
                "main_concepts": advanced_metadata.main_concepts,  # AI-extracted
                "sub_concepts": advanced_metadata.sub_concepts,  # AI-extracted
                "concept_relationships": advanced_metadata.concept_relationships,  # AI-mapped
                "concept_definitions": advanced_metadata.concept_definitions,  # AI-extracted
                "skills_developed": advanced_metadata.skills_developed,  # AI-analyzed
                "competencies": advanced_metadata.competencies,  # Educational competencies
                "prerequisite_concepts": advanced_metadata.prerequisite_concepts,  # Cross-grade mapping
                "learning_objectives": advanced_metadata.learning_objectives,  # AI-extracted
                "explicit_objectives": advanced_metadata.explicit_objectives,  # Found in text
                "implicit_objectives": advanced_metadata.implicit_objectives,  # Inferred by AI
                "keywords": self._extract_keywords(learning_unit)
            },
            
            # Enhanced educational context
            "educational_context": {
                "common_misconceptions": advanced_metadata.common_misconceptions,  # AI-identified
                "real_world_applications": advanced_metadata.real_world_applications,  # AI-extracted
                "career_connections": advanced_metadata.career_connections,  # Subject-specific
                "historical_context": advanced_metadata.historical_context,  # Background info
                "assessment_objectives": advanced_metadata.assessment_objectives  # What to assess
            },
            
            "cross_references": {
                "internal_figures": learning_unit.figures,
                "referenced_sections": self._find_section_references(learning_unit),
                "referenced_equations": self._find_equation_references(learning_unit)
            },
            
            # Enhanced quality indicators with AI metrics
            "quality_indicators": {
                "completeness": self._assess_completeness(learning_unit),
                "coherence": self._assess_coherence(learning_unit),
                "pedagogical_soundness": self._assess_pedagogical_soundness(learning_unit),
                "content_depth": advanced_metadata.content_depth,  # AI-calculated
                "pedagogical_completeness": advanced_metadata.pedagogical_completeness,  # AI-assessed
                "conceptual_clarity": advanced_metadata.conceptual_clarity,  # AI-evaluated
                "engagement_level": advanced_metadata.engagement_level  # AI-measured
            }
        }
        
        return metadata
    
    def _get_full_unit_content(self, learning_unit: LearningUnit) -> str:
        """Get full content from learning unit for AI analysis"""
        content_parts = []
        
        # Add intro content
        if learning_unit.intro_content:
            content_parts.append(learning_unit.intro_content)
        
        # Add activities
        for activity in learning_unit.activities:
            if 'content' in activity:
                content_parts.append(activity['content'])
        
        # Add examples
        for example in learning_unit.examples:
            if 'content' in example:
                content_parts.append(example['content'])
        
        # Add special boxes
        for box in learning_unit.special_boxes:
            if 'content' in box:
                content_parts.append(box['content'])
        
        # Add questions
        for question in learning_unit.questions:
            if 'text' in question:
                content_parts.append(question['text'])
        
        # Add formulas
        for formula in learning_unit.formulas:
            if 'formula' in formula:
                content_parts.append(formula['formula'])
        
        # Add mathematical content
        for math_content in learning_unit.mathematical_content:
            if 'expression' in math_content:
                content_parts.append(math_content['expression'])
        
        # Add conclusion
        if learning_unit.conclusion:
            content_parts.append(learning_unit.conclusion)
        
        return '\n\n'.join(content_parts)
    
    def _identify_content_types(self, unit: LearningUnit) -> List[str]:
        """Identify types of content in the learning unit"""
        types = []
        if unit.intro_content:
            types.append("conceptual_explanation")
        if unit.activities:
            types.append("hands_on_activity")
        if unit.examples:
            types.append("worked_examples")
        if unit.figures:
            types.append("visual_aids")
        if unit.questions:
            types.append("assessment_questions")
        if unit.formulas:
            types.append("mathematical_formulas")
        if unit.special_boxes:
            types.append("enrichment_content")
        if unit.mathematical_content:
            types.append("mathematical_expressions")
        if unit.cross_references:
            types.append("connected_learning")
        if unit.assessments:
            types.append("assessment_activities")
        if unit.pedagogical_markers:
            types.append("learning_objectives")
        return types
    
    def _identify_learning_styles(self, unit: LearningUnit) -> List[str]:
        """Identify learning styles addressed by the unit"""
        styles = []
        if unit.activities:
            styles.append("kinesthetic")
        if unit.figures:
            styles.append("visual")
        if unit.examples or unit.formulas or unit.mathematical_content:
            styles.append("logical_mathematical")
        if unit.questions or unit.assessments:
            styles.append("analytical")
        if unit.intro_content and len(unit.intro_content) > 200:
            styles.append("verbal_linguistic")
        if unit.special_boxes:
            styles.append("exploratory")
        if unit.cross_references:
            styles.append("connective")
        return styles
    
    def _assess_cognitive_level(self, unit: LearningUnit) -> str:
        """Assess cognitive level using Bloom's taxonomy"""
        # Simplified assessment - in production, use more sophisticated analysis
        if any(keyword in str(unit).lower() for keyword in ['analyze', 'evaluate', 'create']):
            return "higher_order"
        elif any(keyword in str(unit).lower() for keyword in ['apply', 'demonstrate', 'solve']):
            return "application"
        else:
            return "understanding"
    
    def _assess_difficulty_level(self, unit: LearningUnit) -> str:
        """Assess difficulty level of the content"""
        # Simple heuristic - can be enhanced with AI
        complexity_score = 0
        
        # Check for mathematical content
        if re.search(r'[∫∑∏√]', str(unit)):
            complexity_score += 2
        
        # Check for multi-step procedures
        if len(unit.examples) > 2:
            complexity_score += 1
        
        # Check content length
        if self._calculate_unit_size(unit) > 1500:
            complexity_score += 1
        
        if complexity_score >= 3:
            return "advanced"
        elif complexity_score >= 1:
            return "intermediate"
        else:
            return "beginner"
    
    def _estimate_learning_time(self, unit: LearningUnit) -> int:
        """Estimate time needed to complete the learning unit"""
        # Base reading time (200 words per minute)
        word_count = self._calculate_unit_size(unit) // 5
        reading_time = word_count // 200
        
        # Add time for activities (15 minutes each)
        activity_time = len(unit.activities) * 15
        
        # Add time for examples (5 minutes each)
        example_time = len(unit.examples) * 5
        
        return reading_time + activity_time + example_time
    
    def _identify_skills(self, unit: LearningUnit) -> List[str]:
        """Identify skills developed through the unit"""
        skills = []
        
        if unit.activities:
            skills.extend(["experimentation", "observation", "data_collection"])
        
        if unit.examples:
            skills.extend(["problem_solving", "calculation", "application"])
        
        if unit.activities and any('measure' in str(a).lower() for a in unit.activities):
            skills.append("measurement")
        
        unit_str = str(unit)
        if 'graph' in unit_str.lower() or 'plot' in unit_str.lower():
            skills.append("data_visualization")
        
        return list(set(skills))
    
    def _extract_learning_objectives(self, unit: LearningUnit) -> List[str]:
        """Extract or infer learning objectives"""
        objectives = []
        
        # Look for explicit objectives
        objective_patterns = [
            r'(?:After this (?:activity|section|lesson), you will be able to:?\s*)([^.]+)',
            r'(?:Learning objectives?:?\s*)([^.]+)',
            r'(?:By the end of this (?:activity|section), students will:?\s*)([^.]+)'
        ]
        
        combined_text = str(unit)
        for pattern in objective_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            objectives.extend(matches)
        
        # Infer objectives from content if none found
        if not objectives:
            if unit.activities:
                objectives.append(f"Understand through hands-on experimentation")
            if unit.examples:
                objectives.append(f"Apply concepts through problem-solving")
            if unit.concepts:
                objectives.append(f"Understand key concepts: {', '.join(unit.concepts[:3])}")
        
        return objectives
    
    def _extract_keywords(self, unit: LearningUnit) -> List[str]:
        """Extract key terms and concepts"""
        # This is a simplified version - in production, use NLP techniques
        keywords = set(unit.concepts)
        
        # Add technical terms
        technical_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Capitalized terms
            r'\b(\w+force|\w+motion|\w+energy)\b',  # Domain-specific terms
        ]
        
        combined_text = str(unit)
        for pattern in technical_patterns:
            matches = re.findall(pattern, combined_text)
            keywords.update(matches)
        
        return list(keywords)[:10]  # Limit to top 10
    
    def _find_section_references(self, unit: LearningUnit) -> List[str]:
        """Find references to other sections"""
        references = []
        combined_text = str(unit)
        
        # Look for section references
        section_refs = re.findall(r'(?:Section|section)\s+(\d+\.\d+)', combined_text)
        references.extend(section_refs)
        
        # Look for chapter references
        chapter_refs = re.findall(r'(?:Chapter|chapter)\s+(\d+)', combined_text)
        references.extend([f"Chapter {ref}" for ref in chapter_refs])
        
        return list(set(references))
    
    def _find_equation_references(self, unit: LearningUnit) -> List[str]:
        """Find equation references"""
        combined_text = str(unit)
        equations = re.findall(r'(?:Equation|equation|Eq\.?)\s*\(?(\d+\.\d+)\)?', combined_text)
        return list(set(equations))
    
    def _assess_completeness(self, unit: LearningUnit) -> float:
        """Assess how complete the learning unit is"""
        score = 0.0
        
        if unit.intro_content:
            score += 0.2
        if unit.activities:
            score += 0.3
        if unit.examples:
            score += 0.3
        if unit.conclusion:
            score += 0.1
        if unit.concepts:
            score += 0.1
        
        return min(score, 1.0)
    
    def _assess_coherence(self, unit: LearningUnit) -> float:
        """Assess the coherence of the learning unit"""
        # Check if elements reference each other
        coherence_score = 0.8  # Base score
        
        # Check if activities are referenced in intro
        if unit.activities and unit.intro_content:
            for activity in unit.activities:
                if activity.get('number') and activity['number'] in unit.intro_content:
                    coherence_score += 0.05
        
        # Check if examples build on activities
        if unit.examples and unit.activities:
            coherence_score += 0.1
        
        return min(coherence_score, 1.0)
    
    def _assess_pedagogical_soundness(self, unit: LearningUnit) -> float:
        """Assess pedagogical quality"""
        score = 0.7  # Base score
        
        # Check for proper learning sequence
        if unit.intro_content and (unit.activities or unit.examples):
            score += 0.1
        
        # Check for variety in learning approaches
        if unit.activities and unit.examples:
            score += 0.1
        
        # Check for conceptual clarity
        if unit.concepts:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_quality_score(self, unit: LearningUnit, metadata: Dict) -> float:
        """Calculate overall quality score for the chunk"""
        completeness = metadata['quality_indicators']['completeness']
        coherence = metadata['quality_indicators']['coherence']
        soundness = metadata['quality_indicators']['pedagogical_soundness']
        
        # Weighted average
        quality_score = (completeness * 0.3 + coherence * 0.3 + soundness * 0.4)
        
        return round(quality_score, 2)
    
    def _extract_residual_content(self, mother_content: str, used_positions: List[Tuple[int, int]]) -> str:
        """
        FIXED: Properly extract content that hasn't been included in any chunk.
        This fixes the critical bug in the original implementation.
        """
        if not used_positions:
            return mother_content
        
        # Sort positions by start index
        sorted_positions = sorted(used_positions, key=lambda x: x[0])
        
        # Merge overlapping positions
        merged_positions = []
        for start, end in sorted_positions:
            if merged_positions and start <= merged_positions[-1][1]:
                # Overlapping - extend the previous range
                merged_positions[-1] = (merged_positions[-1][0], max(merged_positions[-1][1], end))
            else:
                # Non-overlapping - add new range
                merged_positions.append((start, end))
        
        # Extract residual content
        residual_parts = []
        current_pos = 0
        
        for start, end in merged_positions:
            if current_pos < start:
                # Add content before this used section
                residual_part = mother_content[current_pos:start].strip()
                if residual_part:
                    residual_parts.append(residual_part)
            current_pos = max(current_pos, end)
        
        # Add any remaining content after the last used position
        if current_pos < len(mother_content):
            residual_part = mother_content[current_pos:].strip()
            if residual_part:
                residual_parts.append(residual_part)
        
        # Join residual parts with proper spacing
        residual_content = '\n\n'.join(residual_parts)
        
        # Log what was extracted
        logger.info(f"Extracted {len(residual_content)} characters of residual content from {len(mother_content)} total")
        
        return residual_content


class PrerequisiteMapper:
    """
    Handles cross-grade prerequisite mapping for holistic learning.
    This is a new component not present in the original system.
    """
    
    def __init__(self):
        self.concept_hierarchy = {}
        self.prerequisite_map = {}
        self.grade_progression = {}
        
    def analyze_cross_grade_prerequisites(self, chunks_by_grade: Dict[int, List[HolisticChunk]]) -> Dict:
        """
        Analyze chunks across grades 4-10 to build prerequisite map.
        This enables adaptive learning and prerequisite checking.
        """
        # Extract concepts by grade
        for grade, chunks in chunks_by_grade.items():
            self.grade_progression[grade] = self._extract_grade_concepts(chunks)
        
        # Build prerequisite relationships
        for grade in range(5, 11):  # Start from grade 5
            current_concepts = self.grade_progression.get(grade, {})
            
            for concept, concept_info in current_concepts.items():
                prerequisites = self._find_concept_prerequisites(
                    concept, concept_info, max_grade=grade-1
                )
                
                self.prerequisite_map[f"{grade}_{concept}"] = {
                    'concept': concept,
                    'grade': grade,
                    'prerequisites': prerequisites,
                    'builds_toward': self._find_future_concepts(concept, min_grade=grade+1)
                }
        
        return self.prerequisite_map
    
    def _extract_grade_concepts(self, chunks: List[HolisticChunk]) -> Dict:
        """Extract key concepts from chunks for a specific grade"""
        concepts = {}
        
        for chunk in chunks:
            chunk_concepts = chunk.metadata.get('concepts_and_skills', {}).get('main_concepts', [])
            
            for concept in chunk_concepts:
                if concept not in concepts:
                    concepts[concept] = {
                        'occurrences': 0,
                        'contexts': [],
                        'related_topics': set(),
                        'skills': set()
                    }
                
                concepts[concept]['occurrences'] += 1
                concepts[concept]['contexts'].append(chunk.chunk_id)
                
                # Add related topics from the same chunk
                related = chunk.metadata.get('concepts_and_skills', {}).get('keywords', [])
                concepts[concept]['related_topics'].update(related)
                
                # Add associated skills
                skills = chunk.metadata.get('concepts_and_skills', {}).get('skills_developed', [])
                concepts[concept]['skills'].update(skills)
        
        return concepts
    
    def _find_concept_prerequisites(self, concept: str, concept_info: Dict, max_grade: int) -> List[Dict]:
        """Find prerequisite concepts for a given concept"""
        prerequisites = []
        
        # Define conceptual relationships (this would be enhanced with AI in production)
        prerequisite_patterns = {
            'force': ['motion', 'push', 'pull'],
            'acceleration': ['velocity', 'speed', 'motion'],
            'velocity': ['speed', 'direction', 'motion'],
            'energy': ['work', 'force', 'motion'],
            'momentum': ['mass', 'velocity', 'motion'],
            'pressure': ['force', 'area'],
            'density': ['mass', 'volume'],
            'electric current': ['charge', 'electrons', 'conductor'],
            'magnetic field': ['magnet', 'force', 'poles'],
            'chemical reaction': ['elements', 'compounds', 'atoms']
        }
        
        # Look for prerequisites
        concept_lower = concept.lower()
        potential_prereqs = prerequisite_patterns.get(concept_lower, [])
        
        # Search in earlier grades
        for grade in range(4, max_grade + 1):
            grade_concepts = self.grade_progression.get(grade, {})
            
            for grade_concept, grade_concept_info in grade_concepts.items():
                grade_concept_lower = grade_concept.lower()
                
                # Check if this is a prerequisite
                is_prerequisite = False
                strength = 0.0
                
                # Direct match
                if grade_concept_lower in potential_prereqs:
                    is_prerequisite = True
                    strength = 0.9
                
                # Partial match
                elif any(prereq in grade_concept_lower for prereq in potential_prereqs):
                    is_prerequisite = True
                    strength = 0.7
                
                # Semantic similarity (simplified)
                elif self._concepts_related(grade_concept, concept):
                    is_prerequisite = True
                    strength = 0.5
                
                if is_prerequisite:
                    prerequisites.append({
                        'concept': grade_concept,
                        'grade': grade,
                        'strength': strength,
                        'relationship_type': self._classify_relationship(grade_concept, concept),
                        'contexts': grade_concept_info.get('contexts', [])[:3]  # Top 3 contexts
                    })
        
        # Sort by grade and strength
        prerequisites.sort(key=lambda x: (x['grade'], x['strength']), reverse=True)
        
        return prerequisites
    
    def _find_future_concepts(self, concept: str, min_grade: int) -> List[Dict]:
        """Find concepts that build upon the current concept"""
        future_concepts = []
        
        # Search in later grades
        for grade in range(min_grade, 11):
            grade_concepts = self.grade_progression.get(grade, {})
            
            for future_concept, future_info in grade_concepts.items():
                # Check if current concept is a prerequisite for future concept
                if self._is_prerequisite_for(concept, future_concept):
                    future_concepts.append({
                        'concept': future_concept,
                        'grade': grade,
                        'relationship_type': self._classify_relationship(concept, future_concept)
                    })
        
        return future_concepts
    
    def _concepts_related(self, concept1: str, concept2: str) -> bool:
        """Check if two concepts are semantically related"""
        # Simplified check - in production, use word embeddings or AI
        c1_words = set(concept1.lower().split())
        c2_words = set(concept2.lower().split())
        
        # Check for common words
        common = c1_words.intersection(c2_words)
        if common:
            return True
        
        # Check for known relationships
        related_terms = {
            'force': {'push', 'pull', 'newton', 'dynamics'},
            'motion': {'movement', 'velocity', 'speed', 'kinematic'},
            'energy': {'work', 'power', 'kinetic', 'potential'},
            'light': {'optics', 'ray', 'reflection', 'refraction'},
            'electricity': {'current', 'voltage', 'circuit', 'charge'},
            'heat': {'temperature', 'thermal', 'calorie', 'conduction'}
        }
        
        for base_term, related in related_terms.items():
            if base_term in c1_words and any(term in c2_words for term in related):
                return True
            if base_term in c2_words and any(term in c1_words for term in related):
                return True
        
        return False
    
    def _is_prerequisite_for(self, prereq_concept: str, target_concept: str) -> bool:
        """Check if prereq_concept is a prerequisite for target_concept"""
        # This is the inverse of _find_concept_prerequisites logic
        # Simplified version - enhance with AI in production
        prereq_lower = prereq_concept.lower()
        target_lower = target_concept.lower()
        
        # Known progressions
        progressions = {
            'motion': ['velocity', 'acceleration', 'momentum'],
            'force': ['work', 'energy', 'power'],
            'speed': ['velocity', 'acceleration'],
            'atoms': ['molecules', 'compounds', 'reactions'],
            'cells': ['tissues', 'organs', 'systems']
        }
        
        for base, progression in progressions.items():
            if base in prereq_lower:
                return any(prog in target_lower for prog in progression)
        
        return False
    
    def _classify_relationship(self, concept1: str, concept2: str) -> str:
        """Classify the type of relationship between concepts"""
        c1_lower = concept1.lower()
        c2_lower = concept2.lower()
        
        # Check for specific relationship types
        if 'force' in c1_lower and 'motion' in c2_lower:
            return 'cause_effect'
        elif any(term in c1_lower for term in ['basic', 'simple']) and \
             any(term in c2_lower for term in ['advanced', 'complex']):
            return 'simple_to_complex'
        elif len(c2_lower.split()) > len(c1_lower.split()):
            return 'generalization'
        else:
            return 'related_concept'
    
    def get_prerequisites_for_chunk(self, chunk: HolisticChunk) -> List[Dict]:
        """Get prerequisites for a specific chunk"""
        prerequisites = []
        
        # Get concepts from chunk
        chunk_concepts = chunk.metadata.get('concepts_and_skills', {}).get('main_concepts', [])
        grade = chunk.metadata.get('basic_info', {}).get('grade_level', 9)
        
        # Find prerequisites for each concept
        for concept in chunk_concepts:
            concept_key = f"{grade}_{concept}"
            if concept_key in self.prerequisite_map:
                prerequisites.extend(self.prerequisite_map[concept_key]['prerequisites'])
        
        # Remove duplicates and sort by relevance
        unique_prerequisites = {}
        for prereq in prerequisites:
            key = f"{prereq['grade']}_{prereq['concept']}"
            if key not in unique_prerequisites or prereq['strength'] > unique_prerequisites[key]['strength']:
                unique_prerequisites[key] = prereq
        
        return list(unique_prerequisites.values())


def demonstrate_holistic_system():
    """Demonstrate the improved holistic RAG system"""
    print("🚀 Holistic Educational RAG System - Demonstration")
    print("=" * 60)
    
    # Initialize system
    chunker = HolisticRAGChunker()
    prereq_mapper = PrerequisiteMapper()
    
    # Example mother section
    mother_section = {
        'section_number': '8.1',
        'title': 'Force and Motion',
        'start_pos': 0,
        'end_pos': 5000,
        'grade_level': 9,
        'subject': 'Physics',
        'chapter': 8
    }
    
    # Example content that would have been fragmented in original system
    sample_content = """
    8.1 Force and Motion
    
    When we push or pull an object, we are applying a force on it. Force can change 
    the state of motion of an object. Let's understand this through an activity.
    
    ACTIVITY 8.1
    Take a ball and place it on a table. Push the ball gently with your finger. 
    What do you observe? The ball starts moving in the direction of the push.
    Now, while the ball is moving, give it another push in the same direction.
    What happens? The ball moves faster. This shows that force can change the
    speed of a moving object.
    
    From this activity, we learn that force can:
    - Start motion in a stationary object
    - Change the speed of a moving object
    - Change the direction of motion
    
    Example 8.1
    A force of 10 N is applied to a box of mass 2 kg resting on a smooth surface.
    Calculate the acceleration of the box.
    
    Solution: Using Newton's second law, F = ma
    Given: F = 10 N, m = 2 kg
    Therefore, a = F/m = 10/2 = 5 m/s²
    
    The acceleration of the box is 5 m/s².
    
    This example demonstrates how we can calculate the effect of force on motion
    using mathematical relationships. The same principle applies to all objects,
    whether they are balls, boxes, or vehicles.
    """
    
    # Process with holistic system
    print("\n📚 Processing educational content...")
    chunks = chunker.process_mother_section(
        mother_section=mother_section,
        full_text=sample_content,
        char_to_page_map={i: 1 for i in range(len(sample_content))}
    )
    
    print(f"\n✅ Created {len(chunks)} contextual chunks")
    
    # Display results
    for i, chunk in enumerate(chunks, 1):
        print(f"\n{'='*60}")
        print(f"📋 Contextual Chunk {i}")
        print(f"{'='*60}")
        print(f"ID: {chunk.chunk_id}")
        print(f"Quality Score: {chunk.quality_score}")
        print(f"\n📝 Content Preview:")
        print(chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content)
        print(f"\n📊 Metadata Highlights:")
        print(f"- Grade Level: {chunk.metadata['basic_info']['grade_level']}")
        print(f"- Activities: {chunk.metadata['content_composition']['activity_count']}")
        print(f"- Examples: {chunk.metadata['content_composition']['example_count']}")
        print(f"- Learning Styles: {chunk.metadata['pedagogical_elements']['learning_styles']}")
        print(f"- Estimated Time: {chunk.metadata['pedagogical_elements']['estimated_time_minutes']} minutes")
        print(f"- Main Concepts: {chunk.metadata['concepts_and_skills']['main_concepts']}")
        print(f"\n✨ Key Improvement: Activity and Example stay together with context!")
    
    print(f"\n{'='*60}")
    print("🎯 System Improvements Summary")
    print(f"{'='*60}")
    print("✅ Fixed residual content extraction - no more duplication")
    print("✅ Contextual chunks preserve pedagogical flow")
    print("✅ Activities and examples remain with their explanatory content")
    print("✅ Rich metadata enables prerequisite mapping")
    print("✅ Ready for AI-powered enhancements")
    
    return chunks


if __name__ == "__main__":
    # Run demonstration
    chunks = demonstrate_holistic_system()