"""
Main entry point for the Jarvis AI Assistant FastAPI application.

This script initializes the FastAPI app, sets up the lifespan manager for
service initialization and shutdown, configures routes, and starts the Uvicorn server.
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Pre-emptive CPU Optimizations ---
# This must be done BEFORE importing libraries like numpy or torch
from config.performance_config import apply_cpu_optimizations
apply_cpu_optimizations()

# --- Project and Logging Setup ---
# Add project root to sys.path for absolute imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import configuration and utilities AFTER setting up path and optimizations
from config.app_config import AppConfig
from utils.api_optimizer import optimize_fastapi_app, start_cache_cleanup_task
from utils.memory_optimizer import optimize_memory_periodically

# Configure logging based on AppConfig
logging.basicConfig(
    level=AppConfig.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# --- Service and Controller Imports ---
from services.embedding_service import EmbeddingService
from services.database_service import DatabaseService
from services.llm_service import LLMService
from controllers.rag_controller import RAGController

# Dictionary to hold our singleton services and controllers
app_state: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan. Initializes services on startup and
    cleans up on shutdown. Also starts background tasks.
    """
    # --- Startup --- 
    logging.info("Application startup: Initializing services...")
    
    # Initialize services using centralized AppConfig
    embedding_service = EmbeddingService(model_name=AppConfig.EMBEDDING_MODEL)
    database_service = DatabaseService(embedding_service=embedding_service)
    llm_service = LLMService(
        model_name=AppConfig.OLLAMA_MODEL,
        host=AppConfig.OLLAMA_HOST
    )
    
    # Initialize the main controller with dependent services
    rag_controller = RAGController(
        embedding_service=embedding_service,
        database_service=database_service,
        llm_service=llm_service
    )
    app_state['rag_controller'] = rag_controller
    logging.info("Services initialized successfully.")

    # Start background tasks
    logging.info("Starting background tasks...")
    app_state['cache_cleanup_task'] = start_cache_cleanup_task()
    app_state['memory_optimizer_task'] = optimize_memory_periodically()
    logging.info("Background tasks started.")

    yield

    # --- Shutdown ---
    logging.info("Application shutdown: Cleaning up resources...")
    # Cancel background tasks gracefully
    for task_name, task in app_state.items():
        if hasattr(task, 'cancel'):
            try:
                task.cancel()
                logging.info(f"Cancelled task: {task_name}")
            except Exception as e:
                logging.error(f"Error cancelling task {task_name}: {e}", exc_info=True)
    
    app_state.clear()
    logging.info("Shutdown complete.")


# Create FastAPI app with lifespan
app = FastAPI(
    title=AppConfig.APP_NAME,
    description="API for interacting with the Jarvis AI assistant, featuring RAG and local LLM capabilities.",
    version="1.0.0",
    lifespan=lifespan
)

# Apply performance optimizations
# Add CORS middleware to allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = optimize_fastapi_app(app)

# Dependency to get the RAG controller
def get_rag_controller() -> RAGController:
    """
    FastAPI dependency to get the singleton RAGController instance.

    Returns:
        The singleton RAGController instance from the application state.
    """
    return app_state.get('rag_controller')

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Welcome to the Jarvis AI Assistant API!"}

# Import and include the API routers
from routes import chat_routes, knowledge_routes, performance_routes

app.include_router(chat_routes.router, prefix="/api/v1")
app.include_router(knowledge_routes.router, prefix="/api/v1")
app.include_router(performance_routes.router, prefix="/api/v1")

if __name__ == "__main__":
    # Host and port are now configurable via .env, but we can provide code-level defaults.
    # Note: AppConfig doesn't handle these as they are specific to the run command.
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    logging.info(f"Starting Uvicorn server at http://{host}:{port} with reload={'enabled' if reload else 'disabled'}")
    uvicorn.run("api:app", host=host, port=port, reload=reload)
