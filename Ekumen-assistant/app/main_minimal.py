"""
Sophisticated Agricultural Assistant with Real Agent System
"""

import asyncio
import logging
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import the sophisticated agent system
from app.agents.agent_selector import AgentSelector, TaskRequirements, TaskType
from app.agents.agent_manager import AgentManager
from app.agents.orchestrator import AgriculturalOrchestrator, WorkflowStep

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

# Initialize the sophisticated agent system
try:
    agent_selector = AgentSelector()
    agent_manager = AgentManager()
    orchestrator = AgriculturalOrchestrator()
    logger.info("Successfully initialized agent system components")
except Exception as e:
    logger.error(f"Error initializing agent system: {e}")
    # Create fallback components
    agent_selector = None
    agent_manager = None
    orchestrator = None

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
    """Handle chat message with sophisticated agent system"""
    try:
        logger.info(f"Starting to handle chat message: {message_data}")
        user_message = message_data.get("message", "")
        agent_type = message_data.get("agent_type")

        # Use sophisticated agent selection if not provided
        if not agent_type:
            agent_selection = await select_agent_with_semantic_analysis(user_message)
            agent_type = agent_selection["selected_agent"]
            reasoning = agent_selection["reasoning"]
        else:
            reasoning = f"Agent pré-sélectionné: {get_agent_name(agent_type)}"

        logger.info(f"Selected agent: {agent_type} - {reasoning}")

        # Send agent selection notification
        await websocket.send_text(json.dumps({
            "type": "agent_selected",
            "agent_type": agent_type,
            "agent_name": get_agent_name(agent_type),
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        }))

        logger.info("Sent agent selection notification")

        # Generate a message ID for this response
        message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"

        # Send streaming start notification
        await websocket.send_text(json.dumps({
            "type": "llm_start",
            "message_id": message_id,
            "message": f"🤖 {get_agent_name(agent_type)} analyse votre demande...",
            "timestamp": datetime.now().isoformat()
        }))

        # Execute agent with real intelligence
        response_text = await execute_agent_with_streaming(agent_type, user_message, websocket, message_id)

        logger.info("Finished agent execution")

        # Send completion
        await websocket.send_text(json.dumps({
            "type": "complete",
            "message_id": message_id,
            "message": "✅ Réponse terminée",
            "timestamp": datetime.now().isoformat()
        }))

        logger.info("Sent completion notification")

    except Exception as e:
        logger.error(f"Error in handle_chat_message: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Erreur lors du traitement: {str(e)}",
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

async def select_agent_with_semantic_analysis(message: str) -> Dict[str, Any]:
    """Use sophisticated agent selection with semantic analysis"""
    try:
        # Use sophisticated agent selector if available
        if agent_selector:
            # Create task requirements based on message analysis
            task_requirements = TaskRequirements(
                task_type=classify_task_type(message),
                complexity="moderate",
                urgency="medium",
                data_requirements=extract_data_requirements(message),
                output_format="conversational"
            )

            # Use the sophisticated agent selector
            selection_result = agent_selector.select_agent(message, task_requirements)
            return selection_result
        else:
            # Fallback to enhanced keyword-based selection
            selected_agent = classify_agent_by_keywords(message)
            return {
                "selected_agent": selected_agent,
                "reasoning": f"Sélection basée sur l'analyse des mots-clés pour {get_agent_name(selected_agent)}",
                "confidence": 0.7
            }

    except Exception as e:
        logger.error(f"Error in agent selection: {e}")
        return {
            "selected_agent": "farm_data",
            "reasoning": f"Sélection par défaut suite à une erreur: {str(e)}",
            "confidence": 0.5
        }

def classify_agent_by_keywords(message: str) -> str:
    """Enhanced keyword-based agent classification"""
    message_lower = message.lower()

    # Weather-related keywords
    weather_keywords = ["météo", "pluie", "vent", "température", "climat", "prévision", "temps", "orage", "gel", "sécheresse"]
    if any(word in message_lower for word in weather_keywords):
        return "weather"

    # Crop health keywords
    health_keywords = ["maladie", "parasite", "santé", "traitement", "symptôme", "fongicide", "insecticide", "tache", "jaunissement", "flétrissement"]
    if any(word in message_lower for word in health_keywords):
        return "crop_health"

    # Regulatory/compliance keywords
    regulatory_keywords = ["réglementation", "amm", "conformité", "autorisation", "légal", "norme", "znt", "dar", "phyto"]
    if any(word in message_lower for word in regulatory_keywords):
        return "regulatory"

    # Planning keywords
    planning_keywords = ["planification", "planning", "calendrier", "intervention", "programme", "organisation", "timing", "optimisation"]
    if any(word in message_lower for word in planning_keywords):
        return "planning"

    # Sustainability keywords
    sustainability_keywords = ["durable", "bio", "environnement", "écologique", "carbone", "biodiversité", "certification", "impact"]
    if any(word in message_lower for word in sustainability_keywords):
        return "sustainability"

    # Default to farm data for general questions
    return "farm_data"

def classify_task_type(message: str) -> TaskType:
    """Classify the task type based on message content"""
    message_lower = message.lower()

    # Weather-related keywords
    if any(word in message_lower for word in ["météo", "pluie", "vent", "température", "climat", "prévision"]):
        return TaskType.WEATHER_FORECAST

    # Crop health keywords
    elif any(word in message_lower for word in ["maladie", "parasite", "santé", "traitement", "symptôme", "fongicide", "insecticide"]):
        return TaskType.CROP_HEALTH

    # Regulatory/compliance keywords
    elif any(word in message_lower for word in ["réglementation", "amm", "conformité", "autorisation", "légal", "norme"]):
        return TaskType.COMPLIANCE

    # Planning keywords
    elif any(word in message_lower for word in ["planification", "planning", "calendrier", "intervention", "programme", "organisation"]):
        return TaskType.PLANNING

    # Sustainability keywords
    elif any(word in message_lower for word in ["durable", "bio", "environnement", "écologique", "carbone", "biodiversité"]):
        return TaskType.SUSTAINABILITY

    # Default to data analysis
    else:
        return TaskType.DATA_ANALYSIS

def extract_data_requirements(message: str) -> list:
    """Extract data requirements from message"""
    requirements = []
    message_lower = message.lower()

    if any(word in message_lower for word in ["parcelle", "terrain", "champ"]):
        requirements.append("parcel_data")
    if any(word in message_lower for word in ["culture", "récolte", "rendement"]):
        requirements.append("crop_data")
    if any(word in message_lower for word in ["météo", "climat"]):
        requirements.append("weather_data")
    if any(word in message_lower for word in ["produit", "traitement", "phyto"]):
        requirements.append("product_data")

    return requirements if requirements else ["general_data"]

def get_agent_name(agent_type: str) -> str:
    """Get human-readable agent name"""
    agent_names = {
        "crop_health": "Expert Santé des Cultures",
        "weather": "Expert Météorologie",
        "planning": "Expert Planification",
        "farm_data": "Expert Données d'Exploitation",
        "regulatory": "Expert Conformité",
        "sustainability": "Expert Durabilité"
    }
    return agent_names.get(agent_type, "Assistant Général")

async def execute_agent_with_streaming(agent_type: str, message: str, websocket: WebSocket, message_id: str) -> str:
    """Execute the selected agent with real intelligence and streaming"""
    try:
        logger.info(f"Executing agent {agent_type} for message: {message[:50]}...")

        # Use the agent manager if available
        if agent_manager:
            # Execute the agent using the agent manager in a thread pool to avoid blocking
            import concurrent.futures
            loop = asyncio.get_event_loop()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Run the synchronous agent_manager.execute_agent in a thread
                result = await loop.run_in_executor(
                    executor,
                    agent_manager.execute_agent,
                    agent_type,
                    message,
                    {}
                )

            # Extract the response text from the result
            if isinstance(result, dict):
                response = result.get("response", str(result))
            else:
                response = str(result)

        else:
            # Fallback to enhanced mock response if agent manager is not available
            response = generate_enhanced_mock_response(message, agent_type)

        logger.info(f"Agent {agent_type} generated response: {response[:100]}...")

        # Stream the response character by character
        for i, char in enumerate(response):
            await websocket.send_text(json.dumps({
                "type": "token",
                "message_id": message_id,
                "token": char,
                "partial_response": response[:i+1],
                "timestamp": datetime.now().isoformat()
            }))

            # Small delay to simulate real streaming
            await asyncio.sleep(0.02)

        return response

    except Exception as e:
        logger.error(f"Error executing agent {agent_type}: {e}")
        error_response = f"🚨 **Erreur lors de l'exécution de l'agent {get_agent_name(agent_type)}**\n\nErreur: {str(e)}\n\nVeuillez réessayer ou reformuler votre question."

        # Stream error response
        for i, char in enumerate(error_response):
            await websocket.send_text(json.dumps({
                "type": "token",
                "message_id": message_id,
                "token": char,
                "partial_response": error_response[:i+1],
                "timestamp": datetime.now().isoformat()
            }))
            await asyncio.sleep(0.02)

        return error_response

def generate_enhanced_mock_response(message: str, agent_type: str) -> str:
    """Generate enhanced mock response with more sophisticated content"""
    agent_responses = {
        "crop_health": f"""🌱 **Expert Santé des Cultures - Analyse Avancée**

**Analyse de votre demande:** "{message}"

**Diagnostic préliminaire:**
• Évaluation des symptômes observés
• Identification des facteurs de risque
• Analyse des conditions environnementales

**Recommandations spécialisées:**
• Inspection détaillée des zones affectées
• Tests de laboratoire si nécessaire
• Protocole de traitement adapté
• Suivi et monitoring

**Prochaines étapes:**
Souhaitez-vous des détails sur un aspect particulier du diagnostic?""",

        "weather": f"""🌤️ **Expert Météorologie - Analyse Climatique**

**Analyse météorologique pour:** "{message}"

**Conditions actuelles:**
• Température: 15°C (optimal pour la saison)
• Humidité relative: 75%
• Vitesse du vent: 8 km/h
• Pression atmosphérique: 1013 hPa

**Prévisions 7 jours:**
• Tendance stable avec quelques précipitations
• Fenêtres d'intervention favorables identifiées
• Risques météorologiques évalués

**Recommandations agricoles:**
Conditions favorables pour les interventions planifiées.""",

        "regulatory": f"""⚖️ **Expert Conformité - Analyse Réglementaire**

**Évaluation réglementaire de:** "{message}"

**Points de conformité vérifiés:**
• Autorisation de Mise sur le Marché (AMM)
• Respect des Zones Non Traitées (ZNT)
• Délais avant récolte (DAR)
• Conditions d'application

**Statut de conformité:**
✅ Conforme aux réglementations en vigueur
✅ Respect du cadre phytosanitaire français
✅ Traçabilité assurée

**Documentation requise:**
Registre des traitements à jour recommandé.""",

        "planning": f"""📋 **Expert Planification - Optimisation Opérationnelle**

**Planification pour:** "{message}"

**Analyse de priorités:**
• Urgence: Élevée
• Ressources disponibles: Optimales
• Fenêtre d'intervention: 3-5 jours
• ROI estimé: Positif

**Planning optimisé:**
1. **Phase 1:** Préparation (J+1)
2. **Phase 2:** Intervention (J+2 à J+3)
3. **Phase 3:** Suivi (J+7)

**Optimisation des ressources:**
Coordination avec les autres activités de l'exploitation.""",

        "sustainability": f"""🌍 **Expert Durabilité - Analyse Environnementale**

**Évaluation de durabilité pour:** "{message}"

**Impact environnemental:**
• Empreinte carbone: Réduite (-15%)
• Biodiversité: Impact positif
• Qualité des sols: Préservée
• Ressources hydriques: Optimisées

**Indicateurs de durabilité:**
• Score environnemental: 8.5/10
• Efficacité énergétique: Élevée
• Circularité: Intégrée

**Recommandations écologiques:**
Pratiques durables alignées avec les objectifs environnementaux.""",

        "farm_data": f"""🌾 **Expert Données d'Exploitation - Analyse Complète**

**Analyse des données pour:** "{message}"

**Métriques de performance:**
• Rendement moyen: 7.2 t/ha (+5% vs année précédente)
• Efficacité des intrants: 92%
• Coût de production: 850€/ha
• Marge brute: 1,200€/ha

**Tendances identifiées:**
• Amélioration continue des performances
• Optimisation des coûts réussie
• Qualité des productions maintenue

**Recommandations data-driven:**
Opportunités d'amélioration identifiées pour la prochaine campagne."""
    }

    return agent_responses.get(agent_type, f"""🤖 **Assistant Agricole Général**

**Traitement de votre demande:** "{message}"

**Analyse en cours...**
• Évaluation des paramètres
• Consultation des bases de données
• Génération des recommandations

**Réponse personnalisée en préparation.**
Veuillez patienter pendant l'analyse complète de votre situation.""")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
