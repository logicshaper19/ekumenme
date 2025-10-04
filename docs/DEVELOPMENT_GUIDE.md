# Ekumen Development Guide

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL (or Docker)

### Setup
```bash
# Clone and setup
git clone <repository>
cd Ekumen

# Backend setup
cd Ekumen-assistant
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend setup (new terminal)
cd Ekumen-frontend
npm install
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🏗️ Development Workflow

### **Voice Journal Development**
1. **Frontend**: Modify `JournalVoiceInterface.tsx`
2. **Backend**: Update `JournalService` or `JournalAgent`
3. **Testing**: Use WebSocket connection to test voice flow

### **Chat Assistant Development**
1. **Frontend**: Modify `VoiceInterface.tsx` or `ChatInterface.tsx`
2. **Backend**: Update `LCELChatService` or prompts
3. **Testing**: Test chat flow with voice and text input

### **Monitoring Development**
1. **Backend**: Update `VoiceMonitoringService`
2. **Endpoints**: Modify `/api/v1/monitoring/*`
3. **Testing**: Check metrics at `/api/v1/monitoring/health`

## 🧪 Testing

### **Voice Journal Testing**
```bash
# Test voice WebSocket
cd Ekumen-assistant
python -c "
import asyncio
import websockets
async def test():
    async with websockets.connect('ws://localhost:8000/api/v1/voice/ws') as ws:
        await ws.send('test message')
        response = await ws.recv()
        print(response)
asyncio.run(test())
"
```

### **Chat Testing**
```bash
# Test chat WebSocket
curl -X GET "http://localhost:8000/api/v1/chat/ws/test_conversation?token=test_token"
```

### **Monitoring Testing**
```bash
# Test health endpoint
curl http://localhost:8000/api/v1/monitoring/health
```

## 🔧 Key Components

### **Frontend Components**
- `JournalVoiceInterface.tsx` - Voice recording for farm interventions
- `VoiceInterface.tsx` - Voice input for chat
- `VoiceJournal.tsx` - Journal management interface
- `ChatInterface.tsx` - Chat assistant interface

### **Backend Services**
- `JournalService` - Voice journal processing pipeline
- `LCELChatService` - Chat with automatic history
- `VoiceService` - OpenAI Whisper + TTS
- `VoiceMonitoringService` - System monitoring

### **AI Agents**
- `JournalAgent` - LangChain agent for journal processing
- Atomic tools in `atomic_tools.py` - EPHY, weather, database operations

## 📊 Monitoring & Debugging

### **System Health**
- Health check: `/api/v1/monitoring/health`
- Metrics: `/api/v1/monitoring/metrics`
- User metrics: `/api/v1/monitoring/analytics/users/{user_id}`

### **Logs**
- Backend logs: Check console output
- Frontend logs: Browser developer tools
- WebSocket logs: Network tab in browser

### **Common Issues**
1. **Voice not working**: Check microphone permissions
2. **WebSocket connection failed**: Verify backend is running
3. **AI responses slow**: Check OpenAI API key and rate limits

## 🚀 Deployment

### **Development**
```bash
# Start all services
./scripts/start-dev.sh
```

### **Production**
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Additional Resources

- [System Architecture](architecture/SYSTEM_ARCHITECTURE.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [API Reference](http://localhost:8000/docs)
