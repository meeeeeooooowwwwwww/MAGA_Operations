#!/usr/bin/env python3
"""
File Utility Module.

Provides functions for file operations including reading, writing, and processing files.
Supports various file formats and operations.
"""
import os
import json
import csv
import yaml
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO, TextIO, Callable, Iterator

# Import utility modules
from scripts.utils.logger import get_logger

# Initialize logger
logger = get_logger("file_utils")

def ensure_dir(directory: str) -> str:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory (str): Directory path
        
    Returns:
        str: Directory path
    """
    os.makedirs(directory, exist_ok=True)
    return directory

def get_file_hash(file_path: str, algorithm: str = "sha256", buffer_size: int = 65536) -> str:
    """
    Calculate hash of a file.
    
    Args:
        file_path (str): Path to file
        algorithm (str, optional): Hash algorithm (md5, sha1, sha256, sha512)
        buffer_size (int, optional): Read buffer size
        
    Returns:
        str: File hash
    """
    # Select hash algorithm
    if algorithm == "md5":
        hash_obj = hashlib.md5()
    elif algorithm == "sha1":
        hash_obj = hashlib.sha1()
    elif algorithm == "sha256":
        hash_obj = hashlib.sha256()
    elif algorithm == "sha512":
        hash_obj = hashlib.sha512()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    # Calculate hash
    with open(file_path, "rb") as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            hash_obj.update(data)
    
    return hash_obj.hexdigest()

def read_file(file_path: str, mode: str = "r", encoding: str = "utf-8") -> str:
    """
    Read entire file as text.
    
    Args:
        file_path (str): Path to file
        mode (str, optional): File mode
        encoding (str, optional): File encoding
        
    Returns:
        str: File contents
    """
    with open(file_path, mode=mode, encoding=encoding if "b" not in mode else None) as f:
        return f.read()

def write_file(file_path: str, content: str, mode: str = "w", encoding: str = "utf-8") -> None:
    """
    Write text to file.
    
    Args:
        file_path (str): Path to file
        content (str): Content to write
        mode (str, optional): File mode
        encoding (str, optional): File encoding
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    with open(file_path, mode=mode, encoding=encoding if "b" not in mode else None) as f:
        f.write(content)

def read_json(file_path: str) -> Any:
    """
    Read JSON file.
    
    Args:
        file_path (str): Path to file
        
    Returns:
        any: Parsed JSON data
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(file_path: str, data: Any, indent: int = 2, ensure_ascii: bool = False) -> None:
    """
    Write data to JSON file.
    
    Args:
        file_path (str): Path to file
        data (any): Data to write
        indent (int, optional): JSON indentation
        ensure_ascii (bool, optional): Ensure ASCII encoding
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

def read_yaml(file_path: str) -> Any:
    """
    Read YAML file.
    
    Args:
        file_path (str): Path to file
        
    Returns:
        any: Parsed YAML data
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def write_yaml(file_path: str, data: Any) -> None:
    """
    Write data to YAML file.
    
    Args:
        file_path (str): Path to file
        data (any): Data to write
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)

def read_csv(file_path: str, delimiter: str = ",", has_header: bool = True) -> List[Dict[str, str]]:
    """
    Read CSV file.
    
    Args:
        file_path (str): Path to file
        delimiter (str, optional): CSV delimiter
        has_header (bool, optional): Whether CSV has header row
        
    Returns:
        list: List of dictionaries for each row
    """
    rows = []
    
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        if has_header:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                rows.append(dict(row))
        else:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                rows.append(row)
    
    return rows

