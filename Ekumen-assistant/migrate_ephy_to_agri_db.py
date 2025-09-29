#!/usr/bin/env python3
"""
Migrate EPHY data from ekumen_assistant database to agri_db database
"""

import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Force the database to use agri_db (Ekumenbackend database)
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://agri_user:agri_password@localhost:5432/agri_db'
os.environ['DATABASE_URL_SYNC'] = 'postgresql://agri_user:agri_password@localhost:5432/agri_db'

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import AsyncSessionLocal, async_engine
from app.models.ephy import SubstanceActive, Titulaire, Produit


class EPHYMigrator:
    """Migrate EPHY data from ekumen_assistant to agri_db."""
    
    def __init__(self):
        # Source database (ekumen_assistant)
        self.source_engine = create_async_engine(
            'postgresql+asyncpg://postgres:@localhost:5432/ekumen_assistant',
            echo=False
        )
        self.source_session_factory = async_sessionmaker(
            self.source_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Target database (agri_db) - using the configured engine
        self.target_engine = async_engine
        self.target_session_factory = AsyncSessionLocal
        
        self.stats = {
            "substances": 0,
            "titulaires": 0,
            "products": 0,
            "errors": []
        }
    
    async def create_target_tables(self):
        """Create EPHY tables in agri_db."""
        try:
            from sqlalchemy import MetaData
            
            # Create EPHY-only metadata
            ephy_metadata = MetaData()
            
            # Get EPHY tables from models
            ephy_tables = [
                SubstanceActive.__table__,
                Titulaire.__table__,
                Produit.__table__
            ]
            
            for table in ephy_tables:
                table.tometadata(ephy_metadata)
            
            # Create tables in target database
            async with self.target_engine.begin() as conn:
                await conn.run_sync(ephy_metadata.create_all)
            print("✅ EPHY tables created in agri_db")
            
            # Add missing enum values
            await self.add_missing_enum_values()
            
            return True
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    async def add_missing_enum_values(self):
        """Add missing enum values to existing enums."""
        try:
            async with self.target_engine.begin() as conn:
                # Add missing values to ProductType enum if they don't exist
                await conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ADJUVANT' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'producttype')) THEN
                            ALTER TYPE producttype ADD VALUE 'ADJUVANT';
                        END IF;
                        -- Note: Database enum uses PRODUIT_MIXTE (normalized from CSV PRODUIT-MIXTE)
                        IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'PRODUIT_MIXTE' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'producttype')) THEN
                            ALTER TYPE producttype ADD VALUE 'PRODUIT_MIXTE';
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'MELANGE' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'producttype')) THEN
                            ALTER TYPE producttype ADD VALUE 'MELANGE';
                        END IF;
                    END $$;
                """))
            print("✅ Added missing enum values to agri_db")
        except Exception as e:
            print(f"⚠️ Error adding enum values: {e}")
            # Don't raise - this is not critical
    
    async def migrate_substances(self):
        """Migrate substances from source to target."""
        try:
            async with self.source_session_factory() as source_session:
                async with self.target_session_factory() as target_session:
                    # Get all substances from source
                    result = await source_session.execute(text("SELECT * FROM substances_actives"))
                    substances = result.fetchall()
                    
                    for row in substances:
                        substance = SubstanceActive(
                            nom_substance=row.nom_substance,
                            numero_cas=row.numero_cas,
                            etat_autorisation=row.etat_autorisation,
                            variants=row.variants
                        )
                        await target_session.merge(substance)
                        self.stats["substances"] += 1
                    
                    await target_session.commit()
                    print(f"✅ Migrated {self.stats['substances']} substances")
        except Exception as e:
            print(f"❌ Error migrating substances: {e}")
            self.stats["errors"].append(f"Substances: {e}")
    
    async def migrate_titulaires(self):
        """Migrate titulaires from source to target."""
        try:
            async with self.source_session_factory() as source_session:
                async with self.target_session_factory() as target_session:
                    # Get all titulaires from source
                    result = await source_session.execute(text("SELECT * FROM titulaires"))
                    titulaires = result.fetchall()
                    
                    for row in titulaires:
                        titulaire = Titulaire(
                            nom=row.nom
                        )
                        await target_session.merge(titulaire)
                        self.stats["titulaires"] += 1
                    
                    await target_session.commit()
                    print(f"✅ Migrated {self.stats['titulaires']} titulaires")
        except Exception as e:
            print(f"❌ Error migrating titulaires: {e}")
            self.stats["errors"].append(f"Titulaires: {e}")
    
    async def migrate_products(self):
        """Migrate products from source to target."""
        try:
            async with self.source_session_factory() as source_session:
                async with self.target_session_factory() as target_session:
                    # Get all products from source
                    result = await source_session.execute(text("SELECT * FROM produits"))
                    products = result.fetchall()
                    
                    for row in products:
                        product = Produit(
                            numero_amm=row.numero_amm,
                            nom_produit=row.nom_produit,
                            type_produit=row.type_produit,
                            seconds_noms_commerciaux=row.seconds_noms_commerciaux,
                            titulaire_id=row.titulaire_id,
                            type_commercial=row.type_commercial,
                            gamme_usage=row.gamme_usage,
                            mentions_autorisees=row.mentions_autorisees,
                            restrictions_usage=row.restrictions_usage,
                            restrictions_usage_libelle=row.restrictions_usage_libelle,
                            etat_autorisation=row.etat_autorisation,
                            date_retrait_produit=row.date_retrait_produit,
                            date_premiere_autorisation=row.date_premiere_autorisation,
                            numero_amm_reference=row.numero_amm_reference,
                            nom_produit_reference=row.nom_produit_reference
                        )
                        await target_session.merge(product)
                        self.stats["products"] += 1
                    
                    await target_session.commit()
                    print(f"✅ Migrated {self.stats['products']} products")
        except Exception as e:
            print(f"❌ Error migrating products: {e}")
            self.stats["errors"].append(f"Products: {e}")
    
    async def verify_migration(self):
        """Verify the migration was successful."""
        try:
            async with self.target_session_factory() as session:
                # Count records in target database
                result = await session.execute(text("SELECT COUNT(*) FROM produits"))
                product_count = result.scalar()
                
                result = await session.execute(text("SELECT COUNT(*) FROM substances_actives"))
                substance_count = result.scalar()
                
                result = await session.execute(text("SELECT COUNT(*) FROM titulaires"))
                titulaire_count = result.scalar()
                
                print(f"\n📊 Migration Verification:")
                print(f"✅ Products in agri_db: {product_count}")
                print(f"✅ Substances in agri_db: {substance_count}")
                print(f"✅ Titulaires in agri_db: {titulaire_count}")
                
                return product_count > 0
        except Exception as e:
            print(f"❌ Error verifying migration: {e}")
            return False
    
    async def run_migration(self):
        """Run the complete migration process."""
        print("🚀 Starting EPHY migration from ekumen_assistant to agri_db")
        print("=" * 60)
        
        # Create target tables
        if not await self.create_target_tables():
            print("❌ Failed to create target tables")
            return False
        
        # Migrate data
        await self.migrate_substances()
        await self.migrate_titulaires()
        await self.migrate_products()
        
        # Verify migration
        success = await self.verify_migration()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary")
        print("=" * 60)
        print(f"✅ Substances migrated: {self.stats['substances']}")
        print(f"✅ Titulaires migrated: {self.stats['titulaires']}")
        print(f"✅ Products migrated: {self.stats['products']}")
        
        if self.stats["errors"]:
            print(f"⚠️ Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats["errors"]:
                print(f"   - {error}")
        else:
            print("✅ No errors!")
        
        print("=" * 60)
        if success:
            print("🎉 EPHY migration completed successfully!")
        else:
            print("❌ Migration failed!")
        
        return success
    
    async def cleanup(self):
        """Clean up database connections."""
        await self.source_engine.dispose()


async def main():
    """Main migration function."""
    migrator = EPHYMigrator()
    try:
        success = await migrator.run_migration()
        return success
    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
