#!/bin/bash

# Start minimal services for EPHY import testing
echo "🚀 Starting minimal services for EPHY import..."

# Start only PostgreSQL and Redis
docker-compose up -d postgres redis

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "📊 Checking service status..."
docker-compose ps postgres redis

echo "✅ Minimal services started!"
echo "📋 Next steps:"
echo "   1. Start the API: docker-compose up -d api"
echo "   2. Test import: python scripts/api_ephy_test.py"
