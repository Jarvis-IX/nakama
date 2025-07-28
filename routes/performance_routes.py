from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
import psutil
import time

# Import the dependency and configuration
from api import get_rag_controller
from controllers.rag_controller import RAGController
from config.performance_config import PerformanceConfig
from utils.api_optimizer import api_optimizer
from utils.memory_optimizer import memory_optimizer

router = APIRouter(
    tags=["Performance"],
    responses={404: {"description": "Not found"}},
)

class PerformanceMetrics(BaseModel):
    system_info: Dict[str, Any]
    cpu_usage: float
    memory_usage: Dict[str, float]
    optimization_status: Dict[str, Any]
    model_info: Dict[str, Any]

@router.get("/performance/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics(
    rag_controller: RAGController = Depends(get_rag_controller)
):
    """
    Get current performance metrics and system status.
    Useful for monitoring CPU usage and optimization effectiveness.
    """
    # Get system information
    system_info = PerformanceConfig.get_system_info()
    
    # Get current resource usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    memory_usage = {
        "total_gb": round(memory.total / (1024**3), 2),
        "available_gb": round(memory.available / (1024**3), 2),
        "used_gb": round(memory.used / (1024**3), 2),
        "percent": memory.percent
    }
    
    # Get optimization status
    optimization_status = {
        "cpu_cores_configured": PerformanceConfig.CPU_CORES,
        "embedding_batch_size": PerformanceConfig.EMBEDDING_BATCH_SIZE,
        "llm_context_window": PerformanceConfig.LLM_CONTEXT_WINDOW,
        "max_conversation_history": PerformanceConfig.MAX_CONVERSATION_HISTORY,
        "cpu_optimizations_active": system_info["optimizations_applied"]
    }
    
    # Get model information if available
    model_info = {}
    if rag_controller:
        try:
            model_info = {
                "embedding_model": rag_controller.embedding_service.get_model_info(),
                "llm_model": rag_controller.llm_service.get_model_info()
            }
        except Exception as e:
            model_info = {"error": f"Could not retrieve model info: {str(e)}"}
    
    return PerformanceMetrics(
        system_info=system_info,
        cpu_usage=cpu_percent,
        memory_usage=memory_usage,
        optimization_status=optimization_status,
        model_info=model_info
    )

@router.get("/performance/api-stats")
async def get_api_performance_stats():
    """
    Get API-specific performance statistics including caching and optimization metrics.
    """
    api_stats = api_optimizer.get_performance_stats()
    memory_stats = memory_optimizer.get_memory_stats()
    
    return {
        "api_performance": api_stats,
        "memory_optimization": memory_stats,
        "cache_status": {
            "embedding_cache_enabled": True,
            "response_cache_enabled": True,
            "memory_optimization_active": True
        },
        "optimizations_active": {
            "cpu_threading": True,
            "memory_profiling": True,
            "response_compression": True,
            "connection_pooling": True,
            "garbage_collection_tuning": True
        }
    }

@router.get("/performance/benchmark")
async def run_performance_benchmark(
    rag_controller: RAGController = Depends(get_rag_controller)
):
    """
    Run a simple performance benchmark to test response times.
    """
    if not rag_controller:
        return {"error": "RAG controller not available"}
    
    benchmark_results = {}
    
    try:
        # Test embedding generation speed
        start_time = time.time()
        test_text = "This is a test sentence for benchmarking embedding generation speed."
        embedding = rag_controller.embedding_service.generate_embedding(test_text)
        embedding_time = time.time() - start_time
        
        benchmark_results["embedding_generation"] = {
            "time_seconds": round(embedding_time, 4),
            "embedding_dimension": len(embedding)
        }
        
        # Test LLM response speed (simple query)
        start_time = time.time()
        response_generator = rag_controller.stream_response(
            question="What is 2+2?",
            use_context=False
        )
        
        # Consume the generator to measure full response time
        response_chunks = list(response_generator)
        llm_time = time.time() - start_time
        
        benchmark_results["llm_response"] = {
            "time_seconds": round(llm_time, 4),
            "response_length": len(''.join(response_chunks)),
            "chunks_generated": len(response_chunks)
        }
        
        # Overall performance score (lower is better)
        performance_score = embedding_time + llm_time
        benchmark_results["overall_performance_score"] = round(performance_score, 4)
        
        return {
            "status": "completed",
            "timestamp": time.time(),
            "results": benchmark_results,
            "recommendations": _get_performance_recommendations(benchmark_results)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

def _get_performance_recommendations(results: Dict[str, Any]) -> list:
    """Generate performance recommendations based on benchmark results"""
    recommendations = []
    
    embedding_time = results.get("embedding_generation", {}).get("time_seconds", 0)
    llm_time = results.get("llm_response", {}).get("time_seconds", 0)
    
    if embedding_time > 0.5:
        recommendations.append("Embedding generation is slow. Consider reducing batch sizes or text length.")
    
    if llm_time > 10:
        recommendations.append("LLM response time is high. Consider reducing context window or max tokens.")
    
    if not recommendations:
        recommendations.append("Performance looks good! System is well-optimized for your hardware.")
    
    return recommendations
