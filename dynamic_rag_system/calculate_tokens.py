#!/usr/bin/env python3
"""
Calculate token counts for each chunk using different tokenization methods
"""

import sqlite3
import json
import re

def estimate_tokens_simple(text):
    """Simple token estimation: words + punctuation"""
    # Split by whitespace and count
    words = len(text.split())
    # Add extra tokens for punctuation and special characters
    punctuation_count = len(re.findall(r'[.,!?;:()\[\]{}"\'`]', text))
    return words + punctuation_count

def estimate_tokens_gpt_style(text):
    """GPT-style token estimation (roughly 4 characters per token)"""
    return len(text) // 4

def estimate_tokens_precise(text):
    """More precise estimation considering common patterns"""
    # Split by whitespace
    words = text.split()
    token_count = 0
    
    for word in words:
        # Most words are 1 token
        if len(word) <= 4:
            token_count += 1
        # Longer words might be split
        elif len(word) <= 8:
            token_count += 1 if word.isalpha() else 2
        else:
            # Very long words (likely compound or technical terms)
            token_count += max(1, len(word) // 4)
    
    # Add tokens for punctuation and special formatting
    special_chars = len(re.findall(r'[.,!?;:()\[\]{}"\'`\n\t]', text))
    token_count += special_chars // 2  # Punctuation often combines with adjacent tokens
    
    # Add tokens for numbers and formulas
    numbers = len(re.findall(r'\d+', text))
    token_count += numbers
    
    # Add tokens for mathematical expressions
    math_expressions = len(re.findall(r'[=+\-*/^]', text))
    token_count += math_expressions // 2
    
    return token_count

def analyze_chunk_tokens():
    """Analyze token counts for all chunks"""
    
    db_path = "iesc107_analysis_20250802_175151.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        print("=" * 80)
        print("🔢 TOKEN ANALYSIS - iesc107.pdf CHUNKS")
        print("=" * 80)
        
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
        
        total_tokens_simple = 0
        total_tokens_gpt = 0
        total_tokens_precise = 0
        total_characters = 0
        total_words = 0
        
        print(f"\n{'Chunk':<8} {'Type':<10} {'Chars':<8} {'Words':<8} {'Simple':<8} {'GPT-4':<8} {'Precise':<8} {'Section/Info':<30}")
        print("-" * 90)
        
        for i, chunk in enumerate(chunks, 1):
            chunk_type = chunk['chunk_type']
            chunk_id = chunk['chunk_id'][:8]
            content = chunk['content']
            metadata = json.loads(chunk['metadata']) if chunk['metadata'] else {}
            
            # Calculate different token estimates
            char_count = len(content)
            word_count = len(content.split())
            tokens_simple = estimate_tokens_simple(content)
            tokens_gpt = estimate_tokens_gpt_style(content)
            tokens_precise = estimate_tokens_precise(content)
            
            # Get section info for content chunks
            section_info = ""
            if chunk_type == 'content':
                section_info = f"Sec {metadata.get('section_number', '?')}"
            elif chunk_type == 'activity':
                activity_count = metadata.get('count', 0)
                section_info = f"{activity_count} activities"
            elif chunk_type == 'example':
                example_count = metadata.get('count', 0)
                section_info = f"{example_count} examples"
            else:
                section_info = chunk_type
            
            print(f"{i:<8} {chunk_type:<10} {char_count:<8,} {word_count:<8,} {tokens_simple:<8,} {tokens_gpt:<8,} {tokens_precise:<8,} {section_info:<30}")
            
            total_tokens_simple += tokens_simple
            total_tokens_gpt += tokens_gpt
            total_tokens_precise += tokens_precise
            total_characters += char_count
            total_words += word_count
        
        print("-" * 90)
        print(f"{'TOTAL':<8} {'ALL':<10} {total_characters:<8,} {total_words:<8,} {total_tokens_simple:<8,} {total_tokens_gpt:<8,} {total_tokens_precise:<8,} {'All chunks':<30}")
        
        # Detailed analysis
        print(f"\n" + "=" * 80)
        print("📊 DETAILED TOKEN ANALYSIS")
        print("=" * 80)
        
        print(f"\n📏 Overall Statistics:")
        print(f"   Total characters: {total_characters:,}")
        print(f"   Total words: {total_words:,}")
        print(f"   Average characters per word: {total_characters / total_words:.1f}")
        
        print(f"\n🔢 Token Estimates:")
        print(f"   Simple method (words + punctuation): {total_tokens_simple:,} tokens")
        print(f"   GPT-style (4 chars/token): {total_tokens_gpt:,} tokens")
        print(f"   Precise method (context-aware): {total_tokens_precise:,} tokens")
        
        print(f"\n📊 Token Distribution by Chunk Type:")
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk['chunk_type']
            content = chunk['content']
            tokens = estimate_tokens_precise(content)
            
            if chunk_type not in chunk_types:
                chunk_types[chunk_type] = {'count': 0, 'tokens': 0, 'chars': 0}
            
            chunk_types[chunk_type]['count'] += 1
            chunk_types[chunk_type]['tokens'] += tokens
            chunk_types[chunk_type]['chars'] += len(content)
        
        for chunk_type, stats in chunk_types.items():
            avg_tokens = stats['tokens'] // stats['count']
            avg_chars = stats['chars'] // stats['count']
            print(f"   {chunk_type.title()}: {stats['count']} chunks, {stats['tokens']:,} tokens total, {avg_tokens:,} avg/chunk")
        
        # Token usage for different AI models
        print(f"\n🤖 AI Model Context Usage:")
        print(f"   GPT-4 context window (128k tokens): {(total_tokens_precise / 128000) * 100:.1f}% used")
        print(f"   GPT-3.5 context window (16k tokens): {(total_tokens_precise / 16000) * 100:.1f}% used")
        print(f"   Claude-3 context window (200k tokens): {(total_tokens_precise / 200000) * 100:.1f}% used")
        
        # Embedding considerations
        print(f"\n🔍 Vector Embedding Considerations:")
        max_chunk_tokens = max(estimate_tokens_precise(chunk['content']) for chunk in chunks)
        min_chunk_tokens = min(estimate_tokens_precise(chunk['content']) for chunk in chunks)
        avg_chunk_tokens = total_tokens_precise // len(chunks)
        
        print(f"   Largest chunk: {max_chunk_tokens:,} tokens")
        print(f"   Smallest chunk: {min_chunk_tokens:,} tokens")
        print(f"   Average chunk: {avg_chunk_tokens:,} tokens")
        print(f"   OpenAI embedding limit (8k tokens): {'✅ All chunks fit' if max_chunk_tokens <= 8000 else '⚠️ Some chunks exceed'}")
        
        # Cost estimation (rough)
        print(f"\n💰 Rough Cost Estimates (USD):")
        print(f"   GPT-4 processing (~$0.03/1k tokens): ${(total_tokens_precise * 0.03 / 1000):.2f}")
        print(f"   GPT-3.5 processing (~$0.002/1k tokens): ${(total_tokens_precise * 0.002 / 1000):.3f}")
        print(f"   OpenAI embeddings (~$0.0001/1k tokens): ${(total_tokens_precise * 0.0001 / 1000):.4f}")
        
        # Show individual chunk details
        print(f"\n" + "=" * 80)
        print("📋 INDIVIDUAL CHUNK TOKEN DETAILS")
        print("=" * 80)
        
        for i, chunk in enumerate(chunks, 1):
            chunk_type = chunk['chunk_type']
            chunk_id = chunk['chunk_id'][:8]
            content = chunk['content']
            metadata = json.loads(chunk['metadata']) if chunk['metadata'] else {}
            
            tokens = estimate_tokens_precise(content)
            chars = len(content)
            words = len(content.split())
            
            print(f"\n📋 Chunk {i}: {chunk_type.upper()}")
            print(f"   ID: {chunk_id}")
            print(f"   Content: {chars:,} chars, {words:,} words, ~{tokens:,} tokens")
            
            if chunk_type == 'content':
                section = metadata.get('section_number', 'Unknown')
                title = metadata.get('section_title', 'Untitled')[:40]
                print(f"   Section: {section} - {title}")
            elif chunk_type == 'activity':
                activities = metadata.get('activity_numbers', [])
                print(f"   Activities: {len(activities)} total ({', '.join(activities[:5])}{'...' if len(activities) > 5 else ''})")
            elif chunk_type == 'example':
                examples = metadata.get('example_numbers', [])
                has_solutions = metadata.get('has_solutions', False)
                print(f"   Examples: {len(examples)} total, Solutions: {'Yes' if has_solutions else 'No'}")
            
            # Token density analysis
            token_density = tokens / chars if chars > 0 else 0
            print(f"   Token density: {token_density:.3f} tokens/char")
            
            # Determine if chunk is good for different use cases
            if tokens <= 1000:
                print(f"   ✅ Excellent for: Chat completion, embedding, fine-tuning")
            elif tokens <= 2000:
                print(f"   ✅ Good for: Chat completion, embedding")
            elif tokens <= 4000:
                print(f"   ⚠️  Consider splitting for: Embedding, fine-tuning")
            else:
                print(f"   🔄 Recommend splitting for: Most use cases")
        
        conn.close()
        
    except FileNotFoundError:
        print(f"❌ Database file not found: {db_path}")
        print("Please run the iesc107.pdf processing script first.")
    except Exception as e:
        print(f"❌ Error analyzing tokens: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_chunk_tokens()