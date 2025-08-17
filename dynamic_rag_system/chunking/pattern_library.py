"""
Pattern Library - Configurable regex patterns for educational content detection.

Enhanced version of the original PatternLibrary with:
- Configuration-driven patterns
- Pattern versioning and A/B testing
- Subject-specific pattern sets
- Pattern learning from user corrections
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

from ..core.config import get_config
from ..core.models import ContentType, SourceDocument

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns for content detection"""
    SECTION_HEADER = "section_header"
    ACTIVITY = "activity"
    EXAMPLE = "example"
    FIGURE_CONTENT = "figure_content"
    FIGURE_REFERENCE = "figure_reference"
    SPECIAL_BOX = "special_box"
    MATHEMATICAL = "mathematical"
    SUMMARY = "summary"
    EXERCISES = "exercises"
    # New content types for better educational coverage
    REAL_WORLD_APPLICATION = "real_world_application"
    PRACTICAL_USE = "practical_use"
    BASIC_CONCEPT = "basic_concept"
    CONCEPTUAL_EXPLANATION = "conceptual_explanation"
    DEFINITION = "definition"
    EXPERIMENTAL_PROCEDURE = "experimental_procedure"
    HANDS_ON_ACTIVITY = "hands_on_activity"
    PHYSICAL_PHENOMENA = "physical_phenomena"


@dataclass
class Pattern:
    """Individual pattern with metadata"""
    pattern_id: str
    regex: str
    pattern_type: PatternType
    confidence_base: float
    subject_specific: bool = False
    subjects: List[str] = field(default_factory=list)
    grade_levels: List[str] = field(default_factory=list)
    curriculum: str = "NCERT"
    language: str = "en"
    description: str = ""
    examples: List[str] = field(default_factory=list)
    version: str = "1.0"
    success_rate: float = 0.0  # Updated based on usage
    last_updated: str = ""
    
    def matches(self, text: str, flags: int = re.IGNORECASE) -> List[re.Match]:
        """Find all matches for this pattern in text"""
        try:
            return list(re.finditer(self.regex, text, flags))
        except re.error as e:
            logger.error(f"Invalid regex pattern {self.pattern_id}: {e}")
            return []
    
    def calculate_confidence(self, match: re.Match, context: str = "") -> float:
        """Calculate confidence for a specific match"""
        confidence = self.confidence_base
        
        # Adjust based on context
        if context:
            # Boost confidence if surrounded by educational content
            if any(word in context.lower() for word in ['chapter', 'section', 'lesson']):
                confidence += 0.1
            
            # Reduce confidence if in middle of sentence
            match_start = match.start()
            if match_start > 0 and context[match_start - 1].isalnum():
                confidence -= 0.2
        
        # Apply success rate adjustment
        if self.success_rate > 0:
            confidence *= (0.5 + 0.5 * self.success_rate)  # Scale by historical performance
        
        return max(0.0, min(1.0, confidence))


