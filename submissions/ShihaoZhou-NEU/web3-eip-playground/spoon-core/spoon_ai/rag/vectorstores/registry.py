import os
from typing import Optional, Dict

from .base import VectorStore, InMemoryVectorStore

# Global cache to reuse instances within the same process
_STORE_CACHE: Dict[str, VectorStore] = {}


def get_vector_store(backend: Optional[str] = None) -> VectorStore:
    """Return a vector store by backend name.

    Backends:
    - faiss: local/offline (mapped to in-memory cosine store)
    - pinecone: cloud Pinecone (requires PINECONE_API_KEY)
    - qdrant: local/cloud Qdrant (requires qdrant-client, default http://localhost:6333)
    - chroma: local Chroma (requires chromadb)
    """
    name = (backend or os.getenv("RAG_BACKEND", "faiss")).lower()
    
    if name in _STORE_CACHE:
        return _STORE_CACHE[name]

    store: VectorStore

    if name == "pinecone":
        from .pinecone_store import PineconeVectorStore
        store = PineconeVectorStore()
    elif name == "qdrant":
        from .qdrant_store import QdrantVectorStore
        store = QdrantVectorStore()
    elif name == "chroma":
        from .chroma_store import ChromaVectorStore
        store = ChromaVectorStore()
    elif name == "faiss":
        try:
            import faiss  # noqa: F401
            from .faiss_store import FaissVectorStore
            store = FaissVectorStore()
        except Exception as e:
            print(f"Warning: FAISS not available ({e}), falling back to InMemoryVectorStore")
            # fallback to in-memory if faiss not installed
            store = InMemoryVectorStore()
    else:
        # Default: FAISS/local → InMemory
        store = InMemoryVectorStore()

    _STORE_CACHE[name] = store
    return store
