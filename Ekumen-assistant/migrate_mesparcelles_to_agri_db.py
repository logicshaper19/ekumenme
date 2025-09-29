#!/usr/bin/env python3
"""
Migrate MesParcelles data to agri_db with proper schema organization
Consolidates all agricultural data into one database for better integration
"""

import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))


class MesParcellesMigrator:
    """Migrate MesParcelles data to agri_db with schema organization."""
    
    def __init__(self, source_db_url: str):
        """
        Initialize migrator.
        
        Args:
            source_db_url: Connection string for source MesParcelles database
        """
        # Source database (MesParcelles)
        self.source_engine = create_async_engine(source_db_url, echo=False)
        self.source_session_factory = async_sessionmaker(
            self.source_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Target database (agri_db) - using configured connection
        from app.core.database import async_engine, AsyncSessionLocal
        self.target_engine = async_engine
        self.target_session_factory = AsyncSessionLocal
        
        self.stats = {
            "regions": 0,
            "exploitations": 0,
            "parcelles": 0,
            "cultures": 0,
            "types_intervention": 0,
            "types_intrant": 0,
            "intrants": 0,
            "interventions": 0,
            "intervention_intrants": 0,
            "succession_cultures": 0,
            "varietes_cultures_cepages": 0,
            "consommateurs_services": 0,
            "valorisation_services": 0,
            "service_permissions": 0,
            "errors": []
        }
    
    async def create_schemas(self):
        """Create schema organization in target database."""
        try:
            async with self.target_engine.begin() as conn:
                # Create schemas for organized data structure
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS farm_operations;"))
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS reference;"))
                # regulatory schema already exists from EPHY migration
                
                logger.info("✅ Created schema organization in agri_db")
                return True
        except Exception as e:
            logger.error(f"❌ Error creating schemas: {e}")
            return False
    
    async def create_mesparcelles_tables(self):
        """Create MesParcelles tables in the target database with proper schemas."""
        try:
            async with self.target_engine.begin() as conn:
                # Reference tables (shared lookup data)
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS reference.regions (
                        id_region INTEGER PRIMARY KEY,
                        libelle VARCHAR(100) NOT NULL,
                        code VARCHAR(50) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS reference.cultures (
                        id_culture INTEGER PRIMARY KEY,
                        libelle VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS reference.types_intervention (
                        id_type_intervention INTEGER PRIMARY KEY,
                        libelle VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS reference.types_intrant (
                        id_type_intrant INTEGER PRIMARY KEY,
                        libelle VARCHAR(255) NOT NULL,
                        categorie CHAR(1), -- 'P' for Phyto, 'F' for Fertilizer, etc.
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS reference.intrants (
                        id_intrant INTEGER PRIMARY KEY,
                        libelle VARCHAR(255) NOT NULL,
                        id_type_intrant INTEGER,
                        code_amm VARCHAR(20), -- Links to regulatory.produits.numero_amm
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (id_type_intrant) REFERENCES reference.types_intrant(id_type_intrant)
                    );
                """))
                
                # Farm operations tables
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.exploitations (
                        siret VARCHAR(14) PRIMARY KEY,
                        id_region INTEGER,
                        nom VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (id_region) REFERENCES reference.regions(id_region)
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.parcelles (
                        uuid_parcelle UUID PRIMARY KEY,
                        siret_exploitation VARCHAR(14) NOT NULL,
                        millesime INTEGER NOT NULL,
                        nom VARCHAR(255),
                        surface_mesuree_ha DECIMAL(10,2),
                        insee_commune VARCHAR(10),
                        geometrie_vide BOOLEAN DEFAULT FALSE,
                        uuid_parcelle_millesime_precedent UUID,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (siret_exploitation) REFERENCES farm_operations.exploitations(siret),
                        FOREIGN KEY (uuid_parcelle_millesime_precedent) REFERENCES farm_operations.parcelles(uuid_parcelle)
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.interventions (
                        uuid_intervention UUID PRIMARY KEY,
                        siret_exploitation VARCHAR(14) NOT NULL,
                        uuid_parcelle UUID NOT NULL,
                        numero_lot INTEGER,
                        id_culture INTEGER,
                        id_type_intervention INTEGER NOT NULL,
                        surface_travaillee_ha DECIMAL(10,2),
                        date_debut DATE NOT NULL,
                        date_fin DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (siret_exploitation) REFERENCES farm_operations.exploitations(siret),
                        FOREIGN KEY (uuid_parcelle) REFERENCES farm_operations.parcelles(uuid_parcelle),
                        FOREIGN KEY (id_culture) REFERENCES reference.cultures(id_culture),
                        FOREIGN KEY (id_type_intervention) REFERENCES reference.types_intervention(id_type_intervention)
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.intervention_intrants (
                        id SERIAL PRIMARY KEY,
                        uuid_intervention UUID NOT NULL,
                        id_intrant INTEGER NOT NULL,
                        quantite_totale DECIMAL(10,3),
                        unite_intrant_intervention VARCHAR(10), -- L, kg, etc.
                        cible VARCHAR(255), -- Target pest/disease for phyto products
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (uuid_intervention) REFERENCES farm_operations.interventions(uuid_intervention),
                        FOREIGN KEY (id_intrant) REFERENCES reference.intrants(id_intrant)
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.succession_cultures (
                        id SERIAL PRIMARY KEY,
                        uuid_parcelle UUID NOT NULL,
                        id_culture INTEGER NOT NULL,
                        rang INTEGER NOT NULL, -- Order in succession
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (uuid_parcelle) REFERENCES farm_operations.parcelles(uuid_parcelle),
                        FOREIGN KEY (id_culture) REFERENCES reference.cultures(id_culture)
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.varietes_cultures_cepages (
                        id SERIAL PRIMARY KEY,
                        succession_id INTEGER NOT NULL,
                        variete VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (succession_id) REFERENCES farm_operations.succession_cultures(id)
                    );
                """))
                
                # Service management tables
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.consommateurs_services (
                        id SERIAL PRIMARY KEY,
                        siret VARCHAR(14) NOT NULL,
                        millesime INTEGER NOT NULL,
                        service_actif BOOLEAN DEFAULT FALSE,
                        date_activation TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (siret) REFERENCES farm_operations.exploitations(siret),
                        UNIQUE(siret, millesime)
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.valorisation_services (
                        codenational VARCHAR(100) PRIMARY KEY,
                        libelle VARCHAR(255) NOT NULL,
                        libellecourt VARCHAR(100),
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS farm_operations.service_permissions (
                        id SERIAL PRIMARY KEY,
                        siret VARCHAR(14) NOT NULL,
                        codenational VARCHAR(100) NOT NULL,
                        client_id VARCHAR(100) NOT NULL,
                        accorde BOOLEAN DEFAULT FALSE,
                        date_octroi TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (siret) REFERENCES farm_operations.exploitations(siret),
                        FOREIGN KEY (codenational) REFERENCES farm_operations.valorisation_services(codenational)
                    );
                """))
                
                logger.info("✅ Created MesParcelles tables in agri_db with schema organization")
                return True
        except Exception as e:
            logger.error(f"❌ Error creating MesParcelles tables: {e}")
            return False
    
    async def migrate_table_data(self, table_name: str, target_schema: str = None):
        """Migrate data from a specific table."""
        try:
            target_table = f"{target_schema}.{table_name}" if target_schema else table_name
            
            async with self.source_session_factory() as source_session:
                async with self.target_session_factory() as target_session:
                    # Get all data from source table
                    result = await source_session.execute(text(f"SELECT * FROM {table_name}"))
                    rows = result.fetchall()
                    
                    if not rows:
                        logger.info(f"⚠️ No data found in {table_name}")
                        return
                    
                    # Get column names
                    columns = result.keys()
                    
                    # Prepare insert statement
                    column_list = ", ".join(columns)
                    placeholder_list = ", ".join([f":{col}" for col in columns])
                    
                    insert_sql = f"""
                        INSERT INTO {target_table} ({column_list}) 
                        VALUES ({placeholder_list})
                        ON CONFLICT DO NOTHING
                    """
                    
                    # Insert data in batches
                    batch_size = 1000
                    for i in range(0, len(rows), batch_size):
                        batch = rows[i:i + batch_size]
                        batch_data = [dict(row._mapping) for row in batch]
                        
                        await target_session.execute(text(insert_sql), batch_data)
                        self.stats[table_name] += len(batch_data)
                    
                    await target_session.commit()
                    logger.info(f"✅ Migrated {self.stats[table_name]} records from {table_name}")
                    
        except Exception as e:
            logger.error(f"❌ Error migrating {table_name}: {e}")
            self.stats["errors"].append(f"{table_name}: {e}")
    
    async def create_integration_views(self):
        """Create views that integrate MesParcelles and EPHY data."""
        try:
            async with self.target_engine.begin() as conn:
                # View: Product usage with regulatory information
                await conn.execute(text("""
                    CREATE OR REPLACE VIEW farm_operations.product_usage_with_regulatory AS
                    SELECT 
                        i.uuid_intervention,
                        i.date_debut,
                        i.date_fin,
                        i.surface_travaillee_ha,
                        inp.libelle as produit_utilise,
                        ii.quantite_totale,
                        ii.unite_intrant_intervention,
                        ii.cible,
                        p.nom_produit as produit_ephy,
                        p.type_produit,
                        p.mentions_autorisees,
                        p.restrictions_usage,
                        e.nom as exploitation_nom,
                        parc.nom as parcelle_nom
                    FROM farm_operations.interventions i
                    JOIN farm_operations.intervention_intrants ii ON i.uuid_intervention = ii.uuid_intervention
                    JOIN reference.intrants inp ON ii.id_intrant = inp.id_intrant
                    LEFT JOIN regulatory.produits p ON inp.code_amm = p.numero_amm
                    JOIN farm_operations.exploitations e ON i.siret_exploitation = e.siret
                    JOIN farm_operations.parcelles parc ON i.uuid_parcelle = parc.uuid_parcelle;
                """))
                
                # View: Compliance dashboard
                await conn.execute(text("""
                    CREATE OR REPLACE VIEW farm_operations.compliance_dashboard AS
                    SELECT 
                        e.siret,
                        e.nom as exploitation,
                        COUNT(DISTINCT i.uuid_intervention) as total_interventions,
                        COUNT(DISTINCT CASE WHEN p.mentions_autorisees LIKE '%jardins%' THEN i.uuid_intervention END) as garden_authorized,
                        COUNT(DISTINCT CASE WHEN p.mentions_autorisees LIKE '%biologique%' THEN i.uuid_intervention END) as organic_authorized,
                        COUNT(DISTINCT CASE WHEN p.numero_amm IS NULL AND inp.code_amm IS NOT NULL THEN i.uuid_intervention END) as unknown_amm
                    FROM farm_operations.exploitations e
                    LEFT JOIN farm_operations.interventions i ON e.siret = i.siret_exploitation
                    LEFT JOIN farm_operations.intervention_intrants ii ON i.uuid_intervention = ii.uuid_intervention
                    LEFT JOIN reference.intrants inp ON ii.id_intrant = inp.id_intrant
                    LEFT JOIN regulatory.produits p ON inp.code_amm = p.numero_amm
                    GROUP BY e.siret, e.nom;
                """))
                
                logger.info("✅ Created integration views")
                return True
        except Exception as e:
            logger.error(f"❌ Error creating integration views: {e}")
            return False
    
    async def run_migration(self, source_db_url: str):
        """Run the complete migration process."""
        logger.info("🚀 Starting MesParcelles migration to agri_db")
        logger.info("=" * 60)
        
        # Create schemas
        if not await self.create_schemas():
            return False
        
        # Create tables
        if not await self.create_mesparcelles_tables():
            return False
        
        # Migration order (respecting foreign key dependencies)
        migration_order = [
            ("regions", "reference"),
            ("cultures", "reference"),
            ("types_intervention", "reference"),
            ("types_intrant", "reference"),
            ("intrants", "reference"),
            ("exploitations", "farm_operations"),
            ("parcelles", "farm_operations"),
            ("interventions", "farm_operations"),
            ("intervention_intrants", "farm_operations"),
            ("succession_cultures", "farm_operations"),
            ("varietes_cultures_cepages", "farm_operations"),
            ("consommateurs_services", "farm_operations"),
            ("valorisation_services", "farm_operations"),
            ("service_permissions", "farm_operations")
        ]
        
        # Migrate data
        for table_name, schema in migration_order:
            await self.migrate_table_data(table_name, schema)
        
        # Create integration views
        await self.create_integration_views()
        
        # Print summary
        self.print_migration_summary()
        
        return len(self.stats["errors"]) == 0
    
    def print_migration_summary(self):
        """Print migration summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 MesParcelles Migration Summary")
        logger.info("=" * 60)
        
        total_records = 0
        for key, value in self.stats.items():
            if key != "errors" and isinstance(value, int):
                logger.info(f"✅ {key}: {value} records")
                total_records += value
        
        logger.info(f"\n📈 Total records migrated: {total_records}")
        
        if self.stats["errors"]:
            logger.info(f"⚠️ Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats["errors"]:
                logger.info(f"   - {error}")
        else:
            logger.info("✅ No errors!")
        
        logger.info("=" * 60)
        logger.info("🎉 MesParcelles migration completed!")
        logger.info("\n🔗 Integration features available:")
        logger.info("   - farm_operations.product_usage_with_regulatory view")
        logger.info("   - farm_operations.compliance_dashboard view")
        logger.info("   - Cross-schema queries between farm data and EPHY regulatory data")
    
    async def cleanup(self):
        """Clean up database connections."""
        await self.source_engine.dispose()


async def main():
    """Main migration function."""
    if len(sys.argv) < 2:
        print("Usage: python migrate_mesparcelles_to_agri_db.py <source_database_url>")
        print("Example: python migrate_mesparcelles_to_agri_db.py postgresql+asyncpg://user:pass@localhost:5432/mesparcelles")
        sys.exit(1)
    
    source_db_url = sys.argv[1]
    
    migrator = MesParcellesMigrator(source_db_url)
    try:
        success = await migrator.run_migration(source_db_url)
        return success
    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
