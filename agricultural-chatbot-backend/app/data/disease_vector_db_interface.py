"""
Vector Database Interface for Disease Diagnosis Knowledge

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
class DiseaseKnowledge:
    """Structured disease knowledge for vector storage."""
    crop_type: str
    disease_name: str
    scientific_name: str
    symptoms: List[str]
    environmental_conditions: Dict[str, Any]
    treatment: List[str]
    prevention: List[str]
    severity: str
    critical_stages: List[str]
    economic_threshold: str
    monitoring_methods: List[str]
    spread_conditions: Dict[str, Any]
    embedding_vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class DiseaseSearchResult:
    """Search result from vector database."""
    disease_knowledge: DiseaseKnowledge
    similarity_score: float
    match_type: str  # "symptom", "environmental", "treatment", "general"

class DiseaseKnowledgeBaseInterface(ABC):
    """Abstract interface for disease knowledge base operations."""
    
    @abstractmethod
    async def search_by_symptoms(
        self, 
        symptoms: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[DiseaseSearchResult]:
        """Search disease knowledge by symptoms."""
        pass
    
    @abstractmethod
    async def search_by_environmental_conditions(
        self, 
        environmental_conditions: Dict[str, Any], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[DiseaseSearchResult]:
        """Search disease knowledge by environmental conditions."""
        pass
    
    @abstractmethod
    async def get_crop_diseases(
        self, 
        crop_type: str
    ) -> List[DiseaseKnowledge]:
        """Get all disease knowledge for a specific crop."""
        pass
    
    @abstractmethod
    async def add_disease_knowledge(
        self, 
        knowledge: DiseaseKnowledge
    ) -> bool:
        """Add new disease knowledge."""
        pass
    
    @abstractmethod
    async def update_disease_knowledge(
        self, 
        crop_type: str, 
        disease_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing disease knowledge."""
        pass

