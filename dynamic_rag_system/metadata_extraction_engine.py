#!/usr/bin/env python3
"""
Advanced Metadata Extraction Engine for Educational Content
Transforms captured content into intelligent educational metadata
"""

import re
import json
from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

@dataclass
class EducationalMetadata:
    """Comprehensive educational metadata structure"""
    
    # Learning Objectives
    learning_objectives: List[str] = field(default_factory=list)
    explicit_objectives: List[str] = field(default_factory=list)
    implicit_objectives: List[str] = field(default_factory=list)
    
    # Concept Hierarchy
    main_concepts: List[str] = field(default_factory=list)
    sub_concepts: List[str] = field(default_factory=list)
    concept_relationships: Dict[str, List[str]] = field(default_factory=dict)
    concept_definitions: Dict[str, str] = field(default_factory=dict)
    
    # Difficulty and Cognitive Analysis
    difficulty_level: str = "intermediate"
    cognitive_levels: List[str] = field(default_factory=list)
    reading_level: Dict[str, Any] = field(default_factory=dict)
    prerequisite_concepts: List[str] = field(default_factory=list)
    
    # Educational Context
    common_misconceptions: List[str] = field(default_factory=list)
    real_world_applications: List[str] = field(default_factory=list)
    career_connections: List[str] = field(default_factory=list)
    historical_context: List[str] = field(default_factory=list)
    
    # Skills and Competencies
    skills_developed: List[str] = field(default_factory=list)
    competencies: List[str] = field(default_factory=list)
    assessment_objectives: List[str] = field(default_factory=list)
    
    # Content Types (Enhanced for better coverage)
    content_types: List[str] = field(default_factory=list)
    has_basic_concepts: bool = False
    has_real_world_applications: bool = False
    has_practical_uses: bool = False
    has_conceptual_explanations: bool = False
    has_definitions: bool = False
    has_physical_phenomena: bool = False
    has_experimental_procedures: bool = False
    has_hands_on_activities: bool = False
    
    # Quality Indicators
    content_depth: float = 0.0
    pedagogical_completeness: float = 0.0
    conceptual_clarity: float = 0.0
    engagement_level: float = 0.0


