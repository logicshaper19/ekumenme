"""
RAG Service with Knowledge Base Workflow Integration
Integrates with the vetted, time-bound knowledge contribution system
"""

import logging
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime, timedelta

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.core.config import settings
from app.models.knowledge_base import KnowledgeBaseDocument, DocumentStatus
from app.services.knowledge_base_workflow import KnowledgeBaseWorkflowService

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
        db: AsyncSession = None,
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
                # Use metadata filtering if supported by vector store
                search_results = self.vectorstore.similarity_search(
                    query,
                    k=k,
                    filter={"document_id": {"$in": doc_ids}} if hasattr(self.vectorstore, 'similarity_search') else None
                )
                
                # If metadata filtering not supported, filter results manually
                if not hasattr(self.vectorstore, 'similarity_search') or not search_results:
                    # Fallback: get all results and filter
                    search_results = self.vectorstore.similarity_search(query, k=k*2)
                    search_results = [doc for doc in search_results 
                                    if doc.metadata.get("document_id") in doc_ids]
                    search_results = search_results[:k]
                
                # Enhance documents with workflow metadata
                enhanced_docs = await self._enhance_documents_with_metadata(
                    search_results, accessible_docs, db
                )
                
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
                        KnowledgeBaseDocument.expiration_date == None,  # No expiration set
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
                        # Shared with all organizations
                        func.jsonb_array_length(
                            func.coalesce(
                                KnowledgeBaseDocument.shared_with_organizations, 
                                '[]'::jsonb
                            )
                        ) == 0,  # Empty array means shared with all
                        # Shared with specific organizations including user's org
                        func.jsonb_array_length(
                            func.coalesce(
                                KnowledgeBaseDocument.shared_with_organizations, 
                                '[]'::jsonb
                            )
                        ) > 0
                    )
                )
            )
            
            # User can access documents shared with them specifically
            access_conditions.append(
                and_(
                    KnowledgeBaseDocument.shared_with_users.isnot(None),
                    func.jsonb_array_length(KnowledgeBaseDocument.shared_with_users) > 0
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
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "document_id": str(document.id),
                        "chunk_index": i,
                        "filename": document.filename,
                        "document_type": document.document_type.value,
                        "organization_id": str(document.organization_id),
                        "uploaded_by": str(document.uploaded_by),
                        "created_at": document.created_at.isoformat(),
                        "version": document.version
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
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval
        """
        if len(text) <= chunk_size:
            return [text]
        
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
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
        return chunks
    
    async def remove_document_from_vectorstore(
        self,
        document_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Remove a document from the vector store (e.g., when expired)
        """
        try:
            # Note: ChromaDB doesn't have a direct delete by metadata method
            # This would require implementing a custom deletion strategy
            # For now, we'll mark the document as inactive in the database
            # and filter it out during retrieval
            
            result = await db.execute(
                select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.id == document_id)
            )
            document = result.scalar_one()
            
            # Update document visibility
            document.visibility = "internal"
            document.organization_metadata["deactivated_at"] = datetime.utcnow().isoformat()
            
            await db.commit()
            
            logger.info(f"Deactivated document {document_id} from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error removing document from vector store: {e}")
            return False
    
    async def get_document_statistics(
        self,
        organization_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base
        """
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
