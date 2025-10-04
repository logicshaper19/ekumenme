"""
Document Processing Service
Handles text extraction from various file formats for knowledge base
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio
from io import BytesIO

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for processing documents and extracting text content"""
    
    def __init__(self):
        pass
    
    async def extract_text_from_file(
        self,
        file_path: str,
        file_type: str,
        filename: str
    ) -> str:
        """
        Extract text content from various file formats
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return f"File not found: {filename}"
            
            # Handle different file types
            if file_type.lower() == 'pdf':
                return await self._extract_pdf_text(file_path)
            elif file_type.lower() in ['txt', 'md']:
                return await self._extract_text_file(file_path)
            elif file_type.lower() in ['docx', 'doc']:
                return await self._extract_docx_text(file_path)
            elif file_type.lower() in ['csv']:
                return await self._extract_csv_text(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return f"Unsupported file type: {file_type}. Filename: {filename}"
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return f"Error processing file: {filename}. Error: {str(e)}"
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            # Try to import PyPDF2 or similar PDF processing library
            try:
                import PyPDF2  # type: ignore
                
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text += page.extract_text() + "\n"
                    
                    return text.strip() if text.strip() else "No text content found in PDF"
                    
            except ImportError:
                logger.warning("PyPDF2 not installed. Using fallback PDF processing.")
                return f"PDF file: {Path(file_path).name}. PDF text extraction requires PyPDF2 library."
                
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return f"Error extracting PDF text: {str(e)}"
    
    async def _extract_text_file(self, file_path: str) -> str:
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Error reading text file: {e}")
                return f"Error reading text file: {str(e)}"
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            try:
                from docx import Document  # type: ignore
                
                doc = Document(file_path)
                text = ""
                
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                
                return text.strip() if text.strip() else "No text content found in DOCX"
                
            except ImportError:
                logger.warning("python-docx not installed. Using fallback DOCX processing.")
                return f"DOCX file: {Path(file_path).name}. DOCX text extraction requires python-docx library."
                
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return f"Error extracting DOCX text: {str(e)}"
    
    async def _extract_csv_text(self, file_path: str) -> str:
        """Extract text from CSV files"""
        try:
            import csv
            
            text = ""
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                
                for row_num, row in enumerate(csv_reader):
                    if row_num == 0:  # Header row
                        text += "Headers: " + ", ".join(row) + "\n"
                    else:
                        text += f"Row {row_num}: " + ", ".join(row) + "\n"
            
            return text.strip() if text.strip() else "No content found in CSV"
            
        except Exception as e:
            logger.error(f"Error extracting CSV text: {e}")
            return f"Error extracting CSV text: {str(e)}"
    
    def split_text_into_chunks(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> list[Dict[str, Any]]:
        """
        Split text into overlapping chunks for vector storage
        """
        if not text or len(text) < chunk_size:
            return [{"content": text, "chunk_start": 0, "chunk_end": len(text)}]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                sentence_endings = ['.', '!', '?', '\n']
                for i in range(end, max(start + chunk_size - 100, start), -1):
                    if text[i] in sentence_endings:
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "chunk_start": start,
                    "chunk_end": end
                })
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
