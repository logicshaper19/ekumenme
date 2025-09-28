"""
Vector Database Interface for Nutrient Deficiency Knowledge

This module provides an interface for future vector database integration.
It abstracts the knowledge base operations to allow seamless migration
from JSON files to vector databases like Pinecone, Weaviate, or Chroma.
"""

from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class NutrientKnowledge:
    """Structured nutrient knowledge for vector storage."""
    crop_type: str
    nutrient: str
    nutrient_name: str
    symbol: str
    symptoms: List[str]
    soil_indicators: List[str]
    treatment: List[str]
    prevention: List[str]
    dosage_guidelines: Dict[str, str]
    critical_stages: List[str]
    deficiency_level: str
    embedding_vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SearchResult:
    """Search result from vector database."""
    nutrient_knowledge: NutrientKnowledge
    similarity_score: float
    match_type: str  # "symptom", "soil", "treatment", "general"

class KnowledgeBaseInterface(ABC):
    """Abstract interface for knowledge base operations."""
    
    @abstractmethod
    async def search_by_symptoms(
        self, 
        symptoms: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search nutrient knowledge by symptoms."""
        pass
    
    @abstractmethod
    async def search_by_soil_conditions(
        self, 
        soil_conditions: Dict[str, Any], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search nutrient knowledge by soil conditions."""
        pass
    
    @abstractmethod
    async def get_crop_nutrients(
        self, 
        crop_type: str
    ) -> List[NutrientKnowledge]:
        """Get all nutrient knowledge for a specific crop."""
        pass
    
    @abstractmethod
    async def add_nutrient_knowledge(
        self, 
        knowledge: NutrientKnowledge
    ) -> bool:
        """Add new nutrient knowledge."""
        pass
    
    @abstractmethod
    async def update_nutrient_knowledge(
        self, 
        crop_type: str, 
        nutrient: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing nutrient knowledge."""
        pass

class JSONKnowledgeBase(KnowledgeBaseInterface):
    """JSON-based knowledge base implementation (current)."""
    
    def __init__(self, knowledge_file_path: str):
        self.knowledge_file_path = knowledge_file_path
        self._knowledge_cache: Optional[Dict[str, Any]] = None
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """Load knowledge from JSON file."""
        if self._knowledge_cache is not None:
            return self._knowledge_cache
        
        try:
            with open(self.knowledge_file_path, 'r', encoding='utf-8') as f:
                self._knowledge_cache = json.load(f)
            logger.info(f"Loaded knowledge base from {self.knowledge_file_path}")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self._knowledge_cache = {}
        
        return self._knowledge_cache
    
    async def search_by_symptoms(
        self, 
        symptoms: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search nutrient knowledge by symptoms."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        search_crops = [crop_type] if crop_type else list(crops.keys())
        
        for crop in search_crops:
            if crop not in crops:
                continue
                
            nutrients = crops[crop].get("nutrients", {})
            for nutrient_key, nutrient_info in nutrients.items():
                nutrient_symptoms = nutrient_info.get("symptoms", [])
                
                # Calculate symptom match
                matches = [s for s in symptoms if s in nutrient_symptoms]
                if matches:
                    similarity_score = len(matches) / len(nutrient_symptoms) if nutrient_symptoms else 0
                    
                    nutrient_knowledge = NutrientKnowledge(
                        crop_type=crop,
                        nutrient=nutrient_key,
                        nutrient_name=nutrient_info.get("name", nutrient_key),
                        symbol=nutrient_info.get("symbol", ""),
                        symptoms=nutrient_symptoms,
                        soil_indicators=nutrient_info.get("soil_indicators", []),
                        treatment=nutrient_info.get("treatment", []),
                        prevention=nutrient_info.get("prevention", []),
                        dosage_guidelines=nutrient_info.get("dosage_guidelines", {}),
                        critical_stages=nutrient_info.get("critical_stages", []),
                        deficiency_level=nutrient_info.get("deficiency_level", "moderate")
                    )
                    
                    results.append(SearchResult(
                        nutrient_knowledge=nutrient_knowledge,
                        similarity_score=similarity_score,
                        match_type="symptom"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_soil_conditions(
        self, 
        soil_conditions: Dict[str, Any], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search nutrient knowledge by soil conditions."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        search_crops = [crop_type] if crop_type else list(crops.keys())
        
        for crop in search_crops:
            if crop not in crops:
                continue
                
            nutrients = crops[crop].get("nutrients", {})
            for nutrient_key, nutrient_info in nutrients.items():
                soil_indicators = nutrient_info.get("soil_indicators", [])
                
                # Calculate soil match
                matches = [s for s in soil_conditions.keys() if s in soil_indicators]
                if matches:
                    similarity_score = len(matches) / len(soil_indicators) if soil_indicators else 0
                    
                    nutrient_knowledge = NutrientKnowledge(
                        crop_type=crop,
                        nutrient=nutrient_key,
                        nutrient_name=nutrient_info.get("name", nutrient_key),
                        symbol=nutrient_info.get("symbol", ""),
                        symptoms=nutrient_info.get("symptoms", []),
                        soil_indicators=soil_indicators,
                        treatment=nutrient_info.get("treatment", []),
                        prevention=nutrient_info.get("prevention", []),
                        dosage_guidelines=nutrient_info.get("dosage_guidelines", {}),
                        critical_stages=nutrient_info.get("critical_stages", []),
                        deficiency_level=nutrient_info.get("deficiency_level", "moderate")
                    )
                    
                    results.append(SearchResult(
                        nutrient_knowledge=nutrient_knowledge,
                        similarity_score=similarity_score,
                        match_type="soil"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def get_crop_nutrients(
        self, 
        crop_type: str
    ) -> List[NutrientKnowledge]:
        """Get all nutrient knowledge for a specific crop."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        if crop_type not in crops:
            return results
        
        nutrients = crops[crop_type].get("nutrients", {})
        for nutrient_key, nutrient_info in nutrients.items():
            nutrient_knowledge = NutrientKnowledge(
                crop_type=crop_type,
                nutrient=nutrient_key,
                nutrient_name=nutrient_info.get("name", nutrient_key),
                symbol=nutrient_info.get("symbol", ""),
                symptoms=nutrient_info.get("symptoms", []),
                soil_indicators=nutrient_info.get("soil_indicators", []),
                treatment=nutrient_info.get("treatment", []),
                prevention=nutrient_info.get("prevention", []),
                dosage_guidelines=nutrient_info.get("dosage_guidelines", {}),
                critical_stages=nutrient_info.get("critical_stages", []),
                deficiency_level=nutrient_info.get("deficiency_level", "moderate")
            )
            results.append(nutrient_knowledge)
        
        return results
    
    async def add_nutrient_knowledge(
        self, 
        knowledge: NutrientKnowledge
    ) -> bool:
        """Add new nutrient knowledge (not implemented for JSON)."""
        logger.warning("Adding nutrient knowledge not supported in JSON mode")
        return False
    
    async def update_nutrient_knowledge(
        self, 
        crop_type: str, 
        nutrient: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing nutrient knowledge (not implemented for JSON)."""
        logger.warning("Updating nutrient knowledge not supported in JSON mode")
        return False

class VectorKnowledgeBase(KnowledgeBaseInterface):
    """
    Vector database implementation (future).
    
    This class will be implemented when vector database integration is added.
    It will use embeddings to perform semantic search on nutrient knowledge.
    """
    
    def __init__(self, vector_db_config: Dict[str, Any]):
        self.config = vector_db_config
        self.embedding_model = None  # Will be initialized with actual embedding model
        self.vector_db = None  # Will be initialized with actual vector database
    
    async def search_by_symptoms(
        self, 
        symptoms: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search nutrient knowledge by symptoms using vector similarity."""
        # TODO: Implement vector-based symptom search
        # 1. Generate embeddings for symptoms
        # 2. Search vector database for similar nutrient knowledge
        # 3. Return ranked results
        logger.info("Vector-based symptom search not yet implemented")
        return []
    
    async def search_by_soil_conditions(
        self, 
        soil_conditions: Dict[str, Any], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search nutrient knowledge by soil conditions using vector similarity."""
        # TODO: Implement vector-based soil condition search
        logger.info("Vector-based soil condition search not yet implemented")
        return []
    
    async def get_crop_nutrients(
        self, 
        crop_type: str
    ) -> List[NutrientKnowledge]:
        """Get all nutrient knowledge for a specific crop."""
        # TODO: Implement vector-based crop nutrient retrieval
        logger.info("Vector-based crop nutrient retrieval not yet implemented")
        return []
    
    async def add_nutrient_knowledge(
        self, 
        knowledge: NutrientKnowledge
    ) -> bool:
        """Add new nutrient knowledge to vector database."""
        # TODO: Implement vector-based knowledge addition
        # 1. Generate embeddings for the knowledge
        # 2. Store in vector database
        logger.info("Vector-based knowledge addition not yet implemented")
        return False
    
    async def update_nutrient_knowledge(
        self, 
        crop_type: str, 
        nutrient: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing nutrient knowledge in vector database."""
        # TODO: Implement vector-based knowledge update
        logger.info("Vector-based knowledge update not yet implemented")
        return False

class KnowledgeBaseFactory:
    """Factory for creating knowledge base instances."""
    
    @staticmethod
    def create_knowledge_base(
        backend_type: str = "json",
        config: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBaseInterface:
        """
        Create knowledge base instance based on backend type.
        
        Args:
            backend_type: "json" or "vector"
            config: Configuration for the knowledge base
        """
        if backend_type == "json":
            knowledge_file = config.get("knowledge_file") if config else None
            if not knowledge_file:
                # Default path
                current_dir = Path(__file__).parent
                knowledge_file = str(current_dir / "nutrient_deficiency_knowledge.json")
            return JSONKnowledgeBase(knowledge_file)
        
        elif backend_type == "vector":
            if not config:
                raise ValueError("Vector database configuration required")
            return VectorKnowledgeBase(config)
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

# Global knowledge base instance
_knowledge_base: Optional[KnowledgeBaseInterface] = None

def get_knowledge_base() -> KnowledgeBaseInterface:
    """Get global knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBaseFactory.create_knowledge_base()
    return _knowledge_base

def set_knowledge_base(knowledge_base: KnowledgeBaseInterface):
    """Set global knowledge base instance."""
    global _knowledge_base
    _knowledge_base = knowledge_base

def reset_knowledge_base():
    """Reset global knowledge base instance."""
    global _knowledge_base
    _knowledge_base = None
