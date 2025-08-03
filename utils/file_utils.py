"""
File handling utilities
"""
import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional
from config import config

def validate_file_type(filename: str) -> bool:
    """Validate if file type is supported"""
    file_extension = filename.lower().split('.')[-1]
    return file_extension in config.ALLOWED_FILE_TYPES

def validate_file_size(file_size: int) -> bool:
    """Validate if file size is within limits"""
    max_size_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024
    return file_size <= max_size_bytes

def get_file_hash(file_content: bytes) -> str:
    """Generate hash for file content"""
    return hashlib.md5(file_content).hexdigest()

def ensure_upload_directory() -> Path:
    """Ensure upload directory exists"""
    upload_path = Path(config.UPLOAD_FOLDER)
    upload_path.mkdir(exist_ok=True)
    return upload_path

def generate_safe_filename(original_filename: str, file_hash: str) -> str:
    """Generate safe filename with hash"""
    name, extension = os.path.splitext(original_filename)
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"{safe_name}_{file_hash[:8]}{extension}"

def get_file_info(filename: str, file_size: int) -> Tuple[bool, Optional[str], dict]:
    """Get comprehensive file information and validation"""
    info = {
        "filename": filename,
        "size": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "extension": filename.lower().split('.')[-1] if '.' in filename else None
    }
    
    # Validate file type
    if not validate_file_type(filename):
        return False, f"Tipo de arquivo não suportado. Tipos permitidos: {', '.join(config.ALLOWED_FILE_TYPES)}", info
    
    # Validate file size
    if not validate_file_size(file_size):
        return False, f"Arquivo muito grande. Tamanho máximo: {config.MAX_FILE_SIZE_MB}MB", info
    
    return True, None, info