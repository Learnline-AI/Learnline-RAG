#!/usr/bin/env python3
"""
Conceptual Learning Test - 10 Questions from Actual Book Content
Tests how well semantic chunks provide concrete, learnable answers
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
from semantic_chunker import SemanticEducationalChunker, ChunkType

def create_conceptual_questions():
    """Create 10 conceptual questions from actual book content"""
    return [
        {
            'id': 'Q1',
            'question': 'How is sound produced and what happens when an object vibrates?',
            'concepts': ['sound production', 'vibration', 'vibrating objects'],
            'learning_objectives': ['Understand sound production', 'Explain vibration-sound relationship'],
            'expected_answers': ['Vibrating objects produce sound', 'Air around object vibrates', 'Creates sound waves']
        },
        {
            'id': 'Q2', 
            'question': 'What is a medium and how does sound travel through different media?',
            'concepts': ['medium', 'sound propagation', 'solid', 'liquid', 'gas'],
            'learning_objectives': ['Define medium', 'Explain sound travel through different states'],
            'expected_answers': ['Medium is substance for transmission', 'Can be solid/liquid/gas', 'Particles vibrate but don\'t travel']
        },
        {
            'id': 'Q3',
            'question': 'What are compressions and rarefactions in sound waves?',
            'concepts': ['compression', 'rarefaction', 'pressure', 'density'],
            'learning_objectives': ['Define compression and rarefaction', 'Understand pressure variations'],
            'expected_answers': ['Compression is high pressure region', 'Rarefaction is low pressure region', 'Sound propagates as series of these']
        },
        {
            'id': 'Q4',
            'question': 'Why are sound waves called longitudinal waves?',
            'concepts': ['longitudinal waves', 'particle motion', 'wave direction'],
            'learning_objectives': ['Define longitudinal waves', 'Explain particle motion'],
            'expected_answers': ['Particles move parallel to wave direction', 'Particles oscillate back and forth', 'Not transverse motion']
        },
        {
            'id': 'Q5',
            'question': 'How does sound reflect off surfaces and what are the laws of reflection?',
            'concepts': ['sound reflection', 'echo', 'laws of reflection'],
            'learning_objectives': ['Explain sound reflection', 'State reflection laws'],
            'expected_answers': ['Sound bounces off surfaces', 'Incident and reflected angles equal', 'All three in same plane']
        },
        {
            'id': 'Q6',
            'question': 'What determines the speed of sound in different media?',
            'concepts': ['speed of sound', 'temperature', 'medium properties'],
            'learning_objectives': ['Identify speed factors', 'Understand temperature dependence'],
            'expected_answers': ['Depends on medium properties', 'Speed increases with temperature', 'Faster in solids than gases']
        },
        {
            'id': 'Q7',
            'question': 'What is the audible range of human hearing?',
            'concepts': ['audible range', 'frequency', 'infrasonic', 'ultrasonic'],
            'learning_objectives': ['Define audible range', 'Understand frequency ranges'],
            'expected_answers': ['20 Hz to 20,000 Hz', 'Below 20 Hz is infrasonic', 'Above 20 kHz is ultrasonic']
        },
        {
            'id': 'Q8',
            'question': 'How do frequency and amplitude affect sound characteristics?',
            'concepts': ['frequency', 'amplitude', 'pitch', 'loudness'],
            'learning_objectives': ['Relate frequency to pitch', 'Relate amplitude to loudness'],
            'expected_answers': ['Frequency determines pitch', 'Amplitude determines loudness', 'Higher frequency = higher pitch']
        },
        {
            'id': 'Q9',
            'question': 'What are the practical applications of ultrasound?',
            'concepts': ['ultrasound', 'medical applications', 'industrial uses'],
            'learning_objectives': ['Identify ultrasound applications', 'Understand medical uses'],
            'expected_answers': ['Medical imaging', 'Fetal examination', 'Breaking kidney stones', 'Industrial testing']
        },
        {
            'id': 'Q10',
            'question': 'How can you calculate the speed of sound using frequency and wavelength?',
            'concepts': ['speed calculation', 'frequency', 'wavelength', 'formula'],
            'learning_objectives': ['Use formula v = λν', 'Calculate speed from frequency and wavelength'],
            'expected_answers': ['Speed = wavelength × frequency', 'v = λν', 'Wavelength is distance between compressions']
        }
    ]

def calculate_conceptual_relevance(chunk, question):
    """Calculate relevance for conceptual learning"""
    score = 0.0
    
    # Check chunk type
    if hasattr(chunk, 'chunk_type') and chunk.chunk_type in [ChunkType.CONTENT, ChunkType.EXAMPLE, ChunkType.ACTIVITY]:
        score += 1.0
    
    # Check concept matches
    question_concepts = question.get('concepts', [])
    content_lower = chunk.content.lower()
    
    for concept in question_concepts:
        if concept.lower() in content_lower:
            score += 1.0
    
    # Check learning objectives
    objectives = question.get('learning_objectives', [])
    for objective in objectives:
        if any(word in content_lower for word in objective.lower().split()):
            score += 0.5
    
    # Check expected answers
    expected_answers = question.get('expected_answers', [])
    for answer in expected_answers:
        if any(word in content_lower for word in answer.lower().split()):
            score += 0.8
    
    return score

def test_conceptual_learning():
    """Test conceptual learning effectiveness"""
    print("🧠 CONCEPTUAL LEARNING EFFECTIVENESS TEST")
    print("=" * 60)
    
    # Sample content from the book
    sample_content = """
    11.1 Production of Sound
    
    Sound is produced by vibrating objects. When an object vibrates, it causes the air around it to vibrate, creating sound waves.
    
    Activity 11.1
    Take a tuning fork and strike it gently against a rubber pad. Hold it near your ear. You will hear a sound. Now touch the tuning fork to a glass of water. You will see ripples in the water. This shows that the tuning fork is vibrating.
    
    11.2 Propagation of Sound
    
    Sound is produced by vibrating objects. The matter or substance through which sound is transmitted is called a medium. It can be solid, liquid or gas. Sound moves through a medium from the point of generation to the listener. When an object vibrates, it sets the particles of the medium around it vibrating. The particles do not travel all the way from the vibrating object to the ear.
    
    Compression is the region of high pressure and rarefaction is the region of low pressure. Pressure is related to the number of particles of a medium in a given volume. More density of the particles in the medium gives more pressure and vice versa. Thus, propagation of sound can be visualised as propagation of density variations or pressure variations in the medium.
    
    11.2.1 SOUND WAVES ARE LONGITUDINAL WAVES
    
    The regions where the coils become closer are called compressions (C) and the regions where the coils are further apart are called rarefactions (R). As we already know, sound propagates in the medium as a series of compressions and rarefactions. These waves are called longitudinal waves. In these waves the individual particles of the medium move in a direction parallel to the direction of propagation of the disturbance. The particles do not move from one place to another but they simply oscillate back and forth about their position of rest. This is exactly how a sound wave propagates, hence sound waves are longitudinal waves.
    
    11.3 Reflection of Sound
    
    Sound bounces off a solid or a liquid like a rubber ball bounces off a wall. Like light, sound gets reflected at the surface of a solid or liquid and follows the same laws of reflection. The directions in which the sound is incident and is reflected make equal angles with the normal to the reflecting surface at the point of incidence, and the three are in the same plane. An obstacle of large size which may be polished or rough is needed for the reflection of sound waves.
    
    11.4 Range of Hearing
    
    The audible range of sound for human beings extends from about 20 Hz to 20000 Hz (one Hz = one cycle/s). Children under the age of five and some animals, such as dogs can hear up to 25 kHz (1 kHz = 1000 Hz). As people grow older their ears become less sensitive to higher frequencies. Sounds of frequencies below 20 Hz are called infrasonic sound or infrasound. Frequencies higher than 20 kHz are called ultrasonic sound or ultrasound. Ultrasound is produced by animals such as dolphins, bats and porpoises.
    
    What you have learnt
    
    • Sound is produced due to vibration of different objects.
    • Sound travels as a longitudinal wave through a material medium.
    • Sound travels as successive compressions and rarefactions in the medium.
    • The distance between two consecutive compressions or two consecutive rarefactions is called the wavelength, λ.
    • The number of complete oscillations per unit time is called the frequency (ν), ν = 1/T.
    • The speed v, frequency ν, and wavelength λ, of sound are related by the equation, v = λν.
    • The speed of sound depends primarily on the nature and the temperature of the transmitting medium.
    • The audible range of hearing for average human beings is in the frequency range of 20 Hz – 20 kHz.
    • Sound waves with frequencies below the audible range are termed "infrasonic" and those above the audible range are termed "ultrasonic".
    • Ultrasound has many medical and industrial applications.
    """
    
    print("📖 Processing book content...")
    
    # Create semantic chunker
    semantic_chunker = SemanticEducationalChunker()
    
    try:
        # Create semantic chunks
        chunks, relationships = semantic_chunker.create_semantic_chunks(sample_content)
        print(f"✅ Created {len(chunks)} semantic chunks")
        print(f"✅ Created {len(relationships)} relationships")
        
        # Create questions
        questions = create_conceptual_questions()
        
        # Test each question
        print(f"\n❓ Testing 10 Conceptual Questions...")
        print("=" * 60)
        
        results = []
        total_score = 0
        
        for question in questions:
            print(f"\n🔍 {question['id']}: {question['question']}")
            print(f"   Learning Objectives: {len(question['learning_objectives'])}")
            print(f"   Expected Answers: {len(question['expected_answers'])}")
            
            # Find relevant chunks
            relevant_chunks = []
            
            for chunk in chunks:
                relevance_score = calculate_conceptual_relevance(chunk, question)
                
                if relevance_score > 0:
                    relevant_chunks.append({
                        'chunk': chunk,
                        'score': relevance_score,
                        'chunk_type': chunk.chunk_type.value if hasattr(chunk, 'chunk_type') else 'unknown',
                        'content_preview': chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                    })
            
            # Sort by relevance score
            relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
            
            # Take top 3 results
            top_results = relevant_chunks[:3]
            
            result = {
                'question': question,
                'total_relevant': len(relevant_chunks),
                'top_results': top_results,
                'max_score': max([r['score'] for r in relevant_chunks]) if relevant_chunks else 0
            }
            
            results.append(result)
            total_score += result['max_score']
            
            # Print results
            if top_results:
                print(f"   📊 Found {len(relevant_chunks)} relevant chunks")
                print(f"   🏆 Top 3 Results:")
                
                for i, chunk_info in enumerate(top_results):
                    print(f"      {i+1}. Score: {chunk_info['score']:.2f}, Type: {chunk_info['chunk_type']}")
                    print(f"         Preview: {chunk_info['content_preview']}")
                    print()
            else:
                print(f"   ❌ No relevant chunks found")
        
        # Analyze results
        print(f"\n📈 CONCEPTUAL LEARNING ANALYSIS")
        print("=" * 60)
        
        avg_score = total_score / len(questions)
        questions_with_matches = sum(1 for r in results if r['total_relevant'] > 0)
        
        print(f"📊 Overall Results:")
        print(f"   • Questions with matches: {questions_with_matches}/{len(questions)} ({questions_with_matches/len(questions)*100:.1f}%)")
        print(f"   • Average conceptual score: {avg_score:.2f}")
        print(f"   • Total relationships created: {len(relationships)}")
        
        # Learning effectiveness grade
        if avg_score >= 4.0:
            effectiveness_grade = "A+ (Excellent Learning Support)"
        elif avg_score >= 3.0:
            effectiveness_grade = "A (Very Good Learning Support)"
        elif avg_score >= 2.0:
            effectiveness_grade = "B (Good Learning Support)"
        elif avg_score >= 1.5:
            effectiveness_grade = "C (Fair Learning Support)"
        else:
            effectiveness_grade = "D (Poor Learning Support)"
        
        print(f"   • Learning Effectiveness Grade: {effectiveness_grade}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("=" * 60)
        
        if avg_score >= 3.0:
            print("🏆  EXCELLENT CONCEPTUAL LEARNING SUPPORT:")
            print("   • Semantic chunks provide comprehensive answers")
            print("   • Learning objectives are well fulfilled")
            print("   • Students can achieve concrete learning outcomes")
        elif avg_score >= 2.0:
            print("✅  GOOD LEARNING SUPPORT WITH ROOM FOR IMPROVEMENT:")
            print("   • Most learning objectives are covered")
            print("   • Enhance concept extraction for better coverage")
            print("   • Improve practical application examples")
        else:
            print("⚠️  LEARNING SUPPORT NEEDS IMPROVEMENT:")
            print("   • Learning objectives not adequately covered")
            print("   • Enhance semantic understanding for educational content")
            print("   • Improve chunking for learning goal fulfillment")
        
        return {
            'overall_score': avg_score,
            'effectiveness_grade': effectiveness_grade,
            'questions_tested': len(questions),
            'questions_with_matches': questions_with_matches,
            'relationships_created': len(relationships),
            'detailed_results': results
        }
        
    except Exception as e:
        print(f"❌ Error during conceptual learning test: {e}")
        return None

def save_results(results):
    """Save test results"""
    if not results:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conceptual_learning_test_results_{timestamp}.json"
    
    # Convert to serializable format
    serializable_results = {
        'test_date': datetime.now().isoformat(),
        'overall_score': results['overall_score'],
        'effectiveness_grade': results['effectiveness_grade'],
        'questions_tested': results['questions_tested'],
        'questions_with_matches': results['questions_with_matches'],
        'relationships_created': results['relationships_created'],
        'detailed_results': []
    }
    
    for result in results['detailed_results']:
        serializable_result = {
            'question_id': result['question']['id'],
            'question_text': result['question']['question'],
            'learning_objectives': result['question']['learning_objectives'],
            'expected_answers': result['question']['expected_answers'],
            'total_relevant_chunks': result['total_relevant'],
            'max_score': result['max_score'],
            'top_results': []
        }
        
        for chunk_info in result['top_results']:
            serializable_result['top_results'].append({
                'score': chunk_info['score'],
                'chunk_type': chunk_info['chunk_type'],
                'content_preview': chunk_info['content_preview']
            })
        
        serializable_results['detailed_results'].append(serializable_result)
    
    with open(filename, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"💾 Results saved to: {filename}")

if __name__ == "__main__":
    results = test_conceptual_learning()
    
    if results:
        save_results(results)
        print(f"\n🎯 CONCEPTUAL LEARNING TEST COMPLETED")
        print(f"   Overall Score: {results['overall_score']:.2f}")
        print(f"   Effectiveness Grade: {results['effectiveness_grade']}")
        print(f"   Success Rate: {results['questions_with_matches']}/{results['questions_tested']}")
    else:
        print("❌ Conceptual learning test failed")
