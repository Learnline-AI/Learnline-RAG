#!/usr/bin/env python3
"""
Quality Validation Test for iesc111.pdf chunks
"""

import os
import sys
import json
from pathlib import Path
import traceback

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from holistic_rag_system import HolisticRAGChunker
from quality_validation_system import QualityValidator

def run_quality_validation():
    """Run comprehensive quality validation on iesc111.pdf chunks"""
    print("🔍" * 25)
    print("📊 QUALITY VALIDATION: iesc111.pdf")  
    print("🔍" * 25)
    print()
    
    pdf_path = "/Users/umangagarwal/Downloads/iesc1dd/iesc111.pdf"
    
    try:
        # Process PDF and generate chunks (same as before)
        import fitz
        doc = fitz.open(pdf_path)
        full_text = ""
        for page_num in range(len(doc)):
            page_text = doc[page_num].get_text()
            full_text += page_text + "\n"
        doc.close()
        
        # Create sections and chunks
        import re
        section_pattern = r'(\d+\.\d+)\s+([A-Z][^\.]+)'
        section_matches = list(re.finditer(section_pattern, full_text))
        
        chunker = HolisticRAGChunker()
        all_chunks = []
        
        for i, section_match in enumerate(section_matches):
            section_number = section_match.group(1)
            section_title = section_match.group(2).strip()
            start_pos = section_match.start()
            
            if i + 1 < len(section_matches):
                end_pos = section_matches[i + 1].start()
            else:
                end_pos = len(full_text)
            
            section_content = full_text[start_pos:end_pos].strip()
            
            mother_section = {
                'section_number': section_number,
                'title': section_title,
                'content': section_content,
                'full_content': section_content,
                'start_pos': start_pos,
                'end_pos': end_pos,
                'page_number': 1,
                'activities': [],
                'examples': [],
                'figures': [],
                'special_content': []
            }
            
            try:
                chunks = chunker.process_mother_section(mother_section, full_text, pdf_path)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"⚠️ Error in section {section_number}: {e}")
                continue
        
        print(f"✅ Generated {len(all_chunks)} chunks for validation")
        
        # Now run quality validation
        validator = QualityValidator()
        
        print(f"\\n📊 RUNNING QUALITY VALIDATION...")
        print("=" * 60)
        
        all_scores = []
        total_scores = {
            'content_completeness': 0,
            'concept_quality': 0,
            'educational_soundness': 0,
            'application_quality': 0,
            'coherence': 0,
            'metadata_richness': 0,
            'sentence_completeness': 0
        }
        
        for i, chunk in enumerate(all_chunks):
            print(f"\\n🔍 Validating Chunk {i+1}/{len(all_chunks)}")
            print(f"   ID: {chunk.chunk_id}")
            print(f"   Size: {len(chunk.content):,} characters")
            
            try:
                # The validator expects the chunk object directly, not a dict
                # Pass the chunk object and its content as original_content
                scores = validator.validate_chunk_quality(chunk, chunk.content)
                all_scores.append(scores)
                
                # Display individual scores
                print(f"   📈 Quality Scores:")
                for metric, score in scores['individual_scores'].items():
                    print(f"     {metric.replace('_', ' ').title()}: {score:.2f}/1.00")
                    if metric in total_scores:
                        total_scores[metric] += score
                
                print(f"   ⭐ Overall Score: {scores['overall_score']:.2f}/1.00")
                
                # Show issues if any
                if scores.get('issues'):
                    print(f"   ⚠️ Issues Found:")
                    for issue in scores['issues'][:3]:  # Show first 3 issues
                        print(f"     - {issue}")
                
            except Exception as e:
                print(f"   ❌ Validation Error: {e}")
                continue
        
        # Calculate overall statistics
        if all_chunks and all_scores:
            avg_scores = {metric: total/len(all_chunks) for metric, total in total_scores.items()}
            overall_avg = sum(score['overall_score'] for score in all_scores) / len(all_scores)
        else:
            avg_scores = total_scores
            overall_avg = 0
        
        print(f"\\n{'='*60}")
        print("📊 OVERALL VALIDATION RESULTS")
        print('=' * 60)
        
        print(f"📚 Total Chunks Validated: {len(all_chunks)}")
        print(f"⭐ Average Overall Score: {overall_avg:.2f}/1.00")
        
        print(f"\\n📈 Average Scores by Metric:")
        for metric, score in avg_scores.items():
            status = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
            print(f"   {status} {metric.replace('_', ' ').title()}: {score:.2f}/1.00")
        
        # Performance categories
        excellent = sum(1 for s in all_scores if s['overall_score'] >= 0.8)
        good = sum(1 for s in all_scores if 0.6 <= s['overall_score'] < 0.8) 
        fair = sum(1 for s in all_scores if 0.4 <= s['overall_score'] < 0.6)
        poor = sum(1 for s in all_scores if s['overall_score'] < 0.4)
        
        print(f"\\n🎯 Performance Distribution:")
        if excellent > 0: print(f"   🟢 Excellent (0.8+): {excellent} chunks")
        if good > 0: print(f"   🟡 Good (0.6-0.79): {good} chunks")  
        if fair > 0: print(f"   🟠 Fair (0.4-0.59): {fair} chunks")
        if poor > 0: print(f"   🔴 Needs Work (<0.4): {poor} chunks")
        
        # Top performers
        if all_scores:
            top_chunks = sorted(all_scores, key=lambda x: x['overall_score'], reverse=True)[:3]
            print(f"\\n🏆 Top 3 Performing Chunks:")
            for i, chunk_score in enumerate(top_chunks):
                chunk_id = chunk_score.get('chunk_id', f'chunk_{i+1}')
                score = chunk_score['overall_score']
                print(f"   {i+1}. {chunk_id}: {score:.2f}/1.00")
        
        # Common issues
        all_issues = []
        for score_result in all_scores:
            if 'issues' in score_result:
                all_issues.extend(score_result['issues'])
        
        if all_issues:
            # Count issue frequency
            issue_count = {}
            for issue in all_issues:
                issue_count[issue] = issue_count.get(issue, 0) + 1
            
            # Show most common issues
            common_issues = sorted(issue_count.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\\n⚠️ Most Common Issues:")
            for issue, count in common_issues:
                print(f"   • {issue} ({count} occurrences)")
        
        # Final assessment
        print(f"\\n🎉 FINAL ASSESSMENT:")
        if overall_avg >= 0.8:
            status = "🟢 EXCELLENT - Production Ready"
        elif overall_avg >= 0.6:
            status = "🟡 GOOD - Minor improvements needed"
        elif overall_avg >= 0.4:
            status = "🟠 FAIR - Moderate improvements needed"  
        else:
            status = "🔴 NEEDS SIGNIFICANT WORK"
        
        print(f"   Status: {status}")
        print(f"   Overall Quality: {overall_avg:.2f}/1.00")
        
        return all_chunks, all_scores, avg_scores, overall_avg
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        return None, None, None, 0

if __name__ == "__main__":
    chunks, scores, avg_scores, overall_avg = run_quality_validation()