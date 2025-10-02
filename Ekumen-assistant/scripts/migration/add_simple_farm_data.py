#!/usr/bin/env python3
"""
Add simple farm data based on the MesParcelles table provided
"""

import sys
from pathlib import Path
from datetime import date
from decimal import Decimal
import uuid as uuid_lib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.models import Exploitation, Parcelle, Intervention
from sqlalchemy import select


def add_farm_data():
    """Add farm data from the provided table."""
    db = SessionLocal()
    
    try:
        print("🚀 Adding farm data from MesParcelles table...")
        
        # Check if data already exists
        existing = db.execute(select(Exploitation)).scalars().first()
        if existing:
            print("⚠️  Data already exists.")
            return
        
        # Create exploitation
        exploitation = Exploitation(
            siret="93429231900019",
            nom="Ferme Tuferes",
            commune_insee="75120",
            surface_totale_ha=Decimal("228.54")
        )
        db.add(exploitation)
        db.flush()
        print(f"✅ Created exploitation: {exploitation.nom}")
        
        # Create parcelle Tuferes
        parcelle_uuid = uuid_lib.UUID("60dff7b9-3183-412b-b7a2-dd6d895f181c")
        parcelle = Parcelle(
            siret=exploitation.siret,
            uuid_parcelle=parcelle_uuid,
            millesime=2024,
            nom="Tuferes",
            commune_insee="75120",
            surface_ha=Decimal("228.54"),
            surface_mesuree_ha=Decimal("228.54"),
            culture_code="BLE",
            id_culture=1438,
            variete="Blé Hiver",
            id_variete=11438
        )
        db.add(parcelle)
        db.flush()
        print(f"✅ Created parcelle: {parcelle.nom}")
        
        # Create interventions from the table
        interventions_data = [
            {
                "uuid": "837b375b-5836-463f-b912-6feeed9ad193",
                "date": date(2024, 9, 8),
                "type": "traitement_phytosanitaire",
                "surface": Decimal("182.83"),
                "produit": "Saracen Delta",
                "quantite": "18.283 L",
                "materiel": "Tracteur John Deere 7055E"
            },
            {
                "uuid": "b3ecd2e5-f734-4f95-bce3-06fb84fd5189",
                "date": date(2024, 8, 25),
                "type": "traitement_phytosanitaire",
                "surface": Decimal("228.54"),
                "produit": "Codix",
                "quantite": "457.08 L",
                "materiel": "Tracteur John Deere"
            },
            {
                "uuid": "7aea91b8-e415-477c-b4d5-4c7c55339eaf",
                "date": date(2024, 9, 8),
                "type": "traitement_phytosanitaire",
                "surface": Decimal("182.83"),
                "produit": "Saracène Delta",
                "quantite": "155.4055 L",
                "materiel": "Tracteur John Deere 6575"
            },
            {
                "uuid": "65889c18-8df3-45a0-8cf2-975037537dcb",
                "date": date(2024, 9, 11),
                "type": "fertilisation",
                "surface": Decimal("182.832"),
                "produit": "FEEDSER",
                "quantite": "182.832 L",
                "materiel": "Tractor John Deere 7525 E"
            }
        ]
        
        for i_data in interventions_data:
            intervention = Intervention(
                parcelle_id=parcelle.id,
                siret=exploitation.siret,
                uuid_intervention=uuid_lib.UUID(i_data["uuid"]),
                type_intervention=i_data["type"],
                date_intervention=i_data["date"],
                date_debut=i_data["date"],
                date_fin=i_data["date"],
                surface_travaillee_ha=i_data["surface"],
                produit_utilise=i_data["produit"],
                dose_ha=i_data["quantite"],
                materiel_utilise=i_data["materiel"]
            )
            db.add(intervention)
            print(f"✅ Created intervention: {i_data['type']} on {i_data['date']}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ Farm data added successfully!")
        print("=" * 60)
        print(f"Exploitation: {exploitation.nom} (SIRET: {exploitation.siret})")
        print(f"Parcelle: {parcelle.nom} ({parcelle.surface_ha} ha)")
        print(f"Culture: {parcelle.culture_code} - {parcelle.variete}")
        print(f"Interventions: {len(interventions_data)}")
        print("\n🎉 You can now query your farm data!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_farm_data()

