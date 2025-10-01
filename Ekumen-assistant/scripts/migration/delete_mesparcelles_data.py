#!/usr/bin/env python3
"""
Delete all MesParcelles data from the database.
This script removes all data from MesParcelles tables while preserving EPHY regulatory data.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import AsyncSessionLocal


class MesParcellesDataDeleter:
    """Delete all MesParcelles data from the database."""
    
    def __init__(self):
        self.stats = {
            "tables_cleared": [],
            "rows_deleted": {},
            "errors": []
        }
        
        # Tables to delete in reverse dependency order (children first, parents last)
        self.deletion_order = [
            # Farm operations tables (most dependent first)
            ("intervention_intrants", "farm_operations"),
            ("intervention_extrants", "farm_operations"),
            ("intervention_prestataires", "farm_operations"),
            ("intervention_materiels", "farm_operations"),
            ("interventions", "farm_operations"),
            ("succession_cultures", "farm_operations"),
            ("cultures_intermediaires", "farm_operations"),
            ("parcelles", "farm_operations"),
            ("service_permissions", "farm_operations"),
            ("valorisation_services", "farm_operations"),
            ("consommateurs_services", "farm_operations"),
            ("service_activation", "farm_operations"),
            ("conformite_reglementaire", "farm_operations"),
            ("exploitations", "farm_operations"),
            
            # Reference tables (shared lookup data)
            ("fertilisant_details", "reference"),
            ("phyto_details", "reference"),
            ("intrants", "reference"),
            ("types_intrant", "reference"),
            ("types_intervention", "reference"),
            ("varietes_cultures_cepages", "reference"),
            ("cultures", "reference"),
            ("regions", "reference"),
        ]
    
    async def check_existing_data(self):
        """Check what MesParcelles data exists before deletion."""
        print("\n🔍 Checking existing MesParcelles data...")
        print("=" * 60)
        
        try:
            async with AsyncSessionLocal() as session:
                for table_name, schema in self.deletion_order:
                    try:
                        result = await session.execute(text(f"""
                            SELECT COUNT(*) FROM {schema}.{table_name}
                        """))
                        count = result.scalar()
                        if count > 0:
                            print(f"  📊 {schema}.{table_name}: {count} rows")
                            self.stats["rows_deleted"][f"{schema}.{table_name}"] = count
                    except Exception as e:
                        # Table might not exist
                        if "does not exist" not in str(e):
                            print(f"  ⚠️  {schema}.{table_name}: Error checking - {e}")
                
                print(f"\n✅ Found data in {len(self.stats['rows_deleted'])} tables")
                
        except Exception as e:
            print(f"❌ Error checking existing data: {e}")
            self.stats["errors"].append(f"Check data: {e}")
    
    async def delete_table_data(self, table_name: str, schema: str):
        """Delete all data from a specific table."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Check if table exists
                    result = await session.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = '{schema}' 
                            AND table_name = '{table_name}'
                        )
                    """))
                    table_exists = result.scalar()
                    
                    if not table_exists:
                        print(f"  ⏭️  {schema}.{table_name}: Table does not exist, skipping")
                        return
                    
                    # Get count before deletion
                    result = await session.execute(text(f"""
                        SELECT COUNT(*) FROM {schema}.{table_name}
                    """))
                    count_before = result.scalar()
                    
                    if count_before == 0:
                        print(f"  ⏭️  {schema}.{table_name}: Already empty")
                        return
                    
                    # Delete all rows
                    await session.execute(text(f"""
                        DELETE FROM {schema}.{table_name}
                    """))
                    
                    # Verify deletion
                    result = await session.execute(text(f"""
                        SELECT COUNT(*) FROM {schema}.{table_name}
                    """))
                    count_after = result.scalar()
                    
                    if count_after == 0:
                        print(f"  ✅ {schema}.{table_name}: Deleted {count_before} rows")
                        self.stats["tables_cleared"].append(f"{schema}.{table_name}")
                    else:
                        print(f"  ⚠️  {schema}.{table_name}: Warning - {count_after} rows remain")
                        self.stats["errors"].append(f"{schema}.{table_name}: Incomplete deletion")
                    
        except Exception as e:
            error_msg = f"{schema}.{table_name}: {str(e)}"
            print(f"  ❌ Error deleting from {schema}.{table_name}: {e}")
            self.stats["errors"].append(error_msg)
    
    async def delete_all_mesparcelles_data(self):
        """Delete all MesParcelles data in the correct order."""
        print("\n🗑️  Deleting MesParcelles data...")
        print("=" * 60)
        
        for table_name, schema in self.deletion_order:
            await self.delete_table_data(table_name, schema)
    
    async def verify_ephy_data_intact(self):
        """Verify that EPHY regulatory data is still intact."""
        print("\n🔍 Verifying EPHY regulatory data is intact...")
        print("=" * 60)
        
        try:
            async with AsyncSessionLocal() as session:
                # Check EPHY tables
                ephy_tables = [
                    ("produits", "regulatory"),
                    ("substances_actives", "regulatory"),
                    ("titulaires", "regulatory"),
                ]
                
                all_intact = True
                for table_name, schema in ephy_tables:
                    try:
                        result = await session.execute(text(f"""
                            SELECT COUNT(*) FROM {schema}.{table_name}
                        """))
                        count = result.scalar()
                        print(f"  ✅ {schema}.{table_name}: {count} rows (intact)")
                    except Exception as e:
                        print(f"  ❌ {schema}.{table_name}: Error - {e}")
                        all_intact = False
                
                if all_intact:
                    print("\n✅ All EPHY regulatory data is intact")
                else:
                    print("\n⚠️  Some EPHY data may be missing")
                    
        except Exception as e:
            print(f"❌ Error verifying EPHY data: {e}")
            self.stats["errors"].append(f"EPHY verification: {e}")
    
    def print_summary(self):
        """Print deletion summary."""
        print("\n" + "=" * 60)
        print("📊 DELETION SUMMARY")
        print("=" * 60)
        
        print(f"\n✅ Tables cleared: {len(self.stats['tables_cleared'])}")
        for table in self.stats['tables_cleared']:
            rows = self.stats['rows_deleted'].get(table, 0)
            print(f"   - {table}: {rows} rows deleted")
        
        if self.stats['errors']:
            print(f"\n❌ Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"   - {error}")
        else:
            print("\n✅ No errors encountered")
        
        print("\n" + "=" * 60)
        print("🎉 MesParcelles data deletion complete!")
        print("=" * 60)
    
    async def run_deletion(self):
        """Run the complete deletion process."""
        print("\n" + "=" * 60)
        print("🗑️  MESPARCELLES DATA DELETION")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check existing data
        await self.check_existing_data()
        
        # Confirm deletion
        if self.stats["rows_deleted"]:
            total_rows = sum(self.stats["rows_deleted"].values())
            print(f"\n⚠️  WARNING: About to delete {total_rows} rows from {len(self.stats['rows_deleted'])} tables")
            print("This action cannot be undone!")
            
            response = input("\nType 'DELETE' to confirm deletion: ")
            if response != "DELETE":
                print("\n❌ Deletion cancelled by user")
                return False
        else:
            print("\n✅ No MesParcelles data found to delete")
            return True
        
        # Delete all data
        await self.delete_all_mesparcelles_data()
        
        # Verify EPHY data is intact
        await self.verify_ephy_data_intact()
        
        # Print summary
        self.print_summary()
        
        return len(self.stats["errors"]) == 0


async def main():
    """Main entry point."""
    deleter = MesParcellesDataDeleter()
    success = await deleter.run_deletion()
    
    if success:
        print("\n✅ Deletion completed successfully!")
        print("You can now add new MesParcelles data.")
        sys.exit(0)
    else:
        print("\n❌ Deletion completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

