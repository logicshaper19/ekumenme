"""
Advanced LangChain Service for Agricultural AI
Integrates RAG, reasoning chains, and advanced agent orchestration
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.unified_regulatory_service import UnifiedRegulatoryService
from app.services.semantic_routing_service import SemanticRoutingService
from app.services.memory_persistence_service import MemoryPersistenceService
from app.services.langgraph_workflow_service import LangGraphWorkflowService

logger = logging.getLogger(__name__)


class AgriculturalResponse(BaseModel):
    """Structured response for agricultural queries"""
    response: str = Field(description="Main response content")
    agent_type: str = Field(description="Type of agent that processed the query")
    confidence: float = Field(description="Confidence score 0-1")
    sources: List[str] = Field(default=[], description="Knowledge sources used")
    recommendations: List[str] = Field(default=[], description="Specific recommendations")
    regulatory_compliance: Optional[Dict[str, Any]] = Field(default=None, description="Compliance information")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class AdvancedLangChainService:
    """Advanced LangChain service with RAG, reasoning chains, and agent orchestration"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.memory = None
        self.rag_chain = None
        self.regulatory_service = UnifiedRegulatoryService()
        self.semantic_router = None
        self.memory_persistence = None
        self.langgraph_workflow = None
        self.tools = []
        self.agent_executor = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize LangChain components"""
        try:
            # Initialize LLM
            self.llm = ChatOpenAI(
                model_name="gpt-4",
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Initialize memory
            self.memory = ConversationBufferWindowMemory(
                k=10,
                memory_key="chat_history",
                return_messages=True
            )
            
            # Initialize tools
            self._initialize_tools()
            
            # Initialize vector store (will be populated with agricultural knowledge)
            self._initialize_vectorstore()
            
            # Initialize RAG chain
            self._initialize_rag_chain()
            
            # Initialize agent executor
            self._initialize_agent_executor()

            # Initialize semantic routing
            self._initialize_semantic_routing()

            # Initialize memory persistence
            self._initialize_memory_persistence()

            # Initialize LangGraph workflow
            self._initialize_langgraph_workflow()

            logger.info("Advanced LangChain service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain components: {e}")
            raise
    
    def _initialize_tools(self):
        """Initialize agricultural tools"""
        
        @tool
        def get_weather_data(location: str, days: int = 7) -> str:
            """Get weather forecast for agricultural planning"""
            try:
                # Import weather tool
                from app.tools.weather_agent.get_weather_data_tool import GetWeatherDataTool
                weather_tool = GetWeatherDataTool()
                return weather_tool._run(location=location, days=days)
            except Exception as e:
                return f"Error getting weather data: {str(e)}"
        
        @tool
        def check_regulatory_compliance(product_name: str, crop: str = None) -> str:
            """Check regulatory compliance for agricultural products"""
            try:
                result = self.regulatory_service.validate_product_usage(
                    product_name=product_name,
                    crop_type=crop
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            except Exception as e:
                return f"Error checking compliance: {str(e)}"
        
        @tool
        def get_farm_data(siret: str = None, parcel_id: str = None) -> str:
            """Get farm operational data from MesParcelles integration"""
            try:
                # This would connect to your integrated agri_db
                from sqlalchemy import text
                from app.core.database import AsyncSessionLocal
                
                async def _get_data():
                    async with AsyncSessionLocal() as session:
                        if siret:
                            result = await session.execute(text("""
                                SELECT e.nom, COUNT(p.id) as parcelles_count, 
                                       COUNT(i.uuid_intervention) as interventions_count
                                FROM farm_operations.exploitations e
                                LEFT JOIN farm_operations.parcelles p ON e.siret = p.siret_exploitation
                                LEFT JOIN farm_operations.interventions i ON p.id = i.id_parcelle
                                WHERE e.siret = :siret
                                GROUP BY e.siret, e.nom
                            """), {"siret": siret})
                            data = result.fetchone()
                            if data:
                                return f"Exploitation: {data[0]}, Parcelles: {data[1]}, Interventions: {data[2]}"
                        
                        # Default summary
                        result = await session.execute(text("""
                            SELECT COUNT(DISTINCT e.siret) as exploitations,
                                   COUNT(DISTINCT p.id) as parcelles,
                                   COUNT(DISTINCT i.uuid_intervention) as interventions
                            FROM farm_operations.exploitations e
                            LEFT JOIN farm_operations.parcelles p ON e.siret = p.siret_exploitation
                            LEFT JOIN farm_operations.interventions i ON p.id = i.id_parcelle
                        """))
                        data = result.fetchone()
                        return f"Total: {data[0]} exploitations, {data[1]} parcelles, {data[2]} interventions"
                
                # Run async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(_get_data())
                loop.close()
                return result
                
            except Exception as e:
                return f"Error getting farm data: {str(e)}"
        
        @tool
        def analyze_intervention_compliance(intervention_data: str) -> str:
            """Analyze intervention compliance with EPHY regulations"""
            try:
                # Parse intervention data and check compliance
                data = json.loads(intervention_data) if isinstance(intervention_data, str) else intervention_data
                
                compliance_results = []
                for product in data.get('products', []):
                    result = self.regulatory_service.validate_product_usage(
                        product_name=product.get('name', ''),
                        crop_type=data.get('crop_type'),
                        dosage=product.get('dosage'),
                        application_method=data.get('application_method')
                    )
                    compliance_results.append(result)
                
                return json.dumps(compliance_results, ensure_ascii=False, indent=2)
            except Exception as e:
                return f"Error analyzing compliance: {str(e)}"
        
        # Add more specialized tools
        @tool
        def diagnose_crop_disease(symptoms: str, crop_type: str = None) -> str:
            """Diagnose crop diseases from symptoms"""
            try:
                from app.tools.crop_health_agent.diagnose_disease_tool import DiagnoseDiseaseTool
                disease_tool = DiagnoseDiseaseTool()
                return disease_tool._run(symptoms=symptoms, crop_type=crop_type)
            except Exception as e:
                return f"Error diagnosing disease: {str(e)}"

        @tool
        def identify_pest(damage_description: str, crop_type: str = None) -> str:
            """Identify crop pests from damage patterns"""
            try:
                from app.tools.crop_health_agent.identify_pest_tool import IdentifyPestTool
                pest_tool = IdentifyPestTool()
                return pest_tool._run(damage_description=damage_description, crop_type=crop_type)
            except Exception as e:
                return f"Error identifying pest: {str(e)}"

        @tool
        def analyze_nutrient_deficiency(symptoms: str, crop_type: str = None) -> str:
            """Analyze nutrient deficiencies from symptoms"""
            try:
                from app.tools.crop_health_agent.analyze_nutrient_deficiency_tool import AnalyzeNutrientDeficiencyTool
                nutrient_tool = AnalyzeNutrientDeficiencyTool()
                return nutrient_tool._run(symptoms=symptoms, crop_type=crop_type)
            except Exception as e:
                return f"Error analyzing nutrient deficiency: {str(e)}"

        @tool
        def generate_planning_tasks(crops: str, surface: float, planning_objective: str = "standard") -> str:
            """Generate planning tasks for crops and surface area"""
            try:
                from app.tools.planning_agent.generate_planning_tasks_tool import GeneratePlanningTasksTool
                planning_tool = GeneratePlanningTasksTool()
                return planning_tool._run(crops=crops, surface=surface, planning_objective=planning_objective)
            except Exception as e:
                return f"Error generating planning tasks: {str(e)}"

        @tool
        def calculate_performance_metrics(farm_data: str) -> str:
            """Calculate farm performance metrics"""
            try:
                from app.tools.farm_data_agent.calculate_performance_metrics_tool import CalculatePerformanceMetricsTool
                metrics_tool = CalculatePerformanceMetricsTool()
                return metrics_tool._run(farm_data=farm_data)
            except Exception as e:
                return f"Error calculating performance metrics: {str(e)}"

        @tool
        def lookup_amm_database(product_name: str, crop_type: str = None) -> str:
            """Look up AMM information using real EPHY database"""
            try:
                from app.tools.regulatory_agent.database_integrated_amm_tool import DatabaseIntegratedAMMLookupTool
                amm_tool = DatabaseIntegratedAMMLookupTool()
                return amm_tool._run(product_name=product_name, crop_type=crop_type)
            except Exception as e:
                return f"Error looking up AMM data: {str(e)}"

        @tool
        def analyze_weather_risks(weather_data: str, crop_type: str = None) -> str:
            """Analyze weather risks for agricultural operations"""
            try:
                from app.tools.weather_agent.analyze_weather_risks_tool import AnalyzeWeatherRisksTool
                risk_tool = AnalyzeWeatherRisksTool()
                return risk_tool._run(weather_data=weather_data, crop_type=crop_type)
            except Exception as e:
                return f"Error analyzing weather risks: {str(e)}"

        @tool
        def calculate_carbon_footprint(farm_operations: str) -> str:
            """Calculate carbon footprint of farm operations"""
            try:
                from app.tools.sustainability_agent.calculate_carbon_footprint_tool import CalculateCarbonFootprintTool
                carbon_tool = CalculateCarbonFootprintTool()
                return carbon_tool._run(farm_operations=farm_operations)
            except Exception as e:
                return f"Error calculating carbon footprint: {str(e)}"

        # Compile all tools
        self.tools = [
            get_weather_data, check_regulatory_compliance, get_farm_data, analyze_intervention_compliance,
            diagnose_crop_disease, identify_pest, analyze_nutrient_deficiency, generate_planning_tasks,
            calculate_performance_metrics, lookup_amm_database, analyze_weather_risks, calculate_carbon_footprint
        ]
    
    def _initialize_vectorstore(self):
        """Initialize vector store with agricultural knowledge"""
        try:
            # Create agricultural knowledge documents
            agricultural_docs = [
                "Les zones non traitées (ZNT) sont obligatoires le long des cours d'eau pour protéger l'environnement aquatique.",
                "Le glyphosate est limité à 2 applications par an avec une dose maximale de 3L/ha.",
                "Les néonicotinoïdes sont interdits sur tournesol, colza et lin sauf dérogation betterave 2024.",
                "Le cuivre est limité à 4 kg/ha/an en conventionnel et 6 kg/ha/an en agriculture biologique.",
                "Les délais avant récolte varient selon les cultures: 7 jours pour légumes feuilles, 21 jours fruits à pépins.",
                "La pulvérisation est optimale avec vent < 10 km/h, humidité > 60%, température < 30°C.",
                "Les heures d'application doivent éviter l'activité des abeilles (8h-18h) et privilégier 6h-10h ou 18h-22h.",
                "La protection des eaux souterraines nécessite des précautions spéciales en Champagne (sol crayeux).",
                "En Bretagne, les restrictions algues vertes s'appliquent avec multiplicateur pluviométrie 1.4.",
                "La Provence nécessite des précautions feu (multiplicateur 1.8) et restrictions vent mistral."
            ]
            
            # Create vector store
            self.vectorstore = Chroma.from_texts(
                texts=agricultural_docs,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
            )
            
            logger.info("Vector store initialized with agricultural knowledge")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            # Create empty vector store as fallback
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                persist_directory="./chroma_db"
            )
    
    def _initialize_rag_chain(self):
        """Initialize RAG chain for knowledge retrieval"""
        try:
            if self.vectorstore:
                retriever = self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 3}
                )
                
                self.rag_chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm,
                    retriever=retriever,
                    memory=self.memory,
                    return_source_documents=True,
                    verbose=True
                )
                
                logger.info("RAG chain initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG chain: {e}")
    
    def _initialize_agent_executor(self):
        """Initialize agent executor with tools"""
        try:
            # Import enhanced prompts
            from app.prompts.base_prompts import BASE_AGRICULTURAL_SYSTEM_PROMPT, RESPONSE_FORMAT_TEMPLATE

            # Create agent prompt with enhanced personality and structure
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""{BASE_AGRICULTURAL_SYSTEM_PROMPT}

OUTILS DISPONIBLES:
Tu as accès à des outils spécialisés pour:
- Données météorologiques (get_weather_data)
- Conformité réglementaire (check_regulatory_compliance, lookup_amm_database)
- Données d'exploitation (get_farm_data, calculate_performance_metrics)
- Diagnostic phytosanitaire (diagnose_crop_disease, identify_pest, analyze_nutrient_deficiency)
- Planification (generate_planning_tasks)
- Analyse des risques (analyze_weather_risks)
- Durabilité (calculate_carbon_footprint)

UTILISE CES OUTILS de manière proactive pour enrichir tes réponses avec des données réelles.

{RESPONSE_FORMAT_TEMPLATE}
                """),
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
                max_iterations=5
            )
            
            logger.info("Agent executor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize agent executor: {e}")

    def _initialize_semantic_routing(self):
        """Initialize semantic routing service"""
        try:
            self.semantic_router = SemanticRoutingService()
            logger.info("Semantic routing initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize semantic routing: {e}")
            self.semantic_router = None

    def _initialize_memory_persistence(self):
        """Initialize memory persistence service"""
        try:
            self.memory_persistence = MemoryPersistenceService()
            logger.info("Memory persistence initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize memory persistence: {e}")
            self.memory_persistence = None

    def _initialize_langgraph_workflow(self):
        """Initialize LangGraph workflow service"""
        try:
            self.langgraph_workflow = LangGraphWorkflowService()
            logger.info("LangGraph workflow initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph workflow: {e}")
            self.langgraph_workflow = None

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_rag: bool = True,
        use_reasoning_chains: bool = True,
        use_tools: bool = True,
        use_langgraph: bool = True
    ) -> Dict[str, Any]:
        """Process agricultural query with advanced LangChain capabilities"""
        try:
            start_time = datetime.now()
            context = context or {}

            # Step 0: Try LangGraph workflow first if enabled and available
            if use_langgraph and self.langgraph_workflow:
                try:
                    langgraph_result = await self.langgraph_workflow.process_agricultural_query(query, context)

                    # If LangGraph succeeded, return its result
                    if langgraph_result.get("response") and not langgraph_result.get("metadata", {}).get("error"):
                        processing_time = (datetime.now() - start_time).total_seconds()
                        langgraph_result["metadata"]["processing_time"] = processing_time
                        langgraph_result["metadata"]["used_langgraph"] = True
                        return langgraph_result

                except Exception as e:
                    logger.warning(f"LangGraph workflow failed, falling back to standard processing: {e}")

            # Step 1: Semantic routing and query analysis (fallback)
            routing_result = None
            if self.semantic_router:
                routing_result = await self.semantic_router.route_query(query, context)

            query_analysis = self._analyze_query(query, routing_result)

            # Step 2: Use RAG if enabled and available
            rag_context = ""
            sources = []
            if use_rag and self.rag_chain:
                try:
                    rag_result = await self._get_rag_context(query)
                    rag_context = rag_result.get("answer", "")
                    sources = [doc.page_content for doc in rag_result.get("source_documents", [])]
                except Exception as e:
                    logger.warning(f"RAG processing failed: {e}")

            # Step 3: Use agent executor with tools if enabled
            agent_response = ""
            tool_results = []
            if use_tools and self.agent_executor:
                try:
                    agent_result = await self._execute_agent(query, context)
                    agent_response = agent_result.get("output", "")
                    tool_results = agent_result.get("intermediate_steps", [])
                except Exception as e:
                    logger.warning(f"Agent execution failed: {e}")

            # Step 4: Use reasoning chains if enabled
            reasoning_result = ""
            if use_reasoning_chains:
                try:
                    reasoning_result = await self._apply_reasoning_chains(query, context, rag_context)
                except Exception as e:
                    logger.warning(f"Reasoning chains failed: {e}")

            # Step 5: Synthesize final response
            final_response = self._synthesize_response(
                query=query,
                rag_context=rag_context,
                agent_response=agent_response,
                reasoning_result=reasoning_result,
                query_analysis=query_analysis
            )

            # Step 6: Add regulatory compliance check
            compliance_info = None
            if query_analysis.get("involves_products", False):
                try:
                    compliance_info = await self._check_regulatory_compliance(query, context)
                except Exception as e:
                    logger.warning(f"Compliance check failed: {e}")

            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                "response": final_response,
                "agent_type": query_analysis.get("agent_type", "general"),
                "confidence": query_analysis.get("confidence", 0.8),
                "sources": sources,
                "recommendations": self._extract_recommendations(final_response),
                "regulatory_compliance": compliance_info,
                "metadata": {
                    "processing_time": processing_time,
                    "used_rag": use_rag and bool(rag_context),
                    "used_tools": use_tools and bool(agent_response),
                    "used_reasoning": use_reasoning_chains and bool(reasoning_result),
                    "tool_results": len(tool_results),
                    "query_analysis": query_analysis
                }
            }

        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "response": f"Désolé, une erreur s'est produite lors du traitement de votre demande: {str(e)}",
                "agent_type": "error",
                "confidence": 0.0,
                "sources": [],
                "recommendations": [],
                "regulatory_compliance": None,
                "metadata": {"error": str(e)}
            }

    def _analyze_query(self, query: str, routing_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze query to determine routing and complexity"""
        query_lower = query.lower()

        # Use semantic routing result if available
        if routing_result:
            agent_type = routing_result.get("primary_agent", "general")
            confidence = routing_result.get("confidence", 0.6)
            secondary_agents = routing_result.get("secondary_agents", [])
            routing_explanation = routing_result.get("routing_explanation", "")
        else:
            # Fallback to keyword-based detection
            if any(word in query_lower for word in ["météo", "temps", "pluie", "vent", "température"]):
                agent_type = "weather"
                confidence = 0.9
            elif any(word in query_lower for word in ["réglementation", "amm", "znt", "conformité", "autorisé"]):
                agent_type = "regulatory"
                confidence = 0.9
            elif any(word in query_lower for word in ["parcelle", "exploitation", "intervention", "traitement"]):
                agent_type = "farm_data"
                confidence = 0.8
            elif any(word in query_lower for word in ["planification", "optimisation", "recommandation"]):
                agent_type = "planning"
                confidence = 0.8
            else:
                agent_type = "general"
                confidence = 0.6
            secondary_agents = []
            routing_explanation = "Keyword-based routing"

        # Detect if involves products
        involves_products = any(word in query_lower for word in [
            "produit", "traitement", "fongicide", "herbicide", "insecticide",
            "glyphosate", "cuivre", "néonicotinoïde"
        ])

        # Detect complexity
        complexity = "simple"
        if len(query.split()) > 20 or "et" in query_lower or "puis" in query_lower:
            complexity = "complex"
        elif len(query.split()) > 10:
            complexity = "moderate"

        return {
            "agent_type": agent_type,
            "confidence": confidence,
            "involves_products": involves_products,
            "complexity": complexity,
            "query_length": len(query),
            "word_count": len(query.split()),
            "secondary_agents": secondary_agents,
            "routing_explanation": routing_explanation,
            "semantic_routing_used": routing_result is not None
        }

    async def _get_rag_context(self, query: str) -> Dict[str, Any]:
        """Get context from RAG system"""
        try:
            result = self.rag_chain({"question": query})
            return result
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {e}")
            return {"answer": "", "source_documents": []}

    async def _execute_agent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent with tools"""
        try:
            # Prepare input with context
            agent_input = {
                "input": query,
                **context
            }

            result = self.agent_executor.invoke(agent_input)
            return result
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {"output": "", "intermediate_steps": []}

    async def _apply_reasoning_chains(self, query: str, context: Dict[str, Any], rag_context: str) -> str:
        """Apply advanced multi-step reasoning chains for complex analysis"""
        try:
            # Step 1: Query Analysis and Classification
            query_analysis_result = await self._analyze_query_complexity(query, context)

            # Step 2: Choose appropriate reasoning chain based on query type
            if query_analysis_result["complexity"] == "high":
                return await self._apply_complex_reasoning_chain(query, context, rag_context, query_analysis_result)
            elif query_analysis_result["domain"] == "regulatory":
                return await self._apply_regulatory_reasoning_chain(query, context, rag_context)
            elif query_analysis_result["domain"] == "weather":
                return await self._apply_weather_reasoning_chain(query, context, rag_context)
            elif query_analysis_result["domain"] == "planning":
                return await self._apply_planning_reasoning_chain(query, context, rag_context)
            else:
                return await self._apply_general_reasoning_chain(query, context, rag_context)

        except Exception as e:
            logger.error(f"Advanced reasoning chains failed: {e}")
            return ""

    async def _analyze_query_complexity(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze query complexity and domain"""
        try:
            analysis_prompt = ChatPromptTemplate.from_template("""
            Analysez cette requête agricole et classifiez-la:

            Requête: {query}
            Contexte: {context}

            Répondez au format JSON avec:
            {{
                "complexity": "low|medium|high",
                "domain": "weather|regulatory|planning|pest_disease|general",
                "requires_multi_step": true/false,
                "key_factors": ["facteur1", "facteur2"],
                "reasoning_type": "analytical|procedural|diagnostic|strategic"
            }}
            """)

            from langchain.chains import LLMChain
            analysis_chain = LLMChain(llm=self.llm, prompt=analysis_prompt)
            result = analysis_chain.run(query=query, context=str(context))

            try:
                return json.loads(result)
            except:
                return {
                    "complexity": "medium",
                    "domain": "general",
                    "requires_multi_step": False,
                    "key_factors": [],
                    "reasoning_type": "analytical"
                }

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {"complexity": "medium", "domain": "general"}

    async def _apply_complex_reasoning_chain(self, query: str, context: Dict[str, Any], rag_context: str, analysis: Dict[str, Any]) -> str:
        """Apply complex multi-step reasoning for sophisticated queries"""
        try:
            complex_reasoning_prompt = ChatPromptTemplate.from_template("""
            En tant qu'expert agricole senior, résolvez cette demande complexe par étapes:

            DEMANDE: {query}
            CONTEXTE: {context}
            CONNAISSANCES: {rag_context}
            ANALYSE: {analysis}

            PROCESSUS DE RAISONNEMENT AVANCÉ:

            ÉTAPE 1 - DÉCOMPOSITION DU PROBLÈME:
            - Identifiez les sous-problèmes
            - Hiérarchisez les priorités
            - Définissez les interdépendances

            ÉTAPE 2 - COLLECTE ET ANALYSE DES DONNÉES:
            - Évaluez les données disponibles
            - Identifiez les lacunes d'information
            - Analysez la fiabilité des sources

            ÉTAPE 3 - APPLICATION DES CONNAISSANCES EXPERTES:
            - Appliquez les principes agronomiques
            - Intégrez les contraintes réglementaires
            - Considérez les facteurs environnementaux

            ÉTAPE 4 - ÉVALUATION DES OPTIONS:
            - Générez plusieurs solutions
            - Analysez les avantages/inconvénients
            - Évaluez les risques et opportunités

            ÉTAPE 5 - RECOMMANDATION FINALE:
            - Synthétisez la meilleure approche
            - Justifiez le choix
            - Proposez un plan d'action

            RÉPONSE STRUCTURÉE:
            """)

            from langchain.chains import LLMChain
            complex_chain = LLMChain(llm=self.llm, prompt=complex_reasoning_prompt)

            result = complex_chain.run(
                query=query,
                context=str(context),
                rag_context=rag_context,
                analysis=str(analysis)
            )

            return result

        except Exception as e:
            logger.error(f"Complex reasoning chain failed: {e}")
            return ""

    async def _apply_regulatory_reasoning_chain(self, query: str, context: Dict[str, Any], rag_context: str) -> str:
        """Apply regulatory-focused reasoning chain"""
        try:
            regulatory_prompt = ChatPromptTemplate.from_template("""
            En tant qu'expert en réglementation phytosanitaire française, analysez:

            DEMANDE: {query}
            CONTEXTE: {context}
            CONNAISSANCES: {rag_context}

            ANALYSE RÉGLEMENTAIRE:
            1. Identification des produits/substances concernés
            2. Vérification des autorisations AMM
            3. Contrôle des usages autorisés
            4. Évaluation des ZNT (Zones de Non-Traitement)
            5. Vérification des DAR (Délais Avant Récolte)
            6. Conformité aux arrêtés préfectoraux

            CONCLUSION RÉGLEMENTAIRE:
            """)

            from langchain.chains import LLMChain
            regulatory_chain = LLMChain(llm=self.llm, prompt=regulatory_prompt)
            return regulatory_chain.run(query=query, context=str(context), rag_context=rag_context)

        except Exception as e:
            logger.error(f"Regulatory reasoning chain failed: {e}")
            return ""

    async def _apply_weather_reasoning_chain(self, query: str, context: Dict[str, Any], rag_context: str) -> str:
        """Apply weather-focused reasoning chain"""
        try:
            weather_prompt = ChatPromptTemplate.from_template("""
            En tant qu'expert en météorologie agricole, analysez:

            DEMANDE: {query}
            CONTEXTE: {context}
            CONNAISSANCES: {rag_context}

            ANALYSE MÉTÉOROLOGIQUE:
            1. Conditions actuelles et prévisions
            2. Impact sur les cultures et interventions
            3. Fenêtres d'application optimales
            4. Risques météorologiques
            5. Adaptations nécessaires
            6. Recommandations de timing

            CONSEIL MÉTÉO:
            """)

            from langchain.chains import LLMChain
            weather_chain = LLMChain(llm=self.llm, prompt=weather_prompt)
            return weather_chain.run(query=query, context=str(context), rag_context=rag_context)

        except Exception as e:
            logger.error(f"Weather reasoning chain failed: {e}")
            return ""

    async def _apply_planning_reasoning_chain(self, query: str, context: Dict[str, Any], rag_context: str) -> str:
        """Apply planning-focused reasoning chain"""
        try:
            planning_prompt = ChatPromptTemplate.from_template("""
            En tant qu'expert en planification agricole, développez:

            DEMANDE: {query}
            CONTEXTE: {context}
            CONNAISSANCES: {rag_context}

            PLANIFICATION STRATÉGIQUE:
            1. Analyse des objectifs et contraintes
            2. Séquençage des interventions
            3. Optimisation du calendrier cultural
            4. Gestion des ressources
            5. Intégration des facteurs externes
            6. Plan d'action détaillé

            PLAN RECOMMANDÉ:
            """)

            from langchain.chains import LLMChain
            planning_chain = LLMChain(llm=self.llm, prompt=planning_prompt)
            return planning_chain.run(query=query, context=str(context), rag_context=rag_context)

        except Exception as e:
            logger.error(f"Planning reasoning chain failed: {e}")
            return ""

    async def _apply_general_reasoning_chain(self, query: str, context: Dict[str, Any], rag_context: str) -> str:
        """Apply general agricultural reasoning chain"""
        try:
            general_prompt = ChatPromptTemplate.from_template("""
            En tant qu'expert agricole généraliste, analysez:

            DEMANDE: {query}
            CONTEXTE: {context}
            CONNAISSANCES: {rag_context}

            RAISONNEMENT AGRICOLE:
            1. Analyse de la situation
            2. Identification des contraintes
            3. Application des bonnes pratiques
            4. Évaluation des options
            5. Recommandations pratiques
            6. Suivi et ajustements

            CONSEIL AGRICOLE:
            """)

            from langchain.chains import LLMChain
            general_chain = LLMChain(llm=self.llm, prompt=general_prompt)
            return general_chain.run(query=query, context=str(context), rag_context=rag_context)

        except Exception as e:
            logger.error(f"General reasoning chain failed: {e}")
            return ""

    def _synthesize_response(
        self,
        query: str,
        rag_context: str,
        agent_response: str,
        reasoning_result: str,
        query_analysis: Dict[str, Any]
    ) -> str:
        """Synthesize final response from all components"""

        # Prioritize responses based on quality and relevance
        responses = []

        if reasoning_result and len(reasoning_result.strip()) > 50:
            responses.append(("reasoning", reasoning_result, 0.9))

        if agent_response and len(agent_response.strip()) > 30:
            responses.append(("agent", agent_response, 0.8))

        if rag_context and len(rag_context.strip()) > 20:
            responses.append(("rag", rag_context, 0.7))

        if not responses:
            return "Je n'ai pas pu traiter votre demande. Pouvez-vous la reformuler ou être plus spécifique?"

        # Use the highest quality response
        responses.sort(key=lambda x: x[2], reverse=True)
        best_response = responses[0][1]

        # Add confidence indicator if low
        if query_analysis.get("confidence", 1.0) < 0.7:
            best_response += "\n\n⚠️ Cette réponse est basée sur une interprétation de votre demande. N'hésitez pas à préciser si nécessaire."

        return best_response

    async def _check_regulatory_compliance(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check regulatory compliance for product-related queries"""
        try:
            # Extract product names from query (simplified)
            query_lower = query.lower()
            products = []

            # Common product detection
            if "glyphosate" in query_lower:
                products.append("glyphosate")
            if "cuivre" in query_lower:
                products.append("cuivre")

            if not products:
                return None

            compliance_results = []
            for product in products:
                result = self.regulatory_service.validate_product_usage(
                    product_name=product,
                    crop_type=context.get("crop_type")
                )
                compliance_results.append(result)

            return {
                "products_checked": products,
                "compliance_results": compliance_results,
                "overall_compliant": all(r.get("is_compliant", False) for r in compliance_results)
            }

        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            return None

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract actionable recommendations from response"""
        recommendations = []

        # Simple extraction based on common patterns
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in [
                "recommande", "conseille", "suggère", "préconise",
                "il faut", "vous devez", "pensez à"
            ]):
                recommendations.append(line)

        return recommendations[:5]  # Limit to 5 recommendations
