#!/usr/bin/env python3
"""
Add test farm data to the current agri database schema
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.models.agri_models import Exploitation, Parcelle, Intervention
from sqlalchemy import select


def create_test_data():
    """Create test farm data."""
    db = SessionLocal()
    
    try:
        print("🚀 Creating test farm data...")
        
        # Check if data already exists
        existing = db.execute(select(Exploitation)).scalars().first()
        if existing:
            print("⚠️  Data already exists. Skipping creation.")
            return
        
        # Create test exploitation
        exploitation = Exploitation(
            siret="93429231900019",
            nom="Ferme Bio de Normandie",
            region_code="28",  # Normandie
            department_code="76",  # Seine-Maritime
            commune_insee="76540",  # Rouen
            surface_totale_ha=228.54,
            type_exploitation="grandes_cultures",
            bio=True,
            certification_bio="AB",
            date_certification_bio=date(2020, 1, 1)
        )
        db.add(exploitation)
        db.flush()
        
        print(f"✅ Created exploitation: {exploitation.nom} (SIRET: {exploitation.siret})")
        
        # Create test parcelles
        parcelles_data = [
            {
                "nom": "Tuferes",
                "numero_ilot": "001",
                "numero_parcelle": "A",
                "surface_ha": 228.54,
                "culture_code": "BLE",
                "variete": "Blé tendre d'hiver",
                "date_semis": date(2024, 10, 15),
                "bbch_stage": 13,  # 3 leaves unfolded
                "commune_insee": "76540"
            },
            {
                "nom": "Les Champs du Nord",
                "numero_ilot": "002",
                "numero_parcelle": "B",
                "surface_ha": 45.2,
                "culture_code": "MAI",
                "variete": "Maïs grain",
                "date_semis": date(2024, 4, 20),
                "bbch_stage": 85,  # Soft dough
                "commune_insee": "76540"
            },
            {
                "nom": "Prairie Sud",
                "numero_ilot": "003",
                "numero_parcelle": "C",
                "surface_ha": 12.8,
                "culture_code": "PTR",
                "variete": "Prairie temporaire",
                "date_semis": date(2023, 3, 1),
                "bbch_stage": 30,  # Beginning of stem elongation
                "commune_insee": "76540"
            }
        ]
        
        for p_data in parcelles_data:
            parcelle = Parcelle(
                siret=exploitation.siret,
                millesime=2024,
                **p_data
            )
            db.add(parcelle)
            print(f"✅ Created parcelle: {parcelle.nom} ({parcelle.surface_ha} ha, {parcelle.culture_code})")
        
        db.flush()
        
        # Create some test interventions
        parcelles = db.execute(select(Parcelle).where(Parcelle.siret == exploitation.siret)).scalars().all()
        
        for parcelle in parcelles:
            if parcelle.culture_code == "BLE":
                # Wheat interventions
                interventions_data = [
                    {
                        "type_intervention": "semis",
                        "date_intervention": date(2024, 10, 15),
                        "description": "Semis blé tendre d'hiver",
                        "surface_ha": parcelle.surface_ha
                    },
                    {
                        "type_intervention": "fertilisation",
                        "date_intervention": date(2024, 11, 5),
                        "description": "Apport azote de fond",
                        "surface_ha": parcelle.surface_ha,
                        "produit_utilise": "Ammonitrate 33.5%",
                        "dose_ha": "150 kg/ha"
                    }
                ]
            elif parcelle.culture_code == "MAI":
                # Corn interventions
                interventions_data = [
                    {
                        "type_intervention": "semis",
                        "date_intervention": date(2024, 4, 20),
                        "description": "Semis maïs grain",
                        "surface_ha": parcelle.surface_ha
                    },
                    {
                        "type_intervention": "traitement",
                        "date_intervention": date(2024, 5, 15),
                        "description": "Désherbage post-levée",
                        "surface_ha": parcelle.surface_ha,
                        "produit_utilise": "Herbicide maïs",
                        "dose_ha": "2 L/ha"
                    }
                ]
            else:
                interventions_data = []
            
            for i_data in interventions_data:
                intervention = Intervention(
                    parcelle_id=parcelle.id,
                    siret=exploitation.siret,
                    **i_data
                )
                db.add(intervention)
                print(f"✅ Created intervention: {intervention.type_intervention} on {intervention.date_intervention}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ Test farm data created successfully!")
        print("=" * 60)
        print(f"Exploitation: {exploitation.nom}")
        print(f"SIRET: {exploitation.siret}")
        print(f"Parcelles: {len(parcelles_data)}")
        print(f"Total surface: {exploitation.surface_totale_ha} ha")
        print("\n🎉 You can now test the agricultural tools!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()

