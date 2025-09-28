#!/bin/bash

echo "🚀 Starting Minimal Agricultural API..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install fastapi uvicorn pydantic

# Start the server
echo "🌱 Starting FastAPI server..."
echo "📡 API will be available at: http://localhost:8000"
echo "📚 API docs will be available at: http://localhost:8000/docs"
echo "❤️  Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -c "
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel

app = FastAPI(
    title='Agricultural API - Minimal Version',
    description='Simple test version of the agricultural API',
    version='0.1.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class Exploitation(BaseModel):
    siret: str
    nom: str = ''
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

exploitations_db = {}
parcelles_db = {}
interventions_db = {}

@app.get('/')
async def root():
    return {
        'message': 'Agricultural API is running!',
        'version': '0.1.0',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'database': 'in-memory',
        'services': ['api'],
        'timestamp': datetime.now().isoformat()
    }

@app.get('/api/v1/exploitations', response_model=List[Exploitation])
async def get_exploitations():
    return list(exploitations_db.values())

@app.post('/api/v1/exploitations', response_model=Exploitation)
async def create_exploitation(exploitation: Exploitation):
    exploitations_db[exploitation.siret] = exploitation
    return exploitation

@app.get('/api/v1/exploitations/{siret}', response_model=Exploitation)
async def get_exploitation(siret: str):
    if siret not in exploitations_db:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Exploitation not found')
    return exploitations_db[siret]

@app.get('/api/v1/parcelles', response_model=List[Parcelle])
async def get_parcelles(siret_exploitation: str = None):
    parcelles = list(parcelles_db.values())
    if siret_exploitation:
        parcelles = [p for p in parcelles if p.siret_exploitation == siret_exploitation]
    return parcelles

@app.post('/api/v1/parcelles', response_model=Parcelle)
async def create_parcelle(parcelle: Parcelle):
    parcelles_db[parcelle.uuid_parcelle] = parcelle
    return parcelle

@app.get('/api/v1/interventions', response_model=List[Intervention])
async def get_interventions(uuid_parcelle: str = None):
    interventions = list(interventions_db.values())
    if uuid_parcelle:
        interventions = [i for i in interventions if i.uuid_parcelle == uuid_parcelle]
    return interventions

@app.post('/api/v1/interventions', response_model=Intervention)
async def create_intervention(intervention: Intervention):
    interventions_db[intervention.uuid_intervention] = intervention
    return intervention

@app.post('/api/v1/seed-sample-data')
async def seed_sample_data():
    import uuid
    
    sample_exploitation = Exploitation(
        siret='80240331100029',
        nom='Exploitation de Test'
    )
    exploitations_db[sample_exploitation.siret] = sample_exploitation
    
    parcelle_uuid = str(uuid.uuid4())
    sample_parcelle = Parcelle(
        uuid_parcelle=parcelle_uuid,
        siret_exploitation='80240331100029',
        nom='Parcelle Test 1',
        surface_ha=5.5,
        millesime=2024
    )
    parcelles_db[parcelle_uuid] = sample_parcelle
    
    intervention_uuid = str(uuid.uuid4())
    sample_intervention = Intervention(
        uuid_intervention=intervention_uuid,
        uuid_parcelle=parcelle_uuid,
        date_debut='2024-06-15',
        date_fin='2024-06-15',
        type_intervention='Traitement phytosanitaire',
        surface_travaillee_ha=5.5
    )
    interventions_db[intervention_uuid] = sample_intervention
    
    return {
        'message': 'Sample data created successfully',
        'data': {
            'exploitations': 1,
            'parcelles': 1,
            'interventions': 1
        }
    }

@app.get('/api/v1/stats')
async def get_stats():
    return {
        'exploitations_count': len(exploitations_db),
        'parcelles_count': len(parcelles_db),
        'interventions_count': len(interventions_db),
        'total_surface_ha': sum(p.surface_ha for p in parcelles_db.values()),
        'last_updated': datetime.now().isoformat()
    }

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
"
