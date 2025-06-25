"""
Document search functionality using sentence embeddings
"""

import json
import logging
import re
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class DocumentSearchEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the document search engine
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.document_chunks = []  # List of text chunks
        self.embeddings = None     # Numpy array of embeddings
        self.chunk_metadata = []   # Metadata for each chunk (doc_id, chunk_id, etc.)
        
        # Initialize model (this will download on first use)
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Clean up text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If paragraph is small enough, add to current chunk
            if len(current_chunk + paragraph) <= chunk_size:
                current_chunk += paragraph + " "
            else:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with current paragraph
                if len(paragraph) <= chunk_size:
                    current_chunk = paragraph + " "
                else:
                    # Split long paragraph into smaller chunks
                    words = paragraph.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk + word) <= chunk_size:
                            current_chunk += word + " "
                        else:
                            if current_chunk.strip():
                                chunks.append(current_chunk.strip())
                            current_chunk = word + " "
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Ensure minimum chunk quality
        chunks = [chunk for chunk in chunks if len(chunk.split()) >= 5]
        
        return chunks
    
    def add_document(self, doc_id: str, text: str, filename: str = ""):
        """
        Add a document to the search index
        
        Args:
            doc_id: Unique document identifier
            text: Document text content
            filename: Original filename for reference
        """
        try:
            # Chunk the text
            chunks = self._chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks for document {doc_id}")
            
            # Generate embeddings for chunks
            if chunks:
                chunk_embeddings = self.model.encode(chunks)
                
                # Store chunks and metadata
                for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                    self.document_chunks.append(chunk)
                    self.chunk_metadata.append({
                        'doc_id': doc_id,
                        'chunk_id': i,
                        'filename': filename,
                        'text': chunk
                    })
                
                # Update embeddings array
                if self.embeddings is None:
                    self.embeddings = chunk_embeddings
                else:
                    self.embeddings = np.vstack([self.embeddings, chunk_embeddings])
                
                logger.info(f"Added {len(chunks)} chunks from {filename} to search index")
                
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            raise
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for relevant document chunks
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant chunks with similarity scores
        """
        if self.embeddings is None or len(self.document_chunks) == 0:
            logger.info("No documents in search index")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                similarity_score = similarities[idx]
                # Only include results with reasonable similarity (> 0.1)
                if similarity_score > 0.1:
                    results.append({
                        'text': self.document_chunks[idx],
                        'similarity': float(similarity_score),
                        'metadata': self.chunk_metadata[idx]
                    })
            
            logger.info(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get statistics about the search index"""
        return {
            'total_chunks': len(self.document_chunks),
            'total_documents': len(set(meta['doc_id'] for meta in self.chunk_metadata)),
            'model_name': self.model_name
        }
    
    def clear_index(self):
        """Clear the search index"""
        self.document_chunks = []
        self.embeddings = None
        self.chunk_metadata = []
        logger.info("Search index cleared")

# Global search engine instance
search_engine = DocumentSearchEngine()

def load_documents_into_search_engine(documents_db: Dict):
    """
    Load all documents from the database into the search engine
    
    Args:
        documents_db: Dictionary of document data
    """
    try:
        search_engine.clear_index()
        
        for doc_id, doc_info in documents_db.items():
            search_engine.add_document(
                doc_id=doc_id,
                text=doc_info.get('text_content', ''),
                filename=doc_info.get('original_filename', '')
            )
        
        logger.info(f"Loaded {len(documents_db)} documents into search engine")
        
    except Exception as e:
        logger.error(f"Error loading documents into search engine: {e}")
        raise