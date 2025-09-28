#!/bin/bash

# Ekumen Local Development Startup Script
# This script starts all services for local development

echo "🚀 Starting Ekumen Local Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service=$1
    local port=$2
    local command=$3
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service is already running on port $port${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $service is not running on port $port${NC}"
        return 1
    fi
}

# Function to start a service
start_service() {
    local service=$1
    local port=$2
    local command=$3
    local dir=$4
    
    echo -e "${BLUE}🔄 Starting $service...${NC}"
    cd "$dir"
    eval "$command" &
    local pid=$!
    echo -e "${GREEN}✅ $service started with PID $pid${NC}"
    echo $pid
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check PostgreSQL
if check_service "PostgreSQL" "5432" "psql"; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not running. Please start it with: brew services start postgresql@15${NC}"
    exit 1
fi

# Check Redis
if check_service "Redis" "6379" "redis-cli"; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running. Please start it with: brew services start redis${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f "Ekumen-assistant/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp Ekumen-assistant/env.local Ekumen-assistant/.env
    echo -e "${YELLOW}📝 Please edit Ekumen-assistant/.env and add your API keys${NC}"
fi

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"

# Start Backend
echo -e "${BLUE}🔄 Starting Backend (FastAPI)...${NC}"
cd Ekumen-assistant
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start Frontend
echo -e "${BLUE}🔄 Starting Frontend (React)...${NC}"
cd Ekumen-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Display status
echo -e "${GREEN}🎉 Development environment started!${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo -e "  Backend (FastAPI):  http://localhost:8000 (PID: $BACKEND_PID)"
echo -e "  Frontend (React):   http://localhost:3000 (PID: $FRONTEND_PID)"
echo -e "  API Documentation:  http://localhost:8000/docs"
echo -e "  Database:           PostgreSQL on localhost:5432"
echo -e "  Cache:              Redis on localhost:6379"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "  - Press Ctrl+C to stop all services"
echo -e "  - Backend logs: Check terminal output"
echo -e "  - Frontend logs: Check browser console"
echo -e "  - Database: Use psql -d ekumen_assistant"
echo ""
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "  - Test backend: curl http://localhost:8000/health"
echo -e "  - View logs: tail -f logs/app.log"
echo -e "  - Database shell: psql -d ekumen_assistant"
echo ""

# Wait for user to stop
echo -e "${YELLOW}Press Ctrl+C to stop all services...${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}🛑 Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes
wait
