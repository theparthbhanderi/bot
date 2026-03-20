"""
Optimization: Cache Service for KINGPARTH Bot
Handles LLM, Research, and Agent result caching with TTL.
Uses Redis if available, fallback to in-memory Dict.
"""

import hashlib
import json
import time
from typing import Optional, Any


class CacheService:
    """
    Fast Multi-Layer Caching System.
    """
    def __init__(self):
        self._memory_cache = {}
        self._redis = None
        
        # Try to initialize Redis if possible
        try:
            import redis
            self._redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None

    def _generate_key(self, prefix: str, query: str) -> str:
        """
        Create a unique hash for a query to use as cache key.
        """
        hash_obj = hashlib.mdsafe_hex(query.lower().strip()) if hasattr(hashlib, 'mdsafe_hex') else hashlib.md5(query.lower().strip().encode()).hexdigest()
        return f"{prefix}:{hash_obj}"

    def get(self, prefix: str, query: str) -> Optional[Any]:
        """
        Get cached result.
        """
        key = self._generate_key(prefix, query)
        
        # Try Redis
        if self._redis:
            try:
                val = self._redis.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass
        
        # Try Memory fallback
        if key in self._memory_cache:
            item = self._memory_cache[key]
            if item['expiry'] > time.time():
                return item['data']
            else:
                del self._memory_cache[key]
        
        return None

    def set(self, prefix: str, query: str, data: Any, ttl_seconds: int = 600):
        """
        Set cache result with TTL.
        """
        key = self._generate_key(prefix, query)
        
        # Set in Redis
        if self._redis:
            try:
                self._redis.setex(key, ttl_seconds, json.dumps(data))
            except Exception:
                pass
        
        # Set in Memory
        self._memory_cache[key] = {
            'data': data,
            'expiry': time.time() + ttl_seconds
        }

    def clear(self):
        """Clear the cache."""
        self._memory_cache = {}
        if self._redis:
            try:
                self._redis.flushdb()
            except Exception:
                pass


# Singleton instance
cache = CacheService()
