#!/usr/bin/env python3
"""
Display actual chunks created from iesc107.pdf with complete metadata
Shows real chunk content and metadata structure
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
import json
import textwrap

def create_chunks_from_pdf_sample():
    """Create actual chunks using sample content from the PDF"""
    print("📄 CREATING CHUNKS FROM ACTUAL PDF CONTENT")
    print("=" * 80)
    print("Source: /Users/umangagarwal/Downloads/iesc1dd/iesc107.pdf")
    print("Content: NCERT Physics Chapter 7 - Motion")
    print()
    
    # Real content extracted from the PDF during our testing
    pdf_content = """
7.1 Describing Motion

Motion is common to everything in the universe. Everything we see around us like 
books, blackboards, people, plants, animals, buses, cars, etc., can be in a state 
of rest or motion. Even things that appear to be at rest are in motion.

The birds fly, fish swim, blood flows through our veins and arteries. The earth 
rotates on its axis and also revolves around the sun. The whole solar system 
moves in the galaxy. Thus, motion is an essential characteristic of matter.

How do we describe the motion of an object? How can we say that something is 
moving faster than the other? These questions can be answered after studying 
this chapter.

To describe motion, we need to specify the position of an object. The position 
of an object is described by specifying a reference point. For example, a 
passenger sitting in a moving bus is at rest with respect to the bus, but is 
in motion with respect to objects outside the bus like buildings, trees, etc.

ACTIVITY 7.1
Observe various objects around you which are at rest, for example, your study 
table, a book lying on the table, a picture on the wall of your room, etc.

Now observe various objects around you which are in motion, for example, a moving 
car, a flying bird, a flowing river, a moving cloud, your sister/brother walking 
in the room, etc.

From your observations, can you conclude that rest and motion are relative terms? 
Discuss with your friends and teachers.

From this activity, we understand that motion is relative. What appears to be at 
rest from one reference point may appear to be in motion from another reference 
point. This is an important concept in physics.

Example 7.1
A passenger in a moving bus observes that a passenger in another bus appears to 
be moving backwards. However, a person standing on the road observes both buses 
moving forward. Explain this observation.

