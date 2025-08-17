#!/usr/bin/env python3
"""
AI Integration Module for Enhanced Educational RAG System
Provides OpenAI and Anthropic Claude API integration for intelligent content analysis
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import time

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """Response from AI service"""
    content: str
    reasoning: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    tokens_used: int = 0
    model_used: str = ""
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class AIConfig:
    """Configuration for AI services"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 30
    max_retries: int = 3
    enable_reasoning: bool = True


class AIIntegrationService:
    """
    Central service for AI API integrations
    Supports both OpenAI and Anthropic Claude APIs
    """
    
    def __init__(self, config: AIConfig = None):
        self.config = config or self._load_default_config()
        self._setup_clients()
        
        # AI prompt templates
        self.templates = self._initialize_prompt_templates()
        
        # Usage tracking
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0
        }
        
        logger.info("AI Integration Service initialized")
    
    def _load_default_config(self) -> AIConfig:
        """Load AI configuration from environment variables"""
        return AIConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            default_model=os.getenv('DEFAULT_AI_MODEL', 'gpt-4'),
            max_tokens=int(os.getenv('MAX_AI_TOKENS', '2000')),
            temperature=float(os.getenv('AI_TEMPERATURE', '0.1')),
            timeout=int(os.getenv('AI_TIMEOUT', '30')),
            max_retries=int(os.getenv('AI_MAX_RETRIES', '3'))
        )
    
    def _setup_clients(self):
        """Initialize AI service clients"""
        self.openai_client = None
        self.anthropic_client = None
        
        # Setup OpenAI
        if self.config.openai_api_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        
        # Setup Anthropic
        if self.config.anthropic_api_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("Anthropic package not installed. Install with: pip install anthropic")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
    
    def _initialize_prompt_templates(self) -> Dict[str, str]:
        """Initialize AI prompt templates for educational content analysis"""
        return {
            'boundary_detection': """
You are an expert educational content analyst. Analyze the following NCERT educational content and identify natural learning unit boundaries.

Content:
{content}

Please identify:
1. Natural pedagogical boundaries where content can be meaningfully separated
2. Learning units that should stay together (activities with explanations, examples with context)
3. Optimal split points that preserve educational flow
4. Content types present in each learning unit (definitions, applications, examples, concepts, etc.)

IMPORTANT: Respond with ONLY a valid JSON object. Do not include any additional text before or after the JSON.

Response format:
{{
    "boundaries": [
        {{
            "position": 100,
            "type": "natural_break",
            "reasoning": "explanation of why this is a good boundary",
            "confidence": 0.8
        }}
    ],
    "learning_units": [
        {{
            "start": 0,
            "end": 200,
            "type": "activity",
            "description": "brief description",
            "educational_elements": ["list of elements contained"],
            "content_types": ["basic_concepts", "hands_on_activity", "practical_uses"],
            "learning_objectives": ["understand concept X", "demonstrate principle Y"]
        }}
    ]
}}
""",
            
            'concept_extraction': """
You are an expert in educational content analysis specializing in NCERT curriculum. Extract key concepts from this educational content.

Content:
{content}
Subject: {subject}
Grade Level: {grade_level}

Extract:
1. Main concepts (primary learning objectives)
2. Sub-concepts (supporting ideas)
3. Concept relationships (prerequisites, dependencies)
4. Educational context (applications, examples)
5. Content types present in this text

IMPORTANT: Respond with ONLY a valid JSON object. Do not include any additional text.

Response format:
{{
    "main_concepts": ["concept1", "concept2"],
    "sub_concepts": ["subconcept1", "subconcept2"],
    "concept_relationships": [
        {{
            "from": "concept1",
            "to": "concept2", 
            "relationship": "prerequisite",
            "strength": 0.8
        }}
    ],
    "educational_context": {{
        "applications": ["real world application1", "practical use1"],
        "examples": ["concrete example1", "demonstration1"],
        "misconceptions": ["common error1"],
        "definitions": ["key term definition1"],
        "phenomena": ["observable phenomenon1"]
    }},
    "content_types": ["basic_concepts", "real_world_applications", "practical_uses", "conceptual_explanation", "definitions", "physical_phenomena", "experimental_procedure"]
}}
}
""",
            
            'quality_assessment': """
You are an educational quality expert. Assess the pedagogical quality of this educational content chunk.

Content:
{content}
Metadata: {metadata}

Evaluate:
1. Educational soundness (clear learning objectives, proper sequencing)
2. Content completeness (all necessary information present)
3. Pedagogical coherence (logical flow, connections)
4. Student engagement (active learning, examples, activities)

Respond with JSON:
{
    "overall_quality": <0.0-1.0>,
    "dimensions": {
        "educational_soundness": <0.0-1.0>,
        "content_completeness": <0.0-1.0>,
        "pedagogical_coherence": <0.0-1.0>,
        "student_engagement": <0.0-1.0>
    },
    "strengths": ["list of strong points"],
    "weaknesses": ["list of areas for improvement"],
    "recommendations": ["specific improvement suggestions"]
}
""",
            
            'prerequisite_analysis': """
You are an expert in educational prerequisite analysis. Analyze the concept dependencies in this content.

Content: {content}
Grade Level: {grade_level}
Subject: {subject}

Identify:
1. Prerequisites needed to understand this content
2. Concepts this content enables (post-requisites)
3. Cross-grade concept connections
4. Learning progression pathways

Respond with JSON:
{
    "prerequisites": [
        {
            "concept": "prerequisite concept",
            "grade_level": "typical grade where learned",
            "importance": "critical|important|helpful",
            "reasoning": "why this is needed"
        }
    ],
    "enables": [
        {
            "concept": "concept this enables",
            "grade_level": "where typically used",
            "connection_type": "direct|indirect|application"
        }
    ],
    "learning_progression": {
        "previous_grade_connections": ["concepts from earlier grades"],
        "next_grade_connections": ["concepts for future grades"],
        "within_grade_sequence": ["order within current grade"]
    }
}
"""
        }
    
    async def analyze_with_ai(self, 
                            prompt_template: str, 
                            variables: Dict[str, Any],
                            model: str = None,
                            use_reasoning: bool = None) -> AIResponse:
        """
        Analyze content using AI with specified template and variables
        """
        start_time = datetime.now()
        self.usage_stats['total_requests'] += 1
        
        try:
            # Format prompt
            prompt = self.templates[prompt_template].format(**variables)
            model = model or self.config.default_model
            use_reasoning = use_reasoning if use_reasoning is not None else self.config.enable_reasoning
            
            # Choose appropriate client
            if model.startswith('gpt') and self.openai_client:
                response = await self._call_openai(prompt, model, use_reasoning)
            elif model.startswith('claude') and self.anthropic_client:
                response = await self._call_anthropic(prompt, model, use_reasoning)
            else:
                # Fallback to available client
                if self.openai_client:
                    response = await self._call_openai(prompt, 'gpt-4', use_reasoning)
                elif self.anthropic_client:
                    response = await self._call_anthropic(prompt, 'claude-3-sonnet-20240229', use_reasoning)
                else:
                    raise ValueError("No AI client available. Please configure API keys.")
            
            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.usage_stats['successful_requests'] += 1
            self.usage_stats['total_tokens'] += response.tokens_used
            
            # Update average response time
            total_requests = self.usage_stats['successful_requests']
            current_avg = self.usage_stats['average_response_time']
            self.usage_stats['average_response_time'] = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
            
            logger.info(f"AI analysis completed in {processing_time:.2f}s using {response.model_used}")
            return response
            
        except Exception as e:
            self.usage_stats['failed_requests'] += 1
            logger.error(f"AI analysis failed: {e}")
            raise
    
    async def _call_openai(self, prompt: str, model: str, use_reasoning: bool = False) -> AIResponse:
        """Call OpenAI API"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return AIResponse(
                content=content,
                confidence=1.0,
                tokens_used=tokens_used,
                model_used=model,
                metadata={'provider': 'openai'}
            )
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    async def _call_anthropic(self, prompt: str, model: str, use_reasoning: bool = False) -> AIResponse:
        """Call Anthropic Claude API"""
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens if response.usage else 0
            
            return AIResponse(
                content=content,
                confidence=1.0,
                tokens_used=tokens_used,
                model_used=model,
                metadata={'provider': 'anthropic'}
            )
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    # Convenience methods for specific analysis types
    
    async def detect_boundaries(self, content: str) -> AIResponse:
        """Detect natural learning unit boundaries using AI"""
        return await self.analyze_with_ai(
            'boundary_detection', 
            {'content': content}
        )
    
    async def extract_concepts(self, content: str, subject: str = "Physics", grade_level: int = 9) -> AIResponse:
        """Extract concepts and relationships using AI"""
        return await self.analyze_with_ai(
            'concept_extraction',
            {
                'content': content,
                'subject': subject,
                'grade_level': grade_level
            }
        )
    
    async def assess_quality(self, content: str, metadata: Dict[str, Any] = None) -> AIResponse:
        """Assess content quality using AI"""
        return await self.analyze_with_ai(
            'quality_assessment',
            {
                'content': content,
                'metadata': json.dumps(metadata or {}, indent=2)
            }
        )
    
    async def analyze_prerequisites(self, content: str, subject: str = "Physics", grade_level: int = 9) -> AIResponse:
        """Analyze prerequisite relationships using AI"""
        return await self.analyze_with_ai(
            'prerequisite_analysis',
            {
                'content': content,
                'subject': subject,
                'grade_level': grade_level
            }
        )
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get AI service usage statistics"""
        return self.usage_stats.copy()
    
    def is_available(self) -> bool:
        """Check if AI services are available"""
        return self.openai_client is not None or self.anthropic_client is not None


