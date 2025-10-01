#!/usr/bin/env python3
"""
Create MesParcelles schema and sample data in agri_db
Sets up the complete agricultural data management system with proper integration to EPHY
"""

import asyncio
import sys
import uuid
from pathlib import Path
from sqlalchemy import text
from datetime import datetime, date, timedelta
import random

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import AsyncSessionLocal


class MesParcellesSchemaCreator:
    """Create MesParcelles schema and sample data in agri_db."""
    
    def __init__(self):
        self.stats = {
            "schemas_created": 0,
            "tables_created": 0,
            "sample_records": 0,
            "integration_views": 0,
            "errors": []
        }
    
    async def create_schemas(self):
        """Create schema organization."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Create schemas for organized data structure
                    await session.execute(text("CREATE SCHEMA IF NOT EXISTS farm_operations;"))
                    await session.execute(text("CREATE SCHEMA IF NOT EXISTS reference;"))
                    # Move EPHY tables to regulatory schema
                    await session.execute(text("CREATE SCHEMA IF NOT EXISTS regulatory;"))
                    
                    # Move existing EPHY tables to regulatory schema
                    await session.execute(text("ALTER TABLE produits SET SCHEMA regulatory;"))
                    await session.execute(text("ALTER TABLE substances_actives SET SCHEMA regulatory;"))
                    await session.execute(text("ALTER TABLE titulaires SET SCHEMA regulatory;"))
                    
                    self.stats["schemas_created"] = 3
                    print("✅ Created schema organization: farm_operations, reference, regulatory")
                    
        except Exception as e:
            print(f"❌ Error creating schemas: {e}")
            self.stats["errors"].append(f"Schema creation: {e}")
    
    async def create_reference_tables(self):
        """Create reference tables with sample data."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Regions table
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.regions (
                            id_region INTEGER PRIMARY KEY,
                            libelle VARCHAR(100) NOT NULL,
                            code VARCHAR(50) UNIQUE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    # Cultures table
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.cultures (
                            id_culture INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    # Types intervention table
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.types_intervention (
                            id_type_intervention INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    # Types intrant table
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.types_intrant (
                            id_type_intrant INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL,
                            categorie CHAR(1), -- 'P' for Phyto, 'F' for Fertilizer, etc.
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    # Intrants table (with AMM links to EPHY)
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.intrants (
                            id_intrant INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL,
                            id_type_intrant INTEGER,
                            code_amm VARCHAR(20), -- Links to regulatory.produits.numero_amm
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (id_type_intrant) REFERENCES reference.types_intrant(id_type_intrant)
                        );
                    """))
                    
                    self.stats["tables_created"] += 5
                    print("✅ Created reference tables")
                    
        except Exception as e:
            print(f"❌ Error creating reference tables: {e}")
            self.stats["errors"].append(f"Reference tables: {e}")
    
    async def create_farm_operations_tables(self):
        """Create farm operations tables."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Exploitations table
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.exploitations (
                            siret VARCHAR(14) PRIMARY KEY,
                            id_region INTEGER,
                            nom VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (id_region) REFERENCES reference.regions(id_region)
                        );
                    """))
                    
                    # Parcelles table
                    await session.execute(text("""
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
                    
                    # Interventions table
                    await session.execute(text("""
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
                    
                    # Intervention intrants table
                    await session.execute(text("""
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
                    
                    # Succession cultures table
                    await session.execute(text("""
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
                    
                    # Varietes cultures cepages table
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.varietes_cultures_cepages (
                            id SERIAL PRIMARY KEY,
                            succession_id INTEGER NOT NULL,
                            variete VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (succession_id) REFERENCES farm_operations.succession_cultures(id)
                        );
                    """))
                    
                    # Service management tables
                    await session.execute(text("""
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
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.valorisation_services (
                            codenational VARCHAR(100) PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL,
                            libellecourt VARCHAR(100),
                            description TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    await session.execute(text("""
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
                    
                    self.stats["tables_created"] += 9
                    print("✅ Created farm operations tables")
                    
        except Exception as e:
            print(f"❌ Error creating farm operations tables: {e}")
            self.stats["errors"].append(f"Farm operations tables: {e}")
    
    async def insert_sample_data(self):
        """Insert sample data for testing and demonstration."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Sample regions
                    regions_data = [
                        (1, 'Île-de-France', 'IDF'),
                        (2, 'Normandie', 'NOR'),
                        (3, 'Bretagne', 'BRE'),
                        (4, 'Pays de la Loire', 'PDL'),
                        (5, 'Centre-Val de Loire', 'CVL')
                    ]
                    
                    for id_region, libelle, code in regions_data:
                        await session.execute(text("""
                            INSERT INTO reference.regions (id_region, libelle, code) 
                            VALUES (:id_region, :libelle, :code) 
                            ON CONFLICT (code) DO NOTHING
                        """), {"id_region": id_region, "libelle": libelle, "code": code})
                    
                    # Sample cultures
                    cultures_data = [
                        (1, 'Blé tendre'),
                        (2, 'Maïs grain'),
                        (3, 'Orge'),
                        (4, 'Colza'),
                        (5, 'Tournesol'),
                        (6, 'Pomme de terre'),
                        (7, 'Betterave sucrière'),
                        (8, 'Vigne'),
                        (9, 'Prairie temporaire'),
                        (10, 'Légumes de plein champ')
                    ]
                    
                    for id_culture, libelle in cultures_data:
                        await session.execute(text("""
                            INSERT INTO reference.cultures (id_culture, libelle) 
                            VALUES (:id_culture, :libelle) 
                            ON CONFLICT (id_culture) DO NOTHING
                        """), {"id_culture": id_culture, "libelle": libelle})
                    
                    # Sample intervention types
                    intervention_types = [
                        (1, 'Semis'),
                        (2, 'Traitement phytosanitaire'),
                        (3, 'Fertilisation'),
                        (4, 'Récolte'),
                        (5, 'Travail du sol'),
                        (6, 'Irrigation'),
                        (7, 'Désherbage mécanique'),
                        (8, 'Taille'),
                        (9, 'Pulvérisation'),
                        (10, 'Épandage')
                    ]
                    
                    for id_type, libelle in intervention_types:
                        await session.execute(text("""
                            INSERT INTO reference.types_intervention (id_type_intervention, libelle) 
                            VALUES (:id_type, :libelle) 
                            ON CONFLICT (id_type_intervention) DO NOTHING
                        """), {"id_type": id_type, "libelle": libelle})
                    
                    # Sample intrant types
                    intrant_types = [
                        (1, 'Herbicide', 'P'),
                        (2, 'Fongicide', 'P'),
                        (3, 'Insecticide', 'P'),
                        (4, 'Engrais azoté', 'F'),
                        (5, 'Engrais phosphaté', 'F'),
                        (6, 'Engrais potassique', 'F'),
                        (7, 'Amendement calcaire', 'A'),
                        (8, 'Semences', 'S'),
                        (9, 'Adjuvant', 'P'),
                        (10, 'Régulateur de croissance', 'P')
                    ]
                    
                    for id_type, libelle, categorie in intrant_types:
                        await session.execute(text("""
                            INSERT INTO reference.types_intrant (id_type_intrant, libelle, categorie) 
                            VALUES (:id_type, :libelle, :categorie) 
                            ON CONFLICT (id_type_intrant) DO NOTHING
                        """), {"id_type": id_type, "libelle": libelle, "categorie": categorie})
                    
                    self.stats["sample_records"] += len(regions_data) + len(cultures_data) + len(intervention_types) + len(intrant_types)
                    print("✅ Inserted reference sample data")
                    
        except Exception as e:
            print(f"❌ Error inserting sample data: {e}")
            self.stats["errors"].append(f"Sample data: {e}")
    
    async def create_sample_intrants_with_amm_links(self):
        """Create sample intrants linked to real EPHY AMM codes."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Get some real AMM codes from EPHY data
                    result = await session.execute(text("""
                        SELECT numero_amm, nom_produit, type_produit 
                        FROM regulatory.produits 
                        WHERE mentions_autorisees LIKE '%jardins%' 
                        LIMIT 10
                    """))
                    ephy_products = result.fetchall()
                    
                    # Create intrants linked to real EPHY products
                    intrant_id = 1
                    for amm, nom_produit, type_produit in ephy_products:
                        # Determine intrant type based on EPHY product type
                        if type_produit == 'PPP':
                            id_type_intrant = 2  # Fongicide as default for PPP
                        elif type_produit == 'MFSC':
                            id_type_intrant = 4  # Engrais azoté
                        else:
                            id_type_intrant = 1  # Herbicide as default
                        
                        await session.execute(text("""
                            INSERT INTO reference.intrants (id_intrant, libelle, id_type_intrant, code_amm) 
                            VALUES (:id_intrant, :libelle, :id_type_intrant, :code_amm) 
                            ON CONFLICT (id_intrant) DO NOTHING
                        """), {
                            "id_intrant": intrant_id,
                            "libelle": nom_produit[:255],  # Truncate if too long
                            "id_type_intrant": id_type_intrant,
                            "code_amm": amm
                        })
                        intrant_id += 1
                    
                    self.stats["sample_records"] += len(ephy_products)
                    print(f"✅ Created {len(ephy_products)} intrants linked to EPHY AMM codes")
                    
        except Exception as e:
            print(f"❌ Error creating intrants with AMM links: {e}")
            self.stats["errors"].append(f"AMM-linked intrants: {e}")
    
    async def create_integration_views(self):
        """Create views that integrate MesParcelles and EPHY data."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # View: Product usage with regulatory information
                    await session.execute(text("""
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
                    await session.execute(text("""
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
                    
                    self.stats["integration_views"] = 2
                    print("✅ Created integration views")
                    
        except Exception as e:
            print(f"❌ Error creating integration views: {e}")
            self.stats["errors"].append(f"Integration views: {e}")
    
    async def run_setup(self):
        """Run the complete MesParcelles setup."""
        print("🚀 Creating MesParcelles Schema in agri_db")
        print("=" * 50)
        
        # Create schemas
        await self.create_schemas()
        
        # Create tables
        await self.create_reference_tables()
        await self.create_farm_operations_tables()
        
        # Insert sample data
        await self.insert_sample_data()
        await self.create_sample_intrants_with_amm_links()
        
        # Create integration views
        await self.create_integration_views()
        
        # Print summary
        self.print_summary()
        
        return len(self.stats["errors"]) == 0
    
    def print_summary(self):
        """Print setup summary."""
        print("\n" + "=" * 60)
        print("📊 MesParcelles Schema Creation Summary")
        print("=" * 60)
        print(f"✅ Schemas created: {self.stats['schemas_created']}")
        print(f"✅ Tables created: {self.stats['tables_created']}")
        print(f"✅ Sample records: {self.stats['sample_records']}")
        print(f"✅ Integration views: {self.stats['integration_views']}")
        
        if self.stats["errors"]:
            print(f"⚠️ Errors: {len(self.stats['errors'])}")
            for error in self.stats["errors"]:
                print(f"   - {error}")
        else:
            print("✅ No errors!")
        
        print("\n🎉 MesParcelles schema setup complete!")
        print("\n🔗 Integration features:")
        print("   - EPHY data moved to regulatory schema")
        print("   - MesParcelles data in farm_operations schema")
        print("   - Reference data with AMM links")
        print("   - Integration views for cross-domain queries")


async def main():
    """Main setup function."""
    creator = MesParcellesSchemaCreator()
    success = await creator.run_setup()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
