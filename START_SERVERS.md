# 🚀 How to Start Ekumen Servers

## ⚠️ IMPORTANT: Always Start Backend First!

The frontend depends on the backend API. **You must start the backend before the frontend.**

---

## 📋 Prerequisites

- Python 3.9+ installed
- Node.js 18+ installed
- PostgreSQL running (optional for basic features)
- Redis running (optional for caching)

---

## 🔧 Backend Setup (Ekumen-assistant)

### **Option 1: Using the startup script (Recommended)**

```bash
cd Ekumen-assistant
./start_backend.sh
```

### **Option 2: Manual start**

```bash
cd Ekumen-assistant

# Activate virtual environment
source venv/bin/activate

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Verify Backend is Running**

Open your browser and go to:
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

You should see:
```json
{
  "status": "healthy",
  "service": "Ekumen Assistant",
  "version": "1.0.0",
  "timestamp": 1234567890.123
}
```

---

## 🎨 Frontend Setup (Ekumen-frontend)

### **Start Frontend** (after backend is running)

```bash
cd Ekumen-frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

### **Verify Frontend is Running**

Open your browser and go to:
- **Frontend**: http://localhost:3000

You should see the Ekumen login page.

---

## 🔐 Default Test Credentials

Use these credentials to log in:

**Email**: `farmer@example.com`  
**Password**: `password123`

---

## 🐛 Troubleshooting

### **Problem: CORS Errors**

**Symptom**: Console shows errors like:
```
Access-Control-Allow-Origin header is missing
```

**Solution**:
1. Make sure backend is running on port 8000
2. Check backend logs for errors
3. Verify CORS settings in `Ekumen-assistant/app/core/config.py`

---

### **Problem: Backend Won't Start**

**Symptom**: Error messages when starting backend

**Solutions**:

#### **1. Missing Dependencies**
```bash
cd Ekumen-assistant
source venv/bin/activate
pip install -r requirements.txt
```

#### **2. Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### **3. Database Connection Error**
```bash
# Check if PostgreSQL is running
pg_isready

# If not running, start it
brew services start postgresql
```

---

### **Problem: Frontend Won't Start**

**Symptom**: Error messages when starting frontend

**Solutions**:

#### **1. Missing Dependencies**
```bash
cd Ekumen-frontend
rm -rf node_modules package-lock.json
npm install
```

#### **2. Port Already in Use**
```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

---

### **Problem: Authentication Fails**

**Symptom**: Can't log in, gets stuck on login page

**Solutions**:

#### **1. Backend Not Running**
- Check if backend is running: http://localhost:8000/health
- If not, start backend first

#### **2. Database Not Initialized**
```bash
cd Ekumen-assistant
source venv/bin/activate
python -c "from app.core.database import init_db; init_db()"
```

#### **3. Clear Browser Cache**
- Open DevTools (F12)
- Go to Application tab
- Clear all storage
- Refresh page

---

## 📊 Checking Server Status

### **Backend Status**

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

### **Frontend Status**

```bash
# Check if frontend is running
curl http://localhost:3000

# Open in browser
open http://localhost:3000
```

---

## 🔄 Restarting Servers

### **Restart Backend**

```bash
# Find backend process
ps aux | grep uvicorn

# Kill it
kill -9 <PID>

# Start again
cd Ekumen-assistant
./start_backend.sh
```

### **Restart Frontend**

```bash
# Stop with Ctrl+C in terminal
# Or find and kill process
ps aux | grep "vite"
kill -9 <PID>

# Start again
cd Ekumen-frontend
npm run dev
```

---

## 📝 Development Workflow

### **Typical Startup Sequence**

1. **Start Backend** (Terminal 1)
   ```bash
   cd Ekumen-assistant
   ./start_backend.sh
   ```

2. **Wait for Backend** (5-10 seconds)
   - Check http://localhost:8000/health

3. **Start Frontend** (Terminal 2)
   ```bash
   cd Ekumen-frontend
   npm run dev
   ```

4. **Open Browser**
   - Go to http://localhost:3000
   - Log in with test credentials

---

## 🎯 Quick Start (All-in-One)

Create a file `start_all.sh` in the root directory:

```bash
#!/bin/bash

echo "🚀 Starting Ekumen Servers..."

# Start backend in background
cd Ekumen-assistant
./start_backend.sh &
BACKEND_PID=$!

echo "⏳ Waiting for backend to start..."
sleep 10

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running!"
    
    # Start frontend
    cd ../Ekumen-frontend
    npm run dev
else
    echo "❌ Backend failed to start!"
    kill $BACKEND_PID
    exit 1
fi
```

Then run:
```bash
chmod +x start_all.sh
./start_all.sh
```

---

## 🛑 Stopping Servers

### **Stop Backend**
- Press `Ctrl+C` in the terminal running the backend

### **Stop Frontend**
- Press `Ctrl+C` in the terminal running the frontend

### **Stop All**
```bash
# Kill all uvicorn processes (backend)
pkill -f uvicorn

# Kill all vite processes (frontend)
pkill -f vite
```

---

## 📦 Environment Variables

### **Backend (.env)**

Create `Ekumen-assistant/.env`:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ekumen_db

# Security
SECRET_KEY=your-secret-key-here

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Weather API
WEATHER_API_KEY=your-weather-api-key
```

### **Frontend (.env)**

Create `Ekumen-frontend/.env`:
```bash
VITE_API_URL=http://localhost:8000
```

---

## ✅ Verification Checklist

Before starting development, verify:

- [ ] Backend starts without errors
- [ ] Backend health check returns 200
- [ ] Frontend starts without errors
- [ ] Frontend loads in browser
- [ ] Can log in with test credentials
- [ ] No CORS errors in console
- [ ] API calls work (check Network tab)

---

## 🆘 Still Having Issues?

1. **Check logs**: Look at terminal output for error messages
2. **Check browser console**: Press F12 and look for errors
3. **Verify ports**: Make sure 3000 and 8000 are not in use
4. **Restart everything**: Kill all processes and start fresh
5. **Check dependencies**: Run `pip install -r requirements.txt` and `npm install`

---

## 📚 Additional Resources

- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health
- **Frontend**: http://localhost:3000

---

**🎉 Happy Coding!**

