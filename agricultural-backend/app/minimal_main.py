from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel

app = FastAPI(
    title="Agricultural API - Minimal Version",
    description="Simple test version of the agricultural API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple data models for testing
class Exploitation(BaseModel):
    siret: str
    nom: str = ""
    created_at: datetime = datetime.now()

class Parcelle(BaseModel):
    uuid_parcelle: str
    siret_exploitation: str
    nom: str
    surface_ha: float
    millesime: int = 2024

class Intervention(BaseModel):
    uuid_intervention: str
    uuid_parcelle: str
    date_debut: str
    date_fin: str
    type_intervention: str
    surface_travaillee_ha: float

# In-memory storage for testing
exploitations_db = {}
parcelles_db = {}
interventions_db = {}

@app.get("/")
async def root():
    return {
        "message": "Agricultural API is running!",
        "version": "0.1.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "in-memory",
        "services": ["api"],
        "timestamp": datetime.now().isoformat()
    }

# Exploitations endpoints
@app.get("/api/v1/exploitations", response_model=List[Exploitation])
async def get_exploitations():
    """Get all exploitations"""
    return list(exploitations_db.values())

@app.post("/api/v1/exploitations", response_model=Exploitation)
async def create_exploitation(exploitation: Exploitation):
    """Create a new exploitation"""
    exploitations_db[exploitation.siret] = exploitation
    return exploitation

@app.get("/api/v1/exploitations/{siret}", response_model=Exploitation)
async def get_exploitation(siret: str):
    """Get exploitation by SIRET"""
    if siret not in exploitations_db:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Exploitation not found")
    return exploitations_db[siret]

# Parcelles endpoints
@app.get("/api/v1/parcelles", response_model=List[Parcelle])
async def get_parcelles(siret_exploitation: str = None):
    """Get parcelles, optionally filtered by SIRET"""
    parcelles = list(parcelles_db.values())
    if siret_exploitation:
        parcelles = [p for p in parcelles if p.siret_exploitation == siret_exploitation]
    return parcelles

@app.post("/api/v1/parcelles", response_model=Parcelle)
async def create_parcelle(parcelle: Parcelle):
    """Create a new parcelle"""
    parcelles_db[parcelle.uuid_parcelle] = parcelle
    return parcelle

@app.get("/api/v1/parcelles/{uuid_parcelle}", response_model=Parcelle)
async def get_parcelle(uuid_parcelle: str):
    """Get parcelle by UUID"""
    if uuid_parcelle not in parcelles_db:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Parcelle not found")
    return parcelles_db[uuid_parcelle]

# Interventions endpoints
@app.get("/api/v1/interventions", response_model=List[Intervention])
async def get_interventions(uuid_parcelle: str = None):
    """Get interventions, optionally filtered by parcelle"""
    interventions = list(interventions_db.values())
    if uuid_parcelle:
        interventions = [i for i in interventions if i.uuid_parcelle == uuid_parcelle]
    return interventions

@app.post("/api/v1/interventions", response_model=Intervention)
async def create_intervention(intervention: Intervention):
    """Create a new intervention"""
    interventions_db[intervention.uuid_intervention] = intervention
    return intervention

# Sample data endpoint
@app.post("/api/v1/seed-sample-data")
async def seed_sample_data():
    """Add some sample data for testing"""
    import uuid
    
    # Sample exploitation
    sample_exploitation = Exploitation(
        siret="80240331100029",
        nom="Exploitation de Test"
    )
    exploitations_db[sample_exploitation.siret] = sample_exploitation
    
    # Sample parcelle
    parcelle_uuid = str(uuid.uuid4())
    sample_parcelle = Parcelle(
        uuid_parcelle=parcelle_uuid,
        siret_exploitation="80240331100029",
        nom="Parcelle Test 1",
        surface_ha=5.5,
        millesime=2024
    )
    parcelles_db[parcelle_uuid] = sample_parcelle
    
    # Sample intervention
    intervention_uuid = str(uuid.uuid4())
    sample_intervention = Intervention(
        uuid_intervention=intervention_uuid,
        uuid_parcelle=parcelle_uuid,
        date_debut="2024-06-15",
        date_fin="2024-06-15",
        type_intervention="Traitement phytosanitaire",
        surface_travaillee_ha=5.5
    )
    interventions_db[intervention_uuid] = sample_intervention
    
    return {
        "message": "Sample data created successfully",
        "data": {
            "exploitations": 1,
            "parcelles": 1,
            "interventions": 1
        }
    }

# MesParcelles simulation endpoint
@app.post("/api/v1/sync/mesparcelles/{siret}")
async def simulate_mesparcelles_sync(siret: str, millesime: int = 2024):
    """Simulate MesParcelles API sync"""
    import uuid
    import random
    
    # Check if exploitation exists
    if siret not in exploitations_db:
        exploitations_db[siret] = Exploitation(siret=siret, nom=f"Exploitation {siret}")
    
    # Create some random parcelles
    parcelles_created = 0
    interventions_created = 0
    
    for i in range(random.randint(2, 5)):
        parcelle_uuid = str(uuid.uuid4())
        parcelle = Parcelle(
            uuid_parcelle=parcelle_uuid,
            siret_exploitation=siret,
            nom=f"Parcelle {i+1}",
            surface_ha=round(random.uniform(1.0, 10.0), 2),
            millesime=millesime
        )
        parcelles_db[parcelle_uuid] = parcelle
        parcelles_created += 1
        
        # Create interventions for this parcelle
        for j in range(random.randint(1, 3)):
            intervention_uuid = str(uuid.uuid4())
            intervention = Intervention(
                uuid_intervention=intervention_uuid,
                uuid_parcelle=parcelle_uuid,
                date_debut=f"2024-0{random.randint(4,8)}-{random.randint(10,28):02d}",
                date_fin=f"2024-0{random.randint(4,8)}-{random.randint(10,28):02d}",
                type_intervention=random.choice([
                    "Traitement phytosanitaire",
                    "Fertilisation",
                    "Semis",
                    "Récolte"
                ]),
                surface_travaillee_ha=parcelle.surface_ha
            )
            interventions_db[intervention_uuid] = intervention
            interventions_created += 1
    
    return {
        "message": f"Sync completed for {siret}",
        "parcelles_synced": parcelles_created,
        "interventions_synced": interventions_created,
        "millesime": millesime
    }

# Compliance checking simulation
@app.get("/api/v1/compliance/intervention/{intervention_id}")
async def check_intervention_compliance(intervention_id: str):
    """Simulate compliance checking"""
    if intervention_id not in interventions_db:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Intervention not found")
    
    intervention = interventions_db[intervention_id]
    
    # Simulate compliance check
    import random
    is_compliant = random.choice([True, True, True, False])  # 75% compliant
    
    issues = []
    if not is_compliant:
        issues = random.sample([
            "Dose maximale dépassée",
            "Produit non autorisé pour cette culture",
            "Délai avant récolte non respecté",
            "Zone de non-traitement non respectée"
        ], random.randint(1, 2))
    
    return {
        "intervention_id": intervention_id,
        "compliant": is_compliant,
        "issues": issues,
        "checks_performed": [
            "Autorisation produit",
            "Dose appliquée",
            "Période d'application",
            "Zones de protection"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/stats")
async def get_stats():
    """Get current database stats"""
    return {
        "exploitations_count": len(exploitations_db),
        "parcelles_count": len(parcelles_db),
        "interventions_count": len(interventions_db),
        "total_surface_ha": sum(p.surface_ha for p in parcelles_db.values()),
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "minimal_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
