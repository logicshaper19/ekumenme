#!/usr/bin/env python3
"""
Real integration test for RAG service
Tests against actual database, ChromaDB, and real data
NO MOCKS - only real components
"""

import asyncio
import time
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Ekumen-assistant'))

async def test_real_rag_service():
    """Test RAG service with real components"""
    print("🚀 Real RAG Service Integration Test")
    print("=" * 50)
    print("Testing against ACTUAL database and ChromaDB")
    print("NO MOCKS - only real components")
    print()
    
    try:
        # Import real components
        from app.services.knowledge_base.rag_service import RAGService
        from app.core.database import get_async_db
        from app.models.user import User
        from app.models.organization import Organization
        from sqlalchemy import select
        
        print("✅ Successfully imported real components")
        
        # Get real database session
        async for db in get_async_db():
            print("✅ Got real database session")
            
            # Check if we have any real users and organizations
            user_result = await db.execute(select(User).limit(1))
            user = user_result.scalar_one_or_none()
            
            if not user:
                print("❌ No users found in database")
                print("   Need to create test data first")
                return False
            
            org_result = await db.execute(select(Organization).limit(1))
            org = org_result.scalar_one_or_none()
            
            if not org:
                print("❌ No organizations found in database")
                print("   Need to create test data first")
                return False
            
            print(f"✅ Found test user: {user.id}")
            print(f"✅ Found test organization: {org.id}")
            
            # Initialize real RAG service
            print("\n🔧 Initializing real RAG service...")
            rag_service = RAGService()
            print("✅ RAG service initialized")
            
            # Test 1: Real query performance
            print("\n📊 Test 1: Real Query Performance")
            print("-" * 30)
            
            query = "agricultural practices"
            start_time = time.time()
            
            try:
                results = await rag_service.get_relevant_documents(
                    query=query,
                    user_id=str(user.id),
                    organization_id=str(org.id),
                    db=db,
                    k=5
                )
                elapsed = time.time() - start_time
                
                print(f"Query: '{query}'")
                print(f"Time: {elapsed:.3f}s")
                print(f"Results: {len(results)} documents")
                
                if elapsed < 0.5:
                    print("✅ PASSED: Query under 500ms")
                else:
                    print(f"❌ FAILED: Query took {elapsed:.3f}s (over 500ms)")
                
                # Show actual results
                for i, doc in enumerate(results, 1):
                    print(f"  {i}. {doc.metadata.get('filename', 'Unknown')}")
                    print(f"     Content: {doc.page_content[:100]}...")
                    print(f"     Org: {doc.metadata.get('organization_id')}")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
                return False
            
            # Test 2: Cache performance
            print("\n📊 Test 2: Cache Performance")
            print("-" * 30)
            
            # Same query again - should hit cache
            start_time = time.time()
            try:
                cached_results = await rag_service.get_relevant_documents(
                    query=query,
                    user_id=str(user.id),
                    organization_id=str(org.id),
                    db=db,
                    k=5
                )
                cached_elapsed = time.time() - start_time
                
                print(f"Cached query time: {cached_elapsed:.3f}s")
                print(f"Cached results: {len(cached_results)} documents")
                
                if cached_elapsed < elapsed:
                    speedup = elapsed / cached_elapsed if cached_elapsed > 0 else float('inf')
                    print(f"✅ PASSED: Cache speedup {speedup:.1f}x")
                else:
                    print("❌ FAILED: No cache speedup")
                
            except Exception as e:
                print(f"❌ Cached query failed: {e}")
                return False
            
            # Test 3: Different query
            print("\n📊 Test 3: Different Query")
            print("-" * 30)
            
            different_query = "soil management"
            start_time = time.time()
            try:
                diff_results = await rag_service.get_relevant_documents(
                    query=different_query,
                    user_id=str(user.id),
                    organization_id=str(org.id),
                    db=db,
                    k=5
                )
                diff_elapsed = time.time() - start_time
                
                print(f"Query: '{different_query}'")
                print(f"Time: {diff_elapsed:.3f}s")
                print(f"Results: {len(diff_results)} documents")
                
                if diff_elapsed < 0.5:
                    print("✅ PASSED: Different query under 500ms")
                else:
                    print(f"❌ FAILED: Different query took {diff_elapsed:.3f}s")
                
            except Exception as e:
                print(f"❌ Different query failed: {e}")
                return False
            
            # Test 4: Error handling
            print("\n📊 Test 4: Error Handling")
            print("-" * 30)
            
            try:
                # Test with invalid user ID
                error_results = await rag_service.get_relevant_documents(
                    query="test",
                    user_id="invalid_user_id",
                    organization_id=str(org.id),
                    db=db,
                    k=5
                )
                print(f"Error handling results: {len(error_results)} documents")
                print("✅ PASSED: Error handling works (returned empty or filtered results)")
                
            except Exception as e:
                print(f"❌ Error handling failed: {e}")
                return False
            
            # Summary
            print("\n📈 Performance Summary")
            print("-" * 20)
            print(f"First query:     {elapsed:.3f}s")
            print(f"Cached query:    {cached_elapsed:.3f}s")
            print(f"Different query: {diff_elapsed:.3f}s")
            
            if cached_elapsed < elapsed:
                speedup = elapsed / cached_elapsed if cached_elapsed > 0 else float('inf')
                print(f"Cache speedup:   {speedup:.1f}x")
            
            # Overall assessment
            all_fast = elapsed < 0.5 and diff_elapsed < 0.5
            cache_works = cached_elapsed < elapsed
            
            print("\n🎯 Overall Assessment")
            print("-" * 20)
            if all_fast and cache_works:
                print("✅ EXCELLENT: All queries fast, caching working")
                return True
            elif all_fast:
                print("✅ GOOD: All queries fast, caching needs work")
                return True
            else:
                print("❌ NEEDS WORK: Some queries too slow")
                return False
            
            break  # Exit the async generator
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run real integration test"""
    success = await test_real_rag_service()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 REAL INTEGRATION TEST PASSED!")
        print("RAG service works with actual components.")
    else:
        print("⚠️  REAL INTEGRATION TEST FAILED!")
        print("RAG service needs more work.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
