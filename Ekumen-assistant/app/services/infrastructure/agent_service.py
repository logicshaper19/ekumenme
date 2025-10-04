"""
Agent service for agricultural chatbot
Handles AI agent orchestration and message processing
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.conversation import Conversation, AgentType
from app.models.user import User
from app.schemas.chat import ChatResponse


class AgentService:
    """Service for managing AI agents and message processing"""
    
    def __init__(self):
        self.agents = {
            AgentType.FARM_DATA: self._process_farm_data_message,
            AgentType.REGULATORY: self._process_regulatory_message,
            AgentType.WEATHER: self._process_weather_message,
            AgentType.CROP_HEALTH: self._process_crop_health_message,
            AgentType.PLANNING: self._process_planning_message,
            AgentType.SUSTAINABILITY: self._process_sustainability_message,
        }
    
    async def process_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        message: str,
        user: User
    ) -> ChatResponse:
        """Process a message with the appropriate agent"""
        agent_type = conversation.agent_type
        
        if agent_type not in self.agents:
            return ChatResponse(
                content="Désolé, je ne peux pas traiter ce type de demande pour le moment.",
                agent_type=agent_type,
                timestamp=datetime.utcnow(),
                metadata={"error": "Unknown agent type"}
            )
        
        try:
            # Process message with the appropriate agent
            response = await self.agents[agent_type](
                db=db,
                conversation=conversation,
                message=message,
                user=user
            )
            
            return response
            
        except Exception as e:
            return ChatResponse(
                content="Une erreur est survenue lors du traitement de votre demande. Veuillez réessayer.",
                agent_type=agent_type,
                timestamp=datetime.utcnow(),
                metadata={"error": str(e)}
            )
    
    async def _process_farm_data_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        message: str,
        user: User
    ) -> ChatResponse:
        """Process message with Farm Data Manager agent"""
        try:
            from app.agents.farm_data_agent import FarmDataIntelligenceAgent
            
            # Initialize farm data agent
            farm_agent = FarmDataIntelligenceAgent()
            
            # Prepare context with farm SIRET if available
            context = {}
            if conversation.farm_siret:
                context["farm_siret"] = conversation.farm_siret
                context["user_id"] = str(user.id)
            
            # Process message with farm data agent
            result = await farm_agent.aprocess(message, context)
            
            if result.get("success", True):
                response_content = result.get("response", "Désolé, je n'ai pas pu traiter votre demande.")
                
                return ChatResponse(
                    content=response_content,
                    agent_type=AgentType.FARM_DATA,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "agent_name": "Gestionnaire de Données d'Exploitation",
                        "capabilities": ["parcels", "interventions", "farm_profile", "regional_context"],
                        "iterations": result.get("iterations", 0),
                        "tools_used": result.get("tools_used", [])
                    }
                )
            else:
                # Handle error case
                error_message = result.get("error", "Erreur inconnue")
                response_content = f"""
Désolé, je n'ai pas pu traiter votre demande concernant les données d'exploitation.

**Erreur** : {error_message}

Veuillez vérifier que :
- Votre exploitation est bien configurée
- Vous avez accès aux données de votre ferme
- Votre question est claire et spécifique

Vous pouvez essayer de reformuler votre question ou me demander de l'aide pour accéder à vos données d'exploitation.
                """.strip()
                
                return ChatResponse(
                    content=response_content,
                    agent_type=AgentType.FARM_DATA,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "agent_name": "Gestionnaire de Données d'Exploitation",
                        "error": error_message,
                        "error_type": result.get("error_type", "unknown")
                    }
                )
                
        except Exception as e:
            # Fallback to placeholder if farm agent fails
            response_content = f"""
Bonjour {user.full_name or user.email.split('@')[0]},

Je suis votre Gestionnaire de Données d'Exploitation. Je peux vous aider avec :

📊 **Données de votre exploitation** :
- Informations sur vos parcelles
- Historique des interventions
- Profil de votre exploitation
- Contexte régional

🔍 **Votre demande** : {message}

Actuellement, je rencontre un problème technique. Veuillez réessayer dans quelques instants.

En attendant, vous pouvez :
- Consulter vos données directement via l'interface web
- Me poser des questions générales sur l'agriculture
- Demander de l'aide pour configurer votre exploitation

