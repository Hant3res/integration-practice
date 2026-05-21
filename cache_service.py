import redis
import json
import time
from functools import wraps
from typing import Optional, Any

class RedisCacheService:
    """Сервис кэширования на Redis (аналог IDistributedCache)"""
    
    def __init__(self, host='localhost', port=6379, db=0, default_ttl=300):
        try:
            self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.client.ping()
            self.default_ttl = default_ttl
            self.stats = {"hits": 0, "misses": 0}
            print("[OK] Redis cache connected")
        except Exception as e:
            print(f"[WARN] Redis connection failed: {e}")
            raise
    
    def get(self, key: str) -> Optional[str]:
        """Получить значение из кэша"""
        start = time.time()
        value = self.client.get(key)
        elapsed = (time.time() - start) * 1000
        
        if value:
            self.stats["hits"] += 1
            print(f"[HIT] {key} ({elapsed:.2f}ms)")
            return value
        else:
            self.stats["misses"] += 1
            print(f"[MISS] {key} ({elapsed:.2f}ms)")
            return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Сохранить значение в кэш"""
        ttl = ttl or self.default_ttl
        self.client.setex(key, ttl, value)
        print(f"[SET] {key} (TTL={ttl}s)")
    
    def get_json(self, key: str) -> Optional[dict]:
        """Получить и десериализовать JSON"""
        data = self.get(key)
        return json.loads(data) if data else None
    
    def set_json(self, key: str, data: Any, ttl: Optional[int] = None):
        """Сериализовать и сохранить JSON"""
        self.set(key, json.dumps(data, ensure_ascii=False), ttl)
    
    def get_stats(self) -> dict:
        """Получить статистику кэша"""
        return self.stats
    
    def clear(self, pattern: str = "*"):
        """Очистить кэш по паттерну"""
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)
            print(f"[CLEAR] Deleted {len(keys)} keys")

class MemoryCacheService:
    """In-memory cache (fallback)"""
    def __init__(self, default_ttl=300):
        self.cache = {}
        self.default_ttl = default_ttl
        self.stats = {"hits": 0, "misses": 0}
        print("[OK] Using in-memory cache (Redis not available)")
    
    def get(self, key: str):
        data = self.cache.get(key)
        if data:
            expiry, value = data
            if time.time() < expiry:
                self.stats["hits"] += 1
                return value
            else:
                del self.cache[key]
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None):
        ttl = ttl or self.default_ttl
        self.cache[key] = (time.time() + ttl, value)
    
    def get_json(self, key: str):
        data = self.get(key)
        return json.loads(data) if data else None
    
    def set_json(self, key: str, data: Any, ttl: Optional[int] = None):
        self.set(key, json.dumps(data, ensure_ascii=False), ttl)
    
    def get_stats(self):
        return self.stats
    
    def clear(self, pattern: str = "*"):
        count = len(self.cache)
        self.cache.clear()
        print(f"[CLEAR] Deleted {count} keys")

# Выбор сервиса кэширования
cache = None
try:
    cache = RedisCacheService()
except:
    cache = MemoryCacheService()