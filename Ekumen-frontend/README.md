# Ekumen Frontend - React Application

Modern React frontend for the Ekumen agricultural AI platform with voice interfaces and farm management.

## 🏗️ Architecture

```
src/
├── components/              # Reusable UI components
│   ├── JournalVoiceInterface.tsx  # Voice journal recording
│   ├── VoiceInterface.tsx         # Chat voice interface
│   └── Analytics/                 # Dashboard components
├── pages/                   # Main application pages
│   ├── VoiceJournal.tsx     # Journal management
│   ├── ChatInterface.tsx    # Chat assistant
│   └── Parcelles.tsx        # Farm management
├── services/                # API and WebSocket services
│   └── websocket.ts         # WebSocket communication
└── hooks/                   # Custom React hooks
```

## 🎯 Key Features

- **Voice Journal Interface**: Record farm interventions with real-time validation
- **Chat Assistant**: Conversational AI with voice input/output
- **Farm Management**: Parcel tracking and treatment planning
- **Analytics Dashboard**: Performance metrics and insights

## 🚀 Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

## 🎨 UI Components

- **JournalVoiceInterface**: Voice recording for farm interventions
- **VoiceInterface**: Voice input for chat assistant
- **Analytics Components**: Performance dashboards and charts

## 🔗 API Integration

- WebSocket connections for real-time voice processing
- REST API for farm data and user management
- Real-time monitoring and health checks

## 📚 Documentation

- [Theme System](docs/THEME_SYSTEM_DOCS.md)
- [Navigation Structure](docs/NAVIGATION_REORGANIZATION.md)
