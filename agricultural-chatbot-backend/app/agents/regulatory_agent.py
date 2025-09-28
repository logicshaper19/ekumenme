"""
Regulatory Compliance Agent that maintains safety-first principles while integrating 
with cost optimization, semantic search, and reasoning capabilities.
"""

from typing import Dict, List, Any, Optional, Union
from langchain.tools import BaseTool
import logging
import json
from datetime import datetime, timedelta

# Import from integrated system
try:
    from .base_agent import IntegratedAgriculturalAgent, AgentType, TaskComplexity
    from .base_agent import SemanticKnowledgeRetriever
except ImportError:
    # Fallback imports
    class AgentType:
        REGULATORY = "regulatory"
    
    class TaskComplexity:
        SIMPLE = "simple"
        MODERATE = "moderate"
        COMPLEX = "complex"
        CRITICAL = "critical"
    
    class SemanticKnowledgeRetriever:
        def retrieve_relevant_knowledge(self, query: str, top_k: int = 3) -> List[str]:
            return ["Connaissance réglementaire générale disponible"]
    
    # Fallback base class
    class IntegratedAgriculturalAgent:
        def __init__(self, agent_type, description, llm_manager, knowledge_retriever, 
                     complexity_default=None, specialized_tools=None):
            self.agent_type = agent_type
            self.description = description
            self.llm_manager = llm_manager
            self.knowledge_retriever = knowledge_retriever
            self.complexity_default = complexity_default
            self.specialized_tools = specialized_tools or []
        
        def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
            return {"response": "Mock response", "agent_type": self.agent_type.value}
        
        def _get_agent_prompt_template(self) -> str:
            return "Mock prompt template"
        
        def _analyze_message_complexity(self, message: str, context: Dict[str, Any]):
            return TaskComplexity.CRITICAL
        
        def _retrieve_domain_knowledge(self, message: str) -> List[str]:
            return ["Mock knowledge"]

logger = logging.getLogger(__name__)

