from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from .base import VectorStore


class FaissVectorStore(VectorStore):
    """FAISS-backed local vector store (cosine via inner product + L2 norm)."""

    def __init__(self, *, persist_dir: Optional[str] = None) -> None:
        import os
        self.persist_dir = persist_dir or os.getenv("RAG_FAISS_DIR", os.path.join(os.getenv("RAG_DIR", ".rag_store"), "faiss"))
        self._collections: Dict[str, Dict] = {}
        self._load()

    def _get_index_path(self, collection: str) -> str:
        return os.path.join(self.persist_dir, f"{collection}.index")

    def _get_meta_path(self, collection: str) -> str:
        return os.path.join(self.persist_dir, f"{collection}.pkl")

    def _load(self):
        import os
        import pickle
        import faiss # type: ignore
        
        if not os.path.exists(self.persist_dir):
            return

        for fname in os.listdir(self.persist_dir):
            if fname.endswith(".index"):
                collection = fname[:-6]
                index_path = os.path.join(self.persist_dir, fname)
                meta_path = self._get_meta_path(collection)
                
                if not os.path.exists(meta_path):
                    continue
                    
                try:
                    index = faiss.read_index(index_path)
                    with open(meta_path, "rb") as f:
                        meta_data = pickle.load(f)
                    
                    self._collections[collection] = {
                        "index": index,
                        "ids": meta_data["ids"],
                        "metas": meta_data["metas"],
                        "dim": meta_data["dim"],
                    }
                except Exception as e:
                    print(f"Error loading FAISS collection '{collection}': {e}")
                    # Ignore corrupted files
                    pass

    def _save(self, collection: str):
        import os
        import pickle
        import faiss # type: ignore
        
        os.makedirs(self.persist_dir, exist_ok=True)
        col = self._collections.get(collection)
        if not col:
            return

        index_path = self._get_index_path(collection)
        meta_path = self._get_meta_path(collection)
        
        faiss.write_index(col["index"], index_path)
        with open(meta_path, "wb") as f:
            pickle.dump({
                "ids": col["ids"],
                "metas": col["metas"],
                "dim": col["dim"]
            }, f)

    def _get_or_create(self, collection: str, dim: Optional[int] = None):
        import faiss  # type: ignore

        col = self._collections.get(collection)
        if col is None:
            if dim is None or dim <= 0:
                raise RuntimeError("FAISS collection not initialized and no dim provided")
            index = faiss.IndexFlatIP(dim)
            col = {
                "index": index,
                "ids": [],  # type: List[str]
                "metas": {},  # type: Dict[str, Dict]
                "dim": dim,
            }
            self._collections[collection] = col
        return col

    def _normalize(self, vecs: List[List[float]]):
        import numpy as np

        arr = np.asarray(vecs, dtype="float32")
        norms = (arr**2).sum(axis=1) ** 0.5
        norms[norms == 0] = 1.0
        arr = arr / norms[:, None]
        return arr

    def add(self, *, collection: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict]) -> None:
        import numpy as np

        if not embeddings:
            return
        dim = len(embeddings[0])
        col = self._get_or_create(collection, dim)
        if col["dim"] != dim:
            raise RuntimeError(f"FAISS dim mismatch: existing {col['dim']} vs new {dim}")

        arr = self._normalize(embeddings)
        col["index"].add(arr)
        col["ids"].extend(ids)
        for id_, md in zip(ids, metadatas):
            col["metas"][id_] = md
        
        # Persist changes
        self._save(collection)

    def query(self, *, collection: str, query_embeddings: List[List[float]], top_k: int = 5, filter: Optional[Dict] = None) -> List[List[Tuple[str, float, Dict]]]:
        import numpy as np

        # Ensure loaded or created if not in memory (but _load handles init)
        col = self._collections.get(collection)
        if not col:
            # If not in memory and not loaded, it doesn't exist
            return [[] for _ in query_embeddings]

        if len(col["ids"]) == 0:
            return [[] for _ in query_embeddings]

        q = self._normalize(query_embeddings)
        scores, idxs = col["index"].search(q, min(top_k, len(col["ids"])))
        results: List[List[Tuple[str, float, Dict]]] = []
        for row_scores, row_idxs in zip(scores, idxs):
            triples: List[Tuple[str, float, Dict]] = []
            for s, i in zip(row_scores, row_idxs):
                if i < 0:
                    continue
                id_ = col["ids"][int(i)]
                md = col["metas"].get(id_, {})
                # simple metadata exact filter if provided
                if filter:
                    ok = True
                    for k, v in filter.items():
                        if md.get(k) != v:
                            ok = False
                            break
                    if not ok:
                        continue
                triples.append((id_, float(s), md))
            results.append(triples)
        return results

    def delete_collection(self, collection: str) -> None:
        import os
        self._collections.pop(collection, None)
        # Also remove from disk
        try:
            if os.path.exists(self._get_index_path(collection)):
                os.remove(self._get_index_path(collection))
            if os.path.exists(self._get_meta_path(collection)):
                os.remove(self._get_meta_path(collection))
        except Exception:
            pass

