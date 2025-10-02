#!/usr/bin/env python3
"""
Direct import of MesParcelles data to Supabase
"""

import json
from sqlalchemy import create_engine, text
from datetime import date
from decimal import Decimal

# Supabase connection
db_url = 'postgresql://postgres:slp225khayegA!@db.ghsfhuekuebwnrjhlitr.supabase.co:5432/postgres'

print('🔌 Connecting to Supabase...')
engine = create_engine(db_url)

# Load JSON data
print('📂 Loading mesparcelles_data.json...')
with open('mesparcelles_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

parcels_data = data.get('parcels', [])
geometries_data = data.get('geometries', [])
interventions_data = data.get('interventions', [])

print(f'Found {len(parcels_data)} parcels, {len(interventions_data)} interventions')

# Create geometry mapping
geometry_map = {}
for geom in geometries_data:
    uuid_parcelle = geom.get('uuid_parcelle')
    if uuid_parcelle:
        geometry_map[uuid_parcelle] = geom.get('geometrie')

stats = {'exploitations': 0, 'parcelles': 0, 'interventions': 0, 'intrants': 0}

with engine.connect() as conn:
    print('\n🚀 Starting import...')
    
    # Process parcels
    for parcel_data in parcels_data:
        siret = parcel_data.get('siret_exploitation')
        
        # Check if exploitation exists
        result = conn.execute(text(
            "SELECT siret FROM exploitations WHERE siret = :siret"
        ), {"siret": siret})
        
        if not result.fetchone():
            # Create exploitation
            conn.execute(text("""
                INSERT INTO exploitations (siret, nom, commune_insee)
                VALUES (:siret, :nom, :commune_insee)
            """), {
                "siret": siret,
                "nom": f"Exploitation {siret}",
                "commune_insee": parcel_data.get('insee_commune')
            })
            stats['exploitations'] += 1
            print(f'✅ Created exploitation: {siret}')
        
        # Get crop info
        succession_cultures = parcel_data.get('succession_cultures', [])
        culture_info = succession_cultures[0] if succession_cultures else {}
        variete_info = culture_info.get('varietes_cultures_cepages', [{}])[0]
        
        uuid_parcelle = parcel_data.get('uuid_parcelle')
        
        # Check if parcelle exists
        result = conn.execute(text(
            "SELECT id FROM parcelles WHERE uuid_parcelle = :uuid"
        ), {"uuid": uuid_parcelle})
        
        if not result.fetchone():
            # Create parcelle
            try:
                conn.execute(text("""
                    INSERT INTO parcelles (
                        siret, uuid_parcelle, millesime, nom, commune_insee,
                        surface_ha, surface_mesuree_ha, id_culture, culture_code,
                        variete, id_variete, geometrie_vide
                    ) VALUES (
                        :siret, :uuid_parcelle, :millesime, :nom, :commune_insee,
                        :surface_ha, :surface_mesuree_ha, :id_culture, :culture_code,
                        :variete, :id_variete, :geometrie_vide
                    )
                """), {
                    "siret": siret,
                    "uuid_parcelle": uuid_parcelle,
                    "millesime": parcel_data.get('millesime', 2024),
                    "nom": parcel_data.get('nom'),
                    "commune_insee": parcel_data.get('insee_commune'),
                    "surface_ha": float(parcel_data.get('surface_mesuree_ha', 0)),
                    "surface_mesuree_ha": float(parcel_data.get('surface_mesuree_ha', 0)),
                    "id_culture": culture_info.get('id_culture'),
                    "culture_code": culture_info.get('libelle', '').upper()[:10] if culture_info.get('libelle') else None,
                    "variete": variete_info.get('libelle'),
                    "id_variete": variete_info.get('id_variete'),
                    "geometrie_vide": parcel_data.get('geometrie_vide', False)
                })
                stats['parcelles'] += 1
                print(f'✅ Created parcelle: {parcel_data.get("nom")} ({parcel_data.get("surface_mesuree_ha")} ha)')
            except Exception as e:
                print(f'❌ Error creating parcelle: {e}')
                raise
    
    # Process interventions
    for intervention_data in interventions_data:
        uuid_parcelle = intervention_data.get('uuid_parcelle')
        uuid_intervention = intervention_data.get('uuid_intervention')
        
        # Check if intervention exists
        result = conn.execute(text(
            "SELECT id FROM interventions WHERE uuid_intervention = :uuid"
        ), {"uuid": uuid_intervention})
        
        if result.fetchone():
            continue
        
        # Find parcelle
        result = conn.execute(text(
            "SELECT id, siret FROM parcelles WHERE uuid_parcelle = :uuid"
        ), {"uuid": uuid_parcelle})
        
        parcelle = result.fetchone()
        if not parcelle:
            print(f'⚠️  Parcelle not found for intervention {uuid_intervention}')
            continue
        
        parcelle_id, siret = parcelle
        
        # Parse date
        date_str = intervention_data.get('date_debut')
        intervention_date = date.fromisoformat(date_str) if date_str else date.today()
        
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
        conn.execute(text("""
            INSERT INTO interventions (
                parcelle_id, siret, uuid_intervention, type_intervention,
                id_type_intervention, date_intervention, date_debut,
                surface_travaillee_ha, id_culture, materiel_utilise, intrants
            ) VALUES (
                :parcelle_id, :siret, :uuid_intervention, :type_intervention,
                :id_type_intervention, :date_intervention, :date_debut,
                :surface_travaillee_ha, :id_culture, :materiel_utilise, :intrants::jsonb
            )
        """), {
            "parcelle_id": parcelle_id,
            "siret": siret,
            "uuid_intervention": uuid_intervention,
            "type_intervention": type_intervention,
            "id_type_intervention": id_type,
            "date_intervention": intervention_date,
            "date_debut": intervention_date,
            "surface_travaillee_ha": float(intervention_data.get('surface_travaillee_ha', 0)),
            "id_culture": intervention_data.get('id_culture'),
            "materiel_utilise": intervention_data.get('materiel_utilise'),
            "intrants": json.dumps(intervention_data.get('intrants', []))
        })
        stats['interventions'] += 1
        print(f'✅ Created intervention: {type_intervention} on {intervention_date}')
        
        # Process intrants
        for intrant_data in intervention_data.get('intrants', []):
            id_intrant = intrant_data.get('id_intrant')
            
            # Check if intrant exists
            result = conn.execute(text(
                "SELECT id FROM intrants WHERE id_intrant = :id"
            ), {"id": id_intrant})
            
            if not result.fetchone():
                conn.execute(text("""
                    INSERT INTO intrants (
                        id_intrant, libelle, type_intrant, id_type_intrant, code_amm
                    ) VALUES (
                        :id_intrant, :libelle, :type_intrant, :id_type_intrant, :code_amm
                    )
                """), {
                    "id_intrant": id_intrant,
                    "libelle": intrant_data.get('libelle'),
                    "type_intrant": intrant_data.get('type_intrant'),
                    "id_type_intrant": intrant_data.get('id_type_intrant'),
                    "code_amm": intrant_data.get('code_amm')
                })
                stats['intrants'] += 1
    
    conn.commit()
    
    print('\n' + '=' * 60)
    print('✅ MesParcelles data imported successfully!')
    print('=' * 60)
    print(f'Exploitations: {stats["exploitations"]}')
    print(f'Parcelles: {stats["parcelles"]}')
    print(f'Interventions: {stats["interventions"]}')
    print(f'Intrants: {stats["intrants"]}')
    print('\n🎉 Data is ready for use!')

print('\n✅ Import complete!')

