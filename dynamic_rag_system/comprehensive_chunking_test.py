#!/usr/bin/env python3
"""
Comprehensive Chunking Quality Test
Tests 10 questions to evaluate if all relevant chunks are retrieved for complete learning
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker

def create_10_comprehensive_questions():
    """Create 10 comprehensive questions covering all aspects of sound"""
    return [
        {
            'id': 'Q1',
            'question': 'What is sound and how is it produced?',
            'concepts': ['sound', 'production', 'vibration', 'tuning fork'],
            'expected_sections': ['11.1'],
            'difficulty': 'basic',
            'type': 'definition',
            'learning_objectives': ['understand sound production', 'identify vibrating objects']
        },
        {
            'id': 'Q2',
            'question': 'How does sound travel through different media?',
            'concepts': ['sound', 'propagation', 'medium', 'travel', 'waves'],
            'expected_sections': ['11.2'],
            'difficulty': 'intermediate',
            'type': 'explanation',
            'learning_objectives': ['understand sound propagation', 'identify different media']
        },
        {
            'id': 'Q3',
            'question': 'What happens when sound reflects off surfaces?',
            'concepts': ['sound', 'reflection', 'echo', 'surfaces', 'bounce'],
            'expected_sections': ['11.3'],
            'difficulty': 'intermediate',
            'type': 'phenomenon',
            'learning_objectives': ['understand sound reflection', 'explain echo formation']
        },
        {
            'id': 'Q4',
            'question': 'What is the speed of sound in different materials?',
            'concepts': ['speed', 'sound', 'materials', 'velocity', 'medium'],
            'expected_sections': ['11.2'],
            'difficulty': 'advanced',
            'type': 'calculation',
            'learning_objectives': ['compare sound speeds', 'understand material properties']
        },
        {
            'id': 'Q5',
            'question': 'How do we measure the frequency of sound?',
            'concepts': ['frequency', 'measurement', 'sound', 'pitch', 'tuning fork'],
            'expected_sections': ['11.1', '11.4'],
            'difficulty': 'intermediate',
            'type': 'experiment',
            'learning_objectives': ['measure sound frequency', 'understand pitch']
        },
        {
            'id': 'Q6',
            'question': 'What is the audible range of sound for humans?',
            'concepts': ['audible', 'range', 'human', 'hearing', 'frequency'],
            'expected_sections': ['11.4'],
            'difficulty': 'basic',
            'type': 'fact',
            'learning_objectives': ['know human hearing range', 'understand frequency limits']
        },
        {
            'id': 'Q7',
            'question': 'What are the applications of ultrasound?',
            'concepts': ['ultrasound', 'applications', 'high frequency', 'medical', 'industrial'],
            'expected_sections': ['11.5'],
            'difficulty': 'advanced',
            'type': 'application',
            'learning_objectives': ['understand ultrasound uses', 'identify practical applications']
        },
        {
            'id': 'Q8',
            'question': 'How does sound help in navigation and communication?',
            'concepts': ['sound', 'navigation', 'communication', 'echo', 'ultrasound'],
            'expected_sections': ['11.3', '11.5'],
            'difficulty': 'intermediate',
            'type': 'application',
            'learning_objectives': ['understand sound applications', 'explain navigation uses']
        },
        {
            'id': 'Q9',
            'question': 'What are the characteristics of sound waves?',
            'concepts': ['characteristics', 'sound', 'wave', 'frequency', 'amplitude', 'wavelength'],
            'expected_sections': ['11.1', '11.2', '11.4'],
            'difficulty': 'intermediate',
            'type': 'concept',
            'learning_objectives': ['identify wave characteristics', 'understand wave properties']
        },
        {
            'id': 'Q10',
            'question': 'How do animals use sound differently from humans?',
            'concepts': ['animals', 'sound', 'hearing', 'frequency', 'ultrasound', 'infrasound'],
            'expected_sections': ['11.4', '11.5'],
            'difficulty': 'advanced',
            'type': 'comparison',
            'learning_objectives': ['compare animal and human hearing', 'understand frequency ranges']
        }
    ]

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def create_sections_from_text(text):
    """Create sections from text"""
    section_pattern = r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]{3,60})(?:\n|$)'
    sections = []
    
    for match in re.finditer(section_pattern, text, re.MULTILINE):
        sections.append({
            'number': match.group(1),
            'title': match.group(2).strip(),
            'position': match.start()
        })
    
    # Create mother sections
    mother_sections = []
    for i, section in enumerate(sections):
        start_pos = section['position']
        if i < len(sections) - 1:
            end_pos = sections[i + 1]['position']
        else:
            end_pos = len(text)
        
        mother_sections.append({
            'section_number': section['number'],
            'title': section['title'],
            'start_pos': start_pos,
            'end_pos': end_pos,
            'grade_level': 9,
            'subject': 'Physics',
            'chapter': int(section['number'].split('.')[0])
        })
    
    return mother_sections

def calculate_comprehensive_relevance(chunk, question):
    """Calculate comprehensive relevance score"""
    score = 0
    content_lower = chunk.content.lower()
    
    # Content keyword matching (weight: 2)
    for concept in question['concepts']:
        if concept.lower() in content_lower:
            score += 2
    
    # Metadata concept matching (weight: 3)
    chunk_concepts = chunk.metadata.get('concepts_and_skills', {}).get('main_concepts', [])
    for chunk_concept in chunk_concepts:
        for question_concept in question['concepts']:
            if question_concept.lower() in chunk_concept.lower():
                score += 3
    
    # Learning objectives matching (weight: 2)
    objectives = chunk.metadata.get('pedagogical_elements', {}).get('learning_objectives', [])
    for objective in objectives:
        for concept in question['concepts']:
            if concept.lower() in objective.lower():
                score += 2
    
    # Keywords matching (weight: 1)
    keywords = chunk.metadata.get('concepts_and_skills', {}).get('keywords', [])
    for keyword in keywords:
        for concept in question['concepts']:
            if concept.lower() in keyword.lower():
                score += 1
    
    # Section matching (weight: 5)
    section_number = chunk.metadata.get('basic_info', {}).get('section', '')
    if section_number in question['expected_sections']:
        score += 5
    
    # Content type relevance (weight: 2)
    content_types = chunk.metadata.get('pedagogical_elements', {}).get('content_types', [])
    if question['type'] == 'definition' and 'conceptual_explanation' in content_types:
        score += 2
    elif question['type'] == 'experiment' and 'hands_on_activity' in content_types:
        score += 2
    elif question['type'] == 'calculation' and 'mathematical_formulas' in content_types:
        score += 2
    elif question['type'] == 'application' and 'real_world_applications' in content_types:
        score += 2
    
    # Quality score bonus (weight: 1)
    score += chunk.quality_score
    
    return score

def evaluate_learning_completeness(chunks, question, relevant_chunks):
    """Evaluate if all necessary chunks for complete learning are retrieved"""
    completeness_score = 0
    missing_aspects = []
    
    # Check if we have chunks from all expected sections
    expected_sections = question['expected_sections']
    found_sections = set()
    
    for chunk_info in relevant_chunks:
        section = chunk_info['chunk'].metadata.get('basic_info', {}).get('section', '')
        found_sections.add(section)
    
    # Section coverage
    section_coverage = len(found_sections.intersection(set(expected_sections))) / len(expected_sections)
    completeness_score += section_coverage * 30  # 30% weight for section coverage
    
    if section_coverage < 1.0:
        missing_sections = set(expected_sections) - found_sections
        missing_aspects.append(f"Missing sections: {', '.join(missing_sections)}")
    
    # Content type coverage
    content_types_found = set()
    for chunk_info in relevant_chunks:
        content_types = chunk_info['chunk'].metadata.get('pedagogical_elements', {}).get('content_types', [])
        content_types_found.update(content_types)
    
    # Check for essential content types
    essential_types = {
        'definition': ['conceptual_explanation', 'basic_concepts'],
        'experiment': ['hands_on_activity', 'experimental_procedure'],
        'calculation': ['mathematical_formulas', 'numerical_examples'],
        'application': ['real_world_applications', 'practical_uses'],
        'phenomenon': ['physical_phenomena', 'observations']
    }
    
    required_types = essential_types.get(question['type'], [])
    type_coverage = 0
    if required_types:
        found_required = sum(1 for req_type in required_types if req_type in content_types_found)
        type_coverage = found_required / len(required_types)
        completeness_score += type_coverage * 25  # 25% weight for content type coverage
    
    if type_coverage < 1.0:
        missing_types = [t for t in required_types if t not in content_types_found]
        missing_aspects.append(f"Missing content types: {', '.join(missing_types)}")
    
    # Concept coverage
    concepts_found = set()
    for chunk_info in relevant_chunks:
        chunk_concepts = chunk_info['chunk'].metadata.get('concepts_and_skills', {}).get('main_concepts', [])
        concepts_found.update([c.lower() for c in chunk_concepts])
    
    question_concepts = set([c.lower() for c in question['concepts']])
    concept_coverage = len(concepts_found.intersection(question_concepts)) / len(question_concepts)
    completeness_score += concept_coverage * 25  # 25% weight for concept coverage
    
    if concept_coverage < 1.0:
        missing_concepts = question_concepts - concepts_found
        missing_aspects.append(f"Missing concepts: {', '.join(missing_concepts)}")
    
    # Quality coverage
    avg_quality = sum(chunk_info['chunk'].quality_score for chunk_info in relevant_chunks) / len(relevant_chunks)
    completeness_score += avg_quality * 20  # 20% weight for quality
    
    return {
        'completeness_score': completeness_score,
        'section_coverage': section_coverage,
        'type_coverage': type_coverage,
        'concept_coverage': concept_coverage,
        'avg_quality': avg_quality,
        'missing_aspects': missing_aspects
    }

def run_comprehensive_test():
    """Run comprehensive chunking quality test"""
    print("🧠 COMPREHENSIVE CHUNKING QUALITY TEST")
    print("=" * 70)
    
    pdf_path = "/Users/umangagarwal/Downloads/iesc1dd/iesc111.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Extract text
    print("📖 Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("❌ Failed to extract text")
        return
    
    print(f"✅ Extracted {len(text)} characters")
    
    # Create sections
    print("\n🏗️ Creating sections...")
    mother_sections = create_sections_from_text(text)
    print(f"✅ Created {len(mother_sections)} sections")
    
    # Process with chunker
    print("\n🧠 Processing with Holistic Chunker...")
    chunker = HolisticRAGChunker()
    all_chunks = []
    
    for section in mother_sections:
        print(f"   📚 Section {section['section_number']}: {section['title']}")
        try:
            chunks = chunker.process_mother_section(
                mother_section=section,
                full_text=text,
                char_to_page_map={i: 1 for i in range(len(text))}
            )
            all_chunks.extend(chunks)
            print(f"      ✅ Created {len(chunks)} chunks")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print(f"\n📊 Total chunks created: {len(all_chunks)}")
    
    # Create test questions
    questions = create_10_comprehensive_questions()
    
    # Test each question
    print(f"\n❓ Testing 10 Comprehensive Questions...")
    print("=" * 70)
    
    results = []
    total_completeness = 0
    
    for question in questions:
        print(f"\n🔍 {question['id']}: {question['question']}")
        print(f"   Concepts: {', '.join(question['concepts'])}")
        print(f"   Expected Sections: {', '.join(question['expected_sections'])}")
        print(f"   Type: {question['type']}, Difficulty: {question['difficulty']}")
        
        # Find relevant chunks
        relevant_chunks = []
        
        for chunk in all_chunks:
            relevance_score = calculate_comprehensive_relevance(chunk, question)
            
            if relevance_score > 0:
                relevant_chunks.append({
                    'chunk': chunk,
                    'score': relevance_score,
                    'section': chunk.metadata.get('basic_info', {}).get('section', ''),
                    'content_preview': chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
                })
        
        # Sort by relevance score
        relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top 5 results for comprehensive analysis
        top_results = relevant_chunks[:5]
        
        # Evaluate learning completeness
        completeness = evaluate_learning_completeness(all_chunks, question, top_results)
        total_completeness += completeness['completeness_score']
        
        result = {
            'question': question,
            'total_relevant': len(relevant_chunks),
            'top_results': top_results,
            'completeness': completeness
        }
        
        results.append(result)
        
        # Print results
        if top_results:
            print(f"   📊 Found {len(relevant_chunks)} relevant chunks")
            print(f"   🎯 Completeness Score: {completeness['completeness_score']:.1f}/100")
            print(f"   📈 Coverage: Sections({completeness['section_coverage']:.1f}), Types({completeness['type_coverage']:.1f}), Concepts({completeness['concept_coverage']:.1f})")
            
            if completeness['missing_aspects']:
                print(f"   ⚠️ Missing: {', '.join(completeness['missing_aspects'])}")
            
            print(f"   🏆 Top 3 Results:")
            
            for i, chunk_info in enumerate(top_results[:3]):
                chunk = chunk_info['chunk']
                print(f"      {i+1}. Score: {chunk_info['score']:.1f}, Section: {chunk_info['section']}")
                print(f"         Quality: {chunk.quality_score:.2f}, Length: {len(chunk.content)} chars")
                print(f"         Preview: {chunk_info['content_preview']}")
                print()
        else:
            print(f"   ❌ No relevant chunks found")
    
    # Overall analysis
    print(f"\n📈 COMPREHENSIVE RESULTS ANALYSIS")
    print("=" * 70)
    
    avg_completeness = total_completeness / len(questions)
    
    print(f"📊 Overall Performance:")
    print(f"   • Average Completeness Score: {avg_completeness:.1f}/100")
    print(f"   • Questions with Results: {sum(1 for r in results if r['top_results'])}/{len(questions)}")
    print(f"   • Average Relevant Chunks: {sum(r['total_relevant'] for r in results) / len(questions):.1f}")
    
    # Completeness distribution
    excellent = sum(1 for r in results if r['completeness']['completeness_score'] >= 80)
    good = sum(1 for r in results if 60 <= r['completeness']['completeness_score'] < 80)
    fair = sum(1 for r in results if 40 <= r['completeness']['completeness_score'] < 60)
    poor = sum(1 for r in results if r['completeness']['completeness_score'] < 40)
    
    print(f"   • Completeness Distribution: Excellent({excellent}), Good({good}), Fair({fair}), Poor({poor})")
    
    # Detailed question analysis
    print(f"\n📋 Question-by-Question Completeness:")
    for result in results:
        question = result['question']
        completeness = result['completeness']
        
        status = "🟢" if completeness['completeness_score'] >= 80 else "🟡" if completeness['completeness_score'] >= 60 else "🔴"
        print(f"   {status} {question['id']}: {completeness['completeness_score']:.1f}/100 - {question['question'][:50]}...")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR COMPLETE LEARNING")
    print("=" * 70)
    
    if avg_completeness >= 80:
        print("✅ EXCELLENT: System provides comprehensive learning coverage!")
        print("   • All major concepts are well-covered")
        print("   • Multiple content types available")
        print("   • High-quality chunks for learning")
    elif avg_completeness >= 60:
        print("🟡 GOOD: System provides good learning coverage with room for improvement")
        print("   • Most concepts are covered")
        print("   • Some content types may be missing")
        print("   • Consider enhancing specific areas")
    else:
        print("🔴 NEEDS IMPROVEMENT: System needs enhancement for complete learning")
        print("   • Many concepts are missing")
        print("   • Content type coverage is insufficient")
        print("   • Requires significant improvements")
    
    # Specific recommendations
    print(f"\n🔧 Specific Improvements Needed:")
    
    # Analyze common missing aspects
    all_missing = []
    for result in results:
        all_missing.extend(result['completeness']['missing_aspects'])
    
    if all_missing:
        missing_counts = {}
        for missing in all_missing:
            missing_counts[missing] = missing_counts.get(missing, 0) + 1
        
        print("   Most common missing aspects:")
        for missing, count in sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"   • {missing} (affects {count} questions)")
    
    print(f"\n🎯 FINAL VERDICT:")
    if avg_completeness >= 80:
        print("🚀 EXCELLENT CHUNKING - Ready for complete learning!")
    elif avg_completeness >= 60:
        print("✅ GOOD CHUNKING - Mostly ready with minor improvements needed")
    else:
        print("⚠️ CHUNKING NEEDS IMPROVEMENT - Requires enhancement for complete learning")

if __name__ == "__main__":
    run_comprehensive_test() 