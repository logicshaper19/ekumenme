"""
Semantic Routing Service for Agricultural AI
Intelligent query analysis and agent selection based on content
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import re

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class SemanticRoutingService:
    """Intelligent routing service for agricultural queries"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.tfidf_vectorizer = None
        self.agent_patterns = {}
        self.routing_cache = {}
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize semantic routing components"""
        try:
            # Initialize LLM and embeddings
            self.llm = ChatOpenAI(
                model_name="gpt-4",
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Initialize TF-IDF for fast keyword matching
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Define agent patterns and keywords
            self._setup_agent_patterns()
            
            # Create routing knowledge base
            self._create_routing_vectorstore()
            
            logger.info("Semantic routing service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic routing: {e}")
            raise
    
    def _setup_agent_patterns(self):
        """Setup patterns and keywords for different agent types"""
        self.agent_patterns = {
            "weather": {
                "keywords": [
                    "météo", "temps", "pluie", "vent", "température", "humidité",
                    "prévisions", "climat", "gel", "grêle", "sécheresse", "orage",
                    "weather", "rain", "wind", "temperature", "humidity", "forecast"
                ],
                "patterns": [
                    r"quel.*temps",
                    r"prévision.*météo",
                    r"condition.*météorologique",
                    r"risque.*gel",
                    r"fenêtre.*application"
                ],
                "confidence_boost": 0.2
            },
            "regulatory": {
                "keywords": [
                    "réglementation", "amm", "znt", "conformité", "autorisation",
                    "dar", "délai", "récolte", "arrêté", "préfectoral", "ephy",
                    "regulation", "compliance", "authorization", "legal"
                ],
                "patterns": [
                    r"autoris.*amm",
                    r"zone.*non.*traitement",
                    r"délai.*avant.*récolte",
                    r"conforme.*réglementation",
                    r"usage.*autorisé"
                ],
                "confidence_boost": 0.3
            },
            "pest_disease": {
                "keywords": [
                    "maladie", "ravageur", "insecte", "champignon", "virus",
                    "traitement", "fongicide", "insecticide", "diagnostic",
                    "symptôme", "pest", "disease", "fungus", "insect", "treatment"
                ],
                "patterns": [
                    r"diagnostic.*maladie",
                    r"traitement.*ravageur",
                    r"symptôme.*culture",
                    r"identifier.*pest",
                    r"lutte.*biologique"
                ],
                "confidence_boost": 0.25
            },
            "planning": {
                "keywords": [
                    "planification", "calendrier", "programme", "itinéraire",
                    "technique", "rotation", "assolement", "planning", "schedule",
                    "strategy", "program", "rotation", "sequence"
                ],
                "patterns": [
                    r"plan.*cultural",
                    r"calendrier.*intervention",
                    r"programme.*traitement",
                    r"rotation.*culture",
                    r"stratégie.*exploitation"
                ],
                "confidence_boost": 0.2
            },
            "farm_management": {
                "keywords": [
                    "exploitation", "parcelle", "intervention", "gestion",
                    "rendement", "production", "économie", "coût", "marge",
                    "farm", "field", "management", "yield", "production", "cost"
                ],
                "patterns": [
                    r"gestion.*exploitation",
                    r"rendement.*parcelle",
                    r"analyse.*économique",
                    r"optimisation.*production",
                    r"suivi.*intervention"
                ],
                "confidence_boost": 0.15
            }
        }
    
    def _create_routing_vectorstore(self):
        """Create vector store for semantic routing"""
        try:
            # Create routing examples for each agent type
            routing_documents = []
            
            for agent_type, config in self.agent_patterns.items():
                # Create example queries for each agent type
                examples = self._generate_routing_examples(agent_type, config)
                
                for example in examples:
                    doc = Document(
                        page_content=example,
                        metadata={"agent_type": agent_type, "confidence": 0.8}
                    )
                    routing_documents.append(doc)
            
            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=routing_documents,
                embedding=self.embeddings,
                collection_name="agricultural_routing"
            )
            
            logger.info(f"Created routing vectorstore with {len(routing_documents)} examples")
            
        except Exception as e:
            logger.error(f"Failed to create routing vectorstore: {e}")
            raise
    
    def _generate_routing_examples(self, agent_type: str, config: Dict[str, Any]) -> List[str]:
        """Generate example queries for agent type"""
        examples = {
            "weather": [
                "Quelles sont les prévisions météo pour cette semaine?",
                "Puis-je traiter avec ce vent?",
                "Risque de pluie dans les prochaines heures?",
                "Conditions météo pour pulvérisation",
                "Fenêtre d'application optimale"
            ],
            "regulatory": [
                "Ce produit est-il autorisé sur blé?",
                "Quelle est la ZNT pour ce fongicide?",
                "Délai avant récolte pour ce traitement?",
                "Usage autorisé de ce produit phytosanitaire",
                "Conformité réglementaire de cette intervention"
            ],
            "pest_disease": [
                "Diagnostic de cette maladie sur mes cultures",
                "Quel traitement contre ce ravageur?",
                "Identifier ces symptômes sur les feuilles",
                "Lutte contre les pucerons",
                "Traitement préventif des maladies"
            ],
            "planning": [
                "Planification de mes traitements",
                "Calendrier cultural pour cette saison",
                "Programme de fertilisation",
                "Rotation des cultures optimale",
                "Stratégie d'intervention intégrée"
            ],
            "farm_management": [
                "Analyse de rendement de mes parcelles",
                "Gestion économique de l'exploitation",
                "Suivi des interventions réalisées",
                "Optimisation des coûts de production",
                "Performance de mes cultures"
            ]
        }
        
        return examples.get(agent_type, [])
    
    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Route query to appropriate agent with confidence scoring"""
        try:
            # Check cache first
            cache_key = f"{query}_{str(context)}"
            if cache_key in self.routing_cache:
                return self.routing_cache[cache_key]
            
            # Multi-method routing analysis
            routing_results = await self._analyze_routing_multi_method(query, context)
            
            # Cache result
            self.routing_cache[cache_key] = routing_results
            
            # Limit cache size
            if len(self.routing_cache) > 1000:
                # Remove oldest entries
                oldest_keys = list(self.routing_cache.keys())[:100]
                for key in oldest_keys:
                    del self.routing_cache[key]
            
            return routing_results
            
        except Exception as e:
            logger.error(f"Query routing failed: {e}")
            return {
                "primary_agent": "general",
                "confidence": 0.5,
                "secondary_agents": [],
                "routing_explanation": f"Routing failed: {str(e)}",
                "metadata": {"error": str(e)}
            }
    
    async def _analyze_routing_multi_method(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze routing using multiple methods and combine results"""
        
        # Method 1: Keyword-based routing
        keyword_results = self._route_by_keywords(query)
        
        # Method 2: Pattern-based routing
        pattern_results = self._route_by_patterns(query)
        
        # Method 3: Semantic similarity routing
        semantic_results = await self._route_by_semantic_similarity(query)
        
        # Method 4: LLM-based routing
        llm_results = await self._route_by_llm_analysis(query, context)
        
        # Combine and weight results
        combined_results = self._combine_routing_results([
            ("keyword", keyword_results, 0.2),
            ("pattern", pattern_results, 0.25),
            ("semantic", semantic_results, 0.3),
            ("llm", llm_results, 0.25)
        ])
        
        return combined_results

    def _route_by_keywords(self, query: str) -> Dict[str, float]:
        """Route query based on keyword matching"""
        query_lower = query.lower()
        scores = {}

        for agent_type, config in self.agent_patterns.items():
            score = 0.0
            keyword_matches = 0

            for keyword in config["keywords"]:
                if keyword.lower() in query_lower:
                    score += 1.0
                    keyword_matches += 1

            # Normalize score
            if config["keywords"]:
                scores[agent_type] = (score / len(config["keywords"])) + (config.get("confidence_boost", 0) * keyword_matches)

        return scores

    def _route_by_patterns(self, query: str) -> Dict[str, float]:
        """Route query based on regex pattern matching"""
        query_lower = query.lower()
        scores = {}

        for agent_type, config in self.agent_patterns.items():
            score = 0.0

            for pattern in config.get("patterns", []):
                if re.search(pattern, query_lower):
                    score += 1.0

            # Normalize and boost
            if config.get("patterns"):
                scores[agent_type] = (score / len(config["patterns"])) + config.get("confidence_boost", 0)

        return scores

    async def _route_by_semantic_similarity(self, query: str) -> Dict[str, float]:
        """Route query based on semantic similarity"""
        try:
            if not self.vectorstore:
                return {}

            # Search for similar routing examples
            similar_docs = self.vectorstore.similarity_search_with_score(query, k=10)

            scores = {}
            for doc, similarity_score in similar_docs:
                agent_type = doc.metadata.get("agent_type")
                if agent_type:
                    if agent_type not in scores:
                        scores[agent_type] = 0.0
                    scores[agent_type] += similarity_score * doc.metadata.get("confidence", 0.5)

            # Normalize scores
            if scores:
                max_score = max(scores.values())
                if max_score > 0:
                    scores = {k: v / max_score for k, v in scores.items()}

            return scores

        except Exception as e:
            logger.error(f"Semantic similarity routing failed: {e}")
            return {}

    async def _route_by_llm_analysis(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Route query using LLM analysis"""
        try:
            routing_prompt = ChatPromptTemplate.from_template("""
            Analysez cette requête agricole et déterminez le type d'agent le plus approprié:

            Requête: {query}
            Contexte: {context}

            Types d'agents disponibles:
            - weather: Questions météorologiques et conditions d'application
            - regulatory: Conformité réglementaire, AMM, ZNT, autorisations
            - pest_disease: Diagnostic et traitement des maladies/ravageurs
            - planning: Planification culturale et calendriers d'intervention
            - farm_management: Gestion d'exploitation et analyse de performance

            Répondez au format JSON:
            {{
                "primary_agent": "type_agent",
                "confidence": 0.0-1.0,
                "reasoning": "explication du choix",
                "secondary_options": ["agent2", "agent3"]
            }}
            """)

            llm_chain = LLMChain(llm=self.llm, prompt=routing_prompt)
            result = llm_chain.run(query=query, context=str(context or {}))

            try:
                parsed_result = json.loads(result)

                scores = {}
                primary_agent = parsed_result.get("primary_agent")
                confidence = parsed_result.get("confidence", 0.5)

                if primary_agent:
                    scores[primary_agent] = confidence

                # Add secondary options with lower scores
                for secondary in parsed_result.get("secondary_options", []):
                    if secondary not in scores:
                        scores[secondary] = confidence * 0.6

                return scores

            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM routing result")
                return {}

        except Exception as e:
            logger.error(f"LLM routing analysis failed: {e}")
            return {}

    def _combine_routing_results(self, method_results: List[Tuple[str, Dict[str, float], float]]) -> Dict[str, Any]:
        """Combine routing results from multiple methods"""

        # Aggregate weighted scores
        combined_scores = {}
        method_details = {}

        for method_name, scores, weight in method_results:
            method_details[method_name] = scores

            for agent_type, score in scores.items():
                if agent_type not in combined_scores:
                    combined_scores[agent_type] = 0.0
                combined_scores[agent_type] += score * weight

        if not combined_scores:
            return {
                "primary_agent": "general",
                "confidence": 0.5,
                "secondary_agents": [],
                "routing_explanation": "No clear routing preference found",
                "metadata": {"method_details": method_details}
            }

        # Sort agents by score
        sorted_agents = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        primary_agent = sorted_agents[0][0]
        primary_confidence = sorted_agents[0][1]

        # Get secondary agents (score > 0.3 of primary)
        threshold = primary_confidence * 0.3
        secondary_agents = [
            agent for agent, score in sorted_agents[1:]
            if score > threshold
        ]

        # Generate explanation
        explanation = self._generate_routing_explanation(
            primary_agent, primary_confidence, method_details
        )

        return {
            "primary_agent": primary_agent,
            "confidence": min(primary_confidence, 1.0),
            "secondary_agents": secondary_agents[:3],  # Limit to top 3
            "routing_explanation": explanation,
            "metadata": {
                "all_scores": combined_scores,
                "method_details": method_details,
                "routing_methods_used": len(method_results)
            }
        }

    def _generate_routing_explanation(
        self,
        primary_agent: str,
        confidence: float,
        method_details: Dict[str, Dict[str, float]]
    ) -> str:
        """Generate human-readable routing explanation"""

        agent_descriptions = {
            "weather": "agent météorologique pour les conditions d'application",
            "regulatory": "agent réglementaire pour la conformité phytosanitaire",
            "pest_disease": "agent de diagnostic pour les maladies et ravageurs",
            "planning": "agent de planification pour les calendriers culturaux",
            "farm_management": "agent de gestion pour l'analyse d'exploitation",
            "general": "agent généraliste pour les questions diverses"
        }

        description = agent_descriptions.get(primary_agent, "agent spécialisé")

        # Find strongest contributing method
        strongest_method = ""
        strongest_score = 0.0

        for method, scores in method_details.items():
            if primary_agent in scores and scores[primary_agent] > strongest_score:
                strongest_score = scores[primary_agent]
                strongest_method = method

        method_names = {
            "keyword": "analyse des mots-clés",
            "pattern": "reconnaissance de motifs",
            "semantic": "similarité sémantique",
            "llm": "analyse par IA"
        }

        method_desc = method_names.get(strongest_method, "analyse combinée")

        return f"Routage vers {description} (confiance: {confidence:.2f}) basé principalement sur {method_desc}"
