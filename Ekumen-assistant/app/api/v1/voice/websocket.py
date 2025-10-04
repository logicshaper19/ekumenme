"""
Voice WebSocket endpoints for streaming voice assistant
Handles real-time voice streaming with Whisper transcription and TTS response
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from app.services.shared.auth_service import AuthService
from app.services.infrastructure.voice_service import VoiceService
from app.services.shared.chat_service import ChatService
from app.services.shared.tool_registry_service import get_tool_registry
from app.services.journal_service import JournalService
from app.services.validation.intervention_checker import InterventionChecker
import logging
import json
import asyncio
import io
import base64
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
voice_service = VoiceService()
chat_service = ChatService()
tool_registry = get_tool_registry()
journal_service = JournalService()
intervention_checker = InterventionChecker()

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Connection management
class VoiceWebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.connection_users: Dict[str, str] = {}
        self.connection_orgs: Dict[str, str] = {}
        self.audio_buffers: Dict[str, list] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str, org_id: str):
        """Add a new WebSocket connection"""
        self.connections[connection_id] = websocket
        self.connection_users[connection_id] = user_id
        self.connection_orgs[connection_id] = org_id
        self.audio_buffers[connection_id] = []
        logger.info(f"Voice WebSocket connection {connection_id} established for user {user_id}")

    async def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            del self.connection_users[connection_id]
            del self.connection_orgs[connection_id]
            if connection_id in self.audio_buffers:
                del self.audio_buffers[connection_id]
            logger.info(f"Voice WebSocket connection {connection_id} disconnected")

    async def send_message(self, connection_id: str, message: dict):
        """Send message to specific connection"""
        if connection_id in self.connections:
            try:
                await self.connections[connection_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                await self.disconnect(connection_id)

    def add_audio_chunk(self, connection_id: str, audio_chunk: bytes):
        """Add audio chunk to buffer"""
        if connection_id in self.audio_buffers:
            self.audio_buffers[connection_id].append(audio_chunk)
    
    def get_complete_audio(self, connection_id: str) -> bytes:
        """Get complete audio data for a connection"""
        if connection_id in self.audio_buffers:
            return b''.join(self.audio_buffers[connection_id])
        return b''

    def get_audio_buffer(self, connection_id: str) -> bytes:
        """Get complete audio buffer and clear it"""
        if connection_id in self.audio_buffers:
            buffer = b''.join(self.audio_buffers[connection_id])
            self.audio_buffers[connection_id] = []
            return buffer
        return b''

# Global WebSocket manager instance
voice_ws_manager = VoiceWebSocketManager()

@router.websocket("/ws/voice")
async def voice_stream(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for streaming voice assistant
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token
    """
    connection_id = None

    try:
        # Verify token and get user
        user = await auth_service.verify_websocket_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Extract org_id from token
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        
        if not org_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Organization not selected")
            return

        # Accept the WebSocket connection
        await websocket.accept()
        connection_id = f"voice_{user.id}_{org_id}_{int(asyncio.get_event_loop().time())}"
        
        # Register connection
        await voice_ws_manager.connect(websocket, connection_id, str(user.id), org_id)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "connection_id": connection_id,
            "message": "Connected to voice assistant"
        })

        logger.info(f"Voice WebSocket connection {connection_id} established for user {user.id}")

        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive()
                
                if data["type"] == "websocket.receive":
                    if "bytes" in data:
                        # Handle binary audio data
                        await handle_audio_data(websocket, connection_id, data["bytes"])
                    elif "text" in data:
                        # Handle text messages
                        message_data = json.loads(data["text"])
                        await handle_text_message(websocket, connection_id, message_data)
                        
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket connection {connection_id} disconnected")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        if connection_id:
            await voice_ws_manager.disconnect(connection_id)

async def handle_audio_data(websocket: WebSocket, connection_id: str, audio_bytes: bytes):
    """Handle incoming audio data"""
    try:
        # Add audio chunk to buffer
        voice_ws_manager.add_audio_chunk(connection_id, audio_bytes)
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "audio_received",
            "timestamp": asyncio.get_event_loop().time()
        })
        
    except Exception as e:
        logger.error(f"Error handling audio data: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error processing audio: {str(e)}"
        })

