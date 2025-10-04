"""
Journal Service - Simplified Voice Processing Pipeline
Handles voice input, transcription, and async validation
"""

from typing import Dict, List, Optional, Any
import logging
import asyncio
import time
from datetime import datetime
import json

from app.services.infrastructure.voice_service import VoiceService
from app.agents.real_journal_agent import RealJournalAgent
from app.models.intervention import VoiceJournalEntry
from app.core.database import get_async_db
from app.services.monitoring.voice_monitoring import voice_monitor, monitor_voice_function
from sqlalchemy import select

logger = logging.getLogger(__name__)


class JournalService:
    """
    Simplified journal service that:
    1. Transcribes voice input
    2. Saves entry immediately (no blocking validation)
    3. Queues async validation
    4. Returns entry ID for immediate feedback
    """
    
    def __init__(self):
        self.voice_service = VoiceService()
        self.journal_agent = RealJournalAgent()
        self.validation_queue = asyncio.Queue()
        
        # Start validation worker
        asyncio.create_task(self._validation_worker())
    
    @monitor_voice_function('process_voice_input')
    async def process_voice_input(
        self, 
        audio_data: bytes, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process voice input through simplified pipeline:
        1. Transcribe audio
        2. Save entry immediately
        3. Queue for async validation
        4. Return entry ID
        
        Args:
            audio_data: Raw audio bytes
            user_context: User and farm context
            
        Returns:
            Processing result with entry ID
        """
        try:
            # Step 1: Transcribe audio
            logger.info("Transcribing audio...")
            transcription_tracking_id = voice_monitor.record_transcription_start(
                user_context.get("user_id", "unknown"),
                user_context.get("org_id", "unknown")
            )
            
            start_time = time.time()
            transcription_result = await self.voice_service.transcribe_audio_bytes(audio_data)
            transcription_duration = (time.time() - start_time) * 1000
            
            voice_monitor.record_transcription_complete(
                transcription_tracking_id,
                transcription_duration,
                success=transcription_result is not None,
                transcript_length=len(transcription_result.text) if transcription_result else None
            )
            
            if not transcription_result:
                return {
                    "success": False,
                    "error": "Transcription failed",
                    "user_context": user_context
                }
            
            transcript = transcription_result.text
            logger.info(f"Transcription: {transcript}")
            
            # Step 2: Create basic journal entry
            entry_data = {
                "raw_transcript": transcript,
                "user_id": user_context.get("user_id"),
                "org_id": user_context.get("org_id"),
                "created_at": datetime.now().isoformat(),
                "processing_status": "pending_validation"
            }
            
            # Step 3: Save entry immediately
            entry_id = await self._save_entry_immediately(entry_data)
            logger.info(f"Entry saved with ID: {entry_id}")
            
            # Step 4: Queue for async validation
            validation_task = {
                "entry_id": entry_id,
                "transcript": transcript,
                "user_context": user_context,
                "queued_at": datetime.now().isoformat()
            }
            
            await self.validation_queue.put(validation_task)
            logger.info(f"Entry {entry_id} queued for validation")
            
            # Step 5: Return immediate response
            return {
                "success": True,
                "entry_id": entry_id,
                "transcript": transcript,
                "status": "saved_pending_validation",
                "message": "Entry saved successfully, validation in progress",
                "user_context": user_context
            }
            
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_context": user_context
            }
    
    async def _save_entry_immediately(self, entry_data: Dict[str, Any]) -> str:
        """Save journal entry immediately without validation"""
        try:
            start_time = time.time()
            
            async for db in get_async_db():
                # Create minimal journal entry
                journal_entry = VoiceJournalEntry(
                    user_id=entry_data.get("user_id"),
                    raw_transcript=entry_data.get("raw_transcript"),
                    processing_status="pending_validation",
                    created_at=datetime.now()
                )
                
                db.add(journal_entry)
                await db.commit()
                await db.refresh(journal_entry)
                
                entry_id = str(journal_entry.id)
                save_duration = (time.time() - start_time) * 1000
                
                # Record save completion
                voice_monitor.record_save_complete(
                    entry_id,
                    entry_data.get("user_id", "unknown"),
                    entry_data.get("org_id", "unknown"),
                    save_duration,
                    success=True
                )
                
                return entry_id
                
        except Exception as e:
            logger.error(f"Error saving entry immediately: {e}")
            
            # Record save failure
            save_duration = (time.time() - start_time) * 1000
            voice_monitor.record_save_complete(
                "unknown",
                entry_data.get("user_id", "unknown"),
                entry_data.get("org_id", "unknown"),
                save_duration,
                success=False,
                error_message=str(e)
            )
            
            raise
    
    async def _validation_worker(self):
        """Background worker that processes validation queue"""
        logger.info("Validation worker started")
        
        while True:
            try:
                # Get next validation task
                task = await self.validation_queue.get()
                entry_id = task["entry_id"]
                transcript = task["transcript"]
                user_context = task["user_context"]
                
                logger.info(f"Processing validation for entry {entry_id}")
                
                # Record validation start
                validation_tracking_id = voice_monitor.record_validation_start(
                    entry_id, 
                    user_context.get("user_id", "unknown"),
                    user_context.get("org_id", "unknown")
                )
                
                # Process with journal agent
                start_time = time.time()
                result = await self.journal_agent.process_journal_entry(
                    transcript=transcript,
                    user_context=user_context
                )
                validation_duration = (time.time() - start_time) * 1000
                
                # Record validation complete
                voice_monitor.record_validation_complete(
                    validation_tracking_id,
                    entry_id,
                    validation_duration,
                    success=result.get("success", False),
                    validation_results=result
                )
                
                # Update entry with validation results
                await self._update_entry_with_validation(entry_id, result)
                
                # Mark task as done
                self.validation_queue.task_done()
                
                logger.info(f"Validation completed for entry {entry_id}")
                
            except Exception as e:
                logger.error(f"Error in validation worker: {e}")
                # Mark task as done even if failed
                if 'task' in locals():
                    self.validation_queue.task_done()
                
                # Wait before retrying
                await asyncio.sleep(5)
    
    async def _update_entry_with_validation(
        self, 
        entry_id: str, 
        validation_result: Dict[str, Any]
    ):
        """Update journal entry with validation results"""
        try:
            async for db in get_async_db():
                # Get the entry
                entry = await db.get(VoiceJournalEntry, entry_id)
                if not entry:
                    logger.error(f"Entry {entry_id} not found for update")
                    return
                
                # Update with validation results
                entry.processing_status = "validated" if validation_result.get("success") else "validation_failed"
                entry.validation_results = validation_result
                entry.validated_at = datetime.now()
                
                # Extract structured data if available
                if validation_result.get("success"):
                    # Try to extract structured data from agent output
                    agent_output = validation_result.get("agent_output", "")
                    # This would need more sophisticated parsing in a real implementation
                    entry.structured_data = {
                        "agent_output": agent_output,
                        "validation_success": True
                    }
                
                await db.commit()
                logger.info(f"Entry {entry_id} updated with validation results")
                
        except Exception as e:
            logger.error(f"Error updating entry {entry_id}: {e}")
    
    async def get_entry_status(self, entry_id: str) -> Dict[str, Any]:
        """Get current status of a journal entry"""
        try:
            async for db in get_async_db():
                entry = await db.get(VoiceJournalEntry, entry_id)
                if not entry:
                    return {
                        "success": False,
                        "error": "Entry not found"
                    }
                
                return {
                    "success": True,
                    "entry_id": entry_id,
                    "status": entry.processing_status,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "validated_at": entry.validated_at.isoformat() if entry.validated_at else None,
                    "transcript": entry.raw_transcript,
                    "validation_results": entry.validation_results
                }
                
        except Exception as e:
            logger.error(f"Error getting entry status {entry_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_recent_entries(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get recent journal entries for a user"""
        try:
            async for db in get_async_db():
                result = await db.execute(
                    select(VoiceJournalEntry)
                    .where(VoiceJournalEntry.user_id == user_id)
                    .order_by(VoiceJournalEntry.created_at.desc())
                    .limit(limit)
                )
                entries = result.scalars().all()
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "entries": [
                        {
                            "id": str(entry.id),
                            "transcript": entry.raw_transcript,
                            "status": entry.processing_status,
                            "created_at": entry.created_at.isoformat() if entry.created_at else None,
                            "validated_at": entry.validated_at.isoformat() if entry.validated_at else None
                        }
                        for entry in entries
                    ],
                    "count": len(entries)
                }
                
        except Exception as e:
            logger.error(f"Error getting recent entries for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def retry_validation(self, entry_id: str) -> Dict[str, Any]:
        """Retry validation for a failed entry"""
        try:
            async for db in get_async_db():
                entry = await db.get(VoiceJournalEntry, entry_id)
                if not entry:
                    return {
                        "success": False,
                        "error": "Entry not found"
                    }
                
                # Queue for re-validation
                validation_task = {
                    "entry_id": entry_id,
                    "transcript": entry.raw_transcript,
                    "user_context": {"user_id": entry.user_id},
                    "queued_at": datetime.now().isoformat(),
                    "retry": True
                }
                
                await self.validation_queue.put(validation_task)
                
                return {
                    "success": True,
                    "entry_id": entry_id,
                    "message": "Entry queued for re-validation"
                }
                
        except Exception as e:
            logger.error(f"Error retrying validation for entry {entry_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current validation queue status"""
        return {
            "queue_size": self.validation_queue.qsize(),
            "worker_running": True,  # Simplified - in real implementation, track worker status
            "timestamp": datetime.now().isoformat()
        }