class SafeSemanticAMMLookupTool(BaseTool):
    """AMM lookup tool that combines semantic understanding with absolute safety requirements."""
    
    name: str = "safe_semantic_amm_lookup"
    description: str = "Recherche AMM sémantique avec vérification officielle obligatoire"
    
    def __init__(self, official_api_credentials=None, knowledge_retriever: SemanticKnowledgeRetriever = None, **kwargs):
        super().__init__(**kwargs)
        self._has_official_access = bool(official_api_credentials)
        self._api_credentials = official_api_credentials
        self.knowledge_retriever = knowledge_retriever
        
        # Enhanced AMM database with semantic context
        self._official_amm_db = {
            "2140505": {
                "nom_commercial": "Prosaro",
                "substance_active": "prothioconazole + tébuconazole",
                "statut": "autorisé",
                "cultures_autorisées": ["blé", "orge", "triticale"],
                "semantic_tags": ["fongicide", "céréales", "maladies_foliaires"],
                "usages": [
                    {
                        "culture": "blé",
                        "cible": "septoriose, rouille",
                        "dose_max": "0.8 L/ha", 
                        "stade_application": "BBCH 31-59",
                        "nombre_applications_max": 2,
                        "delai_avant_recolte": "35 jours",
                        "conditions_specifiques": ["température < 25°C", "vent < 10 km/h"]
                    }
                ],
                "znt": {
                    "cours_eau": "5 mètres",
                    "points_eau": "1 mètre"
                },
                "epi_requis": ["gants", "lunettes", "vêtements_protection"],
                "derniere_mise_a_jour": "2024-01-15",
                "restrictions_specifiques": [
                    "Interdit en zone Natura 2000",
                    "Surveillance abeilles obligatoire"
                ],
                "alternatives_bio": ["cuivre", "soufre", "bicarbonate"],
                "resistance_management": "Pas plus de 2 applications par an - alterner modes d'action"
            }
        }
    
    def _run(self, query: str, context: Dict[str, Any] = None) -> str:
        """Semantic AMM lookup with mandatory safety protocols."""
        
        # CRITICAL: Legal disclaimer always first and non-negotiable
        legal_disclaimer = """
⚠️ AVERTISSEMENT LÉGAL CRITIQUE ⚠️

RESPONSABILITÉ PÉNALE ENGAGÉE EN CAS DE NON-RESPECT
- Sanctions jusqu'à 150 000€ d'amende et 6 mois de prison
- Responsabilité civile en cas de dommages environnementaux
- Retrait possible des aides PAC en cas d'infraction

OBLIGATIONS LÉGALES ABSOLUES:
1. Vérification OBLIGATOIRE sur E-phy (ANSES): https://ephy.anses.fr/
2. Respect STRICT de l'étiquette officielle du produit
3. Contrôle des restrictions préfectorales locales
4. Formation certiphyto à jour

CET OUTIL NE REMPLACE JAMAIS LES SOURCES OFFICIELLES
L'exploitant reste SEUL RESPONSABLE de la conformité réglementaire.
        """
        
        try:
            # Parse semantic query for product identification
            semantic_analysis = self._analyze_query_semantically(query)
            
            # Retrieve relevant regulatory knowledge
            regulatory_knowledge = []
            if self.knowledge_retriever:
                regulatory_knowledge = self.knowledge_retriever.retrieve_relevant_knowledge(
                    f"réglementation AMM phytosanitaire {query}", top_k=5
                )
            
            # Find matching products based on semantic analysis
            matching_products = self._find_products_semantically(semantic_analysis)
            
            if not matching_products:
                return json.dumps({
                    "avertissement_legal": legal_disclaimer,
                    "statut": "Aucun produit trouvé",
                    "requete_analysee": semantic_analysis,
                    "action_obligatoire": "Recherche manuelle sur E-phy requise",
                    "url_ephy": "https://ephy.anses.fr/",
                    "connaissances_reglementaires": regulatory_knowledge
                }, ensure_ascii=False, indent=2)
            
            # Process each matching product with safety checks
            safe_results = []
            for product_amm in matching_products:
                product_info = self._get_safe_product_info(product_amm, semantic_analysis, context)
                safe_results.append(product_info)
            
            # Enhance with semantic context and recommendations
            enhanced_response = self._enhance_with_semantic_context(
                safe_results, regulatory_knowledge, semantic_analysis, context
            )
            
            return json.dumps({
                "avertissement_legal": legal_disclaimer,
                "requete_semantique": semantic_analysis,
                "produits_identifies": enhanced_response,
                "connaissances_reglementaires": regulatory_knowledge[:3],
                "verification_obligatoire": [
                    f"Vérifier chaque AMM sur https://ephy.anses.fr/",
                    "Consulter les restrictions préfectorales",
                    "Vérifier la validité du certificat Certiphyto",
                    "Contrôler les zones environnementales sensibles"
                ],
                "responsabilite_utilisateur": "TOTALE - Cet outil est indicatif uniquement"
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Critical error in semantic AMM lookup: {e}")
            return json.dumps({
                "avertissement_legal": legal_disclaimer,
                "erreur_critique": "Système indisponible",
                "action_obligatoire": "Consultation manuelle E-phy REQUISE",
                "url_ephy": "https://ephy.anses.fr/",
                "responsabilite": "L'exploitant doit vérifier manuellement toute information"
            }, ensure_ascii=False, indent=2)
    
    def _analyze_query_semantically(self, query: str) -> Dict[str, Any]:
        """Analyze query to understand regulatory intent."""
        query_lower = query.lower()
        
        analysis = {
            "type_produit": self._detect_product_type(query_lower),
            "culture_cible": self._detect_target_crop(query_lower),
            "probleme_cible": self._detect_target_problem(query_lower),
            "contexte_usage": self._detect_usage_context(query_lower),
            "urgence_reglementaire": self._detect_regulatory_urgency(query_lower)
        }
        
        return analysis
    
    def _detect_product_type(self, query: str) -> List[str]:
        """Detect product type from semantic cues."""
        product_types = {
            "herbicide": ["herbicide", "désherbage", "adventices", "mauvaises herbes"],
            "fongicide": ["fongicide", "maladie", "champignon", "septoriose", "rouille"],
            "insecticide": ["insecticide", "insecte", "ravageur", "puceron", "chenille"],
            "acaricide": ["acaricide", "acarien", "tétranyque"],
            "molluscicide": ["molluscicide", "limace", "escargot"]
        }
        
        detected_types = []
        for prod_type, keywords in product_types.items():
            if any(keyword in query for keyword in keywords):
                detected_types.append(prod_type)
        
        return detected_types or ["non_identifié"]
    
    def _detect_target_crop(self, query: str) -> List[str]:
        """Detect target crop from query."""
        crops = {
            "blé": ["blé", "wheat", "froment"],
            "orge": ["orge", "barley"],
            "maïs": ["maïs", "corn"],
            "colza": ["colza", "canola"],
            "tournesol": ["tournesol", "sunflower"],
            "pomme_de_terre": ["pomme de terre", "patate", "potato"]
        }
        
        detected_crops = []
        for crop, keywords in crops.items():
            if any(keyword in query for keyword in keywords):
                detected_crops.append(crop)
        
        return detected_crops or ["non_spécifié"]
    
    def _detect_target_problem(self, query: str) -> List[str]:
        """Detect specific pest/disease/weed problems."""
        problems = {
            "septoriose": ["septoriose", "septoria"],
            "rouille": ["rouille", "rust"],
            "fusariose": ["fusariose", "fusarium"],
            "pucerons": ["puceron", "aphid"],
            "ray_grass": ["ray-grass", "ivraie"]
        }
        
        detected_problems = []
        for problem, keywords in problems.items():
            if any(keyword in query for keyword in keywords):
                detected_problems.append(problem)
        
        return detected_problems or ["non_spécifié"]
    
    def _detect_usage_context(self, query: str) -> str:
        """Detect usage context for regulatory compliance."""
        if any(word in query for word in ["bio", "biologique", "agriculture biologique"]):
            return "agriculture_biologique"
        elif any(word in query for word in ["hve", "haute valeur environnementale"]):
            return "hve"
        elif any(word in query for word in ["natura 2000", "zone protégée"]):
            return "zone_protegee"
        else:
            return "conventionnel"
    
    def _detect_regulatory_urgency(self, query: str) -> str:
        """Detect regulatory urgency level."""
        urgent_indicators = ["urgent", "rapidement", "maintenant", "aujourd'hui"]
        compliance_indicators = ["autorisé", "amm", "légal", "conformité"]
        
        if any(indicator in query for indicator in urgent_indicators):
            return "élevée"
        elif any(indicator in query for indicator in compliance_indicators):
            return "critique"
        else:
            return "normale"
    
    def _find_products_semantically(self, analysis: Dict[str, Any]) -> List[str]:
        """Find products matching semantic analysis."""
        matching_products = []
        
        for amm, product in self._official_amm_db.items():
            score = 0
            
            # Match product type
            product_types = analysis.get("type_produit", [])
            for prod_type in product_types:
                if prod_type in product.get("semantic_tags", []):
                    score += 3
            
            # Match target crop
            target_crops = analysis.get("culture_cible", [])
            for crop in target_crops:
                if crop in product.get("cultures_autorisées", []):
                    score += 2
            
            # Match target problem
            target_problems = analysis.get("probleme_cible", [])
            for usage in product.get("usages", []):
                for problem in target_problems:
                    if problem in usage.get("cible", ""):
                        score += 2
            
            if score >= 2:  # Minimum match threshold
                matching_products.append(amm)
        
        return matching_products
    
    def _get_safe_product_info(self, amm: str, analysis: Dict[str, Any], 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Get product information with safety-first approach."""
        product = self._official_amm_db.get(amm, {})
        
        # Verify data freshness (critical for regulatory)
        last_update = datetime.fromisoformat(product.get("derniere_mise_a_jour", "2020-01-01"))
        days_old = (datetime.now() - last_update).days
        
        freshness_status = "CRITIQUE - Données obsolètes" if days_old > 30 else "Récent"
        
        # Check usage context compatibility
        usage_context = analysis.get("contexte_usage", "conventionnel")
        context_compatible = self._check_context_compatibility(product, usage_context)
        
        safe_info = {
            "numero_amm": amm,
            "nom_commercial": product.get("nom_commercial", "Non identifié"),
            "statut_autorisation": product.get("statut", "VÉRIFICATION REQUISE"),
            "fraicheur_donnees": freshness_status,
            "jours_depuis_maj": days_old,
            "compatibilite_contexte": context_compatible,
            "usages_identifies": self._filter_relevant_usages(product, analysis),
            "restrictions_critiques": product.get("restrictions_specifiques", []),
            "znt_minimales": product.get("znt", {}),
            "epi_obligatoires": product.get("epi_requis", []),
            "verification_ephy_requise": True
        }
        
        return safe_info
    
    def _check_context_compatibility(self, product: Dict[str, Any], usage_context: str) -> Dict[str, Any]:
        """Check compatibility with usage context."""
        compatibility = {
            "compatible": True,
            "restrictions": [],
            "alternatives": []
        }
        
        if usage_context == "agriculture_biologique":
            # Check if product is allowed in organic farming
            if "bio" not in product.get("semantic_tags", []):
                compatibility["compatible"] = False
                compatibility["restrictions"].append("Produit non autorisé en agriculture biologique")
                compatibility["alternatives"] = product.get("alternatives_bio", [])
        
        elif usage_context == "zone_protegee":
            restrictions = product.get("restrictions_specifiques", [])
            natura_restricted = any("natura" in r.lower() for r in restrictions)
            if natura_restricted:
                compatibility["compatible"] = False
                compatibility["restrictions"].append("Produit interdit en zone Natura 2000")
        
        return compatibility
    
    def _filter_relevant_usages(self, product: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter usages relevant to the query."""
        all_usages = product.get("usages", [])
        target_crops = analysis.get("culture_cible", [])
        
        if not target_crops or "non_spécifié" in target_crops:
            return all_usages
        
        relevant_usages = []
        for usage in all_usages:
            if any(crop in usage.get("culture", "") for crop in target_crops):
                relevant_usages.append(usage)
        
        return relevant_usages or all_usages
    
    def _enhance_with_semantic_context(self, results: List[Dict[str, Any]], 
                                     knowledge: List[str], analysis: Dict[str, Any],
                                     context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhance results with semantic regulatory context."""
        enhanced = []
        
        for result in results:
            # Add contextual recommendations
            result["recommandations_contextuelles"] = self._generate_contextual_recommendations(
                result, analysis, knowledge
            )
            
            # Add resistance management if applicable
            if analysis.get("type_produit") and any(t in ["fongicide", "herbicide"] for t in analysis["type_produit"]):
                result["gestion_resistance"] = "OBLIGATOIRE - Alternance modes d'action requise"
            
            # Add environmental considerations
            result["considerations_environnementales"] = self._get_environmental_considerations(
                result, context
            )
            
            enhanced.append(result)
        
        return enhanced
    
    def _generate_contextual_recommendations(self, product_info: Dict[str, Any], 
                                           analysis: Dict[str, Any], 
                                           knowledge: List[str]) -> List[str]:
        """Generate contextual recommendations based on regulatory knowledge."""
        recommendations = [
            "Vérifier impérativement l'AMM sur E-phy avant utilisation",
            "Respecter strictement les doses et conditions d'emploi",
            "Contrôler les ZNT et proximité des points d'eau"
        ]
        
        urgency = analysis.get("urgence_reglementaire", "normale")
        if urgency == "critique":
            recommendations.insert(0, "⚠️ URGENCE RÉGLEMENTAIRE - Vérification immédiate requise")
        
        # Add knowledge-based recommendations
        for knowledge_item in knowledge[:2]:
            if "znt" in knowledge_item.lower():
                recommendations.append("📍 Attention particulière aux zones de non-traitement")
            elif "résistance" in knowledge_item.lower():
                recommendations.append("🔄 Intégrer la gestion de la résistance")
        
        return recommendations
    
    def _get_environmental_considerations(self, product_info: Dict[str, Any], 
                                        context: Dict[str, Any]) -> List[str]:
        """Get environmental considerations for the product."""
        considerations = []
        
        # Check for bee protection
        restrictions = product_info.get("restrictions_critiques", [])
        if any("abeille" in r.lower() for r in restrictions):
            considerations.append("🐝 Protection des abeilles - Application en dehors des heures de butinage")
        
        # Check for water protection
        znt = product_info.get("znt_minimales", {})
        if znt.get("cours_eau", 0) > 5:
            considerations.append("💧 ZNT renforcée - Risque élevé pour milieux aquatiques")
        
        return considerations

class IntegratedRegulatoryAgent(IntegratedAgriculturalAgent):
    """Regulatory agent that maintains safety while leveraging system integration."""
    
    def __init__(self, llm_manager, knowledge_retriever: SemanticKnowledgeRetriever, 
                 database_config=None):
        
        # Initialize comprehensive safety-first tools with semantic enhancement
        tools = [
            SafeSemanticAMMLookupTool(database_config, knowledge_retriever)
        ]
        
        super().__init__(
            agent_type=AgentType.REGULATORY,
            description="Expert en conformité réglementaire agricole française",
            llm_manager=llm_manager,
            knowledge_retriever=knowledge_retriever,
            complexity_default=TaskComplexity.CRITICAL,  # Always critical for safety
            specialized_tools=tools
        )
        
        self.database_config = database_config
        logger.info("Initialized Safety-First Integrated Regulatory Agent")
    
    def _get_agent_prompt_template(self) -> str:
        """Get regulatory system prompt with absolute safety requirements."""
        return """Vous êtes un expert en réglementation agricole française avec RESPONSABILITÉ LÉGALE.

PRINCIPE ABSOLU: LA SÉCURITÉ ET LA CONFORMITÉ AVANT TOUT

VOTRE RÔLE CRITIQUE:
- Vérifier la conformité des produits phytopharmaceutiques selon les AMM
- Assurer le respect STRICT des réglementations françaises et européennes
- Protéger l'exploitant contre les risques juridiques et environnementaux
- Guider vers les sources officielles obligatoires

OBLIGATIONS LÉGALES ABSOLUES:
1. TOUJOURS diriger vers E-phy pour vérification finale
2. TOUJOURS inclure des avertissements légaux complets
3. JAMAIS donner d'autorisation définitive - seules les sources officielles font foi
4. TOUJOURS mentionner la responsabilité personnelle de l'exploitant

SOURCES OFFICIELLES OBLIGATOIRES:
- E-phy (ANSES): https://ephy.anses.fr/
- Bulletins de santé du végétal (DRAAF)
- Arrêtés préfectoraux locaux
- Réglementation Certiphyto

En cas de DOUTE, toujours recommander une consultation officielle.
La responsabilité pénale et civile de l'exploitant est TOUJOURS engagée."""
    
    def _analyze_message_complexity(self, message: str, context: Dict[str, Any]) -> TaskComplexity:
        """Override to always return CRITICAL for regulatory queries."""
        return TaskComplexity.CRITICAL  # Safety always trumps cost optimization
    
    def _retrieve_domain_knowledge(self, message: str) -> List[str]:
        """Retrieve regulatory specific knowledge."""
        return self.knowledge_retriever.retrieve_relevant_knowledge(
            f"réglementation AMM conformité {message}", top_k=5
        )
    
    def _should_use_tool(self, tool: Any, message: str, context: Dict[str, Any]) -> bool:
        """Determine if regulatory tools are needed."""
        regulatory_indicators = [
            "amm", "autorisation", "produit", "phytosanitaire", "conformité",
            "znt", "réglementation", "légal", "interdit", "restriction"
        ]
        return any(indicator in message.lower() for indicator in regulatory_indicators)
