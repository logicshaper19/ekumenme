# Voice Assistant Implementation

## Overview

This document describes the implementation of the streaming voice assistant for the Ekumen agricultural chatbot. The system provides real-time voice interaction with fast, natural conversation flow using OpenAI Whisper for transcription and OpenAI TTS for speech synthesis.

## Architecture

```
Frontend (React) → WebSocket → Backend (FastAPI) → OpenAI APIs
     ↓                ↓              ↓
Audio Stream → Audio Chunks → Whisper (transcription)
     ↓                ↓              ↓
Text Display ← Text Chunks ← Chat Assistant (streaming)
     ↓                ↓              ↓
Audio Playback ← Audio Chunks ← TTS (streaming)
```

## Key Features

### 🎤 Real-time Voice Streaming
- **Fast Response**: ~2.3 seconds from stop speaking to hearing response
- **Sentence-level Streaming**: Audio generation starts while AI is still thinking
- **Natural Conversation**: Continuous back-and-forth dialogue

### 🧠 Intelligent Processing
- **Whisper Integration**: High-quality French transcription
- **Agricultural Context**: Specialized prompts for farm activities
- **Structured Data Extraction**: Automatic parsing of intervention details

### 📝 Voice Journal Integration
- **Smart Data Extraction**: Automatically extracts parcelle, intervention type, products, weather
- **Compliance Validation**: Checks against EPHY database and regulations
- **Auto-creation**: Creates structured journal entries and interventions

## Implementation Details

### Backend Components

#### 1. WebSocket Endpoints (`/app/api/v1/voice/websocket.py`)

**Main Voice Assistant**: `/api/v1/voice/ws/voice`
- Real-time voice streaming
- Chat assistant integration
- Sentence-level audio generation

**Voice Journal**: `/api/v1/voice/ws/voice/journal`
- Specialized for farm activity recording
- Structured data extraction
- Compliance validation

#### 2. Voice Service (`/app/services/infrastructure/voice_service.py`)

```python
class VoiceService:
    async def transcribe_audio_bytes(self, audio_bytes: bytes) -> VoiceTranscriptionResult
    async def synthesize_speech(self, text: str) -> bytes
    async def synthesize_speech_streaming(self, text: str) -> AsyncGenerator[bytes, None]
```

**Key Features**:
- OpenAI Whisper integration for transcription
- OpenAI TTS for speech synthesis
- Streaming audio generation
- French language optimization

#### 3. WebSocket Manager

```python
class VoiceWebSocketManager:
    async def connect(self, websocket, connection_id, user_id, org_id)
    async def send_message(self, connection_id, message)
    async def handle_audio_data(self, websocket, connection_id, audio_bytes)
```

### Frontend Components

#### 1. Streaming Voice Assistant (`/src/components/StreamingVoiceAssistant.tsx`)

**Features**:
- Real-time WebSocket connection
- Audio level visualization
- Streaming audio playback
- Connection status management
- Dual mode support (chat/journal)

**Props**:
```typescript
interface StreamingVoiceAssistantProps {
  onTranscript?: (text: string) => void
  onVoiceMessage?: (message: string) => void
  onJournalEntry?: (entry: any) => void
  mode?: 'chat' | 'journal'
  className?: string
}
```

#### 2. Enhanced Voice Journal (`/src/pages/VoiceJournal.tsx`)

**New Features**:
- Dual voice recording options
- Streaming voice assistant integration
- Structured data display
- Real-time validation feedback

## Usage Examples

### Basic Voice Chat

```typescript
<StreamingVoiceAssistant
  onVoiceMessage={(message) => console.log('AI Response:', message)}
  mode="chat"
/>
```

### Voice Journal Entry

```typescript
<StreamingVoiceAssistant
  onJournalEntry={(entry) => {
    console.log('Structured data:', entry.data)
    console.log('Validation:', entry.validation)
  }}
  mode="journal"
/>
```

### Voice Input Example

**User says**: "J'ai appliqué du fongicide sur la parcelle Nord de 12 hectares ce matin. Conditions ensoleillées, 18 degrés, vent faible. Utilisé 2 litres par hectare."

