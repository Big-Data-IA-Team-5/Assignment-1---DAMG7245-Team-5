"""
Common utility functions used across multiple modules.

This module contains shared functionality to reduce code duplication
and provide consistent behavior across the application.
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


# Set up logger for common utilities
logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """
    Set up standardized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def run_command_safely(
    cmd: List[str], 
    description: str = "Command",
    capture_output: bool = True,
    check: bool = True
) -> subprocess.CompletedProcess:
    """
    Execute a command safely with proper error handling and logging.
    
    Args:
        cmd: Command and arguments as list
        description: Description for logging
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit
        
    Returns:
        CompletedProcess instance
        
    Raises:
        subprocess.CalledProcessError: If command fails and check=True
    """
    logger.info(f"[{description}] Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check
        )
        
        if result.stdout:
            for line in result.stdout.strip().split('\\n'):
                if line.strip():
                    logger.info(f"[{description}] {line}")
        
        if result.stderr:
            for line in result.stderr.strip().split('\\n'):
                if line.strip():
                    logger.warning(f"[{description}] {line}")
        
        return result
        
    except subprocess.CalledProcessError as e:
        logger.error(f"[{description}] Command failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(f"[{description}] stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"[{description}] stderr: {e.stderr}")
        raise


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def save_json(data: Dict[str, Any], filepath: Union[str, Path], indent: int = 2) -> None:
    """
    Save data to JSON file with consistent formatting.
    
    Args:
        data: Data to save
        filepath: Output file path
        indent: JSON indentation level
    """
    filepath = Path(filepath)
    ensure_directory(filepath.parent)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    
    logger.info(f"Saved JSON data to: {filepath}")


def load_json(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Load data from JSON file with error handling.
    
    Args:
        filepath: Input file path
        
    Returns:
        Loaded data dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded JSON data from: {filepath}")
    return data


def clean_filename(filename: str) -> str:
    """
    Clean a filename by removing or replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for filesystem use
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores and whitespace
    filename = filename.strip('_').strip()
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_pdf_path(pdf_path: Union[str, Path]) -> Path:
    """
    Validate that a PDF path exists and is a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Validated Path object
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not a PDF
    """
    path = Path(pdf_path)
    
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    
    if not path.suffix.lower() == '.pdf':
        raise ValueError(f"File is not a PDF: {path}")
    
    return path


class ProgressReporter:
    """Simple progress reporting utility."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
    
    def update(self, increment: int = 1) -> None:
        """Update progress by increment."""
        self.current = min(self.current + increment, self.total)
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        logger.info(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)")
    
    def finish(self) -> None:
        """Mark progress as complete."""
        self.current = self.total
        logger.info(f"{self.description}: Complete!")


# Custom exceptions for better error handling
class ProcessingError(Exception):
    """Base class for processing errors."""
    pass


class ExtractionError(ProcessingError):
    """Error during data extraction."""
    pass


class ValidationError(ProcessingError):
    """Error during data validation."""
    pass


class ConfigurationError(ProcessingError):
    """Error in configuration or setup."""
    pass