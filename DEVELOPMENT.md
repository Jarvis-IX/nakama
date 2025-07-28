# Development Guide

This guide provides detailed instructions for setting up a development environment for the Jarvis AI Assistant project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Debugging](#debugging)
- [Performance Profiling](#performance-profiling)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Prerequisites

- Python 3.13.5+
- [Poetry](https://python-poetry.org/) for dependency management
- [Ollama](https://ollama.ai/) (for local LLM inference)
- [Supabase](https://supabase.com/) account (for vector database)
- Git
- (Optional) Docker and Docker Compose for containerized development

## Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/jarvis-ai-assistant.git
   cd jarvis-ai-assistant
   ```

2. **Set up Python environment**
   ```bash
   # Install Poetry if you haven't already
   pip install poetry
   
   # Install dependencies
   poetry install
   
   # Activate the virtual environment
   poetry shell
   ```

3. **Configure environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your configuration
   # (See Configuration section below for details)
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```ini
# Supabase Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
SUPABASE_TABLE=documents  # Default table name for documents

# Ollama Configuration
OLLAMA_MODEL=llama3.2:3b  # Default model
OLLAMA_HOST=http://127.0.0.1:11434  # Ollama server URL

# Application Settings
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
API_HOST=127.0.0.1
API_PORT=8000
API_RELOAD=True  # Auto-reload in development

# Performance Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Sentence Transformer model
CHUNK_SIZE=500  # Characters per text chunk
CHUNK_OVERLAP=50  # Overlap between chunks
```

## Project Structure

```
jarvis-ai-assistant/
├── config/               # Configuration management
│   ├── __init__.py
│   ├── app_config.py     # Application configuration
│   └── performance.py    # Performance tuning
├── controllers/          # Business logic
│   ├── __init__.py
│   └── rag_controller.py # RAG pipeline controller
├── routes/               # API endpoints
│   ├── __init__.py
│   ├── chat_routes.py    # Chat endpoints
│   └── knowledge_routes.py # Knowledge base endpoints
├── services/             # Core services
│   ├── __init__.py
│   ├── database.py       # Database operations
│   ├── embedding.py      # Text embedding
│   └── llm.py           # LLM integration
├── utils/                # Helper functions
│   ├── __init__.py
│   ├── api_optimizer.py  # API performance
│   ├── file_utils.py     # File handling
│   ├── memory_optimizer.py # Memory management
│   └── text_utils.py     # Text processing
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── temp-storage/         # Temporary file storage
├── .env.example         # Example environment config
├── .gitignore
├── LICENSE
├── poetry.lock
├── pyproject.toml
├── README.md
└── api.py              # FastAPI application entry point
```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Run the development server**
   ```bash
   uvicorn api:app --reload
   ```

3. **Access the API documentation**
   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

4. **Make your changes** following the code style guidelines

5. **Run tests**
   ```bash
   # Run all tests
   pytest
   
   # Run a specific test file
   pytest tests/test_rag_controller.py
   
   # Run with coverage
   pytest --cov=./ --cov-report=html
   ```

6. **Format and lint your code**
   ```bash
   # Auto-format code
   black .
   isort .
   
   # Check code style
   flake8 .
   mypy .
   ```

7. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   git push origin feature/your-feature-name
   ```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=./ --cov-report=html

# Run a specific test
pytest tests/test_rag_controller.py::test_rag_workflow

# Run tests in parallel
pytest -n auto
```

### Writing Tests

- Put test files in the `tests/` directory
- Name test files with `test_` prefix (e.g., `test_rag_controller.py`)
- Use descriptive test function names starting with `test_`
- Use fixtures for common test data and setup
- Mock external dependencies

## Debugging

### VS Code Configuration

Add this to your `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "api:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

### Debugging with pdb

```python
import pdb; pdb.set_trace()  # Python 3.7+
# or
breakpoint()  # Python 3.7+
```

## Performance Profiling

### CPU Profiling

```bash
# Install profiling tools
pip install pyinstrument

# Profile the application
pyinstrument -m uvicorn api:app
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Add @profile decorator to functions you want to profile
# Then run:
python -m memory_profiler your_script.py
```

## Documentation

### Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve
```

### Writing Documentation

- Keep documentation up to date with code changes
- Use docstrings following Google style guide
- Document public APIs thoroughly
- Include examples for complex functionality

## Release Process

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Create a release tag**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```
4. **Create a GitHub release** with release notes
5. **Publish to PyPI** (if applicable)
   ```bash
   poetry build
   poetry publish
   ```

## Troubleshooting

### Common Issues

- **Ollama connection refused**: Make sure Ollama is running (`ollama serve`)
- **Supabase connection issues**: Verify `SUPABASE_URL` and `SUPABASE_KEY`
- **Import errors**: Make sure you've activated the virtual environment
- **Memory issues**: Try reducing `CHUNK_SIZE` or using a smaller model

## Getting Help

- Check the [GitHub Issues](https://github.com/your-username/jarvis-ai-assistant/issues)
- Join our [community forum](#) (if available)
- Open a new issue for bugs or feature requests
