#!/usr/bin/env python3
"""
Test RAG service with real data by creating a test document
"""

import asyncio
import time
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Ekumen-assistant'))

async def create_test_document_and_test():
    """Create a test document and test RAG service with it"""
    print("🚀 RAG Service Test with Real Data")
    print("=" * 50)
    
    try:
        from app.services.knowledge_base.rag_service import RAGService
        from app.core.database import get_async_db
        from app.models.user import User
        from app.models.organization import Organization
        from app.models.knowledge_base import KnowledgeBaseDocument, DocumentStatus, DocumentType
        from sqlalchemy import select
        
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
            
            # Create a test document that will be accessible
            test_doc = KnowledgeBaseDocument(
                organization_id=org.id,
                uploaded_by=user.id,
                filename="test_agricultural_guide.pdf",
                file_path="/tmp/test_agricultural_guide.pdf",
                file_type="application/pdf",
                file_size_bytes=1024,
                file_hash="test_hash_123",
                processing_status=DocumentStatus.COMPLETED,
                chunk_count=3,
                embedding_model="text-embedding-ada-002",
                document_type=DocumentType.MANUAL,
                tags=["agriculture", "crops", "farming"],
                description="Test agricultural practices guide",
                visibility="shared",  # This makes it accessible
                shared_with_organizations=None,  # Shared with all
                shared_with_users=None,
                is_ekumen_provided=False,
                organization_metadata={"test": True},
                workflow_metadata={"test": True},
                submission_status="approved",
                approved_by=user.id,
                approved_at=datetime.utcnow(),
                expiration_date=None,
                auto_renewal=False,
                quality_score=0.9,
                version=1,
                query_count=0,
                last_accessed_at=None
            )
            
            db.add(test_doc)
            await db.commit()
            
            print(f"✅ Created test document: {test_doc.id}")
            
            # Now add it to the vector store
            rag_service = RAGService()
            
            # Create some test content
            test_content = """
            Agricultural Best Practices Guide
            
            Chapter 1: Crop Rotation
            Crop rotation is essential for maintaining soil health and preventing pest buildup. 
            Rotate between legumes, grains, and vegetables to maintain soil fertility.
            
            Chapter 2: Soil Management
            Regular soil testing helps determine nutrient needs. Use organic matter and 
            compost to improve soil structure and water retention.
            
            Chapter 3: Pest Control
            Integrated pest management combines biological, cultural, and chemical methods
            to control pests while minimizing environmental impact.
            """
            
            # Add document to vector store
            success = await rag_service.add_document_to_vectorstore(
                document=test_doc,
                content=test_content,
                db=db
            )
            
            if success:
                print("✅ Added document to vector store")
            else:
                print("❌ Failed to add document to vector store")
                return False
            
            # Now test the RAG service with real data
            print("\n📊 Testing RAG Service with Real Data")
            print("-" * 40)
            
            # Test 1: Query for crop rotation
            print("Test 1: Query for 'crop rotation'")
            start_time = time.time()
            results1 = await rag_service.get_relevant_documents(
                query="crop rotation",
                user_id=str(user.id),
                organization_id=str(org.id),
                db=db,
                k=5
            )
            time1 = time.time() - start_time
            
            print(f"  Time: {time1:.3f}s")
            print(f"  Results: {len(results1)} documents")
            
            for i, doc in enumerate(results1, 1):
                print(f"    {i}. {doc.metadata.get('filename', 'Unknown')}")
                print(f"       Content: {doc.page_content[:100]}...")
                print(f"       Score: {doc.metadata.get('score', 'N/A')}")
            
            # Test 2: Query for soil management
            print("\nTest 2: Query for 'soil management'")
            start_time = time.time()
            results2 = await rag_service.get_relevant_documents(
                query="soil management",
                user_id=str(user.id),
                organization_id=str(org.id),
                db=db,
                k=5
            )
            time2 = time.time() - start_time
            
            print(f"  Time: {time2:.3f}s")
            print(f"  Results: {len(results2)} documents")
            
            # Test 3: Cache test
            print("\nTest 3: Cache test (same query)")
            start_time = time.time()
            results3 = await rag_service.get_relevant_documents(
                query="crop rotation",
                user_id=str(user.id),
                organization_id=str(org.id),
                db=db,
                k=5
            )
            time3 = time.time() - start_time
            
            print(f"  Time: {time3:.3f}s")
            print(f"  Results: {len(results3)} documents")
            
            if time3 < time1:
                speedup = time1 / time3 if time3 > 0 else float('inf')
                print(f"  Cache speedup: {speedup:.1f}x")
            
            # Summary
            print("\n📈 Performance Summary")
            print("-" * 20)
            print(f"Crop rotation query: {time1:.3f}s")
            print(f"Soil management query: {time2:.3f}s")
            print(f"Cached query: {time3:.3f}s")
            
            # Clean up test document
            await db.delete(test_doc)
            await db.commit()
            print(f"\n✅ Cleaned up test document")
            
            # Overall assessment
            all_fast = time1 < 0.5 and time2 < 0.5 and time3 < 0.5
            found_results = len(results1) > 0 and len(results2) > 0
            
            print("\n🎯 Overall Assessment")
            print("-" * 20)
            if all_fast and found_results:
                print("✅ EXCELLENT: Fast queries with real results")
                return True
            elif found_results:
                print("✅ GOOD: Found results, but some queries slow")
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
    """Run test with real data"""
    success = await create_test_document_and_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 RAG SERVICE TEST WITH REAL DATA PASSED!")
        print("RAG service works with actual documents and vector search.")
    else:
        print("⚠️  RAG SERVICE TEST WITH REAL DATA FAILED!")
        print("RAG service needs more work.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
