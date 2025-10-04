"""
Journal Intelligence Agent
Specialized agent for voice journal entry processing and validation
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, date
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from pydantic import BaseModel, Field

from app.services.validation.intervention_checker import InterventionChecker
from app.services.infrastructure.ephy_service import EphyService
from app.services.infrastructure.weather_service import WeatherService
from app.models.intervention import VoiceJournalEntry

logger = logging.getLogger(__name__)


class JournalExtractionInput(BaseModel):
    """Input for journal data extraction"""
    transcript: str = Field(description="Voice transcript of the journal entry")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="User and farm context")


class JournalValidationInput(BaseModel):
    """Input for journal validation"""
    intervention_data: Dict[str, Any] = Field(description="Extracted intervention data")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="User and farm context")


class JournalConfirmationInput(BaseModel):
    """Input for journal confirmation"""
    intervention_data: Dict[str, Any] = Field(description="Intervention data to confirm")
    validation_results: List[Dict[str, Any]] = Field(description="Validation results")


@tool(args_schema=JournalExtractionInput)
async def extract_journal_data_tool(transcript: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract structured intervention data from voice transcript.
    Uses advanced NLP to parse agricultural intervention descriptions.
    """
    try:
        # Enhanced extraction prompt with agricultural context
        extraction_prompt = f"""
        Tu es un expert en agriculture française. Extrait les informations structurées de cette entrée de journal agricole.

        TRANSCRIPT: "{transcript}"

        CONTEXTE UTILISATEUR: {user_context or "Non spécifié"}

        Retourne un JSON structuré avec les champs suivants:
        {{
            "type_intervention": "semis|traitement_phytosanitaire|fertilisation|recolte|irrigation|travail_sol|observation|autre",
            "parcelle": "nom ou identifiant de la parcelle",
            "date_intervention": "YYYY-MM-DD",
            "surface_travaillee_ha": "surface en hectares (nombre)",
            "culture": "type de culture (blé, maïs, colza, etc.)",
            "intrants": [
                {{
                    "libelle": "nom du produit",
                    "code_amm": "code AMM si mentionné",
                    "quantite_totale": "quantité utilisée (nombre)",
                    "unite_intrant_intervention": "unité (L, kg, etc.)",
                    "type_intrant": "Phytosanitaire|Fertilisation|Semence|Autre",
                    "cible": "cible du traitement (mauvaises herbes, maladies, ravageurs)"
                }}
            ],
            "materiels": [
                {{
                    "libelle": "nom de l'équipement",
                    "type_materiel": "Pulvérisateur|Semoir|Tracteur|Autre"
                }}
            ],
            "conditions_meteo": "description des conditions météo",
            "temperature_celsius": "température en °C (nombre)",
            "humidity_percent": "humidité en % (nombre)",
            "wind_speed_kmh": "vitesse du vent en km/h (nombre)",
            "notes": "notes supplémentaires",
            "duration_minutes": "durée de l'intervention en minutes (nombre)",
            "prestataire": "nom du prestataire si applicable",
            "cout_euros": "coût en euros (nombre)"
        }}

        RÈGLES D'EXTRACTION:
        1. Si une information n'est pas mentionnée, utilise null
        2. Pour les dates, utilise le format YYYY-MM-DD
        3. Pour les nombres, utilise des valeurs numériques (pas de texte)
        4. Pour les types d'intervention, utilise exactement les valeurs listées
        5. Si plusieurs produits sont mentionnés, crée un tableau d'intrants
        6. Extrait les codes AMM si mentionnés (format: 1234567)
        7. Pour les cultures, utilise les noms français standards
        8. Si la date n'est pas spécifiée, utilise la date d'aujourd'hui: {date.today().isoformat()}

        EXEMPLES:
        - "J'ai semé du blé sur la parcelle Nord" → type_intervention: "semis", culture: "blé", parcelle: "Nord"
        - "Traitement fongicide avec Saracen Delta" → type_intervention: "traitement_phytosanitaire", intrants: [{{"libelle": "Saracen Delta", "type_intrant": "Phytosanitaire"}}]
        - "Fertilisation azotée 200 kg/ha" → type_intervention: "fertilisation", intrants: [{{"libelle": "Azote", "quantite_totale": 200, "unite_intrant_intervention": "kg/ha"}}]
        """
        
        # Use OpenAI for extraction
        from openai import AsyncOpenAI
        from app.core.config import settings
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en agriculture française. Extrait les informations structurées des entrées de journal avec précision."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.1
        )
        
        # Parse JSON response
        import json
        structured_data = json.loads(response.choices[0].message.content)
        
        # Add metadata
        structured_data["extraction_metadata"] = {
            "extracted_at": datetime.now().isoformat(),
            "transcript_length": len(transcript),
            "user_context": user_context
        }
        
        return {
            "success": True,
            "data": structured_data,
            "extraction_quality": "high"
        }
        
    except Exception as e:
        logger.error(f"Error extracting journal data: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "type_intervention": "unknown",
                "content": transcript,
                "notes": f"Erreur lors de l'extraction: {str(e)}"
            }
        }


