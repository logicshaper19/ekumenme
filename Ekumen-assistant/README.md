# Ekumen Assistant - Backend API

FastAPI-based backend providing agricultural AI services, voice processing, and farm management APIs.

## 🏗️ Architecture

```
app/
├── api/v1/                  # API endpoints
│   ├── auth/               # Authentication
│   ├── chat/               # Chat and conversation APIs
│   ├── journal/            # Voice journal processing
│   ├── voice/              # Voice WebSocket endpoints
│   ├── monitoring/         # System monitoring
│   └── products/           # Product and EPHY data
├── agents/                 # AI agents
│   └── journal_agent.py    # Journal processing agent
├── services/               # Business logic services
│   ├── infrastructure/     # Core services (voice, chat, etc.)
│   ├── monitoring/         # Monitoring and observability
│   └── shared/             # Shared services
├── tools/                  # LangChain tools
│   └── atomic_tools.py     # Atomic EPHY, weather, DB tools
├── models/                 # Database models
└── core/                   # Core configuration and utilities
```

## 🚀 Key Services

- **JournalService**: Voice journal processing with async validation
- **LCELChatService**: Modern LangChain chat with query reformulation
- **VoiceService**: OpenAI Whisper transcription and TTS
- **MonitoringService**: System health and performance tracking

## 🎯 API Endpoints

- `POST /api/v1/auth/login` - User authentication
- `WS /api/v1/chat/ws/{conversation_id}` - Chat WebSocket
- `WS /api/v1/voice/ws` - Voice journal WebSocket
- `GET /api/v1/monitoring/health` - System health check

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/
```

## 📚 Documentation

- [Implementation Guides](../docs/implementation/)
- [Architecture Documentation](../docs/architecture/)
- [API Reference](http://localhost:8000/docs)
