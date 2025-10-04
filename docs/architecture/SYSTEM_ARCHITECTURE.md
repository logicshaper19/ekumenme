# Ekumen System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (React)       │    │   (FastAPI)     │    │   Services      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ VoiceJournal    │◄──►│ JournalService  │◄──►│ OpenAI Whisper  │
│ JournalVoice    │    │ JournalAgent    │    │ OpenAI TTS      │
│ VoiceInterface  │    │ LCELChatService │    │ EPHY Database   │
│ ChatInterface   │    │ VoiceService    │    │ Weather API     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Core Services

### **Voice Journal System**
- **Purpose**: Record farm interventions with AI validation
- **Flow**: Voice → Whisper → JournalAgent → Validation → Database
- **Components**:
  - `JournalVoiceInterface.tsx` (Frontend)
  - `JournalService` (Backend orchestration)
  - `JournalAgent` (LangChain agent with atomic tools)

### **Chat Assistant**
- **Purpose**: Conversational AI with agricultural expertise
- **Flow**: Voice → Whisper → LCELChatService → RAG → TTS → Voice
- **Components**:
  - `VoiceInterface.tsx` (Frontend)
  - `LCELChatService` (Backend with query reformulation)
  - RAG with knowledge base retrieval

### **Monitoring System**
- **Purpose**: System health and performance tracking
- **Components**:
  - `VoiceMonitoringService` (Metrics collection)
  - Prometheus export format
  - Real-time health checks

## 🔧 Technical Stack

### **Backend**
- **Framework**: FastAPI with WebSocket support
- **AI**: LangChain with OpenAI integration
- **Database**: PostgreSQL with SQLAlchemy
- **Vector Store**: ChromaDB for RAG
- **Monitoring**: Custom metrics with Prometheus format

### **Frontend**
- **Framework**: React with TypeScript
- **UI**: Tailwind CSS with custom design system
- **Communication**: WebSocket for real-time features
- **State**: React hooks and context

### **AI Integration**
- **Transcription**: OpenAI Whisper
- **Text-to-Speech**: OpenAI TTS
- **Language Model**: GPT-4 for chat and reasoning
- **Tools**: Atomic tools for EPHY, weather, database operations

## 📊 Data Flow

### **Voice Journal Processing**
1. User records voice → Frontend sends audio chunks
2. Backend transcribes with Whisper
3. JournalAgent processes with atomic tools
4. Immediate save + async validation queue
5. Real-time feedback to user

### **Chat Processing**
1. User voice/text input → Frontend
2. Query reformulation (context-aware)
3. RAG retrieval from knowledge base
4. LLM response generation
5. TTS synthesis and streaming

## 🔒 Security & Performance

### **Authentication**
- JWT-based authentication
- Role-based access control (user, org admin, super admin)
- WebSocket connection authentication

### **Performance**
- Async processing for non-blocking operations
- Rolling averages for metrics
- Memory management with cleanup workers
- Streaming responses for real-time UX

## 🚀 Deployment

### **Development**
- Local development with hot reload
- Docker Compose for services
- Environment-based configuration

### **Production**
- Docker containers
- PostgreSQL database
- ChromaDB vector store
- Monitoring and health checks