async def handle_text_message(websocket: WebSocket, connection_id: str, message_data: dict):
    """Handle text messages from client"""
    try:
        message_type = message_data.get("type")
        
        if message_type == "start_voice_input":
            # Client is starting to record
            await websocket.send_json({
                "type": "voice_input_started",
                "message": "Ready to receive audio"
            })
            
        elif message_type == "stop_voice_input":
            # Client stopped recording, process the audio
            await process_voice_input(websocket, connection_id)
            
        elif message_type == "ping":
            # Handle ping/pong for connection health
            await websocket.send_json({
                "type": "pong",
                "timestamp": message_data.get("timestamp")
            })
            
        elif message_type == "confirmation_response":
            # Handle farmer's confirmation responses
            await handle_confirmation_response(websocket, connection_id, message_data)
            
        else:
            logger.warning(f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

async def process_voice_input(websocket: WebSocket, connection_id: str):
    """Process complete voice input and generate response"""
    try:
        # Get complete audio buffer
        audio_data = voice_ws_manager.get_audio_buffer(connection_id)
        
        if not audio_data:
            await websocket.send_json({
                "type": "error",
                "message": "No audio data received"
            })
            return
        
        # Send processing status
        await websocket.send_json({
            "type": "processing_started",
            "message": "Transcribing audio..."
        })
        
        # 1. Transcribe audio using Whisper
        transcript = await transcribe_audio(audio_data)
        
        # Send transcript to display
        await websocket.send_json({
            "type": "user_transcript",
            "text": transcript,
            "is_final": True
        })
        
        # 2. Generate AI response and stream it
        await stream_ai_response(websocket, connection_id, transcript)
        
    except Exception as e:
        logger.error(f"Error processing voice input: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error processing voice input: {str(e)}"
        })

