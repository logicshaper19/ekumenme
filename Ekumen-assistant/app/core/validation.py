"""
File validation utilities for the application
"""

import os
import mimetypes
from fastapi import HTTPException, status, UploadFile

# File validation constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
    'application/rtf'
}

def validate_file_upload(file: UploadFile) -> None:
    """
    Validate uploaded file for security and size constraints
    Raises HTTPException if validation fails
    Utility function - not a FastAPI dependency
    """
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type '{file.content_type}' not allowed"
        )
    
    if file.filename:
        if '..' in file.filename or '/' in file.filename or '\\' in file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename: path traversal not allowed"
            )
        
        if len(file.filename) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename too long (maximum 255 characters)"
            )
