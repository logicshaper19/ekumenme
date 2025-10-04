#!/bin/bash

# Ekumen Health Check and Fix Script
echo "🔍 Ekumen Health Check..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "1️⃣  Checking Backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is NOT running${NC}"
    echo -e "${YELLOW}   Fix: cd Ekumen-assistant && ./start_backend.sh${NC}"
fi

echo ""

# Check if frontend is running
echo "2️⃣  Checking Frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${RED}❌ Frontend is NOT running${NC}"
    echo -e "${YELLOW}   Fix: cd Ekumen-frontend && npm run dev${NC}"
fi

echo ""

# Check for port conflicts
echo "3️⃣  Checking Port Conflicts..."

# Check port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo -e "${GREEN}✅ Port 8000 is in use (PID: $PID)${NC}"
else
    echo -e "${YELLOW}⚠️  Port 8000 is free (backend not running)${NC}"
fi

# Check port 3000
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PID=$(lsof -Pi :3000 -sTCP:LISTEN -t)
    echo -e "${GREEN}✅ Port 3000 is in use (PID: $PID)${NC}"
else
    echo -e "${YELLOW}⚠️  Port 3000 is free (frontend not running)${NC}"
fi

echo ""

# Check Python virtual environment
echo "4️⃣  Checking Python Environment..."
if [ -d "Ekumen-assistant/venv" ]; then
    echo -e "${GREEN}✅ Python venv exists${NC}"
else
    echo -e "${RED}❌ Python venv NOT found${NC}"
    echo -e "${YELLOW}   Fix: cd Ekumen-assistant && python -m venv venv${NC}"
fi

echo ""

# Check Node modules
echo "5️⃣  Checking Node Modules..."
if [ -d "Ekumen-frontend/node_modules" ]; then
    echo -e "${GREEN}✅ Node modules installed${NC}"
else
    echo -e "${RED}❌ Node modules NOT found${NC}"
    echo -e "${YELLOW}   Fix: cd Ekumen-frontend && npm install${NC}"
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if both servers are running
BACKEND_RUNNING=$(curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "yes" || echo "no")
FRONTEND_RUNNING=$(curl -s http://localhost:3000 > /dev/null 2>&1 && echo "yes" || echo "no")

if [ "$BACKEND_RUNNING" = "yes" ] && [ "$FRONTEND_RUNNING" = "yes" ]; then
    echo -e "${GREEN}🎉 All systems operational!${NC}"
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend:  http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
elif [ "$BACKEND_RUNNING" = "no" ] && [ "$FRONTEND_RUNNING" = "no" ]; then
    echo -e "${RED}❌ Both servers are down${NC}"
    echo ""
    echo "To start both servers:"
    echo "  1. Terminal 1: cd Ekumen-assistant && ./start_backend.sh"
    echo "  2. Terminal 2: cd Ekumen-frontend && npm run dev"
elif [ "$BACKEND_RUNNING" = "no" ]; then
    echo -e "${YELLOW}⚠️  Backend is down (Frontend is running)${NC}"
    echo ""
    echo "To start backend:"
    echo "  cd Ekumen-assistant && ./start_backend.sh"
else
    echo -e "${YELLOW}⚠️  Frontend is down (Backend is running)${NC}"
    echo ""
    echo "To start frontend:"
    echo "  cd Ekumen-frontend && npm run dev"
fi

echo ""