async def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert audio to text using OpenAI Whisper"""
    try:
        # Create a file-like object from bytes
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.webm"
        
        # Transcribe using OpenAI Whisper
        transcript = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="fr"  # French for agricultural context
        )
        
        return transcript.text
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise Exception(f"Transcription failed: {str(e)}")

async def stream_ai_response(websocket: WebSocket, connection_id: str, user_text: str):
    """Stream AI response as text + audio"""
    try:
        # Send response started status
        await websocket.send_json({
            "type": "ai_response_started",
            "message": "Generating response..."
        })
        
        # Buffer to collect text for TTS
        text_buffer = ""
        sentence_endings = ['.', '!', '?', '\n']
        
        # Get user and org context
        user_id = voice_ws_manager.connection_users.get(connection_id)
        org_id = voice_ws_manager.connection_orgs.get(connection_id)
        
        # 3. Stream AI thinking (your chat assistant)
        async for chunk in stream_chat_response(user_text, user_id, org_id):
            # Send text chunk to display immediately
            await websocket.send_json({
                "type": "ai_text_chunk",
                "text": chunk
            })
            
            # Add to buffer
            text_buffer += chunk
            
            # 4. When we have a complete sentence, generate audio
            if any(ending in chunk for ending in sentence_endings):
                # Generate audio for this sentence
                if text_buffer.strip():
                    asyncio.create_task(
                        generate_and_stream_audio(websocket, text_buffer.strip())
                    )
                text_buffer = ""  # Reset buffer
        
        # Handle any remaining text
        if text_buffer.strip():
            await generate_and_stream_audio(websocket, text_buffer.strip())
            
        # Send completion status
        await websocket.send_json({
            "type": "ai_response_complete",
            "message": "Response complete"
        })
        
    except Exception as e:
        logger.error(f"Error streaming AI response: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error generating response: {str(e)}"
        })

async def stream_chat_response(user_text: str, user_id: str, org_id: str):
    """Stream chat response from your agricultural assistant"""
    try:
        # Create a conversation message
        from app.schemas.chat import ChatMessage
        message = ChatMessage(
            content=user_text,
            role="user"
        )
        
        # Use your existing chat service with streaming
        # This integrates with your existing agricultural agents
        async for chunk in chat_service.stream_response(
            message=message,
            user_id=user_id,
            org_id=org_id,
            conversation_id="voice_assistant"  # Use a dedicated conversation for voice
        ):
            if chunk.get("content"):
                yield chunk["content"]
                
    except Exception as e:
        logger.error(f"Error in chat response streaming: {e}")
        yield f"Désolé, une erreur s'est produite: {str(e)}"

async def generate_and_stream_audio(websocket: WebSocket, text: str):
    """Generate and stream audio for text using OpenAI TTS"""
    try:
        # Generate audio using OpenAI TTS
        response = await openai_client.audio.speech.create(
            model="tts-1",  # Fast model for streaming
            voice="nova",   # Good French voice
            input=text,
            response_format="opus"  # Best for streaming
        )
        
        # Convert response to bytes
        audio_bytes = response.content
        
        # Send audio chunk
        await websocket.send_json({
            "type": "audio_chunk",
            "data": base64.b64encode(audio_bytes).decode('utf-8'),
            "text": text  # Include text for debugging
        })
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        # Send error but don't break the flow
        await websocket.send_json({
            "type": "audio_error",
            "message": f"Error generating audio: {str(e)}"
        })

@router.websocket("/ws/voice/journal")
async def voice_journal_stream(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for voice journal entries
    Specialized for farm activity recording
    """
    connection_id = None

    try:
        # Verify token and get user
        user = await auth_service.verify_websocket_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Extract org_id from token
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        
        if not org_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Organization not selected")
            return

        # Accept the WebSocket connection
        await websocket.accept()
        connection_id = f"voice_journal_{user.id}_{org_id}_{int(asyncio.get_event_loop().time())}"
        
        # Register connection
        await voice_ws_manager.connect(websocket, connection_id, str(user.id), org_id)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "connection_id": connection_id,
            "message": "Connected to voice journal"
        })

        logger.info(f"Voice Journal WebSocket connection {connection_id} established for user {user.id}")

        # Message handling loop (similar to voice_stream but with journal-specific processing)
        while True:
            try:
                data = await websocket.receive()
                
                if data["type"] == "websocket.receive":
                    if "bytes" in data:
                        await handle_journal_audio_data(websocket, connection_id, data["bytes"])
                    elif "text" in data:
                        message_data = json.loads(data["text"])
                        await handle_journal_text_message(websocket, connection_id, message_data)
                        
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing journal WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        logger.info(f"Voice Journal WebSocket connection {connection_id} disconnected")
    except Exception as e:
        logger.error(f"Voice Journal WebSocket error: {e}")
        if connection_id:
            await voice_ws_manager.disconnect(connection_id)

async def handle_journal_audio_data(websocket: WebSocket, connection_id: str, audio_bytes: bytes):
    """Handle audio data for journal entries"""
    # Similar to handle_audio_data but with journal-specific processing
    await handle_audio_data(websocket, connection_id, audio_bytes)