def write_csv(file_path: str, data: List[Dict[str, Any]], fieldnames: List[str] = None, delimiter: str = ",") -> None:
    """
    Write data to CSV file.
    
    Args:
        file_path (str): Path to file
        data (list): List of dictionaries or lists to write
        fieldnames (list, optional): Field names for header
        delimiter (str, optional): CSV delimiter
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        # Determine field names if not provided
        if fieldnames is None and data:
            if isinstance(data[0], dict):
                fieldnames = list(data[0].keys())
        
        if fieldnames:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            
            for row in data:
                writer.writerow(row)
        else:
            writer = csv.writer(f, delimiter=delimiter)
            
            for row in data:
                writer.writerow(row)

def copy_file(src: str, dst: str, preserve_metadata: bool = True) -> str:
    """
    Copy file from source to destination.
    
    Args:
        src (str): Source path
        dst (str): Destination path
        preserve_metadata (bool, optional): Preserve file metadata
        
    Returns:
        str: Destination path
    """
    # Create destination directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    
    if preserve_metadata:
        return shutil.copy2(src, dst)
    else:
        return shutil.copy(src, dst)

def move_file(src: str, dst: str) -> str:
    """
    Move file from source to destination.
    
    Args:
        src (str): Source path
        dst (str): Destination path
        
    Returns:
        str: Destination path
    """
    # Create destination directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    
    return shutil.move(src, dst)

def safe_delete(path: str) -> bool:
    """
    Safely delete file or directory.
    
    Args:
        path (str): Path to delete
        
    Returns:
        bool: True if deleted, False otherwise
    """
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
        else:
            return False
        return True
    except Exception as e:
        logger.error(f"Error deleting {path}: {e}")
        return False

def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> List[str]:
    """
    List files in directory matching pattern.
    
    Args:
        directory (str): Directory path
        pattern (str, optional): Glob pattern
        recursive (bool, optional): Whether to search recursively
        
    Returns:
        list: List of file paths
    """
    path = Path(directory)
    
    if recursive:
        return [str(file) for file in path.glob(f"**/{pattern}") if file.is_file()]
    else:
        return [str(file) for file in path.glob(pattern) if file.is_file()]

def get_file_size(file_path: str, human_readable: bool = False) -> Union[int, str]:
    """
    Get file size.
    
    Args:
        file_path (str): Path to file
        human_readable (bool, optional): Return human-readable size
        
    Returns:
        int or str: File size
    """
    size = os.path.getsize(file_path)
    
    if not human_readable:
        return size
    
    # Convert to human-readable format
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{size:.2f}{unit}"
        size /= 1024

def get_file_extension(file_path: str) -> str:
    """
    Get file extension.
    
    Args:
        file_path (str): Path to file
        
    Returns:
        str: File extension
    """
    return os.path.splitext(file_path)[1]

def atomic_write(file_path: str, write_func: Callable[[TextIO], None], mode: str = "w", encoding: str = "utf-8") -> None:
    """
    Atomically write to file.
    
    Args:
        file_path (str): Path to file
        write_func: Function to write to file
        mode (str, optional): File mode
        encoding (str, optional): File encoding
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    # Create temporary file
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(file_path)))
    
    try:
        # Write to temporary file
        with os.fdopen(fd, mode, encoding=encoding if "b" not in mode else None) as f:
            write_func(f)
        
        # Replace target file with temporary file
        shutil.move(temp_path, file_path)
    except Exception:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

def read_chunks(file_path: str, chunk_size: int = 8192) -> Iterator[bytes]:
    """
    Read file in chunks.
    
    Args:
        file_path (str): Path to file
        chunk_size (int, optional): Chunk size
        
    Yields:
        bytes: File chunk
    """
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def backup_file(file_path: str, backup_dir: str = None, suffix: str = None) -> str:
    """
    Create a backup of a file.
    
    Args:
        file_path (str): Path to file
        backup_dir (str, optional): Backup directory
        suffix (str, optional): Backup file suffix
        
    Returns:
        str: Backup file path
    """
    # Generate backup path
    if backup_dir is None:
        backup_dir = os.path.dirname(file_path)
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename
    base_name = os.path.basename(file_path)
    if suffix is None:
        import datetime
        suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    backup_name = f"{os.path.splitext(base_name)[0]}_{suffix}{os.path.splitext(base_name)[1]}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Copy file
    shutil.copy2(file_path, backup_path)
    
    return backup_path

if __name__ == "__main__":
    # Test file utilities
    import tempfile
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test write_file and read_file
        test_file = os.path.join(temp_dir, "test.txt")
        write_file(test_file, "Hello, world!")
        content = read_file(test_file)
        print(f"read_file: {content}")
        
        # Test write_json and read_json
        test_json = os.path.join(temp_dir, "test.json")
        data = {"name": "John", "age": 30, "city": "New York"}
        write_json(test_json, data)
        json_data = read_json(test_json)
        print(f"read_json: {json_data}")
        
        # Test write_csv and read_csv
        test_csv = os.path.join(temp_dir, "test.csv")
        csv_data = [
            {"name": "John", "age": "30", "city": "New York"},
            {"name": "Jane", "age": "25", "city": "Boston"},
            {"name": "Bob", "age": "40", "city": "Chicago"}
        ]
        write_csv(test_csv, csv_data)
        csv_rows = read_csv(test_csv)
        print(f"read_csv: {csv_rows}")
        
        # Test file operations
        backup_path = backup_file(test_file, temp_dir)
        print(f"backup_file: {backup_path}")
        
        file_size = get_file_size(test_file, human_readable=True)
        print(f"get_file_size: {file_size}")
        
        file_hash = get_file_hash(test_file)
        print(f"get_file_hash: {file_hash}")
        
        # Test directory operations
        files = list_files(temp_dir)
        print(f"list_files: {files}") 