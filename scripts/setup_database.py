#!/usr/bin/env python3
"""
Database Setup Script for Jarvis AI Assistant
Initializes Supabase database with required tables and functions
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.database_service import DatabaseService
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database tables and functions"""
    print("🔧 Setting up Jarvis database...")
    
    try:
        # Initialize database service
        db_service = DatabaseService()
        
        # Test connection
        print("📡 Testing database connection...")
        if not db_service.health_check():
            print("❌ Database connection failed!")
            return False
        
        print("✅ Database connection successful!")
        
        # Get current stats
        stats = db_service.get_document_stats()
        print(f"📊 Current database stats: {stats}")
        
        # Add some initial test data if database is empty
        if stats.get('total_documents', 0) == 0:
            print("📚 Adding initial test knowledge...")
            
            test_documents = [
                {
                    "content": "Jarvis is an AI assistant built with open-source technologies including Supabase, Ollama, and SentenceTransformers.",
                    "metadata": {"source": "system", "category": "about"}
                },
                {
                    "content": "The system uses all-MiniLM-L6-v2 for generating 384-dimension embeddings, which are optimized for CPU-only inference.",
                    "metadata": {"source": "system", "category": "technical"}
                },
                {
                    "content": "Jarvis can answer questions by searching through a knowledge base using vector similarity and generating responses with a local LLM.",
                    "metadata": {"source": "system", "category": "capabilities"}
                },
                {
                    "content": "The system is designed to run on modest hardware like Intel Core i5 with 16GB RAM, making it accessible for personal use.",
                    "metadata": {"source": "system", "category": "requirements"}
                }
            ]
            
            # We need to generate embeddings for these documents
            from services.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            
            for doc in test_documents:
                embedding = embedding_service.generate_embedding(doc["content"])
                result = db_service.insert_document(
                    content=doc["content"],
                    embedding=embedding,
                    metadata=doc.get("metadata")
                )
                
                if result:
                    print(f"✅ Added: {doc['content'][:50]}...")
                else:
                    print(f"❌ Failed to add: {doc['content'][:50]}...")
        
        # Final stats
        final_stats = db_service.get_document_stats()
        print(f"📊 Final database stats: {final_stats}")
        
        print("🎉 Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        print(f"❌ Database setup failed: {e}")
        return False

def create_rpc_functions():
    """Instructions for creating RPC functions in Supabase"""
    print("\n📋 Manual Setup Required:")
    print("=" * 50)
    print("Please run the following SQL in your Supabase SQL Editor:")
    print("\n1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run the contents of 'setup_rpc_functions.sql'")
    print("\nThis will create the necessary RPC functions for vector search.")
    print("=" * 50)

def main():
    """Main entry point"""
    print("🚀 Jarvis Database Setup")
    print("=" * 30)
    
    # Check environment variables
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        print("❌ Missing environment variables!")
        print("Please ensure SUPABASE_URL and SUPABASE_KEY are set in your .env file")
        sys.exit(1)
    
    # Setup database
    success = setup_database()
    
    if success:
        # Show RPC function setup instructions
        create_rpc_functions()
        print("\n✅ Database setup completed!")
        print("🎯 Next steps:")
        print("1. Run the RPC functions SQL as shown above")
        print("2. Test with: python scripts/main.py --test")
        print("3. Start chatting: python scripts/main.py")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
