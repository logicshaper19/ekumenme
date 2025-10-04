"""
Scheduler Service for Knowledge Base Workflow
Handles automated tasks like expiration checks and reminders
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import schedule
import time
from threading import Thread

from app.core.database import AsyncSessionLocal
from app.services.knowledge_base import (
    KnowledgeBaseWorkflowService,
    RAGService
)

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing scheduled tasks related to knowledge base workflow
    """
    
    def __init__(self):
        self.workflow_service = KnowledgeBaseWorkflowService()
        self.rag_service = RAGService()
        self.is_running = False
        self.scheduler_thread = None
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("✅ Knowledge Base Scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("🛑 Knowledge Base Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        # Schedule daily tasks
        schedule.every().day.at("09:00").do(self._daily_expiration_check)
        schedule.every().day.at("10:00").do(self._daily_cleanup_expired)
        schedule.every().monday.at("08:00").do(self._weekly_quality_report)
        
        # Schedule hourly tasks
        schedule.every().hour.do(self._hourly_reminder_check)
        
        logger.info("📅 Scheduled tasks configured:")
        logger.info("  - Daily expiration check: 09:00")
        logger.info("  - Daily cleanup expired: 10:00")
        logger.info("  - Weekly quality report: Monday 08:00")
        logger.info("  - Hourly reminder check: Every hour")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    async def _daily_expiration_check(self):
        """Daily check for expiring documents and send reminders"""
        try:
            logger.info("🔍 Running daily expiration check...")
            
            async with AsyncSessionLocal() as db:
                expiring_docs = await self.workflow_service.check_expiring_documents(db=db)
                
                if expiring_docs:
                    logger.info(f"📧 Sent {len(expiring_docs)} expiration reminders")
                    
                    # Log details for monitoring
                    for doc in expiring_docs:
                        logger.info(f"  - {doc['filename']} expires in {doc['days_until_expiration']} days")
                else:
                    logger.info("✅ No documents expiring soon")
                    
        except Exception as e:
            logger.error(f"Error in daily expiration check: {e}")
    
    async def _daily_cleanup_expired(self):
        """Daily cleanup of expired documents"""
        try:
            logger.info("🧹 Running daily cleanup of expired documents...")
            
            async with AsyncSessionLocal() as db:
                deactivated_ids = await self.workflow_service.deactivate_expired_documents(db=db)
                
                if deactivated_ids:
                    logger.info(f"🚫 Deactivated {len(deactivated_ids)} expired documents")
                    
                    # Remove from vector store
                    for doc_id in deactivated_ids:
                        await self.rag_service.remove_document_from_vectorstore(doc_id, db)
                else:
                    logger.info("✅ No expired documents to clean up")
                    
        except Exception as e:
            logger.error(f"Error in daily cleanup: {e}")
    
    async def _hourly_reminder_check(self):
        """Hourly check for urgent reminders"""
        try:
            # Check for documents expiring in the next 7 days
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, and_, func
                from app.models.knowledge_base import KnowledgeBaseDocument, DocumentStatus
                
                urgent_threshold = datetime.utcnow() + timedelta(days=7)
                
                result = await db.execute(
                    select(KnowledgeBaseDocument).where(
                        and_(
                            KnowledgeBaseDocument.processing_status == DocumentStatus.COMPLETED,
                            KnowledgeBaseDocument.visibility == "shared",
                            func.json_extract_path_text(
                                KnowledgeBaseDocument.organization_metadata, 
                                'expiration_date'
                            ).cast(func.date) <= urgent_threshold.date(),
                            func.json_extract_path_text(
                                KnowledgeBaseDocument.organization_metadata, 
                                'expiration_date'
                            ).cast(func.date) > datetime.utcnow().date()
                        )
                    )
                )
                urgent_docs = result.scalars().all()
                
                if urgent_docs:
                    logger.warning(f"⚠️  {len(urgent_docs)} documents expiring within 7 days")
                    
        except Exception as e:
            logger.error(f"Error in hourly reminder check: {e}")
    
    async def _weekly_quality_report(self):
        """Weekly quality report for knowledge base"""
        try:
            logger.info("📊 Generating weekly quality report...")
            
            async with AsyncSessionLocal() as db:
                stats = await self.rag_service.get_document_statistics(db=db)
                
                logger.info("📈 Knowledge Base Statistics:")
                logger.info(f"  - Total documents: {stats.get('total_documents', 0)}")
                logger.info(f"  - Active documents: {stats.get('active_documents', 0)}")
                logger.info(f"  - Expired documents: {stats.get('expired_documents', 0)}")
                logger.info(f"  - Pending review: {stats.get('pending_review', 0)}")
                logger.info(f"  - Average quality score: {stats.get('average_quality_score', 0)}")
                logger.info(f"  - Total chunks: {stats.get('total_chunks', 0)}")
                
                # Document type breakdown
                doc_types = stats.get('document_types', {})
                if doc_types:
                    logger.info("📋 Document types:")
                    for doc_type, count in doc_types.items():
                        logger.info(f"  - {doc_type}: {count}")
                        
        except Exception as e:
            logger.error(f"Error generating weekly quality report: {e}")
    
    async def run_manual_expiration_check(self) -> Dict[str, Any]:
        """Manually run expiration check (for API endpoint)"""
        try:
            async with AsyncSessionLocal() as db:
                expiring_docs = await self.workflow_service.check_expiring_documents(db=db)
                deactivated_ids = await self.workflow_service.deactivate_expired_documents(db=db)
                
                return {
                    "status": "success",
                    "reminders_sent": len(expiring_docs),
                    "documents_deactivated": len(deactivated_ids),
                    "expiring_documents": expiring_docs,
                    "deactivated_documents": deactivated_ids
                }
                
        except Exception as e:
            logger.error(f"Error in manual expiration check: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "scheduled_jobs": len(schedule.jobs),
            "next_run": str(schedule.next_run()) if schedule.jobs else None,
            "jobs": [
                {
                    "job": str(job.job_func),
                    "next_run": str(job.next_run),
                    "interval": str(job.interval)
                }
                for job in schedule.jobs
            ]
        }


# Global scheduler instance
scheduler_service = SchedulerService()


def start_knowledge_base_scheduler():
    """Start the knowledge base scheduler"""
    scheduler_service.start_scheduler()


def stop_knowledge_base_scheduler():
    """Stop the knowledge base scheduler"""
    scheduler_service.stop_scheduler()
