# Ekumen - Agricultural AI Platform

A comprehensive agricultural AI platform with voice journaling, chat assistance, and farm management capabilities.

## 🏗️ Project Structure

```
Ekumen/
├── Ekumen-assistant/          # Backend API and AI services
├── Ekumen-frontend/           # React frontend application
├── Ekumen-design-system/      # Shared design system components
├── Ekumenbackend/            # Legacy backend (being phased out)
├── docs/                     # Project documentation
│   ├── implementation/       # Implementation guides and summaries
│   ├── testing/             # Testing documentation
│   ├── deployment/          # Deployment guides
│   └── architecture/        # Architecture documentation
├── tests/                   # Integration and E2E tests
├── scripts/                 # Development and deployment scripts
└── config/                  # Configuration files
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker (optional)

### Development Setup

1. **Start Backend**
   ```bash
   cd Ekumen-assistant
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start Frontend**
   ```bash
   cd Ekumen-frontend
   npm install
   npm run dev
   ```

3. **Access Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📚 Documentation

- [Implementation Guides](docs/implementation/)
- [Architecture Documentation](docs/architecture/)
- [Testing Documentation](docs/testing/)
- [Deployment Guides](docs/deployment/)

## 🎯 Key Features

- **Voice Journal Interface**: Record farm interventions with AI-powered validation
- **Chat Assistant**: Agricultural AI assistant with RAG capabilities
- **Farm Management**: Parcel tracking, treatment planning, compliance monitoring
- **Real-time Monitoring**: System health and performance tracking

## 🛠️ Development

See [LOCAL_DEVELOPMENT_GUIDE.md](docs/LOCAL_DEVELOPMENT_GUIDE.md) for detailed development setup.

## 📄 License

Private - Ekumen Agricultural Solutions
