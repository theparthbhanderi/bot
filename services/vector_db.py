"""
Vector Database Service for RAG (Retrieval-Augmented Generation)
Uses sentence-transformers and FAISS for semantic search.
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional

# Try to import optional dependencies
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# Storage path for vector database
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), 'vector_db.pkl')


class VectorStore:
    """
    Vector store for semantic search using FAISS and sentence-transformers.
    Provides RAG capabilities for the bot.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the vector store.
        
        Args:
            model_name: Name of the sentence-transformer model
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.metadata = []
        
        # Try to load existing index
        self._load_index()
        
        # Initialize model if available
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
                print(f"✅ Sentence transformer loaded: {model_name}")
            except Exception as e:
                print(f"⚠️ Could not load sentence transformer: {e}")
                self.model = None
        else:
            print("⚠️ sentence-transformers not installed. RAG features disabled.")
            self.dimension = 384  # Default for all-MiniLM-L6-v2
    
    def _load_index(self):
        """Load existing vector index from disk."""
        if os.path.exists(VECTOR_DB_PATH):
            try:
                with open(VECTOR_DB_PATH, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.metadata = data.get('metadata', [])
                    
                    # Reload FAISS index if FAISS is available
                    if FAISS_AVAILABLE and 'embeddings' in data:
                        embeddings = np.array(data['embeddings']).astype('float32')
                        if embeddings.size > 0:
                            self.index = faiss.IndexFlatL2(embeddings.shape[1])
                            self.index.add(embeddings)
                    
                    print(f"✅ Loaded {len(self.documents)} documents from index")
            except Exception as e:
                print(f"⚠️ Could not load vector index: {e}")
    
    def _save_index(self):
        """Save vector index to disk."""
        try:
            # Reconstruct embeddings from index if possible
            embeddings = None
            if self.index is not None and self.index.ntotal > 0:
                # Flat index allows reconstructing
                embeddings = faiss.rev_swig_ptr(self.index.get_xb(), self.index.ntotal * self.index.d)
                embeddings = embeddings.reshape(self.index.ntotal, self.index.d)

            data = {
                'documents': self.documents,
                'metadata': self.metadata,
                'model_name': self.model_name,
                'embeddings': embeddings
            }
            with open(VECTOR_DB_PATH, 'wb') as f:
                pickle.dump(data, f)
            print(f"✅ Saved {len(self.documents)} documents to index")
        except Exception as e:
            print(f"⚠️ Could not save vector index: {e}")
    
    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]] = None):
        """
        Add documents to the vector store.
        
        Args:
            texts: List of text documents
            metadata: Optional metadata for each document
        """
        if not self.model:
            print("⚠️ Model not loaded. Cannot add documents.")
            return
        
        if not texts:
            return
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Initialize FAISS index if needed
        if self.index is None:
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
        
        # Add to index
        self.index.add(embeddings)
        
        # Store documents and metadata
        self.documents.extend(texts)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(texts))
        
        # Save to disk
        self._save_index()
        print(f"✅ Added {len(texts)} documents to vector store")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of matching documents with scores
        """
        if not self.model or self.index is None or not self.documents:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            
            # Search index
            distances, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
            
            # Format results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.documents):
                    results.append({
                        'text': self.documents[idx],
                        'metadata': self.metadata[idx] if idx < len(self.metadata) else {},
                        'score': float(distance),
                        'rank': i + 1
                    })
            
            return results
        except Exception as e:
            print(f"⚠️ Search error: {e}")
            return []
    
    def get_context(self, query: str, max_chars: int = 2000) -> str:
        """
        Get context from relevant documents for RAG.
        
        Args:
            query: Search query
            max_chars: Maximum characters to return
        
        Returns:
            Combined context string
        """
        results = self.search(query, top_k=3)
        
        if not results:
            return ""
        
        context_parts = []
        for result in results:
            context_parts.append(result['text'])
        
        context = "\n\n".join(context_parts)
        
        # Truncate if too long
        if len(context) > max_chars:
            context = context[:max_chars] + "..."
        
        return context
    
    def clear(self):
        """Clear all documents from the vector store."""
        self.documents = []
        self.metadata = []
        self.index = None
        self._save_index()
        print("✅ Vector store cleared")


# Global vector store instance
vector_store = None

def get_vector_store() -> VectorStore:
    """
    Get the global vector store instance.
    
    Returns:
        VectorStore instance
    """
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store


def add_to_knowledge(user_id: int, title: str, content: str):
    """
    Add content to a user's knowledge base.
    
    Args:
        user_id: User ID
        title: Content title
        content: Content text
    """
    store = get_vector_store()
    store.add_documents(
        texts=[content],
        metadata=[{'user_id': user_id, 'title': title}]
    )


def search_knowledge(user_id: int, query: str) -> str:
    """
    Search user's knowledge base.
    
    Args:
        user_id: User ID
        query: Search query
    
    Returns:
        Relevant context string
    """
    store = get_vector_store()
    results = store.search(query, top_k=3)
    
    # Filter by user_id
    user_results = [r for r in results if r['metadata'].get('user_id') == user_id]
    
    if not user_results:
        return ""
    
    context_parts = [r['text'] for r in user_results]
    return "\n\n".join(context_parts)
