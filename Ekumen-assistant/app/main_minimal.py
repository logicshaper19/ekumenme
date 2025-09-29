"""
Minimal FastAPI application for testing frontend-backend connection.
"""

import logging
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Ekumen Agricultural Assistant - Minimal",
    description="Minimal version for testing frontend connection",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Ekumen Agricultural Assistant - Minimal",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.websocket("/api/v1/chat/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str, token: str = None):
    """
    Minimal WebSocket endpoint for testing frontend connection
    """
    connection_id = f"{conversation_id}_{int(time.time())}"
    
    try:
        # Accept the connection
        await websocket.accept()
        active_connections[connection_id] = websocket
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "🌾 Connecté à l'assistant agricole (mode test)",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        logger.info(f"WebSocket connected: {connection_id}")
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                logger.info(f"Received message: {message_data}")
                
                # Handle different message types
                if message_data.get("type") == "chat_message":
                    await handle_chat_message(websocket, message_data)
                elif message_data.get("type") == "voice_start":
                    await handle_voice_start(websocket)
                elif message_data.get("type") == "voice_stop":
                    await handle_voice_stop(websocket)
                elif message_data.get("type") == "voice_data":
                    await handle_voice_data(websocket, message_data)
                else:
                    logger.warning(f"Unknown message type: {message_data.get('type')}")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Erreur de traitement: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Clean up connection
        if connection_id in active_connections:
            del active_connections[connection_id]
        logger.info(f"WebSocket disconnected: {connection_id}")

async def handle_chat_message(websocket: WebSocket, message_data: dict):
    """Handle chat message with simulated agent response"""
    user_message = message_data.get("message", "")
    agent_type = message_data.get("agent_type")
    
    # Simulate agent selection
    if not agent_type:
        agent_type = select_agent_for_message(user_message)
    
    # Send agent selection notification
    await websocket.send_text(json.dumps({
        "type": "agent_selected",
        "agent_type": agent_type,
        "agent_name": get_agent_name(agent_type),
        "reasoning": f"Message analysé et routé vers {get_agent_name(agent_type)}",
        "timestamp": datetime.now().isoformat()
    }))
    
    # Simulate streaming response
    await websocket.send_text(json.dumps({
        "type": "llm_start",
        "message": f"🤖 {get_agent_name(agent_type)} analyse votre demande...",
        "timestamp": datetime.now().isoformat()
    }))
    
    # Simulate streaming tokens
    response_text = generate_mock_response(user_message, agent_type)
    
    for i, char in enumerate(response_text):
        await websocket.send_text(json.dumps({
            "type": "token",
            "token": char,
            "partial_response": response_text[:i+1],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Small delay to simulate real streaming
        import asyncio
        await asyncio.sleep(0.02)
    
    # Send completion
    await websocket.send_text(json.dumps({
        "type": "complete",
        "message": "✅ Réponse terminée",
        "timestamp": datetime.now().isoformat()
    }))

async def handle_voice_start(websocket: WebSocket):
    """Handle voice input start"""
    await websocket.send_text(json.dumps({
        "type": "voice_started",
        "message": "🎤 Écoute vocale activée",
        "timestamp": datetime.now().isoformat()
    }))

async def handle_voice_stop(websocket: WebSocket):
    """Handle voice input stop"""
    await websocket.send_text(json.dumps({
        "type": "voice_stopped",
        "message": "🎤 Écoute vocale arrêtée",
        "timestamp": datetime.now().isoformat()
    }))

async def handle_voice_data(websocket: WebSocket, message_data: dict):
    """Handle voice data (simulate transcription)"""
    # Simulate voice transcription
    await websocket.send_text(json.dumps({
        "type": "voice_transcript",
        "text": "Transcription simulée: Mon blé a des taches jaunes",
        "is_final": True,
        "timestamp": datetime.now().isoformat()
    }))

def select_agent_for_message(message: str) -> str:
    """Simple agent selection based on keywords"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["météo", "pluie", "vent", "température"]):
        return "weather"
    elif any(word in message_lower for word in ["maladie", "tache", "symptôme", "traitement"]):
        return "crop_health"
    elif any(word in message_lower for word in ["amm", "réglementation", "conformité"]):
        return "regulatory"
    elif any(word in message_lower for word in ["planification", "calendrier", "programme"]):
        return "planning"
    elif any(word in message_lower for word in ["durabilité", "environnement", "carbone"]):
        return "sustainability"
    else:
        return "farm_data"

def get_agent_name(agent_type: str) -> str:
    """Get agent display name"""
    agent_names = {
        "farm_data": "Données d'Exploitation",
        "weather": "Météorologie",
        "crop_health": "Santé des Cultures",
        "planning": "Planification",
        "regulatory": "Conformité",
        "sustainability": "Durabilité"
    }
    return agent_names.get(agent_type, "Assistant Général")

def generate_mock_response(message: str, agent_type: str) -> str:
    """Generate a mock response based on agent type"""
    agent_responses = {
        "crop_health": f"🌱 **Analyse de santé des cultures**\n\nConcernant votre question: \"{message}\"\n\nJe recommande:\n• Inspection visuelle détaillée\n• Identification précise des symptômes\n• Traitement adapté si nécessaire\n\nSouhaitez-vous plus de détails sur un aspect particulier?",
        "weather": f"🌤️ **Analyse météorologique**\n\nPour votre demande: \"{message}\"\n\nConditions actuelles:\n• Température: 15°C\n• Humidité: 75%\n• Vent: 8 km/h\n\nRecommandations pour vos interventions à venir.",
        "regulatory": f"⚖️ **Conformité réglementaire**\n\nAnalyse de: \"{message}\"\n\nPoints de conformité:\n• Vérification AMM\n• Respect des ZNT\n• Délais de sécurité\n\nTout semble conforme aux réglementations en vigueur.",
        "planning": f"📋 **Planification agricole**\n\nPour: \"{message}\"\n\nPlanification suggérée:\n• Priorité 1: Intervention immédiate\n• Priorité 2: Suivi dans 7 jours\n• Optimisation des ressources\n\nVoulez-vous détailler le planning?",
        "sustainability": f"🌍 **Analyse de durabilité**\n\nÉvaluation de: \"{message}\"\n\nImpact environnemental:\n• Empreinte carbone: Faible\n• Biodiversité: Impact positif\n• Ressources: Utilisation optimisée\n\nPratiques durables recommandées.",
        "farm_data": f"🌾 **Analyse des données d'exploitation**\n\nAnalyse de: \"{message}\"\n\nDonnées de performance:\n• Rendement: Dans la moyenne\n• Coûts: Optimisés\n• Efficacité: Bonne\n\nRecommandations pour améliorer les performances."
    }
    
    return agent_responses.get(agent_type, f"🤖 **Assistant Général**\n\nJe traite votre demande: \"{message}\"\n\nAnalyse en cours et recommandations à venir.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
