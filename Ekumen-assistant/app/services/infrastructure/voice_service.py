"""
Voice service for agricultural chatbot
Handles voice transcription and text-to-speech
"""

from typing import Optional, AsyncGenerator
import asyncio
import aiohttp
import base64
import io
import logging
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class VoiceTranscriptionResult:
    """Result of voice transcription"""
    def __init__(self, text: str, confidence: float, language: str, duration: Optional[float] = None):
        self.text = text
        self.confidence = confidence
        self.language = language
        self.duration = duration


class VoiceService:
    """Service for voice processing (transcription and synthesis) using OpenAI APIs"""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.elevenlabs_api_key = settings.ELEVENLABS_API_KEY
        self.whisper_model = settings.WHISPER_MODEL
        self.elevenlabs_voice_id = settings.ELEVENLABS_VOICE_ID
    
    async def transcribe_audio(self, audio_file) -> VoiceTranscriptionResult:
        """Transcribe audio file using OpenAI Whisper API"""
        try:
            # Read audio file
            audio_content = await audio_file.read()
            
            # Create a file-like object from bytes
            audio_io = io.BytesIO(audio_content)
            audio_io.name = "audio.webm"
            
            # Transcribe using OpenAI Whisper
            transcript = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_io,
                language="fr"  # French for agricultural context
            )
            
            logger.info(f"Audio transcribed successfully: {len(transcript.text)} characters")
            
            return VoiceTranscriptionResult(
                text=transcript.text,
                confidence=0.95,  # Whisper doesn't provide confidence scores
                language="fr",
                duration=None  # Could be calculated from audio file
            )
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise Exception(f"Erreur lors de la transcription: {str(e)}")
    
    async def transcribe_audio_bytes(self, audio_bytes: bytes) -> VoiceTranscriptionResult:
        """Transcribe audio bytes using OpenAI Whisper API"""
        try:
            # Create a file-like object from bytes
            audio_io = io.BytesIO(audio_bytes)
            audio_io.name = "audio.webm"
            
            # Transcribe using OpenAI Whisper
            transcript = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_io,
                language="fr"  # French for agricultural context
            )
            
            logger.info(f"Audio bytes transcribed successfully: {len(transcript.text)} characters")
            
            return VoiceTranscriptionResult(
                text=transcript.text,
                confidence=0.95,
                language="fr",
                duration=None
            )
            
        except Exception as e:
            logger.error(f"Error transcribing audio bytes: {e}")
            raise Exception(f"Erreur lors de la transcription: {str(e)}")
    
    async def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Convert text to speech using OpenAI TTS API"""
        try:
            # Use OpenAI TTS instead of ElevenLabs for better integration
            response = await self.openai_client.audio.speech.create(
                model="tts-1",  # Fast model for real-time
                voice="nova",   # Good French voice
                input=text,
                response_format="opus"  # Best for streaming
            )
            
            logger.info(f"Speech synthesized successfully: {len(text)} characters")
            return response.content
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise Exception(f"Erreur lors de la synthèse vocale: {str(e)}")
    
    async def synthesize_speech_streaming(self, text: str, voice_id: Optional[str] = None) -> AsyncGenerator[bytes, None]:
        """Stream text-to-speech using OpenAI TTS API"""
        try:
            # For streaming, we'll generate the full audio and yield it in chunks
            audio_bytes = await self.synthesize_speech(text, voice_id)
            
            # Yield in chunks for streaming effect
            chunk_size = 4096
            for i in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[i:i + chunk_size]
                await asyncio.sleep(0.01)  # Small delay for streaming effect
                
        except Exception as e:
            logger.error(f"Error in streaming speech synthesis: {e}")
            raise Exception(f"Erreur lors de la synthèse vocale en streaming: {str(e)}")
    
    async def transcribe_audio_file(self, file_path: str) -> VoiceTranscriptionResult:
        """Transcribe audio file from file path"""
        try:
            with open(file_path, 'rb') as audio_file:
                # For now, return a mock transcription
                # TODO: Implement actual file-based transcription
                return VoiceTranscriptionResult(
                    text="Transcription de fichier en cours de développement",
                    confidence=0.90,
                    language="fr",
                    duration=10.0
                )
                
        except Exception as e:
            raise Exception(f"Erreur lors de la transcription du fichier: {str(e)}")
    
    async def validate_audio_file(self, audio_file) -> bool:
        """Validate audio file format and size"""
        try:
            # Check file size
            audio_content = await audio_file.read()
            if len(audio_content) > settings.MAX_FILE_SIZE:
                return False
            
            # Check file type
            content_type = audio_file.content_type
            if content_type not in settings.ALLOWED_FILE_TYPES:
                return False
            
            # Reset file pointer
            await audio_file.seek(0)
            
            return True
            
        except Exception:
            return False
    
    async def get_supported_voices(self) -> list:
        """Get list of supported voices for text-to-speech"""
        # TODO: Implement actual voice list from ElevenLabs API
        return [
            {
                "voice_id": "pNInz6obpgDQGcFmaJgB",
                "name": "Adam",
                "language": "fr",
                "gender": "male"
            },
            {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",
                "name": "Bella",
                "language": "fr", 
                "gender": "female"
            }
        ]
    
    async def get_voice_settings(self, voice_id: str) -> dict:
        """Get voice settings for a specific voice"""
        # TODO: Implement actual voice settings retrieval
        return {
            "voice_id": voice_id,
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True
        }
    
    async def update_voice_settings(self, voice_id: str, settings: dict) -> bool:
        """Update voice settings"""
        # TODO: Implement actual voice settings update
        return True
    
    async def create_custom_voice(self, name: str, description: str, audio_samples: list) -> str:
        """Create a custom voice from audio samples"""
        # TODO: Implement custom voice creation
        return "custom_voice_id"
    
    async def delete_custom_voice(self, voice_id: str) -> bool:
        """Delete a custom voice"""
        # TODO: Implement custom voice deletion
        return True
    
    async def get_usage_statistics(self) -> dict:
        """Get voice service usage statistics"""
        # TODO: Implement actual usage statistics
        return {
            "characters_used": 0,
            "characters_limit": 10000,
            "voices_used": 0,
            "voices_limit": 5
        }