Avez-vous des questions spécifiques sur vos données d'exploitation ?
            """.strip()
            
            return ChatResponse(
                content=response_content,
                agent_type=AgentType.FARM_DATA,
                timestamp=datetime.utcnow(),
                metadata={
                    "agent_name": "Gestionnaire de Données d'Exploitation",
                    "capabilities": ["parcels", "interventions", "farm_profile", "regional_context"],
                    "error": str(e)
                }
            )
    
    async def _process_regulatory_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        message: str,
        user: User
    ) -> ChatResponse:
        """Process message with Regulatory & Product Compliance agent"""
        # TODO: Implement actual regulatory agent logic
        
        response_content = f"""
Bonjour {user.full_name or user.email.split('@')[0]},

Je suis votre Conseiller en Conformité Réglementaire. Je peux vous aider avec :

⚖️ **Conformité réglementaire** :
- Recherche de produits autorisés (AMM)
- Conditions d'utilisation
- Classifications de sécurité
- Correspondance avec produits importés

🔍 **Votre demande** : {message}

Pour le moment, je suis en cours de développement. Bientôt, je pourrai :
- Vérifier l'autorisation de vos produits phytosanitaires
- Contrôler la conformité de vos interventions
- Vous alerter sur les restrictions réglementaires
- Fournir les conditions d'utilisation précises

Avez-vous des questions sur la réglementation de vos produits ?
        """.strip()
        
        return ChatResponse(
            content=response_content,
            agent_type=AgentType.REGULATORY,
            timestamp=datetime.utcnow(),
            metadata={
                "agent_name": "Conseiller en Conformité Réglementaire",
                "capabilities": ["amm_search", "usage_conditions", "safety_classifications", "compliance_check"]
            }
        )
    
    async def _process_weather_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        message: str,
        user: User
    ) -> ChatResponse:
        """Process message with Weather Intelligence agent"""
        # TODO: Implement actual weather agent logic
        
        response_content = f"""
Bonjour {user.full_name or user.email.split('@')[0]},

Je suis votre Conseiller Météorologique Agricole. Je peux vous aider avec :

🌤️ **Intelligence météorologique** :
- Conditions météo actuelles
- Prévisions à court et long terme
- Alertes météo agricoles
- Conseils d'intervention selon la météo

🔍 **Votre demande** : {message}

Pour le moment, je suis en cours de développement. Bientôt, je pourrai :
- Analyser les conditions météo optimales pour vos interventions
- Vous alerter sur les risques météorologiques
- Recommander les meilleurs moments pour traiter
- Intégrer les données Météo France

Avez-vous des questions sur les conditions météorologiques ?
        """.strip()
        
        return ChatResponse(
            content=response_content,
            agent_type=AgentType.WEATHER,
            timestamp=datetime.utcnow(),
            metadata={
                "agent_name": "Conseiller Météorologique Agricole",
                "capabilities": ["current_weather", "forecasts", "weather_alerts", "intervention_timing"]
            }
        )
    
    async def _process_crop_health_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        message: str,
        user: User
    ) -> ChatResponse:
        """Process message with Crop Health Monitor agent"""
        # TODO: Implement actual crop health agent logic
        
        response_content = f"""
Bonjour {user.full_name or user.email.split('@')[0]},

Je suis votre Moniteur de Santé des Cultures. Je peux vous aider avec :

🌱 **Santé des cultures** :
- Diagnostic des maladies et ravageurs
- Recommandations de traitement
- Surveillance des cultures
- Prévention des problèmes

🔍 **Votre demande** : {message}

Pour le moment, je suis en cours de développement. Bientôt, je pourrai :
- Analyser les symptômes de vos cultures
- Identifier les maladies et ravageurs
- Recommander des traitements appropriés
- Suivre l'évolution de la santé de vos cultures

Avez-vous des questions sur la santé de vos cultures ?
        """.strip()
        
        return ChatResponse(
            content=response_content,
            agent_type=AgentType.CROP_HEALTH,
            timestamp=datetime.utcnow(),
            metadata={
                "agent_name": "Moniteur de Santé des Cultures",
                "capabilities": ["disease_diagnosis", "pest_identification", "treatment_recommendations", "crop_monitoring"]
            }
        )
    
    async def _process_planning_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        message: str,
        user: User
    ) -> ChatResponse:
        """Process message with Operational Planning Coordinator agent"""
        # TODO: Implement actual planning agent logic
        
        response_content = f"""
Bonjour {user.full_name or user.email.split('@')[0]},

