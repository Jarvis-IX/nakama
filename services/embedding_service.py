"""
Embedding Service for Jarvis AI Assistant
Handles text embedding generation using all-MiniLM-L6-v2
"""

from sentence_transformers import SentenceTransformer
from typing import List
import logging
import numpy as np
import os
import torch
from utils.memory_optimizer import memory_optimizer, memory_profile

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service
        
        Args:
            model_name: SentenceTransformers model name
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model with CPU optimizations"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")

            # Dynamically set CPU optimization settings based on available cores
            try:
                threads = str(os.cpu_count() or 4) # Default to 4 if detection fails
                os.environ['OMP_NUM_THREADS'] = threads
                os.environ['MKL_NUM_THREADS'] = threads
                torch.set_num_threads(int(threads))
                logger.info(f"Set CPU threads for torch/MKL/OMP to {threads}")
            except Exception as thread_e:
                logger.warning(f"Could not set CPU thread counts: {thread_e}")

            # Load model with CPU-specific optimizations
            self.model = SentenceTransformer(self.model_name, device='cpu')

            # Enable CPU optimizations
            if hasattr(torch.backends, 'mkldnn') and torch.backends.mkldnn.is_available():
                logger.info("MKL-DNN optimization enabled for CPU")

            logger.info("Embedding model loaded successfully with CPU optimizations")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to load embedding model: {self.model_name}") from e
    
    @memory_profile
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text with caching
        
        Args:
            text: Input text
            
        Returns:
            384-dimension embedding as list
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        # Check cache first
        # cached_embedding = memory_optimizer.get_cached_embedding(text)
        # if cached_embedding is not None:
        #     logger.debug("Retrieved embedding from cache")
        #     return cached_embedding
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            embedding_list = embedding.tolist()
            
            # Cache the result
            # memory_optimizer.cache_embedding(text, embedding_list)
            
            return embedding_list
        except Exception as e:
            logger.error(f"Error generating embedding for text: '{text[:50]}...': {e}", exc_info=True)
            raise RuntimeError("Failed to generate embedding") from e
    
    @memory_profile
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with optimized batching and caching
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing (optimized for CPU)
            
        Returns:
            List of 384-dimension embeddings
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        try:
            all_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            # This logic is optimized to avoid re-calculating embeddings for texts
            # that are already in the cache. It first separates cached vs. uncached
            # texts, processes only the uncached ones, and then merges the results.
            for i, text in enumerate(texts):
                cached_embedding = memory_optimizer.get_cached_embedding(text)
                if cached_embedding is not None:
                    all_embeddings.append(cached_embedding)
                else:
                    all_embeddings.append(None)  # Placeholder
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # Process uncached texts in batches
            if uncached_texts:
                logger.debug(f"Processing {len(uncached_texts)} uncached embeddings")
                uncached_embeddings = []
                
                for i in range(0, len(uncached_texts), batch_size):
                    batch_texts = uncached_texts[i:i + batch_size]
                    batch_embeddings = self.model.encode(
                        batch_texts,
                        batch_size=min(batch_size, len(batch_texts)),
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=True
                    )
                    
                    batch_list = [embedding.tolist() for embedding in batch_embeddings]
                    uncached_embeddings.extend(batch_list)
                    
                    # Cache the new embeddings
                    for j, text in enumerate(batch_texts):
                        memory_optimizer.cache_embedding(text, batch_list[j])
                
                # Fill in the uncached embeddings
                for i, embedding in enumerate(uncached_embeddings):
                    all_embeddings[uncached_indices[i]] = embedding
            
            # Trigger garbage collection after large batch processing
            if len(texts) > 100:
                memory_optimizer.optimize_gc()
            
            return all_embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError("Failed to generate batch embeddings") from e
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}", exc_info=True)
            raise RuntimeError("Failed to calculate similarity") from e
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        if not self.model:
            return {
                "model_name": self.model_name,
                "is_loaded": False
            }
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
            "max_sequence_length": self.model.get_max_seq_length(),
            "is_loaded": True
        }
