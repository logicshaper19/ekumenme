"""
Vector Database Interface for Pest Identification Knowledge

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
class PestKnowledge:
    """Structured pest knowledge for vector storage."""
    crop_type: str
    pest_name: str
    scientific_name: str
    damage_patterns: List[str]
    pest_indicators: List[str]
    treatment: List[str]
    prevention: List[str]
    severity: str
    critical_stages: List[str]
    economic_threshold: str
    monitoring_methods: List[str]
    embedding_vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PestSearchResult:
    """Search result from vector database."""
    pest_knowledge: PestKnowledge
    similarity_score: float
    match_type: str  # "damage", "indicator", "treatment", "general"

class PestKnowledgeBaseInterface(ABC):
    """Abstract interface for pest knowledge base operations."""
    
    @abstractmethod
    async def search_by_damage_patterns(
        self, 
        damage_patterns: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[PestSearchResult]:
        """Search pest knowledge by damage patterns."""
        pass
    
    @abstractmethod
    async def search_by_pest_indicators(
        self, 
        pest_indicators: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[PestSearchResult]:
        """Search pest knowledge by pest indicators."""
        pass
    
    @abstractmethod
    async def get_crop_pests(
        self, 
        crop_type: str
    ) -> List[PestKnowledge]:
        """Get all pest knowledge for a specific crop."""
        pass
    
    @abstractmethod
    async def add_pest_knowledge(
        self, 
        knowledge: PestKnowledge
    ) -> bool:
        """Add new pest knowledge."""
        pass
    
    @abstractmethod
    async def update_pest_knowledge(
        self, 
        crop_type: str, 
        pest_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing pest knowledge."""
        pass

