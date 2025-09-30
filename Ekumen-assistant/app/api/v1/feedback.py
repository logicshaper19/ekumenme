"""
Feedback API endpoints
Handles user feedback on AI responses (thumbs up/down)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_sync_db
from app.models.feedback import ResponseFeedback, FeedbackType, FeedbackCategory
from app.models.user import User
from app.api.v1.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    message_id: UUID
    conversation_id: UUID
    feedback_type: FeedbackType
    feedback_category: Optional[FeedbackCategory] = None
    comment: Optional[str] = None
    query_text: Optional[str] = None
    response_text: Optional[str] = None
    context_metadata: Optional[dict] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: UUID
    message_id: UUID
    conversation_id: UUID
    feedback_type: FeedbackType
    feedback_category: Optional[FeedbackCategory]
    comment: Optional[str]
    reviewed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """Schema for feedback statistics"""
    total_feedback: int
    thumbs_up: int
    thumbs_down: int
    thumbs_up_rate: float
    needs_review: int
    reviewed: int


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Submit feedback on an AI response.
    
    - **message_id**: ID of the message being rated
    - **conversation_id**: ID of the conversation
    - **feedback_type**: thumbs_up or thumbs_down
    - **feedback_category**: (optional) category for negative feedback
    - **comment**: (optional) detailed feedback comment
    """
    try:
        # Validate that thumbs_down has a category or comment
        if feedback.feedback_type == FeedbackType.THUMBS_DOWN:
            if not feedback.feedback_category and not feedback.comment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Thumbs down feedback requires either a category or comment"
                )
        
        # Check if feedback already exists for this message
        existing_feedback = db.query(ResponseFeedback).filter(
            ResponseFeedback.message_id == feedback.message_id,
            ResponseFeedback.user_id == current_user.id
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.feedback_type = feedback.feedback_type
            existing_feedback.feedback_category = feedback.feedback_category
            existing_feedback.comment = feedback.comment
            existing_feedback.context_metadata = feedback.context_metadata
            db.commit()
            db.refresh(existing_feedback)
            
            logger.info(
                f"Updated feedback for message {feedback.message_id} "
                f"by user {current_user.email}: {feedback.feedback_type.value}"
            )
            
            return existing_feedback
        
        # Create new feedback
        new_feedback = ResponseFeedback(
            user_id=current_user.id,
            conversation_id=feedback.conversation_id,
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type,
            feedback_category=feedback.feedback_category,
            comment=feedback.comment,
            query_text=feedback.query_text,
            response_text=feedback.response_text,
            context_metadata=feedback.context_metadata
        )
        
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        
        logger.info(
            f"Created feedback for message {feedback.message_id} "
            f"by user {current_user.email}: {feedback.feedback_type.value}"
        )
        
        return new_feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating feedback: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/message/{message_id}", response_model=Optional[FeedbackResponse])
async def get_message_feedback(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Get feedback for a specific message by the current user.
    
    Returns None if no feedback exists.
    """
    feedback = db.query(ResponseFeedback).filter(
        ResponseFeedback.message_id == message_id,
        ResponseFeedback.user_id == current_user.id
    ).first()
    
    return feedback


@router.get("/conversation/{conversation_id}", response_model=List[FeedbackResponse])
async def get_conversation_feedback(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Get all feedback for a conversation by the current user.
    """
    feedback_list = db.query(ResponseFeedback).filter(
        ResponseFeedback.conversation_id == conversation_id,
        ResponseFeedback.user_id == current_user.id
    ).order_by(desc(ResponseFeedback.created_at)).all()
    
    return feedback_list


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Get feedback statistics for the current user.
    """
    # Get all feedback by user
    all_feedback = db.query(ResponseFeedback).filter(
        ResponseFeedback.user_id == current_user.id
    ).all()
    
    total = len(all_feedback)
    thumbs_up = sum(1 for f in all_feedback if f.is_positive)
    thumbs_down = sum(1 for f in all_feedback if f.is_negative)
    needs_review = sum(1 for f in all_feedback if f.needs_review)
    reviewed = sum(1 for f in all_feedback if f.reviewed)
    
    thumbs_up_rate = (thumbs_up / total * 100) if total > 0 else 0.0
    
    return FeedbackStats(
        total_feedback=total,
        thumbs_up=thumbs_up,
        thumbs_down=thumbs_down,
        thumbs_up_rate=round(thumbs_up_rate, 2),
        needs_review=needs_review,
        reviewed=reviewed
    )


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Delete feedback (only by the user who created it).
    """
    feedback = db.query(ResponseFeedback).filter(
        ResponseFeedback.id == feedback_id,
        ResponseFeedback.user_id == current_user.id
    ).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    db.delete(feedback)
    db.commit()
    
    logger.info(f"Deleted feedback {feedback_id} by user {current_user.email}")
    
    return None


# Admin endpoints for reviewing feedback
@router.get("/admin/needs-review", response_model=List[FeedbackResponse])
async def get_feedback_needing_review(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Get all negative feedback that needs review (admin only).
    """
    # TODO: Add admin permission check
    
    feedback_list = db.query(ResponseFeedback).filter(
        ResponseFeedback.feedback_type == FeedbackType.THUMBS_DOWN,
        ResponseFeedback.reviewed == False
    ).order_by(desc(ResponseFeedback.created_at)).offset(skip).limit(limit).all()
    
    return feedback_list

