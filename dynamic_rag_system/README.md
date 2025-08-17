# Dynamic Educational RAG System

A sophisticated, modular RAG (Retrieval-Augmented Generation) system specifically designed for educational content. Built to preserve the pedagogical intelligence of the original NCERT processing system while adding scalability, multi-source support, and advanced content management.

## 🎯 Overview

This system transforms your original monolithic RAG implementation into a production-ready, dynamic platform that can:

- **Process multiple content sources**: PDFs, YouTube transcripts, web content
- **Maintain educational context**: Preserves pedagogical structure and relationships
- **Scale dynamically**: Add new content without reprocessing everything
- **Track changes**: Version control for content and embeddings
- **Build knowledge graphs**: Automatic relationship detection between concepts

## 🏗️ Architecture

```
dynamic_rag_system/
├── core/                    # Fundamental data models and configuration
├── ingestion/              # Multi-source content processing
├── chunking/               # Educational structure detection and chunking
├── enrichment/             # AI-powered metadata extraction
├── embedding/              # Vector generation and management
├── storage/                # Data persistence and indexing
├── pipeline/               # Processing orchestration
├── retrieval/              # Search and ranking
├── api/                    # REST APIs for integration
└── utils/                  # Utilities and helpers
```

## 🚀 Key Features

### 📚 Educational Intelligence Preserved
- **Hierarchical Section Detection**: Maintains the proven section detection from your original system
- **Activity & Example Recognition**: Specialized patterns for educational content types
- **Concept Relationship Mapping**: Builds knowledge graphs of prerequisite relationships
- **Quality Validation**: Multi-layer validation ensures educational soundness

### 🔄 Dynamic Content Management
- **Incremental Processing**: Add new files without reprocessing existing content
- **Version Control**: Track changes in chunks and embeddings over time
- **Relationship Tracking**: Maintain connections between related content
- **Change Detection**: Automatic detection of file modifications

### 📊 Production-Ready Infrastructure
- **Queue Management**: Intelligent job scheduling with priority and resource management
- **Error Recovery**: Robust error handling with automatic retries
- **Monitoring**: Real-time progress tracking and performance metrics
- **Scalable Storage**: SQLite for development, easily upgradeable to PostgreSQL

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- PyMuPDF (fitz)
- SQLite3
- Optional: OpenAI API key for AI metadata extraction

### Installation
```bash
# Clone or download the system
cd dynamic_rag_system

# Install dependencies
pip install PyMuPDF sqlite3 numpy pandas tqdm

# Optional: For AI features
pip install openai anthropic
```

### Configuration
```python
from core.config import get_config

config = get_config()
# Customize settings as needed
config.ai.openai_api_key = "your-api-key"
config.processing.min_chunk_size = 800
config.processing.max_chunk_size = 1200
```

## 🚀 Quick Start

### 1. Run the Demonstration
```bash
python demo.py
```

This will showcase all major features with sample data.

### 2. Process Your First Document
```python
from storage.file_registry import FileRegistry
from ingestion.pdf_processor import PDFProcessor
from chunking.section_detector import SectionDetector
from chunking.pattern_library import PatternLibrary

# Initialize components
registry = FileRegistry()
processor = PDFProcessor()
patterns = PatternLibrary(curriculum="NCERT")
detector = SectionDetector(patterns)

# Register and process a document
document = registry.register_document(
    "path/to/your/ncert_physics.pdf",
    title="NCERT Physics Chapter 8",
    educational_metadata={
        "subject": "Physics",
        "grade_level": "9",
        "curriculum": "NCERT"
    }
)

# Extract text and detect structure
extraction_result = processor.process_document(document)
sections = detector.detect_sections(extraction_result)

print(f"Found {len(sections)} sections with educational structure")
```

### 3. Build Relationships and Knowledge Graph
```python
from chunking.chunk_manager import ChunkManager, RelationshipType

chunk_manager = ChunkManager()

# Store chunks with versioning
for chunk in baby_chunks:
    version = chunk_manager.store_chunk_version(chunk, "Initial processing")

# Detect prerequisite relationships
relationships = chunk_manager.detect_prerequisite_relationships(baby_chunks)

# Add concept mappings
chunk_manager.add_concept_mapping("Force", chunk_id, confidence=0.9)
```

## 📁 Component Details

### Core Models (`core/`)
- **SourceDocument**: Represents any input document with educational metadata
- **MotherSection**: Major sections (8.1, 8.2, etc.) with boundaries and special content
- **BabyChunk**: RAG-friendly chunks with type-specific metadata and relationships
- **ChunkRelationship**: Represents relationships between chunks (prerequisite, related, etc.)

### Pattern Library (`chunking/pattern_library.py`)
- **Configurable Patterns**: Regex patterns for educational content detection
- **Multi-language Support**: English and Hindi patterns included
- **Performance Tracking**: Patterns learn and improve over time
- **Curriculum-Specific**: Tailored for NCERT, CBSE, and other curricula

