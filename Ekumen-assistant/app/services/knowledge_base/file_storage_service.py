"""
Simple File Storage Service
Handles per-organization file storage with content-based hashing and deduplication
"""

import hashlib
import logging
import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile

from app.core.database import get_async_db
from app.models.knowledge_base import KnowledgeBaseDocument
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FileStorageService:
    """Simple service for managing per-organization file storage with deduplication"""
    
    def __init__(self):
        self.base_upload_dir = Path("uploads/knowledge_base")
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
        
        # File size limits (in bytes)
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.min_file_size = 1  # 1 byte minimum
        
        # Allowed MIME types
        self.allowed_mime_types = {
            'application/pdf',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png',
            'image/tiff'
        }
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def create_org_file_path(self, organization_id: str, file_hash: str) -> Path:
        """
        Create organization-scoped file path: uploads/knowledge_base/{org_id}/{hash[:2]}/{hash[2:4]}/{hash}
        """
        hash_dir_1 = file_hash[:2]
        hash_dir_2 = file_hash[2:4]
        
        path = self.base_upload_dir / organization_id / hash_dir_1 / hash_dir_2
        path.mkdir(parents=True, exist_ok=True)
        
        return path / file_hash
    
    def validate_file(self, file: UploadFile, file_content: bytes) -> Dict[str, Any]:
        """
        Validate file size, MIME type, and other constraints
        """
        file_size = len(file_content)
        
        # Check file size
        if file_size < self.min_file_size:
            return {"valid": False, "error": "File is too small", "error_code": "FILE_TOO_SMALL"}
        
        if file_size > self.max_file_size:
            return {"valid": False, "error": f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB", "error_code": "FILE_TOO_LARGE"}
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type and mime_type not in self.allowed_mime_types:
            return {"valid": False, "error": f"File type not allowed: {mime_type}. Allowed types: {', '.join(self.allowed_mime_types)}", "error_code": "INVALID_FILE_TYPE"}
        
        # Check filename
        if not file.filename or len(file.filename.strip()) == 0:
            return {"valid": False, "error": "Filename is required", "error_code": "MISSING_FILENAME"}
        
        if len(file.filename) > 255:
            return {"valid": False, "error": "Filename too long (max 255 characters)", "error_code": "FILENAME_TOO_LONG"}
        
        return {"valid": True, "mime_type": mime_type, "file_size": file_size}
    
    async def check_duplicate_in_organization(
        self,
        file_hash: str,
        organization_id: str,
        db: AsyncSession
    ) -> Optional[KnowledgeBaseDocument]:
        """
        Check if a file with the same content already exists in the organization
        """
        try:
            result = await db.execute(
                select(KnowledgeBaseDocument)
                .where(
                    and_(
                        KnowledgeBaseDocument.file_hash == file_hash,
                        KnowledgeBaseDocument.organization_id == organization_id
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error checking for duplicate file in organization: {e}")
            return None
    
    async def save_file(
        self,
        file: UploadFile,
        organization_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Save uploaded file with per-organization deduplication and transaction safety
        """
        file_path = None
        try:
            # Read file content
            file_content = await file.read()
            
            # Validate file
            validation = self.validate_file(file, file_content)
            if not validation["valid"]:
                return {
                    "status": "validation_error",
                    "message": validation["error"],
                    "error_code": validation.get("error_code", "VALIDATION_ERROR")
                }
            
            file_size = validation["file_size"]
            mime_type = validation["mime_type"]
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_content)
            
            # Check for duplicates within organization
            existing_document = await self.check_duplicate_in_organization(file_hash, organization_id, db)
            
            if existing_document:
                logger.info(f"Duplicate file detected in organization: {file.filename} (hash: {file_hash[:8]}...)")
                return {
                    "status": "duplicate",
                    "document_id": str(existing_document.id),
                    "message": f"File with identical content already exists: {existing_document.filename}",
                    "existing_filename": existing_document.filename,
                    "file_hash": file_hash,
                    "uploaded_at": existing_document.created_at.isoformat() if existing_document.created_at else None
                }
            
            # Create organization-scoped file path
            file_path = self.create_org_file_path(organization_id, file_hash)
            
            # Save file to disk
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            logger.info(f"File saved successfully: {file_path}")
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "file_hash": file_hash,
                "file_size": file_size,
                "mime_type": mime_type,
                "original_filename": file.filename
            }
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            
            # Clean up file if it was written but operation failed
            if file_path and Path(file_path).exists():
                try:
                    Path(file_path).unlink()
                    logger.info(f"Cleaned up orphaned file: {file_path}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to clean up orphaned file {file_path}: {cleanup_error}")
            
            return {
                "status": "error",
                "message": f"Failed to save file: {str(e)}",
                "error_code": "FILE_SAVE_ERROR"
            }
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    async def verify_file_integrity(
        self,
        file_path: str,
        expected_hash: str
    ) -> Dict[str, Any]:
        """
        Verify file integrity by comparing with stored hash
        """
        try:
            if not Path(file_path).exists():
                return {
                    "valid": False,
                    "error": "File not found",
                    "error_code": "FILE_NOT_FOUND"
                }
            
            with open(file_path, "rb") as f:
                content = f.read()
                actual_hash = self.calculate_file_hash(content)
                
                if actual_hash != expected_hash:
                    logger.warning(f"File integrity check failed for {file_path}: hash mismatch")
                    return {
                        "valid": False,
                        "error": "File integrity check failed - hash mismatch",
                        "error_code": "HASH_MISMATCH",
                        "expected_hash": expected_hash,
                        "actual_hash": actual_hash
                    }
                
                return {
                    "valid": True,
                    "message": "File integrity verified",
                    "file_size": len(content),
                    "hash": actual_hash
                }
                
        except Exception as e:
            logger.error(f"Error verifying file integrity: {e}")
            return {
                "valid": False,
                "error": f"Error verifying file integrity: {str(e)}",
                "error_code": "VERIFICATION_ERROR"
            }
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information without reading the entire file
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                "exists": True,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "is_file": path.is_file()
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None