#!/usr/bin/env python3
"""
Detailed Chunks Report - Show complete content and metadata for each chunk
"""

import sqlite3
import json
from datetime import datetime

def format_metadata(metadata):
    """Format metadata in a readable way"""
    if not metadata:
        return "No metadata available"
    
    formatted = []
    for key, value in metadata.items():
        if isinstance(value, list):
            if len(value) <= 5:
                formatted.append(f"    {key}: {value}")
            else:
                formatted.append(f"    {key}: {value[:5]}... (showing 5 of {len(value)} items)")
        elif isinstance(value, str) and len(value) > 100:
            formatted.append(f"    {key}: {value[:100]}...")
        else:
            formatted.append(f"    {key}: {value}")
    
    return "\n".join(formatted)

def display_detailed_chunks():
    """Display each chunk with complete content and metadata"""
    
    db_path = "iesc107_analysis_20250802_175151.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        print("=" * 80)
        print("📚 DETAILED CHUNKS REPORT - iesc107.pdf")
        print("📖 NCERT Physics Chapter 7: Motion")
        print("=" * 80)
        print()
        
        # Get document information first
        doc_cursor = conn.execute("SELECT * FROM documents LIMIT 1")
        doc = doc_cursor.fetchone()
        
        if doc:
            print("📄 DOCUMENT INFORMATION:")
            print(f"    Title: {doc['title']}")
            print(f"    File Path: {doc['file_path']}")
            print(f"    File Size: {doc['file_size']:,} bytes ({doc['file_size'] / (1024*1024):.2f} MB)")
            print(f"    Total Pages: {doc['total_pages']}")
            print(f"    Processed At: {doc['processed_at']}")
            print(f"    Total Chunks Created: {doc['total_chunks']}")
            
            structure_summary = json.loads(doc['structure_summary'])
            content_types = json.loads(doc['content_types']) if doc['content_types'] else []
            
            print(f"    Content Types Detected: {', '.join(content_types)}")
            print(f"    Educational Elements Found:")
            for element_type, count in structure_summary.items():
                print(f"        {element_type.replace('_', ' ').title()}: {count}")
        
        print("\n" + "=" * 80)
        print("🧩 INDIVIDUAL CHUNKS")
        print("=" * 80)
        
        # Get all chunks ordered by type and ID
        cursor = conn.execute("""
            SELECT chunk_id, chunk_type, content, metadata, created_at
            FROM chunks 
            ORDER BY 
                CASE chunk_type 
                    WHEN 'content' THEN 1
                    WHEN 'activity' THEN 2 
                    WHEN 'example' THEN 3
                    WHEN 'summary' THEN 4
                    ELSE 5
                END,
                chunk_id
        """)
        
        chunks = cursor.fetchall()
        
        for i, chunk in enumerate(chunks, 1):
            chunk_type = chunk['chunk_type']
            chunk_id = chunk['chunk_id']
            content = chunk['content']
            metadata = json.loads(chunk['metadata']) if chunk['metadata'] else {}
            created_at = chunk['created_at']
            
            print(f"\n{'█' * 80}")
            print(f"📋 CHUNK #{i}: {chunk_type.upper()}")
            print(f"{'█' * 80}")
            print(f"🆔 Chunk ID: {chunk_id}")
            print(f"📊 Type: {chunk_type}")
            print(f"📏 Content Size: {len(content):,} characters ({len(content.split())} words)")
            print(f"🕒 Created: {created_at}")
            
            print(f"\n📋 METADATA:")
            print(format_metadata(metadata))
            
            print(f"\n📝 FULL CONTENT:")
            print("▼" * 80)
            
            # Display content based on type
            if chunk_type == 'content':
                print(content)
            
            elif chunk_type == 'activity':
                print("🎯 EDUCATIONAL ACTIVITIES CHUNK")
                print("=" * 50)
                
                # Try to separate individual activities
                activities = content.split('Activity')
                activity_count = 0
                
                for j, activity_text in enumerate(activities):
                    if activity_text.strip():
                        # Clean up activity text
                        lines = activity_text.strip().split('\n')
                        if lines and any(char.isdigit() for char in lines[0]):
                            activity_count += 1
                            print(f"\n🔹 ACTIVITY {activity_count}:")
                            print("-" * 30)
                            
                            # Print activity content
                            for line in lines:
                                if line.strip():
                                    print(line)
                            
                            print()  # Add spacing between activities
                
                if activity_count == 0:
                    # Fallback: show raw content if parsing fails
                    print(content)
            
            elif chunk_type == 'example':
                print("🧮 MATHEMATICAL EXAMPLES CHUNK")
                print("=" * 50)
                
                # Try to separate individual examples
                examples = content.split('Example')
                example_count = 0
                
                for j, example_text in enumerate(examples):
                    if example_text.strip():
                        lines = example_text.strip().split('\n')
                        if lines and any(char.isdigit() for char in lines[0]):
                            example_count += 1
                            print(f"\n🔹 EXAMPLE {example_count}:")
                            print("-" * 30)
                            
                            # Print example content
                            for line in lines:
                                if line.strip():
                                    print(line)
                            
                            print()  # Add spacing between examples
                
                if example_count == 0:
                    # Fallback: show raw content if parsing fails
                    print(content)
            
            else:
                # For any other chunk types
                print(content)
            
            print("▲" * 80)
            
            # Add chunk summary
            word_count = len(content.split())
            char_count = len(content)
            print(f"\n📊 CHUNK SUMMARY:")
            print(f"    Words: {word_count:,}")
            print(f"    Characters: {char_count:,}")
            print(f"    Lines: {len(content.split(chr(10))):,}")
            
            if i < len(chunks):
                print(f"\n{'─' * 80}")
        
        # Final summary
        print(f"\n{'=' * 80}")
        print("📈 PROCESSING SUMMARY")
        print(f"{'=' * 80}")
        
        total_words = sum(len(chunk['content'].split()) for chunk in chunks)
        total_chars = sum(len(chunk['content']) for chunk in chunks)
        
        chunk_stats = {}
        for chunk in chunks:
            chunk_type = chunk['chunk_type']
            chunk_stats[chunk_type] = chunk_stats.get(chunk_type, 0) + 1
        
        print(f"📖 Total chunks processed: {len(chunks)}")
        print(f"📊 Chunk distribution:")
        for chunk_type, count in chunk_stats.items():
            print(f"    {chunk_type.title()}: {count}")
        
        print(f"📏 Content statistics:")
        print(f"    Total words: {total_words:,}")
        print(f"    Total characters: {total_chars:,}")
        print(f"    Average chunk size: {total_chars // len(chunks):,} characters")
        
        print(f"\n🎯 Educational RAG System Processing Status: ✅ COMPLETE")
        print(f"📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        conn.close()
        
    except FileNotFoundError:
        print(f"❌ Database file not found: {db_path}")
        print("Please run the iesc107.pdf processing script first.")
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    display_detailed_chunks()