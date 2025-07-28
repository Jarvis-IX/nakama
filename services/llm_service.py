"""
LLM Service for Jarvis AI Assistant
Handles communication with Ollama for local LLM inference
"""

import ollama
from typing import Optional, Dict, Any, List
import logging
import os
from config.performance_config import PerformanceConfig

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model_name: str = "llama3.2:3b", host: str = "http://127.0.0.1:11434"):
        """
        Initialize LLM service
        
        Args:
            model_name: Ollama model to use
            host: Ollama server host
        """
        self.model_name = model_name
        self.host = host
        self.client = None  # Lazy initialization
        logger.info(f"LLM service configured for model: {self.model_name}")
        self.system_prompt = self._get_system_prompt()
        

    
    def _get_system_prompt(self) -> str:
        """Define Jarvis's personality and capabilities"""
        return """You are Jarvis, a helpful AI assistant. You have access to a knowledge base through vector search.

Key traits:
- Be concise and helpful
- Use the provided context to answer questions accurately
- If you don't know something from the context, say so clearly
- Be conversational but professional
- Focus on being useful and actionable

When provided with context from the knowledge base, use it to inform your responses. If the context is not relevant to the question, acknowledge this and provide a general response based on your training."""



    def _get_client(self):
        """Initialize and return the Ollama client, checking for model availability on first call."""
        if self.client is None:
            try:
                logger.info(f"Initializing Ollama client for host: {self.host}")
                self.client = ollama.Client(host=self.host)
                # Check connection and model availability on first use
                available_models = [m['name'] for m in self.client.list()['models']]
                logger.info(f"Successfully connected to Ollama. Available models: {[m['name'] for m in self.client.list()['models']]}")
                if self.model_name not in available_models:
                    logger.warning(f"Model '{self.model_name}' not found. Ollama may attempt to pull it.")
            except Exception as e:
                logger.error(f"Failed to connect to Ollama at {self.host}. Is it running? Error: {e}", exc_info=True)
                self.client = None # Reset on failure
                raise ConnectionError(f"Failed to connect to Ollama at {self.host}") from e
        return self.client

    def generate_response(self, 
                         user_message: str, 
                         context: Optional[List[Dict[str, Any]]] = None,
                         conversation_history: Optional[List[Dict[str, str]]] = None,
                         temperature: float = 0.7,
                         max_tokens: int = 512) -> str:
        """
        Generate a response using the LLM
        
        Args:
            user_message: The user's input message
            context: Retrieved documents from vector search
            conversation_history: Previous conversation turns
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            Generated response from Jarvis
        """
        try:
            prompt = self._build_prompt(user_message, context, conversation_history)
            
            # Prepare messages for the conversation
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history if provided (using performance config limit)
            if conversation_history:
                messages.extend(conversation_history[-PerformanceConfig.MAX_CONVERSATION_HISTORY:])
            
            # Add current user message
            messages.append({"role": "user", "content": prompt})
            
            client = self._get_client()
            if not client:
                return "Error: Could not connect to the LLM service."

            # Generate response with CPU-optimized settings
            response = client.chat(
                model=self.model_name,
                messages=messages,
                options=PerformanceConfig.get_ollama_options(streaming=False)
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return f"I apologize, but I encountered an error: {str(e)}"

    def _build_messages(self, user_message: str, context: Optional[List[Dict[str, Any]]] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """Constructs the list of messages for the Ollama API call."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history (last 6 turns)
        if conversation_history:
            messages.extend(conversation_history[-6:])

        # Build the user's message with context
        context_str = ""
        if context and len(context) > 0:
            context_str += "\n--- Relevant Information from Knowledge Base ---\n"
            for i, doc in enumerate(context, 1):
                content = doc.get('content', '')
                similarity = doc.get('similarity', 0)
                context_str += f"{i}. (Similarity: {similarity:.3f}) {content}\n"
            context_str += "--- End of Relevant Information ---\n"
            user_prompt = f"{context_str}\nUser question: {user_message}"
        else:
            user_prompt = user_message
        
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def stream_response(self, 
                       user_message: str, 
                       context: Optional[List[Dict[str, Any]]] = None,
                       conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Stream response for real-time chat experience
        
        Args:
            user_message: The user's input message
            context: Retrieved documents from vector search
            conversation_history: Previous conversation turns
            
        Yields:
            str: Chunks of the response text.
        """
        try:
            messages = self._build_messages(user_message, context, conversation_history)
            client = self._get_client()

            if not client:
                yield "Error: Could not connect to the LLM service."
                return

            # Stream the response from the LLM
            stream = client.chat(
                model=self.model_name,
                messages=messages,
                stream=True,
                options=PerformanceConfig.get_ollama_options(streaming=True)
            )

            for chunk in stream:
                if 'content' in chunk['message']:
                    yield chunk['message']['content']

            logger.info("Finished iterating over Ollama stream.")

        except Exception as e:
            logger.error(f"Error in streaming response: {e}", exc_info=True)
            yield f"Error: {str(e)}" # Yield error to the stream

    def get_model_info(self) -> dict:
        """Get information about the current model"""
        try:
            models = self.client.list()
            for model in models['models']:
                if model['name'] == self.model_name:
                    return {
                        "name": model['name'],
                        "size": model.get('size', 'Unknown'),
                        "modified_at": model.get('modified_at', 'Unknown'),
                        "available": True
                    }
            return {"name": self.model_name, "available": False}
        except Exception as e:
            logger.error(f"Error getting model info: {e}", exc_info=True)
            return {"name": self.model_name, "available": False, "error": str(e)}