**AI extracts**:
```json
{
  "intervention_type": "traitement_fongicide",
  "parcelle": "Parcelle Nord",
  "surface_hectares": 12,
  "products_used": [{"name": "fongicide", "quantity": 2, "unit": "litres/hectare"}],
  "weather_conditions": "ensoleillé",
  "temperature_celsius": 18,
  "wind_speed_kmh": "faible"
}
```

## Performance Optimization

### Timing Breakdown
1. **User stops speaking**: 0ms
2. **Transcription completes**: ~1000ms (1s)
3. **First AI text chunk**: ~1200ms (0.2s after transcription)
4. **First sentence complete**: ~1800ms (0.6s after first chunk)
5. **First audio starts playing**: ~2300ms (0.5s TTS generation)
6. **Total response time**: ~2.3 seconds

### Optimization Strategies
- **Sentence-level streaming**: Generate audio for complete sentences immediately
- **Parallel processing**: TTS generation starts while AI is still thinking
- **Chunked audio**: Small audio chunks for immediate playback
- **Connection pooling**: Reuse WebSocket connections

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_ORGANIZATION=your_org_id

# Voice Processing
WHISPER_MODEL=whisper-1
MAX_AUDIO_DURATION=300  # 5 minutes max
```

### Frontend Configuration

```typescript
// WebSocket connection
const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/voice/ws/voice?token=${token}`

// Audio settings
const audioConstraints = {
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
  channelCount: 1,
  sampleRate: 16000
}
```

## Testing

### Run Tests

```bash
# Test voice assistant functionality
python test_voice_assistant.py

# Test WebSocket connections
# Start the backend server first
uvicorn app.main:app --reload

# Then run the test script
python test_voice_assistant.py
```

### Manual Testing

1. **Start the backend server**:
   ```bash
   cd Ekumen-assistant
   uvicorn app.main:app --reload
   ```

2. **Start the frontend**:
   ```bash
   cd Ekumen-frontend
   npm run dev
   ```

3. **Test voice functionality**:
   - Navigate to the Voice Journal page
   - Click "Assistant Vocal IA"
   - Record a voice message
   - Verify transcription and response

## Error Handling

### Backend Error Handling
- WebSocket connection failures
- Audio processing errors
- OpenAI API rate limits
- Authentication failures

### Frontend Error Handling
- Microphone permission denied
- WebSocket connection lost
- Audio playback errors
- Network timeouts

## Security Considerations

### Authentication
- JWT token validation for WebSocket connections
- User and organization context validation
- Rate limiting for voice requests

### Data Privacy
- Audio data not stored permanently
- Transcriptions processed in memory
- Secure WebSocket connections (WSS in production)

## Future Enhancements

### Planned Features
1. **Multi-language Support**: Support for multiple languages
2. **Custom Voices**: Farm-specific voice training
3. **Offline Mode**: Local processing for critical operations
4. **Voice Commands**: Direct farm system control
5. **Integration**: Weather data, equipment status, market prices

### Performance Improvements
1. **Edge Processing**: Reduce latency with edge computing
2. **Audio Compression**: Optimize bandwidth usage
3. **Caching**: Cache common responses
4. **Load Balancing**: Distribute voice processing load

## Troubleshooting

### Common Issues

**WebSocket Connection Failed**:
- Check authentication token
- Verify backend server is running
- Check network connectivity

**Audio Not Playing**:
- Check browser audio permissions
- Verify audio codec support
- Check WebSocket message format

**Transcription Errors**:
- Verify OpenAI API key
- Check audio quality
- Ensure French language setting

**Performance Issues**:
- Check network latency
- Monitor OpenAI API usage
- Verify server resources

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Development Setup
1. Install dependencies
2. Set up environment variables
3. Run tests
4. Start development servers

### Code Style
- Follow existing code patterns
- Add type hints for Python
- Use TypeScript for frontend
- Document new features

## License

This implementation is part of the Ekumen agricultural assistant project.
