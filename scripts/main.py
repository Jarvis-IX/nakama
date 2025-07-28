#!/usr/bin/env python3
"""
Jarvis AI Assistant - Main Entry Point
Your personal open-source AI assistant with local LLM and vector search
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.embedding_service import EmbeddingService
from services.database_service import DatabaseService
from services.llm_service import LLMService
from controllers.rag_controller import RAGController
from utils.file_utils import ensure_directory_exists
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('jarvis.log')
        ]
    )

def initialize_services():
    """Initialize all services"""
    print("🤖 Initializing Jarvis AI Assistant...")
    
    # Initialize services
    embedding_service = EmbeddingService(
        model_name=os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    )
    
    database_service = DatabaseService()
    
    llm_service = LLMService(
        model_name=os.getenv('OLLAMA_MODEL', 'llama3.2:3b'),
        host=os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    )
    
    # Initialize RAG controller
    rag_controller = RAGController(
        embedding_service=embedding_service,
        database_service=database_service,
        llm_service=llm_service
    )
    
    print("✅ Jarvis initialized successfully!")
    return rag_controller

def interactive_chat(rag_controller: RAGController):
    """Start interactive chat session"""
    print("\n🤖 Jarvis AI Assistant")
    print("=" * 50)
    print("Type 'exit', 'quit', or 'bye' to end the conversation")
    print("Type 'clear' to clear conversation history")
    print("Type 'status' to check system status")
    print("Type 'help' for available commands")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("🤖 Jarvis: Goodbye! Have a great day!")
                break
            
            if user_input.lower() == 'clear':
                rag_controller.clear_conversation_history()
                print("🤖 Jarvis: Conversation history cleared.")
                continue
            
            if user_input.lower() == 'status':
                status = rag_controller.get_system_status()
                print("🤖 Jarvis: System Status:")
                for key, value in status.items():
                    print(f"  • {key}: {value}")
                continue
            
            if user_input.lower() == 'help':
                show_help()
                continue
            
            if not user_input:
                continue
            
            print("🤖 Jarvis: ", end="", flush=True)
            
            # Get streaming response
            response = rag_controller.stream_response(user_input)
            
        except KeyboardInterrupt:
            print("\n🤖 Jarvis: Goodbye!")
            break
        except Exception as e:
            print(f"\n🤖 Jarvis: I encountered an error: {str(e)}")

def show_help():
    """Show available commands"""
    print("\n🤖 Jarvis: Available commands:")
    print("  • Ask any question - I'll search my knowledge base and respond")
    print("  • 'clear' - Clear conversation history")
    print("  • 'status' - Show system status")
    print("  • 'help' - Show this help message")
    print("  • 'exit', 'quit', 'bye' - End conversation")

def run_tests(rag_controller: RAGController):
    """Run system tests"""
    print("🧪 Running Jarvis system tests...")
    
    # Test 1: LLM connection
    print("\n🔍 Testing LLM connection...")
    try:
        response = rag_controller.llm_service.generate_response("Hello, are you working?")
        print(f"✅ LLM Response: {response[:100]}...")
    except Exception as e:
        print(f"❌ LLM Test Failed: {e}")
        return False
    
    # Test 2: Database connection
    print("\n🔍 Testing database connection...")
    try:
        healthy = rag_controller.database_service.health_check()
        if healthy:
            print("✅ Database connection healthy")
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database Test Failed: {e}")
        return False
    
    # Test 3: Embedding service
    print("\n🔍 Testing embedding service...")
    try:
        embedding = rag_controller.embedding_service.generate_embedding("test text")
        print(f"✅ Embedding generated: {len(embedding)} dimensions")
    except Exception as e:
        print(f"❌ Embedding Test Failed: {e}")
        return False
    
    # Test 4: End-to-end RAG pipeline
    print("\n🔍 Testing RAG pipeline...")
    try:
        result = rag_controller.ask_question("What can you help me with?")
        print(f"✅ RAG Pipeline: {result['response'][:100]}...")
    except Exception as e:
        print(f"❌ RAG Pipeline Test Failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Jarvis is ready to use.")
    return True

def add_knowledge_from_file(rag_controller: RAGController, file_path: str):
    """Add knowledge from a text file"""
    try:
        from utils.file_utils import read_text_file
        from utils.text_utils import chunk_text
        
        content = read_text_file(file_path)
        if not content:
            print(f"❌ Could not read file: {file_path}")
            return False
        
        # Chunk the content
        chunks = chunk_text(content, chunk_size=500, overlap=50)
        
        print(f"📚 Adding {len(chunks)} chunks from {file_path}...")
        
        # Add chunks as separate documents
        documents = [{"content": chunk} for chunk in chunks]
        success = rag_controller.batch_add_knowledge(documents)
        
        if success:
            print(f"✅ Successfully added knowledge from {file_path}")
        else:
            print(f"❌ Failed to add knowledge from {file_path}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error adding knowledge from file: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Jarvis AI Assistant")
    parser.add_argument("--model", default=None, 
                       help="Ollama model to use (overrides env var)")
    parser.add_argument("--test", action="store_true", 
                       help="Run system tests")
    parser.add_argument("--add-knowledge", type=str, 
                       help="Add knowledge from text file")
    parser.add_argument("--question", type=str, 
                       help="Ask a single question and exit")
    parser.add_argument("--log-level", default="INFO", 
                       help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Ensure temp storage directory exists
    temp_storage = os.getenv('TEMP_STORAGE_PATH', './temp-storage')
    ensure_directory_exists(temp_storage)
    
    try:
        # Override model if specified
        if args.model:
            os.environ['OLLAMA_MODEL'] = args.model
        
        # Initialize Jarvis
        rag_controller = initialize_services()
        
        if args.test:
            # Run tests
            success = run_tests(rag_controller)
            sys.exit(0 if success else 1)
        
        if args.add_knowledge:
            # Add knowledge from file
            success = add_knowledge_from_file(rag_controller, args.add_knowledge)
            sys.exit(0 if success else 1)
        
        if args.question:
            # Single question mode
            print(f"❓ Question: {args.question}")
            print("🤖 Jarvis: ", end="", flush=True)
            response = rag_controller.stream_response(args.question)
            sys.exit(0)
        
        # Interactive mode (default)
        interactive_chat(rag_controller)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
