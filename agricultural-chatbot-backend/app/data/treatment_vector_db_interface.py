"""
Vector Database Interface for Treatment Plan Knowledge

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
class TreatmentKnowledge:
    """Structured treatment knowledge for vector storage."""
    treatment_name: str
    category: str
    cost_per_hectare: float
    effectiveness: str
    application_method: str
    timing: str
    safety_class: str
    environmental_impact: str
    target_diseases: List[str]
    target_pests: List[str]
    target_nutrients: List[str]
    target_crops: List[str]
    application_conditions: Dict[str, Any]
    dose_range: Dict[str, str]
    waiting_period: str
    compatibility: List[str]
    embedding_vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TreatmentSearchResult:
    """Search result from vector database."""
    treatment_knowledge: TreatmentKnowledge
    similarity_score: float
    match_type: str  # "disease", "pest", "nutrient", "crop", "general"

class TreatmentKnowledgeBaseInterface(ABC):
    """Abstract interface for treatment knowledge base operations."""
    
    @abstractmethod
    async def search_by_disease(
        self, 
        disease_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by disease."""
        pass
    
    @abstractmethod
    async def search_by_pest(
        self, 
        pest_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by pest."""
        pass
    
    @abstractmethod
    async def search_by_nutrient(
        self, 
        nutrient_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by nutrient deficiency."""
        pass
    
    @abstractmethod
    async def search_by_crop(
        self, 
        crop_type: str, 
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by crop type."""
        pass
    
    @abstractmethod
    async def get_all_treatments(
        self
    ) -> List[TreatmentKnowledge]:
        """Get all treatment knowledge."""
        pass
    
    @abstractmethod
    async def add_treatment_knowledge(
        self, 
        knowledge: TreatmentKnowledge
    ) -> bool:
        """Add new treatment knowledge."""
        pass
    
    @abstractmethod
    async def update_treatment_knowledge(
        self, 
        treatment_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing treatment knowledge."""
        pass

class JSONTreatmentKnowledgeBase(TreatmentKnowledgeBaseInterface):
    """JSON-based treatment knowledge base implementation (current)."""
    
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
            logger.info(f"Loaded treatment knowledge base from {self.knowledge_file_path}")
        except Exception as e:
            logger.error(f"Error loading treatment knowledge base: {e}")
            self._knowledge_cache = {}
        
        return self._knowledge_cache
    
    async def search_by_disease(
        self, 
        disease_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by disease."""
        knowledge = self._load_knowledge()
        results = []
        
        treatments = knowledge.get("treatments", {})
        
        for category, category_treatments in treatments.items():
            for treatment_key, treatment_info in category_treatments.items():
                target_diseases = treatment_info.get("target_diseases", [])
                
                # Calculate disease match
                if disease_name.lower() in [d.lower() for d in target_diseases]:
                    similarity_score = self._calculate_disease_similarity(disease_name, target_diseases)
                    
                    treatment_knowledge = self._create_treatment_knowledge(treatment_key, treatment_info)
                    
                    results.append(TreatmentSearchResult(
                        treatment_knowledge=treatment_knowledge,
                        similarity_score=similarity_score,
                        match_type="disease"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_pest(
        self, 
        pest_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by pest."""
        knowledge = self._load_knowledge()
        results = []
        
        treatments = knowledge.get("treatments", {})
        
        for category, category_treatments in treatments.items():
            for treatment_key, treatment_info in category_treatments.items():
                target_pests = treatment_info.get("target_pests", [])
                
                # Calculate pest match
                if pest_name.lower() in [p.lower() for p in target_pests]:
                    similarity_score = self._calculate_pest_similarity(pest_name, target_pests)
                    
                    treatment_knowledge = self._create_treatment_knowledge(treatment_key, treatment_info)
                    
                    results.append(TreatmentSearchResult(
                        treatment_knowledge=treatment_knowledge,
                        similarity_score=similarity_score,
                        match_type="pest"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_nutrient(
        self, 
        nutrient_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by nutrient deficiency."""
        knowledge = self._load_knowledge()
        results = []
        
        treatments = knowledge.get("treatments", {})
        
        for category, category_treatments in treatments.items():
            for treatment_key, treatment_info in category_treatments.items():
                target_nutrients = treatment_info.get("target_nutrients", [])
                
                # Calculate nutrient match
                if nutrient_name.lower() in [n.lower() for n in target_nutrients]:
                    similarity_score = self._calculate_nutrient_similarity(nutrient_name, target_nutrients)
                    
                    treatment_knowledge = self._create_treatment_knowledge(treatment_key, treatment_info)
                    
                    results.append(TreatmentSearchResult(
                        treatment_knowledge=treatment_knowledge,
                        similarity_score=similarity_score,
                        match_type="nutrient"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_crop(
        self, 
        crop_type: str, 
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by crop type."""
        knowledge = self._load_knowledge()
        results = []
        
        treatments = knowledge.get("treatments", {})
        
        for category, category_treatments in treatments.items():
            for treatment_key, treatment_info in category_treatments.items():
                target_crops = treatment_info.get("target_crops", [])
                
                # Calculate crop match
                if crop_type.lower() in [c.lower() for c in target_crops]:
                    similarity_score = self._calculate_crop_similarity(crop_type, target_crops)
                    
                    treatment_knowledge = self._create_treatment_knowledge(treatment_key, treatment_info)
                    
                    results.append(TreatmentSearchResult(
                        treatment_knowledge=treatment_knowledge,
                        similarity_score=similarity_score,
                        match_type="crop"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def get_all_treatments(
        self
    ) -> List[TreatmentKnowledge]:
        """Get all treatment knowledge."""
        knowledge = self._load_knowledge()
        results = []
        
        treatments = knowledge.get("treatments", {})
        for category, category_treatments in treatments.items():
            for treatment_key, treatment_info in category_treatments.items():
                treatment_knowledge = self._create_treatment_knowledge(treatment_key, treatment_info)
                results.append(treatment_knowledge)
        
        return results
    
    def _create_treatment_knowledge(self, treatment_key: str, treatment_info: Dict[str, Any]) -> TreatmentKnowledge:
        """Create TreatmentKnowledge object from treatment info."""
        return TreatmentKnowledge(
            treatment_name=treatment_key,
            category=treatment_info.get("category", ""),
            cost_per_hectare=treatment_info.get("cost_per_hectare", 0.0),
            effectiveness=treatment_info.get("effectiveness", ""),
            application_method=treatment_info.get("application_method", ""),
            timing=treatment_info.get("timing", ""),
            safety_class=treatment_info.get("safety_class", ""),
            environmental_impact=treatment_info.get("environmental_impact", ""),
            target_diseases=treatment_info.get("target_diseases", []),
            target_pests=treatment_info.get("target_pests", []),
            target_nutrients=treatment_info.get("target_nutrients", []),
            target_crops=treatment_info.get("target_crops", []),
            application_conditions=treatment_info.get("application_conditions", {}),
            dose_range=treatment_info.get("dose_range", {}),
            waiting_period=treatment_info.get("waiting_period", ""),
            compatibility=treatment_info.get("compatibility", [])
        )
    
    def _calculate_disease_similarity(self, disease_name: str, target_diseases: List[str]) -> float:
        """Calculate similarity between disease name and target diseases."""
        disease_lower = disease_name.lower()
        target_lower = [d.lower() for d in target_diseases]
        
        if disease_lower in target_lower:
            return 1.0
        
        # Calculate partial matches
        max_similarity = 0.0
        for target in target_lower:
            if disease_lower in target or target in disease_lower:
                max_similarity = max(max_similarity, 0.8)
            else:
                # Simple character overlap calculation
                common_chars = set(disease_lower) & set(target)
                total_chars = set(disease_lower) | set(target)
                similarity = len(common_chars) / len(total_chars) if total_chars else 0.0
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_pest_similarity(self, pest_name: str, target_pests: List[str]) -> float:
        """Calculate similarity between pest name and target pests."""
        pest_lower = pest_name.lower()
        target_lower = [p.lower() for p in target_pests]
        
        if pest_lower in target_lower:
            return 1.0
        
        # Calculate partial matches
        max_similarity = 0.0
        for target in target_lower:
            if pest_lower in target or target in pest_lower:
                max_similarity = max(max_similarity, 0.8)
            else:
                # Simple character overlap calculation
                common_chars = set(pest_lower) & set(target)
                total_chars = set(pest_lower) | set(target)
                similarity = len(common_chars) / len(total_chars) if total_chars else 0.0
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_nutrient_similarity(self, nutrient_name: str, target_nutrients: List[str]) -> float:
        """Calculate similarity between nutrient name and target nutrients."""
        nutrient_lower = nutrient_name.lower()
        target_lower = [n.lower() for n in target_nutrients]
        
        if nutrient_lower in target_lower:
            return 1.0
        
        # Calculate partial matches
        max_similarity = 0.0
        for target in target_lower:
            if nutrient_lower in target or target in nutrient_lower:
                max_similarity = max(max_similarity, 0.8)
            else:
                # Simple character overlap calculation
                common_chars = set(nutrient_lower) & set(target)
                total_chars = set(nutrient_lower) | set(target)
                similarity = len(common_chars) / len(total_chars) if total_chars else 0.0
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_crop_similarity(self, crop_type: str, target_crops: List[str]) -> float:
        """Calculate similarity between crop type and target crops."""
        crop_lower = crop_type.lower()
        target_lower = [c.lower() for c in target_crops]
        
        if crop_lower in target_lower:
            return 1.0
        
        # Calculate partial matches
        max_similarity = 0.0
        for target in target_lower:
            if crop_lower in target or target in crop_lower:
                max_similarity = max(max_similarity, 0.8)
            else:
                # Simple character overlap calculation
                common_chars = set(crop_lower) & set(target)
                total_chars = set(crop_lower) | set(target)
                similarity = len(common_chars) / len(total_chars) if total_chars else 0.0
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    async def add_treatment_knowledge(
        self, 
        knowledge: TreatmentKnowledge
    ) -> bool:
        """Add new treatment knowledge (not implemented for JSON)."""
        logger.warning("Adding treatment knowledge not supported in JSON mode")
        return False
    
    async def update_treatment_knowledge(
        self, 
        treatment_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing treatment knowledge (not implemented for JSON)."""
        logger.warning("Updating treatment knowledge not supported in JSON mode")
        return False

class VectorTreatmentKnowledgeBase(TreatmentKnowledgeBaseInterface):
    """
    Vector database implementation (future).
    
    This class will be implemented when vector database integration is added.
    It will use embeddings to perform semantic search on treatment knowledge.
    """
    
    def __init__(self, vector_db_config: Dict[str, Any]):
        self.config = vector_db_config
        self.embedding_model = None  # Will be initialized with actual embedding model
        self.vector_db = None  # Will be initialized with actual vector database
    
    async def search_by_disease(
        self, 
        disease_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by disease using vector similarity."""
        # TODO: Implement vector-based disease search
        # 1. Generate embeddings for disease name
        # 2. Search vector database for similar treatment knowledge
        # 3. Return ranked results
        logger.info("Vector-based disease search not yet implemented")
        return []
    
    async def search_by_pest(
        self, 
        pest_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by pest using vector similarity."""
        # TODO: Implement vector-based pest search
        logger.info("Vector-based pest search not yet implemented")
        return []
    
    async def search_by_nutrient(
        self, 
        nutrient_name: str, 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by nutrient using vector similarity."""
        # TODO: Implement vector-based nutrient search
        logger.info("Vector-based nutrient search not yet implemented")
        return []
    
    async def search_by_crop(
        self, 
        crop_type: str, 
        limit: int = 10
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge by crop using vector similarity."""
        # TODO: Implement vector-based crop search
        logger.info("Vector-based crop search not yet implemented")
        return []
    
    async def get_all_treatments(
        self
    ) -> List[TreatmentKnowledge]:
        """Get all treatment knowledge."""
        # TODO: Implement vector-based treatment retrieval
        logger.info("Vector-based treatment retrieval not yet implemented")
        return []
    
    async def add_treatment_knowledge(
        self, 
        knowledge: TreatmentKnowledge
    ) -> bool:
        """Add new treatment knowledge to vector database."""
        # TODO: Implement vector-based knowledge addition
        # 1. Generate embeddings for the knowledge
        # 2. Store in vector database
        logger.info("Vector-based knowledge addition not yet implemented")
        return False
    
    async def update_treatment_knowledge(
        self, 
        treatment_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing treatment knowledge in vector database."""
        # TODO: Implement vector-based knowledge update
        logger.info("Vector-based knowledge update not yet implemented")
        return False

class TreatmentKnowledgeBaseFactory:
    """Factory for creating treatment knowledge base instances."""
    
    @staticmethod
    def create_treatment_knowledge_base(
        backend_type: str = "json",
        config: Optional[Dict[str, Any]] = None
    ) -> TreatmentKnowledgeBaseInterface:
        """
        Create treatment knowledge base instance based on backend type.
        
        Args:
            backend_type: "json" or "vector"
            config: Configuration for the knowledge base
        """
        if backend_type == "json":
            knowledge_file = config.get("knowledge_file") if config else None
            if not knowledge_file:
                # Default path
                current_dir = Path(__file__).parent
                knowledge_file = str(current_dir / "treatment_plan_knowledge.json")
            return JSONTreatmentKnowledgeBase(knowledge_file)
        
        elif backend_type == "vector":
            if not config:
                raise ValueError("Vector database configuration required")
            return VectorTreatmentKnowledgeBase(config)
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

# Global treatment knowledge base instance
_treatment_knowledge_base: Optional[TreatmentKnowledgeBaseInterface] = None

def get_treatment_knowledge_base() -> TreatmentKnowledgeBaseInterface:
    """Get global treatment knowledge base instance."""
    global _treatment_knowledge_base
    if _treatment_knowledge_base is None:
        _treatment_knowledge_base = TreatmentKnowledgeBaseFactory.create_treatment_knowledge_base()
    return _treatment_knowledge_base

def set_treatment_knowledge_base(knowledge_base: TreatmentKnowledgeBaseInterface):
    """Set global treatment knowledge base instance."""
    global _treatment_knowledge_base
    _treatment_knowledge_base = knowledge_base

def reset_treatment_knowledge_base():
    """Reset global treatment knowledge base instance."""
    global _treatment_knowledge_base
    _treatment_knowledge_base = None
