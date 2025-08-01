# Jarvis AI Assistant
![Jarvis AI Logo](https://via.placeholder.com/150)
*A personal, open-source AI assistant with local LLM and vector search capabilities*

## 📋 Overview
Jarvis AI Assistant is a privacy-focused, self-hosted AI companion that runs entirely on your local machine. It combines the power of local language models with semantic search capabilities to provide a private, secure, and highly customizable AI experience.

## ✨ Key Features
### 🤖 Local LLM Integration
- **Private & Secure**: All processing happens locally on your machine
- **Multiple Models**: Supports various Ollama models (default: llama3.2:3b)
- **CPU Optimized**: Efficiently runs on consumer hardware

### 🔍 Smart Document Processing
- **File Ingestion**: Supports PDF, TXT, and other text formats
- **Semantic Search**: Advanced vector-based retrieval
- **Context-Aware**: Maintains conversation context for relevant responses

### ⚡ Performance Optimized
- **Background Processing**: Non-blocking operations for smooth UX
- **Intelligent Caching**: Reduces redundant computations
- **Resource Efficient**: Designed for CPU-only environments

### 🔄 Open Ecosystem
- **Extensible Architecture**: Easy to add new features and integrations
- **API-First Design**: Built with FastAPI for seamless integration
- **Community Driven**: Open source and welcoming to contributions

## 🚀 Getting Started
### Prerequisites
- Python 3.13+ (3.13.5+ recommended)
- Ollama installed and running locally
- Supabase account (for vector storage)
- 8GB+ RAM (16GB recommended)

### Installation
1. **Clone the repository**
```bash
git clone https://github.com/yourusername/jarvis-ai-assistant.git
cd jarvis-ai-assistant
```

2. **Set up Python environment**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: .\venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
```

3. **Configure environment**
```bash
# Copy and edit the example configuration
cp .env.example .env
# Edit .env with your Supabase and Ollama details
```

4. **Set up Ollama**
```bash
# Download and install Ollama from https://ollama.ai
# Pull the default model
ollama pull llama3.2:3b
```

5. **Run the application**
```bash
# Start the FastAPI server
uvicorn api:app --reload
```

6. **Access the API**
- Open your browser to: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs

## ⚙️ Configuration
### Environment Variables
Create a `.env` file based on `.env.example` with your configuration:
```ini
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_TABLE=documents
# Ollama Configuration
OLLAMA_MODEL=llama3.2:3b
OLLAMA_HOST=http://127.0.0.1:11434
# Application Settings
LOG_LEVEL=INFO
API_HOST=127.0.0.1
API_PORT=8000
API_RELOAD=True
```

## 📚 API Documentation
### Available Endpoints
- `GET /` - Health check and welcome message
- `POST /api/v1/chat` - Chat with the AI
- `POST /api/v1/chat/stream` - Stream chat responses
- `POST /api/v1/knowledge/add-text` - Add text to knowledge base
- `POST /api/v1/knowledge/add-file` - Upload and process a file
- `GET /api/v1/status` - Get system status and metrics

### Example API Usage
```bash
# Chat with the AI
curl -X POST http://localhost:8000/api/v1/chat \
-H "Content-Type: application/json" \
-d '{"message": "Hello, Jarvis!"}'
# Stream response
curl -N http://localhost:8000/api/v1/chat/stream \
-H "Content-Type: application/json" \
-d '{"message": "Tell me about yourself"}'
```

## 🏗️ Project Structure
```
jarvis-ai-assistant/
├── config/ # Configuration management
│ ├── app_config.py # Application configuration
│ └── performance.py # Performance tuning
├── controllers/ # Business logic
├── routes/ # API endpoints
├── services/ # Core services
│ ├── database.py # Database operations
│ ├── embedding.py # Text embedding
│ └── llm.py # LLM integration
├── utils/ # Helper functions
├── scripts/ # Utility scripts
├── temp-storage/ # Temporary file storage
├── .env.example # Example environment config
├── api.py # FastAPI application
└── requirements.txt # Dependencies
```

## 🛠️ Development
### Prerequisites
- Python 3.13+
- Poetry (for dependency management)
- Pre-commit hooks

### Setup
1. **Install development dependencies**
```bash
pip install -r requirements-dev.txt
pre-commit install
```

2. **Run tests**
```bash
pytest tests/
```

3. **Code style**
```bash
# Auto-format code
black .
# Check code style
flake8 .
```

## 🤝 Contributing
We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🚨 Troubleshooting
### Common Issues
1. **Ollama connection refused**
- Ensure Ollama is running: `ollama serve`
- Check `OLLAMA_HOST` in `.env`
2. **Supabase connection issues**
- Verify `SUPABASE_URL` and `SUPABASE_KEY`
- Check if the table schema matches the code
3. **Performance problems**
- Try a smaller LLM model
- Reduce `CHUNK_SIZE` in `.env`
- Check system resource usage

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- [Ollama](https://ollama.ai) for making local LLMs accessible
- [Supabase](https://supabase.com) for the open-source Firebase alternative
- The open-source community for their invaluable contributions

---
<p align="center">
  Made with ❤️ Jarvis
</p>