class JSONPestKnowledgeBase(PestKnowledgeBaseInterface):
    """JSON-based pest knowledge base implementation (current)."""
    
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
            logger.info(f"Loaded pest knowledge base from {self.knowledge_file_path}")
        except Exception as e:
            logger.error(f"Error loading pest knowledge base: {e}")
            self._knowledge_cache = {}
        
        return self._knowledge_cache
    
    async def search_by_damage_patterns(
        self, 
        damage_patterns: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[PestSearchResult]:
        """Search pest knowledge by damage patterns."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        search_crops = [crop_type] if crop_type else list(crops.keys())
        
        for crop in search_crops:
            if crop not in crops:
                continue
                
            pests = crops[crop].get("pests", {})
            for pest_key, pest_info in pests.items():
                pest_damage_patterns = pest_info.get("damage_patterns", [])
                
                # Calculate damage pattern match
                matches = [d for d in damage_patterns if d in pest_damage_patterns]
                if matches:
                    similarity_score = len(matches) / len(pest_damage_patterns) if pest_damage_patterns else 0
                    
                    pest_knowledge = PestKnowledge(
                        crop_type=crop,
                        pest_name=pest_key,
                        scientific_name=pest_info.get("scientific_name", ""),
                        damage_patterns=pest_damage_patterns,
                        pest_indicators=pest_info.get("pest_indicators", []),
                        treatment=pest_info.get("treatment", []),
                        prevention=pest_info.get("prevention", []),
                        severity=pest_info.get("severity", "moderate"),
                        critical_stages=pest_info.get("critical_stages", []),
                        economic_threshold=pest_info.get("economic_threshold", ""),
                        monitoring_methods=pest_info.get("monitoring_methods", [])
                    )
                    
                    results.append(PestSearchResult(
                        pest_knowledge=pest_knowledge,
                        similarity_score=similarity_score,
                        match_type="damage"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_pest_indicators(
        self, 
        pest_indicators: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[PestSearchResult]:
        """Search pest knowledge by pest indicators."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        search_crops = [crop_type] if crop_type else list(crops.keys())
        
        for crop in search_crops:
            if crop not in crops:
                continue
                
            pests = crops[crop].get("pests", {})
            for pest_key, pest_info in pests.items():
                pest_indicators_list = pest_info.get("pest_indicators", [])
                
                # Calculate pest indicator match
                matches = [p for p in pest_indicators if p in pest_indicators_list]
                if matches:
                    similarity_score = len(matches) / len(pest_indicators_list) if pest_indicators_list else 0
                    
                    pest_knowledge = PestKnowledge(
                        crop_type=crop,
                        pest_name=pest_key,
                        scientific_name=pest_info.get("scientific_name", ""),
                        damage_patterns=pest_info.get("damage_patterns", []),
                        pest_indicators=pest_indicators_list,
                        treatment=pest_info.get("treatment", []),
                        prevention=pest_info.get("prevention", []),
                        severity=pest_info.get("severity", "moderate"),
                        critical_stages=pest_info.get("critical_stages", []),
                        economic_threshold=pest_info.get("economic_threshold", ""),
                        monitoring_methods=pest_info.get("monitoring_methods", [])
                    )
                    
                    results.append(PestSearchResult(
                        pest_knowledge=pest_knowledge,
                        similarity_score=similarity_score,
                        match_type="indicator"
                    ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def get_crop_pests(
        self, 
        crop_type: str
    ) -> List[PestKnowledge]:
        """Get all pest knowledge for a specific crop."""
        knowledge = self._load_knowledge()
        results = []
        
        crops = knowledge.get("crops", {})
        if crop_type not in crops:
            return results
        
        pests = crops[crop_type].get("pests", {})
        for pest_key, pest_info in pests.items():
            pest_knowledge = PestKnowledge(
                crop_type=crop_type,
                pest_name=pest_key,
                scientific_name=pest_info.get("scientific_name", ""),
                damage_patterns=pest_info.get("damage_patterns", []),
                pest_indicators=pest_info.get("pest_indicators", []),
                treatment=pest_info.get("treatment", []),
                prevention=pest_info.get("prevention", []),
                severity=pest_info.get("severity", "moderate"),
                critical_stages=pest_info.get("critical_stages", []),
                economic_threshold=pest_info.get("economic_threshold", ""),
                monitoring_methods=pest_info.get("monitoring_methods", [])
            )
            results.append(pest_knowledge)
        
        return results
    
    async def add_pest_knowledge(
        self, 
        knowledge: PestKnowledge
    ) -> bool:
        """Add new pest knowledge (not implemented for JSON)."""
        logger.warning("Adding pest knowledge not supported in JSON mode")
        return False
    
    async def update_pest_knowledge(
        self, 
        crop_type: str, 
        pest_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing pest knowledge (not implemented for JSON)."""
        logger.warning("Updating pest knowledge not supported in JSON mode")
        return False

class VectorPestKnowledgeBase(PestKnowledgeBaseInterface):
    """
    Vector database implementation (future).
    
    This class will be implemented when vector database integration is added.
    It will use embeddings to perform semantic search on pest knowledge.
    """
    
    def __init__(self, vector_db_config: Dict[str, Any]):
        self.config = vector_db_config
        self.embedding_model = None  # Will be initialized with actual embedding model
        self.vector_db = None  # Will be initialized with actual vector database
    
    async def search_by_damage_patterns(
        self, 
        damage_patterns: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[PestSearchResult]:
        """Search pest knowledge by damage patterns using vector similarity."""
        # TODO: Implement vector-based damage pattern search
        # 1. Generate embeddings for damage patterns
        # 2. Search vector database for similar pest knowledge
        # 3. Return ranked results
        logger.info("Vector-based damage pattern search not yet implemented")
        return []
    
    async def search_by_pest_indicators(
        self, 
        pest_indicators: List[str], 
        crop_type: Optional[str] = None,
        limit: int = 10
    ) -> List[PestSearchResult]:
        """Search pest knowledge by pest indicators using vector similarity."""
        # TODO: Implement vector-based pest indicator search
        logger.info("Vector-based pest indicator search not yet implemented")
        return []
    
    async def get_crop_pests(
        self, 
        crop_type: str
    ) -> List[PestKnowledge]:
        """Get all pest knowledge for a specific crop."""
        # TODO: Implement vector-based crop pest retrieval
        logger.info("Vector-based crop pest retrieval not yet implemented")
        return []
    
    async def add_pest_knowledge(
        self, 
        knowledge: PestKnowledge
    ) -> bool:
        """Add new pest knowledge to vector database."""
        # TODO: Implement vector-based knowledge addition
        # 1. Generate embeddings for the knowledge
        # 2. Store in vector database
        logger.info("Vector-based knowledge addition not yet implemented")
        return False
    
    async def update_pest_knowledge(
        self, 
        crop_type: str, 
        pest_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing pest knowledge in vector database."""
        # TODO: Implement vector-based knowledge update
        logger.info("Vector-based knowledge update not yet implemented")
        return False

class PestKnowledgeBaseFactory:
    """Factory for creating pest knowledge base instances."""
    
    @staticmethod
    def create_pest_knowledge_base(
        backend_type: str = "json",
        config: Optional[Dict[str, Any]] = None
    ) -> PestKnowledgeBaseInterface:
        """
        Create pest knowledge base instance based on backend type.
        
        Args:
            backend_type: "json" or "vector"
            config: Configuration for the knowledge base
        """
        if backend_type == "json":
            knowledge_file = config.get("knowledge_file") if config else None
            if not knowledge_file:
                # Default path
                current_dir = Path(__file__).parent
                knowledge_file = str(current_dir / "pest_identification_knowledge.json")
            return JSONPestKnowledgeBase(knowledge_file)
        
        elif backend_type == "vector":
            if not config:
                raise ValueError("Vector database configuration required")
            return VectorPestKnowledgeBase(config)
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

# Global pest knowledge base instance
_pest_knowledge_base: Optional[PestKnowledgeBaseInterface] = None

def get_pest_knowledge_base() -> PestKnowledgeBaseInterface:
    """Get global pest knowledge base instance."""
    global _pest_knowledge_base
    if _pest_knowledge_base is None:
        _pest_knowledge_base = PestKnowledgeBaseFactory.create_pest_knowledge_base()
    return _pest_knowledge_base

def set_pest_knowledge_base(knowledge_base: PestKnowledgeBaseInterface):
    """Set global pest knowledge base instance."""
    global _pest_knowledge_base
    _pest_knowledge_base = knowledge_base

def reset_pest_knowledge_base():
    """Reset global pest knowledge base instance."""
    global _pest_knowledge_base
    _pest_knowledge_base = None
