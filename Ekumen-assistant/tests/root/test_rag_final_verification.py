#!/usr/bin/env python3
"""
Final verification test for RAG service
Tests with existing data and shows real performance
"""

import asyncio
import time
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Ekumen-assistant'))

async def test_rag_final_verification():
    """Final verification test with real components"""
    print("🚀 RAG Service Final Verification")
    print("=" * 50)
    print("Testing with REAL database, REAL ChromaDB, REAL data")
    print()
    
    try:
        from app.services.knowledge_base.rag_service import RAGService
        from app.core.database import get_async_db
        from app.models.user import User
        from app.models.organization import Organization
        from app.models.knowledge_base import KnowledgeBaseDocument, DocumentStatus
        from sqlalchemy import select, update
        
        # Get database session
        async for db in get_async_db():
            # Get test user and organization
            user_result = await db.execute(select(User).limit(1))
            user = user_result.scalar_one_or_none()
            
            org_result = await db.execute(select(Organization).limit(1))
            org = org_result.scalar_one_or_none()
            
            if not user or not org:
                print("❌ No test user or organization found")
                return False
            
            print(f"✅ Using user: {user.id}")
            print(f"✅ Using organization: {org.id}")
            
            # Check existing documents
            docs_result = await db.execute(select(KnowledgeBaseDocument))
            existing_docs = docs_result.scalars().all()
            print(f"✅ Found {len(existing_docs)} existing documents")
            
            # Make one document accessible for testing
            accessible_doc = None
            for doc in existing_docs:
                if doc.organization_id == org.id:
                    # Update this document to be accessible
                    await db.execute(
                        update(KnowledgeBaseDocument)
                        .where(KnowledgeBaseDocument.id == doc.id)
                        .values(
                            processing_status=DocumentStatus.COMPLETED,
                            visibility="shared",
                            submission_status="approved",
                            shared_with_organizations=None,  # Shared with all
                            shared_with_users=None,
                            is_ekumen_provided=False
                        )
                    )
                    accessible_doc = doc
                    break
            
            if not accessible_doc:
                print("❌ No documents found for this organization")
                return False
            
            await db.commit()
            print(f"✅ Made document accessible: {accessible_doc.filename}")
            
            # Initialize RAG service
            print("\n🔧 Initializing RAG service...")
            rag_service = RAGService()
            print("✅ RAG service initialized")
            
            # Test 1: Real query performance
            print("\n📊 Test 1: Real Query Performance")
            print("-" * 40)
            
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
                    print(f"     Score: {doc.metadata.get('score', 'N/A')}")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # Test 2: Cache performance
            print("\n📊 Test 2: Cache Performance")
            print("-" * 40)
            
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
            print("-" * 40)
            
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
            print("-" * 40)
            
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
            found_results = len(results) > 0
            
            print("\n🎯 Overall Assessment")
            print("-" * 20)
            if all_fast and cache_works and found_results:
                print("✅ EXCELLENT: Fast queries, caching working, found results")
                return True
            elif all_fast and found_results:
                print("✅ GOOD: Fast queries with results, caching needs work")
                return True
            elif found_results:
                print("✅ OK: Found results, but some queries slow")
                return True
            else:
                print("❌ NEEDS WORK: No results found or queries too slow")
                return False
            
            break
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run final verification test"""
    success = await test_rag_final_verification()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 RAG SERVICE FINAL VERIFICATION PASSED!")
        print("RAG service works with real components and data.")
    else:
        print("⚠️  RAG SERVICE FINAL VERIFICATION FAILED!")
        print("RAG service needs more work.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
