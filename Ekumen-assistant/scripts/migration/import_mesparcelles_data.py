#!/usr/bin/env python3
"""
Import MesParcelles JSON data into the database
"""

import sys
import json
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.models.mesparcelles import Exploitation, Parcelle, Intervention, Intrant
from sqlalchemy import select


def import_mesparcelles_data(json_file_path: str):
    """Import MesParcelles data from JSON file."""
    
    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = SessionLocal()
    
    try:
        print("🚀 Importing MesParcelles data...")
        print("=" * 60)
        
        # Process parcels
        parcels_data = data.get('parcels', [])
        geometries_data = data.get('geometries', [])
        interventions_data = data.get('interventions', [])
        
        # Create a mapping of parcel UUIDs to geometries
        geometry_map = {}
        for geom in geometries_data:
            uuid_parcelle = geom.get('uuid_parcelle')
            if uuid_parcelle:
                geometry_map[uuid_parcelle] = geom.get('geometrie')
        
        stats = {
            'exploitations': 0,
            'parcelles': 0,
            'interventions': 0,
            'intrants': 0
        }
        
        # Process each parcel
        for parcel_data in parcels_data:
            siret = parcel_data.get('siret_exploitation')
            
            # Create or get exploitation
            exploitation = db.execute(
                select(Exploitation).where(Exploitation.siret == siret)
            ).scalar_one_or_none()
            
            if not exploitation:
                exploitation = Exploitation(
                    siret=siret,
                    nom=f"Exploitation {siret}",  # Default name
                    commune_insee=parcel_data.get('insee_commune')
                )
                db.add(exploitation)
                db.flush()
                stats['exploitations'] += 1
                print(f"✅ Created exploitation: {siret}")
            
            # Create parcelle
            uuid_parcelle = parcel_data.get('uuid_parcelle')
            
            # Check if parcelle already exists
            existing_parcelle = db.execute(
                select(Parcelle).where(Parcelle.uuid_parcelle == uuid_parcelle)
            ).scalar_one_or_none()
            
            if existing_parcelle:
                print(f"⚠️  Parcelle {parcel_data.get('nom')} already exists, skipping...")
                continue
            
            # Get crop information
            succession_cultures = parcel_data.get('succession_cultures', [])
            culture_info = succession_cultures[0] if succession_cultures else {}
            variete_info = culture_info.get('varietes_cultures_cepages', [{}])[0]
            
            # Handle empty UUID strings
            uuid_precedent = parcel_data.get('uuid_parcelle_millesime_precedent')
            if uuid_precedent == '':
                uuid_precedent = None

            parcelle = Parcelle(
                siret=siret,
                uuid_parcelle=uuid_parcelle,
                millesime=parcel_data.get('millesime', 2024),
                nom=parcel_data.get('nom'),
                commune_insee=parcel_data.get('insee_commune'),
                surface_ha=Decimal(str(parcel_data.get('surface_mesuree_ha', 0))),
                surface_mesuree_ha=Decimal(str(parcel_data.get('surface_mesuree_ha', 0))),
                id_culture=culture_info.get('id_culture'),
                culture_code=culture_info.get('libelle', '').upper()[:10] if culture_info.get('libelle') else None,
                variete=variete_info.get('libelle'),
                id_variete=variete_info.get('id_variete'),
                geometrie_vide=parcel_data.get('geometrie_vide', False),
                geometrie=geometry_map.get(uuid_parcelle),
                succession_cultures=succession_cultures,
                culture_intermediaire=parcel_data.get('culture_intermediaire'),
                link_parcelle_millesime_precedent=parcel_data.get('link_parcelle_millesime_precedent') or None,
                uuid_parcelle_millesime_precedent=uuid_precedent
            )
            db.add(parcelle)
            db.flush()
            stats['parcelles'] += 1
            print(f"✅ Created parcelle: {parcelle.nom} ({parcelle.surface_ha} ha)")
        
        # Process interventions
        for intervention_data in interventions_data:
            uuid_parcelle = intervention_data.get('uuid_parcelle')
            uuid_intervention = intervention_data.get('uuid_intervention')
            
            # Check if intervention already exists
            existing_intervention = db.execute(
                select(Intervention).where(Intervention.uuid_intervention == uuid_intervention)
            ).scalar_one_or_none()
            
            if existing_intervention:
                continue
            
            # Find the parcelle
            parcelle = db.execute(
                select(Parcelle).where(Parcelle.uuid_parcelle == uuid_parcelle)
            ).scalar_one_or_none()
            
            if not parcelle:
                print(f"⚠️  Parcelle not found for intervention {uuid_intervention}, skipping...")
                continue
            
            # Parse date
            date_str = intervention_data.get('date_debut')
            if date_str:
                intervention_date = date.fromisoformat(date_str)
            else:
                intervention_date = date.today()
            
            # Get intervention type
            type_mapping = {
                1: 'semis',
                2: 'traitement_phytosanitaire',
                3: 'fertilisation',
                4: 'recolte'
            }
            id_type = intervention_data.get('id_type_intervention')
            type_intervention = type_mapping.get(id_type, 'autre')
            
            # Create intervention
            intervention = Intervention(
                parcelle_id=parcelle.id,
                siret=parcelle.siret,
                uuid_intervention=uuid_intervention,
                type_intervention=type_intervention,
                id_type_intervention=id_type,
                date_intervention=intervention_date,
                date_debut=intervention_date,
                date_fin=date.fromisoformat(intervention_data.get('date_fin')) if intervention_data.get('date_fin') else intervention_date,
                surface_travaillee_ha=Decimal(str(intervention_data.get('surface_travaillee_ha', 0))),
                id_culture=intervention_data.get('id_culture'),
                materiel_utilise=intervention_data.get('materiel_utilise'),
                intrants=intervention_data.get('intrants', [])
            )
            db.add(intervention)
            stats['interventions'] += 1
            
            # Process intrants
            intrants_list = intervention_data.get('intrants', [])
            for intrant_data in intrants_list:
                # Create or get intrant
                id_intrant = intrant_data.get('id_intrant')
                
                intrant = db.execute(
                    select(Intrant).where(Intrant.id_intrant == id_intrant)
                ).scalar_one_or_none()
                
                if not intrant:
                    intrant = Intrant(
                        id_intrant=id_intrant,
                        libelle=intrant_data.get('libelle'),
                        type_intrant=intrant_data.get('type_intrant'),
                        id_type_intrant=intrant_data.get('id_type_intrant'),
                        code_amm=intrant_data.get('code_amm')
                    )
                    db.add(intrant)
                    stats['intrants'] += 1
            
            print(f"✅ Created intervention: {type_intervention} on {intervention_date}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ MesParcelles data imported successfully!")
        print("=" * 60)
        print(f"Exploitations: {stats['exploitations']}")
        print(f"Parcelles: {stats['parcelles']}")
        print(f"Interventions: {stats['interventions']}")
        print(f"Intrants: {stats['intrants']}")
        print("\n🎉 Data is ready for use!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error importing data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Default to mesparcelles_data.json in the project root
    json_file = Path(__file__).parent.parent.parent / "mesparcelles_data.json"
    
    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        sys.exit(1)
    
    import_mesparcelles_data(str(json_file))

