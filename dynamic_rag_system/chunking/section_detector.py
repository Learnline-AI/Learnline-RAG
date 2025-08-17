"""
Section Detector - Enhanced hierarchical section detection.

Migrated from NCERTHierarchicalChunker with improvements:
- Configurable pattern library
- Better boundary detection
- Enhanced validation and confidence scoring
- Support for multiple document types
"""

import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

from ..core.models import SourceDocument, MotherSection, DocumentID
from ..core.config import get_config
from ..core.exceptions import SectionDetectionError, EducationalContentError
from .pattern_library import PatternLibrary, PatternType
from ..ingestion.pdf_processor import PDFExtractionResult

logger = logging.getLogger(__name__)


@dataclass
class SectionHeader:
    """Detected section header with metadata"""
    section_number: str
    section_title: str
    position: int
    end_position: int
    page_number: int
    confidence: float
    pattern_used: str
    full_match: str


@dataclass
class SpecialContentItem:
    """Detected special content (activity, figure, etc.)"""
    content_type: str  # 'activity', 'figure', 'example', etc.
    identifier: str    # e.g., '8.1', 'Fig. 8.2'
    position_in_section: int
    absolute_position: int
    text_preview: str
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class SectionBoundary:
    """Complete section with boundaries and special content"""
    section_id: str
    section_number: str
    section_title: str
    start_pos: int
    end_pos: int
    content_length: int
    word_count: int
    page_number: int
    confidence: float
    special_content: Dict[str, List[SpecialContentItem]]
    content_preview: str


