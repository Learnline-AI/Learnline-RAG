#!/usr/bin/env python3
"""
Vector Embedding Engine for Enhanced Educational RAG System
Generates semantic embeddings for educational content chunks
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import pickle
import sqlite3
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingMetadata:
    """Metadata for embeddings"""
    chunk_id: str
    content_hash: str
    embedding_model: str
    embedding_dimensions: int
    created_at: str
    chunk_type: str
    subject: str
    grade_level: int
    concepts: List[str]
    quality_score: float

@dataclass
class SemanticMatch:
    """Represents a semantic match between chunks"""
    chunk_id: str
    similarity_score: float
    content_preview: str
    concepts: List[str]
    chunk_type: str
    metadata: Dict[str, Any]

class VectorEmbeddingEngine:
    """
    Generates and manages vector embeddings for educational content
    Supports multiple embedding models and semantic search
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.embedding_model = None
        self.embedding_cache = {}
        self.vector_index = None
        self._initialize_embedding_model()
        
    def _get_default_config(self) -> Dict:
        """Default configuration for embedding generation"""
        return {
            'embedding_model': 'openai',  # Prioritize OpenAI embeddings
            'model_name': 'text-embedding-3-small',  # OpenAI embedding model
            'embedding_dimensions': 1536,  # OpenAI text-embedding-3-small dimensions
            'batch_size': 100,  # OpenAI supports larger batches
            'similarity_threshold': 0.3,  # Lower threshold for better semantic matching
            'max_content_length': 8000,  # OpenAI supports longer text
            'cache_embeddings': True,
            'vector_db_path': 'embeddings/vector_cache.db'
        }
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model based on configuration"""
        model_type = self.config['embedding_model']
        
        if model_type == 'openai':
            try:
                import openai
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    self.embedding_model = 'openai'  # Mark as initialized
                    logger.info(f"Initialized OpenAI embeddings with model: {self.config['model_name']}")
                else:
                    logger.warning("OPENAI_API_KEY not found in environment variables")
                    self._initialize_fallback_model()
            except ImportError:
                logger.warning("OpenAI not available. Install with: pip install openai")
                self._initialize_fallback_model()
        
        elif model_type == 'sentence-transformers':
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(self.config['model_name'])
                logger.info(f"Initialized SentenceTransformers model: {self.config['model_name']}")
            except ImportError:
                logger.warning("SentenceTransformers not available. Install with: pip install sentence-transformers")
                self._initialize_fallback_model()
        
        else:
            self._initialize_fallback_model()
    
    def _initialize_fallback_model(self):
        """Initialize fallback TF-IDF based embeddings"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.embedding_model = TfidfVectorizer(
                max_features=384,  # Match dimensions
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )
            self.config['embedding_model'] = 'tfidf'
            self.config['embedding_dimensions'] = 384
            logger.info("Initialized fallback TF-IDF model")
        except ImportError:
            logger.error("No embedding models available. Install scikit-learn or sentence-transformers")
            self.embedding_model = None
    
    def is_available(self) -> bool:
        """Check if embedding generation is available"""
        return self.embedding_model is not None
    
    def generate_embedding(self, content: str, metadata: Dict[str, Any] = None) -> Optional[np.ndarray]:
        """Generate embedding for a single piece of content"""
        if not self.is_available():
            logger.warning("No embedding model available")
            return None
        
        # Preprocess content
        processed_content = self._preprocess_content(content)
        
        try:
            if self.config['embedding_model'] == 'sentence-transformers':
                embedding = self.embedding_model.encode(processed_content, convert_to_numpy=True)
                
            elif self.config['embedding_model'] == 'openai':
                response = self.openai_client.embeddings.create(
                    model=self.config['model_name'],
                    input=processed_content
                )
                embedding = np.array(response.data[0].embedding)
                
            elif self.config['embedding_model'] == 'tfidf':
                # For TF-IDF, we need to fit on a corpus first
                if not hasattr(self.embedding_model, 'vocabulary_'):
                    # This is a single document case, return a simple hash-based embedding
                    return self._generate_hash_embedding(processed_content)
                else:
                    embedding = self.embedding_model.transform([processed_content]).toarray()[0]
            
            else:
                return None
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._generate_hash_embedding(processed_content)
    
    def generate_embeddings_batch(self, contents: List[str], metadatas: List[Dict] = None) -> List[Optional[np.ndarray]]:
        """Generate embeddings for multiple pieces of content efficiently"""
        if not self.is_available():
            logger.warning("No embedding model available")
            return [None] * len(contents)
        
        if not contents:
            return []
        
        # Preprocess all contents
        processed_contents = [self._preprocess_content(content) for content in contents]
        
        try:
            if self.config['embedding_model'] == 'sentence-transformers':
                embeddings = self.embedding_model.encode(processed_contents, convert_to_numpy=True, batch_size=self.config['batch_size'])
                return [emb.astype(np.float32) for emb in embeddings]
                
            elif self.config['embedding_model'] == 'openai':
                # OpenAI batch processing - send multiple texts in one request
                response = self.openai_client.embeddings.create(
                    model=self.config['model_name'],
                    input=processed_contents
                )
                embeddings = []
                for data_point in response.data:
                    embedding = np.array(data_point.embedding, dtype=np.float32)
                    embeddings.append(embedding)
                return embeddings
                
            elif self.config['embedding_model'] == 'tfidf':
                # Fit TF-IDF on the entire corpus
                tfidf_matrix = self.embedding_model.fit_transform(processed_contents)
                embeddings = [tfidf_matrix[i].toarray()[0].astype(np.float32) for i in range(tfidf_matrix.shape[0])]
                return embeddings
            
            else:
                return [self._generate_hash_embedding(content) for content in processed_contents]
                
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [self._generate_hash_embedding(content) for content in processed_contents]
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content before embedding generation"""
        if not content:
            return ""
        
        # Truncate if too long
        if len(content) > self.config['max_content_length']:
            content = content[:self.config['max_content_length']] + "..."
        
        # Basic cleaning
        content = content.replace('\n', ' ').replace('\r', ' ')
        content = ' '.join(content.split())  # Remove extra whitespace
        
        return content
    
    def _generate_hash_embedding(self, content: str) -> np.ndarray:
        """Generate a simple hash-based embedding as fallback"""
        # Create a consistent hash-based embedding
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Convert hash to numeric values
        embedding = []
        for i in range(0, min(len(content_hash), 32), 2):  # Take pairs of hex digits
            hex_pair = content_hash[i:i+2]
            embedding.append(int(hex_pair, 16) / 255.0)  # Normalize to [0,1]
        
        # Pad to required dimensions
        while len(embedding) < self.config['embedding_dimensions']:
            embedding.extend(embedding[:self.config['embedding_dimensions'] - len(embedding)])
        
        return np.array(embedding[:self.config['embedding_dimensions']], dtype=np.float32)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings"""
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        try:
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0
    
    def find_similar_chunks(self, query_embedding: np.ndarray, 
                           candidate_embeddings: List[Tuple[str, np.ndarray, Dict]], 
                           top_k: int = 5) -> List[SemanticMatch]:
        """Find most similar chunks based on embedding similarity"""
        if query_embedding is None or not candidate_embeddings:
            return []
        
        similarities = []
        
        for chunk_id, embedding, metadata in candidate_embeddings:
            if embedding is not None:
                similarity = self.compute_similarity(query_embedding, embedding)
                if similarity >= self.config['similarity_threshold']:
                    similarities.append((chunk_id, similarity, metadata))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Create SemanticMatch objects
        matches = []
        for chunk_id, similarity, metadata in similarities[:top_k]:
            match = SemanticMatch(
                chunk_id=chunk_id,
                similarity_score=similarity,
                content_preview=metadata.get('content_preview', ''),
                concepts=metadata.get('concepts', []),
                chunk_type=metadata.get('chunk_type', 'unknown'),
                metadata=metadata
            )
            matches.append(match)
        
        return matches
    
    def save_embeddings_to_cache(self, embeddings_data: List[Tuple[str, np.ndarray, EmbeddingMetadata]]):
        """Save embeddings to persistent cache"""
        if not self.config['cache_embeddings']:
            return
        
        try:
            os.makedirs(os.path.dirname(self.config['vector_db_path']), exist_ok=True)
            
            conn = sqlite3.connect(self.config['vector_db_path'])
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    content_hash TEXT,
                    embedding BLOB,
                    metadata TEXT,
                    created_at TEXT,
                    model_name TEXT
                )
            ''')
            
            for chunk_id, embedding, metadata in embeddings_data:
                embedding_blob = pickle.dumps(embedding)
                metadata_json = json.dumps(metadata.__dict__)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO embeddings 
                    (chunk_id, content_hash, embedding, metadata, created_at, model_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    chunk_id,
                    metadata.content_hash,
                    embedding_blob,
                    metadata_json,
                    metadata.created_at,
                    metadata.embedding_model
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(embeddings_data)} embeddings to cache")
            
        except Exception as e:
            logger.error(f"Failed to save embeddings to cache: {e}")
    
    def load_embeddings_from_cache(self, chunk_ids: List[str] = None) -> Dict[str, Tuple[np.ndarray, EmbeddingMetadata]]:
        """Load embeddings from persistent cache"""
        if not self.config['cache_embeddings'] or not os.path.exists(self.config['vector_db_path']):
            return {}
        
        try:
            conn = sqlite3.connect(self.config['vector_db_path'])
            cursor = conn.cursor()
            
            if chunk_ids:
                placeholders = ','.join(['?' for _ in chunk_ids])
                query = f'SELECT chunk_id, embedding, metadata FROM embeddings WHERE chunk_id IN ({placeholders})'
                cursor.execute(query, chunk_ids)
            else:
                cursor.execute('SELECT chunk_id, embedding, metadata FROM embeddings')
            
            results = cursor.fetchall()
            conn.close()
            
            cached_embeddings = {}
            for chunk_id, embedding_blob, metadata_json in results:
                embedding = pickle.loads(embedding_blob)
                metadata_dict = json.loads(metadata_json)
                metadata = EmbeddingMetadata(**metadata_dict)
                cached_embeddings[chunk_id] = (embedding, metadata)
            
            logger.info(f"Loaded {len(cached_embeddings)} embeddings from cache")
            return cached_embeddings
            
        except Exception as e:
            logger.error(f"Failed to load embeddings from cache: {e}")
            return {}
    
    def get_embedding_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated embeddings"""
        if not os.path.exists(self.config['vector_db_path']):
            return {'total_embeddings': 0, 'models_used': [], 'cache_size_mb': 0}
        
        try:
            conn = sqlite3.connect(self.config['vector_db_path'])
            cursor = conn.cursor()
            
            # Total embeddings
            cursor.execute('SELECT COUNT(*) FROM embeddings')
            total_embeddings = cursor.fetchone()[0]
            
            # Models used
            cursor.execute('SELECT DISTINCT model_name FROM embeddings')
            models_used = [row[0] for row in cursor.fetchall()]
            
            # Cache size
            cursor.execute('SELECT SUM(LENGTH(embedding)) FROM embeddings')
            total_bytes = cursor.fetchone()[0] or 0
            cache_size_mb = total_bytes / (1024 * 1024)
            
            conn.close()
            
            return {
                'total_embeddings': total_embeddings,
                'models_used': models_used,
                'cache_size_mb': round(cache_size_mb, 2),
                'embedding_dimensions': self.config['embedding_dimensions'],
                'current_model': self.config['embedding_model']
            }
            
        except Exception as e:
            logger.error(f"Failed to get embedding statistics: {e}")
            return {'total_embeddings': 0, 'models_used': [], 'cache_size_mb': 0}

# Convenience functions for easy usage

def create_embeddings_for_chunks(chunks: List[Dict], embedding_engine: VectorEmbeddingEngine = None) -> Dict[str, np.ndarray]:
    """Create embeddings for a list of educational chunks"""
    if embedding_engine is None:
        embedding_engine = VectorEmbeddingEngine()
    
    if not embedding_engine.is_available():
        logger.warning("Embedding engine not available")
        return {}
    
    contents = []
    chunk_ids = []
    metadatas = []
    
    for chunk in chunks:
        chunk_id = chunk.get('chunk_id', str(hash(chunk.get('content', ''))))
        content = chunk.get('content', '')
        metadata = chunk.get('metadata', {})
        
        contents.append(content)
        chunk_ids.append(chunk_id)
        metadatas.append(metadata)
    
    # Generate embeddings in batch
    embeddings = embedding_engine.generate_embeddings_batch(contents, metadatas)
    
    # Create embedding metadata and save to cache
    embeddings_data = []
    chunk_embeddings = {}
    
    for i, (chunk_id, embedding, content, metadata) in enumerate(zip(chunk_ids, embeddings, contents, metadatas)):
        if embedding is not None:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            embedding_metadata = EmbeddingMetadata(
                chunk_id=chunk_id,
                content_hash=content_hash,
                embedding_model=embedding_engine.config['embedding_model'],
                embedding_dimensions=len(embedding),
                created_at=datetime.now().isoformat(),
                chunk_type=metadata.get('type', 'unknown'),
                subject=metadata.get('basic_info', {}).get('subject', 'unknown'),
                grade_level=metadata.get('basic_info', {}).get('grade_level', 0),
                concepts=metadata.get('concepts_and_skills', {}).get('main_concepts', []),
                quality_score=metadata.get('quality_score', 0.0)
            )
            
            embeddings_data.append((chunk_id, embedding, embedding_metadata))
            chunk_embeddings[chunk_id] = embedding
    
    # Save to cache
    embedding_engine.save_embeddings_to_cache(embeddings_data)
    
    logger.info(f"Created embeddings for {len(chunk_embeddings)} chunks")
    return chunk_embeddings

def find_semantically_similar_content(query_content: str, 
                                    candidate_chunks: List[Dict], 
                                    top_k: int = 5,
                                    embedding_engine: VectorEmbeddingEngine = None) -> List[SemanticMatch]:
    """Find semantically similar educational content"""
    if embedding_engine is None:
        embedding_engine = VectorEmbeddingEngine()
    
    if not embedding_engine.is_available():
        logger.warning("Embedding engine not available")
        return []
    
    # Generate query embedding
    query_embedding = embedding_engine.generate_embedding(query_content)
    if query_embedding is None:
        return []
    
    # Generate candidate embeddings
    candidate_embeddings = []
    for chunk in candidate_chunks:
        chunk_id = chunk.get('chunk_id', str(hash(chunk.get('content', ''))))
        content = chunk.get('content', '')
        metadata = chunk.get('metadata', {})
        
        embedding = embedding_engine.generate_embedding(content, metadata)
        if embedding is not None:
            # Prepare metadata for matching
            match_metadata = {
                'content_preview': content[:200] + "..." if len(content) > 200 else content,
                'concepts': metadata.get('concepts_and_skills', {}).get('main_concepts', []),
                'chunk_type': metadata.get('type', 'unknown'),
                'quality_score': chunk.get('quality_score', 0.0),
                'grade_level': metadata.get('basic_info', {}).get('grade_level', 0),
                'subject': metadata.get('basic_info', {}).get('subject', 'unknown')
            }
            candidate_embeddings.append((chunk_id, embedding, match_metadata))
    
    # Find similar chunks
    matches = embedding_engine.find_similar_chunks(query_embedding, candidate_embeddings, top_k)
    
    return matches