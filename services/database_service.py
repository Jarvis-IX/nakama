"""
Database Service for Jarvis AI Assistant
Handles Supabase database operations and vector search
"""

import os
import time
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, embedding_service):
        """
        Initialize the Supabase client.

        Args:
            embedding_service: An initialized instance of EmbeddingService.
        """
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be provided")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.embedding_service = embedding_service  # Dependency Injection
        logger.info("Database service initialized")

    def insert_document(self, content: str, metadata: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Insert a document with its embedding.
        The embedding is generated automatically by this method.

        Args:
            content: Document content
            metadata: Optional metadata

        Returns:
            Inserted document data or None if failed
        """

        try:
            logger.info(f"Generating embedding for: {content[:50]}...")
            start_time_embed = time.time()
            embedding = self.embedding_service.generate_embedding(content)
            end_time_embed = time.time()
            logger.info(f"Single embedding generation took {end_time_embed - start_time_embed:.4f} seconds")

            data = {
                'content': content,
                'embedding': embedding,
                'metadata': metadata or {}
            }
            
            logger.info(f"Inserting single document into Supabase")
            start_time_insert = time.time()
            result = self.client.table('documents').insert(data).execute()
            end_time_insert = time.time()
            logger.info(f"Single Supabase insert took {end_time_insert - start_time_insert:.4f} seconds")
            
            if result.data:
                logger.info(f"Inserted document: {content[:50]}...")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error inserting document: {e}", exc_info=True)
            return None

    def batch_insert_documents(self, documents: List[Dict[str, Any]], batch_size: int = 50) -> bool:
        """
        Insert multiple documents in batches with their embeddings.

        Args:
            documents: A list of documents, where each document is a dictionary
                       (e.g., {'content': '...', 'metadata': {...}}).
            batch_size: The number of documents to process in each batch.

        Returns:
            True if all batches were inserted successfully, False otherwise.
        """
        if self.embedding_service is None:
            raise ValueError("Embedding service is not initialized. It must be provided during DatabaseService instantiation.")

        total_docs = len(documents)
        num_batches = (total_docs + batch_size - 1) // batch_size
        logger.info(f"Starting batch insert of {total_docs} documents in {num_batches} batches.")

        try:
            for i in range(0, total_docs, batch_size):
                batch_num = (i // batch_size) + 1
                batch_docs = documents[i:i + batch_size]
                
                # 1. Generate embeddings for the batch
                logger.info(f"Generating embeddings for batch {batch_num}/{num_batches}")
                start_time_embed = time.time()
                contents = [doc['content'] for doc in batch_docs]
                embeddings = self.embedding_service.generate_embeddings_batch(contents)
                end_time_embed = time.time()
                logger.info(f"Embedding generation for batch {batch_num} took {end_time_embed - start_time_embed:.4f} seconds")

                # 2. Prepare documents for insertion
                docs_to_insert = []
                for j, doc in enumerate(batch_docs):
                    docs_to_insert.append({
                        'content': doc['content'],
                        'embedding': embeddings[j],
                        'metadata': doc.get('metadata', {})
                    })

                # 3. Insert the batch into Supabase
                logger.info(f"Inserting batch {batch_num}/{num_batches} into Supabase")
                start_time_insert = time.time()
                response = self.client.table("documents").insert(docs_to_insert).execute()
                end_time_insert = time.time()
                logger.info(f"Supabase insert for batch {batch_num} took {end_time_insert - start_time_insert:.4f} seconds")
                
                if not response.data:
                    logger.error(f"Failed to insert batch {batch_num}. Response: {response.error}")
                    return False
            
            logger.info(f"Successfully inserted {total_docs} documents.")
            return True

        except Exception as e:
            logger.error(f"An error occurred during batch insert: {e}", exc_info=True)
            return False

    def search_similar_documents(self, 
                               query_embedding: List[float], 
                               limit: int = 5, 
                               similarity_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar documents with similarity scores
        """
        try:
            # Try using RPC function first
            result = self.client.rpc('search_documents_cosine', {
                'query_embedding': query_embedding,
                'similarity_threshold': similarity_threshold,
                'max_results': limit
            }).execute()
            
            if result.data:
                logger.info(f"Found {len(result.data)} similar documents")
                return result.data
            else:
                # Fallback to lower threshold
                logger.info("No results with current threshold, trying lower threshold...")
                result = self.client.rpc('search_documents_cosine', {
                    'query_embedding': query_embedding,
                    'similarity_threshold': 0.3,
                    'max_results': limit
                }).execute()
                return result.data if result.data else []
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            # Fallback to simple query
            return self._fallback_search(limit)

    def _fallback_search(self, limit: int) -> List[Dict[str, Any]]:
        """Fallback search when RPC function is not available"""
        try:
            result = self.client.table('documents').select('*').limit(limit).execute()
            
            if result.data:
                documents = []
                for doc in result.data:
                    documents.append({
                        'id': doc['id'],
                        'content': doc['content'],
                        'similarity': 0.5,  # Placeholder similarity
                        'created_at': doc.get('created_at')
                    })
                return documents
            return []
        except Exception as e:
            logger.error(f"Fallback search failed: {e}", exc_info=True)
            return []

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by ID
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table('documents').delete().eq('id', document_id).execute()
            
            if result.data:
                logger.info(f"Deleted document: {document_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}", exc_info=True)
            return False

    def get_document_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with database statistics
        """
        try:
            # Try using RPC function
            result = self.client.rpc('get_document_stats').execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                # Fallback to manual count
                count_result = self.client.table('documents').select('id', count='exact').execute()
                return {
                    'total_documents': count_result.count or 0,
                    'avg_content_length': 0,
                    'latest_document': None
                }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            return {
                'total_documents': 0,
                'avg_content_length': 0,
                'latest_document': None,
                'error': str(e)
            }

    def update_document(self, document_id: str, content: str, embedding: List[float]) -> bool:
        """
        Update an existing document
        
        Args:
            document_id: Document UUID
            content: New content
            embedding: New embedding
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table('documents').update({
                'content': content,
                'embedding': embedding,
                'updated_at': 'now()'
            }).eq('id', document_id).execute()
            
            if result.data:
                logger.info(f"Updated document: {document_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating document: {e}", exc_info=True)
            return False

    def health_check(self) -> bool:
        """
        Check if database connection is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            result = self.client.table('documents').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}", exc_info=True)
            return False
