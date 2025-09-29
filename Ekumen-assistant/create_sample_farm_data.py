#!/usr/bin/env python3
"""
Create sample farm operations data to demonstrate the complete MesParcelles + EPHY integration
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


class SampleFarmDataCreator:
    """Create realistic sample farm operations data."""
    
    def __init__(self):
        self.stats = {
            "exploitations": 0,
            "parcelles": 0,
            "interventions": 0,
            "intervention_intrants": 0,
            "errors": []
        }
    
    async def create_sample_exploitations(self):
        """Create sample farm exploitations."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Sample exploitations with realistic SIRET numbers
                    exploitations_data = [
                        ("80240331100029", 1, "Ferme Bio de Normandie"),
                        ("85123456789012", 2, "EARL des Champs Verts"),
                        ("77987654321098", 3, "GAEC du Soleil Levant"),
                        ("91234567890123", 4, "Exploitation Dupont"),
                        ("69876543210987", 5, "Domaine des Trois Chênes")
                    ]
                    
                    for siret, id_region, nom in exploitations_data:
                        await session.execute(text("""
                            INSERT INTO farm_operations.exploitations (siret, id_region, nom) 
                            VALUES (:siret, :id_region, :nom) 
                            ON CONFLICT (siret) DO NOTHING
                        """), {"siret": siret, "id_region": id_region, "nom": nom})
                    
                    self.stats["exploitations"] = len(exploitations_data)
                    print(f"✅ Created {len(exploitations_data)} sample exploitations")
                    
        except Exception as e:
            print(f"❌ Error creating exploitations: {e}")
            self.stats["errors"].append(f"Exploitations: {e}")
    
    async def create_sample_parcelles(self):
        """Create sample parcelles for each exploitation."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Get exploitations
                    result = await session.execute(text("SELECT siret FROM farm_operations.exploitations"))
                    sirets = [row[0] for row in result.fetchall()]
                    
                    parcelle_count = 0
                    for siret in sirets:
                        # Create 2-4 parcelles per exploitation
                        num_parcelles = random.randint(2, 4)
                        
                        for i in range(num_parcelles):
                            uuid_parcelle = str(uuid.uuid4())
                            nom_parcelle = f"Parcelle {chr(65 + i)}"  # A, B, C, D
                            surface = round(random.uniform(2.5, 15.8), 2)  # 2.5 to 15.8 hectares
                            insee_commune = f"7{random.randint(1000, 9999)}"  # Random INSEE code
                            
                            await session.execute(text("""
                                INSERT INTO farm_operations.parcelles 
                                (uuid_parcelle, siret_exploitation, millesime, nom, surface_mesuree_ha, insee_commune) 
                                VALUES (:uuid_parcelle, :siret, :millesime, :nom, :surface, :insee)
                            """), {
                                "uuid_parcelle": uuid_parcelle,
                                "siret": siret,
                                "millesime": 2024,
                                "nom": nom_parcelle,
                                "surface": surface,
                                "insee": insee_commune
                            })
                            parcelle_count += 1
                    
                    self.stats["parcelles"] = parcelle_count
                    print(f"✅ Created {parcelle_count} sample parcelles")
                    
        except Exception as e:
            print(f"❌ Error creating parcelles: {e}")
            self.stats["errors"].append(f"Parcelles: {e}")
    
    async def create_sample_interventions(self):
        """Create sample interventions with realistic agricultural operations."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Get parcelles
                    result = await session.execute(text("""
                        SELECT uuid_parcelle, siret_exploitation, surface_mesuree_ha 
                        FROM farm_operations.parcelles
                    """))
                    parcelles = result.fetchall()
                    
                    intervention_count = 0
                    
                    for uuid_parcelle, siret, surface in parcelles:
                        # Create 3-6 interventions per parcelle for 2024 season
                        num_interventions = random.randint(3, 6)
                        
                        # Define realistic intervention sequence
                        intervention_sequence = [
                            (1, 1, "2024-03-15", "2024-03-15"),  # Semis, Blé tendre
                            (3, None, "2024-04-10", "2024-04-10"),  # Fertilisation
                            (2, None, "2024-05-20", "2024-05-20"),  # Traitement phytosanitaire
                            (2, None, "2024-06-15", "2024-06-15"),  # Traitement phytosanitaire
                            (3, None, "2024-07-01", "2024-07-01"),  # Fertilisation
                            (4, None, "2024-08-15", "2024-08-20"),  # Récolte
                        ]
                        
                        for i in range(min(num_interventions, len(intervention_sequence))):
                            uuid_intervention = str(uuid.uuid4())
                            id_type_intervention, id_culture, date_debut, date_fin = intervention_sequence[i]
                            
                            # Add some randomness to dates
                            base_date = datetime.strptime(date_debut, "%Y-%m-%d").date()
                            random_days = random.randint(-5, 5)
                            actual_date = base_date + timedelta(days=random_days)
                            
                            # Surface worked is usually the full parcel or a portion
                            surface_travaillee = round(float(surface) * random.uniform(0.8, 1.0), 2)
                            
                            await session.execute(text("""
                                INSERT INTO farm_operations.interventions 
                                (uuid_intervention, siret_exploitation, uuid_parcelle, id_culture, 
                                 id_type_intervention, surface_travaillee_ha, date_debut, date_fin) 
                                VALUES (:uuid_intervention, :siret, :uuid_parcelle, :id_culture, 
                                        :id_type_intervention, :surface_travaillee, :date_debut, :date_fin)
                            """), {
                                "uuid_intervention": uuid_intervention,
                                "siret": siret,
                                "uuid_parcelle": uuid_parcelle,
                                "id_culture": id_culture,
                                "id_type_intervention": id_type_intervention,
                                "surface_travaillee": surface_travaillee,
                                "date_debut": actual_date,
                                "date_fin": actual_date if date_debut == date_fin else actual_date + timedelta(days=1)
                            })
                            intervention_count += 1
                    
                    self.stats["interventions"] = intervention_count
                    print(f"✅ Created {intervention_count} sample interventions")
                    
        except Exception as e:
            print(f"❌ Error creating interventions: {e}")
            self.stats["errors"].append(f"Interventions: {e}")
    
    async def create_sample_intervention_intrants(self):
        """Create sample intervention intrants using real EPHY-linked products."""
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Get interventions that need intrants (fertilization and phyto treatments)
                    result = await session.execute(text("""
                        SELECT i.uuid_intervention, i.id_type_intervention, i.surface_travaillee_ha
                        FROM farm_operations.interventions i
                        WHERE i.id_type_intervention IN (2, 3)  -- Phyto treatments and fertilization
                    """))
                    interventions = result.fetchall()
                    
                    # Get available intrants
                    result = await session.execute(text("""
                        SELECT id_intrant, libelle, id_type_intrant, code_amm
                        FROM reference.intrants
                        WHERE code_amm IS NOT NULL
                    """))
                    intrants = result.fetchall()
                    
                    intrant_usage_count = 0
                    
                    for uuid_intervention, id_type_intervention, surface_ha in interventions:
                        # Select appropriate intrants based on intervention type
                        if id_type_intervention == 2:  # Phyto treatment
                            # Use phytosanitary products
                            suitable_intrants = [i for i in intrants if i[2] in [1, 2, 3]]  # Herbicide, Fongicide, Insecticide
                        else:  # Fertilization
                            # Use fertilizers (but we only have phyto products in our sample)
                            # So we'll use some phyto products as examples
                            suitable_intrants = intrants[:3]  # Use first 3 as examples
                        
                        if suitable_intrants:
                            # Use 1-2 intrants per intervention
                            num_intrants = random.randint(1, min(2, len(suitable_intrants)))
                            selected_intrants = random.sample(suitable_intrants, num_intrants)
                            
                            for id_intrant, libelle, id_type_intrant, code_amm in selected_intrants:
                                # Calculate realistic quantities
                                if id_type_intervention == 2:  # Phyto
                                    quantite = round(float(surface_ha) * random.uniform(0.5, 2.0), 2)  # L/ha
                                    unite = "L"
                                    cible = random.choice(["Adventices", "Maladies fongiques", "Insectes", "Pucerons"])
                                else:  # Fertilization
                                    quantite = round(float(surface_ha) * random.uniform(50, 150), 1)  # kg/ha
                                    unite = "kg"
                                    cible = None
                                
                                await session.execute(text("""
                                    INSERT INTO farm_operations.intervention_intrants 
                                    (uuid_intervention, id_intrant, quantite_totale, unite_intrant_intervention, cible) 
                                    VALUES (:uuid_intervention, :id_intrant, :quantite, :unite, :cible)
                                """), {
                                    "uuid_intervention": uuid_intervention,
                                    "id_intrant": id_intrant,
                                    "quantite": quantite,
                                    "unite": unite,
                                    "cible": cible
                                })
                                intrant_usage_count += 1
                    
                    self.stats["intervention_intrants"] = intrant_usage_count
                    print(f"✅ Created {intrant_usage_count} intervention intrant usages")
                    
        except Exception as e:
            print(f"❌ Error creating intervention intrants: {e}")
            self.stats["errors"].append(f"Intervention intrants: {e}")
    
    async def test_integration_views(self):
        """Test the integration views with sample data."""
        try:
            async with AsyncSessionLocal() as session:
                print("\n🔍 Testing Integration Views:")
                print("=" * 40)
                
                # Test product usage with regulatory view
                result = await session.execute(text("""
                    SELECT 
                        exploitation_nom,
                        date_debut,
                        produit_utilise,
                        produit_ephy,
                        quantite_totale,
                        unite_intrant_intervention,
                        CASE 
                            WHEN mentions_autorisees LIKE '%jardins%' THEN 'Garden Authorized'
                            WHEN mentions_autorisees LIKE '%biologique%' THEN 'Organic Authorized'
                            ELSE 'Standard Use'
                        END as authorization_type
                    FROM farm_operations.product_usage_with_regulatory
                    ORDER BY date_debut DESC
                    LIMIT 5
                """))
                
                usage_data = result.fetchall()
                print("📊 Product Usage with Regulatory Context:")
                for row in usage_data:
                    print(f"   - {row[0]}: {row[2]} ({row[4]} {row[5]}) - {row[6]}")
                
                # Test compliance dashboard
                result = await session.execute(text("""
                    SELECT exploitation, total_interventions, garden_authorized, organic_authorized
                    FROM farm_operations.compliance_dashboard
                    WHERE total_interventions > 0
                """))
                
                compliance_data = result.fetchall()
                print("\n📈 Compliance Dashboard:")
                for row in compliance_data:
                    print(f"   - {row[0]}: {row[1]} interventions ({row[2]} garden, {row[3]} organic)")
                
                print("\n✅ Integration views working correctly!")
                
        except Exception as e:
            print(f"❌ Error testing integration views: {e}")
            self.stats["errors"].append(f"Integration test: {e}")
    
    async def run_creation(self):
        """Run the complete sample data creation."""
        print("🚀 Creating Sample Farm Operations Data")
        print("=" * 50)
        
        await self.create_sample_exploitations()
        await self.create_sample_parcelles()
        await self.create_sample_interventions()
        await self.create_sample_intervention_intrants()
        await self.test_integration_views()
        
        self.print_summary()
        
        return len(self.stats["errors"]) == 0
    
    def print_summary(self):
        """Print creation summary."""
        print("\n" + "=" * 60)
        print("📊 Sample Farm Data Creation Summary")
        print("=" * 60)
        print(f"✅ Exploitations: {self.stats['exploitations']}")
        print(f"✅ Parcelles: {self.stats['parcelles']}")
        print(f"✅ Interventions: {self.stats['interventions']}")
        print(f"✅ Intervention intrants: {self.stats['intervention_intrants']}")
        
        if self.stats["errors"]:
            print(f"⚠️ Errors: {len(self.stats['errors'])}")
            for error in self.stats["errors"]:
                print(f"   - {error}")
        else:
            print("✅ No errors!")
        
        print("\n🎉 Sample farm data creation complete!")
        print("\n🔗 Ready for semantic agricultural agents:")
        print("   - Real farm operations data")
        print("   - EPHY regulatory integration")
        print("   - Cross-domain compliance checking")
        print("   - Unified agricultural database")


async def main():
    """Main creation function."""
    creator = SampleFarmDataCreator()
    success = await creator.run_creation()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
