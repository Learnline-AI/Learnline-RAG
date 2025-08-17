#!/usr/bin/env python3
"""
Display all chunks from iesc107.pdf processing
"""

import sqlite3
import json

def display_chunks():
    """Display all chunks in a readable format"""
    
    db_path = "iesc107_analysis_20250802_175151.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        print("🎓" * 20)
        print("📚 CHUNKS FROM iesc107.pdf (NCERT Physics Chapter 7 - Motion)")
        print("🎓" * 20)
        print()
        
        # Get all chunks
        cursor = conn.execute("""
            SELECT chunk_id, chunk_type, content, metadata 
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
            
            print(f"{'='*60}")
            print(f"📋 CHUNK {i}: {chunk_type.upper()}")
            print(f"🆔 ID: {chunk_id}")
            print(f"📏 Size: {len(content):,} characters")
            
            # Show metadata
            if metadata:
                print(f"📊 Metadata:")
                for key, value in metadata.items():
                    if isinstance(value, list) and len(value) > 5:
                        print(f"   {key}: {value[:5]}... ({len(value)} total)")
                    else:
                        print(f"   {key}: {value}")
            
            print(f"\n📝 Content:")
            print("-" * 40)
            
            # Show content with appropriate formatting
            if chunk_type == 'activity':
                print("🎯 EDUCATIONAL ACTIVITIES:")
                # Split activities and show them clearly
                activities = content.split('Activity')
                for j, activity in enumerate(activities[1:], 1):  # Skip first empty part
                    activity_lines = activity.strip().split('\n')
                    if activity_lines:
                        activity_num = activity_lines[0].strip()
                        print(f"\n  📌 Activity {activity_num}")
                        # Show first few lines of each activity
                        for line in activity_lines[1:6]:
                            if line.strip():
                                print(f"     {line.strip()}")
                        if len(activity_lines) > 6:
                            print(f"     ... (continued)")
                        if j >= 3:  # Show only first 3 activities for brevity
                            remaining = len(activities) - 1 - j
                            if remaining > 0:
                                print(f"\n  📌 ... and {remaining} more activities")
                            break
            
            elif chunk_type == 'example':
                print("🧮 MATHEMATICAL EXAMPLES:")
                # Split examples and show them clearly
                examples = content.split('Example')
                for j, example in enumerate(examples[1:], 1):  # Skip first empty part
                    example_lines = example.strip().split('\n')
                    if example_lines:
                        example_num = example_lines[0].strip()
                        print(f"\n  📌 Example {example_num}")
                        # Show first few lines of each example
                        for line in example_lines[1:8]:
                            if line.strip():
                                print(f"     {line.strip()}")
                        if len(example_lines) > 8:
                            print(f"     ... (solution continues)")
                        if j >= 2:  # Show only first 2 examples for brevity
                            remaining = len(examples) - 1 - j
                            if remaining > 0:
                                print(f"\n  📌 ... and {remaining} more examples")
                            break
            
            elif chunk_type == 'content':
                print(f"📖 SECTION CONTENT:")
                # Show section content with proper formatting
                lines = content.split('\n')
                line_count = 0
                for line in lines:
                    if line.strip():
                        # Highlight section headers
                        if line.strip().startswith(('7.1', '7.2', '7.3', '7.4')):
                            print(f"\n  🔷 {line.strip()}")
                        else:
                            print(f"     {line.strip()}")
                        line_count += 1
                        if line_count >= 15:  # Show first 15 lines
                            remaining_lines = len([l for l in lines if l.strip()]) - line_count
                            if remaining_lines > 0:
                                print(f"     ... ({remaining_lines} more lines)")
                            break
            
            else:
                # Default formatting for other types
                lines = content.split('\n')
                for line in lines[:10]:  # Show first 10 lines
                    if line.strip():
                        print(f"     {line.strip()}")
                if len(lines) > 10:
                    print(f"     ... ({len(lines) - 10} more lines)")
            
            print()
        
        # Summary
        print(f"{'='*60}")
        print(f"📊 PROCESSING SUMMARY")
        print(f"{'='*60}")
        
        # Get document info
        doc_cursor = conn.execute("SELECT * FROM documents LIMIT 1")
        doc = doc_cursor.fetchone()
        
        if doc:
            structure_summary = json.loads(doc['structure_summary'])
            print(f"📖 Document: {doc['title']}")
            print(f"📏 File Size: {doc['file_size'] / (1024*1024):.1f} MB")
            print(f"📄 Pages: {doc['total_pages']}")
            print(f"🧩 Total Chunks: {doc['total_chunks']}")
            print(f"\n🏗️ Educational Elements Detected:")
            for element_type, count in structure_summary.items():
                print(f"   📚 {element_type.title()}: {count}")
        
        # Chunk distribution
        chunk_stats = {}
        total_content = 0
        for chunk in chunks:
            chunk_type = chunk['chunk_type']
            chunk_stats[chunk_type] = chunk_stats.get(chunk_type, 0) + 1
            total_content += len(chunk['content'])
        
        print(f"\n🧩 Chunk Distribution:")
        for chunk_type, count in chunk_stats.items():
            print(f"   🔹 {chunk_type.title()}: {count} chunks")
        
        print(f"\n📏 Content Statistics:")
        print(f"   Total content: {total_content:,} characters")
        print(f"   Average chunk size: {total_content // len(chunks):,} characters")
        
        print(f"\n🎯 Educational RAG System successfully processed NCERT Physics content!")
        print(f"   Ready for AI enhancement and vector embeddings.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error displaying chunks: {e}")

if __name__ == "__main__":
    display_chunks()