class MetadataExtractionEngine:
    """Advanced engine for extracting rich educational metadata"""
    
    def __init__(self):
        self.concept_patterns = self._initialize_concept_patterns()
        self.objective_patterns = self._initialize_objective_patterns()
        self.skill_patterns = self._initialize_skill_patterns()
        self.misconception_patterns = self._initialize_misconception_patterns()
        self.application_patterns = self._initialize_application_patterns()
        self.difficulty_indicators = self._initialize_difficulty_indicators()
        self.content_type_patterns = self._initialize_content_type_patterns()
        
    def extract_comprehensive_metadata(self, learning_unit, content: str, 
                                     grade_level: int, subject: str) -> EducationalMetadata:
        """Extract comprehensive educational metadata from learning unit"""
        
        metadata = EducationalMetadata()
        
        # Extract learning objectives
        metadata.learning_objectives = self._extract_learning_objectives(content, learning_unit)
        metadata.explicit_objectives = self._find_explicit_objectives(content)
        metadata.implicit_objectives = self._infer_implicit_objectives(learning_unit, subject)
        
        # Extract concept hierarchy
        metadata.main_concepts = self._extract_main_concepts(content, learning_unit)
        metadata.sub_concepts = self._extract_sub_concepts(content, metadata.main_concepts)
        metadata.concept_relationships = self._map_concept_relationships(
            metadata.main_concepts, metadata.sub_concepts, content
        )
        metadata.concept_definitions = self._extract_definitions(content)
        
        # Assess difficulty and cognitive levels
        metadata.difficulty_level = self._assess_difficulty_level(content, learning_unit, grade_level)
        metadata.cognitive_levels = self._analyze_cognitive_levels(learning_unit)
        metadata.reading_level = self._analyze_reading_level(content)
        metadata.prerequisite_concepts = self._identify_prerequisites(
            metadata.main_concepts, grade_level, subject
        )
        
        # Extract educational context
        metadata.common_misconceptions = self._identify_misconceptions(
            metadata.main_concepts, content
        )
        metadata.real_world_applications = self._extract_applications(content)
        metadata.career_connections = self._identify_career_connections(
            metadata.main_concepts, subject
        )
        metadata.historical_context = self._extract_historical_context(content)
        
        # Extract content types (ENHANCED)
        content_types_data = self._extract_content_types(content)
        metadata.content_types = content_types_data['types']
        metadata.has_basic_concepts = content_types_data['has_basic_concepts']
        metadata.has_real_world_applications = content_types_data['has_real_world_applications']
        metadata.has_practical_uses = content_types_data['has_practical_uses']
        metadata.has_conceptual_explanations = content_types_data['has_conceptual_explanations']
        metadata.has_definitions = content_types_data['has_definitions']
        metadata.has_physical_phenomena = content_types_data['has_physical_phenomena']
        metadata.has_experimental_procedures = content_types_data['has_experimental_procedures']
        metadata.has_hands_on_activities = content_types_data['has_hands_on_activities']
        
        # Analyze skills and competencies
        metadata.skills_developed = self._analyze_skills_developed(learning_unit)
        metadata.competencies = self._map_competencies(metadata.skills_developed, subject)
        metadata.assessment_objectives = self._extract_assessment_objectives(learning_unit)
        
        # Calculate quality indicators
        metadata.content_depth = self._calculate_content_depth(learning_unit, metadata)
        metadata.pedagogical_completeness = self._assess_pedagogical_completeness(learning_unit)
        metadata.conceptual_clarity = self._assess_conceptual_clarity(content, metadata)
        metadata.engagement_level = self._assess_engagement_level(learning_unit)
        
        return metadata
    
    def _extract_content_types(self, content: str) -> Dict[str, Any]:
        """Extract and classify content types from text"""
        content_lower = content.lower()
        detected_types = []
        type_flags = {
            'has_basic_concepts': False,
            'has_real_world_applications': False,
            'has_practical_uses': False,
            'has_conceptual_explanations': False,
            'has_definitions': False,
            'has_physical_phenomena': False,
            'has_experimental_procedures': False,
            'has_hands_on_activities': False
        }
        
        # Check each content type
        for content_type, patterns in self.content_type_patterns.items():
            type_detected = False
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    type_detected = True
                    break
            
            if type_detected:
                detected_types.append(content_type)
                
                # Set specific flags
                if content_type == 'basic_concepts':
                    type_flags['has_basic_concepts'] = True
                elif content_type == 'real_world_applications':
                    type_flags['has_real_world_applications'] = True
                elif content_type == 'practical_uses':
                    type_flags['has_practical_uses'] = True
                elif content_type == 'conceptual_explanations':
                    type_flags['has_conceptual_explanations'] = True
                elif content_type == 'definitions':
                    type_flags['has_definitions'] = True
                elif content_type == 'physical_phenomena':
                    type_flags['has_physical_phenomena'] = True
                elif content_type == 'experimental_procedures':
                    type_flags['has_experimental_procedures'] = True
                elif content_type == 'hands_on_activities':
                    type_flags['has_hands_on_activities'] = True
        
        return {
            'types': detected_types,
            **type_flags
        }
    
    def _initialize_concept_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for concept extraction"""
        return {
            'physics': [
                r'\b(force|motion|energy|power|work|acceleration|velocity|speed)\b',
                r'\b(mass|weight|density|pressure|temperature|heat)\b',
                r'\b(electric|magnetic|current|voltage|resistance|circuit)\b',
                r'\b(wave|frequency|amplitude|sound|light|optics)\b',
                r'\b(atom|molecule|nucleus|electron|proton|neutron)\b'
            ],
            'chemistry': [
                r'\b(element|compound|mixture|solution|reaction|catalyst)\b',
                r'\b(acid|base|salt|pH|oxidation|reduction)\b',
                r'\b(carbon|hydrogen|oxygen|nitrogen|periodic table)\b',
                r'\b(bond|ionic|covalent|metallic|molecular)\b'
            ],
            'biology': [
                r'\b(cell|tissue|organ|system|organism|species)\b',
                r'\b(DNA|gene|chromosome|heredity|evolution|natural selection)\b',
                r'\b(photosynthesis|respiration|digestion|circulation)\b',
                r'\b(ecosystem|environment|biodiversity|conservation)\b'
            ],
            'mathematics': [
                r'\b(number|algebra|geometry|trigonometry|calculus)\b',
                r'\b(equation|function|graph|coordinate|angle)\b',
                r'\b(probability|statistics|data|mean|median|mode)\b'
            ]
        }
    
    def _initialize_objective_patterns(self) -> List[str]:
        """Initialize patterns for learning objective extraction"""
        return [
            r'(?:students?\s+will\s+be\s+able\s+to|you\s+will\s+learn|objectives?:?\s*)(.*?)(?:\n|$)',
            r'(?:by\s+the\s+end\s+of\s+this\s+(?:chapter|section|lesson))(.*?)(?:\n|$)',
            r'(?:after\s+studying\s+this)(.*?)(?:\n|$)',
            r'(?:on\s+completion\s+of\s+this)(.*?)(?:\n|$)',
            r'(?:learning\s+outcomes?:?\s*)(.*?)(?:\n|$)',
            r'(?:understand|explain|describe|calculate|analyze|apply|demonstrate)\s+([^.]+)',
            r'(?:define|identify|list|compare|contrast|evaluate)\s+([^.]+)'
        ]
    
    def _initialize_skill_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for skill identification"""
        return {
            'cognitive_skills': [
                r'\b(understand|comprehend|analyze|synthesize|evaluate|apply)\b',
                r'\b(compare|contrast|classify|categorize|organize)\b',
                r'\b(explain|describe|interpret|predict|hypothesize)\b'
            ],
            'practical_skills': [
                r'\b(measure|calculate|compute|solve|demonstrate)\b',
                r'\b(experiment|investigate|observe|record|collect)\b',
                r'\b(draw|sketch|construct|build|design)\b'
            ],
            'analytical_skills': [
                r'\b(analyze|examine|evaluate|assess|critique)\b',
                r'\b(interpret|infer|deduce|conclude|reason)\b',
                r'\b(question|inquire|investigate|explore)\b'
            ],
            'communication_skills': [
                r'\b(explain|describe|present|report|discuss)\b',
                r'\b(write|communicate|express|articulate)\b',
                r'\b(listen|read|comprehend|respond)\b'
            ]
        }
    
    def _initialize_misconception_patterns(self) -> Dict[str, List[str]]:
        """Initialize common misconception patterns by subject"""
        return {
            'physics': [
                "heavier objects fall faster",
                "force is needed to maintain motion",
                "heat and temperature are the same",
                "current is consumed in a circuit",
                "friction always opposes motion"
            ],
            'chemistry': [
                "chemical bonds are broken by heating",
                "atoms are indivisible",
                "acids are always dangerous",
                "all chemical reactions release energy",
                "metals conduct electricity because they contain electrons"
            ],
            'biology': [
                "evolution is just a theory",
                "acquired characteristics are inherited",
                "photosynthesis only occurs in leaves",
                "humans evolved from monkeys",
                "antibiotics kill viruses"
            ]
        }
    
    def _initialize_application_patterns(self) -> List[str]:
        """Initialize enhanced patterns for real-world application extraction"""
        return [
            # Basic application patterns
            r'(?:applications?|uses?|examples?):?\s*(.*?)(?:\n|$)',
            r'(?:real[- ]world|everyday|practical)\s+(?:applications?|examples?|uses?):?\s*(.*?)(?:\n|$)',
            r'(?:in\s+(?:industry|medicine|technology|engineering|agriculture|manufacturing|construction)):?\s*(.*?)(?:\n|$)',
            r'(?:used\s+in|applied\s+in|found\s+in):?\s*(.*?)(?:\n|$)',
            
            # Device and technology patterns
            r'(?:devices?|instruments?|equipment|machines?|systems?)\s+(?:that\s+use|using|based\s+on|utilizing)\s*(.*?)(?:\n|$)',
            r'(?:smartphones?|computers?|televisions?|radios?|speakers?|microphones?)\s+(?:use|work\s+by|operate\s+on)\s*(.*?)(?:\n|$)',
            
            # Everyday life patterns
            r'(?:in\s+(?:everyday\s+life|daily\s+life|our\s+daily|common\s+life|real\s+life))\s*(.*?)(?:\n|$)',
            r'(?:we\s+(?:use|see|experience|encounter)|you\s+(?:can\s+)?(?:see|hear|feel|observe))\s*(.*?)(?:\n|$)',
            
            # Field-specific enhanced patterns
            r'(?:medical|healthcare|hospital|clinical)\s+(?:applications?|uses?|equipment)\s*(.*?)(?:\n|$)',
            r'(?:industrial|manufacturing|automotive|aerospace)\s+(?:applications?|uses?|processes?)\s*(.*?)(?:\n|$)',
            r'(?:communication|telecommunications?|broadcasting)\s+(?:systems?|technology|applications?)\s*(.*?)(?:\n|$)',
            
            # Natural phenomena applications
            r'(?:animals?|birds?|mammals?|creatures?)\s+(?:use|produce|generate|emit)\s*(.*?)(?:\n|$)',
            r'(?:bats?|dolphins?|whales?|porpoises?)\s+(?:use|produce|emit)\s*(.*?)(?:\n|$)'
        ]
    
    def _initialize_content_type_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for content type detection"""
        return {
            'basic_concepts': [
                r'(?:^|\n)\s*([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:is|are|refers?\s+to|means?|can\s+be\s+defined\s+as)',
                r'(?:key\s+points?|important\s+concepts?|fundamental\s+ideas?|basic\s+principles?)',
                r'(?:remember|note|keep\s+in\s+mind|it\s+is\s+important)',
                r'(?:concept|idea|principle|theory|law)\s+(?:of|that|which)'
            ],
            'real_world_applications': [
                r'(?:applications?|uses?|practical\s+(?:applications?|uses?))',
                r'(?:in\s+(?:everyday\s+life|daily\s+life|real\s+life|our\s+daily))',
                r'(?:devices?|instruments?|equipment|machines?)\s+(?:that\s+use|using|based\s+on)',
                r'(?:used\s+in|applied\s+in|found\s+in)\s+(?:industry|medicine|technology)',
                r'(?:animals?|birds?|mammals?)\s+(?:use|produce|generate|emit)',
                r'(?:smartphones?|computers?|televisions?|radios?)\s+(?:use|work\s+by)'
            ],
            'practical_uses': [
                r'(?:How\s+to\s+(?:use|apply|calculate|find|determine))',
                r'(?:steps?|procedures?|methods?|techniques?)\s+(?:to|for)',
                r'(?:tips?|hints?|suggestions?|guidelines?)\s+(?:for|to)'
            ],
            'conceptual_explanations': [
                r'(?:this\s+(?:means|implies|shows|demonstrates)|in\s+other\s+words)',
                r'(?:because|since|as\s+a\s+result|therefore|thus|hence)',
                r'(?:Why\s+(?:does|do|is|are)|How\s+(?:does|do|is|are))',
                r'(?:the\s+reason\s+(?:is|for\s+this)|to\s+understand\s+this)'
            ],
            'definitions': [
                r'(?:Definition|Define):?\s*',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:\s*(.{10,200})',
                r'(?:is\s+defined\s+as|can\s+be\s+defined\s+as|means\s+that)'
            ],
            'physical_phenomena': [
                r'(?:observe|notice|see|watch|look\s+at)',
                r'(?:phenomenon|phenomena|occurs?|happens?|takes?\s+place)',
                r'(?:visible|observable|apparent|evident)\s+(?:effects?|changes?|results?)'
            ],
            'experimental_procedures': [
                r'(?:experiment|activity|procedure|method|protocol)',
                r'(?:materials?\s+(?:required|needed)|equipment|apparatus)',
                r'(?:step\s+\d+|first|next|then|finally)',
                r'(?:measure|record|observe|calculate|determine)'
            ],
            'hands_on_activities': [
                r'(?:ACTIVITY|Activity)\s+\d+\.\d+',
                r'(?:try\s+this|do\s+this|perform|carry\s+out)',
                r'(?:take\s+a|use\s+a|get\s+a)\s+(?:ruler|scale|string|ball)',
                r'(?:touch|feel|hold|press|strike|hit)'
            ]
        }
    
    def _initialize_difficulty_indicators(self) -> Dict[str, List[str]]:
        """Initialize difficulty level indicators"""
        return {
            'beginner': [
                'basic', 'simple', 'introduction', 'elementary', 'fundamental',
                'easy', 'straightforward', 'observe', 'identify', 'list'
            ],
            'intermediate': [
                'calculate', 'analyze', 'compare', 'explain', 'apply',
                'demonstrate', 'solve', 'determine', 'interpret'
            ],
            'advanced': [
                'evaluate', 'synthesize', 'design', 'create', 'critique',
                'complex', 'sophisticated', 'advanced', 'derive', 'prove'
            ]
        }
    
    def _extract_learning_objectives(self, content: str, learning_unit) -> List[str]:
        """Extract explicit and implicit learning objectives"""
        objectives = []
        
        # Extract explicit objectives from content
        for pattern in self.objective_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, str) and len(match.strip()) > 10:
                    objectives.append(match.strip())
        
        # Infer objectives from activities and examples
        if learning_unit.activities:
            for activity in learning_unit.activities:
                if 'content' in activity:
                    obj = self._infer_objective_from_activity(activity['content'])
                    if obj:
                        objectives.append(obj)
        
        if learning_unit.examples:
            for example in learning_unit.examples:
                if 'content' in example:
                    obj = self._infer_objective_from_example(example['content'])
                    if obj:
                        objectives.append(obj)
        
        return list(set(objectives))  # Remove duplicates
    
    def _infer_objective_from_activity(self, activity_content: str) -> str:
        """Infer learning objective from activity content"""
        activity_lower = activity_content.lower()
        
        if 'observe' in activity_lower:
            return "Develop observation skills through hands-on investigation"
        elif 'measure' in activity_lower:
            return "Learn measurement techniques and data collection"
        elif 'calculate' in activity_lower:
            return "Apply mathematical concepts to solve problems"
        elif 'experiment' in activity_lower:
            return "Understand scientific method through experimentation"
        elif 'compare' in activity_lower:
            return "Develop analytical thinking through comparison"
        else:
            return "Apply theoretical concepts through practical activity"
    
    def _infer_objective_from_example(self, example_content: str) -> str:
        """Infer learning objective from example content"""
        example_lower = example_content.lower()
        
        if 'solution' in example_lower or 'solve' in example_lower:
            return "Solve problems using learned concepts and formulas"
        elif 'calculate' in example_lower:
            return "Apply mathematical relationships to numerical problems"
        elif 'given' in example_lower and 'find' in example_lower:
            return "Analyze given information to find unknown quantities"
        else:
            return "Understand concept application through worked examples"
    
    def _find_explicit_objectives(self, content: str) -> List[str]:
        """Find explicitly stated learning objectives"""
        explicit_objectives = []
        
        # Look for objective sections
        objective_sections = re.findall(
            r'(?:objectives?|learning\s+outcomes?):?\s*(.*?)(?:\n\n|\n[A-Z])',
            content, re.IGNORECASE | re.DOTALL
        )
        
        for section in objective_sections:
            # Split by bullet points or numbers
            objectives = re.split(r'[•\-\*\d+\.]\s*', section)
            for obj in objectives:
                obj = obj.strip()
                if len(obj) > 15 and not obj.startswith(('By', 'After', 'On')):
                    explicit_objectives.append(obj)
        
        return explicit_objectives
    
    def _infer_implicit_objectives(self, learning_unit, subject: str) -> List[str]:
        """Infer learning objectives from content structure"""
        implicit_objectives = []
        
        # From activities
        if learning_unit.activities:
            implicit_objectives.append("Develop practical understanding through hands-on activities")
            implicit_objectives.append("Apply theoretical concepts to real situations")
        
        # From examples
        if learning_unit.examples:
            implicit_objectives.append("Solve problems using learned concepts")
            implicit_objectives.append("Apply mathematical relationships and formulas")
        
        # From special boxes
        if learning_unit.special_boxes:
            for box in learning_unit.special_boxes:
                if 'biography' in box.get('type', '').lower():
                    implicit_objectives.append("Understand historical development of scientific concepts")
                elif 'application' in box.get('type', '').lower():
                    implicit_objectives.append("Connect learning to real-world applications")
        
        # From assessments
        if learning_unit.assessments:
            implicit_objectives.append("Evaluate understanding through assessment")
            implicit_objectives.append("Demonstrate mastery of key concepts")
        
        return implicit_objectives
    
    def _extract_main_concepts(self, content: str, learning_unit) -> List[str]:
        """Extract main concepts from content using adaptive physics-aware recognition"""
        concepts = set()
        
        # Common words to exclude
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
            'should', 'now', 'new', 'example', 'given', 'which', 'chapter', 'section'
        }
        
        # Subject-specific concept patterns
        subject_concepts = self._get_subject_concepts(learning_unit)
        
        # Extract from explicit definitions
        definition_patterns = [
            r'(?:^|\n)([A-Z][a-z]+(?:\s+[a-z]+)*)\s+is\s+(?:defined\s+as|a|an)\s+',
            r'(?:define|definition\s+of)\s+([a-z]+(?:\s+[a-z]+)*)',
            r'(?:^|\n)([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:means|refers\s+to)\s+',
            r'(?:concept\s+of)\s+([a-z]+(?:\s+[a-z]+)*)'
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                concept = match.strip()
                # Clean and validate concept
                if self._is_valid_concept(concept, stop_words):
                    concepts.add(self._normalize_concept(concept))
        
        # Extract from section titles and headings
        heading_patterns = [
            r'^\d+\.\d+\s+([A-Z][a-zA-Z\s]+?)(?:\n|$)',  # Numbered sections
            r'^([A-Z][a-zA-Z\s]+?):(?:\s|$)',  # Colon-ended headings
            r'^(?:Chapter|Section)\s+\d+[:\s]+([A-Z][a-zA-Z\s]+?)(?:\n|$)'  # Chapter/section titles
        ]
        
        for pattern in heading_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                concept = match.strip()
                if self._is_valid_concept(concept, stop_words) and len(concept.split()) <= 4:
                    concepts.add(concept)
        
        # Extract physics concepts from content using adaptive recognition
        physics_patterns = [
            r'\b(motion|rest|position|displacement|distance|speed|velocity|acceleration)\b',
            r'\b(force|mass|weight|gravity|friction|pressure|energy|power|work)\b',
            r'\b(time|rate|change|uniform|non-uniform|reference\s+point|frame\s+of\s+reference)\b',
            r'\b(scalar|vector|magnitude|direction|measurement|unit)\b'
        ]
        
        for pattern in physics_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                concept = match.strip().title()
                if concept.lower() not in stop_words:
                    concepts.add(concept)
        
        # Extract from formulas and mathematical content
        if learning_unit.formulas:
            physics_concepts = ['force', 'acceleration', 'velocity', 'energy', 'power', 'work']
            for concept in physics_concepts:
                if concept.lower() in content.lower():
                    concepts.add(concept.title())
        
        # Filter and return unique concepts
        filtered_concepts = []
        for concept in concepts:
            if isinstance(concept, str) and len(concept) > 2:
                filtered_concepts.append(concept)
        
        return list(set(filtered_concepts))[:20]  # Limit to top 20 concepts
    
    def _is_valid_concept(self, concept: str, stop_words: set) -> bool:
        """Check if a concept is valid and meaningful"""
        if not concept or len(concept) < 3:
            return False
        
        # Check if it's just stop words
        words = concept.lower().split()
        if all(word in stop_words for word in words):
            return False
        
        # Check if it's too generic
        generic_terms = {'activity', 'example', 'figure', 'table', 'question', 'answer', 'solution'}
        if concept.lower() in generic_terms:
            return False
        
        # Must contain at least one meaningful word
        meaningful_word_found = False
        for word in words:
            if len(word) > 3 and word not in stop_words:
                meaningful_word_found = True
                break
        
        return meaningful_word_found
    
    def _normalize_concept(self, concept: str) -> str:
        """Normalize concept formatting"""
        # Title case for proper formatting
        words = concept.split()
        normalized = []
        for word in words:
            if len(word) > 3:
                normalized.append(word.capitalize())
            else:
                normalized.append(word.lower())
        return ' '.join(normalized)
    
    def _get_subject_concepts(self, learning_unit) -> Dict[str, List[str]]:
        """Get subject-specific concepts based on content"""
        # This could be enhanced with more sophisticated subject detection
        return self.concept_patterns
    
    def _extract_sub_concepts(self, content: str, main_concepts: List[str]) -> List[str]:
        """Extract sub-concepts related to main concepts"""
        sub_concepts = set()
        
        for main_concept in main_concepts:
            # Look for related terms near main concepts
            concept_pattern = rf'\b{re.escape(main_concept.lower())}\b'
            matches = list(re.finditer(concept_pattern, content.lower()))
            
            for match in matches:
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end]
                
                # Extract capitalized terms (potential concepts)
                terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', context)
                for term in terms:
                    if 3 <= len(term) <= 30 and term.lower() != main_concept.lower():
                        sub_concepts.add(term)
        
        return list(sub_concepts)
    
    def _map_concept_relationships(self, main_concepts: List[str], 
                                 sub_concepts: List[str], content: str) -> Dict[str, List[str]]:
        """Map relationships between concepts"""
        relationships = defaultdict(list)
        
        # Find concepts that appear together
        for main_concept in main_concepts:
            for sub_concept in sub_concepts:
                # Check if they appear in the same paragraph
                paragraphs = content.split('\n\n')
                for paragraph in paragraphs:
                    if (main_concept.lower() in paragraph.lower() and 
                        sub_concept.lower() in paragraph.lower()):
                        relationships[main_concept].append(sub_concept)
        
        # Find causal relationships
        causal_patterns = [
            r'([A-Z][a-z\s]+)\s+(?:causes?|leads?\s+to|results?\s+in)\s+([A-Z][a-z\s]+)',
            r'([A-Z][a-z\s]+)\s+(?:depends?\s+on|requires?|needs?)\s+([A-Z][a-z\s]+)'
        ]
        
        for pattern in causal_patterns:
            matches = re.findall(pattern, content)
            for cause, effect in matches:
                cause = cause.strip()
                effect = effect.strip()
                if cause in main_concepts or cause in sub_concepts:
                    relationships[cause].append(effect)
        
        return dict(relationships)
    
    def _extract_definitions(self, content: str) -> Dict[str, str]:
        """Extract concept definitions from content"""
        definitions = {}
        
        definition_patterns = [
            r'Definition:?\s*([^.]+)\s+is\s+([^.]+)',
            r'([A-Z][a-z\s]+)\s+is\s+defined\s+as\s+([^.]+)',
            r'([A-Z][a-z\s]+)\s+means\s+([^.]+)',
            r'([A-Z][a-z\s]+):\s*([A-Z][^.]+)'
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) == 2:
                    concept, definition = match
                    concept = concept.strip()
                    definition = definition.strip()
                    if 3 <= len(concept) <= 50 and 10 <= len(definition) <= 500:
                        definitions[concept] = definition
        
        return definitions
    
    def _assess_difficulty_level(self, content: str, learning_unit, grade_level: int) -> str:
        """Assess the difficulty level of the content"""
        scores = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
        
        # Analyze vocabulary complexity
        words = re.findall(r'\b\w+\b', content.lower())
        word_counter = Counter(words)
        
        for level, indicators in self.difficulty_indicators.items():
            for indicator in indicators:
                scores[level] += word_counter.get(indicator, 0)
        
        # Consider grade level
        if grade_level <= 6:
            scores['beginner'] += 10
        elif grade_level <= 8:
            scores['intermediate'] += 10
        else:
            scores['advanced'] += 5
        
        # Consider content complexity
        if learning_unit.formulas:
            scores['intermediate'] += len(learning_unit.formulas) * 2
        
        if learning_unit.mathematical_content:
            scores['advanced'] += len(learning_unit.mathematical_content)
        
        # Return highest scoring level
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _analyze_cognitive_levels(self, learning_unit) -> List[str]:
        """Analyze cognitive levels using Bloom's taxonomy"""
        levels = set()
        
        # Knowledge level
        if learning_unit.intro_content or learning_unit.concepts:
            levels.add('knowledge')
        
        # Comprehension level
        if learning_unit.activities:
            levels.add('comprehension')
        
        # Application level
        if learning_unit.examples or learning_unit.formulas:
            levels.add('application')
        
        # Analysis level
        if learning_unit.questions or learning_unit.assessments:
            levels.add('analysis')
        
        # Synthesis level
        if any('design' in str(box).lower() or 'create' in str(box).lower() 
               for box in learning_unit.special_boxes):
            levels.add('synthesis')
        
        # Evaluation level
        if any('evaluate' in str(q).lower() or 'critique' in str(q).lower() 
               for q in learning_unit.questions):
            levels.add('evaluation')
        
        return list(levels)
    
    def _analyze_reading_level(self, content: str) -> Dict[str, Any]:
        """Analyze reading level and complexity"""
        words = re.findall(r'\b\w+\b', content)
        sentences = re.split(r'[.!?]+', content)
        
        if not words or not sentences:
            return {'reading_level': 'unknown', 'complexity': 'medium'}
        
        avg_words_per_sentence = len(words) / len(sentences)
        avg_syllables_per_word = sum(self._count_syllables(word) for word in words) / len(words)
        
        # Simplified reading level calculation
        if avg_words_per_sentence < 15 and avg_syllables_per_word < 1.5:
            reading_level = 'elementary'
        elif avg_words_per_sentence < 20 and avg_syllables_per_word < 2.0:
            reading_level = 'middle_school'
        else:
            reading_level = 'high_school'
        
        return {
            'reading_level': reading_level,
            'avg_words_per_sentence': avg_words_per_sentence,
            'avg_syllables_per_word': avg_syllables_per_word,
            'complexity': 'high' if avg_words_per_sentence > 25 else 'medium'
        }
    
    def _count_syllables(self, word: str) -> int:
        """Simple syllable counting"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_char_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_char_was_vowel:
                    syllable_count += 1
                prev_char_was_vowel = True
            else:
                prev_char_was_vowel = False
        
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _identify_prerequisites(self, main_concepts: List[str], 
                              grade_level: int, subject: str) -> List[str]:
        """Identify prerequisite concepts"""
        prerequisites = []
        
        # Subject-specific prerequisite mappings
        prerequisite_map = {
            'force': ['motion', 'mass', 'acceleration'],
            'energy': ['work', 'force', 'motion'],
            'power': ['energy', 'work', 'time'],
            'velocity': ['speed', 'direction', 'displacement'],
            'acceleration': ['velocity', 'time', 'change'],
            'pressure': ['force', 'area', 'surface'],
            'density': ['mass', 'volume', 'substance']
        }
        
        for concept in main_concepts:
            concept_lower = concept.lower()
            if concept_lower in prerequisite_map:
                prerequisites.extend(prerequisite_map[concept_lower])
        
        # Grade-level specific prerequisites
        if grade_level >= 9:
            if subject.lower() == 'physics':
                prerequisites.extend(['basic mathematics', 'algebra', 'geometry'])
        
        return list(set(prerequisites))
    
    def _identify_misconceptions(self, main_concepts: List[str], content: str) -> List[str]:
        """Identify potential misconceptions"""
        misconceptions = []
        
        # Look for correction patterns
        correction_patterns = [
            r'(?:not|never|doesn\'t|don\'t|incorrect|wrong|misconception):?\s*([^.]+)',
            r'(?:contrary\s+to|unlike|however|but):?\s*([^.]+)',
            r'(?:remember\s+that|note\s+that|important):?\s*([^.]+)'
        ]
        
        for pattern in correction_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 20:
                    misconceptions.append(match.strip())
        
        # Add subject-specific common misconceptions
        for concept in main_concepts:
            concept_lower = concept.lower()
            for subject, subject_misconceptions in self.misconception_patterns.items():
                for misconception in subject_misconceptions:
                    if any(word in concept_lower for word in misconception.split()):
                        misconceptions.append(misconception)
        
        return misconceptions
    
    def _extract_applications(self, content: str) -> List[str]:
        """Extract clean, meaningful real-world applications"""
        applications = set()
        
        # Enhanced patterns for complete application descriptions
        enhanced_patterns = [
            # DO YOU KNOW sections often contain applications
            r'DO YOU KNOW\??\s*([^.!?]*(?:used|applied|helps|found)[^.!?]+[.!?])',
            # Direct application statements
            r'(?:This\s+is\s+used\s+in|Applications?\s+include|Used\s+in)\s*([^.!?]+[.!?])',
            # Real-world context
            r'(?:In\s+(?:real|everyday|daily)\s+life,?\s*)([^.!?]+[.!?])',
            # Practical uses
            r'(?:practical(?:ly)?|real-world)\s+(?:application|use|example)s?\s*(?:include|are|:)?\s*([^.!?]+[.!?])',
            # Technology and industry
            r'(?:In\s+(?:technology|industry|medicine|engineering),?\s*)([^.!?]+[.!?])'
        ]
        
        for pattern in enhanced_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                cleaned = self._clean_application_text(match)
                if cleaned and len(cleaned) > 20:
                    applications.add(cleaned)
        
        # Extract from specific sections
        sections_to_check = [
            ('DO YOU KNOW', r'DO YOU KNOW\??(.+?)(?=\n\n|\nActivity|\nExample|$)'),
            ('Applications', r'Applications?:?(.+?)(?=\n\n|$)'),
            ('Real-world', r'Real-world\s+(?:applications?|examples?):?(.+?)(?=\n\n|$)')
        ]
        
        for section_name, pattern in sections_to_check:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Extract complete sentences about applications
                sentences = re.split(r'[.!?]+', match)
                for sentence in sentences:
                    cleaned = self._clean_application_text(sentence)
                    if cleaned and self._is_valid_application(cleaned):
                        applications.add(cleaned)
        
        # Look for contextual applications
        application_indicators = [
            'helps us', 'allows us', 'enables us', 'makes it possible',
            'is essential for', 'is important for', 'is used to',
            'examples include', 'such as in', 'for instance in'
        ]
        
        sentences = re.split(r'(?<=[.!?])\s+', content)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in application_indicators):
                cleaned = self._clean_application_text(sentence)
                if cleaned and self._is_valid_application(cleaned):
                    applications.add(cleaned)
        
        # Convert to list and limit
        return list(applications)[:10]  # Return top 10 applications
    
    def _identify_career_connections(self, main_concepts: List[str], subject: str) -> List[str]:
        """Identify career connections for concepts"""
        career_connections = []
        
        # Subject-specific career mappings
        career_map = {
            'physics': {
                'force': ['mechanical engineer', 'aerospace engineer', 'robotics engineer'],
                'energy': ['renewable energy specialist', 'power plant engineer', 'energy analyst'],
                'motion': ['automotive engineer', 'sports analyst', 'animation specialist'],
                'electricity': ['electrical engineer', 'electronics technician', 'power systems engineer']
            },
            'chemistry': {
                'reaction': ['chemical engineer', 'pharmaceutical researcher', 'materials scientist'],
                'compound': ['drug developer', 'cosmetics chemist', 'food scientist'],
                'analysis': ['forensic scientist', 'environmental analyst', 'quality control specialist']
            },
            'biology': {
                'cell': ['medical researcher', 'biotechnologist', 'genetic counselor'],
                'ecosystem': ['environmental scientist', 'conservation biologist', 'park ranger'],
                'evolution': ['evolutionary biologist', 'paleontologist', 'museum curator']
            }
        }
        
        subject_lower = subject.lower()
        if subject_lower in career_map:
            for concept in main_concepts:
                concept_lower = concept.lower()
                for career_concept, careers in career_map[subject_lower].items():
                    if career_concept in concept_lower:
                        career_connections.extend(careers)
        
        return list(set(career_connections))
    
    def _extract_historical_context(self, content: str) -> List[str]:
        """Extract historical context and background"""
        historical_context = []
        
        # Look for historical patterns
        historical_patterns = [
            r'(?:discovered|invented|formulated)\s+by\s+([^.]+)',
            r'(?:in\s+\d{3,4}|century|years?\s+ago)\s*([^.]+)',
            r'(?:historical|history|background|development):?\s*([^.]+)',
            r'(?:scientist|researcher|physicist|chemist|biologist)\s+([^.]+)'
        ]
        
        for pattern in historical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 15:
                    historical_context.append(match.strip())
        
        # Look for biography boxes
        if 'biography' in content.lower() or 'about the scientist' in content.lower():
            paragraphs = content.split('\n\n')
            for paragraph in paragraphs:
                if any(keyword in paragraph.lower() for keyword in ['biography', 'scientist', 'discovered', 'invented']):
                    if 50 <= len(paragraph.strip()) <= 500:
                        historical_context.append(paragraph.strip())
        
        return historical_context
    
    def _analyze_skills_developed(self, learning_unit) -> List[str]:
        """Analyze skills developed through the learning unit"""
        skills = set()
        
        # From activities
        if learning_unit.activities:
            skills.update(['observation', 'experimentation', 'data_collection', 'hands_on_skills'])
            for activity in learning_unit.activities:
                content = str(activity.get('content', ''))
                if 'measure' in content.lower():
                    skills.add('measurement')
                if 'calculate' in content.lower():
                    skills.add('calculation')
                if 'observe' in content.lower():
                    skills.add('observation')
        
        # From examples
        if learning_unit.examples:
            skills.update(['problem_solving', 'mathematical_application', 'logical_thinking'])
        
        # From questions
        if learning_unit.questions:
            skills.update(['analytical_thinking', 'evaluation', 'critical_thinking'])
        
        # From assessments
        if learning_unit.assessments:
            skills.update(['self_assessment', 'reflection', 'knowledge_application'])
        
        # From mathematical content
        if learning_unit.formulas or learning_unit.mathematical_content:
            skills.update(['mathematical_reasoning', 'quantitative_analysis', 'formula_application'])
        
        return list(skills)
    
    def _map_competencies(self, skills: List[str], subject: str) -> List[str]:
        """Map skills to educational competencies"""
        competency_map = {
            'observation': 'Scientific Inquiry',
            'experimentation': 'Scientific Method',
            'problem_solving': 'Problem Solving',
            'mathematical_application': 'Mathematical Literacy',
            'analytical_thinking': 'Critical Thinking',
            'data_collection': 'Data Analysis',
            'measurement': 'Quantitative Skills',
            'communication': 'Communication Skills',
            'collaboration': 'Collaborative Learning'
        }
        
        competencies = set()
        for skill in skills:
            if skill in competency_map:
                competencies.add(competency_map[skill])
        
        # Add subject-specific competencies
        if subject.lower() == 'physics':
            competencies.update(['Scientific Reasoning', 'Mathematical Modeling'])
        elif subject.lower() == 'chemistry':
            competencies.update(['Chemical Reasoning', 'Laboratory Skills'])
        elif subject.lower() == 'biology':
            competencies.update(['Biological Understanding', 'Environmental Awareness'])
        
        return list(competencies)
    
    def _extract_assessment_objectives(self, learning_unit) -> List[str]:
        """Extract assessment objectives from the learning unit"""
        assessment_objectives = []
        
        # From questions
        if learning_unit.questions:
            assessment_objectives.extend([
                'Evaluate understanding of key concepts',
                'Test application of learned principles',
                'Assess problem-solving abilities'
            ])
        
        # From assessments
        if learning_unit.assessments:
            for assessment in learning_unit.assessments:
                assessment_type = assessment.get('type', '').lower()
                if 'multiple choice' in assessment_type:
                    assessment_objectives.append('Test factual knowledge and understanding')
                elif 'short answer' in assessment_type:
                    assessment_objectives.append('Assess explanatory skills')
                elif 'long answer' in assessment_type:
                    assessment_objectives.append('Evaluate comprehensive understanding')
                elif 'project' in assessment_type:
                    assessment_objectives.append('Assess practical application and creativity')
        
        return assessment_objectives
    
    def _calculate_content_depth(self, learning_unit, metadata: EducationalMetadata) -> float:
        """Calculate content depth score"""
        depth_score = 0.0
        
        # Base content
        if learning_unit.intro_content:
            depth_score += 0.2
        
        # Interactive elements
        if learning_unit.activities:
            depth_score += 0.2
        if learning_unit.examples:
            depth_score += 0.2
        
        # Enrichment content
        if learning_unit.special_boxes:
            depth_score += 0.1
        if learning_unit.figures:
            depth_score += 0.1
        
        # Assessment and questions
        if learning_unit.questions or learning_unit.assessments:
            depth_score += 0.1
        
        # Concept complexity
        if len(metadata.main_concepts) > 3:
            depth_score += 0.05
        if len(metadata.concept_relationships) > 2:
            depth_score += 0.05
        
        return min(1.0, depth_score)
    
    def _assess_pedagogical_completeness(self, learning_unit) -> float:
        """Assess pedagogical completeness"""
        completeness_score = 0.0
        
        # Learning sequence completeness
        if learning_unit.intro_content:  # Introduction
            completeness_score += 0.25
        if learning_unit.activities:  # Practice
            completeness_score += 0.25
        if learning_unit.examples:  # Application
            completeness_score += 0.25
        if learning_unit.questions or learning_unit.assessments:  # Assessment
            completeness_score += 0.25
        
        return completeness_score
    
    def _assess_conceptual_clarity(self, content: str, metadata: EducationalMetadata) -> float:
        """Assess conceptual clarity"""
        clarity_score = 0.0
        
        # Presence of definitions
        if metadata.concept_definitions:
            clarity_score += 0.3
        
        # Clear concept relationships
        if metadata.concept_relationships:
            clarity_score += 0.2
        
        # Examples and illustrations
        if 'example' in content.lower():
            clarity_score += 0.2
        
        # Structured presentation
        if re.search(r'\d+\.\s', content):  # Numbered points
            clarity_score += 0.15
        
        # Clear language
        reading_level = metadata.reading_level.get('reading_level', 'high_school')
        if reading_level in ['elementary', 'middle_school']:
            clarity_score += 0.15
        
        return min(1.0, clarity_score)
    
    def _assess_engagement_level(self, learning_unit) -> float:
        """Assess engagement level of content"""
        engagement_score = 0.0
        
        # Interactive elements
        if learning_unit.activities:
            engagement_score += 0.3
        
        # Varied content types
        content_variety = sum([
            bool(learning_unit.examples),
            bool(learning_unit.figures),
            bool(learning_unit.special_boxes),
            bool(learning_unit.questions),
            bool(learning_unit.assessments)
        ])
        engagement_score += (content_variety / 5) * 0.4
        
        # Real-world connections
        if learning_unit.special_boxes:
            for box in learning_unit.special_boxes:
                if any(keyword in str(box).lower() for keyword in ['application', 'real', 'everyday']):
                    engagement_score += 0.1
                    break
        
        # Assessment variety
        if learning_unit.questions and learning_unit.assessments:
            engagement_score += 0.2
        
        return min(1.0, engagement_score)
    
    def _clean_application_text(self, text: str) -> str:
        """Clean and normalize application text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove incomplete sentence fragments at start
        if text and text[0].islower():
            # Find first capital letter
            for i, char in enumerate(text):
                if char.isupper():
                    text = text[i:]
                    break
        
        # Ensure proper sentence ending
        if text and text[-1] not in '.!?':
            text += '.'
        
        # Clean up common issues
        text = re.sub(r'\s+([,.!?])', r'\1', text)  # Fix spacing before punctuation
        text = re.sub(r'([.!?])\s*\1+', r'\1', text)  # Remove duplicate punctuation
        text = text.strip()
        
        # Ensure first letter is capitalized
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    def _is_valid_application(self, text: str) -> bool:
        """Check if the application text is valid and meaningful"""
        if not text or len(text) < 20:
            return False
        
        # Must contain at least 3 words
        words = text.split()
        if len(words) < 3:
            return False
        
        # Should not be just a fragment
        fragment_indicators = [
            'the', 'and', 'or', 'but', 'of', 'in', 'to', 'for'
        ]
        first_word = words[0].lower()
        if first_word in fragment_indicators:
            return False
        
        # Should contain meaningful content
        meaningless_patterns = [
            r'^\d+',  # Starts with number
            r'^[a-z]',  # Starts with lowercase
            r'^\W',  # Starts with non-word character
        ]
        
        for pattern in meaningless_patterns:
            if re.match(pattern, text):
                return False
        
        return True


def main():
    """Test the metadata extraction engine"""
    print("🧠 Testing Metadata Extraction Engine")
    print("=" * 50)
    
    # This would be integrated with the main holistic system
    engine = MetadataExtractionEngine()
    print("✅ Metadata Extraction Engine initialized")
    print("📊 Pattern libraries loaded:")
    print(f"   • Concept patterns: {sum(len(v) for v in engine.concept_patterns.values())} patterns")
    print(f"   • Objective patterns: {len(engine.objective_patterns)} patterns")
    print(f"   • Skill patterns: {sum(len(v) for v in engine.skill_patterns.values())} patterns")
    print("🚀 Ready for integration with holistic chunker")


if __name__ == "__main__":
    main()