### Section Detection (`chunking/section_detector.py`)
- **Hierarchical Detection**: Preserves the proven section detection logic
- **Special Content**: Identifies activities, examples, figures, and special boxes
- **Confidence Scoring**: Multi-factor confidence calculation
- **Boundary Validation**: Prevents content bleeding between sections

### Chunk Management (`chunking/chunk_manager.py`)
- **Version Control**: Complete change tracking for chunks
- **Relationship Mapping**: Build knowledge graphs automatically
- **Concept Tagging**: Associate chunks with educational concepts
- **Prerequisites Detection**: Automatic detection of learning dependencies

### File Registry (`storage/file_registry.py`)
- **Document Tracking**: Complete lifecycle management for all files
- **Change Detection**: SHA-256 hashing for modification detection
- **Processing Queue**: Intelligent job scheduling and prioritization
- **Statistics**: Real-time monitoring of processing status

## 🎯 Migration from Original System

The new system preserves all working logic while adding modularity:

### Preserved Components
✅ **PDF Text Extraction**: Left-then-right column ordering logic
✅ **Section Detection**: All regex patterns and boundary detection
✅ **Special Content**: Activity, example, and figure detection
✅ **Quality Validation**: Educational soundness checking

### Enhanced Components
🚀 **Modular Architecture**: Easy to extend and maintain
🚀 **Version Control**: Track all changes over time
🚀 **Multi-Source**: Beyond PDFs to YouTube, web content
🚀 **Relationships**: Automatic knowledge graph building
🚀 **Monitoring**: Real-time progress and error tracking

## 🔌 API Integration

### REST APIs (Planned)
```python
# Add new document
POST /api/documents
{
    "file_path": "/path/to/file.pdf",
    "title": "Chapter Title",
    "subject": "Physics",
    "grade_level": "9"
}

# Search content
GET /api/search?q=force+and+motion&grade=9&subject=Physics

# Get chunk relationships
GET /api/chunks/{chunk_id}/relationships
```

### Direct Integration
```python
# Use components directly in your application
from dynamic_rag_system import ProcessingPipeline

pipeline = ProcessingPipeline()
result = pipeline.process_document("file.pdf")
chunks = result.get_baby_chunks()
```

## 📊 Monitoring & Analytics

### Real-time Metrics
- Processing queue status and throughput
- Chunk quality scores and confidence levels
- Relationship detection accuracy
- System resource utilization

### Educational Analytics
- Concept coverage across curriculum
- Learning path analysis
- Prerequisite relationship mapping
- Content difficulty progression

## 🔬 Advanced Features

### Concept Knowledge Graph
```python
# Find all chunks related to "Force"
related_chunks = chunk_manager.get_chunks_by_concept("Force", min_confidence=0.7)

# Discover learning paths
path = chunk_manager.find_related_chunks(
    chunk_id="activity_8_1", 
    max_distance=3,
    min_strength=0.5
)
```

### Multi-Source Processing
```python
# YouTube transcript processing (planned)
from ingestion.youtube_processor import YouTubeProcessor

youtube = YouTubeProcessor()
transcript_chunks = youtube.process_video("youtube_video_id")

# Web content processing (planned)
from ingestion.web_scraper import WebScraper

web = WebScraper()
web_chunks = web.process_url("https://educational-content.com")
```

## 🧪 Testing

```bash
# Run demonstration
python demo.py

# Test pattern matching
python -m chunking.pattern_library

# Test chunk management
python -m chunking.chunk_manager
```

## 🤝 Contributing

This system is designed for educational technology. Key areas for contribution:

1. **New Content Sources**: YouTube, Khan Academy, etc.
2. **Language Support**: Additional curriculum languages
3. **Subject Expansion**: Beyond NCERT to other educational systems
4. **AI Enhancements**: Better metadata extraction
5. **Performance**: Optimization for large-scale processing

## 📈 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Modular architecture
- [x] File registry and queue management
- [x] PDF processing migration
- [x] Section detection enhancement
- [x] Chunk versioning system

### Phase 2: AI Integration (In Progress)
- [ ] AI metadata extraction pipeline
- [ ] Embedding generation and management
- [ ] Vector database integration
- [ ] Search and ranking algorithms

### Phase 3: Multi-Source Support
- [ ] YouTube transcript processing
- [ ] Web content extraction
- [ ] Image and diagram processing
- [ ] Audio content transcription

### Phase 4: Production Features
- [ ] Web-based management interface
- [ ] Multi-user support and authentication
- [ ] Advanced analytics and reporting
- [ ] Integration with LMS platforms

## 📞 Support

For questions about the system architecture or implementation:

1. Review the demonstration script (`demo.py`)
2. Check component documentation in each module
3. Examine the original working logic preservation
4. Test with your specific educational content

## 📄 License

This educational RAG system is designed for educational technology applications. Please ensure compliance with content licensing when processing educational materials.

---

**Built with ❤️ for Educational Technology**

*Preserving pedagogical intelligence while enabling dynamic content management*