class SectionDetector:
    """
    Enhanced hierarchical section detector for educational content.
    
    PRESERVED: All working detection logic from original NCERTHierarchicalChunker
    ENHANCED: Configurable patterns, better validation, multi-document support
    """
    
    def __init__(self, 
                 pattern_library: PatternLibrary = None,
                 document: SourceDocument = None):
        self.config = get_config()
        self.pattern_library = pattern_library or PatternLibrary()
        self.document = document
        
        # Detection thresholds
        self.confidence_threshold = self.config.processing.confidence_threshold
        self.merge_threshold = 80  # Characters to merge nearby sections
        
        # Statistics tracking
        self.detection_stats = {
            "sections_found": 0,
            "activities_found": 0,
            "examples_found": 0,
            "figures_found": 0,
            "special_boxes_found": 0,
            "processing_time": 0.0
        }
    
    def detect_sections(self, 
                       extraction_result: PDFExtractionResult) -> List[MotherSection]:
        """
        Main entry point for section detection.
        
        Args:
            extraction_result: Result from PDF text extraction
            
        Returns:
            List of MotherSection objects with boundaries and special content
        """
        start_time = datetime.now()
        
        try:
            text = extraction_result.full_text
            char_to_page_map = extraction_result.char_to_page_map
            
            logger.info(f"Starting section detection on {len(text)} characters")
            
            # Phase 1: Detect section headers
            section_headers = self._detect_section_headers(text, char_to_page_map)
            logger.info(f"Found {len(section_headers)} section headers")
            
            # Phase 2: Create section boundaries
            section_boundaries = self._create_section_boundaries(section_headers, text)
            logger.info(f"Created {len(section_boundaries)} section boundaries")
            
            # Phase 3: Detect special content within each section
            for boundary in section_boundaries:
                boundary.special_content = self._detect_special_content_in_section(
                    text[boundary.start_pos:boundary.end_pos],
                    boundary.start_pos
                )
            
            # Phase 4: Add intro and end matter
            enhanced_boundaries = self._add_intro_and_end_matter(
                section_boundaries, text, char_to_page_map
            )
            
            # Phase 5: Convert to MotherSection objects
            mother_sections = self._convert_to_mother_sections(
                enhanced_boundaries, extraction_result.document
            )
            
            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.detection_stats.update({
                "sections_found": len(mother_sections),
                "processing_time": processing_time
            })
            
            logger.info(f"Section detection complete: {len(mother_sections)} sections in {processing_time:.1f}s")
            return mother_sections
            
        except Exception as e:
            logger.error(f"Section detection failed: {e}", exc_info=True)
            raise SectionDetectionError(f"Failed to detect sections: {e}")
    
    def _detect_section_headers(self, 
                               text: str, 
                               char_to_page_map: Dict[int, int]) -> List[SectionHeader]:
        """
        Detect section headers using pattern library.
        
        PRESERVED: Core logic from original _detect_section_headers
        ENHANCED: Uses configurable pattern library
        """
        section_headers = []
        
        # Get section header patterns
        patterns_and_matches = self.pattern_library.find_matches(
            text, 
            PatternType.SECTION_HEADER,
            self.document,
            self.confidence_threshold
        )
        
        for pattern, match, confidence in patterns_and_matches:
            section_number = match.group(1)
            section_title = match.group(2).strip()
            
            # Additional confidence calculation based on context
            final_confidence = self._calculate_section_confidence(match, text, confidence)
            
            page_num = char_to_page_map.get(match.start(), 1)
            
            header = SectionHeader(
                section_number=section_number,
                section_title=section_title,
                position=match.start(),
                end_position=match.end(),
                page_number=page_num,
                confidence=final_confidence,
                pattern_used=pattern.pattern_id,
                full_match=match.group(0).strip()
            )
            
            section_headers.append(header)
            logger.debug(f"Section {section_number}: {section_title} (page {page_num}, confidence {final_confidence:.2f})")
        
        # Sort by position and remove duplicates
        section_headers.sort(key=lambda x: x.position)
        return self._remove_duplicate_sections(section_headers)
    
    def _create_section_boundaries(self, 
                                  section_headers: List[SectionHeader], 
                                  text: str) -> List[SectionBoundary]:
        """
        Create section boundaries from headers.
        
        PRESERVED: Logic from original _create_section_boundary_map
        """
        section_boundaries = []
        
        for i, header in enumerate(section_headers):
            start_pos = header.position
            
            # Determine end position
            if i + 1 < len(section_headers):
                end_pos = section_headers[i + 1].position
            else:
                end_pos = len(text)
            
            # Extract section content
            section_content = text[start_pos:end_pos].strip()
            
            boundary = SectionBoundary(
                section_id=f"{header.section_number}_{start_pos}",
                section_number=header.section_number,
                section_title=header.section_title,
                start_pos=start_pos,
                end_pos=end_pos,
                content_length=len(section_content),
                word_count=len(section_content.split()),
                page_number=header.page_number,
                confidence=header.confidence,
                special_content={},
                content_preview=section_content[:200] + "..." if len(section_content) > 200 else section_content
            )
            
            section_boundaries.append(boundary)
            logger.debug(f"Section {header.section_number}: {len(section_content)} chars, {boundary.word_count} words")
        
        return section_boundaries
    
    def _detect_special_content_in_section(self, 
                                          section_content: str, 
                                          section_start_pos: int) -> Dict[str, List[SpecialContentItem]]:
        """
        Detect activities, examples, figures, and special boxes within a section.
        
        ENHANCED: Uses pattern library with deduplication and content vs reference filtering
        """
        special_content = {
            'activities': [],
            'figures': [],
            'examples': [],
            'special_boxes': [],
            'mathematical_content': []
        }
        
        # Detect activities with deduplication
        activities = self._detect_activities(section_content, section_start_pos)
        special_content['activities'] = activities
        self.detection_stats["activities_found"] += len(activities)
        
        # Detect figures (content only, not references)
        figures = self._detect_figures(section_content, section_start_pos)
        special_content['figures'] = figures
        self.detection_stats["figures_found"] += len(figures)
        
        # Detect examples
        examples = self._detect_examples(section_content, section_start_pos)
        special_content['examples'] = examples
        self.detection_stats["examples_found"] += len(examples)
        
        # Detect special boxes
        special_boxes = self._detect_special_boxes(section_content, section_start_pos)
        special_content['special_boxes'] = special_boxes
        self.detection_stats["special_boxes_found"] += len(special_boxes)
        
        # Detect mathematical content
        math_content = self._detect_mathematical_content(section_content, section_start_pos)
        special_content['mathematical_content'] = math_content
        
        return special_content
    
    def _detect_activities(self, 
                          section_content: str, 
                          section_start_pos: int) -> List[SpecialContentItem]:
        """Detect activities with deduplication"""
        activities = []
        seen_activities = set()
        
        patterns_and_matches = self.pattern_library.find_matches(
            section_content,
            PatternType.ACTIVITY,
            self.document
        )
        
        for pattern, match, confidence in patterns_and_matches:
            activity_number = match.group(1)
            position = match.start()
            
            # Deduplication: Only keep if we haven't seen this activity number at similar position
            position_key = f"{activity_number}_{position//100}"  # Group by ~100 char windows
            
            if position_key not in seen_activities:
                seen_activities.add(position_key)
                
                activity = SpecialContentItem(
                    content_type='activity',
                    identifier=activity_number,
                    position_in_section=position,
                    absolute_position=section_start_pos + position,
                    text_preview=section_content[position:position+150].strip(),
                    confidence=confidence,
                    metadata={
                        'pattern_used': pattern.pattern_id,
                        'full_match': match.group(0)
                    }
                )
                activities.append(activity)
        
        return activities
    
    def _detect_figures(self, 
                       section_content: str, 
                       section_start_pos: int) -> List[SpecialContentItem]:
        """Detect figure content (not references)"""
        figures = []
        seen_figures = set()
        
        # Only use content patterns, not reference patterns
        patterns_and_matches = self.pattern_library.find_matches(
            section_content,
            PatternType.FIGURE_CONTENT,
            self.document
        )
        
        for pattern, match, confidence in patterns_and_matches:
            figure_number = match.group(1)
            figure_caption = match.group(2) if len(match.groups()) >= 2 else ""
            position = match.start()
            
            if figure_number not in seen_figures:
                seen_figures.add(figure_number)
                
                figure = SpecialContentItem(
                    content_type='figure',
                    identifier=figure_number,
                    position_in_section=position,
                    absolute_position=section_start_pos + position,
                    text_preview=figure_caption.strip()[:150],
                    confidence=confidence,
                    metadata={
                        'caption': figure_caption.strip(),
                        'has_description': bool(figure_caption.strip()),
                        'is_content': True,
                        'pattern_used': pattern.pattern_id
                    }
                )
                figures.append(figure)
        
        # Count and filter out references for logging
        reference_patterns = self.pattern_library.find_matches(
            section_content,
            PatternType.FIGURE_REFERENCE,
            self.document
        )
        
        if reference_patterns:
            logger.debug(f"Filtered out {len(reference_patterns)} figure references (keeping only content)")
        
        return figures
    
    def _detect_examples(self, 
                        section_content: str, 
                        section_start_pos: int) -> List[SpecialContentItem]:
        """Detect examples"""
        examples = []
        
        patterns_and_matches = self.pattern_library.find_matches(
            section_content,
            PatternType.EXAMPLE,
            self.document
        )
        
        for pattern, match, confidence in patterns_and_matches:
            example_number = match.group(1)
            position = match.start()
            
            example = SpecialContentItem(
                content_type='example',
                identifier=example_number,
                position_in_section=position,
                absolute_position=section_start_pos + position,
                text_preview=section_content[position:position+150].strip(),
                confidence=confidence,
                metadata={
                    'pattern_used': pattern.pattern_id,
                    'full_match': match.group(0)
                }
            )
            examples.append(example)
        
        return examples
    
    def _detect_special_boxes(self, 
                             section_content: str, 
                             section_start_pos: int) -> List[SpecialContentItem]:
        """Detect special boxes (biographies, notes, summaries)"""
        special_boxes = []
        
        patterns_and_matches = self.pattern_library.find_matches(
            section_content,
            PatternType.SPECIAL_BOX,
            self.document
        )
        
        for pattern, match, confidence in patterns_and_matches:
            position = match.start()
            
            box = SpecialContentItem(
                content_type='special_box',
                identifier=match.group(0)[:20],  # Use first 20 chars as identifier
                position_in_section=position,
                absolute_position=section_start_pos + position,
                text_preview=match.group(0)[:100].strip(),
                confidence=confidence,
                metadata={
                    'box_type': self._classify_special_box(match.group(0)),
                    'pattern_used': pattern.pattern_id,
                    'full_match': match.group(0)
                }
            )
            special_boxes.append(box)
        
        return special_boxes
    
    def _detect_mathematical_content(self, 
                                   section_content: str, 
                                   section_start_pos: int) -> List[SpecialContentItem]:
        """Detect mathematical content"""
        math_content = []
        
        patterns_and_matches = self.pattern_library.find_matches(
            section_content,
            PatternType.MATHEMATICAL,
            self.document
        )
        
        for pattern, match, confidence in patterns_and_matches:
            position = match.start()
            
            math_item = SpecialContentItem(
                content_type='mathematical',
                identifier=match.group(0),
                position_in_section=position,
                absolute_position=section_start_pos + position,
                text_preview=match.group(0).strip(),
                confidence=confidence,
                metadata={
                    'equation_type': 'numbered' if '(' in match.group(0) else 'formula',
                    'pattern_used': pattern.pattern_id
                }
            )
            math_content.append(math_item)
        
        return math_content
    
    def _add_intro_and_end_matter(self, 
                                 section_boundaries: List[SectionBoundary], 
                                 text: str, 
                                 char_to_page_map: Dict[int, int]) -> List[SectionBoundary]:
        """
        Add chapter introduction and end matter sections.
        
        ENHANCED: Better boundary detection and conflict resolution
        """
        enhanced_boundaries = []
        
        # Add chapter introduction if substantial content exists before first section
        if section_boundaries:
            first_section_pos = section_boundaries[0].start_pos
            intro_content = text[:first_section_pos].strip()
            
            if len(intro_content) > 100:
                intro_boundary = SectionBoundary(
                    section_id="chapter_intro",
                    section_number="Chapter_Intro",
                    section_title="Chapter Introduction",
                    start_pos=0,
                    end_pos=first_section_pos,
                    content_length=len(intro_content),
                    word_count=len(intro_content.split()),
                    page_number=char_to_page_map.get(0, 1),
                    confidence=0.9,
                    special_content=self._detect_special_content_in_section(intro_content, 0),
                    content_preview=intro_content[:200] + "..."
                )
                enhanced_boundaries.append(intro_boundary)
                logger.info(f"Added Chapter Introduction: {len(intro_content)} chars")
        
        # Fix last section boundary before adding main sections
        if section_boundaries:
            summary_start = self._find_summary_start(text)
            
            if summary_start and len(section_boundaries) > 0:
                last_section = section_boundaries[-1]
                if last_section.end_pos > summary_start:
                    logger.info(f"Fixing boundary: Section {last_section.section_number} end moved from {last_section.end_pos} to {summary_start}")
                    
                    # Recalculate last section content
                    adjusted_content = text[last_section.start_pos:summary_start].strip()
                    last_section.end_pos = summary_start
                    last_section.content_length = len(adjusted_content)
                    last_section.word_count = len(adjusted_content.split())
                    last_section.content_preview = adjusted_content[:200] + "..." if len(adjusted_content) > 200 else adjusted_content
                    
                    # Re-detect special content for adjusted section
                    last_section.special_content = self._detect_special_content_in_section(
                        adjusted_content,
                        last_section.start_pos
                    )
        
        # Add main sections
        enhanced_boundaries.extend(section_boundaries)
        
        # Detect and add end matter sections
        end_matter_sections = self._detect_end_matter_sections(text, char_to_page_map)
        enhanced_boundaries.extend(end_matter_sections)
        
        return enhanced_boundaries
    
    def _find_summary_start(self, text: str) -> Optional[int]:
        """Find the start position of summary/end matter"""
        summary_patterns = [
            r'What\s+you\s+have\s+learnt',
            r'Summary',
            r'SUMMARY'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.start()
        
        return None
    
    def _detect_end_matter_sections(self, 
                                   text: str, 
                                   char_to_page_map: Dict[int, int]) -> List[SectionBoundary]:
        """Detect end-of-chapter sections"""
        end_matter = []
        
        summary_start = self._find_summary_start(text)
        if not summary_start:
            return end_matter
        
        # Find end of summary (start of exercises or end of text)
        exercises_match = re.search(r'Exercises?', text[summary_start:], re.IGNORECASE)
        summary_end = summary_start + exercises_match.start() if exercises_match else len(text)
        
        summary_content = text[summary_start:summary_end].strip()
        
        if len(summary_content) > 100:
            summary_boundary = SectionBoundary(
                section_id="summary",
                section_number="Summary",
                section_title="What you have learnt",
                start_pos=summary_start,
                end_pos=summary_end,
                content_length=len(summary_content),
                word_count=len(summary_content.split()),
                page_number=char_to_page_map.get(summary_start, 1),
                confidence=0.9,
                special_content={},
                content_preview=summary_content[:200] + "..."
            )
            end_matter.append(summary_boundary)
            logger.info(f"Added Summary section: {len(summary_content)} chars")
        
        # Detect exercises section
        if exercises_match:
            exercises_start = summary_start + exercises_match.start()
            exercises_content = text[exercises_start:].strip()
            
            if len(exercises_content) > 100:
                exercises_boundary = SectionBoundary(
                    section_id="exercises",
                    section_number="Exercises",
                    section_title="Exercises",
                    start_pos=exercises_start,
                    end_pos=len(text),
                    content_length=len(exercises_content),
                    word_count=len(exercises_content.split()),
                    page_number=char_to_page_map.get(exercises_start, 1),
                    confidence=0.9,
                    special_content={},
                    content_preview=exercises_content[:200] + "..."
                )
                end_matter.append(exercises_boundary)
                logger.info(f"Added Exercises section: {len(exercises_content)} chars")
        
        return end_matter
    
    def _convert_to_mother_sections(self, 
                                   boundaries: List[SectionBoundary], 
                                   document: SourceDocument) -> List[MotherSection]:
        """Convert section boundaries to MotherSection objects"""
        mother_sections = []
        
        for boundary in boundaries:
            # Convert special content to the format expected by MotherSection
            special_content = {
                'activities': [
                    {
                        'activity_number': item.identifier,
                        'position_in_section': item.position_in_section,
                        'absolute_position': item.absolute_position,
                        'text_preview': item.text_preview,
                        'confidence': item.confidence
                    }
                    for item in boundary.special_content.get('activities', [])
                ],
                'figures': [
                    {
                        'figure_number': item.identifier,
                        'caption': item.metadata.get('caption', ''),
                        'position_in_section': item.position_in_section,
                        'absolute_position': item.absolute_position,
                        'has_description': item.metadata.get('has_description', False),
                        'is_content': item.metadata.get('is_content', True),
                        'confidence': item.confidence
                    }
                    for item in boundary.special_content.get('figures', [])
                ],
                'examples': [
                    {
                        'example_number': item.identifier,
                        'position_in_section': item.position_in_section,
                        'absolute_position': item.absolute_position,
                        'text_preview': item.text_preview
                    }
                    for item in boundary.special_content.get('examples', [])
                ],
                'special_boxes': [
                    {
                        'box_type': item.metadata.get('box_type', 'unknown'),
                        'position_in_section': item.position_in_section,
                        'absolute_position': item.absolute_position,
                        'content_preview': item.text_preview
                    }
                    for item in boundary.special_content.get('special_boxes', [])
                ],
                'mathematical_content': [
                    {
                        'equation_type': item.metadata.get('equation_type', 'unknown'),
                        'content': item.text_preview,
                        'position_in_section': item.position_in_section,
                        'absolute_position': item.absolute_position
                    }
                    for item in boundary.special_content.get('mathematical_content', [])
                ]
            }
            
            mother_section = MotherSection(
                section_id=boundary.section_id,
                document_id=document.document_id,
                section_number=boundary.section_number,
                section_title=boundary.section_title,
                start_pos=boundary.start_pos,
                end_pos=boundary.end_pos,
                page_number=boundary.page_number,
                content_length=boundary.content_length,
                word_count=boundary.word_count,
                confidence=boundary.confidence,
                special_content=special_content,
                content_preview=boundary.content_preview
            )
            
            mother_sections.append(mother_section)
        
        return mother_sections
    
    def _calculate_section_confidence(self, 
                                    match: re.Match, 
                                    text: str, 
                                    base_confidence: float) -> float:
        """Calculate enhanced confidence for section detection"""
        confidence = base_confidence
        
        # Boost confidence for longer, more descriptive titles
        if len(match.groups()) >= 2:
            title = match.group(2)
            if len(title.split()) >= 2:
                confidence += 0.05
            if len(title) > 20:
                confidence += 0.02
        
        # Check if it's at the beginning of a line (good indicator)
        if match.start() == 0 or text[match.start() - 1] == '\n':
            confidence += 0.05
        
        # Check if followed by content (not another section)
        content_after = text[match.end():match.end() + 100]
        if content_after and not re.search(r'^\d+\.\d+\s+[A-Z]', content_after):
            confidence += 0.03
        
        return min(confidence, 0.95)
    
    def _remove_duplicate_sections(self, section_headers: List[SectionHeader]) -> List[SectionHeader]:
        """Remove duplicate section headers"""
        seen_numbers = set()
        unique_headers = []
        
        for header in section_headers:
            if header.section_number not in seen_numbers:
                seen_numbers.add(header.section_number)
                unique_headers.append(header)
            else:
                logger.debug(f"Removed duplicate section: {header.section_number}")
        
        return unique_headers
    
    def _classify_special_box(self, matched_text: str) -> str:
        """Classify the type of special box"""
        text_lower = matched_text.lower()
        
        if any(word in text_lower for word in ['born', 'died', '(']):
            return 'biography'
        elif any(word in text_lower for word in ['summary', 'learnt']):
            return 'summary'
        elif any(word in text_lower for word in ['exercise', 'question']):
            return 'exercises'
        elif any(word in text_lower for word in ['note', 'remember']):
            return 'note'
        else:
            return 'unknown_box'
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get statistics about the detection process"""
        return self.detection_stats.copy()
    
    def validate_sections(self, sections: List[MotherSection]) -> List[str]:
        """Validate detected sections and return list of issues"""
        issues = []
        
        if not sections:
            issues.append("No sections detected")
            return issues
        
        # Check for overlapping sections
        for i, section in enumerate(sections[:-1]):
            next_section = sections[i + 1]
            if section.end_pos > next_section.start_pos:
                issues.append(f"Overlapping sections: {section.section_number} and {next_section.section_number}")
        
        # Check for very small sections
        for section in sections:
            if section.word_count < 50:
                issues.append(f"Very small section: {section.section_number} ({section.word_count} words)")
        
        # Check confidence levels
        low_confidence_sections = [s for s in sections if s.confidence < 0.5]
        if low_confidence_sections:
            issues.append(f"{len(low_confidence_sections)} sections with low confidence")
        
        return issues