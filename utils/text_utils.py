"""
Text utilities for Jarvis AI Assistant
Handles text processing, chunking, and cleaning functions
"""

import re
import textwrap
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Using a constant for stop words improves maintainability
_STOP_WORDS = {
    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
    'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
    'those', 'you', 'your', 'yours', 'yourself', 'yourselves', 'him', 'his',
    'himself', 'she', 'her', 'hers', 'herself', 'its', 'itself', 'they',
    'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
    'whose', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same',
    'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
    'did', 'a', 'an', 'not', 'so', 'if'
}

def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    try:
        if not isinstance(text, str):
            logger.warning("clean_text received non-string input.")
            return ""
        
        # Normalize whitespace: replace multiple spaces, tabs, newlines with a single space
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove non-printable characters except for basic punctuation
        text = re.sub(r'[^\x20-\x7E]', '', text)
        
        return text
    except Exception as e:
        logger.error(f"Error cleaning text: {e}", exc_info=True)
        return text # Return original text on error

def chunk_text(text: str, 
               chunk_size: int = 500, 
               overlap: int = 50,
               preserve_sentences: bool = True) -> List[str]:
    """
    Split text into chunks for embedding
    
    Args:
        text: Input text
        chunk_size: Maximum characters per chunk
        overlap: Characters to overlap between chunks
        preserve_sentences: Try to preserve sentence boundaries
        
    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    
    if preserve_sentences:
        # Split by sentences first
        sentences = split_into_sentences(text)
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
    else:
        # Simple character-based chunking
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap if overlap > 0 else end
    
    return [chunk for chunk in chunks if chunk.strip()]

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    try:
        # Improved regex to handle abbreviations like Mr., e.g., etc.
        # It splits on '.', '!', '?' not preceded by a known abbreviation prefix.
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.!?])\s', text)
        return [s.strip() for s in sentences if s.strip()]
    except Exception as e:
        logger.error(f"Error splitting sentences: {e}", exc_info=True)
        return [text] if text else [] # Fallback to returning the whole text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text (simple implementation)
    
    Args:
        text: Input text
        max_keywords: Maximum number of keywords
        
    Returns:
        List of keywords
    """
    try:
        # Simple keyword extraction (can be improved with NLP libraries)
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        # Remove common stop words from the predefined set
        keywords = [word for word in words if word not in _STOP_WORDS]
        
        # Count frequency and return most common
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:max_keywords]]
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}", exc_info=True)
        return []

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    try:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    except Exception as e:
        logger.error(f"Error truncating text: {e}", exc_info=True)
        return text # Return original on error

def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    try:
        # Replace multiple whitespace characters (space, tab, newline) with a single space
        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e:
        logger.error(f"Error normalizing whitespace: {e}", exc_info=True)
        return text

def count_words(text: str) -> int:
    """
    Count words in text
    
    Args:
        text: Input text
        
    Returns:
        Word count
    """
    try:
        words = re.findall(r'\b\w+\b', text)
        return len(words)
    except Exception as e:
        logger.error(f"Error counting words: {e}", exc_info=True)
        return 0

def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estimate reading time in minutes
    
    Args:
        text: Input text
        words_per_minute: Average reading speed
        
    Returns:
        Estimated reading time in minutes
    """
    try:
        word_count = count_words(text)
        if words_per_minute <= 0:
            return 0
        return max(1, round(word_count / words_per_minute))
    except Exception as e:
        logger.error(f"Error estimating reading time: {e}", exc_info=True)
        return 0

def format_for_display(text: str, max_line_length: int = 80) -> str:
    """
    Format text for display with line wrapping
    
    Args:
        text: Input text
        max_line_length: Maximum characters per line
        
    Returns:
        Formatted text
    """
    try:
        # Use the standard library's textwrap for robust line wrapping
        return textwrap.fill(text, width=max_line_length)
    except Exception as e:
        logger.error(f"Error formatting text for display: {e}", exc_info=True)
        return text