async def handle_journal_text_message(websocket: WebSocket, connection_id: str, message_data: dict):
    """Handle text messages for journal entries"""
    try:
        message_type = message_data.get("type")
        
        if message_type == "stop_voice_input":
            # Process journal entry
            await process_journal_entry(websocket, connection_id)
        else:
            # Delegate to regular handler
            await handle_text_message(websocket, connection_id, message_data)
            
    except Exception as e:
        logger.error(f"Error handling journal text message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

async def process_journal_entry(websocket: WebSocket, connection_id: str):
    """Process voice journal entry and create structured data"""
    try:
        # Get complete audio buffer
        audio_data = voice_ws_manager.get_audio_buffer(connection_id)
        
        if not audio_data:
            await websocket.send_json({
                "type": "error",
                "message": "No audio data received"
            })
            return
        
        # Send processing status
        await websocket.send_json({
            "type": "processing_started",
            "message": "Processing journal entry..."
        })
        
        # 1. Transcribe audio
        transcript = await transcribe_audio(audio_data)
        
        # Send transcript
        await websocket.send_json({
            "type": "user_transcript",
            "text": transcript,
            "is_final": True
        })
        
        # 2. Process with simplified journal service
        user_context = {
            "user_id": voice_ws_manager.connection_users.get(connection_id),
            "org_id": voice_ws_manager.connection_orgs.get(connection_id)
        }
        
        # Get audio data from connection buffer
        audio_data = voice_ws_manager.get_complete_audio(connection_id)
        
        # Process with journal service (transcribe + save + queue validation)
        journal_result = await journal_service.process_voice_input(audio_data, user_context)
        
        if not journal_result.get("success"):
            await websocket.send_json({
                "type": "error",
                "message": f"Erreur lors du traitement: {journal_result.get('error', 'Erreur inconnue')}"
            })
            return
        
        # Send immediate response
        await websocket.send_json({
            "type": "journal_saved",
            "entry_id": journal_result.get("entry_id"),
            "transcript": journal_result.get("transcript"),
            "status": "saved_pending_validation",
            "message": "Entrée enregistrée, validation en cours..."
        })
        
        # Send voice confirmation
        confirmation_text = f"J'ai enregistré votre intervention: {journal_result.get('transcript', '')}. Validation en cours..."
        await websocket.send_json({
            "type": "ai_text_chunk",
            "text": confirmation_text
        })
        
        # Generate audio confirmation
        await generate_and_stream_audio(websocket, confirmation_text)
        
        # Note: Validation happens asynchronously in the background
        # The entry is already saved, validation will update it when complete
        
    except Exception as e:
        logger.error(f"Error processing journal entry: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error processing journal entry: {str(e)}"
        })

async def extract_journal_data(transcript: str) -> dict:
    """Extract structured data from journal transcript"""
    try:
        # Use AI to extract structured data from the transcript
        prompt = f"""
        Extrait les informations structurées de cette entrée de journal agricole:
        
        "{transcript}"
        
        Retourne un JSON avec les champs suivants:
        - intervention_type: type d'intervention (semis, traitement, récolte, etc.)
        - parcelle: nom ou identifiant de la parcelle
        - products_used: liste des produits utilisés avec quantités
        - equipment_used: équipement utilisé
        - weather_conditions: conditions météo
        - temperature_celsius: température en degrés Celsius
        - humidity_percent: humidité en pourcentage
        - wind_speed_kmh: vitesse du vent en km/h
        - notes: notes supplémentaires
        - duration_minutes: durée de l'intervention en minutes
        
        Si une information n'est pas mentionnée, utilise null.
        """
        
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en agriculture. Extrait les informations structurées des entrées de journal."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        # Parse JSON response
        import json
        structured_data = json.loads(response.choices[0].message.content)
        
        return structured_data
        
    except Exception as e:
        logger.error(f"Error extracting journal data: {e}")
        return {
            "intervention_type": "unknown",
            "content": transcript,
            "notes": f"Erreur lors de l'extraction: {str(e)}"
        }

async def validate_journal_entry(data: dict, connection_id: str) -> dict:
    """Validate journal entry data"""
    try:
        # Get user context
        user_id = voice_ws_manager.connection_users.get(connection_id)
        org_id = voice_ws_manager.connection_orgs.get(connection_id)
        
        # Use your existing journal service for validation
        from app.services.infrastructure.journal_service import JournalService
        journal_service = JournalService()
        
        # Create a journal entry object for validation
        from app.schemas.journal import JournalEntryCreate
        entry_data = JournalEntryCreate(
            content=data.get("content", ""),
            intervention_type=data.get("intervention_type", "unknown"),
            parcel_id=data.get("parcel_id"),
            products_used=data.get("products_used"),
            weather_conditions=data.get("weather_conditions"),
            temperature_celsius=data.get("temperature_celsius"),
            humidity_percent=data.get("humidity_percent"),
            wind_speed_kmh=data.get("wind_speed_kmh"),
            notes=data.get("notes")
        )
        
        # Validate entry
        validation_result = await journal_service.validate_entry(
            db=None,  # You might need to pass a db session here
            entry_data=entry_data,
            user=None  # You might need to pass the user object here
        )
        
        return {
            "is_valid": validation_result.is_valid,
            "status": validation_result.status,
            "notes": validation_result.notes,
            "warnings": validation_result.warnings or [],
            "errors": validation_result.errors or []
        }
        
    except Exception as e:
        logger.error(f"Error validating journal entry: {e}")
        return {
            "is_valid": False,
            "status": "error",
            "notes": f"Erreur de validation: {str(e)}",
            "warnings": [],
            "errors": [str(e)]
        }

