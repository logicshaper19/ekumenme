"""
Voice Journal API endpoints
Handles voice journal entries and real-time validation
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.journal import JournalEntryCreate, JournalEntryResponse, ValidationResult
from app.services.auth_service import AuthService
from app.services.journal_service import JournalService
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
journal_service = JournalService()
voice_service = VoiceService()

@router.post("/entries", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    entry_data: JournalEntryCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new voice journal entry
    
    Args:
        entry_data: Journal entry data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JournalEntryResponse: Created journal entry
    """
    try:
        # Validate entry data
        validation_result = await journal_service.validate_entry(
            db=db,
            entry_data=entry_data,
            user=current_user
        )
        
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result.error_message
            )
        
        # Create journal entry
        entry = await journal_service.create_entry(
            db=db,
            user_id=current_user.id,
            entry_data=entry_data
        )
        
        logger.info(f"New journal entry created: {entry.id} for user {current_user.email}")
        
        return JournalEntryResponse(
            id=entry.id,
            content=entry.content,
            intervention_type=entry.intervention_type,
            parcel_id=entry.parcel_id,
            products_used=entry.products_used,
            weather_conditions=entry.weather_conditions,
            validation_status=entry.validation_status,
            created_at=entry.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Journal entry creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create journal entry"
        )

@router.post("/entries/validate", response_model=ValidationResult)
async def validate_journal_entry(
    entry_data: JournalEntryCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Validate a journal entry without creating it
    
    Args:
        entry_data: Journal entry data to validate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ValidationResult: Validation result with details
    """
    try:
        validation_result = await journal_service.validate_entry(
            db=db,
            entry_data=entry_data,
            user=current_user
        )
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Journal entry validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate journal entry"
        )

@router.post("/entries/transcribe", response_model=dict)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Transcribe audio file to text using Whisper
    
    Args:
        audio_file: Audio file to transcribe
        current_user: Current authenticated user
        
    Returns:
        dict: Transcription result
    """
    try:
        # Validate file type
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Transcribe audio
        transcription = await voice_service.transcribe_audio(audio_file)
        
        logger.info(f"Audio transcribed for user {current_user.email}")
        
        return {
            "transcription": transcription.text,
            "confidence": transcription.confidence,
            "language": transcription.language,
            "duration": transcription.duration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio transcription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )

@router.get("/entries", response_model=List[JournalEntryResponse])
async def get_journal_entries(
    skip: int = 0,
    limit: int = 50,
    farm_siret: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get user's journal entries
    
    Args:
        skip: Number of entries to skip
        limit: Maximum number of entries to return
        farm_siret: Filter by farm SIRET
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[JournalEntryResponse]: User's journal entries
    """
    try:
        entries = await journal_service.get_user_entries(
            db=db,
            user_id=current_user.id,
            farm_siret=farm_siret,
            skip=skip,
            limit=limit
        )
        
        return [
            JournalEntryResponse(
                id=entry.id,
                content=entry.content,
                intervention_type=entry.intervention_type,
                parcel_id=entry.parcel_id,
                products_used=entry.products_used,
                weather_conditions=entry.weather_conditions,
                validation_status=entry.validation_status,
                created_at=entry.created_at
            )
            for entry in entries
        ]
        
    except Exception as e:
        logger.error(f"Get journal entries error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve journal entries"
        )

@router.get("/entries/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific journal entry
    
    Args:
        entry_id: ID of the journal entry
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JournalEntryResponse: Journal entry details
    """
    try:
        entry = await journal_service.get_entry(
            db=db,
            entry_id=entry_id,
            user_id=current_user.id
        )
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        
        return JournalEntryResponse(
            id=entry.id,
            content=entry.content,
            intervention_type=entry.intervention_type,
            parcel_id=entry.parcel_id,
            products_used=entry.products_used,
            weather_conditions=entry.weather_conditions,
            validation_status=entry.validation_status,
            created_at=entry.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get journal entry error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve journal entry"
        )

@router.put("/entries/{entry_id}/validate", response_model=JournalEntryResponse)
async def validate_existing_entry(
    entry_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Re-validate an existing journal entry
    
    Args:
        entry_id: ID of the journal entry
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JournalEntryResponse: Updated journal entry
    """
    try:
        entry = await journal_service.get_entry(
            db=db,
            entry_id=entry_id,
            user_id=current_user.id
        )
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        
        # Re-validate entry
        validation_result = await journal_service.validate_existing_entry(
            db=db,
            entry=entry,
            user=current_user
        )
        
        # Update entry with validation result
        entry.validation_status = validation_result.status
        entry.validation_notes = validation_result.notes
        
        await db.commit()
        await db.refresh(entry)
        
        logger.info(f"Journal entry {entry_id} re-validated")
        
        return JournalEntryResponse(
            id=entry.id,
            content=entry.content,
            intervention_type=entry.intervention_type,
            parcel_id=entry.parcel_id,
            products_used=entry.products_used,
            weather_conditions=entry.weather_conditions,
            validation_status=entry.validation_status,
            created_at=entry.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Journal entry validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate journal entry"
        )
