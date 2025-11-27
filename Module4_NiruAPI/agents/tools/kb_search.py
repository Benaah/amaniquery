"""
Knowledge Base Search Tool - Robust, Scalable, Concurrent Search

Features:
- Async/await support for concurrent searches
- Connection pooling and semaphore-based concurrency control
- Circuit breaker pattern for fault tolerance
- Retry logic with exponential backoff
- Request coalescing for duplicate queries
- Response caching with TTL
- Batch search support
- OpenTelemetry instrumentation
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Dict, Any, Optional, List, Callable, Tuple
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Module3_NiruDB.vector_store import VectorStore


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class KBSearchConfig:
    """Configuration for KB search tool."""
    # Concurrency settings
    max_concurrent_searches: int = 10
    max_concurrent_writes: int = 3
    
    # Retry settings
    max_retries: int = 3
    base_retry_delay: float = 0.5
    max_retry_delay: float = 10.0
    
    # Circuit breaker settings
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 30.0
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: float = 300.0  # 5 minutes
    cache_max_size: int = 1000
    
    # Coalescing settings
    coalesce_window_ms: float = 50.0
    
    # Timeout settings
    search_timeout: float = 30.0
    write_timeout: float = 60.0
    
    # Default namespaces
    default_namespaces: List[str] = field(default_factory=lambda: [
        "kenya_law", "kenya_news", "kenya_parliament", "historical", "global_trends"
    ])


# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.
    
    Prevents cascading failures by stopping requests when
    the downstream service is failing.
    """
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    async def can_execute(self) -> bool:
        """Check if request can proceed."""
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering half-open state")
                    return True
                return False
            
            # HALF_OPEN - allow one request to test
            return True
    
    async def record_success(self):
        """Record a successful operation."""
        async with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                logger.info("Circuit breaker closed - service recovered")
    
    async def record_failure(self):
        """Record a failed operation."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker opened after {self._failure_count} failures")
            elif self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning("Circuit breaker re-opened - recovery failed")


# =============================================================================
# CACHE
# =============================================================================

@dataclass
class CacheEntry:
    """Single cache entry with TTL."""
    value: Any
    expires_at: float
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class LRUCache:
    """Thread-safe LRU cache with TTL."""
    
    def __init__(self, max_size: int = 1000, ttl: float = 300.0):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._access_order.remove(key)
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            self._hits += 1
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in cache."""
        async with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
            
            expires_at = time.time() + (ttl or self.ttl)
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
            
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
    
    async def invalidate(self, key: str):
        """Remove key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_order.remove(key)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate
        }


# =============================================================================
# REQUEST COALESCING
# =============================================================================

class RequestCoalescer:
    """
    Coalesces duplicate concurrent requests.
    
    When multiple identical requests arrive within a short window,
    only one actual search is performed and the result is shared.
    """
    
    def __init__(self, window_ms: float = 50.0):
        self.window_ms = window_ms
        self._pending: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
    
    def _make_key(self, query: str, namespaces: List[str], top_k: int) -> str:
        """Create unique key for request."""
        ns_str = ",".join(sorted(namespaces))
        raw = f"{query}:{ns_str}:{top_k}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    async def execute(
        self,
        key: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with request coalescing.
        
        If an identical request is already in flight, wait for its result.
        """
        async with self._lock:
            if key in self._pending:
                # Request already in flight, wait for it
                logger.debug(f"Coalescing request: {key[:8]}...")
                return await self._pending[key]
            
            # Create future for this request
            future = asyncio.get_event_loop().create_future()
            self._pending[key] = future
        
        try:
            # Execute the actual function
            result = await func(*args, **kwargs)
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            async with self._lock:
                self._pending.pop(key, None)


# =============================================================================
# MAIN TOOL CLASS
# =============================================================================

