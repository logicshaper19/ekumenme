#!/bin/bash

# Start Ekumen Assistant Backend Server
echo "🚀 Starting Ekumen Assistant Backend..."

# Activate virtual environment
source venv/bin/activate

# Start uvicorn server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

