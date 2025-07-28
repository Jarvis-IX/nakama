"""
Memory Optimization Utilities for Jarvis AI Assistant
Advanced memory management for CPU-only inference
"""

import asyncio
import gc
import time
from typing import Dict, Any, Optional, Callable
from functools import lru_cache, wraps
import logging

# Try to import psutil, but don't make it a hard requirement
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

class MemoryOptimizer:
    """Advanced memory management for CPU-only AI inference."""

    def __init__(self):
        # LRU cache for embeddings is now managed via a decorator, not here.
        pass

    def optimize_gc(self):
        """Run garbage collection and log the number of collected objects."""
        try:
            # More aggressive collection can be useful in memory-constrained environments
            gc.set_threshold(700, 10, 10)
            collected = gc.collect(generation=2)  # Focus on the oldest generation
            logger.info(f"Garbage collection freed {collected} objects.")
            return collected
        except Exception as e:
            logger.error(f"Error during garbage collection: {e}", exc_info=True)
            return 0

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory usage statistics if psutil is available."""
        if not psutil:
            logger.warning("psutil is not installed. Cannot get memory stats.")
            return {}
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": round(memory_info.rss / 1024**2, 2),
                "vms_mb": round(memory_info.vms / 1024**2, 2),
                "percent": round(process.memory_percent(), 2),
                "gc_counts": gc.get_count(),
            }
        except Exception as e:
            logger.error(f"Could not retrieve memory stats: {e}", exc_info=True)
            return {}

    def clear_embedding_cache(self):
        """Clears the lru_cache for embeddings."""
        # To clear a specific lru_cache, you call .cache_clear() on the decorated function.
        # This is a placeholder for how it would be called from a central place.
        # Example: EmbeddingService.get_embedding.cache_clear()
        logger.info("Embedding cache clear requested. Implement by calling .cache_clear() on the cached function.")

    def clear_all_caches(self):
        """Clear all managed caches and force garbage collection."""
        self.clear_embedding_cache()
        self.optimize_gc()
        logger.info("All caches cleared and garbage collection performed.")

def memory_profile(func: Callable) -> Callable:
    """Decorator to profile memory usage of a function if psutil is available."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not psutil:
            return func(*args, **kwargs)

        process = psutil.Process()
        mem_before = 0
        try:
            mem_before = process.memory_info().rss / 1024**2  # MB
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing function {func.__name__} in memory_profile: {e}", exc_info=True)
            raise # Re-raise the exception after logging
        finally:
            mem_after = process.memory_info().rss / 1024**2  # MB
            mem_diff = mem_after - mem_before
            if mem_diff > 1:  # Log if memory increased by more than 1MB
                logger.info(f"{func.__name__} used {mem_diff:.2f}MB of memory.")

    return wrapper

# Global memory optimizer instance
memory_optimizer = MemoryOptimizer()

def optimize_memory_periodically(interval_seconds: int = 300):
    """Creates an asyncio task to periodically run garbage collection."""

    async def cleanup_task():
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                logger.debug("Running periodic memory optimization...")
                memory_optimizer.optimize_gc()
            except Exception as e:
                logger.error(f"Error in periodic memory cleanup task: {e}", exc_info=True)

    try:
        task = asyncio.create_task(cleanup_task())
        logger.info(f"Started periodic memory optimization task running every {interval_seconds}s.")
        return task
    except Exception as e:
        logger.error(f"Failed to start memory optimization task: {e}", exc_info=True)
        return None
