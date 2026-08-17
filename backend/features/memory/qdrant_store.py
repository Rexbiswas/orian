import json
import logging
import math
import time
import uuid
from typing import List, Dict, Any, Optional
from config import settings

logger = logging.getLogger("orian.qdrant_store")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    _qdrant_available = True
except ImportError:
    _qdrant_available = False

def _simple_text_vector(text: str, dim: int = 128) -> List[float]:
    """Generates a normalized pseudo-embedding vector for text similarity matching."""
    words = text.lower().split()
    vec = [0.0] * dim
    for w in words:
        h = hash(w)
        idx = abs(h) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    return sum(a * b for a, b in zip(vec1, vec2)) if len(vec1) == len(vec2) else 0.0

class InMemQdrantFallback:
    def __init__(self):
        self.points: Dict[str, Dict[str, Any]] = {}

    def upsert_point(self, point_id: str, vector: List[float], payload: Dict[str, Any]):
        self.points[point_id] = {
            "id": point_id,
            "vector": vector,
            "payload": payload
        }

    def search(self, query_vector: List[float], limit: int = 5, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        results = []
        for p_id, p in self.points.items():
            payload = p["payload"]
            
            # Apply metadata filtering
            match = True
            if filter_metadata:
                for k, v in filter_metadata.items():
                    if v is not None and payload.get(k) != v:
                        match = False
                        break
            if not match:
                continue

            sim = sum(a * b for a, b in zip(query_vector, p["vector"]))
            results.append({"id": p_id, "score": sim, "payload": payload})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

class QdrantSemanticMemory:
    def __init__(self):
        self.client = None
        self.is_real_qdrant = False
        self.collection_name = settings.QDRANT_COLLECTION

        if _qdrant_available:
            try:
                qc = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, api_key=settings.QDRANT_API_KEY, timeout=1.0)
                # Check collection
                collections = [c.name for c in qc.get_collections().collections]
                if self.collection_name not in collections:
                    qc.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=128, distance=Distance.COSINE)
                    )
                self.client = qc
                self.is_real_qdrant = True
                logger.info(f"Connected to Qdrant Semantic Memory at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant server ({e}). Operating in Local Vector Store fallback mode.")
                self.client = InMemQdrantFallback()
        else:
            logger.info("qdrant-client package not available. Operating in Local Vector Store fallback mode.")
            self.client = InMemQdrantFallback()

    def store_memory(
        self,
        content: str,
        memory_type: str,  # e.g., 'coding_experience', 'project_knowledge', 'user_preference', 'conversation_summary'
        importance: float = 1.0,
        user_id: str = "default_user",
        project_id: str = "default_project",
        category: str = "general",
        source: str = "user_input",
        metadata: dict = None
    ) -> str:
        mem_id = str(uuid.uuid4())
        now = time.time()
        vector = _simple_text_vector(content)
        
        payload = {
            "memory_id": mem_id,
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "user_id": user_id,
            "project_id": project_id,
            "category": category,
            "source": source,
            "timestamp": now,
            **(metadata or {})
        }

        if self.is_real_qdrant:
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[PointStruct(id=mem_id, vector=vector, payload=payload)]
                )
            except Exception as e:
                logger.error(f"Failed to upsert to Qdrant: {e}")
        else:
            self.client.upsert_point(mem_id, vector, payload)

        return mem_id

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        query_vector = _simple_text_vector(query)
        filter_meta = {}
        if user_id:
            filter_meta["user_id"] = user_id
        if project_id:
            filter_meta["project_id"] = project_id
        if category:
            filter_meta["category"] = category
        if memory_type:
            filter_meta["memory_type"] = memory_type

        if self.is_real_qdrant:
            try:
                conditions = []
                for k, v in filter_meta.items():
                    conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
                q_filter = Filter(must=conditions) if conditions else None

                hits = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=q_filter,
                    limit=limit
                )
                return [{"id": h.id, "score": h.score, "payload": h.payload} for h in hits if h.payload.get("importance", 1.0) >= min_importance]
            except Exception as e:
                logger.error(f"Qdrant search error ({e}). Using local search.")
                return self.client.search(query_vector, limit=limit, filter_metadata=filter_meta)
        else:
            return self.client.search(query_vector, limit=limit, filter_metadata=filter_meta)

qdrant_store = QdrantSemanticMemory()
