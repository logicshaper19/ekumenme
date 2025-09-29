"""
Unit tests for Unified Router Service.

Tests:
- Pattern-based routing
- Query complexity classification
- Execution path selection
- Cache functionality
- Performance metrics
"""

import pytest
import asyncio
from app.services.unified_router_service import (
    UnifiedRouterService,
    QueryComplexity,
    ExecutionPath,
    RoutingDecision
)


class TestUnifiedRouterService:
    """Test suite for Unified Router Service"""
    
    @pytest.fixture
    def router(self):
        """Create router instance for testing"""
        return UnifiedRouterService()
    
    # Test simple queries
    @pytest.mark.asyncio
    async def test_simple_query_bonjour(self, router):
        """Test simple conversational query"""
        decision = await router.route_query("Bonjour, comment ça va?")
        
        assert decision.complexity == QueryComplexity.SIMPLE
        assert decision.execution_path == ExecutionPath.DIRECT_ANSWER
        assert len(decision.required_tools) == 0
        assert decision.use_gpt4 == False
        assert decision.confidence >= 0.9
    
    @pytest.mark.asyncio
    async def test_simple_query_merci(self, router):
        """Test simple thank you query"""
        decision = await router.route_query("Merci beaucoup!")
        
        assert decision.complexity == QueryComplexity.SIMPLE
        assert decision.execution_path == ExecutionPath.DIRECT_ANSWER
        assert decision.use_gpt4 == False
    
    # Test fast path queries
    @pytest.mark.asyncio
    async def test_fast_path_weather(self, router):
        """Test weather query routes to fast path"""
        decision = await router.route_query("Quelle est la météo à Dourdan?")
        
        assert decision.complexity == QueryComplexity.FAST
        assert decision.execution_path == ExecutionPath.FAST_PATH
        assert "weather" in decision.required_tools
        assert decision.use_gpt4 == False
        assert decision.estimated_time <= 5.0
    
    @pytest.mark.asyncio
    async def test_fast_path_regulatory(self, router):
        """Test regulatory query routes to fast path"""
        decision = await router.route_query("Quel est le code AMM pour ce produit?")
        
        assert decision.complexity == QueryComplexity.FAST
        assert decision.execution_path == ExecutionPath.FAST_PATH
        assert "regulatory" in decision.required_tools
        assert decision.use_gpt4 == False
    
    @pytest.mark.asyncio
    async def test_fast_path_farm_data(self, router):
        """Test farm data query routes to fast path"""
        decision = await router.route_query("Quelle est la surface de ma parcelle?")
        
        assert decision.complexity == QueryComplexity.FAST
        assert decision.execution_path == ExecutionPath.FAST_PATH
        assert "farm_data" in decision.required_tools
    
    # Test medium path queries
    @pytest.mark.asyncio
    async def test_medium_path_treatment(self, router):
        """Test treatment query routes to medium path"""
        decision = await router.route_query(
            "Quel traitement pour mes plants de colza contre les limaces?"
        )
        
        assert decision.complexity == QueryComplexity.MEDIUM
        assert decision.execution_path == ExecutionPath.STANDARD_PATH
        assert len(decision.required_tools) > 1
        assert decision.use_gpt4 == False
        assert decision.estimated_time <= 20.0
    
    @pytest.mark.asyncio
    async def test_medium_path_disease(self, router):
        """Test disease diagnosis routes to medium path"""
        decision = await router.route_query(
            "Mes plants ont des taches jaunes, qu'est-ce que c'est?"
        )
        
        assert decision.complexity == QueryComplexity.MEDIUM
        assert decision.execution_path == ExecutionPath.STANDARD_PATH
    
    # Test complex path queries
    @pytest.mark.asyncio
    async def test_complex_path_full_analysis(self, router):
        """Test complex analysis routes to workflow path"""
        decision = await router.route_query(
            "Analyse complète de la faisabilité de cultiver du café à Dourdan"
        )
        
        assert decision.complexity == QueryComplexity.COMPLEX
        assert decision.execution_path == ExecutionPath.WORKFLOW_PATH
        assert len(decision.required_tools) >= 3
        assert decision.use_gpt4 == True
        assert decision.estimated_time >= 20.0
    
    @pytest.mark.asyncio
    async def test_complex_path_detailed_plan(self, router):
        """Test detailed planning routes to workflow path"""
        decision = await router.route_query(
            "Plan détaillé pour optimiser ma production de blé"
        )
        
        assert decision.complexity == QueryComplexity.COMPLEX
        assert decision.execution_path == ExecutionPath.WORKFLOW_PATH
        assert decision.use_gpt4 == True
    
    # Test caching
    @pytest.mark.asyncio
    async def test_cache_hit(self, router):
        """Test cache hit for repeated query"""
        query = "Quelle est la météo?"
        
        # First call - cache miss
        decision1 = await router.route_query(query)
        cache_stats1 = router.get_cache_stats()
        assert cache_stats1["cache_misses"] == 1
        
        # Second call - cache hit
        decision2 = await router.route_query(query)
        cache_stats2 = router.get_cache_stats()
        assert cache_stats2["cache_hits"] == 1
        
        # Decisions should be identical
        assert decision1.complexity == decision2.complexity
        assert decision1.execution_path == decision2.execution_path
    
    @pytest.mark.asyncio
    async def test_cache_different_queries(self, router):
        """Test cache miss for different queries"""
        decision1 = await router.route_query("Quelle est la météo?")
        decision2 = await router.route_query("Quel est le prix du blé?")
        
        cache_stats = router.get_cache_stats()
        assert cache_stats["cache_misses"] == 2
        assert cache_stats["cache_hits"] == 0
    
    # Test cache key generation
    def test_cache_key_generation(self, router):
        """Test cache key generation"""
        key1 = router._generate_cache_key("test query", None)
        key2 = router._generate_cache_key("test query", None)
        key3 = router._generate_cache_key("different query", None)
        
        assert key1 == key2  # Same query = same key
        assert key1 != key3  # Different query = different key
    
    def test_cache_key_with_context(self, router):
        """Test cache key with context"""
        context1 = {"user_id": "123", "farm_siret": "456"}
        context2 = {"user_id": "123", "farm_siret": "456"}
        context3 = {"user_id": "789", "farm_siret": "456"}
        
        key1 = router._generate_cache_key("test", context1)
        key2 = router._generate_cache_key("test", context2)
        key3 = router._generate_cache_key("test", context3)
        
        assert key1 == key2  # Same context = same key
        assert key1 != key3  # Different context = different key
    
    # Test pattern matching
    def test_pattern_matching_simple(self, router):
        """Test simple pattern matching"""
        decision = router._pattern_based_routing("Bonjour", None)
        assert decision.complexity == QueryComplexity.SIMPLE
    
    def test_pattern_matching_weather(self, router):
        """Test weather pattern matching"""
        decision = router._pattern_based_routing("météo", None)
        assert "weather" in decision.required_tools
    
    def test_pattern_matching_regulatory(self, router):
        """Test regulatory pattern matching"""
        decision = router._pattern_based_routing("AMM produit phyto", None)
        assert "regulatory" in decision.required_tools
    
    # Test confidence scores
    @pytest.mark.asyncio
    async def test_high_confidence_simple(self, router):
        """Test high confidence for simple queries"""
        decision = await router.route_query("Bonjour")
        assert decision.confidence >= 0.9
    
    @pytest.mark.asyncio
    async def test_high_confidence_weather(self, router):
        """Test high confidence for weather queries"""
        decision = await router.route_query("Quelle est la météo?")
        assert decision.confidence >= 0.85
    
    # Test edge cases
    @pytest.mark.asyncio
    async def test_empty_query(self, router):
        """Test empty query handling"""
        decision = await router.route_query("")
        assert decision is not None
        assert decision.complexity == QueryComplexity.SIMPLE
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, router):
        """Test very long query handling"""
        long_query = "météo " * 100
        decision = await router.route_query(long_query)
        assert decision is not None
    
    # Test cache statistics
    @pytest.mark.asyncio
    async def test_cache_statistics(self, router):
        """Test cache statistics tracking"""
        # Make several queries
        await router.route_query("météo")
        await router.route_query("météo")  # Cache hit
        await router.route_query("AMM")
        await router.route_query("AMM")  # Cache hit
        
        stats = router.get_cache_stats()
        assert stats["total_requests"] == 4
        assert stats["cache_hits"] == 2
        assert stats["cache_misses"] == 2
        assert stats["hit_rate"] == 0.5
    
    # Test cache size limit
    @pytest.mark.asyncio
    async def test_cache_size_limit(self, router):
        """Test cache size limit enforcement"""
        # Fill cache beyond limit
        for i in range(1100):
            await router.route_query(f"query {i}")
        
        stats = router.get_cache_stats()
        assert stats["cache_size"] <= 1000  # Should be limited to 1000
    
    # Test performance
    @pytest.mark.asyncio
    async def test_routing_performance(self, router):
        """Test routing performance is fast"""
        import time
        
        start = time.time()
        decision = await router.route_query("Quelle est la météo?")
        elapsed = time.time() - start
        
        # Routing should be very fast (< 100ms for pattern-based)
        assert elapsed < 0.1
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, router):
        """Test cache hit performance"""
        import time
        
        # First call
        await router.route_query("météo")
        
        # Second call (cached)
        start = time.time()
        decision = await router.route_query("météo")
        elapsed = time.time() - start
        
        # Cache hit should be extremely fast (< 10ms)
        assert elapsed < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