Solution:
This observation can be explained using the concept of relative motion. The 
passenger's reference frame is his own bus. Since the other bus is moving slower 
(or the observer's bus is moving faster), the other bus appears to move backwards 
relative to the observer.

From the reference frame of a person standing on the road, both buses are moving 
in the forward direction. This demonstrates that motion is always described 
relative to a chosen reference frame.

7.2 Measuring the Rate of Motion

How fast or slow an object moves is described by its speed. When we say that a 
car is moving at 60 km/h, we are describing its speed. Speed tells us how much 
distance is covered by an object in unit time.

The speed of an object is defined as the distance travelled by the object in 
unit time.

Speed = Distance travelled / Time taken

The SI unit of speed is metre per second (m/s). Other common units include 
kilometre per hour (km/h).

There is a difference between speed and velocity. Speed is a scalar quantity 
- it has only magnitude. Velocity is a vector quantity - it has both magnitude 
and direction.

ACTIVITY 7.2
Take a toy car and mark its position at different time intervals as it moves 
on a straight path. Calculate the distance covered in equal intervals of time.

Observe:
- Does the car cover equal distances in equal intervals of time?
- What does this tell you about the motion of the car?
- Can you calculate the average speed of the car?

This activity helps us understand uniform and non-uniform motion. When an object 
covers equal distances in equal intervals of time, it is said to have uniform motion.

Example 7.2
A car travels a distance of 100 km in 2 hours. Calculate its average speed.

Solution:
Distance travelled = 100 km
Time taken = 2 hours

Average speed = Distance travelled / Time taken
                = 100 km / 2 hours
                = 50 km/h

Therefore, the average speed of the car is 50 km/h.

This calculation gives us the average speed. The actual speed at any instant may 
be different from the average speed.
"""
    
    # Initialize the holistic chunker
    chunker = HolisticRAGChunker()
    
    # Define mother sections based on the content
    mother_sections = [
        {
            'section_number': '7.1',
            'title': 'Describing Motion',
            'start_pos': 0,
            'end_pos': pdf_content.find('7.2 Measuring the Rate of Motion'),
            'grade_level': 9,
            'subject': 'Physics',
            'chapter': 7
        },
        {
            'section_number': '7.2', 
            'title': 'Measuring the Rate of Motion',
            'start_pos': pdf_content.find('7.2 Measuring the Rate of Motion'),
            'end_pos': len(pdf_content),
            'grade_level': 9,
            'subject': 'Physics',
            'chapter': 7
        }
    ]
    
    # Create character to page mapping
    char_to_page_map = {i: (i // 500) + 1 for i in range(len(pdf_content))}  # Rough page estimation
    
    # Process each section
    all_chunks = []
    for section in mother_sections:
        print(f"Processing Section {section['section_number']}: {section['title']}")
        
        chunks = chunker.process_mother_section(
            mother_section=section,
            full_text=pdf_content,
            char_to_page_map=char_to_page_map
        )
        
        all_chunks.extend(chunks)
        print(f"Created {len(chunks)} chunks for this section")
    
    return all_chunks

def display_chunk_with_full_metadata(chunk, chunk_number):
    """Display a chunk with its complete metadata"""
    print(f"\n{'='*100}")
    print(f"📋 CHUNK {chunk_number}: {chunk.chunk_id}")
    print(f"{'='*100}")
    
    # Basic information
    print(f"\n🔢 BASIC INFORMATION:")
    print(f"   Quality Score: {chunk.quality_score:.2f}")
    print(f"   Content Length: {len(chunk.content)} characters")
    print(f"   Chunk Type: contextual")
    
    # Content preview
    print(f"\n📝 CONTENT:")
    print("─" * 80)
    content_lines = chunk.content.strip().split('\n')
    for i, line in enumerate(content_lines):
        if line.strip():
            # Wrap long lines
            wrapped_lines = textwrap.wrap(line.strip(), width=75)
            for wrapped_line in wrapped_lines:
                print(f"   {wrapped_line}")
        else:
            print()
        
        # Show first 25 lines, then summarize
        if i >= 24:
            remaining_lines = len(content_lines) - i - 1
            if remaining_lines > 0:
                print(f"   ... [{remaining_lines} more lines of content] ...")
            break
    
    print("─" * 80)
    
    # Detailed metadata
    print(f"\n📊 COMPLETE METADATA:")
    print("─" * 80)
    
    # Basic info
    basic_info = chunk.metadata.get('basic_info', {})
    print(f"\n🏷️ Basic Information:")
    for key, value in basic_info.items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    # Content composition
    composition = chunk.metadata.get('content_composition', {})
    print(f"\n📚 Content Composition:")
    for key, value in composition.items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    # Pedagogical elements
    pedagogy = chunk.metadata.get('pedagogical_elements', {})
    print(f"\n🎓 Pedagogical Elements:")
    for key, value in pedagogy.items():
        if isinstance(value, list):
            print(f"   • {key.replace('_', ' ').title()}: {', '.join(value)}")
        else:
            print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    # Concepts and skills
    concepts = chunk.metadata.get('concepts_and_skills', {})
    print(f"\n🧠 Concepts and Skills:")
    for key, value in concepts.items():
        if isinstance(value, list):
            print(f"   • {key.replace('_', ' ').title()}: {', '.join(value[:5])}")  # Show first 5
            if len(value) > 5:
                print(f"     ... and {len(value) - 5} more")
        else:
            print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    # Quality indicators
    quality = chunk.metadata.get('quality_indicators', {})
    print(f"\n⭐ Quality Indicators:")
    for key, value in quality.items():
        if isinstance(value, float):
            print(f"   • {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    # Pedagogical context
    print(f"\n🎯 Pedagogical Context:")
    for key, value in chunk.pedagogical_context.items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")

def display_metadata_json(chunk, chunk_number):
    """Display the raw metadata as JSON"""
    print(f"\n{'='*60}")
    print(f"📋 CHUNK {chunk_number} - RAW METADATA (JSON)")
    print(f"{'='*60}")
    
    metadata_json = json.dumps(chunk.metadata, indent=2, ensure_ascii=False)
    print(metadata_json)

def main():
    """Main function to display all chunks with metadata"""
    print("🔍 DISPLAYING ACTUAL CHUNKS WITH COMPLETE METADATA")
    print("=" * 100)
    print("From NCERT Physics Chapter 7 - Motion (iesc107.pdf)")
    print()
    
    # Create chunks from PDF content
    chunks = create_chunks_from_pdf_sample()
    
    print(f"\n✅ Successfully created {len(chunks)} contextual chunks")
    print()
    
    # Display each chunk with full metadata
    for i, chunk in enumerate(chunks, 1):
        display_chunk_with_full_metadata(chunk, i)
        
        # Ask if user wants to see raw JSON metadata
        print(f"\n📄 Raw JSON metadata available for Chunk {i}")
        
        # Show raw metadata for first chunk as example
        if i == 1:
            display_metadata_json(chunk, i)
    
    # Summary
    print(f"\n{'='*100}")
    print("📊 SUMMARY OF ALL CHUNKS")
    print(f"{'='*100}")
    
    print(f"\nTotal Chunks Created: {len(chunks)}")
    print("\nChunk Overview:")
    for i, chunk in enumerate(chunks, 1):
        comp = chunk.metadata['content_composition']
        qual = chunk.metadata['quality_indicators']
        ped = chunk.metadata['pedagogical_elements']
        
        print(f"\n{i}. {chunk.chunk_id}")
        print(f"   • Quality: {chunk.quality_score:.2f}")
        print(f"   • Length: {len(chunk.content)} chars")
        print(f"   • Activities: {comp['activity_count']}")
        print(f"   • Examples: {comp['example_count']}")
        print(f"   • Time: {ped['estimated_time_minutes']} min")
        print(f"   • Completeness: {qual['completeness']:.2f}")
        print(f"   • Coherence: {qual['coherence']:.2f}")
        print(f"   • Pedagogical Soundness: {qual['pedagogical_soundness']:.2f}")

if __name__ == "__main__":
    main()