@tool(args_schema=JournalValidationInput)
async def validate_journal_entry_tool(intervention_data: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate journal entry against agricultural guidelines and regulations.
    Checks compliance, data quality, and best practices.
    """
    try:
        intervention_checker = InterventionChecker()
        
        # Validate intervention
        validation_result = await intervention_checker.validate_and_confirm_intervention(
            intervention_data, user_context
        )
        
        return {
            "success": True,
            "validation_results": validation_result.get("validation_results", []),
            "confirmation_summary": validation_result.get("confirmation_summary", {}),
            "requires_confirmation": validation_result.get("requires_confirmation", False),
            "can_proceed": validation_result.get("can_proceed", False),
            "voice_confirmation": validation_result.get("voice_confirmation", "")
        }
        
    except Exception as e:
        logger.error(f"Error validating journal entry: {e}")
        return {
            "success": False,
            "error": str(e),
            "validation_results": []
        }


@tool
async def lookup_approved_products_tool(crop_type: str, product_type: str = "Phytosanitaire") -> Dict[str, Any]:
    """
    Look up approved products for a specific crop from EPHY database.
    Returns list of authorized products with AMM codes.
    """
    try:
        ephy_service = EphyService()
        
        # Get approved products for the crop
        products = await ephy_service.get_approved_products_for_crop(
            crop_type=crop_type,
            product_type=product_type,
            limit=20
        )
        
        return {
            "success": True,
            "crop_type": crop_type,
            "product_type": product_type,
            "products": products,
            "count": len(products)
        }
        
    except Exception as e:
        logger.error(f"Error looking up approved products: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


@tool
async def validate_product_amm_tool(amm_code: str, crop_type: str, dose_per_ha: float) -> Dict[str, Any]:
    """
    Validate AMM code against EPHY database for specific crop and dose.
    Checks authorization status, dose limits, and usage conditions.
    """
    try:
        ephy_service = EphyService()
        
        # Validate product usage
        validation = await ephy_service.validate_product_usage(
            amm_code=amm_code,
            crop_type=crop_type,
            application_date=date.today(),
            dose_per_ha=dose_per_ha
        )
        
        return {
            "success": True,
            "amm_code": amm_code,
            "crop_type": crop_type,
            "dose_per_ha": dose_per_ha,
            "is_valid": validation.get("is_valid", False),
            "errors": validation.get("errors", []),
            "warnings": validation.get("warnings", []),
            "product_info": validation.get("product_info", {})
        }
        
    except Exception as e:
        logger.error(f"Error validating AMM code: {e}")
        return {
            "success": False,
            "error": str(e),
            "is_valid": False
        }


@tool
async def get_weather_conditions_tool(location: str, date: str) -> Dict[str, Any]:
    """
    Get weather conditions for a specific location and date.
    Used for validating intervention timing and conditions.
    """
    try:
        weather_service = WeatherService()
        
        # Parse date
        target_date = datetime.fromisoformat(date).date()
        
        # Get weather data
        weather_data = await weather_service.get_weather_for_date(
            date=target_date,
            location=location
        )
        
        return {
            "success": True,
            "location": location,
            "date": date,
            "weather": weather_data
        }
        
    except Exception as e:
        logger.error(f"Error getting weather conditions: {e}")
        return {
            "success": False,
            "error": str(e),
            "weather": {}
        }


class JournalIntelligenceAgent:
    """
    Journal Intelligence Agent using LangChain ReAct pattern.
    
    Specialized agent for:
    - Voice journal entry processing
    - Structured data extraction
    - Agricultural intervention validation
    - EPHY compliance checking
    - Interactive confirmation generation
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        config: Optional[Dict[str, Any]] = None,
        enable_dynamic_examples: bool = False,
        max_iterations: int = 8,
        enable_metrics: bool = True
    ):
        """
        Initialize Journal Intelligence Agent.
        
        Args:
            llm: Language model to use
            tools: List of tools to use
            config: Additional configuration
            enable_dynamic_examples: Whether to include few-shot examples
            max_iterations: Maximum ReAct iterations
            enable_metrics: Whether to track performance metrics
        """
        # Use provided LLM or create default
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1
        )

        # Use provided tools or default journal tools
        self.tools = tools or [
            extract_journal_data_tool,
            validate_journal_entry_tool,
            lookup_approved_products_tool,
            validate_product_amm_tool,
            get_weather_conditions_tool
        ]

        self.config = config or {}
        self.enable_dynamic_examples = enable_dynamic_examples
        self.max_iterations = max_iterations
        self.enable_metrics = enable_metrics
        
        # Initialize agent executor
        self.agent_executor = None
        self._initialize_agent_executor()
    
    def _initialize_agent_executor(self):
        """Initialize agent executor with journal-specific prompt"""
        try:
            # Journal-specific system prompt
            system_prompt = """Tu es un assistant agricole expert spécialisé dans le traitement des entrées de journal agricole.

PERSONNALITÉ:
- Précis et méthodique dans l'extraction de données
- Rigoureux sur la validation réglementaire
- Pédagogue pour expliquer les problèmes de conformité
- Proactif dans la recherche d'informations manquantes

RÔLE PRINCIPAL:
Tu traites les entrées de journal agricole enregistrées par voix pour:
1. Extraire les données structurées des transcriptions
2. Valider la conformité réglementaire (EPHY, AMM, etc.)
3. Vérifier la cohérence des données
4. Générer des confirmations interactives
5. Proposer des corrections si nécessaire

OUTILS DISPONIBLES:
- extract_journal_data_tool: Extrait les données structurées des transcriptions
- validate_journal_entry_tool: Valide contre les guidelines agricoles
- lookup_approved_products_tool: Recherche les produits autorisés dans EPHY
- validate_product_amm_tool: Valide les codes AMM et doses
- get_weather_conditions_tool: Vérifie les conditions météo

PROCESSUS DE TRAITEMENT:
1. **Extraction**: Utilise extract_journal_data_tool pour structurer les données
2. **Validation**: Utilise validate_journal_entry_tool pour vérifier la conformité
3. **Vérification**: Si des produits sont mentionnés, vérifie les codes AMM
4. **Confirmation**: Génère un résumé pour confirmation par l'agriculteur

RÈGLES IMPORTANTES:
- Toujours vérifier les codes AMM pour les produits phytosanitaires
- Valider les doses contre les limites autorisées
- Vérifier les conditions météo pour les traitements
- Proposer des alternatives si des produits ne sont pas autorisés
- Expliquer clairement les problèmes de conformité

FORMAT DE RÉPONSE:
- Utilise les outils de manière séquentielle
- Explique chaque étape de validation
- Propose des solutions concrètes aux problèmes
- Génère des confirmations claires et compréhensibles"""

            # Create agent prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create agent
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                return_intermediate_steps=True,
                max_iterations=self.max_iterations,
                handle_parsing_errors=True
            )
            
            logger.info("Journal Intelligence Agent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Journal Intelligence Agent: {e}")
    
    async def process_journal_entry(
        self, 
        transcript: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a voice journal entry through the complete pipeline.
        
        Args:
            transcript: Voice transcript of the journal entry
            user_context: User and farm context information
            
        Returns:
            Complete processing result with extraction, validation, and confirmation
        """
        try:
            if not self.agent_executor:
                raise Exception("Agent executor not initialized")
            
            # Create processing prompt
            processing_prompt = f"""
            Traite cette entrée de journal agricole enregistrée par voix:
            
            TRANSCRIPT: "{transcript}"
            
            CONTEXTE UTILISATEUR: {user_context or "Non spécifié"}
            
            Effectue les étapes suivantes:
            1. Extrait les données structurées de la transcription
            2. Valide la conformité réglementaire
            3. Vérifie les codes AMM si des produits sont mentionnés
            4. Génère un résumé de confirmation
            
            Retourne un résultat complet avec toutes les informations nécessaires.
            """
            
            # Process through agent
            result = await self.agent_executor.ainvoke({
                "input": processing_prompt
            })
            
            return {
                "success": True,
                "result": result,
                "transcript": transcript,
                "user_context": user_context,
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing journal entry: {e}")
            return {
                "success": False,
                "error": str(e),
                "transcript": transcript,
                "user_context": user_context
            }
    
    async def extract_and_validate(
        self, 
        transcript: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract and validate journal entry data.
        
        Returns:
            Structured data with validation results
        """
        try:
            # Extract data
            extraction_result = await extract_journal_data_tool(transcript, user_context)
            
            if not extraction_result.get("success"):
                return extraction_result
            
            intervention_data = extraction_result.get("data", {})
            
            # Validate data
            validation_result = await validate_journal_entry_tool(intervention_data, user_context)
            
            return {
                "success": True,
                "extraction": extraction_result,
                "validation": validation_result,
                "intervention_data": intervention_data
            }
            
        except Exception as e:
            logger.error(f"Error in extract_and_validate: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_confirmation(
        self, 
        intervention_data: Dict[str, Any], 
        validation_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate interactive confirmation for the farmer.
        
        Returns:
            Confirmation data with questions and voice text
        """
        try:
            # Use validation tool to generate confirmation
            confirmation_result = await validate_journal_entry_tool(intervention_data)
            
            return {
                "success": True,
                "confirmation": confirmation_result,
                "intervention_data": intervention_data
            }
            
        except Exception as e:
            logger.error(f"Error generating confirmation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
