"""
File utilities for Jarvis AI Assistant
Handles file operations and document processing
"""

import os
import json
import re
import tempfile
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import pypdf
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory_path: Path to directory
        
    Returns:
        True if directory exists or was created
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {e}", exc_info=True)
        return False

def read_text_file(file_path: str) -> Optional[str]:
    """
    Read text file content
    
    Args:
        file_path: Path to text file
        
    Returns:
        File content or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}", exc_info=True)
        return None

def read_pdf_file(file_path: str) -> Optional[str]:
    """
    Read PDF file content
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content or None if error
    """
    try:
        with open(file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            if reader.is_encrypted:
                logger.warning(f"Skipping encrypted PDF file: {file_path}")
                return None
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
    except PdfReadError as e:
        logger.error(f"Invalid or corrupted PDF file {file_path}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error reading PDF file {file_path}: {e}", exc_info=True)
        return None

def write_text_file(file_path: str, content: str) -> bool:
    """
    Write content to text file
    
    Args:
        file_path: Path to output file
        content: Content to write
        
    Returns:
        True if successful
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory_exists(directory)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}", exc_info=True)
        return False

def save_json(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Save data as JSON file
    
    Args:
        file_path: Path to output file
        data: Data to save
        
    Returns:
        True if successful
    """
    try:
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory_exists(directory)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}", exc_info=True)
        return False

def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON file
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded data or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}", exc_info=True)
        return None

def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes, 0 if error
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}", exc_info=True)
        return 0

def list_files_in_directory(directory_path: str, 
                          extension: Optional[str] = None,
                          recursive: bool = False) -> List[str]:
    """
    List files in directory
    
    Args:
        directory_path: Directory to search
        extension: File extension filter (e.g., '.txt')
        recursive: Search subdirectories
        
    Returns:
        List of file paths
    """
    try:
        path = Path(directory_path)
        if not path.is_dir():
            logger.warning(f"Directory not found: {directory_path}")
            return []

        pattern = f"**/*{extension}" if extension else "**/*"
        if not recursive:
            # For non-recursive, glob directly in the directory
            return [str(f) for f in path.glob(f"*{extension}" if extension else "*") if f.is_file()]
        else:
            # For recursive, use rglob
            return [str(f) for f in path.rglob(f"*{extension}" if extension else "*") if f.is_file()]

    except Exception as e:
        logger.error(f"Error listing files in {directory_path}: {e}", exc_info=True)
        return []

def delete_file(file_path: str) -> bool:
    """
    Delete a file
    
    Args:
        file_path: Path to file
        
    Returns:
        True if successful
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}", exc_info=True)
        return False

def create_temp_file(content: str, suffix: str = '.txt') -> Optional[str]:
    """
    Create temporary file with content
    
    Args:
        content: Content to write
        suffix: File suffix
        
    Returns:
        Path to temporary file or None if error
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as temp_file:
            temp_file.write(content)
            return temp_file.name
    except Exception as e:
        logger.error(f"Error creating temp file: {e}", exc_info=True)
        return None

def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24) -> int:
    """
    Clean up old temporary files
    
    Args:
        temp_dir: Temporary directory path
        max_age_hours: Maximum age in hours
        
    Returns:
        Number of files deleted
    """
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for file_path in list_files_in_directory(temp_dir):
            try:
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    if delete_file(file_path):
                        deleted_count += 1
            except Exception as e:
                logger.warning(f"Error checking file age for {file_path}: {e}", exc_info=True)
        
        logger.info(f"Cleaned up {deleted_count} temporary files")
        return deleted_count
    except Exception as e:
        logger.error(f"Error during temp file cleanup: {e}", exc_info=True)
        return 0

def get_file_extension(file_path: str) -> str:
    """
    Get file extension
    
    Args:
        file_path: Path to file
        
    Returns:
        File extension (including dot)
    """
    return os.path.splitext(file_path)[1].lower()

def is_text_file(file_path: str) -> bool:
    """
    Check if file is a text file based on extension
    
    Args:
        file_path: Path to file
        
    Returns:
        True if text file
    """
    text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv'}
    return get_file_extension(file_path) in text_extensions

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'untitled'
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_length = 255 - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename
