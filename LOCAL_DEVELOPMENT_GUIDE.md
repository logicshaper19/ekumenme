# 🚀 Ekumen Local Development Setup Guide

This guide will help you set up the Ekumen agricultural assistant system for local development without Docker.

## ✅ Prerequisites

- **Python 3.9+** ✅ (You have Python 3.9.6)
- **Node.js 16+** ✅ (You have Node.js 24.4.1)
- **PostgreSQL 14+** ✅ (You have PostgreSQL 15.14)
- **Redis** ✅ (You have Redis running)

## 🏗️ Project Structure

```
ekumenme/
├── Ekumen-assistant/     # Main FastAPI backend
├── Ekumen-frontend/      # React frontend
├── Ekumenbackend/        # Secondary backend (optional)
├── Ekumen-design-system/ # Design system components
├── start-dev.sh          # Development startup script
├── test-backend.py       # Backend testing script
└── LOCAL_DEVELOPMENT_GUIDE.md
```

## 🚀 Quick Start

### 1. Start All Services
```bash
cd /Users/elisha/ekumenme
./start-dev.sh
```

This script will:
- ✅ Check if PostgreSQL and Redis are running
- ✅ Start the FastAPI backend on port 8000
- ✅ Start the React frontend on port 3000
- ✅ Display service status and useful URLs

### 2. Manual Service Management

#### Start Backend Only
```bash
cd Ekumen-assistant
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Start Frontend Only
```bash
cd Ekumen-frontend
npm run dev
```

## 🔧 Configuration

### Environment Variables

The backend uses environment variables from `Ekumen-assistant/.env`:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=sYu6PmXHOZxJW3PlvoJDnHhkwe2RqXzC7lm9HGEVOm0

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ekumen_assistant
REDIS_URL=redis://localhost:6379

# Optional API Keys
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
WEATHER_API_KEY=your_weather_api_key_here
```

### Database Setup

The database `ekumen_assistant` is already created. To reset it:

```bash
# Drop and recreate database
/usr/local/Cellar/postgresql@15/15.14/bin/dropdb ekumen_assistant
/usr/local/Cellar/postgresql@15/15.14/bin/createdb ekumen_assistant
```

## 🧪 Testing

### Test Backend
```bash
python test-backend.py
```

### Test Database Connection
```bash
/usr/local/Cellar/postgresql@15/15.14/bin/psql -d ekumen_assistant -c "SELECT version();"
```

### Test Redis Connection
```bash
redis-cli ping
```

## 📊 Service URLs

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Database**: localhost:5432
- **Redis**: localhost:6379

## 🛠️ Development Workflow

### 1. Daily Development
```bash
# Start all services
./start-dev.sh

# In another terminal, make changes to code
# Backend will auto-reload on changes
# Frontend will auto-reload on changes
```

### 2. Backend Development
```bash
cd Ekumen-assistant
source venv/bin/activate

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy .
```

### 3. Frontend Development
```bash
cd Ekumen-frontend

# Run tests
npm test

# Lint code
npm run lint

# Build for production
npm run build
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill process if needed
kill -9 <PID>
```

#### 2. Database Connection Issues
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL if not running
brew services start postgresql@15

# Test connection
/usr/local/Cellar/postgresql@15/15.14/bin/psql -d ekumen_assistant
```

#### 3. Redis Connection Issues
```bash
# Check if Redis is running
brew services list | grep redis

# Start Redis if not running
brew services start redis

# Test connection
redis-cli ping
```

#### 4. Python Dependencies Issues
```bash
cd Ekumen-assistant
source venv/bin/activate
pip install -r requirements-dev.txt
```

#### 5. Node.js Dependencies Issues
```bash
cd Ekumen-frontend
rm -rf node_modules package-lock.json
npm install
```

### Logs and Debugging

#### Backend Logs
- Backend logs appear in the terminal where you started it
- Look for error messages in the console output

#### Frontend Logs
- Open browser developer tools (F12)
- Check Console tab for errors
- Check Network tab for API call issues

#### Database Logs
```bash
# PostgreSQL logs
tail -f /usr/local/var/log/postgresql@15.log

# Redis logs
tail -f /usr/local/var/log/redis.log
```

## 🎯 Next Steps

1. **Add Your API Keys**: Edit `Ekumen-assistant/.env` and add your actual API keys
2. **Test the System**: Run `python test-backend.py` to verify everything works
3. **Explore the API**: Visit http://localhost:8000/docs to see available endpoints
4. **Start Developing**: Make changes to the code and see them reflected immediately

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Redis Documentation**: https://redis.io/documentation

## 🆘 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Look at the logs for error messages
3. Verify all services are running
4. Check that your API keys are correctly set
5. Ensure all dependencies are installed

---

**Happy coding! 🎉**
