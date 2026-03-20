"""
Ultra-Optimization: Cache Service for KINGPARTH Bot
ULTRA-FAST Multi-Layer Caching System.
Layer 1: In-memory LRU Cache (Fastest)
Layer 2: Redis Cache (Scalable)
Layer 3: Semantic Cache (Embeddings)
"""

import hashlib
import json
import time
import os
from typing import Optional, Any
from collections import OrderedDict


class CacheService:
    """
    ULTRA-FAST Multi-Layer Caching System.
    Layer 1: In-memory LRU Cache (Fastest)
    Layer 2: Redis Cache (Scalable)
    Layer 3: Semantic Cache (Embeddings)
    """
    def __init__(self, max_memory_items: int = 1000):
        self._memory_cache = OrderedDict()
        self._max_memory_items = max_memory_items
        self._redis = None
        self._semantic_store = None
        
        # Optimize Redis connection
        try:
            import redis
            # Use connection pool for high performance
            pool = redis.ConnectionPool(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True
            )
            self._redis = redis.Redis(connection_pool=pool)
            self._redis.ping()
        except Exception:
            self._redis = None

    def _init_semantic_store(self):
        """Lazy initialization of semantic store."""
        if self._semantic_store is None:
            try:
                from services.vector_db import VectorStore
                # Using a separate path for semantic cache to avoid mixing with RAG knowledge
                self._semantic_store = VectorStore(model_name='all-MiniLM-L6-v2')
                # Adjusting save path for semantic cache specifically
                self._semantic_store_path = os.path.join(os.path.dirname(__file__), 'semantic_cache.pkl')
                # Override load/save for semantic cache specifically
                self._semantic_store.VECTOR_DB_PATH = self._semantic_store_path
                self._semantic_store._load_index()
            except Exception as e:
                print(f"Semantic Cache Init Error: {e}")

    def _generate_key(self, prefix: str, query: str) -> str:
        """
        Fast BLAKE2b hashing for query keys.
        """
        # BLAKE2 is faster than MD5/SHA on modern CPUs
        hash_obj = hashlib.blake2b(query.lower().strip().encode(), digest_size=16)
        return f"{prefix}:{hash_obj.hexdigest()}"

    def get_semantic(self, prefix: str, query: str, threshold: float = 0.15) -> Optional[Any]:
        """
        Search for semantically similar queries.
        """
        try:
            self._init_semantic_store()
            if not self._semantic_store: return None
            results = self._semantic_store.search(query, top_k=1)
            if results and results[0]['score'] < threshold:
                # Return the data from normal cache using the original query
                original_query = results[0]['text']
                return self.get(prefix, original_query)
        except Exception:
            pass
        return None

    def get(self, prefix: str, query: str) -> Optional[Any]:
        """
        Multi-layer retrieval.
        """
        key = self._generate_key(prefix, query)
        now = time.time()
        
        # 1. L1 Memory Cache (Check & Move to front)
        if key in self._memory_cache:
            item = self._memory_cache[key]
            if item['expiry'] > now:
                # Move to end (most recently used)
                self._memory_cache.move_to_end(key)
                return item['data']
            else:
                del self._memory_cache[key]
        
        # 2. L2 Redis Cache
        if self._redis:
            try:
                val = self._redis.get(key)
                if val:
                    data = json.loads(val)
                    # Backfill L1 for future fast access
                    self.set_memory(key, data, ttl_seconds=300) # Short L1 TTL
                    return data
            except Exception:
                pass
        
        return None

    def set_memory(self, key: str, data: Any, ttl_seconds: int):
        """Internal helper for L1 cache."""
        if len(self._memory_cache) >= self._max_memory_items:
            # Pop least recently used (first item)
            self._memory_cache.popitem(last=False)
        
        self._memory_cache[key] = {
            'data': data,
            'expiry': time.time() + ttl_seconds
        }

    def set(self, prefix: str, query: str, data: Any, ttl_seconds: int = 600, use_semantic: bool = False):
        """
        Set cache result in all layers.
        """
        key = self._generate_key(prefix, query)
        
        # Set L1
        self.set_memory(key, data, ttl_seconds)
        
        # Set L2
        if self._redis:
            try:
                # Use pipelining or async for even more performance if needed
                self._redis.setex(key, ttl_seconds, json.dumps(data))
            except Exception:
                pass

        # Optional Semantic Indexing
        if use_semantic:
            try:
                self._init_semantic_store()
                if self._semantic_store:
                    # Check if query already exists to avoid duplication
                    existing = self._semantic_store.search(query, top_k=1)
                    if not (existing and existing[0]['score'] < 0.05):
                        self._semantic_store.add_documents([query])
            except Exception:
                pass

    def clear(self):
        """Clear all cache layers."""
        self._memory_cache.clear()
        if self._redis:
            try:
                self._redis.flushdb()
            except Exception:
                pass


# Singleton instance
cache = CacheService()