Je suis votre Coordinateur de Planification Opérationnelle. Je peux vous aider avec :

📅 **Planification opérationnelle** :
- Calendrier des interventions
- Optimisation des ressources
- Coordination des équipes
- Gestion des priorités

🔍 **Votre demande** : {message}

Pour le moment, je suis en cours de développement. Bientôt, je pourrai :
- Créer des calendriers d'intervention optimisés
- Coordonner vos activités agricoles
- Optimiser l'utilisation de vos ressources
- Gérer les contraintes météorologiques et réglementaires

Avez-vous des questions sur la planification de vos activités ?
        """.strip()
        
        return ChatResponse(
            content=response_content,
            agent_type=AgentType.PLANNING,
            timestamp=datetime.utcnow(),
            metadata={
                "agent_name": "Coordinateur de Planification Opérationnelle",
                "capabilities": ["intervention_calendar", "resource_optimization", "team_coordination", "priority_management"]
            }
        )
    
    async def _process_sustainability_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        message: str,
        user: User
    ) -> ChatResponse:
        """Process message with Sustainability & Analytics agent"""
        # TODO: Implement actual sustainability agent logic
        
        response_content = f"""
Bonjour {user.full_name or user.email.split('@')[0]},

Je suis votre Conseiller en Durabilité Agricole. Je peux vous aider avec :

🌍 **Durabilité et analytics** :
- Indicateurs de durabilité
- Analyse de l'impact environnemental
- Optimisation des ressources
- Reporting réglementaire

🔍 **Votre demande** : {message}

Pour le moment, je suis en cours de développement. Bientôt, je pourrai :
- Calculer votre empreinte carbone
- Analyser l'efficacité de vos pratiques
- Recommander des améliorations durables
- Générer des rapports de durabilité

Avez-vous des questions sur la durabilité de votre exploitation ?
        """.strip()
        
        return ChatResponse(
            content=response_content,
            agent_type=AgentType.SUSTAINABILITY,
            timestamp=datetime.utcnow(),
            metadata={
                "agent_name": "Conseiller en Durabilité Agricole",
                "capabilities": ["sustainability_metrics", "environmental_impact", "resource_optimization", "sustainability_reporting"]
            }
        )
    
    async def get_agent_capabilities(self, agent_type: AgentType) -> Dict[str, Any]:
        """Get capabilities of a specific agent"""
        capabilities = {
            AgentType.FARM_DATA: {
                "name": "Gestionnaire de Données d'Exploitation",
                "description": "Expert en données d'exploitation agricole française",
                "capabilities": ["parcels", "interventions", "farm_profile", "regional_context"],
                "supported_farm_types": ["all"],
                "language": "fr"
            },
            AgentType.REGULATORY: {
                "name": "Conseiller en Conformité Réglementaire",
                "description": "Expert en réglementation phytosanitaire française",
                "capabilities": ["amm_search", "usage_conditions", "safety_classifications", "compliance_check"],
                "supported_farm_types": ["all"],
                "language": "fr"
            },
            AgentType.WEATHER: {
                "name": "Conseiller Météorologique Agricole",
                "description": "Expert météorologique pour l'agriculture française",
                "capabilities": ["current_weather", "forecasts", "weather_alerts", "intervention_timing"],
                "supported_farm_types": ["all"],
                "language": "fr"
            },
            AgentType.CROP_HEALTH: {
                "name": "Moniteur de Santé des Cultures",
                "description": "Spécialiste de la santé des cultures",
                "capabilities": ["disease_diagnosis", "pest_identification", "treatment_recommendations", "crop_monitoring"],
                "supported_farm_types": ["all"],
                "language": "fr"
            },
            AgentType.PLANNING: {
                "name": "Coordinateur de Planification Opérationnelle",
                "description": "Expert en planification des activités agricoles",
                "capabilities": ["intervention_calendar", "resource_optimization", "team_coordination", "priority_management"],
                "supported_farm_types": ["all"],
                "language": "fr"
            },
            AgentType.SUSTAINABILITY: {
                "name": "Conseiller en Durabilité Agricole",
                "description": "Expert en durabilité et analytics agricoles",
                "capabilities": ["sustainability_metrics", "environmental_impact", "resource_optimization", "sustainability_reporting"],
                "supported_farm_types": ["all"],
                "language": "fr"
            }
        }
        
        return capabilities.get(agent_type, {})
