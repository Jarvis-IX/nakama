# Services

This folder contains core services for the Jarvis AI assistant.

## Purpose

- Handle external integrations (Supabase, Ollama)
- Manage embedding generation and vector operations
- Provide database abstraction layer
- Implement LLM communication logic

## Files

- `embedding_service.py` - Text embedding generation using all-MiniLM-L6-v2
- `database_service.py` - Supabase database operations and vector search
- `llm_service.py` - Ollama LLM communication and response generation
- `vector_service.py` - Vector similarity search and indexing

## Usage

Services are stateless and provide clean interfaces for external dependencies.
