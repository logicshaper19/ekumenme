#!/usr/bin/env python3
"""
Detailed performance test for RAG service
Shows before/after comparison with actual timing data
"""

import asyncio
import time
import sys
import os
from unittest.mock import Mock, AsyncMock

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Ekumen-assistant'))

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.documents import Document

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
                page_content="Agricultural best practices for crop rotation and soil management",
                metadata={"document_id": "doc1", "organization_id": "org1", "score": 0.9}
            ),
            Document(
                page_content="Soil management techniques for sustainable farming practices",
                metadata={"document_id": "doc2", "organization_id": "org1", "score": 0.8}
            ),
            Document(
                page_content="Pest control methods for organic farming and crop protection",
                metadata={"document_id": "doc3", "organization_id": "org2", "score": 0.7}
            )
        ]
    
    def similarity_search(self, query: str, k: int = 5, filter: dict = None):
        # Simulate some processing time
        time.sleep(0.001)  # 1ms to simulate vector search
        
        if filter and "document_id" in filter:
            allowed_ids = filter["document_id"]["$in"]
            filtered = [doc for doc in self.documents if doc.metadata["document_id"] in allowed_ids]
            return filtered[:k]
        return self.documents[:k]

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

async def test_performance_comparison():
    """Test performance with and without caching"""
    print("🚀 RAG Service Performance Test")
    print("=" * 60)
    
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
    
    query = "agricultural practices and crop management"
    user_id = "user1"
    org_id = "org1"
    
    print(f"Query: '{query}'")
    print(f"User: {user_id}, Organization: {org_id}")
    print()
    
    # Test 1: First query (no cache)
    print("📊 Test 1: First Query (No Cache)")
    start_time = time.time()
    results1 = await rag_service.get_relevant_documents(
        query=query,
        user_id=user_id,
        organization_id=org_id,
        db=mock_db,
        k=5
    )
    time1 = time.time() - start_time
    
    print(f"   Results: {len(results1)} documents")
    print(f"   Time: {time1:.3f}s")
    print(f"   Status: {'✅ PASSED' if time1 < 0.5 else '❌ FAILED'} (<500ms)")
    print()
    
    # Test 2: Cached query
    print("📊 Test 2: Cached Query")
    start_time = time.time()
    results2 = await rag_service.get_relevant_documents(
        query=query,
        user_id=user_id,
        organization_id=org_id,
        db=mock_db,
        k=5
    )
    time2 = time.time() - start_time
    
    print(f"   Results: {len(results2)} documents")
    print(f"   Time: {time2:.3f}s")
    print(f"   Status: {'✅ PASSED' if time2 < 0.1 else '❌ FAILED'} (<100ms)")
    print()
    
    # Test 3: Different query (no cache)
    print("📊 Test 3: Different Query (No Cache)")
    start_time = time.time()
    results3 = await rag_service.get_relevant_documents(
        query="soil management techniques",
        user_id=user_id,
        organization_id=org_id,
        db=mock_db,
        k=5
    )
    time3 = time.time() - start_time
    
    print(f"   Results: {len(results3)} documents")
    print(f"   Time: {time3:.3f}s")
    print(f"   Status: {'✅ PASSED' if time3 < 0.5 else '❌ FAILED'} (<500ms)")
    print()
    
    # Performance summary
    print("📈 Performance Summary")
    print("-" * 30)
    print(f"First query:     {time1:.3f}s")
    print(f"Cached query:    {time2:.3f}s")
    print(f"Different query: {time3:.3f}s")
    
    if time2 < time1:
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"Cache speedup:   {speedup:.1f}x")
    
    print()
    
    # Cache statistics
    cache_size = len(rag_service._cache)
    print(f"Cache entries:   {cache_size}")
    print(f"Cache TTL:       {rag_service._cache_ttl}s")
    
    # Overall assessment
    print()
    print("🎯 Overall Assessment")
    print("-" * 20)
    
    all_fast = time1 < 0.5 and time2 < 0.1 and time3 < 0.5
    cache_works = time2 < time1
    
    if all_fast and cache_works:
        print("✅ EXCELLENT: All queries fast, caching working")
        return True
    elif all_fast:
        print("✅ GOOD: All queries fast, but caching needs work")
        return True
    else:
        print("❌ NEEDS WORK: Some queries too slow")
        return False

async def test_multiple_queries():
    """Test performance with multiple queries"""
    print("\n🔄 Multiple Query Performance Test")
    print("=" * 40)
    
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
    
    queries = [
        "agricultural practices",
        "soil management",
        "crop rotation",
        "pest control",
        "organic farming"
    ]
    
    times = []
    
    for i, query in enumerate(queries, 1):
        start_time = time.time()
        results = await rag_service.get_relevant_documents(
            query=query,
            user_id="user1",
            organization_id="org1",
            db=mock_db,
            k=5
        )
        elapsed = time.time() - start_time
        times.append(elapsed)
        
        print(f"Query {i}: {elapsed:.3f}s - {len(results)} results")
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    print()
    print(f"Average time: {avg_time:.3f}s")
    print(f"Max time:     {max_time:.3f}s")
    print(f"Min time:     {min_time:.3f}s")
    
    if avg_time < 0.3:
        print("✅ EXCELLENT: Average query time under 300ms")
        return True
    elif avg_time < 0.5:
        print("✅ GOOD: Average query time under 500ms")
        return True
    else:
        print("❌ NEEDS WORK: Average query time over 500ms")
        return False

async def main():
    """Run detailed performance tests"""
    success1 = await test_performance_comparison()
    success2 = await test_multiple_queries()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL PERFORMANCE TESTS PASSED!")
        print("RAG service is performing well with caching.")
    else:
        print("⚠️  Some performance tests failed.")
        print("RAG service needs optimization.")
    
    return success1 and success2

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
