#!/usr/bin/env python3
"""
Test script for Knowledge Base Workflow
Tests the complete workflow from submission to approval
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import get_async_db
from app.services.knowledge_base_workflow import KnowledgeBaseWorkflowService
from app.models.knowledge_base import KnowledgeBaseDocument, DocumentType
from app.models.user import User
from app.models.organization import Organization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def test_workflow():
    """Test the complete knowledge base workflow"""
    print("🧪 Testing Knowledge Base Workflow")
    print("=" * 50)
    
    # Initialize services
    workflow_service = KnowledgeBaseWorkflowService()
    
    # Get database session
    async for db in get_async_db():
        try:
            # Test 1: Create a test document submission
            print("\n1️⃣ Testing document submission...")
            
            # Get test organization and user
            result = await db.execute(
                select(Organization).where(Organization.name == "Dijon Céréales")
            )
            test_org = result.scalar_one_or_none()
            
            if not test_org:
                print("❌ Test organization 'Dijon Céréales' not found")
                return
            
            result = await db.execute(
                select(User).where(User.email == "martin@dijon-cereales.fr")
            )
            test_user = result.scalar_one_or_none()
            
            if not test_user:
                print("❌ Test user 'martin@dijon-cereales.fr' not found")
                return
            
            print(f"✅ Found test organization: {test_org.name}")
            print(f"✅ Found test user: {test_user.full_name}")
            
            # Create a test document
            test_file_path = "/tmp/test_document.txt"
            with open(test_file_path, "w") as f:
                f.write("""
Test Agricultural Document

This is a test document for the knowledge base workflow.
It contains information about wheat cultivation practices.

Key Points:
- Wheat should be planted in autumn
- Proper soil preparation is essential
- Regular monitoring for diseases is important
- Harvest timing is critical for quality

This document demonstrates the workflow from submission to approval.
                """)
            
            # Submit document
            submission_result = await workflow_service.submit_document(
                organization_id=str(test_org.id),
                uploaded_by=str(test_user.id),
                file_path=test_file_path,
                filename="test_wheat_guide.txt",
                file_type="txt",
                document_type=DocumentType.MANUAL,
                description="Test wheat cultivation guide",
                tags=["wheat", "cultivation", "test"],
                expiration_months=12,
                visibility="shared",
                db=db
            )
            
            print(f"✅ Document submitted: {submission_result['document_id']}")
            print(f"   Status: {submission_result['status']}")
            print(f"   Quality Score: {submission_result.get('quality_score', 'N/A')}")
            
            # Test 2: Check document status
            print("\n2️⃣ Checking document status...")
            
            result = await db.execute(
                select(KnowledgeBaseDocument).where(
                    KnowledgeBaseDocument.id == submission_result['document_id']
                )
            )
            document = result.scalar_one()
            
            print(f"✅ Document status: {document.submission_status}")
            print(f"   Processing status: {document.processing_status}")
            print(f"   Quality score: {document.quality_score}")
            print(f"   Quality issues: {document.quality_issues}")
            
            # Test 3: Superadmin approval (simulate)
            print("\n3️⃣ Testing superadmin approval...")
            
            # Get superadmin user (or create one for testing)
            result = await db.execute(
                select(User).where(User.is_superuser == True)
            )
            superadmin = result.scalar_one_or_none()
            
            if not superadmin:
                print("⚠️  No superadmin user found, creating test superadmin...")
                # Create a test superadmin
                superadmin = User(
                    email="superadmin@test.com",
                    hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MHS.K2",  # Test1234!
                    full_name="Test Superadmin",
                    role="ADMIN",
                    status="ACTIVE",
                    is_superuser=True,
                    is_verified=True
                )
                db.add(superadmin)
                await db.commit()
                print("✅ Test superadmin created")
            
            # Approve document
            approval_result = await workflow_service.approve_document(
                document_id=str(document.id),
                approved_by=str(superadmin.id),
                comments="Test approval - document looks good",
                db=db
            )
            
            print(f"✅ Document approved: {approval_result['message']}")
            print(f"   Approved at: {approval_result['approved_at']}")
            
            # Test 4: Verify document is now available in RAG
            print("\n4️⃣ Testing RAG availability...")
            
            # Refresh document from database
            await db.refresh(document)
            
            print(f"✅ Final document status: {document.submission_status}")
            print(f"   Processing status: {document.processing_status}")
            print(f"   Visibility: {document.visibility}")
            print(f"   Approved by: {document.approved_by}")
            print(f"   Approved at: {document.approved_at}")
            
            # Test 5: Check workflow audit trail
            print("\n5️⃣ Checking workflow audit trail...")
            
            from app.models.knowledge_base import KnowledgeBaseWorkflowAudit
            result = await db.execute(
                select(KnowledgeBaseWorkflowAudit).where(
                    KnowledgeBaseWorkflowAudit.document_id == document.id
                ).order_by(KnowledgeBaseWorkflowAudit.performed_at)
            )
            audit_entries = result.scalars().all()
            
            print(f"✅ Found {len(audit_entries)} audit entries:")
            for entry in audit_entries:
                print(f"   - {entry.action} by {entry.performed_by} at {entry.performed_at}")
                if entry.comments:
                    print(f"     Comments: {entry.comments}")
            
            print("\n🎉 Knowledge Base Workflow Test Completed Successfully!")
            print("=" * 50)
            
            # Cleanup
            os.remove(test_file_path)
            print("🧹 Cleaned up test files")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(test_workflow())
