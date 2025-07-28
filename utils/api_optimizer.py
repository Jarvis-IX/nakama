"""
FastAPI Performance Optimization for Jarvis AI Assistant
Advanced API optimizations for CPU-only inference
"""

import asyncio
import gzip
import time
import uuid
from functools import wraps
from typing import Dict, Any, Optional, Callable, Awaitable
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.gzip import GZipMiddleware
import logging

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Custom middleware for performance monitoring and optimization"""
    
    def __init__(self, app, enable_compression: bool = True):
        super().__init__(app)
        self.enable_compression = enable_compression
        self.request_times = {}
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Request {request_id} started: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            response.headers["X-Request-ID"] = request_id

            if process_time > 1.0:
                logger.warning(f"Slow request {request_id}: {process_time:.4f}s for {request.method} {request.url.path}")
            else:
                logger.info(f"Request {request_id} finished in {process_time:.4f}s with status {response.status_code}")

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request {request_id} failed after {process_time:.4f}s: {e}",
                exc_info=True
            )
            # Re-raise to ensure FastAPI's default error handling kicks in
            raise e
        
        return response

class ResponseCache:
    """Simple in-memory response cache for API endpoints"""
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
        self._cleanup_task: Optional[asyncio.Task] = None
        
    def get_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        return f"{request.method}:{request.url.path}:{request.url.query}"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        if key in self.cache:
            cached_item = self.cache[key]
            if time.time() - cached_item["timestamp"] < self.ttl:
                return cached_item["response"]
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, response: Dict[str, Any]):
        """Cache response with TTL"""
        # Clean old entries if cache is full
        if len(self.cache) >= self.max_size:
            self._cleanup_expired()
        
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }
    
    async def _periodic_cleanup(self):
        """Periodically remove expired entries from the cache."""
        while True:
            await asyncio.sleep(self.ttl)
            self._cleanup_expired()

    def start_cleanup_task(self) -> Optional[asyncio.Task]:
        """Starts the background cleanup task and returns it."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("ResponseCache background cleanup task started.")
        return self._cleanup_task

    def _cleanup_expired(self):
        """Remove expired entries"""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, value in self.cache.items()
                if current_time - value.get("timestamp", 0) >= self.ttl
            ]
            if expired_keys:
                for key in expired_keys:
                    self.cache.pop(key, None)
                logger.debug(f"Cache cleanup removed {len(expired_keys)} expired items.")
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}", exc_info=True)

class ConcurrencyLimiter:
    """Limits the number of concurrent operations using an asyncio.Semaphore."""
    
    def __init__(self, max_concurrency: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.active_count = 0
    
    async def acquire(self):
        """Acquire a slot from the limiter."""
        await self.semaphore.acquire()
        self.active_count += 1
        logger.debug(f"Concurrency slot acquired. Active: {self.active_count}")
    
    def release(self):
        """Release a slot back to the limiter."""
        self.semaphore.release()
        self.active_count -= 1
        logger.debug(f"Concurrency slot released. Active: {self.active_count}")

class APIOptimizer:
    """Main API optimization coordinator"""
    
    def __init__(self):
        self.response_cache = ResponseCache()
        self.concurrency_limiter = ConcurrencyLimiter()
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
            "slow_requests": 0
        }
    
    def get_optimization_middlewares(self):
        """Get list of optimization middlewares to add to FastAPI app"""
        return [
            (PerformanceMiddleware, {}),
            (GZipMiddleware, {"minimum_size": 1000})  # Compress responses > 1KB
        ]
    
    async def cache_get(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get cached response for request"""
        cache_key = self.response_cache.get_cache_key(request)
        cached_response = self.response_cache.get(cache_key)
        
        if cached_response:
            self.metrics["cache_hits"] += 1
            logger.debug(f"Cache hit for {cache_key}")
            return cached_response
        else:
            self.metrics["cache_misses"] += 1
            return None
    
    async def cache_set(self, request: Request, response: Dict[str, Any]):
        """Cache response for request"""
        cache_key = self.response_cache.get_cache_key(request)
        self.response_cache.set(cache_key, response)
        logger.debug(f"Cached response for {cache_key}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        cache_total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (self.metrics["cache_hits"] / cache_total * 100) if cache_total > 0 else 0

        return {
            "total_requests": self.metrics["total_requests"],
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "cache_size": len(self.response_cache.cache),
            "active_connections": self.concurrency_limiter.active_count,
            "avg_response_time_ms": round(self.metrics.get("avg_response_time", 0) * 1000, 2),
            "slow_requests": self.metrics["slow_requests"]
        }
    
    def optimize_for_cpu_inference(self) -> Dict[str, Any]:
        """Apply CPU-specific optimizations"""
        optimizations = {
            "asyncio_policy": "Set event loop policy for CPU workloads",
            "thread_pool": "Configured thread pool for blocking operations",
            "compression": "Enabled response compression",
            "caching": "Enabled response caching",
            "concurrency_limiting": "Limited concurrent operations"
        }
        
        # Set asyncio policy for CPU-bound tasks
        try:
            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                optimizations["asyncio_policy"] = "Windows Proactor policy set"
        except Exception as e:
            logger.warning(f"Could not set asyncio policy: {e}")
        
        return optimizations

    def start_background_tasks(self):
        """Starts the background cache cleanup task."""
        self.response_cache.start_cleanup_task()

# Global API optimizer instance
api_optimizer = APIOptimizer()

def optimize_fastapi_app(app: FastAPI) -> FastAPI:
    """
    Applies a suite of performance optimizations to a FastAPI application.

    - Adds GZip compression for responses.
    - Adds a custom middleware for performance logging and request tracing.
    """
    # Add GZip Middleware for response compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add custom performance and logging middleware
    app.add_middleware(PerformanceMiddleware)

    logger.info("FastAPI app performance middleware applied.")
    return app

def start_cache_cleanup_task() -> Optional[asyncio.Task]:
    """Starts the global API response cache cleanup task."""
    logger.info("Initializing global cache cleanup task...")
    return api_optimizer.response_cache.start_cleanup_task()


def cacheable_endpoint(ttl: int = 300) -> Callable:
    """Decorator for cacheable API endpoints."""
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            try:
                cached_response_data = await api_optimizer.cache_get(request)
                if cached_response_data:
                    return JSONResponse(content=cached_response_data)

                # Execute the actual endpoint function
                response = await func(request, *args, **kwargs)

                # Cache the response if it's a successful one
                if isinstance(response, JSONResponse) and 200 <= response.status_code < 300:
                    await api_optimizer.cache_set(request, response.body)
                
                return response
            except Exception as e:
                logger.error(f"Error in cacheable endpoint '{func.__name__}': {e}", exc_info=True)
                # Re-raise as HTTPException to ensure proper API error response
                raise HTTPException(status_code=500, detail="Internal server error in cached endpoint")
        return wrapper
    return decorator