class KnowledgeBaseSearchTool:
    """
    Robust, scalable knowledge base search tool.
    
    Features:
    - Async/await for concurrent operations
    - Connection pooling via semaphores
    - Circuit breaker for fault tolerance
    - Retry with exponential backoff
    - Request coalescing for duplicate queries
    - LRU cache with TTL
    - Batch search support
    - Metrics and observability
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        config: Optional[KBSearchConfig] = None
    ):
        """
        Initialize KB search tool.
        
        Args:
            vector_store: Vector store instance (creates new if None)
            config: Configuration options
        """
        self.vector_store = vector_store or VectorStore()
        self.config = config or KBSearchConfig()
        
        # Concurrency controls
        self._search_semaphore = asyncio.Semaphore(self.config.max_concurrent_searches)
        self._write_semaphore = asyncio.Semaphore(self.config.max_concurrent_writes)
        
        # Circuit breaker
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_failure_threshold,
            recovery_timeout=self.config.circuit_recovery_timeout
        )
        
        # Cache
        self._cache = LRUCache(
            max_size=self.config.cache_max_size,
            ttl=self.config.cache_ttl_seconds
        ) if self.config.cache_enabled else None
        
        # Request coalescer
        self._coalescer = RequestCoalescer(
            window_ms=self.config.coalesce_window_ms
        )
        
        # Metrics
        self._metrics = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "total_writes": 0,
            "successful_writes": 0,
            "failed_writes": 0,
            "circuit_breaker_rejections": 0,
            "retries": 0
        }
    
    # -------------------------------------------------------------------------
    # SYNC INTERFACE (backwards compatible)
    # -------------------------------------------------------------------------
    
    def execute(
        self,
        query: str,
        top_k: int = 5,
        add_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Synchronous search (backwards compatible).
        
        Args:
            query: Search query
            top_k: Number of results to return
            add_content: Optional content to add to KB
            metadata: Optional metadata for added content
            namespace: Optional list of namespaces to search
            
        Returns:
            Search results and add operation result
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.aexecute(query, top_k, add_content, metadata, namespace)
                    )
                    return future.result(timeout=self.config.search_timeout + 10)
            else:
                return loop.run_until_complete(
                    self.aexecute(query, top_k, add_content, metadata, namespace)
                )
        except Exception as e:
            logger.error(f"Sync execute error: {e}")
            return {
                'query': query,
                'search_results': [],
                'error': str(e)
            }
    
    # -------------------------------------------------------------------------
    # ASYNC INTERFACE
    # -------------------------------------------------------------------------
    
    async def aexecute(
        self,
        query: str,
        top_k: int = 5,
        add_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Async search with all robustness features.
        
        Args:
            query: Search query
            top_k: Number of results to return
            add_content: Optional content to add to KB
            metadata: Optional metadata for added content
            namespace: Optional list of namespaces to search
            
        Returns:
            Search results and add operation result
        """
        result = {
            'query': query,
            'search_results': [],
            'add_result': None,
            'metadata': {
                'cached': False,
                'coalesced': False,
                'retries': 0,
                'latency_ms': 0
            }
        }
        
        start_time = time.time()
        search_namespace = namespace or self.config.default_namespaces
        
        try:
            # Search knowledge base
            search_results = await self._search_with_resilience(
                query=query,
                top_k=top_k,
                namespaces=search_namespace
            )
            result['search_results'] = search_results
            
            # Add content if provided
            if add_content:
                add_result = await self._add_with_resilience(
                    content=add_content,
                    metadata=metadata or {}
                )
                result['add_result'] = add_result
            
            result['metadata']['latency_ms'] = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            logger.error(f"KB execute error: {e}")
            result['error'] = str(e)
            result['metadata']['latency_ms'] = (time.time() - start_time) * 1000
            return result
    
    async def _search_with_resilience(
        self,
        query: str,
        top_k: int,
        namespaces: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search with circuit breaker, caching, coalescing, and retries.
        """
        self._metrics["total_searches"] += 1
        
        # Check circuit breaker
        if not await self._circuit_breaker.can_execute():
            self._metrics["circuit_breaker_rejections"] += 1
            raise Exception("Circuit breaker is open - service unavailable")
        
        # Check cache
        cache_key = self._make_cache_key(query, namespaces, top_k)
        if self._cache:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for query: {query[:30]}...")
                return cached
        
        # Coalesce duplicate requests
        coalesce_key = self._coalescer._make_key(query, namespaces, top_k)
        
        try:
            results = await self._coalescer.execute(
                coalesce_key,
                self._search_with_retry,
                query,
                top_k,
                namespaces
            )
            
            # Cache successful results
            if self._cache and results:
                await self._cache.set(cache_key, results)
            
            await self._circuit_breaker.record_success()
            self._metrics["successful_searches"] += 1
            
            return results
            
        except Exception as e:
            await self._circuit_breaker.record_failure()
            self._metrics["failed_searches"] += 1
            raise
    
    async def _search_with_retry(
        self,
        query: str,
        top_k: int,
        namespaces: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute search with retry logic and exponential backoff.
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                async with self._search_semaphore:
                    return await asyncio.wait_for(
                        self._do_search(query, top_k, namespaces),
                        timeout=self.config.search_timeout
                    )
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"Search timed out after {self.config.search_timeout}s")
                logger.warning(f"Search timeout, attempt {attempt + 1}/{self.config.max_retries}")
            except Exception as e:
                last_exception = e
                logger.warning(f"Search error, attempt {attempt + 1}/{self.config.max_retries}: {e}")
            
            if attempt < self.config.max_retries - 1:
                self._metrics["retries"] += 1
                delay = min(
                    self.config.base_retry_delay * (2 ** attempt),
                    self.config.max_retry_delay
                )
                await asyncio.sleep(delay)
        
        raise last_exception or Exception("Search failed after retries")
    
    async def _do_search(
        self,
        query: str,
        top_k: int,
        namespaces: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute actual search against vector store.
        """
        # Run in executor since vector_store.query is sync
        loop = asyncio.get_event_loop()
        search_results = await loop.run_in_executor(
            None,
            lambda: self.vector_store.query(
                query_text=query,
                n_results=top_k,
                namespace=namespaces
            )
        )
        
        # Format results
        formatted = []
        for item in search_results:
            content = item.get('content') or item.get('text') or item.get('document', '')
            formatted.append({
                'content': (content[:500] if isinstance(content, str) else str(content)[:500]),
                'metadata': item.get('metadata', {}),
                'score': item.get('score', item.get('distance', 0.0))
            })
        
        return formatted
    
    async def _add_with_resilience(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add content with retry logic.
        """
        self._metrics["total_writes"] += 1
        
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                async with self._write_semaphore:
                    result = await asyncio.wait_for(
                        self._do_add(content, metadata),
                        timeout=self.config.write_timeout
                    )
                    self._metrics["successful_writes"] += 1
                    return result
            except Exception as e:
                last_exception = e
                logger.warning(f"Add error, attempt {attempt + 1}/{self.config.max_retries}: {e}")
                
                if attempt < self.config.max_retries - 1:
                    self._metrics["retries"] += 1
                    delay = min(
                        self.config.base_retry_delay * (2 ** attempt),
                        self.config.max_retry_delay
                    )
                    await asyncio.sleep(delay)
        
        self._metrics["failed_writes"] += 1
        return {
            'success': False,
            'error': str(last_exception)
        }
    
    async def _do_add(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute actual add to vector store.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.vector_store.add_documents(
                texts=[content],
                metadatas=[metadata]
            )
        )
        return {
            'success': True,
            'documents_added': 1
        }
    
    def _make_cache_key(self, query: str, namespaces: List[str], top_k: int) -> str:
        """Create cache key for search."""
        ns_str = ",".join(sorted(namespaces))
        raw = f"search:{query}:{ns_str}:{top_k}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    # -------------------------------------------------------------------------
    # BATCH OPERATIONS
    # -------------------------------------------------------------------------
    
    async def batch_search(
        self,
        queries: List[str],
        top_k: int = 5,
        namespace: Optional[List[str]] = None,
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple searches concurrently.
        
        Args:
            queries: List of search queries
            top_k: Number of results per query
            namespace: Namespaces to search
            max_concurrent: Max concurrent searches (uses config default if None)
            
        Returns:
            List of results in same order as queries
        """
        search_namespace = namespace or self.config.default_namespaces
        sem = asyncio.Semaphore(max_concurrent or self.config.max_concurrent_searches)
        
        async def search_one(query: str) -> Dict[str, Any]:
            async with sem:
                return await self.aexecute(
                    query=query,
                    top_k=top_k,
                    namespace=search_namespace
                )
        
        tasks = [search_one(q) for q in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def batch_add(
        self,
        contents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Add multiple documents concurrently.
        
        Args:
            contents: List of content strings
            metadatas: Optional list of metadata dicts
            max_concurrent: Max concurrent writes
            
        Returns:
            List of add results
        """
        metadatas = metadatas or [{} for _ in contents]
        sem = asyncio.Semaphore(max_concurrent or self.config.max_concurrent_writes)
        
        async def add_one(content: str, metadata: Dict) -> Dict[str, Any]:
            async with sem:
                return await self._add_with_resilience(content, metadata)
        
        tasks = [add_one(c, m) for c, m in zip(contents, metadatas)]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    # -------------------------------------------------------------------------
    # HEALTH & METRICS
    # -------------------------------------------------------------------------
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        cache_stats = self._cache.stats if self._cache else {}
        return {
            **self._metrics,
            "circuit_breaker_state": self._circuit_breaker.state.value,
            "cache": cache_stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the search tool.
        
        Returns:
            Health status with component details
        """
        health = {
            "healthy": True,
            "components": {}
        }
        
        # Check circuit breaker
        health["components"]["circuit_breaker"] = {
            "state": self._circuit_breaker.state.value,
            "healthy": self._circuit_breaker.state != CircuitState.OPEN
        }
        
        # Check vector store
        try:
            test_result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.vector_store.query("test", n_results=1, namespace=["kenya_law"])
                ),
                timeout=5.0
            )
            health["components"]["vector_store"] = {"healthy": True}
        except Exception as e:
            health["components"]["vector_store"] = {"healthy": False, "error": str(e)}
            health["healthy"] = False
        
        # Cache stats
        if self._cache:
            health["components"]["cache"] = {
                "healthy": True,
                **self._cache.stats
            }
        
        return health
    
    async def invalidate_cache(self, query: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            query: Specific query to invalidate (clears all if None)
        """
        if not self._cache:
            return
        
        if query:
            for ns in self.config.default_namespaces:
                for top_k in [5, 10, 20]:
                    key = self._make_cache_key(query, [ns], top_k)
                    await self._cache.invalidate(key)
        else:
            self._cache._cache.clear()
            self._cache._access_order.clear()
            logger.info("Cache cleared")

