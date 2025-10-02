#!/bin/bash
# Supabase Setup Script for Ekumen
# This script helps you set up Supabase and migrate your data

set -e  # Exit on error

echo "🚀 Ekumen Supabase Setup"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file first."
    exit 1
fi

# Function to update .env file
update_env() {
    local key=$1
    local value=$2
    local file=".env"
    
    if grep -q "^${key}=" "$file"; then
        # Key exists, update it
        sed -i.bak "s|^${key}=.*|${key}=${value}|" "$file"
    else
        # Key doesn't exist, append it
        echo "${key}=${value}" >> "$file"
    fi
}

echo "📝 Step 1: Supabase Project Setup"
echo "========================================"
echo ""
echo "Please create a Supabase project at: https://supabase.com"
echo ""
echo "After creating your project, you'll need:"
echo "  1. Database connection string"
echo "  2. Project URL"
echo "  3. API keys (anon and service_role)"
echo ""
read -p "Have you created a Supabase project? (y/n): " created

if [ "$created" != "y" ]; then
    echo ""
    echo "Please create a Supabase project first, then run this script again."
    echo "Visit: https://supabase.com"
    exit 0
fi

echo ""
echo "📝 Step 2: Enter Supabase Credentials"
echo "========================================"
echo ""

# Get Supabase URL
read -p "Enter your Supabase Project URL (e.g., https://xxxxx.supabase.co): " supabase_url

# Get database password
read -sp "Enter your Supabase database password: " db_password
echo ""

# Get project reference (extract from URL)
project_ref=$(echo "$supabase_url" | sed -E 's|https://([^.]+)\.supabase\.co|\1|')

# Construct database URLs
db_url_async="postgresql+asyncpg://postgres:${db_password}@db.${project_ref}.supabase.co:5432/postgres"
db_url_sync="postgresql://postgres:${db_password}@db.${project_ref}.supabase.co:5432/postgres"

# Get API keys
echo ""
read -p "Enter your Supabase anon (public) key: " anon_key
read -p "Enter your Supabase service_role key: " service_key

echo ""
echo "📝 Step 3: Updating .env file"
echo "========================================"
echo ""

# Update .env file
update_env "DATABASE_URL" "$db_url_async"
update_env "DATABASE_URL_SYNC" "$db_url_sync"
update_env "SUPABASE_URL" "$supabase_url"
update_env "SUPABASE_ANON_KEY" "$anon_key"
update_env "SUPABASE_SERVICE_KEY" "$service_key"

echo "✅ .env file updated with Supabase credentials"

echo ""
echo "📝 Step 4: Enable PostGIS Extension"
echo "========================================"
echo ""
echo "Please run this SQL in your Supabase SQL Editor:"
echo ""
echo "CREATE EXTENSION IF NOT EXISTS postgis;"
echo ""
read -p "Have you enabled PostGIS? (y/n): " postgis_enabled

if [ "$postgis_enabled" != "y" ]; then
    echo ""
    echo "⚠️  Warning: PostGIS is required for geometry support (parcelle boundaries)"
    echo "Please enable it in Supabase Dashboard > SQL Editor"
fi

echo ""
echo "📝 Step 5: Create Database Tables"
echo "========================================"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo "Creating database tables..."
python -c "
from app.core.database import Base, sync_engine
from app.models import *

print('Creating all tables in Supabase...')
Base.metadata.create_all(bind=sync_engine)
print('✅ Tables created successfully!')
"

if [ $? -eq 0 ]; then
    echo "✅ Database tables created successfully"
else
    echo "❌ Failed to create tables"
    exit 1
fi

echo ""
echo "📝 Step 6: Import Sample Data (Optional)"
echo "========================================"
echo ""
read -p "Do you want to import sample farm data? (y/n): " import_data

if [ "$import_data" = "y" ]; then
    echo "Importing sample data..."
    python scripts/migration/add_simple_farm_data.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Sample data imported successfully"
    else
        echo "❌ Failed to import sample data"
    fi
fi

echo ""
echo "📝 Step 7: Test Connection"
echo "========================================"
echo ""

python -c "
from app.core.database import SessionLocal
from app.models import Exploitation

db = SessionLocal()
try:
    count = db.query(Exploitation).count()
    print(f'✅ Connected to Supabase! Found {count} exploitations.')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
finally:
    db.close()
"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "🎉 Supabase setup complete!"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "  1. Start your application: uvicorn app.main:app --reload"
    echo "  2. Visit Supabase Dashboard to view your data"
    echo "  3. Check out docs/SUPABASE_SETUP.md for more info"
    echo ""
else
    echo ""
    echo "❌ Setup failed. Please check your credentials and try again."
    exit 1
fi

