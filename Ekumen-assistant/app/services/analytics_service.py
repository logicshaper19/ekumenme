"""
Analytics Service for Knowledge Base and Document Performance
Tracks and aggregates analytics data for the knowledge base system
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.dialects.postgresql import JSONB

from app.models.analytics import DocumentAnalytics, QueryAnalytics, AnalyticsEvent
from app.models.knowledge_base import KnowledgeBaseDocument
from app.models.organization import Organization

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for managing analytics data and aggregations"""
    
    def __init__(self):
        pass
    
    async def get_document_analytics(
        self,
        document_id: str,
        db: AsyncSession,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific document
        """
        try:
            # Get document info
            doc_result = await db.execute(
                select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.id == document_id)
            )
            document = doc_result.scalar_one_or_none()
            
            if not document:
                return {"error": "Document not found"}
            
            # Calculate period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get analytics data
            analytics_result = await db.execute(
                select(DocumentAnalytics)
                .where(
                    and_(
                        DocumentAnalytics.document_id == document_id,
                        DocumentAnalytics.period_start >= start_date,
                        DocumentAnalytics.period_end <= end_date
                    )
                )
                .order_by(desc(DocumentAnalytics.period_start))
            )
            analytics_records = analytics_result.scalars().all()
            
            # Aggregate metrics
            total_retrievals = sum(record.retrievals for record in analytics_records)
            total_citations = sum(record.citations for record in analytics_records)
            total_interactions = sum(record.user_interactions for record in analytics_records)
            
            # Calculate satisfaction
            satisfaction_scores = [r.satisfaction_score for r in analytics_records if r.satisfaction_score is not None]
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None
            
            # Get recent query trends
            recent_queries = await self._get_recent_queries_for_document(document_id, db, period_days)
            
            return {
                "document": {
                    "id": str(document.id),
                    "filename": document.filename,
                    "document_type": document.document_type.value if document.document_type else None,
                    "visibility": document.visibility,
                    "created_at": document.created_at.isoformat() if document.created_at else None,
                    "last_accessed_at": document.last_accessed_at.isoformat() if document.last_accessed_at else None,
                    "query_count": document.query_count,
                    "quality_score": float(document.quality_score) if document.quality_score else None
                },
                "analytics": {
                    "period_days": period_days,
                    "total_retrievals": total_retrievals,
                    "total_citations": total_citations,
                    "total_interactions": total_interactions,
                    "citation_rate": (total_citations / total_retrievals * 100) if total_retrievals > 0 else 0,
                    "average_satisfaction": round(avg_satisfaction, 2) if avg_satisfaction else None,
                    "recent_queries": recent_queries
                },
                "trends": self._calculate_trends(analytics_records)
            }
            
        except Exception as e:
            logger.error(f"Error getting document analytics: {e}")
            return {"error": str(e)}
    
    async def _get_recent_queries_for_document(
        self,
        document_id: str,
        db: AsyncSession,
        period_days: int
    ) -> List[Dict[str, Any]]:
        """Get recent queries that retrieved this document"""
        try:
            # This would need to be implemented based on how we store query-document relationships
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting recent queries: {e}")
            return []
    
    def _calculate_trends(self, analytics_records: List[DocumentAnalytics]) -> Dict[str, Any]:
        """Calculate trend data from analytics records"""
        if len(analytics_records) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort by period start
        sorted_records = sorted(analytics_records, key=lambda x: x.period_start)
        
        # Calculate trend for retrievals
        recent_retrievals = sum(r.retrievals for r in sorted_records[-2:])
        previous_retrievals = sum(r.retrievals for r in sorted_records[:-2]) if len(sorted_records) > 2 else 0
        
        if previous_retrievals > 0:
            trend_percentage = ((recent_retrievals - previous_retrievals) / previous_retrievals) * 100
            trend_direction = "up" if trend_percentage > 0 else "down" if trend_percentage < 0 else "stable"
        else:
            trend_percentage = 0
            trend_direction = "stable"
        
        return {
            "trend_direction": trend_direction,
            "trend_percentage": round(trend_percentage, 2),
            "recent_period_retrievals": recent_retrievals,
            "previous_period_retrievals": previous_retrievals
        }
    
    async def get_knowledge_base_overview(
        self,
        organization_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Get overview analytics for the knowledge base
        """
        try:
            # Build base query
            query = select(KnowledgeBaseDocument)
            if organization_id:
                query = query.where(KnowledgeBaseDocument.organization_id == organization_id)
            
            result = await db.execute(query)
            all_docs = result.scalars().all()
            
            # Calculate overview metrics
            total_docs = len(all_docs)
            active_docs = len([doc for doc in all_docs if doc.is_active and not doc.is_expired])
            total_queries = sum(doc.query_count for doc in all_docs)
            
            # Most accessed documents
            most_accessed = sorted(all_docs, key=lambda x: x.query_count, reverse=True)[:5]
            
            # Document types breakdown
            type_counts = {}
            for doc in all_docs:
                doc_type = doc.document_type.value if doc.document_type else "unknown"
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            return {
                "total_documents": total_docs,
                "active_documents": active_docs,
                "total_queries": total_queries,
                "most_accessed_documents": [
                    {
                        "id": str(doc.id),
                        "filename": doc.filename,
                        "query_count": doc.query_count,
                        "last_accessed": doc.last_accessed_at.isoformat() if doc.last_accessed_at else None
                    }
                    for doc in most_accessed
                ],
                "document_types": type_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge base overview: {e}")
            return {"error": str(e)}
    
    async def create_document_analytics_record(
        self,
        document_id: str,
        document_name: str,
        retrievals: int = 0,
        citations: int = 0,
        interactions: int = 0,
        satisfaction_score: Optional[float] = None,
        db: AsyncSession = None
    ) -> bool:
        """
        Create or update a document analytics record
        """
        try:
            from datetime import datetime, timedelta
            
            # Get current period (daily for now)
            now = datetime.utcnow()
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
            
            # Check if record exists
            existing_result = await db.execute(
                select(DocumentAnalytics)
                .where(
                    and_(
                        DocumentAnalytics.document_id == document_id,
                        DocumentAnalytics.period_start == period_start,
                        DocumentAnalytics.period_end == period_end
                    )
                )
            )
            existing_record = existing_result.scalar_one_or_none()
            
            if existing_record:
                # Update existing record
                existing_record.retrievals += retrievals
                existing_record.citations += citations
                existing_record.user_interactions += interactions
                if satisfaction_score is not None:
                    # Update satisfaction score (weighted average)
                    total_ratings = existing_record.satisfaction_count + 1
                    existing_record.satisfaction_score = (
                        (existing_record.satisfaction_score * existing_record.satisfaction_count + satisfaction_score) / total_ratings
                    )
                    existing_record.satisfaction_count = total_ratings
            else:
                # Create new record
                new_record = DocumentAnalytics(
                    document_id=document_id,
                    document_name=document_name,
                    document_audience="public",  # Default for now
                    period_start=period_start,
                    period_end=period_end,
                    period_type="daily",
                    retrievals=retrievals,
                    citations=citations,
                    user_interactions=interactions,
                    satisfaction_score=satisfaction_score,
                    satisfaction_count=1 if satisfaction_score is not None else 0
                )
                db.add(new_record)
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error creating document analytics record: {e}")
            await db.rollback()
            return False
