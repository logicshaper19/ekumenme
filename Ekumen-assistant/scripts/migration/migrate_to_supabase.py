#!/usr/bin/env python3
"""
Migrate data from local PostgreSQL to Supabase

This script:
1. Exports data from local database
2. Imports data to Supabase
3. Verifies the migration

Usage:
    python scripts/migration/migrate_to_supabase.py
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    User, Organization, Conversation, Message,
    Exploitation, Parcelle, Intervention, Intrant,
    Crop, Disease, Pest,
    VoiceJournalEntry, ProductUsage
)


def export_table_data(session, model_class) -> List[Dict[str, Any]]:
    """Export all records from a table as dictionaries."""
    records = session.query(model_class).all()
    data = []
    
    for record in records:
        # Convert SQLAlchemy model to dict
        record_dict = {}
        for column in model_class.__table__.columns:
            value = getattr(record, column.name)
            # Convert special types to JSON-serializable format
            if hasattr(value, 'isoformat'):  # datetime/date
                value = value.isoformat()
            elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                value = str(value)
            record_dict[column.name] = value
        data.append(record_dict)
    
    return data


def import_table_data(session, model_class, data: List[Dict[str, Any]]):
    """Import records into a table."""
    for record_dict in data:
        # Create model instance from dict
        record = model_class(**record_dict)
        session.add(record)
    session.commit()


def migrate_to_supabase(local_db_url: str, supabase_db_url: str):
    """
    Migrate all data from local database to Supabase.
    
    Args:
        local_db_url: Local PostgreSQL connection string
        supabase_db_url: Supabase PostgreSQL connection string
    """
    
    print("🚀 Starting migration to Supabase...")
    print("=" * 60)
    
    # Create engines
    local_engine = create_engine(local_db_url)
    supabase_engine = create_engine(supabase_db_url)
    
    # Create sessions
    LocalSession = sessionmaker(bind=local_engine)
    SupabaseSession = sessionmaker(bind=supabase_engine)
    
    local_session = LocalSession()
    supabase_session = SupabaseSession()
    
    # Define migration order (respecting foreign key constraints)
    migration_order = [
        # Core tables first
        ("Users", User),
        ("Organizations", Organization),
        
        # Agricultural data
        ("Exploitations", Exploitation),
        ("Parcelles", Parcelle),
        ("Interventions", Intervention),
        ("Intrants", Intrant),
        
        # Reference data
        ("Crops", Crop),
        ("Diseases", Disease),
        ("Pests", Pest),
        
        # User data
        ("Conversations", Conversation),
        ("Messages", Message),
        ("Voice Journal Entries", VoiceJournalEntry),
        ("Product Usage", ProductUsage),
    ]
    
    stats = {}
    
    try:
        for table_name, model_class in migration_order:
            print(f"\n📦 Migrating {table_name}...")
            
            # Export from local
            print(f"   Exporting from local database...")
            data = export_table_data(local_session, model_class)
            count = len(data)
            
            if count == 0:
                print(f"   ⚠️  No data to migrate")
                stats[table_name] = 0
                continue
            
            # Import to Supabase
            print(f"   Importing {count} records to Supabase...")
            import_table_data(supabase_session, model_class, data)
            
            print(f"   ✅ Migrated {count} records")
            stats[table_name] = count
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
        print("\n📊 Migration Summary:")
        total = 0
        for table_name, count in stats.items():
            print(f"   {table_name}: {count} records")
            total += count
        print(f"\n   Total: {total} records migrated")
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        for table_name, model_class in migration_order:
            local_count = local_session.query(model_class).count()
            supabase_count = supabase_session.query(model_class).count()
            
            if local_count == supabase_count:
                print(f"   ✅ {table_name}: {supabase_count} records (matches local)")
            else:
                print(f"   ⚠️  {table_name}: {supabase_count} records (local has {local_count})")
        
        print("\n🎉 Migration to Supabase complete!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        supabase_session.rollback()
        raise
    
    finally:
        local_session.close()
        supabase_session.close()


def export_to_json(local_db_url: str, output_file: str = "database_export.json"):
    """
    Export local database to JSON file (backup before migration).
    
    Args:
        local_db_url: Local PostgreSQL connection string
        output_file: Path to output JSON file
    """
    
    print(f"📦 Exporting local database to {output_file}...")
    
    local_engine = create_engine(local_db_url)
    LocalSession = sessionmaker(bind=local_engine)
    local_session = LocalSession()
    
    export_data = {}
    
    tables = [
        ("users", User),
        ("organizations", Organization),
        ("exploitations", Exploitation),
        ("parcelles", Parcelle),
        ("interventions", Intervention),
        ("intrants", Intrant),
        ("crops", Crop),
        ("diseases", Disease),
        ("pests", Pest),
        ("conversations", Conversation),
        ("messages", Message),
        ("voice_journal_entries", VoiceJournalEntry),
        ("product_usage", ProductUsage),
    ]
    
    try:
        for table_name, model_class in tables:
            data = export_table_data(local_session, model_class)
            export_data[table_name] = data
            print(f"   ✅ Exported {len(data)} {table_name}")
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Database exported to {output_file}")
        
    finally:
        local_session.close()


if __name__ == "__main__":
    # Get database URLs from environment or use defaults
    local_db_url = os.getenv(
        "LOCAL_DATABASE_URL",
        "postgresql://agri_user:agri_password@localhost:5432/agri_db"
    )
    
    supabase_db_url = os.getenv("DATABASE_URL_SYNC")
    
    if not supabase_db_url or "[YOUR-PASSWORD]" in supabase_db_url:
        print("❌ Error: Supabase database URL not configured!")
        print("\nPlease update your .env file with your Supabase credentials:")
        print("DATABASE_URL_SYNC=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres")
        print("\nGet your connection string from:")
        print("Supabase Dashboard > Project Settings > Database > Connection string")
        sys.exit(1)
    
    # Ask user what to do
    print("Supabase Migration Tool")
    print("=" * 60)
    print("\nOptions:")
    print("1. Export local database to JSON (backup)")
    print("2. Migrate data to Supabase")
    print("3. Both (recommended)")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        export_to_json(local_db_url)
    elif choice == "2":
        migrate_to_supabase(local_db_url, supabase_db_url)
    elif choice == "3":
        export_to_json(local_db_url)
        print("\n" + "=" * 60 + "\n")
        migrate_to_supabase(local_db_url, supabase_db_url)
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)