def generate_journal_confirmation(data: dict, validation_result: dict) -> str:
    """Generate confirmation text for journal entry"""
    if validation_result.get("is_valid", False):
        return f"Entrée de journal enregistrée avec succès. Intervention: {data.get('intervention_type', 'non spécifiée')} sur la parcelle {data.get('parcelle', 'non spécifiée')}."
    else:
        errors = validation_result.get("errors", [])
        if errors:
            return f"L'entrée de journal contient des erreurs: {', '.join(errors)}. Veuillez corriger et réessayer."
        else:
            return "L'entrée de journal a été enregistrée avec des avertissements. Vérifiez les détails."

async def handle_confirmation_response(websocket: WebSocket, connection_id: str, message_data: dict):
    """Handle farmer's confirmation responses"""
    try:
        # Get the original intervention data from connection context
        # In a real implementation, you'd store this in the connection manager
        intervention_data = message_data.get("intervention_data", {})
        confirmation_responses = message_data.get("responses", {})
        
        # Process confirmation with intervention checker
        result = await intervention_checker.process_farmer_confirmation(
            intervention_data, confirmation_responses
        )
        
        # Send final validation result
        await websocket.send_json({
            "type": "final_validation",
            "result": result
        })
        
        # Save if approved
        if result.get("can_save", False):
            journal_entry = await save_journal_entry(
                result.get("updated_intervention_data", {}), 
                connection_id
            )
            await websocket.send_json({
                "type": "journal_saved",
                "entry_id": journal_entry.get("id"),
                "message": "Journal entry saved successfully after confirmation"
            })
        else:
            await websocket.send_json({
                "type": "intervention_rejected",
                "message": "Intervention not saved due to validation issues"
            })
            
    except Exception as e:
        logger.error(f"Error handling confirmation response: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error processing confirmation: {str(e)}"
        })

async def save_journal_entry(data: dict, connection_id: str) -> dict:
    """Save journal entry to database"""
    try:
        # Get user context
        user_id = voice_ws_manager.connection_users.get(connection_id)
        org_id = voice_ws_manager.connection_orgs.get(connection_id)
        
        # Use your existing journal service to save
        from app.services.infrastructure.journal_service import JournalService
        journal_service = JournalService()
        
        # Create journal entry
        from app.schemas.journal import JournalEntryCreate
        entry_data = JournalEntryCreate(
            content=data.get("content", ""),
            intervention_type=data.get("intervention_type", "unknown"),
            parcel_id=data.get("parcel_id"),
            products_used=data.get("products_used"),
            weather_conditions=data.get("weather_conditions"),
            temperature_celsius=data.get("temperature_celsius"),
            humidity_percent=data.get("humidity_percent"),
            wind_speed_kmh=data.get("wind_speed_kmh"),
            notes=data.get("notes")
        )
        
        # Save entry (you'll need to pass proper db session and user)
        # entry = await journal_service.create_entry(
        #     db=db_session,
        #     user_id=user_id,
        #     entry_data=entry_data
        # )
        
        # For now, return mock data
        return {
            "id": f"journal_{int(asyncio.get_event_loop().time())}",
            "status": "saved"
        }
        
    except Exception as e:
        logger.error(f"Error saving journal entry: {e}")
        raise Exception(f"Failed to save journal entry: {str(e)}")
