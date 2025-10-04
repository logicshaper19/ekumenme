#!/usr/bin/env python3
"""
Test script to verify RAG service fixes actually work
Tests authentication, caching, performance, and error handling
"""

import asyncio
import time
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import List

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Ekumen-assistant'))

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.documents import Document

# Mock the database and other dependencies
class MockAsyncSession:
    def __init__(self):
        self.execute = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class MockVectorStore:
    def __init__(self):
        self.documents = [
            Document(
                page_content="Agricultural best practices for crop rotation",
                metadata={"document_id": "doc1", "organization_id": "org1", "score": 0.9}
            ),
            Document(
                page_content="Soil management techniques for sustainable farming",
                metadata={"document_id": "doc2", "organization_id": "org1", "score": 0.8}
            ),
            Document(
                page_content="Pest control methods for organic farming",
                metadata={"document_id": "doc3", "organization_id": "org2", "score": 0.7}
            )
        ]
    
    def similarity_search(self, query: str, k: int = 5, filter: dict = None):
        # Simulate filtering by document_id
        if filter and "document_id" in filter:
            allowed_ids = filter["document_id"]["$in"]
            filtered = [doc for doc in self.documents if doc.metadata["document_id"] in allowed_ids]
            return filtered[:k]
        return self.documents[:k]
    
    def get(self, where: dict = None):
        if where and "document_id" in where:
            doc_id = where["document_id"]
            matching_docs = [doc for doc in self.documents if doc.metadata["document_id"] == doc_id]
            return {"ids": [doc.metadata["document_id"] for doc in matching_docs]}
        return {"ids": []}
    
    def delete(self, ids: List[str]):
        # Simulate deletion
        pass

class MockKnowledgeBaseDocument:
    def __init__(self, doc_id: str, org_id: str):
        self.id = doc_id
        self.organization_id = org_id
        self.processing_status = "completed"
        self.visibility = "shared"
        self.expiration_date = None
        self.submission_status = "approved"
        self.shared_with_organizations = None
        self.shared_with_users = None
        self.is_ekumen_provided = False
        self.document_type = Mock()
        self.document_type.value = "manual"
        self.quality_score = 0.8
        self.version = 1
        self.organization_metadata = {}
        self.tags = []
        self.description = "Test document"
        self.filename = f"test_{doc_id}.pdf"
        self.chunk_count = 1
        self.query_count = 0
        self.last_accessed_at = None

async def test_authentication_fix():
    """Test that db parameter is now required"""
    print("🧪 Testing authentication fix...")
    
    # Import the actual RAG service
    from app.services.knowledge_base.rag_service import RAGService
    
    rag_service = RAGService()
    rag_service.vectorstore = MockVectorStore()
    
    # Mock the database query
    mock_db = MockAsyncSession()
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [
        MockKnowledgeBaseDocument("doc1", "org1"),
        MockKnowledgeBaseDocument("doc2", "org1")
    ]
    mock_db.execute.return_value = mock_result
    
    # Test 1: Should work with valid parameters
    try:
        results = await rag_service.get_relevant_documents(
            query="agricultural practices",
            user_id="user1",
            organization_id="org1",
            db=mock_db,
            k=5
        )
        print("✅ Test 1: Valid parameters - PASSED")
    except Exception as e:
        print(f"❌ Test 1: Valid parameters - FAILED: {e}")
        return False
    
    # Test 2: Should fail without db parameter (this would be a syntax error now)
    # Since we made db required, this test is about the method signature
    import inspect
    sig = inspect.signature(rag_service.get_relevant_documents)
    db_param = sig.parameters.get('db')
    if db_param and db_param.default == inspect.Parameter.empty:
        print("✅ Test 2: db parameter is required - PASSED")
    else:
        print("❌ Test 2: db parameter is required - FAILED")
        return False
    
    # Test 3: Should fail with None db
    try:
        results = await rag_service.get_relevant_documents(
            query="agricultural practices",
            user_id="user1",
            organization_id="org1",
            db=None,
            k=5
        )
        print("❌ Test 3: None db should fail - FAILED (no exception raised)")
        return False
    except ValueError as e:
        if "Database session is required" in str(e):
            print("✅ Test 3: None db raises ValueError - PASSED")
        else:
            print(f"❌ Test 3: None db raises wrong error - FAILED: {e}")
            return False
    except Exception as e:
        print(f"❌ Test 3: None db raises wrong exception - FAILED: {e}")
        return False
    
    return True