class PatternLibrary:
    """
    Enhanced pattern library with configuration support.
    
    PRESERVED: All working patterns from original implementation
    ENHANCED: Configuration, versioning, and learning capabilities
    """
    
    def __init__(self, curriculum: str = "NCERT", language: str = "en"):
        self.config = get_config()
        self.curriculum = curriculum
        self.language = language
        
        # Pattern storage
        self._patterns: Dict[PatternType, List[Pattern]] = {}
        self._pattern_index: Dict[str, Pattern] = {}
        
        # Performance tracking
        self._usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Initialize with default patterns
        self._initialize_default_patterns()
        
        logger.info(f"Pattern library initialized for {curriculum} curriculum in {language}")
    
    def _initialize_default_patterns(self):
        """Initialize with proven patterns from original implementation"""
        
        # PRESERVED: Working section patterns
        section_patterns = [
            Pattern(
                pattern_id="ncert_section_main",
                regex=r'^(\d+\.\d+)\s+(?!Example|EXAMPLE|MATHEMATICAL|Mathematical)([A-Z][A-Za-z\s]{8,60})(?:\n|$)',
                pattern_type=PatternType.SECTION_HEADER,
                confidence_base=0.9,
                description="Main NCERT section headers like '8.1 Force and Motion'",
                examples=["8.1 Force and Motion", "9.2 Laws of Motion"]
            ),
            Pattern(
                pattern_id="ncert_section_secondary", 
                regex=r'^(\d+\.\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,8})(?:\n|$)',
                pattern_type=PatternType.SECTION_HEADER,
                confidence_base=0.8,
                description="Secondary section pattern",
                examples=["8.3 Balanced Forces"]
            ),
            Pattern(
                pattern_id="ncert_section_caps",
                regex=r'^(\d+\.\d+)\s+([A-Z\s]{10,50})(?:\n|$)',
                pattern_type=PatternType.SECTION_HEADER,
                confidence_base=0.7,
                description="All caps section headers",
                examples=["8.4 FORCE AND MOTION"]
            )
        ]
        
        # PRESERVED: Working activity patterns with Hindi support
        activity_patterns = [
            Pattern(
                pattern_id="activity_standard",
                regex=r'ACTIVITY\s+(\d+\.\d+)',
                pattern_type=PatternType.ACTIVITY,
                confidence_base=0.95,
                description="Standard ACTIVITY pattern",
                examples=["ACTIVITY 8.1", "ACTIVITY 9.2"]
            ),
            Pattern(
                pattern_id="activity_with_separators",
                regex=r'Activity\s*[_\-–—\s]*\s*(\d+\.\d+)',
                pattern_type=PatternType.ACTIVITY,
                confidence_base=0.9,
                description="Activity with various separators",
                examples=["Activity — 8.1", "Activity _ 8.2"]
            ),
            Pattern(
                pattern_id="activity_flexible",
                regex=r'Activity(?:\s|[^\w\d])*(\d+\.\d+)',
                pattern_type=PatternType.ACTIVITY,
                confidence_base=0.85,
                description="Flexible activity pattern",
                examples=["Activity: 8.1", "Activity (8.2)"]
            ),
            Pattern(
                pattern_id="activity_hindi",
                regex=r'गतिविधि\s+(\d+\.\d+)',
                pattern_type=PatternType.ACTIVITY,
                confidence_base=0.9,
                language="hi",
                description="Hindi activity pattern",
                examples=["गतिविधि 8.1"]
            )
        ]
        
        # ENHANCED: Figure patterns with content vs reference separation
        figure_content_patterns = [
            Pattern(
                pattern_id="figure_with_description",
                regex=r'Fig\.\s*(\d+\.\d+):\s*(.+?)(?=\n(?:Fig\.|Activity|\d+\.\d+|$))',
                pattern_type=PatternType.FIGURE_CONTENT,
                confidence_base=0.95,
                description="Figures with descriptions (actual content)",
                examples=["Fig. 8.3: A ball at rest"]
            ),
            Pattern(
                pattern_id="figure_full_word",
                regex=r'Figure\s+(\d+\.\d+):\s*(.+?)(?=\n(?:Figure|Activity|\d+\.\d+|$))',
                pattern_type=PatternType.FIGURE_CONTENT,
                confidence_base=0.9,
                description="Full word Figure with description",
                examples=["Figure 8.4: Forces acting on a box"]
            ),
            Pattern(
                pattern_id="figure_substantial",
                regex=r'Fig\.\s*(\d+\.\d+)\s*[:]?\s*(.{10,}?)(?=\n\n|\n[A-Z]|\n\d+\.\d+|$)',
                pattern_type=PatternType.FIGURE_CONTENT,
                confidence_base=0.8,
                description="Figures with substantial descriptions",
                examples=["Fig. 8.5 This diagram shows..."]
            ),
            Pattern(
                pattern_id="figure_hindi",
                regex=r'चित्र\s+(\d+\.\d+):\s*(.+?)(?=\n|चित्र|$)',
                pattern_type=PatternType.FIGURE_CONTENT,
                confidence_base=0.9,
                language="hi",
                description="Hindi figure pattern",
                examples=["चित्र 8.1: गेंद की गति"]
            )
        ]
        
        # Figure reference patterns (to be filtered out)
        figure_reference_patterns = [
            Pattern(
                pattern_id="figure_bracket_ref",
                regex=r'\\[Fig\\.\\s*(\\d+\\.\\d+)(?:\\([a-z]\\))?\\]',
                pattern_type=PatternType.FIGURE_REFERENCE,
                confidence_base=0.9,
                description="Figure references in brackets",
                examples=["[Fig. 8.4(c)]", "[Fig. 8.1]"]
            ),
            Pattern(
                pattern_id="figure_paren_ref", 
                regex=r'\\(Fig\\.\\s*(\\d+\\.\\d+)(?:\\([a-z]\\))?\\)',
                pattern_type=PatternType.FIGURE_REFERENCE,
                confidence_base=0.9,
                description="Figure references in parentheses",
                examples=["(Fig. 8.10)", "(Fig. 8.4(a))"]
            ),
            Pattern(
                pattern_id="figure_see_ref",
                regex=r'see\\s+Fig\\.\\s*(\\d+\\.\\d+)',
                pattern_type=PatternType.FIGURE_REFERENCE,
                confidence_base=0.85,
                description="See Fig references",
                examples=["see Fig. 8.11"]
            )
        ]
        
        # PRESERVED: Example patterns
        example_patterns = [
            Pattern(
                pattern_id="example_standard",
                regex=r'Example\s+(\d+\.\d+)',
                pattern_type=PatternType.EXAMPLE,
                confidence_base=0.9,
                description="Standard example pattern",
                examples=["Example 8.1", "Example 9.3"]
            ),
            Pattern(
                pattern_id="example_caps",
                regex=r'EXAMPLE\s+(\d+\.\d+)',
                pattern_type=PatternType.EXAMPLE,
                confidence_base=0.9,
                description="All caps example pattern",
                examples=["EXAMPLE 8.2"]
            ),
            Pattern(
                pattern_id="example_hindi",
                regex=r'उदाहरण\s+(\d+\.\d+)',
                pattern_type=PatternType.EXAMPLE,
                confidence_base=0.9,
                language="hi",
                description="Hindi example pattern",
                examples=["उदाहरण 8.1"]
            )
        ]
        
        # PRESERVED: Special box patterns
        special_box_patterns = [
            Pattern(
                pattern_id="biography_box",
                regex=r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*\((\d{4})\s*[–-]\s*(\d{4})\)',
                pattern_type=PatternType.SPECIAL_BOX,
                confidence_base=0.85,
                description="Biography boxes with birth-death years",
                examples=["Isaac Newton (1642 – 1727)"]
            ),
            Pattern(
                pattern_id="summary_box",
                regex=r'(?:What\s+you\s+have\s+learnt|Summary|SUMMARY)',
                pattern_type=PatternType.SPECIAL_BOX,
                confidence_base=0.9,
                description="Summary sections",
                examples=["What you have learnt", "Summary"]
            ),
            Pattern(
                pattern_id="exercises_box",
                regex=r'(?:Exercises?|EXERCISES?|Questions|QUESTIONS)',
                pattern_type=PatternType.SPECIAL_BOX,
                confidence_base=0.9,
                description="Exercise sections",
                examples=["Exercises", "Questions"]
            ),
            Pattern(
                pattern_id="note_box",
                regex=r'(?:Note:|NOTE:|Remember:|REMEMBER:)',
                pattern_type=PatternType.SPECIAL_BOX,
                confidence_base=0.8,
                description="Note and remember boxes",
                examples=["Note:", "Remember:"]
            )
        ]
        
        # Mathematical content patterns
        mathematical_patterns = [
            Pattern(
                pattern_id="numbered_equation",
                regex=r'\((\d+\.\d+)\)',
                pattern_type=PatternType.MATHEMATICAL,
                confidence_base=0.8,
                description="Numbered equations",
                examples=["(8.1)", "(9.2)"]
            ),
            Pattern(
                pattern_id="formula_assignment",
                regex=r'[A-Z]\s*=\s*[^.\n]{3,}',
                pattern_type=PatternType.MATHEMATICAL,
                confidence_base=0.7,
                description="Formula assignments",
                examples=["F = ma", "v = u + at"]
            ),
            Pattern(
                pattern_id="math_symbols",
                regex=r'∝|±|×|÷|∆|∑',
                pattern_type=PatternType.MATHEMATICAL,
                confidence_base=0.6,
                description="Mathematical symbols",
                examples=["∝", "±", "×"]
            )
        ]
        
        # NEW: Real-world application patterns
        application_patterns = [
            Pattern(
                pattern_id="applications_header",
                regex=r'(?:Applications?|Uses?|Practical\s+(?:applications?|uses?)):?\s*(?:\n|$)',
                pattern_type=PatternType.REAL_WORLD_APPLICATION,
                confidence_base=0.95,
                description="Section headers for applications",
                examples=["Applications:", "Practical uses:"]
            ),
            Pattern(
                pattern_id="in_field_usage",
                regex=r'(?:in|used\s+in|applied\s+in)\s+(?:industry|medicine|technology|engineering|agriculture|manufacturing|construction):?\s*(.{10,200})',
                pattern_type=PatternType.REAL_WORLD_APPLICATION,
                confidence_base=0.9,
                description="Field-specific applications",
                examples=["used in medicine", "in technology"]
            ),
            Pattern(
                pattern_id="everyday_usage",
                regex=r'(?:in\s+(?:everyday\s+life|daily\s+life|real\s+life|our\s+daily|common)|everyday\s+(?:examples?|applications?|uses?)):?\s*(.{10,200})',
                pattern_type=PatternType.REAL_WORLD_APPLICATION,
                confidence_base=0.9,
                description="Everyday life applications",
                examples=["in everyday life", "everyday examples"]
            ),
            Pattern(
                pattern_id="device_usage",
                regex=r'(?:devices?|instruments?|equipment|machines?|systems?)\s+(?:that\s+use|using|based\s+on|utilizing):?\s*(.{10,200})',
                pattern_type=PatternType.REAL_WORLD_APPLICATION,
                confidence_base=0.8,
                description="Device and equipment applications",
                examples=["devices that use", "instruments using"]
            )
        ]
        
        # NEW: Practical use patterns
        practical_use_patterns = [
            Pattern(
                pattern_id="how_to_use",
                regex=r'(?:How\s+to\s+(?:use|apply|calculate|find|determine)|To\s+(?:use|apply|calculate)):?\s*(.{10,200})',
                pattern_type=PatternType.PRACTICAL_USE,
                confidence_base=0.9,
                description="How-to practical instructions",
                examples=["How to use", "To calculate"]
            ),
            Pattern(
                pattern_id="practical_tips",
                regex=r'(?:tips?|hints?|suggestions?|guidelines?)\s+(?:for|to):?\s*(.{10,200})',
                pattern_type=PatternType.PRACTICAL_USE,
                confidence_base=0.8,
                description="Practical tips and guidelines",
                examples=["tips for", "hints to"]
            ),
            Pattern(
                pattern_id="procedure_steps",
                regex=r'(?:steps?|procedures?|methods?|techniques?)\s+(?:to|for):?\s*(.{10,200})',
                pattern_type=PatternType.PRACTICAL_USE,
                confidence_base=0.85,
                description="Procedural instructions",
                examples=["steps to", "procedure for"]
            )
        ]
        
        # NEW: Basic concept patterns
        basic_concept_patterns = [
            Pattern(
                pattern_id="concept_definition",
                regex=r'(?:^|\n)\s*([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:is|are|refers?\s+to|means?|can\s+be\s+defined\s+as):?\s*(.{10,200})',
                pattern_type=PatternType.BASIC_CONCEPT,
                confidence_base=0.9,
                description="Basic concept definitions",
                examples=["Sound is", "Force refers to"]
            ),
            Pattern(
                pattern_id="key_point_marker",
                regex=r'(?:key\s+points?|important\s+concepts?|fundamental\s+ideas?|basic\s+principles?):?\s*(.{10,200})',
                pattern_type=PatternType.BASIC_CONCEPT,
                confidence_base=0.85,
                description="Key points and fundamental concepts",
                examples=["Key points:", "Important concepts:"]
            ),
            Pattern(
                pattern_id="remember_points",
                regex=r'(?:remember|note|keep\s+in\s+mind|it\s+is\s+important):?\s*(.{10,200})',
                pattern_type=PatternType.BASIC_CONCEPT,
                confidence_base=0.8,
                description="Important points to remember",
                examples=["Remember", "Note that"]
            )
        ]
        
        # NEW: Conceptual explanation patterns
        conceptual_explanation_patterns = [
            Pattern(
                pattern_id="explanation_markers",
                regex=r'(?:this\s+(?:means|implies|shows|demonstrates)|in\s+other\s+words|to\s+understand\s+this|the\s+reason\s+(?:is|for\s+this)):?\s*(.{10,200})',
                pattern_type=PatternType.CONCEPTUAL_EXPLANATION,
                confidence_base=0.85,
                description="Explanation and reasoning markers",
                examples=["This means", "In other words"]
            ),
            Pattern(
                pattern_id="cause_effect",
                regex=r'(?:because|since|as\s+a\s+result|therefore|thus|hence|consequently):?\s*(.{10,200})',
                pattern_type=PatternType.CONCEPTUAL_EXPLANATION,
                confidence_base=0.8,
                description="Cause and effect explanations",
                examples=["because", "as a result"]
            ),
            Pattern(
                pattern_id="why_how_explanations",
                regex=r'(?:Why\s+(?:does|do|is|are)|How\s+(?:does|do|is|are)):?\s*(.{10,200})',
                pattern_type=PatternType.CONCEPTUAL_EXPLANATION,
                confidence_base=0.85,
                description="Why and how explanations",
                examples=["Why does", "How is"]
            )
        ]
        
        # NEW: Definition patterns
        definition_patterns = [
            Pattern(
                pattern_id="formal_definition",
                regex=r'(?:Definition|Define):?\s*(.{10,200})',
                pattern_type=PatternType.DEFINITION,
                confidence_base=0.95,
                description="Formal definitions",
                examples=["Definition:", "Define force"]
            ),
            Pattern(
                pattern_id="term_definition",
                regex=r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:\s*(.{10,200})',
                pattern_type=PatternType.DEFINITION,
                confidence_base=0.8,
                description="Term: definition format",
                examples=["Force: a push or pull"]
            )
        ]
        
        # NEW: Physical phenomena patterns
        phenomena_patterns = [
            Pattern(
                pattern_id="observe_phenomena",
                regex=r'(?:observe|notice|see|watch|look\s+at):?\s*(.{10,200})',
                pattern_type=PatternType.PHYSICAL_PHENOMENA,
                confidence_base=0.7,
                description="Observable phenomena",
                examples=["observe that", "notice how"]
            ),
            Pattern(
                pattern_id="natural_phenomena",
                regex=r'(?:phenomenon|phenomena|occurs?|happens?|takes?\s+place):?\s*(.{10,200})',
                pattern_type=PatternType.PHYSICAL_PHENOMENA,
                confidence_base=0.8,
                description="Natural phenomena descriptions",
                examples=["phenomenon of", "occurs when"]
            )
        ]
        
        # Register all pattern sets
        pattern_sets = [
            (PatternType.SECTION_HEADER, section_patterns),
            (PatternType.ACTIVITY, activity_patterns),
            (PatternType.FIGURE_CONTENT, figure_content_patterns),
            (PatternType.FIGURE_REFERENCE, figure_reference_patterns),
            (PatternType.EXAMPLE, example_patterns),
            (PatternType.SPECIAL_BOX, special_box_patterns),
            (PatternType.MATHEMATICAL, mathematical_patterns),
            # New content type patterns for better educational coverage
            (PatternType.REAL_WORLD_APPLICATION, application_patterns),
            (PatternType.PRACTICAL_USE, practical_use_patterns),
            (PatternType.BASIC_CONCEPT, basic_concept_patterns),
            (PatternType.CONCEPTUAL_EXPLANATION, conceptual_explanation_patterns),
            (PatternType.DEFINITION, definition_patterns),
            (PatternType.PHYSICAL_PHENOMENA, phenomena_patterns)
        ]
        
        for pattern_type, patterns in pattern_sets:
            self._patterns[pattern_type] = patterns
            for pattern in patterns:
                self._pattern_index[pattern.pattern_id] = pattern
        
        logger.info(f"Initialized {sum(len(patterns) for patterns in self._patterns.values())} patterns")
    
    def get_patterns(self, 
                    pattern_type: PatternType,
                    subject: str = None,
                    grade_level: str = None,
                    language: str = None) -> List[Pattern]:
        """Get patterns filtered by criteria"""
        patterns = self._patterns.get(pattern_type, [])
        
        # Filter by criteria
        filtered = []
        for pattern in patterns:
            # Language filter
            if language and pattern.language != language:
                continue
            
            # Subject filter
            if subject and pattern.subject_specific and subject not in pattern.subjects:
                continue
            
            # Grade level filter
            if grade_level and pattern.grade_levels and grade_level not in pattern.grade_levels:
                continue
            
            filtered.append(pattern)
        
        # Sort by confidence (highest first)
        return sorted(filtered, key=lambda p: p.confidence_base, reverse=True)
    
    def find_matches(self, 
                    text: str,
                    pattern_type: PatternType,
                    document: SourceDocument = None,
                    confidence_threshold: float = None) -> List[Tuple[Pattern, re.Match, float]]:
        """Find all matches for a pattern type with confidence scores"""
        if confidence_threshold is None:
            confidence_threshold = self.config.processing.confidence_threshold
        
        # Get applicable patterns
        patterns = self.get_patterns(
            pattern_type,
            subject=document.subject if document else None,
            grade_level=document.grade_level if document else None,
            language=document.language if document else None
        )
        
        matches = []
        for pattern in patterns:
            for match in pattern.matches(text):
                confidence = pattern.calculate_confidence(match, text)
                if confidence >= confidence_threshold:
                    matches.append((pattern, match, confidence))
                    # Track usage
                    self._track_pattern_usage(pattern.pattern_id, True)
        
        # Sort by confidence (highest first)
        return sorted(matches, key=lambda x: x[2], reverse=True)
    
    def add_custom_pattern(self, pattern: Pattern) -> bool:
        """Add a custom pattern to the library"""
        try:
            # Validate regex
            re.compile(pattern.regex)
            
            # Add to library
            if pattern.pattern_type not in self._patterns:
                self._patterns[pattern.pattern_type] = []
            
            self._patterns[pattern.pattern_type].append(pattern)
            self._pattern_index[pattern.pattern_id] = pattern
            
            logger.info(f"Added custom pattern: {pattern.pattern_id}")
            return True
            
        except re.error as e:
            logger.error(f"Invalid regex in custom pattern {pattern.pattern_id}: {e}")
            return False
    
    def update_pattern_performance(self, pattern_id: str, success: bool):
        """Update pattern performance based on usage feedback"""
        if pattern_id in self._pattern_index:
            pattern = self._pattern_index[pattern_id]
            
            # Update success rate using exponential moving average
            alpha = 0.1  # Learning rate
            if pattern.success_rate == 0.0:
                pattern.success_rate = 1.0 if success else 0.0
            else:
                new_value = 1.0 if success else 0.0
                pattern.success_rate = alpha * new_value + (1 - alpha) * pattern.success_rate
            
            self._track_pattern_usage(pattern_id, success)
            logger.debug(f"Updated pattern {pattern_id} success rate to {pattern.success_rate:.3f}")
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for all patterns"""
        stats = {
            "total_patterns": len(self._pattern_index),
            "patterns_by_type": {pt.value: len(patterns) for pt, patterns in self._patterns.items()},
            "top_performing_patterns": [],
            "usage_stats": self._usage_stats.copy()
        }
        
        # Get top performing patterns
        patterns_with_performance = [
            (pid, pattern.success_rate, pattern.confidence_base)
            for pid, pattern in self._pattern_index.items()
            if pattern.success_rate > 0
        ]
        
        stats["top_performing_patterns"] = sorted(
            patterns_with_performance, 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return stats
    
    def export_patterns(self, pattern_type: PatternType = None) -> Dict[str, Any]:
        """Export patterns for backup or sharing"""
        if pattern_type:
            patterns_to_export = {pattern_type: self._patterns.get(pattern_type, [])}
        else:
            patterns_to_export = self._patterns
        
        export_data = {
            "curriculum": self.curriculum,
            "language": self.language,
            "patterns": {},
            "export_timestamp": "",
            "version": "1.0"
        }
        
        for pt, patterns in patterns_to_export.items():
            export_data["patterns"][pt.value] = [
                {
                    "pattern_id": p.pattern_id,
                    "regex": p.regex,
                    "confidence_base": p.confidence_base,
                    "description": p.description,
                    "examples": p.examples,
                    "success_rate": p.success_rate
                }
                for p in patterns
            ]
        
        return export_data
    
    def import_patterns(self, import_data: Dict[str, Any]) -> int:
        """Import patterns from backup or external source"""
        imported_count = 0
        
        try:
            for pattern_type_str, pattern_list in import_data.get("patterns", {}).items():
                pattern_type = PatternType(pattern_type_str)
                
                for pattern_data in pattern_list:
                    pattern = Pattern(
                        pattern_id=pattern_data["pattern_id"],
                        regex=pattern_data["regex"],
                        pattern_type=pattern_type,
                        confidence_base=pattern_data["confidence_base"],
                        description=pattern_data.get("description", ""),
                        examples=pattern_data.get("examples", []),
                        success_rate=pattern_data.get("success_rate", 0.0)
                    )
                    
                    if self.add_custom_pattern(pattern):
                        imported_count += 1
            
            logger.info(f"Imported {imported_count} patterns")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import patterns: {e}")
            return imported_count
    
    def _track_pattern_usage(self, pattern_id: str, success: bool):
        """Track pattern usage for performance monitoring"""
        if pattern_id not in self._usage_stats:
            self._usage_stats[pattern_id] = {
                "total_uses": 0,
                "successful_uses": 0,
                "last_used": ""
            }
        
        stats = self._usage_stats[pattern_id]
        stats["total_uses"] += 1
        if success:
            stats["successful_uses"] += 1
        stats["last_used"] = ""  # Would be timestamp in real implementation
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Pattern]:
        """Get a specific pattern by ID"""
        return self._pattern_index.get(pattern_id)
    
    def validate_patterns(self) -> List[str]:
        """Validate all patterns and return list of issues"""
        issues = []
        
        for pattern_id, pattern in self._pattern_index.items():
            try:
                # Test regex compilation
                re.compile(pattern.regex)
                
                # Test with examples
                if pattern.examples:
                    for example in pattern.examples:
                        matches = pattern.matches(example)
                        if not matches:
                            issues.append(f"Pattern {pattern_id} doesn't match its example: '{example}'")
                
            except re.error as e:
                issues.append(f"Pattern {pattern_id} has invalid regex: {e}")
        
        return issues