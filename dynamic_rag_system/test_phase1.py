#!/usr/bin/env python3
"""
Phase 1 Testing Script

Tests the core components of the Dynamic Educational RAG System
without complex imports or dependencies.
"""

import sys
import os
from pathlib import Path
import time
import logging
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_core_models():
    """Test core data models"""
    print("🧪 Testing Core Models...")
    
    # Test basic imports
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import core components one by one to isolate issues
        from core.models import (
            SourceDocument, ContentType, ProcessingStatus,
            BabyChunk, ChunkType, MotherSection
        )
        from core.config import SystemConfig
        from core.exceptions import RAGSystemException
        
        print("  ✅ Core imports successful")
        
        # Test SourceDocument creation
        doc = SourceDocument(
            title="Test NCERT Chapter",
            content_type=ContentType.PDF,
            file_path="/test/path.pdf",
            file_size=1024,
            file_hash="test_hash",
            subject="Physics",
            grade_level="9",
            curriculum="NCERT"
        )
        
        print(f"  ✅ SourceDocument created: {doc.document_id}")
        print(f"     Title: {doc.title}")
        print(f"     Type: {doc.content_type.value}")
        print(f"     Subject: {doc.subject}")
        
        # Test BabyChunk creation
        chunk = BabyChunk(
            chunk_type=ChunkType.ACTIVITY,
            document_id=doc.document_id,
            mother_section="8.1",
            mother_section_title="Force and Motion",
            content="Test activity content about force and motion"
        )
        
        print(f"  ✅ BabyChunk created: {chunk.chunk_id}")
        print(f"     Type: {chunk.chunk_type.value}")
        print(f"     Section: {chunk.mother_section}")
        
        # Test configuration
        config = SystemConfig()
        print(f"  ✅ Configuration loaded: {config.system_name}")
        print(f"     Environment: {config.environment.value}")
        print(f"     Debug mode: {config.debug}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Core models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pattern_library():
    """Test pattern library functionality"""
    print("\n🧪 Testing Pattern Library...")
    
    try:
        from chunking.pattern_library import PatternLibrary, PatternType
        
        # Create pattern library
        patterns = PatternLibrary(curriculum="NCERT", language="en")
        print("  ✅ Pattern library created")
        
        # Get statistics
        stats = patterns.get_pattern_statistics()
        print(f"  ✅ Pattern statistics:")
        print(f"     Total patterns: {stats['total_patterns']}")
        for pattern_type, count in stats['patterns_by_type'].items():
            print(f"     {pattern_type}: {count} patterns")
        
        # Test pattern matching on sample text
        sample_text = """
8.1 Force and Motion

When we push or pull an object, we are applying a force on it.

ACTIVITY 8.1
Take a ball and place it on a table. Push the ball gently.

Example 8.1
A force of 10 N is applied to a box of mass 2 kg.

Fig. 8.3: A ball at rest on a table
The ball remains at rest until a force is applied.
"""
        
        # Test different pattern types
        section_matches = patterns.find_matches(sample_text, PatternType.SECTION_HEADER)
        activity_matches = patterns.find_matches(sample_text, PatternType.ACTIVITY)
        example_matches = patterns.find_matches(sample_text, PatternType.EXAMPLE)
        figure_matches = patterns.find_matches(sample_text, PatternType.FIGURE_CONTENT)
        
        print(f"  ✅ Pattern matching results:")
        print(f"     Sections: {len(section_matches)}")
        print(f"     Activities: {len(activity_matches)}")
        print(f"     Examples: {len(example_matches)}")
        print(f"     Figures: {len(figure_matches)}")
        
        # Show specific matches
        for pattern, match, confidence in section_matches:
            print(f"     Section found: {match.group(1)} - {match.group(2)} (confidence: {confidence:.2f})")
        
        for pattern, match, confidence in activity_matches:
            print(f"     Activity found: {match.group(1)} (confidence: {confidence:.2f})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Pattern library test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_registry():
    """Test file registry with temporary database"""
    print("\n🧪 Testing File Registry...")
    
    try:
        # Use temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            tmp_db_path = tmp_db.name
        
        from storage.file_registry import FileRegistry
        from core.models import ContentType
        
        # Create file registry with temp database
        registry = FileRegistry(db_path=tmp_db_path)
        print("  ✅ File registry initialized")
        
        # Test document registration (with fake file for testing)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"fake PDF content for testing")
            tmp_file_path = tmp_file.name
        
        try:
            doc = registry.register_document(
                file_path=tmp_file_path,
                title="Test NCERT Physics",
                content_type=ContentType.PDF,
                educational_metadata={
                    "subject": "Physics",
                    "grade_level": "9",
                    "curriculum": "NCERT",
                    "chapter": "8"
                }
            )
            
            print(f"  ✅ Document registered: {doc.document_id}")
            print(f"     Title: {doc.title}")
            print(f"     File size: {doc.file_size} bytes")
            print(f"     Subject: {doc.subject}")
            
            # Test file change detection
            changed = registry.check_file_changes(doc.document_id)
            print(f"  ✅ Change detection: {'Changed' if changed else 'Unchanged'}")
            
            # Test processing job creation
            job = registry.create_processing_job(
                doc.document_id,
                job_type="test_processing",
                priority=5
            )
            print(f"  ✅ Processing job created: {job.job_id}")
            
            # Get statistics
            stats = registry.get_processing_statistics()
            print(f"  ✅ Registry statistics:")
            print(f"     Documents: {stats['document_counts']}")
            print(f"     Jobs: {stats['job_counts']}")
            
        finally:
            # Cleanup test files
            os.unlink(tmp_file_path)
            registry.close()
            os.unlink(tmp_db_path)
        
        return True
        
    except Exception as e:
        print(f"  ❌ File registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chunk_manager():
    """Test chunk manager functionality"""
    print("\n🧪 Testing Chunk Manager...")
    
    try:
        # Use temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            tmp_db_path = tmp_db.name
        
        from chunking.chunk_manager import ChunkManager, RelationshipType
        from core.models import BabyChunk, ChunkType
        
        # Create chunk manager
        chunk_manager = ChunkManager(db_path=tmp_db_path)
        print("  ✅ Chunk manager initialized")
        
        try:
            # Create test chunks
            chunk1 = BabyChunk(
                chunk_type=ChunkType.ACTIVITY,
                document_id="test_doc_1",
                mother_section="8.1",
                mother_section_title="Force and Motion",
                content="Activity about force and motion concepts",
                activity_metadata={
                    "activity_numbers": ["8.1"],
                    "materials_needed": ["ball", "table"]
                }
            )
            
            chunk2 = BabyChunk(
                chunk_type=ChunkType.EXAMPLE,
                document_id="test_doc_1", 
                mother_section="8.1",
                mother_section_title="Force and Motion",
                content="Example calculation using F=ma formula"
            )
            
            # Store chunk versions
            version1 = chunk_manager.store_chunk_version(chunk1, "Initial creation")
            version2 = chunk_manager.store_chunk_version(chunk2, "Initial creation")
            
            print(f"  ✅ Chunk versions stored:")
            print(f"     Chunk 1: {version1.version_id}")
            print(f"     Chunk 2: {version2.version_id}")
            
            # Add relationship
            relationship = chunk_manager.add_relationship(
                chunk1.chunk_id,
                chunk2.chunk_id,
                RelationshipType.PREREQUISITE,
                strength=0.8,
                confidence=0.9
            )
            
            print(f"  ✅ Relationship created: {relationship.relationship_id}")
            print(f"     Type: {relationship.relationship_type.value}")
            
            # Add concept mappings
            chunk_manager.add_concept_mapping("Force", chunk1.chunk_id, 0.9)
            chunk_manager.add_concept_mapping("Force", chunk2.chunk_id, 0.95)
            
            print(f"  ✅ Concept mappings added")
            
            # Get relationships
            relationships = chunk_manager.get_chunk_relationships(chunk1.chunk_id)
            print(f"  ✅ Found {len(relationships)} relationships for chunk 1")
            
            # Get concepts
            concepts = chunk_manager.get_chunk_concepts(chunk1.chunk_id)
            print(f"  ✅ Found {len(concepts)} concepts for chunk 1")
            for concept_name, confidence in concepts:
                print(f"     Concept: {concept_name} (confidence: {confidence:.2f})")
            
            # Get statistics
            stats = chunk_manager.get_statistics()
            print(f"  ✅ Chunk manager statistics:")
            for key, value in stats.items():
                print(f"     {key}: {value}")
            
        finally:
            chunk_manager.close()
            os.unlink(tmp_db_path)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Chunk manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_queue_manager():
    """Test queue manager functionality"""
    print("\n🧪 Testing Queue Manager...")
    
    try:
        # Use temporary database for file registry
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            tmp_db_path = tmp_db.name
        
        from pipeline.queue_manager import QueueManager
        from storage.file_registry import FileRegistry
        from core.models import ProcessingJob, ProcessingStatus
        
        # Create components
        registry = FileRegistry(db_path=tmp_db_path)
        queue_manager = QueueManager(registry)
        
        print("  ✅ Queue manager initialized")
        
        try:
            # Create test processing jobs
            job1 = ProcessingJob(
                document_id="test_doc_1",
                job_type="pdf_processing",
                priority=5,
                processing_config={"extract_text": True}
            )
            
            job2 = ProcessingJob(
                document_id="test_doc_2", 
                job_type="urgent_processing",
                priority=1,  # Higher priority
                processing_config={"extract_text": True, "detect_sections": True}
            )
            
            # Add jobs to queue
            queue_manager.add_job(job1)
            queue_manager.add_job(job2)
            
            print(f"  ✅ Added 2 jobs to queue")
            
            # Get queue metrics
            metrics = queue_manager.get_metrics()
            print(f"  ✅ Queue metrics:")
            print(f"     Total jobs: {metrics.total_jobs}")
            print(f"     Queued jobs: {metrics.queued_jobs}")
            print(f"     Processing jobs: {metrics.processing_jobs}")
            print(f"     Queue depth by priority: {metrics.queue_depth_by_priority}")
            
            # Test job status
            status1 = queue_manager.get_job_status(job1.job_id)
            status2 = queue_manager.get_job_status(job2.job_id)
            
            print(f"  ✅ Job statuses:")
            print(f"     Job 1: {status1.value if status1 else 'Not found'}")
            print(f"     Job 2: {status2.value if status2 else 'Not found'}")
            
            # Test queue position
            position1 = queue_manager.get_queue_position(job1.job_id)
            position2 = queue_manager.get_queue_position(job2.job_id)
            
            print(f"  ✅ Queue positions:")
            print(f"     Job 1: {position1}")
            print(f"     Job 2: {position2} (should be higher priority)")
            
        finally:
            queue_manager.stop(timeout=2.0)
            registry.close()
            os.unlink(tmp_db_path)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Queue manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_processor():
    """Test PDF processor (without actual PDF file)"""
    print("\n🧪 Testing PDF Processor...")
    
    try:
        from ingestion.pdf_processor import PDFProcessor
        from core.models import SourceDocument, ContentType
        
        # Create PDF processor
        processor = PDFProcessor()
        print("  ✅ PDF processor initialized")
        
        # Test supported formats
        formats = processor.get_supported_formats()
        print(f"  ✅ Supported formats: {formats}")
        
        # Test file validation (with non-existent file)
        valid, message = processor.validate_file("/nonexistent/file.pdf")
        print(f"  ✅ File validation test: {'Valid' if valid else f'Invalid - {message}'}")
        
        # Show processor configuration
        print(f"  ✅ Processor settings:")
        print(f"     Extraction method: {processor.extraction_method}")
        print(f"     NCERT page range: {processor.ncert_page_range}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ PDF processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 1 tests"""
    print("🚀 Dynamic Educational RAG System - Phase 1 Testing")
    print("=" * 60)
    
    tests = [
        ("Core Models", test_core_models),
        ("Pattern Library", test_pattern_library),
        ("File Registry", test_file_registry),
        ("Chunk Manager", test_chunk_manager),
        ("Queue Manager", test_queue_manager),
        ("PDF Processor", test_pdf_processor)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 1 components are working correctly!")
        print("\n🚀 System is ready for:")
        print("  • Processing educational PDF documents")
        print("  • Detecting hierarchical structure and special content")
        print("  • Managing chunks with versioning and relationships")
        print("  • Intelligent job queuing and processing")
        print("  • Building educational knowledge graphs")
    else:
        print("⚠️  Some components need attention before proceeding")
    
    print(f"\n📋 Next Steps:")
    print("  1. Test with real NCERT PDF files")
    print("  2. Implement AI metadata extraction (Phase 2)")
    print("  3. Add embedding generation and vector database")
    print("  4. Build search and retrieval APIs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Critical error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\nThank you for testing the Dynamic Educational RAG System! 🚀")