async def test_caching():
    """Test that caching actually works"""
    print("\n🧪 Testing caching...")
    
    from app.services.knowledge_base.rag_service import RAGService
    
    rag_service = RAGService()
    rag_service.vectorstore = MockVectorStore()
    
    # Mock the database query
    mock_db = MockAsyncSession()
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [
        MockKnowledgeBaseDocument("doc1", "org1"),
        MockKnowledgeBaseDocument("doc2", "org1")
    ]
    mock_db.execute.return_value = mock_result
    
    query = "agricultural practices"
    user_id = "user1"
    org_id = "org1"
    
    # First query - should be slow (no cache)
    start_time = time.time()
    results1 = await rag_service.get_relevant_documents(
        query=query,
        user_id=user_id,
        organization_id=org_id,
        db=mock_db,
        k=5
    )
    time1 = time.time() - start_time
    
    # Second query - should be fast (cached)
    start_time = time.time()
    results2 = await rag_service.get_relevant_documents(
        query=query,
        user_id=user_id,
        organization_id=org_id,
        db=mock_db,
        k=5
    )
    time2 = time.time() - start_time
    
    print(f"First query time: {time1:.3f}s")
    print(f"Cached query time: {time2:.3f}s")
    
    if time2 < time1:
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"✅ Caching works - {speedup:.1f}x speedup")
        return True
    else:
        print("❌ Caching failed - no speedup observed")
        return False

async def test_performance():
    """Test that queries are reasonably fast"""
    print("\n🧪 Testing performance...")
    
    from app.services.knowledge_base.rag_service import RAGService
    
    rag_service = RAGService()
    rag_service.vectorstore = MockVectorStore()
    
    # Mock the database query
    mock_db = MockAsyncSession()
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [
        MockKnowledgeBaseDocument("doc1", "org1"),
        MockKnowledgeBaseDocument("doc2", "org1")
    ]
    mock_db.execute.return_value = mock_result
    
    # Test query performance
    start_time = time.time()
    results = await rag_service.get_relevant_documents(
        query="agricultural practices",
        user_id="user1",
        organization_id="org1",
        db=mock_db,
        k=5
    )
    elapsed = time.time() - start_time
    
    print(f"Query time: {elapsed:.3f}s")
    
    if elapsed < 0.5:  # Should be under 500ms
        print("✅ Performance test - PASSED (<500ms)")
        return True
    else:
        print(f"❌ Performance test - FAILED ({elapsed:.3f}s > 500ms)")
        return False

async def test_error_handling():
    """Test error handling and fallbacks"""
    print("\n🧪 Testing error handling...")
    
    from app.services.knowledge_base.rag_service import RAGService
    
    rag_service = RAGService()
    
    # Mock the database query
    mock_db = MockAsyncSession()
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [
        MockKnowledgeBaseDocument("doc1", "org1"),
        MockKnowledgeBaseDocument("doc2", "org1")
    ]
    mock_db.execute.return_value = mock_result
    
    # Test 1: Vector store failure
    rag_service.vectorstore = MockVectorStore()
    
    # Mock vector store to raise exception
    original_similarity_search = rag_service.vectorstore.similarity_search
    def failing_similarity_search(*args, **kwargs):
        raise Exception("ChromaDB unavailable")
    
    rag_service.vectorstore.similarity_search = failing_similarity_search
    
    try:
        results = await rag_service.get_relevant_documents(
            query="agricultural practices",
            user_id="user1",
            organization_id="org1",
            db=mock_db,
            k=5
        )
        # Should return empty list, not crash
        if results == []:
            print("✅ Error handling - PASSED (returns empty list on failure)")
        else:
            print(f"❌ Error handling - FAILED (returned {len(results)} results instead of empty list)")
            return False
    except Exception as e:
        print(f"❌ Error handling - FAILED (raised exception: {e})")
        return False
    
    return True

async def test_access_control():
    """Test that access control works"""
    print("\n🧪 Testing access control...")
    
    from app.services.knowledge_base.rag_service import RAGService
    
    rag_service = RAGService()
    rag_service.vectorstore = MockVectorStore()
    
    # Mock the database query to return only org1 documents
    mock_db = MockAsyncSession()
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [
        MockKnowledgeBaseDocument("doc1", "org1"),
        MockKnowledgeBaseDocument("doc2", "org1")
    ]
    mock_db.execute.return_value = mock_result
    
    # User from org1 should only see org1 documents
    results = await rag_service.get_relevant_documents(
        query="agricultural practices",
        user_id="user1",
        organization_id="org1",
        db=mock_db,
        k=5
    )
    
    # Check that all results are from org1
    for doc in results:
        if doc.metadata.get('organization_id') != 'org1':
            print(f"❌ Access control - FAILED (found doc from {doc.metadata.get('organization_id')})")
            return False
    
    print("✅ Access control - PASSED (only org1 documents returned)")
    return True

async def main():
    """Run all tests"""
    print("🚀 Testing RAG Service Fixes")
    print("=" * 50)
    
    tests = [
        ("Authentication Fix", test_authentication_fix),
        ("Caching", test_caching),
        ("Performance", test_performance),
        ("Error Handling", test_error_handling),
        ("Access Control", test_access_control),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} - FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG service fixes are working.")
        return True
    else:
        print("⚠️  Some tests failed. RAG service needs more work.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
