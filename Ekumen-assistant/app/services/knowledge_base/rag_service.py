"""
RAG Service with Knowledge Base Workflow Integration
Integrates with the vetted, time-bound knowledge contribution system
Enhanced with detailed source tracking and attribution
"""

import logging
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, AsyncIterator, Tuple
from datetime import datetime, timedelta
import json
import re

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.config import settings
from app.models.knowledge_base import KnowledgeBaseDocument, DocumentStatus
from .knowledge_base_workflow_service import KnowledgeBaseWorkflowService

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG service that integrates with the knowledge base workflow
    Filters documents by expiration, approval status, and organization permissions
    """
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.workflow_service = KnowledgeBaseWorkflowService()
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize LangChain components"""
        try:
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Initialize vector store
            try:
                from langchain_chroma import Chroma as ChromaNew
                self.vectorstore = ChromaNew(
                    embedding_function=self.embeddings,
                    persist_directory="./chroma_db"
                )
                logger.info("✅ RAG using updated langchain-chroma package")
            except ImportError:
                from langchain.vectorstores import Chroma
                self.vectorstore = Chroma(
                    embedding_function=self.embeddings,
                    persist_directory="./chroma_db"
                )
                logger.warning("⚠️  RAG using deprecated Chroma")
            
            logger.info("✅ RAG Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            raise
    
    async def get_relevant_documents(
        self,
        query: str,
        user_id: str,
        organization_id: str,
        db: AsyncSession,
        k: int = 5,
        include_ekumen_content: bool = True
    ) -> List[Document]:
        """
        Get relevant documents with workflow filtering
        
        Args:
            query: Search query
            user_id: Current user ID (required)
            organization_id: User's organization ID (required)
            db: Database session
            k: Number of documents to retrieve
            include_ekumen_content: Whether to include Ekumen-provided content
            
        Returns:
            List of relevant documents
            
        Raises:
            ValueError: If user_id or organization_id is not provided
        """
        if not user_id or not organization_id:
            raise ValueError("Authentication required: user_id and organization_id must be provided")
        
        if not db:
            raise ValueError("Database session is required")
        
        # Check cache first
        cache_key = self._generate_cache_key(query, user_id, organization_id, k, include_ekumen_content)
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < self._cache_ttl:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached_result
        
        try:
            # First, get all approved, active, non-expired documents the user can access
            accessible_docs = await self._get_accessible_documents(
                user_id, organization_id, db, include_ekumen_content
            )
            
            if not accessible_docs:
                logger.warning("No accessible documents found for user")
                return []
            
            # Create document IDs filter for vector search
            doc_ids = [str(doc.id) for doc in accessible_docs]
            
            # Perform vector search with document filtering
            try:
                # ChromaDB supports metadata filtering with proper syntax
                # Get more results than needed to account for filtering
                search_results = self.vectorstore.similarity_search(
                    query,
                    k=min(k * 3, 50),  # Get more results to filter from
                    filter={"document_id": {"$in": doc_ids}} if doc_ids else None
                )
                
                # Filter results to only include accessible documents
                filtered_results = []
                for doc in search_results:
                    doc_id = doc.metadata.get("document_id")
                    if doc_id in doc_ids:
                        filtered_results.append(doc)
                        if len(filtered_results) >= k:
                            break
                
                search_results = filtered_results
                
                # Enhance documents with workflow metadata
                enhanced_docs = await self._enhance_documents_with_metadata(
                    search_results, accessible_docs, db
                )
                
                # Track document analytics asynchronously (non-blocking)
                asyncio.create_task(
                    self._track_document_analytics_async(enhanced_docs, query)
                )
                
                # Cache the results
                self._cache[cache_key] = (enhanced_docs, datetime.utcnow())
                
                return enhanced_docs
                
            except Exception as e:
                logger.error(f"Vector search error: {e}")
                # Fallback to basic search
                return self.vectorstore.similarity_search(query, k=k)
            
        except Exception as e:
            logger.error(f"Error getting relevant documents: {e}")
            return []
    
    async def _get_accessible_documents(
        self,
        user_id: str,
        organization_id: str,
        db: AsyncSession,
        include_ekumen_content: bool = True
    ) -> List[KnowledgeBaseDocument]:
        """
        Get documents accessible to the authenticated user based on workflow rules
        """
        try:
            # Build query for accessible documents
            query = select(KnowledgeBaseDocument).where(
                and_(
                    # Document must be completed and active
                    KnowledgeBaseDocument.processing_status == DocumentStatus.COMPLETED,
                    KnowledgeBaseDocument.visibility.in_(["shared", "public"]),
                    
                    # Document must not be expired
                    or_(
                        KnowledgeBaseDocument.expiration_date.is_(None),  # No expiration set
                        KnowledgeBaseDocument.expiration_date > datetime.utcnow()
                    ),
                    
                    # Document must be approved
                    KnowledgeBaseDocument.submission_status == "approved"
                )
            )
            
            # Add organization access rules for authenticated users
            access_conditions = []
            
            # User can access their own organization's documents
            access_conditions.append(
                KnowledgeBaseDocument.organization_id == organization_id
            )
            
            # User can access shared documents from other organizations
            access_conditions.append(
                and_(
                    KnowledgeBaseDocument.visibility == "shared",
                    or_(
                        # Shared with all organizations (no specific orgs listed)
                        KnowledgeBaseDocument.shared_with_organizations.is_(None),
                        # Shared with specific organizations including user's org
                        KnowledgeBaseDocument.shared_with_organizations.contains([organization_id])
                    )
                )
            )
            
            # User can access documents shared with them specifically
            access_conditions.append(
                and_(
                    KnowledgeBaseDocument.shared_with_users.isnot(None),
                    KnowledgeBaseDocument.shared_with_users.contains([user_id])
                )
            )
            
            # Include Ekumen-provided content (available to all authenticated users)
            if include_ekumen_content:
                access_conditions.append(
                    KnowledgeBaseDocument.is_ekumen_provided == True
                )
            
            query = query.where(or_(*access_conditions))
            
            result = await db.execute(query)
            documents = result.scalars().all()
            
            logger.info(f"Found {len(documents)} accessible documents for user {user_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting accessible documents: {e}")
            return []
    
    async def _enhance_documents_with_metadata(
        self,
        search_results: List[Document],
        accessible_docs: List[KnowledgeBaseDocument],
        db: AsyncSession
    ) -> List[Document]:
        """
        Enhance search results with workflow metadata
        """
        try:
            # Create lookup for accessible documents
            doc_lookup = {str(doc.id): doc for doc in accessible_docs}
            
            enhanced_docs = []
            for doc in search_results:
                doc_id = doc.metadata.get("document_id")
                if doc_id and doc_id in doc_lookup:
                    kb_doc = doc_lookup[doc_id]
                    
                    # Add workflow metadata
                    doc.metadata.update({
                        "document_type": kb_doc.document_type.value,
                        "organization_id": str(kb_doc.organization_id),
                        "quality_score": kb_doc.quality_score,
                        "version": kb_doc.version,
                        "expiration_date": kb_doc.organization_metadata.get("expiration_date") if kb_doc.organization_metadata else None,
                        "is_ekumen_provided": kb_doc.is_ekumen_provided,
                        "tags": kb_doc.tags or [],
                        "description": kb_doc.description
                    })
                    
                    enhanced_docs.append(doc)
            
            return enhanced_docs
            
        except Exception as e:
            logger.error(f"Error enhancing documents: {e}")
            return search_results
    
    async def add_document_to_vectorstore(
        self,
        document: KnowledgeBaseDocument,
        content: str,
        db: AsyncSession
    ) -> bool:
        """
        Add a document to the vector store after approval
        """
        try:
            # Split content into chunks
            chunks = self._split_text_into_chunks(content)
            
            # Create documents with metadata
            documents = []
            for i, chunk_data in enumerate(chunks):
                doc = Document(
                    page_content=chunk_data["content"],
                    metadata={
                        "document_id": str(document.id),
                        "chunk_index": i,
                        "filename": document.filename,
                        "document_type": document.document_type.value,
                        "organization_id": str(document.organization_id),
                        "uploaded_by": str(document.uploaded_by),
                        "created_at": document.created_at.isoformat(),
                        "version": document.version,
                        "visibility": document.visibility,
                        "is_ekumen_provided": document.is_ekumen_provided,
                        "page_number": chunk_data.get("page_number"),
                        "section": chunk_data.get("section"),
                        "chunk_start": chunk_data.get("chunk_start", 0),
                        "chunk_end": chunk_data.get("chunk_end", 0)
                    }
                )
                documents.append(doc)
            
            # Add to vector store
            self.vectorstore.add_documents(documents)
            
            # Update document record
            document.chunk_count = len(chunks)
            await db.commit()
            
            logger.info(f"Added document {document.id} to vector store with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            return False
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks with page/section mapping for better retrieval
        Returns list of dictionaries with chunk content and metadata
        """
        if len(text) <= chunk_size:
            return [{
                "content": text,
                "page_number": self._extract_page_from_text(text),
                "section": self._extract_section_from_text(text),
                "chunk_start": 0,
                "chunk_end": len(text)
            }]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + chunk_size - 100, start), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "page_number": self._extract_page_from_text(chunk_text),
                    "section": self._extract_section_from_text(chunk_text),
                    "chunk_start": start,
                    "chunk_end": end
                })
            
            start = end - overlap
            
        return chunks
    
    async def remove_document_from_vectorstore(
        self,
        document_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Remove a document from the vector store (e.g., when expired)
        Actually removes chunks from ChromaDB, not just marks as inactive
        """
        try:
            # First, get the document to verify it exists
            result = await db.execute(
                select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.warning(f"Document {document_id} not found for removal")
                return False
            
            # Remove from ChromaDB by querying and deleting chunks with this document_id
            try:
                # Get all chunks for this document
                chunks_to_remove = self.vectorstore.get(
                    where={"document_id": document_id}
                )
                
                if chunks_to_remove and chunks_to_remove.get('ids'):
                    # Delete chunks from ChromaDB
                    self.vectorstore.delete(ids=chunks_to_remove['ids'])
                    logger.info(f"Removed {len(chunks_to_remove['ids'])} chunks from vector store for document {document_id}")
                else:
                    logger.info(f"No chunks found in vector store for document {document_id}")
                    
            except Exception as e:
                logger.error(f"Error removing chunks from ChromaDB: {e}")
                # Fallback: mark as inactive in database
                document.visibility = "internal"
                if document.organization_metadata is None:
                    document.organization_metadata = {}
                document.organization_metadata["deactivated_at"] = datetime.utcnow().isoformat()
                await db.commit()
                return False
            
            # Update document status in database
            document.visibility = "internal"
            if document.organization_metadata is None:
                document.organization_metadata = {}
            document.organization_metadata["deactivated_at"] = datetime.utcnow().isoformat()
            document.organization_metadata["removed_from_vectorstore"] = True
            
            await db.commit()
            
            logger.info(f"Successfully removed document {document_id} from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error removing document from vector store: {e}")
            await db.rollback()
            return False
    
    async def get_document_statistics(
        self,
        organization_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base
        """
        if not db:
            raise ValueError("Database session is required")
            
        try:
            # Build base query
            query = select(KnowledgeBaseDocument)
            
            if organization_id:
                query = query.where(KnowledgeBaseDocument.organization_id == organization_id)
            
            result = await db.execute(query)
            all_docs = result.scalars().all()
            
            # Calculate statistics
            total_docs = len(all_docs)
            active_docs = len([doc for doc in all_docs if doc.is_active and not doc.is_expired])
            expired_docs = len([doc for doc in all_docs if doc.is_expired])
            pending_review = len([doc for doc in all_docs if doc.submission_status == "under_review"])
            
            # Document types breakdown
            type_counts = {}
            for doc in all_docs:
                doc_type = doc.document_type.value
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Quality score distribution
            quality_scores = [doc.quality_score for doc in all_docs if doc.quality_score is not None]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            return {
                "total_documents": total_docs,
                "active_documents": active_docs,
                "expired_documents": expired_docs,
                "pending_review": pending_review,
                "document_types": type_counts,
                "average_quality_score": round(avg_quality, 2),
                "total_chunks": sum(doc.chunk_count or 0 for doc in all_docs)
            }
            
        except Exception as e:
            logger.error(f"Error getting document statistics: {e}")
            return {}
    
    async def _track_document_analytics_async(
        self,
        documents: List[Document],
        query: str = None
    ) -> None:
        """
        Track document analytics asynchronously (non-blocking)
        Creates a new database session for analytics operations
        """
        try:
            from app.core.database import get_async_session
            
            async for db in get_async_session():
                await self._track_document_analytics(documents, db, query)
                break
                
        except Exception as e:
            logger.error(f"Error in async analytics tracking: {e}")

    def _generate_cache_key(self, query: str, user_id: str, organization_id: str, k: int, include_ekumen_content: bool) -> str:
        """Generate a cache key for the query"""
        cache_data = f"{query}:{user_id}:{organization_id}:{k}:{include_ekumen_content}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    async def _track_document_analytics(
        self,
        documents: List[Document],
        db: AsyncSession,
        query: str = None
    ) -> None:
        """
        Track document analytics when documents are retrieved
        Updates query_count, last_accessed_at, and creates analytics records with chunk-level tracking
        """
        try:
            from datetime import datetime
            from sqlalchemy import update
            from app.services.farm_data import AnalyticsService
            from app.models.analytics import AnalyticsEvent
            
            analytics_service = AnalyticsService()
            
            for doc in documents:
                document_id = doc.metadata.get("document_id")
                chunk_index = doc.metadata.get("chunk_index", 0)
                if not document_id:
                    continue
                
                # Update query count and last accessed timestamp
                await db.execute(
                    update(KnowledgeBaseDocument)
                    .where(KnowledgeBaseDocument.id == document_id)
                    .values(
                        query_count=KnowledgeBaseDocument.query_count + 1,
                        last_accessed_at=datetime.utcnow()
                    )
                )
                
                # Create analytics record for this retrieval
                await analytics_service.create_document_analytics_record(
                    document_id=document_id,
                    document_name=doc.metadata.get("filename", "Unknown Document"),
                    retrievals=1,  # This document was retrieved once
                    citations=0,   # Will be updated if document is cited
                    interactions=0,  # Will be updated if user interacts with document
                    db=db
                )
                
                # Create chunk-level analytics event
                chunk_event = AnalyticsEvent(
                    event_type="document_retrieved",
                    event_data={
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "chunk_content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "query": query,
                        "relevance_score": doc.metadata.get("score", 0.0),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                db.add(chunk_event)
            
            await db.commit()
            logger.info(f"Updated analytics for {len(documents)} documents with chunk-level tracking")
            
        except Exception as e:
            logger.error(f"Error tracking document analytics: {e}")
            await db.rollback()

    async def track_document_citation(
        self,
        document_id: str,
        query: str,
        citation_context: str,
        confidence_score: float = None,
        chunk_index: int = None,
        db: AsyncSession = None
    ) -> None:
        """
        Track when a document is cited in a response with enhanced confidence scoring
        """
        try:
            from app.services.farm_data import AnalyticsService
            
            analytics_service = AnalyticsService()
            
            # Get document name for analytics
            result = await db.execute(
                select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.id == document_id)
            )
            document = result.scalar_one_or_none()
            document_name = document.filename if document else "Unknown Document"
            
            # Calculate confidence score if not provided
            if confidence_score is None:
                confidence_score = self._calculate_citation_confidence(query, citation_context)
            
            # Update analytics record with citation
            await analytics_service.create_document_analytics_record(
                document_id=document_id,
                document_name=document_name,
                retrievals=0,  # No new retrieval
                citations=1,   # This document was cited once
                interactions=0,  # No user interaction yet
                satisfaction_score=confidence_score,  # Use confidence as satisfaction proxy
                db=db
            )
            
            # Create analytics event for citation tracking
            from app.models.analytics import AnalyticsEvent
            citation_event = AnalyticsEvent(
                event_type="document_cited",
                event_data={
                    "document_id": document_id,
                    "query": query,
                    "citation_context": citation_context,
                    "confidence_score": confidence_score,
                    "chunk_index": chunk_index,
                    "citation_type": "direct" if confidence_score > 0.7 else "indirect",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            db.add(citation_event)
            
            await db.commit()
            logger.info(f"Tracked citation for document {document_id} with confidence {confidence_score}")
            
        except Exception as e:
            logger.error(f"Error tracking document citation: {e}")
            await db.rollback()

    def _calculate_citation_confidence(self, query: str, citation_context: str) -> float:
        """
        Calculate confidence score for a citation based on query-citation alignment
        """
        try:
            # Convert to lowercase for comparison
            query_words = set(query.lower().split())
            context_words = set(citation_context.lower().split())
            
            # Calculate word overlap
            overlap = len(query_words.intersection(context_words))
            total_query_words = len(query_words)
            
            if total_query_words == 0:
                return 0.0
            
            # Base confidence from word overlap
            word_overlap_score = overlap / total_query_words
            
            # Boost for exact phrase matches
            phrase_boost = 0.0
            if len(query) > 10:  # Only for longer queries
                if query.lower() in citation_context.lower():
                    phrase_boost = 0.3
            
            # Boost for high-frequency query words
            frequency_boost = 0.0
            common_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            meaningful_query_words = query_words - common_words
            if meaningful_query_words:
                meaningful_overlap = len(meaningful_query_words.intersection(context_words))
                frequency_boost = (meaningful_overlap / len(meaningful_query_words)) * 0.2
            
            # Combine scores
            final_score = word_overlap_score + phrase_boost + frequency_boost
            
            # Normalize to 0-1 range
            return min(max(final_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating citation confidence: {e}")
            return 0.5  # Default moderate confidence

    async def get_detailed_source_attribution(
        self,
        query: str,
        documents: List[Document],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Enhanced source attribution with detailed text extraction and mapping
        Returns which exact text/pages/sections were used to answer the query
        """
        try:
            attribution_data = {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "sources": [],
                "total_sources": len(documents),
                "confidence_scores": [],
                "text_extracts": []
            }
            
            for i, doc in enumerate(documents):
                source_info = await self._extract_source_details(doc, db)
                if source_info:
                    attribution_data["sources"].append(source_info)
                    
                    # Calculate confidence score based on relevance
                    confidence = self._calculate_confidence_score(doc, query)
                    attribution_data["confidence_scores"].append(confidence)
                    
                    # Extract relevant text snippets
                    text_extract = self._extract_relevant_text(doc, query)
                    attribution_data["text_extracts"].append(text_extract)
            
            # Calculate overall confidence
            if attribution_data["confidence_scores"]:
                attribution_data["overall_confidence"] = sum(attribution_data["confidence_scores"]) / len(attribution_data["confidence_scores"])
            else:
                attribution_data["overall_confidence"] = 0.0
            
            # Track citations for each document used with confidence scoring
            for doc in documents:
                document_id = doc.metadata.get("document_id")
                chunk_index = doc.metadata.get("chunk_index", 0)
                if document_id:
                    # Calculate confidence based on document relevance
                    confidence = self._calculate_confidence_score(doc, query)
                    
                    await self.track_document_citation(
                        document_id=document_id,
                        query=query,
                        citation_context=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        confidence_score=confidence,
                        chunk_index=chunk_index,
                        db=db
                    )
            
            return attribution_data
            
        except Exception as e:
            logger.error(f"Error generating source attribution: {e}")
            return {"error": str(e)}

    async def _extract_source_details(
        self,
        document: Document,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Extract detailed information about a source document
        """
        try:
            doc_id = document.metadata.get("document_id")
            if not doc_id:
                return None
            
            # Get document from database
            result = await db.execute(
                select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.id == doc_id)
            )
            kb_doc = result.scalar_one_or_none()
            
            if not kb_doc:
                return None
            
            # Extract page/section information from metadata
            page_info = self._extract_page_section_info(document)
            
            return {
                "document_id": str(kb_doc.id),
                "filename": kb_doc.filename,
                "document_type": kb_doc.document_type.value if kb_doc.document_type else "unknown",
                "visibility": kb_doc.visibility,
                "created_at": kb_doc.created_at.isoformat() if kb_doc.created_at else None,
                "page_info": page_info,
                "chunk_index": document.metadata.get("chunk_index", 0),
                "chunk_count": document.metadata.get("chunk_count", 1),
                "relevance_score": document.metadata.get("score", 0.0),
                "text_preview": document.page_content[:200] + "..." if len(document.page_content) > 200 else document.page_content
            }
            
        except Exception as e:
            logger.error(f"Error extracting source details: {e}")
            return None

    def _extract_page_section_info(self, document: Document) -> Dict[str, Any]:
        """
        Extract page and section information from document metadata with enhanced mapping
        """
        metadata = document.metadata
        
        # Try to extract page number from various metadata fields
        page_number = (
            metadata.get("page_number") or 
            metadata.get("page") or 
            self._extract_page_from_text(document.page_content)
        )
        
        # Try to extract section information
        section = (
            metadata.get("section") or 
            metadata.get("heading") or 
            self._extract_section_from_text(document.page_content)
        )
        
        # Calculate position within document
        chunk_start = metadata.get("chunk_start", 0)
        chunk_end = metadata.get("chunk_end", 0)
        chunk_size = chunk_end - chunk_start if chunk_end > chunk_start else len(document.page_content)
        
        return {
            "page_number": page_number,
            "section": section,
            "chunk_position": metadata.get("chunk_index", 0),
            "total_chunks": metadata.get("chunk_count", 1),
            "chunk_start_position": chunk_start,
            "chunk_end_position": chunk_end,
            "chunk_size": chunk_size,
            "relative_position": f"Chunk {metadata.get('chunk_index', 0) + 1} of {metadata.get('chunk_count', 1)}"
        }

    def _extract_page_from_text(self, text: str) -> Optional[int]:
        """
        Extract page number from text content
        Note: This is a fallback method. Page numbers should ideally come from PDF metadata
        """
        # Look for explicit page indicators in text
        page_patterns = [
            r'page\s+(\d+)',
            r'p\.\s*(\d+)',
            r'^(\d+)\s*$',  # Line with just a number
        ]
        
        lines = text.split('\n')
        for line in lines[:3]:  # Check first 3 lines only
            line = line.strip()
            for pattern in page_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        page_num = int(match.group(1))
                        # Sanity check: page numbers should be reasonable
                        if 1 <= page_num <= 10000:
                            return page_num
                    except ValueError:
                        continue
        
        return None

    def _extract_section_from_text(self, text: str) -> Optional[str]:
        """
        Try to extract section/heading information from text content
        """
        lines = text.split('\n')
        
        # Look for common heading patterns
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if not line:
                continue
                
            # Check for numbered sections
            if re.match(r'^\d+\.?\s+[A-Z]', line):
                return line[:50] + "..." if len(line) > 50 else line
            
            # Check for all caps headings
            if line.isupper() and len(line) > 3 and len(line) < 100:
                return line
            
            # Check for bold/emphasized text (common in PDFs)
            if re.match(r'^[A-Z][A-Za-z\s]{5,50}$', line):
                return line
        
        return None

    def _calculate_confidence_score(self, document: Document, query: str) -> float:
        """
        Calculate confidence score for how relevant this document is to the query
        Uses vector similarity as primary signal with minimal text-based adjustments
        """
        try:
            # Primary score from vector similarity (most reliable)
            base_score = document.metadata.get("score", 0.0)
            
            # Only use vector similarity - it's already semantic and reliable
            # Text-based heuristics are redundant and can introduce noise
            return min(max(base_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0

    def _extract_relevant_text(self, document: Document, query: str) -> Dict[str, Any]:
        """
        Extract the most relevant text snippets from the document
        """
        try:
            text = document.page_content
            query_words = set(query.lower().split())
            
            # Split text into sentences
            sentences = re.split(r'[.!?]+', text)
            
            # Score sentences based on query word overlap
            scored_sentences = []
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                overlap = len(query_words.intersection(sentence_words))
                if overlap > 0:
                    scored_sentences.append((sentence.strip(), overlap))
            
            # Sort by relevance and take top 3
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in scored_sentences[:3]]
            
            return {
                "relevant_snippets": top_sentences,
                "total_sentences": len(sentences),
                "relevant_sentences": len(scored_sentences),
                "full_text_length": len(text)
            }
            
        except Exception as e:
            logger.error(f"Error extracting relevant text: {e}")
            return {"error": str(e)}

    async def get_chunk_analytics(
        self,
        document_id: str,
        db: AsyncSession,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get chunk-level analytics for a specific document
        Shows which chunks are most frequently accessed and their performance
        """
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import select, func, and_
            from app.models.analytics import AnalyticsEvent
            
            # Calculate period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get chunk-level events for this document
            result = await db.execute(
                select(AnalyticsEvent)
                .where(
                    and_(
                        AnalyticsEvent.event_type == "document_retrieved",
                        AnalyticsEvent.event_data['document_id'].astext == document_id,
                        AnalyticsEvent.created_at >= start_date,
                        AnalyticsEvent.created_at <= end_date
                    )
                )
                .order_by(AnalyticsEvent.created_at.desc())
            )
            chunk_events = result.scalars().all()
            
            # Aggregate chunk statistics
            chunk_stats = {}
            total_retrievals = 0
            
            for event in chunk_events:
                event_data = event.event_data
                chunk_index = event_data.get("chunk_index", 0)
                
                if chunk_index not in chunk_stats:
                    chunk_stats[chunk_index] = {
                        "chunk_index": chunk_index,
                        "retrieval_count": 0,
                        "avg_relevance_score": 0.0,
                        "relevance_scores": [],
                        "queries": [],
                        "last_accessed": None,
                        "content_preview": event_data.get("chunk_content_preview", "")
                    }
                
                chunk_stats[chunk_index]["retrieval_count"] += 1
                chunk_stats[chunk_index]["relevance_scores"].append(event_data.get("relevance_score", 0.0))
                chunk_stats[chunk_index]["queries"].append(event_data.get("query", ""))
                chunk_stats[chunk_index]["last_accessed"] = event.created_at.isoformat()
                total_retrievals += 1
            
            # Calculate average relevance scores
            for chunk_index, stats in chunk_stats.items():
                if stats["relevance_scores"]:
                    stats["avg_relevance_score"] = sum(stats["relevance_scores"]) / len(stats["relevance_scores"])
                # Remove the raw scores array to keep response clean
                del stats["relevance_scores"]
            
            # Sort chunks by retrieval count
            sorted_chunks = sorted(chunk_stats.values(), key=lambda x: x["retrieval_count"], reverse=True)
            
            return {
                "document_id": document_id,
                "period_days": period_days,
                "total_retrievals": total_retrievals,
                "total_chunks_accessed": len(chunk_stats),
                "chunk_statistics": sorted_chunks,
                "most_accessed_chunk": sorted_chunks[0] if sorted_chunks else None,
                "least_accessed_chunk": sorted_chunks[-1] if sorted_chunks else None
            }
            
        except Exception as e:
            logger.error(f"Error getting chunk analytics: {e}")
            return {"error": str(e)}
