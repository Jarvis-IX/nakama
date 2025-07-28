"""
Performance Configuration for Jarvis AI Assistant
Optimized for Intel i5-10210U CPU-only hardware
"""

import logging
import os
from typing import Dict, Any

# Try to import psutil, but don't make it a hard requirement
try:
    import psutil
except ImportError:
    psutil = None

from config.app_config import AppConfig

logger = logging.getLogger(__name__)


class PerformanceConfig:
    """
    Provides dynamically calculated, hardware-aware performance settings.
    This is not user-configurable via .env; it adapts to the host system.
    """
    # Dynamically determine the number of physical CPU cores.
    # Fallback to a sensible default if psutil is not available.
    CPU_PHYSICAL_CORES = psutil.cpu_count(logical=False) if psutil else 4

    # Settings for libraries that use OpenMP or MKL for parallelization.
    # Using physical cores is often optimal for compute-heavy tasks.
    OMP_NUM_THREADS = str(CPU_PHYSICAL_CORES)
    MKL_NUM_THREADS = str(CPU_PHYSICAL_CORES)


def apply_cpu_optimizations() -> None:
    """
    Applies environment variables to optimize for CPU-only inference.
    This should be called once at application startup.
    """
    logger.info(f"Applying CPU optimizations for {PerformanceConfig.CPU_PHYSICAL_CORES} physical cores.")
    os.environ['OMP_NUM_THREADS'] = PerformanceConfig.OMP_NUM_THREADS
    os.environ['MKL_NUM_THREADS'] = PerformanceConfig.MKL_NUM_THREADS
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Avoids warnings with HuggingFace tokenizers
    os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Explicitly disable CUDA


def get_ollama_options() -> Dict[str, Any]:
    """
    Returns a dictionary of optimized Ollama options for CPU inference.
    Pulls base settings from AppConfig and adds hardware-specific tuning.
    """
    return {
        # --- From AppConfig (user-configurable) ---
        "temperature": AppConfig.DEFAULT_TEMPERATURE,
        "num_ctx": App_Config.DEFAULT_MAX_TOKENS, # Renamed for clarity in Ollama
        "top_k": 40, # Good default for CPU
        "top_p": 0.9,
        "repeat_penalty": 1.1,

        # --- From PerformanceConfig (hardware-aware) ---
        "num_thread": PerformanceConfig.CPU_PHYSICAL_CORES,
        "num_gpu": 0,  # Ensure CPU-only operation

        # --- Static recommendation ---
        "stop": ["\nUSER:"],  # Common stop token
    }


def get_system_info() -> Dict[str, Any]:
    """
    Returns a dictionary of system information for performance monitoring.
    Returns empty dict if psutil is not installed.
    """
    if not psutil:
        logger.warning("psutil not installed, cannot retrieve system info.")
        return {}

    try:
        return {
            "cpu_physical_cores": PerformanceConfig.CPU_PHYSICAL_CORES,
            "cpu_logical_cores": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "memory_percent": psutil.virtual_memory().percent,
            "optimizations_applied": {
                "omp_threads": os.environ.get('OMP_NUM_THREADS'),
                "mkl_threads": os.environ.get('MKL_NUM_THREADS'),
                "cuda_disabled": os.environ.get('CUDA_VISIBLE_DEVICES') == '',
            }
        }
    except Exception as e:
        logger.error(f"Could not retrieve system info: {e}", exc_info=True)
        return {}

