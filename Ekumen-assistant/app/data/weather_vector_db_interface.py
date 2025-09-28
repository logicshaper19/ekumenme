"""
Vector Database Interface for Weather Data Knowledge

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
class WeatherKnowledge:
    """Structured weather knowledge for vector storage."""
    condition_name: str
    condition_code: int
    description: str
    agricultural_impact: str
    recommended_activities: List[str]
    restrictions: List[str]
    temperature_range: Dict[str, float]
    humidity_range: Dict[str, float]
    wind_range: Dict[str, float]
    precipitation_range: Optional[Dict[str, float]] = None
    cloud_cover_range: Optional[Dict[str, float]] = None
    uv_index_range: Optional[Dict[str, float]] = None
    embedding_vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class WeatherSearchResult:
    """Search result from vector database."""
    weather_knowledge: WeatherKnowledge
    similarity_score: float
    match_type: str  # "condition", "activity", "impact", "general"

class WeatherKnowledgeBaseInterface(ABC):
    """Abstract interface for weather knowledge base operations."""
    
    @abstractmethod
    async def search_by_condition(
        self, 
        condition_name: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by condition name."""
        pass
    
    @abstractmethod
    async def search_by_agricultural_impact(
        self, 
        impact: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by agricultural impact."""
        pass
    
    @abstractmethod
    async def search_by_activity(
        self, 
        activity: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by recommended activity."""
        pass
    
    @abstractmethod
    async def search_by_weather_parameters(
        self, 
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        wind_speed: Optional[float] = None,
        precipitation: Optional[float] = None,
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by weather parameters."""
        pass
    
    @abstractmethod
    async def get_all_weather_conditions(
        self
    ) -> List[WeatherKnowledge]:
        """Get all weather conditions."""
        pass
    
    @abstractmethod
    async def add_weather_knowledge(
        self, 
        knowledge: WeatherKnowledge
    ) -> bool:
        """Add new weather knowledge."""
        pass
    
    @abstractmethod
    async def update_weather_knowledge(
        self, 
        condition_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing weather knowledge."""
        pass

class JSONWeatherKnowledgeBase(WeatherKnowledgeBaseInterface):
    """JSON-based weather knowledge base implementation (current)."""
    
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
            logger.info(f"Loaded weather knowledge base from {self.knowledge_file_path}")
        except Exception as e:
            logger.error(f"Error loading weather knowledge base: {e}")
            self._knowledge_cache = {}
        
        return self._knowledge_cache
    
    async def search_by_condition(
        self, 
        condition_name: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by condition name."""
        knowledge = self._load_knowledge()
        results = []
        
        weather_conditions = knowledge.get("weather_conditions", {})
        
        for condition_key, condition_info in weather_conditions.items():
            # Calculate condition match
            if condition_name.lower() in condition_key.lower() or condition_name.lower() in condition_info.get("description", "").lower():
                similarity_score = self._calculate_condition_similarity(condition_name, condition_key, condition_info)
                
                weather_knowledge = self._create_weather_knowledge(condition_key, condition_info)
                
                results.append(WeatherSearchResult(
                    weather_knowledge=weather_knowledge,
                    similarity_score=similarity_score,
                    match_type="condition"
                ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_agricultural_impact(
        self, 
        impact: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by agricultural impact."""
        knowledge = self._load_knowledge()
        results = []
        
        weather_conditions = knowledge.get("weather_conditions", {})
        
        for condition_key, condition_info in weather_conditions.items():
            agricultural_impact = condition_info.get("agricultural_impact", "")
            
            # Calculate impact match
            if impact.lower() in agricultural_impact.lower():
                similarity_score = self._calculate_impact_similarity(impact, agricultural_impact)
                
                weather_knowledge = self._create_weather_knowledge(condition_key, condition_info)
                
                results.append(WeatherSearchResult(
                    weather_knowledge=weather_knowledge,
                    similarity_score=similarity_score,
                    match_type="impact"
                ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_activity(
        self, 
        activity: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by recommended activity."""
        knowledge = self._load_knowledge()
        results = []
        
        weather_conditions = knowledge.get("weather_conditions", {})
        
        for condition_key, condition_info in weather_conditions.items():
            recommended_activities = condition_info.get("recommended_activities", [])
            
            # Calculate activity match
            if any(activity.lower() in act.lower() for act in recommended_activities):
                similarity_score = self._calculate_activity_similarity(activity, recommended_activities)
                
                weather_knowledge = self._create_weather_knowledge(condition_key, condition_info)
                
                results.append(WeatherSearchResult(
                    weather_knowledge=weather_knowledge,
                    similarity_score=similarity_score,
                    match_type="activity"
                ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def search_by_weather_parameters(
        self, 
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        wind_speed: Optional[float] = None,
        precipitation: Optional[float] = None,
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by weather parameters."""
        knowledge = self._load_knowledge()
        results = []
        
        weather_conditions = knowledge.get("weather_conditions", {})
        
        for condition_key, condition_info in weather_conditions.items():
            # Calculate parameter match
            match_score = 0
            total_parameters = 0
            
            if temperature is not None:
                total_parameters += 1
                temp_range = condition_info.get("temperature_range", {})
                if temp_range.get("min", 0) <= temperature <= temp_range.get("max", 100):
                    match_score += 1
            
            if humidity is not None:
                total_parameters += 1
                humidity_range = condition_info.get("humidity_range", {})
                if humidity_range.get("min", 0) <= humidity <= humidity_range.get("max", 100):
                    match_score += 1
            
            if wind_speed is not None:
                total_parameters += 1
                wind_range = condition_info.get("wind_range", {})
                if wind_range.get("min", 0) <= wind_speed <= wind_range.get("max", 100):
                    match_score += 1
            
            if precipitation is not None:
                total_parameters += 1
                # For precipitation, we check if it's within acceptable range
                if precipitation <= 5.0:  # Light precipitation
                    match_score += 1
            
            if total_parameters > 0:
                similarity_score = match_score / total_parameters
                
                weather_knowledge = self._create_weather_knowledge(condition_key, condition_info)
                
                results.append(WeatherSearchResult(
                    weather_knowledge=weather_knowledge,
                    similarity_score=similarity_score,
                    match_type="general"
                ))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    async def get_all_weather_conditions(
        self
    ) -> List[WeatherKnowledge]:
        """Get all weather conditions."""
        knowledge = self._load_knowledge()
        results = []
        
        weather_conditions = knowledge.get("weather_conditions", {})
        for condition_key, condition_info in weather_conditions.items():
            weather_knowledge = self._create_weather_knowledge(condition_key, condition_info)
            results.append(weather_knowledge)
        
        return results
    
    def _create_weather_knowledge(self, condition_key: str, condition_info: Dict[str, Any]) -> WeatherKnowledge:
        """Create WeatherKnowledge object from condition info."""
        return WeatherKnowledge(
            condition_name=condition_key,
            condition_code=condition_info.get("condition_code", 0),
            description=condition_info.get("description", ""),
            agricultural_impact=condition_info.get("agricultural_impact", ""),
            recommended_activities=condition_info.get("recommended_activities", []),
            restrictions=condition_info.get("restrictions", []),
            temperature_range=condition_info.get("temperature_range", {}),
            humidity_range=condition_info.get("humidity_range", {}),
            wind_range=condition_info.get("wind_range", {}),
            precipitation_range=condition_info.get("precipitation_range"),
            cloud_cover_range=condition_info.get("cloud_cover_range"),
            uv_index_range=condition_info.get("uv_index_range")
        )
    
    def _calculate_condition_similarity(self, search_term: str, condition_key: str, condition_info: Dict[str, Any]) -> float:
        """Calculate similarity between search term and condition."""
        search_lower = search_term.lower()
        condition_lower = condition_key.lower()
        description_lower = condition_info.get("description", "").lower()
        
        if search_lower == condition_lower:
            return 1.0
        elif search_lower in condition_lower:
            return 0.9
        elif search_lower in description_lower:
            return 0.8
        else:
            # Simple character overlap calculation
            common_chars = set(search_lower) & set(condition_lower)
            total_chars = set(search_lower) | set(condition_lower)
            return len(common_chars) / len(total_chars) if total_chars else 0.0
    
    def _calculate_impact_similarity(self, search_term: str, impact: str) -> float:
        """Calculate similarity between search term and agricultural impact."""
        search_lower = search_term.lower()
        impact_lower = impact.lower()
        
        if search_lower == impact_lower:
            return 1.0
        elif search_lower in impact_lower:
            return 0.8
        else:
            # Simple character overlap calculation
            common_chars = set(search_lower) & set(impact_lower)
            total_chars = set(search_lower) | set(impact_lower)
            return len(common_chars) / len(total_chars) if total_chars else 0.0
    
    def _calculate_activity_similarity(self, search_term: str, activities: List[str]) -> float:
        """Calculate similarity between search term and activities."""
        search_lower = search_term.lower()
        max_similarity = 0.0
        
        for activity in activities:
            activity_lower = activity.lower()
            if search_lower == activity_lower:
                return 1.0
            elif search_lower in activity_lower:
                max_similarity = max(max_similarity, 0.8)
            else:
                # Simple character overlap calculation
                common_chars = set(search_lower) & set(activity_lower)
                total_chars = set(search_lower) | set(activity_lower)
                similarity = len(common_chars) / len(total_chars) if total_chars else 0.0
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    async def add_weather_knowledge(
        self, 
        knowledge: WeatherKnowledge
    ) -> bool:
        """Add new weather knowledge (not implemented for JSON)."""
        logger.warning("Adding weather knowledge not supported in JSON mode")
        return False
    
    async def update_weather_knowledge(
        self, 
        condition_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing weather knowledge (not implemented for JSON)."""
        logger.warning("Updating weather knowledge not supported in JSON mode")
        return False

class VectorWeatherKnowledgeBase(WeatherKnowledgeBaseInterface):
    """
    Vector database implementation (future).
    
    This class will be implemented when vector database integration is added.
    It will use embeddings to perform semantic search on weather knowledge.
    """
    
    def __init__(self, vector_db_config: Dict[str, Any]):
        self.config = vector_db_config
        self.embedding_model = None  # Will be initialized with actual embedding model
        self.vector_db = None  # Will be initialized with actual vector database
    
    async def search_by_condition(
        self, 
        condition_name: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by condition using vector similarity."""
        # TODO: Implement vector-based condition search
        # 1. Generate embeddings for condition name
        # 2. Search vector database for similar weather knowledge
        # 3. Return ranked results
        logger.info("Vector-based condition search not yet implemented")
        return []
    
    async def search_by_agricultural_impact(
        self, 
        impact: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by agricultural impact using vector similarity."""
        # TODO: Implement vector-based impact search
        logger.info("Vector-based impact search not yet implemented")
        return []
    
    async def search_by_activity(
        self, 
        activity: str, 
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by activity using vector similarity."""
        # TODO: Implement vector-based activity search
        logger.info("Vector-based activity search not yet implemented")
        return []
    
    async def search_by_weather_parameters(
        self, 
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        wind_speed: Optional[float] = None,
        precipitation: Optional[float] = None,
        limit: int = 10
    ) -> List[WeatherSearchResult]:
        """Search weather knowledge by weather parameters using vector similarity."""
        # TODO: Implement vector-based parameter search
        logger.info("Vector-based parameter search not yet implemented")
        return []
    
    async def get_all_weather_conditions(
        self
    ) -> List[WeatherKnowledge]:
        """Get all weather conditions."""
        # TODO: Implement vector-based condition retrieval
        logger.info("Vector-based condition retrieval not yet implemented")
        return []
    
    async def add_weather_knowledge(
        self, 
        knowledge: WeatherKnowledge
    ) -> bool:
        """Add new weather knowledge to vector database."""
        # TODO: Implement vector-based knowledge addition
        # 1. Generate embeddings for the knowledge
        # 2. Store in vector database
        logger.info("Vector-based knowledge addition not yet implemented")
        return False
    
    async def update_weather_knowledge(
        self, 
        condition_name: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing weather knowledge in vector database."""
        # TODO: Implement vector-based knowledge update
        logger.info("Vector-based knowledge update not yet implemented")
        return False

class WeatherKnowledgeBaseFactory:
    """Factory for creating weather knowledge base instances."""
    
    @staticmethod
    def create_weather_knowledge_base(
        backend_type: str = "json",
        config: Optional[Dict[str, Any]] = None
    ) -> WeatherKnowledgeBaseInterface:
        """
        Create weather knowledge base instance based on backend type.
        
        Args:
            backend_type: "json" or "vector"
            config: Configuration for the knowledge base
        """
        if backend_type == "json":
            knowledge_file = config.get("knowledge_file") if config else None
            if not knowledge_file:
                # Default path
                current_dir = Path(__file__).parent
                knowledge_file = str(current_dir / "weather_data_knowledge.json")
            return JSONWeatherKnowledgeBase(knowledge_file)
        
        elif backend_type == "vector":
            if not config:
                raise ValueError("Vector database configuration required")
            return VectorWeatherKnowledgeBase(config)
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

# Global weather knowledge base instance
_weather_knowledge_base: Optional[WeatherKnowledgeBaseInterface] = None

def get_weather_knowledge_base() -> WeatherKnowledgeBaseInterface:
    """Get global weather knowledge base instance."""
    global _weather_knowledge_base
    if _weather_knowledge_base is None:
        _weather_knowledge_base = WeatherKnowledgeBaseFactory.create_weather_knowledge_base()
    return _weather_knowledge_base

def set_weather_knowledge_base(knowledge_base: WeatherKnowledgeBaseInterface):
    """Set global weather knowledge base instance."""
    global _weather_knowledge_base
    _weather_knowledge_base = knowledge_base

def reset_weather_knowledge_base():
    """Reset global weather knowledge base instance."""
    global _weather_knowledge_base
    _weather_knowledge_base = None
