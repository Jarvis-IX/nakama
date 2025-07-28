"""
RAG Controller for Jarvis AI Assistant
Orchestrates Retrieval-Augmented Generation pipeline
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import os
import time

# Import services and utilities
from services.embedding_service import EmbeddingService
from services.database_service import DatabaseService
from services.llm_service import LLMService
from utils.file_utils import read_text_file, read_pdf_file
from utils.text_utils import chunk_text

logger = logging.getLogger(__name__)

class RAGController:
    def __init__(self, 
                 embedding_service: EmbeddingService,
                 database_service: DatabaseService,
                 llm_service: LLMService):
        """
        Initialize RAG controller
        
        Args:
            embedding_service: Service for generating embeddings
            database_service: Service for database operations
            llm_service: Service for LLM operations
        """
        self.embedding_service = embedding_service
        self.database_service = database_service
        self.llm_service = llm_service
        
        # Conversation state
        self.conversation_history: List[Dict[str, str]] = []
        
        logger.info("RAG Controller initialized")

    def ask_question(self, 
                    question: str, 
                    use_context: bool = True,
                    similarity_threshold: float = 0.6,
                    max_context_docs: int = 5) -> Dict[str, Any]:
        """
        Process a question using the RAG pipeline
        
        Args:
            question: User's question
            use_context: Whether to retrieve context from knowledge base
            similarity_threshold: Minimum similarity for context retrieval
            max_context_docs: Maximum number of context documents
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            context_docs = []
            
            if use_context:
                # Step 1: Generate embedding for the question
                query_embedding = self.embedding_service.generate_embedding(question)
                
                # Step 2: Retrieve relevant documents
                context_docs = self.database_service.search_similar_documents(
                    query_embedding=query_embedding,
                    limit=max_context_docs,
                    similarity_threshold=similarity_threshold
                )
                
                logger.info(f"Retrieved {len(context_docs)} context documents")
            
            # Step 3: Generate response using LLM
            response = self.llm_service.generate_response(
                user_message=question,
                context=context_docs,
                conversation_history=self.conversation_history
            )
            
            # Step 4: Update conversation history
            self._update_conversation_history(question, response)
            
            return {
                "response": response,
                "context_used": len(context_docs) > 0,
                "context_docs": context_docs
            }
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}", exc_info=True)
            return {"response": f"I encountered an error: {str(e)}", "error": str(e)}

    def stream_response(self, 
                       question: str, 
                       use_context: bool = True,
                       similarity_threshold: float = 0.6,
                       max_context_docs: int = 5):
        """
        Stream response for real-time chat experience
        
        Args:
            question: User's question
            use_context: Whether to retrieve context
            similarity_threshold: Minimum similarity for context
            max_context_docs: Maximum context documents
            
        Yields:
            str: Response chunks from the LLM.
        """
        try:
            logger.info(f"Streaming response for question: '{question}'")
            context_docs = []
            
            if use_context:
                query_embedding = self.embedding_service.generate_embedding(question)
                context_docs = self.database_service.search_similar_documents(
                    query_embedding=query_embedding,
                    limit=max_context_docs,
                    similarity_threshold=similarity_threshold
                )
                logger.info(f"Retrieved {len(context_docs)} context documents for streaming")

            # Step 1: Generate the full response by consuming the stream internally
            response_generator = self.llm_service.stream_response(
                user_message=question,
                context=context_docs,
                conversation_history=self.conversation_history
            )
            full_response = "".join(list(response_generator))

            # Step 2: Update history with the complete and final response
            self._update_conversation_history(question, full_response)

            # Step 3: Yield the response to the client chunk by chunk.
            # This is a simplified way to stream it back. For true low-latency
            # streaming, you'd yield from the original generator and handle
            # history update separately, but this is more robust.
            yield full_response

        except Exception as e:
            logger.error(f"Error streaming response: {e}", exc_info=True)
            yield f"I encountered an error: {str(e)}"
            yield error_message

    def add_knowledge(self, content: str, metadata: Optional[Dict] = None) -> Tuple[bool, int]:
        """
        Add a single piece of text knowledge to the database
        
        Args:
            content: Text content to add
            metadata: Optional metadata
            
        Returns:
            Tuple of success flag and number of documents added
        """
        try:
            # The embedding is now handled by the database service
            result = self.database_service.insert_document(
                content=content,
                metadata=metadata
            )
            if result:
                logger.info(f"Added knowledge: {content[:50]}...")
                return True, 1
            return False, 0
        
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return False, 0

    def batch_add_knowledge(self, documents: List[Dict[str, Any]]) -> Tuple[bool, int]:
        """
        Add multiple documents to the knowledge base
        
        Args:
            documents: List of documents with 'content' and optional 'metadata'
            
        Returns:
            Tuple of success flag and number of documents added
        """
        if not documents:
            return True, 0
        try:
            # The database service now handles batching and embedding
            success = self.database_service.batch_insert_documents(documents)
            if success:
                count = len(documents)
                logger.info(f"Added {count} documents to knowledge base")
                return True, count
            return False, 0
        except Exception as e:
            logger.error(f"Error in batch add knowledge: {e}", exc_info=True)
            return False, 0

    def add_file_knowledge(self, file_path: str) -> Tuple[bool, int]:
        """
        Add knowledge from a file by reading, chunking, and batch inserting it
        
        Args:
            file_path: Path to the file to add knowledge from
            
        Returns:
            Tuple of success flag and number of documents added
        """
        try:
            content = ""
            if file_path.endswith(('.txt', '.md')):
                content = read_text_file(file_path)
            elif file_path.endswith('.pdf'):
                content = read_pdf_file(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return False, 0

            if not content:
                logger.error(f"Could not read content from file: {file_path}")
                return False, 0

            chunks = chunk_text(content, chunk_size=1000, overlap=100)
            source_name = os.path.basename(file_path)
            documents = [
                {"content": chunk, "metadata": {"source": source_name}}
                for chunk in chunks
            ]

            return self.batch_add_knowledge(documents)

        except Exception as e:
            logger.error(f"Failed to add knowledge from file {file_path}: {e}", exc_info=True)
            return False, 0
        finally:
            # Clean up the temporary file after processing
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary file {file_path}: {e}")

    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history"""
        return self.conversation_history.copy()

    def _update_conversation_history(self, question: str, response: str):
        """Update conversation history with new turn"""
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": response})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all system components"""
        try:
            return {
                "embedding_service": self.embedding_service.get_model_info(),
                "llm_service": self.llm_service.get_model_info(),
                "database_service": {
                    "healthy": self.database_service.health_check(),
                    "stats": self.database_service.get_document_stats()
                },
                "conversation_turns": len(self.conversation_history) // 2
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
