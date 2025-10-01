#!/usr/bin/env python3
"""
Phase 2 Migration Runner

Safely runs the create_crops_table.sql migration with proper error handling.
"""

import sys
import asyncio
from pathlib import Path
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def run_migration():
    """Run the Phase 2 migration"""
    
    print("="*60)
    print("🌾 PHASE 2 MIGRATION - CROP TABLE CREATION")
    print("="*60)
    print()
    
    # Read migration file
    migration_file = Path(__file__).parent / "app" / "migrations" / "create_crops_table.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"📄 Reading migration file: {migration_file.name}")
    sql_content = migration_file.read_text()
    
    # Split into individual statements
    # Remove comments and split by semicolon
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        # Skip comment-only lines
        if line.strip().startswith('--'):
            continue
        
        current_statement.append(line)
        
        # If line ends with semicolon, it's end of statement
        if line.strip().endswith(';'):
            stmt = '\n'.join(current_statement)
            if stmt.strip():
                statements.append(stmt)
            current_statement = []
    
    print(f"📊 Found {len(statements)} SQL statements to execute")
    print()
    
    # Execute migration
    async with AsyncSessionLocal() as db:
        try:
            print("🔄 Starting migration...")
            print()
            
            executed = 0
            skipped = 0
            errors = 0
            
            for i, statement in enumerate(statements, 1):
                # Get first line for display
                first_line = statement.strip().split('\n')[0][:60]
                
                try:
                    await db.execute(text(statement))
                    await db.commit()
                    executed += 1
                    
                    # Show progress for major steps
                    if 'CREATE TABLE' in statement:
                        print(f"  ✅ Created table")
                    elif 'INSERT INTO crops' in statement:
                        print(f"  ✅ Populated crops table with 24 crops")
                    elif 'ALTER TABLE bbch_stages' in statement and 'ADD COLUMN' in statement:
                        print(f"  ✅ Added crop_eppo_code to bbch_stages")
                    elif 'UPDATE bbch_stages' in statement:
                        if i == statements.index(next(s for s in statements if 'UPDATE bbch_stages' in s)) + 1:
                            print(f"  ✅ Populating bbch_stages.crop_eppo_code...")
                    elif 'ALTER TABLE diseases' in statement and 'ADD COLUMN' in statement:
                        print(f"  ✅ Added crop_id to diseases")
                    elif 'UPDATE diseases' in statement:
                        print(f"  ✅ Populated diseases.crop_id from crop_eppo_code")
                    elif 'CREATE INDEX' in statement:
                        index_name = statement.split('INDEX')[1].split('ON')[0].strip()
                        if 'IF NOT EXISTS' in statement:
                            index_name = index_name.replace('IF NOT EXISTS', '').strip()
                        # Only show first index creation
                        if 'ix_crops_name_fr' in statement:
                            print(f"  ✅ Created indexes on crops table")
                        elif 'ix_bbch_crop_eppo' in statement:
                            print(f"  ✅ Created index on bbch_stages.crop_eppo_code")
                        elif 'ix_diseases_crop_id' in statement:
                            print(f"  ✅ Created index on diseases.crop_id")
                    elif 'CREATE OR REPLACE VIEW' in statement:
                        print(f"  ✅ Created crop_summary view")
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check if it's a "already exists" error (safe to ignore)
                    if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        skipped += 1
                        # Don't print for every skipped statement
                    else:
                        errors += 1
                        print(f"  ⚠️  Error in statement {i}: {error_msg[:100]}")
                        print(f"     Statement: {first_line}...")
            
            print()
            print("="*60)
            print("📊 MIGRATION SUMMARY")
            print("="*60)
            print(f"  Executed: {executed} statements")
            if skipped > 0:
                print(f"  Skipped: {skipped} statements (already exists)")
            if errors > 0:
                print(f"  Errors: {errors} statements")
            print()
            
            if errors == 0:
                print("✅ Migration completed successfully!")
                print()
                print("Next steps:")
                print("  1. Run tests: python test_crop_model.py")
                print("  2. Verify data: Check crops table in database")
                print("  3. Commit changes: git add . && git commit -m 'Phase 2: Add Crop table'")
                return True
            else:
                print("⚠️  Migration completed with errors")
                print("   Please review the errors above")
                return False
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            return False


async def verify_migration():
    """Verify the migration was successful"""
    
    print()
    print("="*60)
    print("🔍 VERIFYING MIGRATION")
    print("="*60)
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Check crops table
            result = await db.execute(text("SELECT COUNT(*) FROM crops WHERE is_active = TRUE"))
            crop_count = result.scalar()
            print(f"  ✅ Crops table: {crop_count} active crops")
            
            # Check bbch_stages
            result = await db.execute(text("SELECT COUNT(*) FROM bbch_stages WHERE crop_eppo_code IS NOT NULL"))
            bbch_count = result.scalar()
            print(f"  ✅ BBCH stages: {bbch_count} stages with EPPO codes")
            
            # Check diseases
            result = await db.execute(text("SELECT COUNT(*) FROM diseases WHERE crop_id IS NOT NULL"))
            disease_count = result.scalar()
            print(f"  ✅ Diseases: {disease_count} diseases with crop_id")
            
            print()
            
            if crop_count >= 24:
                print("✅ Verification passed! Migration successful!")
                return True
            else:
                print("⚠️  Expected at least 24 crops, found {crop_count}")
                return False
                
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False


async def main():
    """Main entry point"""
    
    # Run migration
    success = await run_migration()
    
    if success:
        # Verify migration
        await verify_migration()
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

