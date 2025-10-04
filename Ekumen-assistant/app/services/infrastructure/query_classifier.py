"""
Query Complexity Classifier
Leverages LangChain for intelligent query classification
"""

import re
import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QueryComplexity(BaseModel):
    """Structured output for query complexity classification"""
    complexity: str = Field(description="Query complexity: 'simple', 'medium', or 'complex'")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    query_type: str = Field(description="Type of query: 'weather_info', 'cultivation_advice', 'planning', etc.")
    reasoning: str = Field(description="Brief explanation of classification")
    requires_full_structure: bool = Field(description="Whether full 6-section response is needed")


class QueryComplexityClassifier:
    """
    Classify query complexity using multiple methods:
    1. Pattern-based (fast, rule-based)
    2. LangChain LLM-based (intelligent, context-aware)
    """
    
    # Simple query patterns (informational, direct answer)
    SIMPLE_PATTERNS = {
        "weather_info": [
            r"quelle.*météo",
            r"quel.*temps",
            r"prévision",
            r"va.*pleuvoir",
            r"température",
            r"combien.*degré",
            r"conditions.*météo"
        ],
        "simple_question": [
            r"c'est quoi",
            r"qu'est-ce que",
            r"définition",
            r"signifie"
        ],
        "status_check": [
            r"état.*culture",
            r"situation.*parcelle",
            r"niveau.*stock"
        ]
    }
    
    # Complex query patterns (planning, advice, multi-step)
    COMPLEX_PATTERNS = {
        "cultivation": [
            r"(planter|cultiver|culture de)",
            r"comment.*faire.*pousser",
            r"réussir.*culture",
            r"démarrer.*plantation"
        ],
        "planning": [
            r"comment.*faire",
            r"étapes.*pour",
            r"planifier",
            r"organiser",
            r"programme"
        ],
        "advice": [
            r"recommand",
            r"conseil",
            r"suggère",
            r"que.*faire",
            r"meilleure.*façon"
        ],
        "comparison": [
            r"choisir",
            r"meilleur",
            r"comparer",
            r"différence.*entre",
            r"alternative"
        ],
        "problem_solving": [
            r"problème",
            r"maladie",
            r"ravageur",
            r"traiter",
            r"solution"
        ]
    }
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize classifier
        
        Args:
            use_llm: Whether to use LangChain LLM for classification (more accurate but slower)
        """
        self.use_llm = use_llm
        self.llm = None
        self.parser = None
        self.classification_prompt = None
        
        if use_llm:
            self._initialize_llm_classifier()
    
    def _initialize_llm_classifier(self):
        """Initialize LangChain LLM-based classifier"""
        try:
            from app.core.config import settings
            
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",  # Fast and cheap for classification
                temperature=0.0,  # Deterministic
                api_key=settings.OPENAI_API_KEY
            )
            
            self.parser = PydanticOutputParser(pydantic_object=QueryComplexity)
            
            self.classification_prompt = ChatPromptTemplate.from_messages([
                ("system", """Tu es un classificateur de requêtes agricoles. 
                
Classifie les requêtes en 3 niveaux de complexité:

