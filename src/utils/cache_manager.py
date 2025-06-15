"""
High-Performance Cache Manager for Financial Data
Optimized for financial data patterns with intelligent TTL and hit rate tracking
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, List
import hashlib
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    timestamp: datetime
    ttl: int  # seconds
    access_count: int = 0
    
    def is_expired(self) -> bool:
        return datetime.now() > (self.timestamp + timedelta(seconds=self.ttl))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'ttl': self.ttl,
            'access_count': self.access_count
        }

@dataclass 
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'size': self.size,
            'hit_rate': round(self.hit_rate, 3)
        }

class CacheManager:
    """
    Intelligent cache manager optimized for financial data
    Features:
    - TTL-based expiration
    - LRU eviction policy  
    - Hit rate tracking
    - Financial data-aware TTL suggestions
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = CacheStats()
        self._lock = asyncio.Lock()
        
        # Financial data specific TTL recommendations
        self.ttl_recommendations = {
            'stock_data': 300,      # 5 minutes - very volatile
            'economic_indicators': 86400,  # 24 hours - daily updates
            'market_context': 1800,  # 30 minutes - moderately volatile
            'company_fundamentals': 14400,  # 4 hours - less frequent updates
            'sector_performance': 900,  # 15 minutes - moderately volatile
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get data from cache with automatic expiration handling"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self.stats.misses += 1
                logger.debug(f"Cache miss for key: {key}")
                return None
            
            if entry.is_expired():
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self.stats.misses += 1
                self.stats.evictions += 1
                logger.debug(f"Cache expired for key: {key}")
                return None
            
            # Update access tracking for LRU
            entry.access_count += 1
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self.stats.hits += 1
            logger.debug(f"Cache hit for key: {key}")
            return entry.data
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set data in cache with intelligent TTL"""
        if ttl is None:
            ttl = self._get_smart_ttl(key)
        
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()
            
            entry = CacheEntry(
                data=data,
                timestamp=datetime.now(),
                ttl=ttl
            )
            
            self._cache[key] = entry
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self.stats.size = len(self._cache)
            logger.debug(f"Cache set for key: {key}, TTL: {ttl}s")
    
    async def delete(self, key: str) -> bool:
        """Delete specific cache entry"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self.stats.size = len(self._cache)
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self.stats = CacheStats()
            logger.info("Cache cleared")
    
    async def cleanup_expired(self) -> int:
        """Remove all expired entries and return count"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
            
            self.stats.evictions += len(expired_keys)
            self.stats.size = len(self._cache)
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_hit_rate(self) -> float:
        """Get current cache hit rate"""
        return self.stats.hit_rate
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return self.stats.to_dict()
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        async with self._lock:
            active_entries = {}
            expired_count = 0
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_count += 1
                else:
                    active_entries[key] = {
                        'access_count': entry.access_count,
                        'age_seconds': (datetime.now() - entry.timestamp).total_seconds(),
                        'ttl_remaining': entry.ttl - (datetime.now() - entry.timestamp).total_seconds()
                    }
            
            return {
                'stats': self.stats.to_dict(),
                'active_entries': len(active_entries),
                'expired_entries': expired_count,
                'max_size': self.max_size,
                'memory_usage': len(str(self._cache)),  # Rough estimate
                'top_accessed': self._get_top_accessed_keys(5)
            }
    
    def _get_smart_ttl(self, key: str) -> int:
        """Determine optimal TTL based on data type"""
        for data_type, ttl in self.ttl_recommendations.items():
            if data_type in key.lower():
                return ttl
        return self.default_ttl
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self._access_order:
            return
        
        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]
            self.stats.evictions += 1
            logger.debug(f"Evicted LRU entry: {lru_key}")
    
    def _get_top_accessed_keys(self, limit: int) -> List[Dict[str, Any]]:
        """Get most frequently accessed cache keys"""
        entries = [
            {'key': key, 'access_count': entry.access_count}
            for key, entry in self._cache.items()
        ]
        entries.sort(key=lambda x: x['access_count'], reverse=True)
        return entries[:limit]
    
    # Context manager support for cleanup
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup_expired()


# Global cache instance for module-level usage
_global_cache = None

def get_cache() -> CacheManager:
    """Get global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache

# Utility functions for common caching patterns
def cache_key_for_stock(symbol: str, data_type: str) -> str:
    """Generate standardized cache key for stock data"""
    return f"stock_{data_type}_{symbol.upper()}_{datetime.now().strftime('%Y%m%d_%H')}"

def cache_key_for_economic() -> str:
    """Generate cache key for economic indicators"""
    return f"economic_indicators_{datetime.now().strftime('%Y%m%d')}"

def cache_key_for_market(symbol: str) -> str:
    """Generate cache key for market context"""
    return f"market_context_{symbol.upper()}_{datetime.now().strftime('%Y%m%d_%H')}"

async def cached_call(cache_manager: CacheManager, key: str, 
                     fetch_func, ttl: Optional[int] = None) -> Any:
    """
    Utility function for cache-first data fetching pattern
    """
    # Try cache first
    cached_data = await cache_manager.get(key)
    if cached_data is not None:
        return cached_data
    
    # Fetch fresh data
    fresh_data = await fetch_func()
    if fresh_data is not None:
        await cache_manager.set(key, fresh_data, ttl)
    
    return fresh_data
