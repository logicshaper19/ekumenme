#!/usr/bin/env python3
"""
Test Supabase connection and setup
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, sync_engine
from app.models import Exploitation, Parcelle, Intervention
from sqlalchemy import text, select
import os


def test_connection():
    """Test basic database connection."""
    print("🔌 Testing Supabase connection...")
    
    try:
        db = SessionLocal()
        
        # Test basic query
        result = db.execute(text("SELECT version();"))
        version = result.scalar()
        print(f"✅ Connected to PostgreSQL!")
        print(f"   Version: {version[:50]}...")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def check_postgis():
    """Check if PostGIS is enabled."""
    print("\n📍 Checking PostGIS extension...")
    
    try:
        db = SessionLocal()
        
        # Check if PostGIS is installed
        result = db.execute(text(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');"
        ))
        has_postgis = result.scalar()
        
        if has_postgis:
            result = db.execute(text("SELECT PostGIS_version();"))
            version = result.scalar()
            print(f"✅ PostGIS is enabled!")
            print(f"   Version: {version}")
        else:
            print("⚠️  PostGIS is not enabled")
            print("   Run this SQL in Supabase SQL Editor:")
            print("   CREATE EXTENSION IF NOT EXISTS postgis;")
        
        db.close()
        return has_postgis
        
    except Exception as e:
        print(f"❌ PostGIS check failed: {e}")
        return False


def check_tables():
    """Check if tables exist."""
    print("\n📊 Checking database tables...")
    
    try:
        db = SessionLocal()
        
        # Check for key tables
        tables_to_check = [
            'users',
            'exploitations',
            'parcelles',
            'interventions',
            'conversations',
            'messages'
        ]
        
        existing_tables = []
        missing_tables = []
        
        for table_name in tables_to_check:
            result = db.execute(text(
                f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}');"
            ))
            exists = result.scalar()
            
            if exists:
                existing_tables.append(table_name)
            else:
                missing_tables.append(table_name)
        
        if existing_tables:
            print(f"✅ Found {len(existing_tables)} tables:")
            for table in existing_tables:
                print(f"   - {table}")
        
        if missing_tables:
            print(f"\n⚠️  Missing {len(missing_tables)} tables:")
            for table in missing_tables:
                print(f"   - {table}")
            print("\n   Run this to create tables:")
            print("   python -c \"from app.core.database import Base, sync_engine; from app.models import *; Base.metadata.create_all(bind=sync_engine)\"")
        
        db.close()
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False


def check_data():
    """Check if sample data exists."""
    print("\n📦 Checking for data...")
    
    try:
        db = SessionLocal()
        
        # Check exploitations
        exp_count = db.execute(select(Exploitation)).scalars().all() if db.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'exploitations');")).scalar() else []
        exp_count = len(exp_count) if isinstance(exp_count, list) else 0
        
        # Check parcelles
        parc_count = db.execute(select(Parcelle)).scalars().all() if db.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'parcelles');")).scalar() else []
        parc_count = len(parc_count) if isinstance(parc_count, list) else 0
        
        # Check interventions
        int_count = db.execute(select(Intervention)).scalars().all() if db.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'interventions');")).scalar() else []
        int_count = len(int_count) if isinstance(int_count, list) else 0
        
        print(f"   Exploitations: {exp_count}")
        print(f"   Parcelles: {parc_count}")
        print(f"   Interventions: {int_count}")
        
        if exp_count == 0:
            print("\n   No data found. Run this to import sample data:")
            print("   python scripts/migration/add_simple_farm_data.py")
        else:
            print("\n✅ Sample data exists!")
        
        db.close()
        return exp_count > 0
        
    except Exception as e:
        print(f"⚠️  Data check skipped: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Supabase Connection Test")
    print("=" * 60)
    
    # Test connection
    if not test_connection():
        print("\n❌ Connection test failed!")
        print("\nPlease check:")
        print("1. Is your Supabase project active?")
        print("2. Are the credentials in .env correct?")
        print("3. Is your IP allowed in Supabase settings?")
        sys.exit(1)
    
    # Check PostGIS
    check_postgis()
    
    # Check tables
    tables_exist = check_tables()
    
    # Check data (only if tables exist)
    if tables_exist:
        check_data()
    
    print("\n" + "=" * 60)
    print("✅ Supabase connection test complete!")
    print("=" * 60)
    
    if not tables_exist:
        print("\n⚠️  Next step: Create database tables")
        print("Run: python -c \"from app.core.database import Base, sync_engine; from app.models import *; Base.metadata.create_all(bind=sync_engine)\"")
    else:
        print("\n✅ Your Supabase database is ready to use!")
        print("\nStart your app with: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()

