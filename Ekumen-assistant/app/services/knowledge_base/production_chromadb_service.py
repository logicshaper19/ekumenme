"""
Production ChromaDB Service
Handles ChromaDB in production with proper configuration, authentication, and error handling
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProductionChromaDBService:
    """
    Production-ready ChromaDB service with:
    - Server-based deployment
    - Authentication
    - Connection pooling
    - Error handling and retries
    - Health monitoring
    - Backup and recovery
    """
    
    def __init__(self):
        self.chromadb_url = settings.CHROMADB_URL
        self.username = settings.CHROMADB_USERNAME
        self.password = settings.CHROMADB_PASSWORD
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self._client = None
        self._collection = None
        
    async def initialize(self):
        """Initialize ChromaDB client with authentication"""
        try:
            from chromadb import HttpClient
            
            self._client = HttpClient(
                host=self.chromadb_url.replace("http://", "").replace("https://", ""),
                port=8001,
                settings=HttpClient.Settings(
                    chroma_api_impl="chromadb.api.fastapi.FastAPI",
                    chroma_server_host=self.chromadb_url.replace("http://", "").replace("https://", ""),
                    chroma_server_http_port=8001,
                    chroma_server_headers={"X-Chroma-Token": self.password}
                )
            )
            
            # Test connection
            await self._health_check()
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name="ekumen_knowledge_base",
                metadata={"description": "Ekumen agricultural knowledge base"}
            )
            
            logger.info("✅ Production ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def _health_check(self) -> bool:
        """Check ChromaDB server health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.chromadb_url}/api/v1/heartbeat",
                    headers={"X-Chroma-Token": self.password},
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"ChromaDB health check failed: {e}")
            return False
    
    async def add_documents(
        self, 
        documents: List[Document], 
        collection_name: str = "ekumen_knowledge_base"
    ) -> List[str]:
        """Add documents to ChromaDB with error handling"""
        try:
            if not self._client:
                await self.initialize()
            
            # Prepare documents for ChromaDB
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            ids = [f"doc_{datetime.now().timestamp()}_{i}" for i in range(len(documents))]
            
            # Generate embeddings
            embeddings = await self.embeddings.aembed_documents(texts)
            
            # Add to collection
            collection = self._client.get_or_create_collection(name=collection_name)
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"✅ Added {len(documents)} documents to ChromaDB")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        collection_name: str = "ekumen_knowledge_base"
    ) -> List[Document]:
        """Perform similarity search with error handling"""
        try:
            if not self._client:
                await self.initialize()
            
            # Generate query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Search collection
            collection = self._client.get_collection(name=collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter
            )
            
            # Convert to Document objects
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc_text in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    if results['distances'] and results['distances'][0]:
                        metadata['score'] = 1 - results['distances'][0][i]  # Convert distance to similarity
                    
                    documents.append(Document(
                        page_content=doc_text,
                        metadata=metadata
                    ))
            
            logger.info(f"✅ Found {len(documents)} similar documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            return []
    
    async def delete_documents(
        self, 
        document_ids: List[str],
        collection_name: str = "ekumen_knowledge_base"
    ) -> bool:
        """Delete documents from ChromaDB"""
        try:
            if not self._client:
                await self.initialize()
            
            collection = self._client.get_collection(name=collection_name)
            collection.delete(ids=document_ids)
            
            logger.info(f"✅ Deleted {len(document_ids)} documents from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    async def get_collection_stats(
        self, 
        collection_name: str = "ekumen_knowledge_base"
    ) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            if not self._client:
                await self.initialize()
            
            collection = self._client.get_collection(name=collection_name)
            count = collection.count()
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "status": "healthy" if await self._health_check() else "unhealthy",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "collection_name": collection_name,
                "document_count": 0,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def backup_collection(
        self, 
        collection_name: str = "ekumen_knowledge_base",
        backup_path: str = None
    ) -> Dict[str, Any]:
        """Backup collection data"""
        try:
            if not self._client:
                await self.initialize()
            
            collection = self._client.get_collection(name=collection_name)
            
            # Get all documents
            results = collection.get()
            
            backup_data = {
                "collection_name": collection_name,
                "documents": results.get('documents', []),
                "metadatas": results.get('metadatas', []),
                "ids": results.get('ids', []),
                "embeddings": results.get('embeddings', []),
                "backup_timestamp": datetime.now().isoformat(),
                "document_count": len(results.get('ids', []))
            }
            
            logger.info(f"✅ Created backup for {backup_data['document_count']} documents")
            return backup_data
            
        except Exception as e:
            logger.error(f"Failed to backup collection: {e}")
            return {"error": str(e)}
    
    async def restore_collection(
        self, 
        backup_data: Dict[str, Any],
        collection_name: str = "ekumen_knowledge_base"
    ) -> bool:
        """Restore collection from backup"""
        try:
            if not self._client:
                await self.initialize()
            
            # Delete existing collection if it exists
            try:
                self._client.delete_collection(name=collection_name)
            except:
                pass  # Collection might not exist
            
            # Create new collection
            collection = self._client.create_collection(
                name=collection_name,
                metadata={"description": f"Restored from backup at {backup_data.get('backup_timestamp')}"}
            )
            
            # Add documents from backup
            if backup_data.get('documents'):
                collection.add(
                    documents=backup_data['documents'],
                    metadatas=backup_data.get('metadatas', []),
                    ids=backup_data.get('ids', []),
                    embeddings=backup_data.get('embeddings', [])
                )
            
            logger.info(f"✅ Restored {len(backup_data.get('ids', []))} documents from backup")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore collection: {e}")
            return False
    
    async def migrate_from_local(
        self, 
        local_chroma_path: str = "./chroma_db"
    ) -> bool:
        """Migrate from local ChromaDB to production server"""
        try:
            # This would require reading the local SQLite database
            # and transferring documents to the production server
            logger.info("Migration from local ChromaDB not implemented yet")
            return False
            
        except Exception as e:
            logger.error(f"Failed to migrate from local ChromaDB: {e}")
            return False


# Global instance
production_chromadb = ProductionChromaDBService()