# Singleton instance for global access
_ai_service = None

def get_ai_service(config: AIConfig = None) -> AIIntegrationService:
    """Get global AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIIntegrationService(config)
    return _ai_service


# Async helper functions for easy use

async def ai_detect_boundaries(content: str) -> Dict[str, Any]:
    """Helper function to detect boundaries with AI"""
    service = get_ai_service()
    if not service.is_available():
        logger.warning("AI service not available, falling back to rule-based detection")
        return {"boundaries": [], "learning_units": []}
    
    try:
        response = await service.detect_boundaries(content)
        
        # Clean and validate JSON response
        response_content = response.content.strip()
        
        # Handle cases where AI returns partial or malformed JSON
        if not response_content:
            logger.warning("Empty AI response, using fallback")
            return {"boundaries": [], "learning_units": []}
        
        # Try to extract JSON from response if it's wrapped in text
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            response_content = json_match.group()
        
        # Parse JSON with error handling
        try:
            parsed_response = json.loads(response_content)
            
            # Validate required fields
            if not isinstance(parsed_response, dict):
                raise ValueError("Response is not a dictionary")
            
            # Ensure required fields exist
            if "boundaries" not in parsed_response:
                parsed_response["boundaries"] = []
            if "learning_units" not in parsed_response:
                parsed_response["learning_units"] = []
            
            return parsed_response
            
        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error: {je}. Response content: {response_content[:200]}...")
            # Try to create a basic response from the content
            return {"boundaries": [], "learning_units": [], "error": "JSON parsing failed", "raw_content": response_content[:500]}
            
    except Exception as e:
        logger.error(f"AI boundary detection failed: {e}")
        return {"boundaries": [], "learning_units": []}

async def ai_extract_concepts(content: str, subject: str = "Physics", grade_level: int = 9) -> Dict[str, Any]:
    """Helper function to extract concepts with AI"""
    service = get_ai_service()
    if not service.is_available():
        logger.warning("AI service not available, falling back to pattern-based extraction")
        return {"main_concepts": [], "sub_concepts": [], "concept_relationships": [], "educational_context": {}}
    
    try:
        response = await service.extract_concepts(content, subject, grade_level)
        
        # Clean and validate JSON response
        response_content = response.content.strip()
        
        if not response_content:
            logger.warning("Empty AI response for concept extraction")
            return {"main_concepts": [], "sub_concepts": [], "concept_relationships": [], "educational_context": {}}
        
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            response_content = json_match.group()
        
        try:
            parsed_response = json.loads(response_content)
            
            # Validate and ensure required fields
            if not isinstance(parsed_response, dict):
                raise ValueError("Response is not a dictionary")
            
            default_fields = ["main_concepts", "sub_concepts", "concept_relationships", "educational_context"]
            for field in default_fields:
                if field not in parsed_response:
                    parsed_response[field] = [] if field != "educational_context" else {}
            
            return parsed_response
            
        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error in concept extraction: {je}")
            return {"main_concepts": [], "sub_concepts": [], "concept_relationships": [], "educational_context": {}, "error": "JSON parsing failed"}
            
    except Exception as e:
        logger.error(f"AI concept extraction failed: {e}")
        return {"main_concepts": [], "sub_concepts": [], "concept_relationships": [], "educational_context": {}}

async def ai_assess_quality(content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper function to assess quality with AI"""
    service = get_ai_service()
    if not service.is_available():
        logger.warning("AI service not available, falling back to rule-based assessment")
        return {"overall_quality": 0.7, "dimensions": {}, "strengths": [], "weaknesses": [], "recommendations": []}
    
    try:
        response = await service.assess_quality(content, metadata)
        return json.loads(response.content)
    except Exception as e:
        logger.error(f"AI quality assessment failed: {e}")
        return {"overall_quality": 0.7, "dimensions": {}, "strengths": [], "weaknesses": [], "recommendations": []}

async def ai_analyze_prerequisites(content: str, subject: str = "Physics", grade_level: int = 9) -> Dict[str, Any]:
    """Helper function to analyze prerequisites with AI"""
    service = get_ai_service()
    if not service.is_available():
        logger.warning("AI service not available, falling back to rule-based analysis")
        return {"prerequisites": [], "enables": [], "learning_progression": {}}
    
    try:
        response = await service.analyze_prerequisites(content, subject, grade_level)
        return json.loads(response.content)
    except Exception as e:
        logger.error(f"AI prerequisite analysis failed: {e}")
        return {"prerequisites": [], "enables": [], "learning_progression": {}}