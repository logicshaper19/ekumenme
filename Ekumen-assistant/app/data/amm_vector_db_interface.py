"""
Vector Database Interface for AMM Lookup Knowledge

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
class AMMKnowledge:
    """Structured AMM knowledge for vector storage."""
    product_name: str
    amm_number: str
    active_ingredient: str
    product_type: str
    manufacturer: str
    authorized_uses: List[str]
    restrictions: List[str]
    safety_measures: List[str]
    validity_period: str
    registration_date: str
    expiry_date: str
    target_crops: List[str]
    target_pests: List[str]
    target_diseases: List[str]
    target_weeds: List[str]
    application_methods: List[str]
    dosage_range: Dict[str, str]
    phytotoxicity_risk: str
    environmental_impact: str
    resistance_risk: str
    embedding_vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AMMSearchResult:
    """Search result from vector database."""
    amm_knowledge: AMMKnowledge
    similarity_score: float
    match_type: str  # "product_name", "active_ingredient", "product_type", "general"

class AMMKnowledgeBaseInterface(ABC):
    """Abstract interface for AMM knowledge base operations."""
    
    @abstractmethod
    async def search_by_product_name(
        self, 
        product_name: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by product name."""
        pass
    
    @abstractmethod
    async def search_by_active_ingredient(
        self, 
        active_ingredient: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by active ingredient."""
        pass
    
    @abstractmethod
    async def search_by_product_type(
        self, 
        product_type: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by product type."""
        pass
    
    @abstractmethod
    async def search_by_criteria(
        self, 
        product_name: Optional[str] = None,
        active_ingredient: Optional[str] = None,
        product_type: Optional[str] = None,
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by multiple criteria."""
        pass
    
    @abstractmethod
    async def get_all_products(
        self
    ) -> List[AMMKnowledge]:
        """Get all AMM products."""
        pass
    
    @abstractmethod
    async def add_amm_knowledge(
        self, 
        knowledge: AMMKnowledge
    ) -> bool:
        """Add new AMM knowledge."""
        pass
    
    @abstractmethod
    async def update_amm_knowledge(
        self, 
        product_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing AMM knowledge."""
        pass

class JSONAMMKnowledgeBase(AMMKnowledgeBaseInterface):
    """JSON-based AMM knowledge base implementation (current)."""
    
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
            logger.info(f"Loaded AMM knowledge base from {self.knowledge_file_path}")
        except Exception as e:
            logger.error(f"Error loading AMM knowledge base: {e}")
            self._knowledge_cache = {}
        
        return self._knowledge_cache
    
    async def search_by_product_name(
        self, 
        product_name: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by product name."""
        knowledge = self._load_knowledge()
        results = []
        
        products = knowledge.get("products", {})
        
        for product_key, product_info in products.items():
            # Calculate product name match
            if product_name.lower() in product_key.lower():
                similarity_score = self._calculate_name_similarity(product_name, product_key)
                
                amm_knowledge = self._create_amm_knowledge(product_key, product_info)
                
                results.append(AMMSearchResult(
                    amm_knowledge=amm_knowledge,
                    similarity_score=similarity_score,
                    match_type="product_name"
                ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_active_ingredient(
        self, 
        active_ingredient: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by active ingredient."""
        knowledge = self._load_knowledge()
        results = []
        
        products = knowledge.get("products", {})
        
        for product_key, product_info in products.items():
            product_active_ingredient = product_info.get("active_ingredient", "")
            
            # Calculate active ingredient match
            if active_ingredient.lower() in product_active_ingredient.lower():
                similarity_score = self._calculate_name_similarity(active_ingredient, product_active_ingredient)
                
                amm_knowledge = self._create_amm_knowledge(product_key, product_info)
                
                results.append(AMMSearchResult(
                    amm_knowledge=amm_knowledge,
                    similarity_score=similarity_score,
                    match_type="active_ingredient"
                ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_product_type(
        self, 
        product_type: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by product type."""
        knowledge = self._load_knowledge()
        results = []
        
        products = knowledge.get("products", {})
        
        for product_key, product_info in products.items():
            product_type_info = product_info.get("product_type", "")
            
            # Calculate product type match
            if product_type.lower() in product_type_info.lower():
                similarity_score = self._calculate_name_similarity(product_type, product_type_info)
                
                amm_knowledge = self._create_amm_knowledge(product_key, product_info)
                
                results.append(AMMSearchResult(
                    amm_knowledge=amm_knowledge,
                    similarity_score=similarity_score,
                    match_type="product_type"
                ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_criteria(
        self, 
        product_name: Optional[str] = None,
        active_ingredient: Optional[str] = None,
        product_type: Optional[str] = None,
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by multiple criteria."""
        knowledge = self._load_knowledge()
        results = []
        
        products = knowledge.get("products", {})
        
        for product_key, product_info in products.items():
            # Calculate overall match score
            match_score = 0
            total_criteria = 0
            
            if product_name:
                total_criteria += 1
                if product_name.lower() in product_key.lower():
                    match_score += self._calculate_name_similarity(product_name, product_key)
            
            if active_ingredient:
                total_criteria += 1
                product_active_ingredient = product_info.get("active_ingredient", "")
                if active_ingredient.lower() in product_active_ingredient.lower():
                    match_score += self._calculate_name_similarity(active_ingredient, product_active_ingredient)
            
            if product_type:
                total_criteria += 1
                product_type_info = product_info.get("product_type", "")
                if product_type.lower() in product_type_info.lower():
                    match_score += self._calculate_name_similarity(product_type, product_type_info)
            
            # If no criteria provided, return all products
            if total_criteria == 0:
                match_score = 1.0
                total_criteria = 1
            
            if match_score > 0:
                similarity_score = match_score / total_criteria
                
                amm_knowledge = self._create_amm_knowledge(product_key, product_info)
                
                results.append(AMMSearchResult(
                    amm_knowledge=amm_knowledge,
                    similarity_score=similarity_score,
                    match_type="general"
                ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def get_all_products(
        self
    ) -> List[AMMKnowledge]:
        """Get all AMM products."""
        knowledge = self._load_knowledge()
        results = []
        
        products = knowledge.get("products", {})
        for product_key, product_info in products.items():
            amm_knowledge = self._create_amm_knowledge(product_key, product_info)
            results.append(amm_knowledge)
        
        return results
    
    def _create_amm_knowledge(self, product_key: str, product_info: Dict[str, Any]) -> AMMKnowledge:
        """Create AMMKnowledge object from product info."""
        return AMMKnowledge(
            product_name=product_key,
            amm_number=product_info.get("amm_number", ""),
            active_ingredient=product_info.get("active_ingredient", ""),
            product_type=product_info.get("product_type", ""),
            manufacturer=product_info.get("manufacturer", ""),
            authorized_uses=product_info.get("authorized_uses", []),
            restrictions=product_info.get("restrictions", []),
            safety_measures=product_info.get("safety_measures", []),
            validity_period=product_info.get("validity_period", ""),
            registration_date=product_info.get("registration_date", ""),
            expiry_date=product_info.get("expiry_date", ""),
            target_crops=product_info.get("target_crops", []),
            target_pests=product_info.get("target_pests", []),
            target_diseases=product_info.get("target_diseases", []),
            target_weeds=product_info.get("target_weeds", []),
            application_methods=product_info.get("application_methods", []),
            dosage_range=product_info.get("dosage_range", {}),
            phytotoxicity_risk=product_info.get("phytotoxicity_risk", ""),
            environmental_impact=product_info.get("environmental_impact", ""),
            resistance_risk=product_info.get("resistance_risk", "")
        )
    
    def _calculate_name_similarity(self, search_term: str, target_term: str) -> float:
        """Calculate similarity between search term and target term."""
        search_lower = search_term.lower()
        target_lower = target_term.lower()
        
        if search_lower == target_lower:
            return 1.0
        elif search_lower in target_lower:
            return 0.8
        elif target_lower in search_lower:
            return 0.6
        else:
            # Simple character overlap calculation
            common_chars = set(search_lower) & set(target_lower)
            total_chars = set(search_lower) | set(target_lower)
            return len(common_chars) / len(total_chars) if total_chars else 0.0
    
    async def add_amm_knowledge(
        self, 
        knowledge: AMMKnowledge
    ) -> bool:
        """Add new AMM knowledge (not implemented for JSON)."""
        logger.warning("Adding AMM knowledge not supported in JSON mode")
        return False
    
    async def update_amm_knowledge(
        self, 
        product_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing AMM knowledge (not implemented for JSON)."""
        logger.warning("Updating AMM knowledge not supported in JSON mode")
        return False

class VectorAMMKnowledgeBase(AMMKnowledgeBaseInterface):
    """
    Vector database implementation (future).
    
    This class will be implemented when vector database integration is added.
    It will use embeddings to perform semantic search on AMM knowledge.
    """
    
    def __init__(self, vector_db_config: Dict[str, Any]):
        self.config = vector_db_config
        self.embedding_model = None  # Will be initialized with actual embedding model
        self.vector_db = None  # Will be initialized with actual vector database
    
    async def search_by_product_name(
        self, 
        product_name: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by product name using vector similarity."""
        # TODO: Implement vector-based product name search
        # 1. Generate embeddings for product name
        # 2. Search vector database for similar AMM knowledge
        # 3. Return ranked results
        logger.info("Vector-based product name search not yet implemented")
        return []
    
    async def search_by_active_ingredient(
        self, 
        active_ingredient: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by active ingredient using vector similarity."""
        # TODO: Implement vector-based active ingredient search
        logger.info("Vector-based active ingredient search not yet implemented")
        return []
    
    async def search_by_product_type(
        self, 
        product_type: str, 
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by product type using vector similarity."""
        # TODO: Implement vector-based product type search
        logger.info("Vector-based product type search not yet implemented")
        return []
    
    async def search_by_criteria(
        self, 
        product_name: Optional[str] = None,
        active_ingredient: Optional[str] = None,
        product_type: Optional[str] = None,
        limit: int = 10
    ) -> List[AMMSearchResult]:
        """Search AMM knowledge by multiple criteria using vector similarity."""
        # TODO: Implement vector-based multi-criteria search
        logger.info("Vector-based multi-criteria search not yet implemented")
        return []
    
    async def get_all_products(
        self
    ) -> List[AMMKnowledge]:
        """Get all AMM products."""
        # TODO: Implement vector-based product retrieval
        logger.info("Vector-based product retrieval not yet implemented")
        return []
    
    async def add_amm_knowledge(
        self, 
        knowledge: AMMKnowledge
    ) -> bool:
        """Add new AMM knowledge to vector database."""
        # TODO: Implement vector-based knowledge addition
        # 1. Generate embeddings for the knowledge
        # 2. Store in vector database
        logger.info("Vector-based knowledge addition not yet implemented")
        return False
    
    async def update_amm_knowledge(
        self, 
        product_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing AMM knowledge in vector database."""
        # TODO: Implement vector-based knowledge update
        logger.info("Vector-based knowledge update not yet implemented")
        return False

class AMMKnowledgeBaseFactory:
    """Factory for creating AMM knowledge base instances."""
    
    @staticmethod
    def create_amm_knowledge_base(
        backend_type: str = "json",
        config: Optional[Dict[str, Any]] = None
    ) -> AMMKnowledgeBaseInterface:
        """
        Create AMM knowledge base instance based on backend type.
        
        Args:
            backend_type: "json" or "vector"
            config: Configuration for the knowledge base
        """
        if backend_type == "json":
            knowledge_file = config.get("knowledge_file") if config else None
            if not knowledge_file:
                # Default path
                current_dir = Path(__file__).parent
                knowledge_file = str(current_dir / "amm_lookup_knowledge.json")
            return JSONAMMKnowledgeBase(knowledge_file)
        
        elif backend_type == "vector":
            if not config:
                raise ValueError("Vector database configuration required")
            return VectorAMMKnowledgeBase(config)
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

# Global AMM knowledge base instance
_amm_knowledge_base: Optional[AMMKnowledgeBaseInterface] = None

def get_amm_knowledge_base() -> AMMKnowledgeBaseInterface:
    """Get global AMM knowledge base instance."""
    global _amm_knowledge_base
    if _amm_knowledge_base is None:
        _amm_knowledge_base = AMMKnowledgeBaseFactory.create_amm_knowledge_base()
    return _amm_knowledge_base

def set_amm_knowledge_base(knowledge_base: AMMKnowledgeBaseInterface):
    """Set global AMM knowledge base instance."""
    global _amm_knowledge_base
    _amm_knowledge_base = knowledge_base

def reset_amm_knowledge_base():
    """Reset global AMM knowledge base instance."""
    global _amm_knowledge_base
    _amm_knowledge_base = None
