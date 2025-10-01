#!/usr/bin/env python3
"""
Check for existing MesParcelles data across different databases and locations
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import AsyncSessionLocal


class MesParcellesDataChecker:
    """Check for existing MesParcelles data in various locations."""
    
    def __init__(self):
        self.mesparcelles_tables = [
            'regions', 'exploitations', 'parcelles', 'cultures',
            'types_intervention', 'types_intrant', 'intrants',
            'interventions', 'intervention_intrants', 'succession_cultures',
            'varietes_cultures_cepages', 'consommateurs_services',
            'valorisation_services', 'service_permissions'
        ]
        self.found_locations = []
    
    async def check_agri_db(self):
        """Check if MesParcelles data exists in agri_db."""
        logger.info("🔍 Checking agri_db for existing MesParcelles data...")
        
        try:
            async with AsyncSessionLocal() as session:
                # Check for tables in public schema
                result = await session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = ANY(:table_names)
                    ORDER BY table_name;
                """), {"table_names": self.mesparcelles_tables})
                
                public_tables = [row[0] for row in result.fetchall()]
                
                if public_tables:
                    logger.info(f"✅ Found MesParcelles tables in agri_db.public: {', '.join(public_tables)}")
                    
                    # Check data counts
                    for table in public_tables:
                        try:
                            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = result.scalar()
                            logger.info(f"   📊 {table}: {count} records")
                        except Exception as e:
                            logger.info(f"   ⚠️ {table}: Error reading ({str(e)[:50]}...)")
                    
                    self.found_locations.append({
                        "location": "agri_db.public",
                        "tables": public_tables,
                        "status": "existing_data"
                    })
                else:
                    logger.info("❌ No MesParcelles tables found in agri_db.public")
                
                # Check for existing schemas that might contain MesParcelles data
                result = await session.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'public')
                    ORDER BY schema_name;
                """))
                schemas = [row[0] for row in result.fetchall()]
                
                if schemas:
                    logger.info(f"🔍 Found additional schemas: {', '.join(schemas)}")
                    
                    for schema in schemas:
                        result = await session.execute(text("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = :schema
                            AND table_name = ANY(:table_names)
                            ORDER BY table_name;
                        """), {"schema": schema, "table_names": self.mesparcelles_tables})
                        
                        schema_tables = [row[0] for row in result.fetchall()]
                        if schema_tables:
                            logger.info(f"✅ Found MesParcelles tables in agri_db.{schema}: {', '.join(schema_tables)}")
                            self.found_locations.append({
                                "location": f"agri_db.{schema}",
                                "tables": schema_tables,
                                "status": "existing_data"
                            })
                
        except Exception as e:
            logger.error(f"❌ Error checking agri_db: {e}")
    
    async def check_other_databases(self):
        """Check for MesParcelles data in other common database names."""
        logger.info("🔍 Checking for other databases with MesParcelles data...")
        
        common_db_names = [
            'mesparcelles',
            'mesparcelles_db', 
            'farm_data',
            'agricultural_data',
            'parcelles',
            'exploitations'
        ]
        
        for db_name in common_db_names:
            try:
                # Try to connect to each potential database
                test_url = f"postgresql+asyncpg://agri_user:agri_password@localhost:5432/{db_name}"
                test_engine = create_async_engine(test_url, echo=False)
                
                async with test_engine.begin() as conn:
                    # Check if database exists and has MesParcelles tables
                    result = await conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = ANY(:table_names)
                        ORDER BY table_name;
                    """), {"table_names": self.mesparcelles_tables})
                    
                    found_tables = [row[0] for row in result.fetchall()]
                    
                    if found_tables:
                        logger.info(f"✅ Found MesParcelles data in database '{db_name}': {', '.join(found_tables)}")
                        
                        # Check data counts
                        for table in found_tables:
                            try:
                                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                                count = result.scalar()
                                logger.info(f"   📊 {table}: {count} records")
                            except Exception as e:
                                logger.info(f"   ⚠️ {table}: Error reading")
                        
                        self.found_locations.append({
                            "location": db_name,
                            "tables": found_tables,
                            "status": "separate_database",
                            "connection_url": test_url
                        })
                
                await test_engine.dispose()
                
            except Exception as e:
                # Database doesn't exist or can't connect - this is expected
                logger.debug(f"Database '{db_name}' not accessible: {e}")
                continue
    
    async def check_ekumenbackend_data(self):
        """Check if MesParcelles data exists in the original Ekumenbackend location."""
        logger.info("🔍 Checking Ekumenbackend for MesParcelles data...")
        
        try:
            # Check if there's data in the original Ekumenbackend database structure
            # This might be in agri_db already but in a different format
            async with AsyncSessionLocal() as session:
                # Look for any tables that might contain farm operation data
                result = await session.execute(text("""
                    SELECT table_name, table_schema
                    FROM information_schema.tables 
                    WHERE table_name LIKE '%farm%' 
                    OR table_name LIKE '%parcel%'
                    OR table_name LIKE '%exploitation%'
                    OR table_name LIKE '%intervention%'
                    ORDER BY table_schema, table_name;
                """))
                
                potential_tables = result.fetchall()
                
                if potential_tables:
                    logger.info("🔍 Found potential farm-related tables:")
                    for table_name, schema in potential_tables:
                        logger.info(f"   - {schema}.{table_name}")
                        
                        try:
                            result = await session.execute(text(f"SELECT COUNT(*) FROM {schema}.{table_name}"))
                            count = result.scalar()
                            logger.info(f"     📊 {count} records")
                        except Exception as e:
                            logger.info(f"     ⚠️ Error reading: {str(e)[:50]}...")
                
        except Exception as e:
            logger.error(f"❌ Error checking Ekumenbackend data: {e}")
    
    def generate_recommendations(self):
        """Generate recommendations based on findings."""
        logger.info("\n" + "=" * 60)
        logger.info("📋 RECOMMENDATIONS")
        logger.info("=" * 60)
        
        if not self.found_locations:
            logger.info("🆕 NO EXISTING MESPARCELLES DATA FOUND")
            logger.info("\n✅ Recommended Action: CREATE SAMPLE DATA")
            logger.info("Since no existing MesParcelles data was found, we should:")
            logger.info("1. Create the MesParcelles schema in agri_db")
            logger.info("2. Generate sample data for testing")
            logger.info("3. Set up the integration with EPHY data")
            
            return "create_sample_data"
        
        elif len(self.found_locations) == 1:
            location = self.found_locations[0]
            logger.info(f"📍 FOUND DATA IN: {location['location']}")
            
            if location['status'] == 'existing_data' and 'agri_db' in location['location']:
                logger.info("\n✅ Recommended Action: REORGANIZE EXISTING DATA")
                logger.info("MesParcelles data exists in agri_db but needs schema organization:")
                logger.info("1. Move tables to proper schemas (farm_operations, reference)")
                logger.info("2. Create integration views")
                logger.info("3. Update application connections")
                
                return "reorganize_existing"
            
            elif location['status'] == 'separate_database':
                logger.info("\n✅ Recommended Action: MIGRATE FROM SEPARATE DATABASE")
                logger.info(f"Run migration from: {location.get('connection_url', 'separate database')}")
                logger.info("1. Use the migration script we created")
                logger.info("2. Migrate data to agri_db with proper schema organization")
                
                return "migrate_from_separate"
        
        else:
            logger.info("⚠️ MULTIPLE DATA LOCATIONS FOUND")
            logger.info("Found MesParcelles data in multiple locations:")
            for i, location in enumerate(self.found_locations, 1):
                logger.info(f"{i}. {location['location']} - {len(location['tables'])} tables")
            
            logger.info("\n✅ Recommended Action: CHOOSE PRIMARY SOURCE")
            logger.info("1. Identify which location has the most complete/recent data")
            logger.info("2. Migrate from that source to agri_db")
            logger.info("3. Archive or remove duplicate data")
            
            return "choose_primary_source"
    
    async def run_check(self):
        """Run complete data location check."""
        logger.info("🔍 MesParcelles Data Location Check")
        logger.info("=" * 50)
        
        # Check all possible locations
        await self.check_agri_db()
        await self.check_other_databases()
        await self.check_ekumenbackend_data()
        
        # Generate recommendations
        recommendation = self.generate_recommendations()
        
        return recommendation, self.found_locations


async def main():
    """Main check function."""
    checker = MesParcellesDataChecker()
    recommendation, locations = await checker.run_check()
    
    logger.info(f"\n🎯 NEXT STEP: {recommendation}")
    
    return recommendation, locations


if __name__ == "__main__":
    recommendation, locations = asyncio.run(main())
    
    # Exit with different codes based on recommendation
    exit_codes = {
        "create_sample_data": 1,
        "reorganize_existing": 2, 
        "migrate_from_separate": 3,
        "choose_primary_source": 4
    }
    
    sys.exit(exit_codes.get(recommendation, 0))
