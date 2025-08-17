#!/usr/bin/env python3
"""
Concept-Based Question Answering Test
Evaluates the system's ability to answer questions using metadata and content analysis
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker

def create_concept_questions():
    """Create concept-based questions for testing"""
    return [
        {
            'id': 'Q1',
            'question': 'What is sound and how is it produced?',
            'concepts': ['sound', 'production', 'vibration'],
            'expected_section': '11.1',
            'difficulty': 'basic',
            'type': 'definition'
        },
        {
            'id': 'Q2', 
            'question': 'How does sound travel through different media?',
            'concepts': ['sound', 'propagation', 'medium', 'travel'],
            'expected_section': '11.2',
            'difficulty': 'intermediate',
            'type': 'explanation'
        },
        {
            'id': 'Q3',
            'question': 'What happens when sound reflects off surfaces?',
            'concepts': ['sound', 'reflection', 'echo', 'surfaces'],
            'expected_section': '11.3',
            'difficulty': 'intermediate',
            'type': 'phenomenon'
        },
        {
            'id': 'Q4',
            'question': 'What is the speed of sound in different materials?',
            'concepts': ['speed', 'sound', 'materials', 'velocity'],
            'expected_section': '11.2',
            'difficulty': 'advanced',
            'type': 'calculation'
        },
        {
            'id': 'Q5',
            'question': 'How do we measure the frequency of sound?',
            'concepts': ['frequency', 'measurement', 'sound', 'pitch'],
            'expected_section': '11.1',
            'difficulty': 'intermediate',
            'type': 'experiment'
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

def calculate_concept_relevance(chunk, question):
    """Calculate relevance score based on concepts and metadata"""
    score = 0
    content_lower = chunk.content.lower()
    
    # Check content for concept keywords
    for concept in question['concepts']:
        if concept.lower() in content_lower:
            score += 2
    
    # Check metadata concepts
    chunk_concepts = chunk.metadata.get('concepts_and_skills', {}).get('main_concepts', [])
    for chunk_concept in chunk_concepts:
        for question_concept in question['concepts']:
            if question_concept.lower() in chunk_concept.lower():
                score += 3  # Higher weight for metadata matches
    
    # Check learning objectives
    objectives = chunk.metadata.get('pedagogical_elements', {}).get('learning_objectives', [])
    for objective in objectives:
        for concept in question['concepts']:
            if concept.lower() in objective.lower():
                score += 2
    
    # Check keywords
    keywords = chunk.metadata.get('concepts_and_skills', {}).get('keywords', [])
    for keyword in keywords:
        for concept in question['concepts']:
            if concept.lower() in keyword.lower():
                score += 1
    
    # Check section match
    section_number = chunk.metadata.get('basic_info', {}).get('section', '')
    if section_number == question['expected_section']:
        score += 5  # High weight for section match
    
    # Check content type relevance
    content_types = chunk.metadata.get('pedagogical_elements', {}).get('content_types', [])
    if question['type'] == 'definition' and 'conceptual_explanation' in content_types:
        score += 2
    elif question['type'] == 'experiment' and 'hands_on_activity' in content_types:
        score += 2
    elif question['type'] == 'calculation' and 'mathematical_formulas' in content_types:
        score += 2
    
    return score

def test_concept_question_answering():
    """Test concept-based question answering"""
    print("🧠 CONCEPT-BASED QUESTION ANSWERING TEST")
    print("=" * 60)
    
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
    questions = create_concept_questions()
    
    # Test each question
    print(f"\n❓ Testing Concept-Based Questions...")
    print("=" * 60)
    
    results = []
    
    for question in questions:
        print(f"\n🔍 {question['id']}: {question['question']}")
        print(f"   Concepts: {', '.join(question['concepts'])}")
        print(f"   Expected Section: {question['expected_section']}")
        print(f"   Type: {question['type']}, Difficulty: {question['difficulty']}")
        
        # Find relevant chunks
        relevant_chunks = []
        
        for chunk in all_chunks:
            relevance_score = calculate_concept_relevance(chunk, question)
            
            if relevance_score > 0:
                relevant_chunks.append({
                    'chunk': chunk,
                    'score': relevance_score,
                    'section': chunk.metadata.get('basic_info', {}).get('section', ''),
                    'content_preview': chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
                })
        
        # Sort by relevance score
        relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top 3 results
        top_results = relevant_chunks[:3]
        
        result = {
            'question': question,
            'total_relevant': len(relevant_chunks),
            'top_results': top_results
        }
        
        results.append(result)
        
        # Print results
        if top_results:
            print(f"   📊 Found {len(relevant_chunks)} relevant chunks")
            print(f"   🏆 Top 3 Results:")
            
            for i, chunk_info in enumerate(top_results):
                chunk = chunk_info['chunk']
                print(f"      {i+1}. Score: {chunk_info['score']}, Section: {chunk_info['section']}")
                print(f"         Quality: {chunk.quality_score:.2f}, Length: {len(chunk.content)} chars")
                print(f"         Preview: {chunk_info['content_preview']}")
                print()
        else:
            print(f"   ❌ No relevant chunks found")
    
    # Analyze results
    print(f"\n📈 RESULTS ANALYSIS")
    print("=" * 60)
    
    total_questions = len(questions)
    questions_with_results = sum(1 for r in results if r['top_results'])
    avg_relevant_chunks = sum(r['total_relevant'] for r in results) / total_questions
    
    print(f"📊 Overall Performance:")
    print(f"   • Questions with results: {questions_with_results}/{total_questions} ({questions_with_results/total_questions*100:.1f}%)")
    print(f"   • Average relevant chunks per question: {avg_relevant_chunks:.1f}")
    
    # Section accuracy analysis
    section_accuracy = 0
    for result in results:
        question = result['question']
        top_result = result['top_results'][0] if result['top_results'] else None
        
        if top_result and top_result['section'] == question['expected_section']:
            section_accuracy += 1
    
    print(f"   • Section accuracy: {section_accuracy}/{total_questions} ({section_accuracy/total_questions*100:.1f}%)")
    
    # Quality analysis
    if results:
        avg_top_score = sum(r['top_results'][0]['score'] for r in results if r['top_results']) / questions_with_results
        print(f"   • Average top relevance score: {avg_top_score:.1f}")
    
    # Detailed question analysis
    print(f"\n📋 Question-by-Question Analysis:")
    for result in results:
        question = result['question']
        top_result = result['top_results'][0] if result['top_results'] else None
        
        status = "✅" if top_result and top_result['section'] == question['expected_section'] else "❌"
        print(f"   {status} {question['id']}: {question['question'][:50]}...")
        if top_result:
            print(f"      Best match: Section {top_result['section']} (score: {top_result['score']})")
        else:
            print(f"      No relevant chunks found")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 60)
    
    if questions_with_results / total_questions < 0.8:
        print("❌ Question answering performance needs improvement:")
        print("   • Enhance concept extraction from content")
        print("   • Improve metadata concept mapping")
        print("   • Add more sophisticated semantic matching")
    else:
        print("✅ Question answering performance is good!")
    
    if section_accuracy / total_questions < 0.8:
        print("❌ Section matching accuracy needs improvement:")
        print("   • Enhance section detection patterns")
        print("   • Improve content-to-section mapping")
        print("   • Add section boundary validation")
    else:
        print("✅ Section matching accuracy is good!")
    
    print(f"\n🎯 System is {'READY' if questions_with_results/total_questions >= 0.8 else 'NEEDS IMPROVEMENT'} for concept-based question answering!")

if __name__ == "__main__":
    test_concept_question_answering() 