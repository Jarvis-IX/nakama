# scripts/debug_insert.py

import sys
import os
from pathlib import Path
import logging

# --- Setup Paths and Logging ---
# Add project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Import Services ---
# We import here after setting up the path
from services.database_service import DatabaseService
from services.embedding_service import EmbeddingService


def main():
    """Main function to run the debug test."""
    logger.info("🚀 Starting insertion debug script...")

    try:
        # --- 1. Initialize Services (with Dependency Injection) ---
        logger.info("Initializing services...")
        # Create the dependency first
        embedding_service = EmbeddingService()
        # Inject it into the service that needs it
        db_service = DatabaseService(embedding_service=embedding_service)
        logger.info("Services initialized successfully.")

        # --- 2. Create Test Data ---
        # This simulates the data created by chunking a file.
        test_documents = [
            {
                "content": "This is the first test document for our debug script.",
                "metadata": {"source": "debug_script.py"}
            },
            {
                "content": "This is the second test document, designed to ensure batching works.",
                "metadata": {"source": "debug_script.py"}
            }
        ]
        logger.info(f"Created {len(test_documents)} test documents.")

        # --- 3. Call the Batch Insert Function ---
        # This is the function we want to test.
        logger.info("Calling batch_insert_documents()...")



        success = db_service.batch_insert_documents(test_documents)

        # --- 4. Report Result ---
        if success:
            logger.info("✅✅✅ Batch insert successful! ✅✅✅")
        else:
            logger.error("❌❌❌ Batch insert failed! ❌❌❌")

    except Exception as e:
        logger.error("An unexpected error occurred in the main script execution!", exc_info=True)

if __name__ == "__main__":
    main()