**SIMPLE** (requires_full_structure=False):
- Questions informatives directes (météo, température, définition)
- Requêtes de statut (état d'une culture, niveau de stock)
- Questions oui/non
- Réponse attendue: 3-5 phrases

**MEDIUM** (requires_full_structure=False):
- Questions avec contexte modéré
- Comparaisons simples
- Conseils ponctuels
- Réponse attendue: 1-2 paragraphes

**COMPLEX** (requires_full_structure=True):
- Planification de culture (planter, cultiver)
- Conseils multi-étapes
- Résolution de problèmes
- Analyses comparatives détaillées
- Réponse attendue: Guide complet avec structure

{format_instructions}"""),
                ("human", "Requête: {query}")
            ])
            
            logger.info("LLM-based query classifier initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize LLM classifier: {e}. Using pattern-based only.")
            self.use_llm = False
    
    def classify(self, query: str, use_llm: Optional[bool] = None) -> Dict[str, Any]:
        """
        Classify query complexity
        
        Args:
            query: User query to classify
            use_llm: Override instance setting for LLM usage
            
        Returns:
            Dict with complexity, confidence, query_type, reasoning, requires_full_structure
        """
        # Use pattern-based classification first (fast)
        pattern_result = self._classify_by_patterns(query)
        
        # If LLM is available and requested, use it for better accuracy
        if (use_llm if use_llm is not None else self.use_llm) and self.llm:
            try:
                llm_result = self._classify_by_llm(query)
                # Combine results (LLM has higher weight)
                return self._combine_classifications(pattern_result, llm_result, llm_weight=0.7)
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}. Using pattern-based result.")
                return pattern_result
        
        return pattern_result
    
    def _classify_by_patterns(self, query: str) -> Dict[str, Any]:
        """Fast pattern-based classification"""
        query_lower = query.lower()
        
        # Check simple patterns
        simple_matches = []
        for category, patterns in self.SIMPLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    simple_matches.append(category)
                    break
        
        # Check complex patterns
        complex_matches = []
        for category, patterns in self.COMPLEX_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    complex_matches.append(category)
                    break
        
        # Determine complexity
        if complex_matches:
            complexity = "complex"
            confidence = 0.8
            query_type = complex_matches[0]
            requires_full_structure = True
            reasoning = f"Matched complex patterns: {', '.join(complex_matches)}"
        elif simple_matches:
            complexity = "simple"
            confidence = 0.85
            query_type = simple_matches[0]
            requires_full_structure = False
            reasoning = f"Matched simple patterns: {', '.join(simple_matches)}"
        else:
            # Default to medium if no clear match
            complexity = "medium"
            confidence = 0.6
            query_type = "general_inquiry"
            requires_full_structure = False
            reasoning = "No clear pattern match, defaulting to medium complexity"
        
        return {
            "complexity": complexity,
            "confidence": confidence,
            "query_type": query_type,
            "reasoning": reasoning,
            "requires_full_structure": requires_full_structure,
            "method": "pattern_based"
        }
    
    def _classify_by_llm(self, query: str) -> Dict[str, Any]:
        """LangChain LLM-based classification (more accurate)"""
        try:
            # Create prompt with format instructions
            prompt = self.classification_prompt.format_messages(
                query=query,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            
            # Parse structured output
            result = self.parser.parse(response.content)
            
            return {
                "complexity": result.complexity,
                "confidence": result.confidence,
                "query_type": result.query_type,
                "reasoning": result.reasoning,
                "requires_full_structure": result.requires_full_structure,
                "method": "llm_based"
            }
            
        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            raise
    
    def _combine_classifications(
        self,
        pattern_result: Dict[str, Any],
        llm_result: Dict[str, Any],
        llm_weight: float = 0.7
    ) -> Dict[str, Any]:
        """Combine pattern and LLM results with weighted confidence"""
        
        # If both agree, high confidence
        if pattern_result["complexity"] == llm_result["complexity"]:
            return {
                **llm_result,
                "confidence": min(0.95, (pattern_result["confidence"] + llm_result["confidence"]) / 2 + 0.1),
                "method": "combined_agreement"
            }
        
        # If they disagree, use LLM result but lower confidence
        return {
            **llm_result,
            "confidence": llm_result["confidence"] * 0.8,
            "method": "combined_llm_priority",
            "reasoning": f"LLM: {llm_result['reasoning']} | Pattern: {pattern_result['reasoning']}"
        }


# Singleton instance
_classifier_instance = None

def get_classifier(use_llm: bool = True) -> QueryComplexityClassifier:
    """Get or create classifier instance"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = QueryComplexityClassifier(use_llm=use_llm)
    return _classifier_instance