class JSONDiseaseKnowledgeBase(DiseaseKnowledgeBaseInterface):
    """JSON-based disease knowledge base implementation (current)."""
    
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
            logger.info(f"Loaded disease knowledge base from {self.knowledge_file_path}")
        except Exception as e:
            logger.error(f"Error loading disease knowledge base: {e}")
            self._knowledge_cache = {}
        
        return self._knowledge_cache
    
    async def search_by_symptoms(
        self, 
        symptoms: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[DiseaseSearchResult]:
        """Search disease knowledge by symptoms."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        search_crops = [crop_type] if crop_type else list(crops.keys())
        
        for crop in search_crops:
            if crop not in crops:
                continue
                
            diseases = crops[crop].get("diseases", {})
            for disease_key, disease_info in diseases.items():
                disease_symptoms = disease_info.get("symptoms", [])
                
                # Calculate symptom match
                matches = [s for s in symptoms if s in disease_symptoms]
                if matches:
                    similarity_score = len(matches) / len(disease_symptoms) if disease_symptoms else 0
                    
                    disease_knowledge = DiseaseKnowledge(
                        crop_type=crop,
                        disease_name=disease_key,
                        scientific_name=disease_info.get("scientific_name", ""),
                        symptoms=disease_symptoms,
                        environmental_conditions=disease_info.get("environmental_conditions", {}),
                        treatment=disease_info.get("treatment", []),
                        prevention=disease_info.get("prevention", []),
                        severity=disease_info.get("severity", "moderate"),
                        critical_stages=disease_info.get("critical_stages", []),
                        economic_threshold=disease_info.get("economic_threshold", ""),
                        monitoring_methods=disease_info.get("monitoring_methods", []),
                        spread_conditions=disease_info.get("spread_conditions", {})
                    )
                    
                    results.append(DiseaseSearchResult(
                        disease_knowledge=disease_knowledge,
                        similarity_score=similarity_score,
                        match_type="symptom"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_environmental_conditions(
        self, 
        environmental_conditions: Dict[str, Any], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[DiseaseSearchResult]:
        """Search disease knowledge by environmental conditions."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        search_crops = [crop_type] if crop_type else list(crops.keys())
        
        for crop in search_crops:
            if crop not in crops:
                continue
                
            diseases = crops[crop].get("diseases", {})
            for disease_key, disease_info in diseases.items():
                disease_conditions = disease_info.get("environmental_conditions", {})
                
                # Calculate environmental condition match
                matches = 0
                total_conditions = 0
                
                for condition, value in environmental_conditions.items():
                    if condition in disease_conditions:
                        total_conditions += 1
                        if self._condition_matches(disease_conditions[condition], value):
                            matches += 1
                
                if matches > 0:
                    similarity_score = matches / total_conditions if total_conditions > 0 else 0
                    
                    disease_knowledge = DiseaseKnowledge(
                        crop_type=crop,
                        disease_name=disease_key,
                        scientific_name=disease_info.get("scientific_name", ""),
                        symptoms=disease_info.get("symptoms", []),
                        environmental_conditions=disease_conditions,
                        treatment=disease_info.get("treatment", []),
                        prevention=disease_info.get("prevention", []),
                        severity=disease_info.get("severity", "moderate"),
                        critical_stages=disease_info.get("critical_stages", []),
                        economic_threshold=disease_info.get("economic_threshold", ""),
                        monitoring_methods=disease_info.get("monitoring_methods", []),
                        spread_conditions=disease_info.get("spread_conditions", {})
                    )
                    
                    results.append(DiseaseSearchResult(
                        disease_knowledge=disease_knowledge,
                        similarity_score=similarity_score,
                        match_type="environmental"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    def _condition_matches(self, expected: str, actual: Any) -> bool:
        """Check if environmental condition matches expected value."""
        if expected == "high" and actual > 70:
            return True
        elif expected == "moderate" and 40 <= actual <= 70:
            return True
        elif expected == "low" and actual < 40:
            return True
        elif expected == "very_high" and actual > 80:
            return True
        elif expected == "cool" and actual < 20:
            return True
        elif expected == "warm" and actual > 25:
            return True
        return False
    
    async def get_crop_diseases(
        self, 
        crop_type: str
    ) -> List[DiseaseKnowledge]:
        """Get all disease knowledge for a specific crop."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        if crop_type not in crops:
            return results
        
        diseases = crops[crop_type].get("diseases", {})
        for disease_key, disease_info in diseases.items():
            disease_knowledge = DiseaseKnowledge(
                crop_type=crop_type,
                disease_name=disease_key,
                scientific_name=disease_info.get("scientific_name", ""),
                symptoms=disease_info.get("symptoms", []),
                environmental_conditions=disease_info.get("environmental_conditions", {}),
                treatment=disease_info.get("treatment", []),
                prevention=disease_info.get("prevention", []),
                severity=disease_info.get("severity", "moderate"),
                critical_stages=disease_info.get("critical_stages", []),
                economic_threshold=disease_info.get("economic_threshold", ""),
                monitoring_methods=disease_info.get("monitoring_methods", []),
                spread_conditions=disease_info.get("spread_conditions", {})
            )
            results.append(disease_knowledge)
        
        return results
    
    async def add_disease_knowledge(
        self, 
        knowledge: DiseaseKnowledge
    ) -> bool:
        """Add new disease knowledge (not implemented for JSON)."""
        logger.warning("Adding disease knowledge not supported in JSON mode")
        return False
    
    async def update_disease_knowledge(
        self, 
        crop_type: str, 
        disease_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing disease knowledge (not implemented for JSON)."""
        logger.warning("Updating disease knowledge not supported in JSON mode")
        return False

class VectorDiseaseKnowledgeBase(DiseaseKnowledgeBaseInterface):
    """
    Vector database implementation (future).
    
    This class will be implemented when vector database integration is added.
    It will use embeddings to perform semantic search on disease knowledge.
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
    ) -> List[DiseaseSearchResult]:
        """Search disease knowledge by symptoms using vector similarity."""
        # TODO: Implement vector-based symptom search
        # 1. Generate embeddings for symptoms
        # 2. Search vector database for similar disease knowledge
        # 3. Return ranked results
        logger.info("Vector-based symptom search not yet implemented")
        return []
    
    async def search_by_environmental_conditions(
        self, 
        environmental_conditions: Dict[str, Any], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[DiseaseSearchResult]:
        """Search disease knowledge by environmental conditions using vector similarity."""
        # TODO: Implement vector-based environmental condition search
        logger.info("Vector-based environmental condition search not yet implemented")
        return []
    
    async def get_crop_diseases(
        self, 
        crop_type: str
    ) -> List[DiseaseKnowledge]:
        """Get all disease knowledge for a specific crop."""
        # TODO: Implement vector-based crop disease retrieval
        logger.info("Vector-based crop disease retrieval not yet implemented")
        return []
    
    async def add_disease_knowledge(
        self, 
        knowledge: DiseaseKnowledge
    ) -> bool:
        """Add new disease knowledge to vector database."""
        # TODO: Implement vector-based knowledge addition
        # 1. Generate embeddings for the knowledge
        # 2. Store in vector database
        logger.info("Vector-based knowledge addition not yet implemented")
        return False
    
    async def update_disease_knowledge(
        self, 
        crop_type: str, 
        disease_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing disease knowledge in vector database."""
        # TODO: Implement vector-based knowledge update
        logger.info("Vector-based knowledge update not yet implemented")
        return False

class DiseaseKnowledgeBaseFactory:
    """Factory for creating disease knowledge base instances."""
    
    @staticmethod
    def create_disease_knowledge_base(
        backend_type: str = "json",
        config: Optional[Dict[str, Any]] = None
    ) -> DiseaseKnowledgeBaseInterface:
        """
        Create disease knowledge base instance based on backend type.
        
        Args:
            backend_type: "json" or "vector"
            config: Configuration for the knowledge base
        """
        if backend_type == "json":
            knowledge_file = config.get("knowledge_file") if config else None
            if not knowledge_file:
                # Default path
                current_dir = Path(__file__).parent
                knowledge_file = str(current_dir / "disease_diagnosis_knowledge.json")
            return JSONDiseaseKnowledgeBase(knowledge_file)
        
        elif backend_type == "vector":
            if not config:
                raise ValueError("Vector database configuration required")
            return VectorDiseaseKnowledgeBase(config)
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

# Global disease knowledge base instance
_disease_knowledge_base: Optional[DiseaseKnowledgeBaseInterface] = None

def get_disease_knowledge_base() -> DiseaseKnowledgeBaseInterface:
    """Get global disease knowledge base instance."""
    global _disease_knowledge_base
    if _disease_knowledge_base is None:
        _disease_knowledge_base = DiseaseKnowledgeBaseFactory.create_disease_knowledge_base()
    return _disease_knowledge_base

def set_disease_knowledge_base(knowledge_base: DiseaseKnowledgeBaseInterface):
    """Set global disease knowledge base instance."""
    global _disease_knowledge_base
    _disease_knowledge_base = knowledge_base

def reset_disease_knowledge_base():
    """Reset global disease knowledge base instance."""
    global _disease_knowledge_base
    _disease_knowledge_base = None
