#!/usr/bin/env python3
"""
Import MesParcelles data from JSON file into the database.
This script handles parcels, geometries, interventions, and all related reference data.
"""

import asyncio
import sys
import json
from pathlib import Path
from sqlalchemy import text
from datetime import datetime, date
from typing import Dict, List, Any
import uuid

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import AsyncSessionLocal


class MesParcellesJSONImporter:
    """Import MesParcelles data from JSON format."""
    
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.data = None
        self.stats = {
            "exploitations": 0,
            "parcelles": 0,
            "geometries": 0,
            "cultures": 0,
            "varietes": 0,
            "succession_cultures": 0,
            "interventions": 0,
            "types_intervention": 0,
            "types_intrant": 0,
            "intrants": 0,
            "intervention_intrants": 0,
            "materiels": 0,
            "intervention_materiels": 0,
            "errors": []
        }
        
        # Track unique items to avoid duplicates
        self.unique_cultures = {}
        self.unique_varietes = {}
        self.unique_types_intervention = {}
        self.unique_types_intrant = {}
        self.unique_intrants = {}
        self.unique_materiels = {}
        self.unique_exploitations = set()
    
    def load_json(self):
        """Load JSON data from file."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ Loaded JSON data from {self.json_file_path}")
            print(f"   - Parcels: {len(self.data.get('parcels', []))}")
            print(f"   - Geometries: {len(self.data.get('geometries', []))}")
            print(f"   - Interventions: {len(self.data.get('interventions', []))}")
            return True
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            self.stats["errors"].append(f"Load JSON: {e}")
            return False
    
    async def create_schemas(self):
        """Create database schemas if they don't exist."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    await session.execute(text("CREATE SCHEMA IF NOT EXISTS farm_operations;"))
                    await session.execute(text("CREATE SCHEMA IF NOT EXISTS reference;"))
                    print("✅ Database schemas ready")
        except Exception as e:
            print(f"❌ Error creating schemas: {e}")
            self.stats["errors"].append(f"Create schemas: {e}")
    
    async def create_tables(self):
        """Create all necessary tables."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Reference tables
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.cultures (
                            id_culture INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.varietes_cultures_cepages (
                            id_variete INTEGER PRIMARY KEY,
                            id_culture INTEGER REFERENCES reference.cultures(id_culture),
                            libelle VARCHAR(255) NOT NULL
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.types_intervention (
                            id_type_intervention INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.types_intrant (
                            id_type_intrant INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL,
                            categorie VARCHAR(100)
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.intrants (
                            id_intrant INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL,
                            id_type_intrant INTEGER REFERENCES reference.types_intrant(id_type_intrant)
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS reference.materiels (
                            id_materiel INTEGER PRIMARY KEY,
                            libelle VARCHAR(255) NOT NULL,
                            categorie VARCHAR(100)
                        );
                    """))
                    
                    # Farm operations tables
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.exploitations (
                            siret VARCHAR(14) PRIMARY KEY,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.parcelles (
                            uuid_parcelle UUID PRIMARY KEY,
                            nom VARCHAR(255),
                            millesime INTEGER NOT NULL,
                            insee_commune VARCHAR(10),
                            siret_exploitation VARCHAR(14) REFERENCES farm_operations.exploitations(siret),
                            surface_mesuree_ha DECIMAL(10,4),
                            geometrie_vide BOOLEAN DEFAULT FALSE,
                            culture_intermediaire TEXT,
                            uuid_parcelle_millesime_precedent UUID,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.succession_cultures (
                            id SERIAL PRIMARY KEY,
                            uuid_parcelle UUID REFERENCES farm_operations.parcelles(uuid_parcelle),
                            rang INTEGER NOT NULL,
                            id_culture INTEGER REFERENCES reference.cultures(id_culture)
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.geometries (
                            id SERIAL PRIMARY KEY,
                            uuid_parcelle UUID REFERENCES farm_operations.parcelles(uuid_parcelle),
                            geometrie JSONB,
                            bbox_xmin DECIMAL(12,3),
                            bbox_xmax DECIMAL(12,3),
                            bbox_ymin DECIMAL(12,3),
                            bbox_ymax DECIMAL(12,3)
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.interventions (
                            uuid_intervention UUID PRIMARY KEY,
                            uuid_parcelle UUID REFERENCES farm_operations.parcelles(uuid_parcelle),
                            siret_exploitation VARCHAR(14) REFERENCES farm_operations.exploitations(siret),
                            id_culture INTEGER REFERENCES reference.cultures(id_culture),
                            id_type_intervention INTEGER REFERENCES reference.types_intervention(id_type_intervention),
                            date_debut DATE NOT NULL,
                            date_fin DATE NOT NULL,
                            surface_travaillee_ha DECIMAL(10,4),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.intervention_intrants (
                            id SERIAL PRIMARY KEY,
                            uuid_intervention UUID REFERENCES farm_operations.interventions(uuid_intervention),
                            id_intrant INTEGER REFERENCES reference.intrants(id_intrant),
                            quantite_totale DECIMAL(12,4),
                            unite_intrant_intervention VARCHAR(20),
                            code_amm VARCHAR(50),
                            id_cible INTEGER
                        );
                    """))
                    
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS farm_operations.intervention_materiels (
                            id SERIAL PRIMARY KEY,
                            uuid_intervention UUID REFERENCES farm_operations.interventions(uuid_intervention),
                            id_materiel INTEGER REFERENCES reference.materiels(id_materiel)
                        );
                    """))
                    
                    print("✅ Database tables created")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            self.stats["errors"].append(f"Create tables: {e}")
    
    async def import_reference_data(self):
        """Import all reference data (cultures, types, etc.)."""
        print("\n📚 Importing reference data...")
        
        # Extract unique reference data from JSON
        for parcel in self.data.get('parcels', []):
            for succession in parcel.get('succession_cultures', []):
                culture_id = succession.get('id_culture')
                culture_label = succession.get('libelle')
                if culture_id and culture_label:
                    self.unique_cultures[culture_id] = culture_label
                
                for variete in succession.get('varietes_cultures_cepages', []):
                    variete_id = variete.get('id_variete')
                    variete_label = variete.get('libelle')
                    if variete_id and variete_label:
                        self.unique_varietes[variete_id] = {
                            'libelle': variete_label,
                            'id_culture': culture_id
                        }
        
        for intervention in self.data.get('interventions', []):
            # Culture
            culture = intervention.get('culture', {})
            if culture.get('id_culture') and culture.get('libelle'):
                self.unique_cultures[culture['id_culture']] = culture['libelle']
            
            # Type intervention
            type_interv = intervention.get('type_intervention', {})
            if type_interv.get('id_type_intervention') and type_interv.get('libelle'):
                self.unique_types_intervention[type_interv['id_type_intervention']] = type_interv['libelle']
            
            # Intrants and types
            for intrant in intervention.get('intrants', []):
                type_intrant = intrant.get('type_intrant', {})
                if type_intrant.get('id_type_intrant') and type_intrant.get('libelle'):
                    self.unique_types_intrant[type_intrant['id_type_intrant']] = {
                        'libelle': type_intrant['libelle'],
                        'categorie': type_intrant.get('categorie', '')
                    }
                
                if intrant.get('id_intrant') and intrant.get('libelle'):
                    self.unique_intrants[intrant['id_intrant']] = {
                        'libelle': intrant['libelle'],
                        'id_type_intrant': type_intrant.get('id_type_intrant')
                    }
            
            # Materiels
            for materiel in intervention.get('materiels', []):
                if materiel.get('id_materiel') and materiel.get('libelle'):
                    self.unique_materiels[materiel['id_materiel']] = {
                        'libelle': materiel['libelle'],
                        'categorie': materiel.get('categorie', 'Unknown')
                    }
        
        # Import to database
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Cultures
                    for culture_id, libelle in self.unique_cultures.items():
                        await session.execute(text("""
                            INSERT INTO reference.cultures (id_culture, libelle)
                            VALUES (:id, :libelle)
                            ON CONFLICT (id_culture) DO NOTHING
                        """), {"id": culture_id, "libelle": libelle})
                    self.stats["cultures"] = len(self.unique_cultures)
                    
                    # Varietes
                    for variete_id, data in self.unique_varietes.items():
                        await session.execute(text("""
                            INSERT INTO reference.varietes_cultures_cepages (id_variete, id_culture, libelle)
                            VALUES (:id, :id_culture, :libelle)
                            ON CONFLICT (id_variete) DO NOTHING
                        """), {"id": variete_id, "id_culture": data['id_culture'], "libelle": data['libelle']})
                    self.stats["varietes"] = len(self.unique_varietes)
                    
                    # Types intervention
                    for type_id, libelle in self.unique_types_intervention.items():
                        await session.execute(text("""
                            INSERT INTO reference.types_intervention (id_type_intervention, libelle)
                            VALUES (:id, :libelle)
                            ON CONFLICT (id_type_intervention) DO NOTHING
                        """), {"id": type_id, "libelle": libelle})
                    self.stats["types_intervention"] = len(self.unique_types_intervention)
                    
                    # Types intrant
                    for type_id, data in self.unique_types_intrant.items():
                        await session.execute(text("""
                            INSERT INTO reference.types_intrant (id_type_intrant, libelle, categorie)
                            VALUES (:id, :libelle, :categorie)
                            ON CONFLICT (id_type_intrant) DO NOTHING
                        """), {"id": type_id, "libelle": data['libelle'], "categorie": data['categorie']})
                    self.stats["types_intrant"] = len(self.unique_types_intrant)
                    
                    # Intrants
                    for intrant_id, data in self.unique_intrants.items():
                        await session.execute(text("""
                            INSERT INTO reference.intrants (id_intrant, libelle, id_type_intrant)
                            VALUES (:id, :libelle, :id_type)
                            ON CONFLICT (id_intrant) DO NOTHING
                        """), {"id": intrant_id, "libelle": data['libelle'], "id_type": data['id_type_intrant']})
                    self.stats["intrants"] = len(self.unique_intrants)
                    
                    # Materiels
                    for materiel_id, data in self.unique_materiels.items():
                        await session.execute(text("""
                            INSERT INTO reference.materiels (id_materiel, libelle, categorie)
                            VALUES (:id, :libelle, :categorie)
                            ON CONFLICT (id_materiel) DO NOTHING
                        """), {"id": materiel_id, "libelle": data['libelle'], "categorie": data['categorie']})
                    self.stats["materiels"] = len(self.unique_materiels)
                    
            print(f"  ✅ Cultures: {self.stats['cultures']}")
            print(f"  ✅ Variétés: {self.stats['varietes']}")
            print(f"  ✅ Types intervention: {self.stats['types_intervention']}")
            print(f"  ✅ Types intrant: {self.stats['types_intrant']}")
            print(f"  ✅ Intrants: {self.stats['intrants']}")
            print(f"  ✅ Matériels: {self.stats['materiels']}")
            
        except Exception as e:
            print(f"❌ Error importing reference data: {e}")
            self.stats["errors"].append(f"Reference data: {e}")

    async def import_exploitations(self):
        """Import exploitations (farms)."""
        print("\n🏢 Importing exploitations...")

        # Extract unique SIRETs
        for parcel in self.data.get('parcels', []):
            siret = parcel.get('siret_exploitation')
            if siret:
                self.unique_exploitations.add(siret)

        for intervention in self.data.get('interventions', []):
            siret = intervention.get('siret_exploitation')
            if siret:
                self.unique_exploitations.add(siret)

        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    for siret in self.unique_exploitations:
                        await session.execute(text("""
                            INSERT INTO farm_operations.exploitations (siret)
                            VALUES (:siret)
                            ON CONFLICT (siret) DO NOTHING
                        """), {"siret": siret})

                    self.stats["exploitations"] = len(self.unique_exploitations)
                    print(f"  ✅ Exploitations: {self.stats['exploitations']}")

        except Exception as e:
            print(f"❌ Error importing exploitations: {e}")
            self.stats["errors"].append(f"Exploitations: {e}")

    async def import_parcelles(self):
        """Import parcelles (parcels)."""
        print("\n🌾 Importing parcelles...")

        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    for parcel in self.data.get('parcels', []):
                        uuid_parcelle = parcel.get('uuid_parcelle')

                        await session.execute(text("""
                            INSERT INTO farm_operations.parcelles (
                                uuid_parcelle, nom, millesime, insee_commune,
                                siret_exploitation, surface_mesuree_ha, geometrie_vide,
                                culture_intermediaire, uuid_parcelle_millesime_precedent
                            ) VALUES (
                                :uuid, :nom, :millesime, :insee,
                                :siret, :surface, :geom_vide,
                                :culture_inter, :uuid_precedent
                            )
                            ON CONFLICT (uuid_parcelle) DO NOTHING
                        """), {
                            "uuid": uuid_parcelle,
                            "nom": parcel.get('nom'),
                            "millesime": parcel.get('millesime'),
                            "insee": parcel.get('insee_commune'),
                            "siret": parcel.get('siret_exploitation'),
                            "surface": parcel.get('surface_mesuree_ha'),
                            "geom_vide": parcel.get('geometrie_vide', False),
                            "culture_inter": parcel.get('culture_intermediaire'),
                            "uuid_precedent": parcel.get('uuid_parcelle_millesime_precedent') or None
                        })

                        self.stats["parcelles"] += 1

                        # Import succession cultures
                        for succession in parcel.get('succession_cultures', []):
                            await session.execute(text("""
                                INSERT INTO farm_operations.succession_cultures (
                                    uuid_parcelle, rang, id_culture
                                ) VALUES (:uuid, :rang, :id_culture)
                            """), {
                                "uuid": uuid_parcelle,
                                "rang": succession.get('rang'),
                                "id_culture": succession.get('id_culture')
                            })
                            self.stats["succession_cultures"] += 1

                    print(f"  ✅ Parcelles: {self.stats['parcelles']}")
                    print(f"  ✅ Succession cultures: {self.stats['succession_cultures']}")

        except Exception as e:
            print(f"❌ Error importing parcelles: {e}")
            self.stats["errors"].append(f"Parcelles: {e}")

    async def import_geometries(self):
        """Import geometries."""
        print("\n📍 Importing geometries...")

        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    for geometry in self.data.get('geometries', []):
                        bbox = geometry.get('bounding_box', {})

                        await session.execute(text("""
                            INSERT INTO farm_operations.geometries (
                                uuid_parcelle, geometrie, bbox_xmin, bbox_xmax, bbox_ymin, bbox_ymax
                            ) VALUES (
                                :uuid, :geom, :xmin, :xmax, :ymin, :ymax
                            )
                        """), {
                            "uuid": geometry.get('uuid_parcelle'),
                            "geom": json.dumps(geometry.get('geometrie')),
                            "xmin": bbox.get('xmin'),
                            "xmax": bbox.get('xmax'),
                            "ymin": bbox.get('ymin'),
                            "ymax": bbox.get('ymax')
                        })

                        self.stats["geometries"] += 1

                    print(f"  ✅ Geometries: {self.stats['geometries']}")

        except Exception as e:
            print(f"❌ Error importing geometries: {e}")
            self.stats["errors"].append(f"Geometries: {e}")

    async def import_interventions(self):
        """Import interventions and related data."""
        print("\n🚜 Importing interventions...")

        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    for intervention in self.data.get('interventions', []):
                        uuid_intervention = intervention.get('uuid_intervention')
                        culture = intervention.get('culture', {})
                        type_interv = intervention.get('type_intervention', {})

                        # Parse dates
                        date_debut_str = intervention.get('date_debut')
                        date_fin_str = intervention.get('date_fin')
                        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else None
                        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else None

                        # Insert intervention
                        await session.execute(text("""
                            INSERT INTO farm_operations.interventions (
                                uuid_intervention, uuid_parcelle, siret_exploitation,
                                id_culture, id_type_intervention, date_debut, date_fin,
                                surface_travaillee_ha
                            ) VALUES (
                                :uuid, :uuid_parcelle, :siret,
                                :id_culture, :id_type, :date_debut, :date_fin,
                                :surface
                            )
                            ON CONFLICT (uuid_intervention) DO NOTHING
                        """), {
                            "uuid": uuid_intervention,
                            "uuid_parcelle": intervention.get('uuid_parcelle'),
                            "siret": intervention.get('siret_exploitation'),
                            "id_culture": culture.get('id_culture'),
                            "id_type": type_interv.get('id_type_intervention'),
                            "date_debut": date_debut,
                            "date_fin": date_fin,
                            "surface": intervention.get('surface_travaillee_ha')
                        })

                        self.stats["interventions"] += 1

                        # Insert intrants
                        for intrant in intervention.get('intrants', []):
                            phyto = intrant.get('phyto', {})
                            cible = phyto.get('cible', {}) if phyto else {}

                            await session.execute(text("""
                                INSERT INTO farm_operations.intervention_intrants (
                                    uuid_intervention, id_intrant, quantite_totale,
                                    unite_intrant_intervention, code_amm, id_cible
                                ) VALUES (
                                    :uuid, :id_intrant, :quantite,
                                    :unite, :code_amm, :id_cible
                                )
                            """), {
                                "uuid": uuid_intervention,
                                "id_intrant": intrant.get('id_intrant'),
                                "quantite": intrant.get('quantite_totale'),
                                "unite": intrant.get('unite_intrant_intervention'),
                                "code_amm": phyto.get('code_amm') if phyto else None,
                                "id_cible": cible.get('id_cible') if cible else None
                            })

                            self.stats["intervention_intrants"] += 1

                        # Insert materiels
                        for materiel in intervention.get('materiels', []):
                            await session.execute(text("""
                                INSERT INTO farm_operations.intervention_materiels (
                                    uuid_intervention, id_materiel
                                ) VALUES (:uuid, :id_materiel)
                            """), {
                                "uuid": uuid_intervention,
                                "id_materiel": materiel.get('id_materiel')
                            })

                            self.stats["intervention_materiels"] += 1

                    print(f"  ✅ Interventions: {self.stats['interventions']}")
                    print(f"  ✅ Intervention intrants: {self.stats['intervention_intrants']}")
                    print(f"  ✅ Intervention matériels: {self.stats['intervention_materiels']}")

        except Exception as e:
            print(f"❌ Error importing interventions: {e}")
            self.stats["errors"].append(f"Interventions: {e}")

    def print_summary(self):
        """Print import summary."""
        print("\n" + "=" * 60)
        print("📊 IMPORT SUMMARY")
        print("=" * 60)

        print("\n✅ Data imported successfully:")
        print(f"   - Exploitations: {self.stats['exploitations']}")
        print(f"   - Parcelles: {self.stats['parcelles']}")
        print(f"   - Geometries: {self.stats['geometries']}")
        print(f"   - Cultures: {self.stats['cultures']}")
        print(f"   - Variétés: {self.stats['varietes']}")
        print(f"   - Succession cultures: {self.stats['succession_cultures']}")
        print(f"   - Interventions: {self.stats['interventions']}")
        print(f"   - Types intervention: {self.stats['types_intervention']}")
        print(f"   - Types intrant: {self.stats['types_intrant']}")
        print(f"   - Intrants: {self.stats['intrants']}")
        print(f"   - Intervention intrants: {self.stats['intervention_intrants']}")
        print(f"   - Matériels: {self.stats['materiels']}")
        print(f"   - Intervention matériels: {self.stats['intervention_materiels']}")

        if self.stats['errors']:
            print(f"\n❌ Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"   - {error}")
        else:
            print("\n✅ No errors encountered")

        print("\n" + "=" * 60)

    async def run_import(self):
        """Run the complete import process."""
        print("\n" + "=" * 60)
        print("📥 MESPARCELLES JSON IMPORT")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Load JSON
        if not self.load_json():
            return False

        # Create schemas and tables
        await self.create_schemas()
        await self.create_tables()

        # Import data in correct order
        await self.import_reference_data()
        await self.import_exploitations()
        await self.import_parcelles()
        await self.import_geometries()
        await self.import_interventions()

        # Print summary
        self.print_summary()

        return len(self.stats["errors"]) == 0


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python import_mesparcelles_json.py <json_file_path>")
        print("\nExample:")
        print("  python import_mesparcelles_json.py mesparcelles_data.json")
        sys.exit(1)

    json_file = sys.argv[1]

    if not Path(json_file).exists():
        print(f"❌ Error: File not found: {json_file}")
        sys.exit(1)

    importer = MesParcellesJSONImporter(json_file)
    success = await importer.run_import()

    if success:
        print("\n✅ Import completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Import completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

