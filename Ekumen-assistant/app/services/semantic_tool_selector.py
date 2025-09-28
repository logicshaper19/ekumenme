"""
Semantic Tool Selection Service
Production-ready tool selection with configuration-based profiles, consistent scoring, and robust fallback mechanisms.
"""

import logging
import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
import time

# Optional imports for enhanced functionality
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SentenceTransformer = None
    np = None
    cosine_similarity = None

logger = logging.getLogger(__name__)

@dataclass
class ToolSelectionResult:
    """Enhanced result of tool selection process with detailed metadata."""
    selected_tools: List[str]
    tool_scores: Dict[str, float]
    selection_method: str
    confidence_tier: str
    overall_confidence: float
    reasoning: str
    alternative_tools: List[Tuple[str, float]]
    execution_time_ms: float
    language_detected: str
    fallback_applied: bool = False
    user_feedback_id: Optional[str] = None

@dataclass
class ToolProfile:
    """Enhanced tool profile with comprehensive metadata."""
    id: str
    name: Dict[str, str]
    description: Dict[str, str]
    domain: str
    subdomain: str
    complexity: str
    priority: int
    keywords: Dict[str, Dict[str, List[str]]]
    intent_patterns: Dict[str, List[str]]
    use_cases: Dict[str, List[str]]
    input_parameters: List[Dict[str, Any]]
    output_types: List[str]
    related_tools: List[str]
    exclusions: List[str]
    performance_metrics: Dict[str, float]
    embedding_cache: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[str] = None

class LanguageDetector:
    """Simple language detection for French/English agricultural text."""
    
    FRENCH_INDICATORS = {
        'articles': ['le', 'la', 'les', 'du', 'de', 'des', 'un', 'une'],
        'prepositions': ['sur', 'dans', 'avec', 'pour', 'par', 'sans'],
        'agricultural': ['blé', 'maïs', 'colza', 'maladie', 'ravageur', 'traitement']
    }
    
    ENGLISH_INDICATORS = {
        'articles': ['the', 'a', 'an'],
        'prepositions': ['on', 'in', 'with', 'for', 'by', 'without'],
        'agricultural': ['wheat', 'corn', 'disease', 'pest', 'treatment', 'crop']
    }
    
    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect language of input text."""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        french_score = 0
        english_score = 0
        
        for word in words:
            # Check French indicators
            for category, indicators in cls.FRENCH_INDICATORS.items():
                if word in indicators:
                    french_score += 2 if category == 'agricultural' else 1
            
            # Check English indicators
            for category, indicators in cls.ENGLISH_INDICATORS.items():
                if word in indicators:
                    english_score += 2 if category == 'agricultural' else 1
        
        return 'fr' if french_score > english_score else 'en'

class ScoringNormalizer:
    """Consistent scoring normalization across all selection methods."""
    
    @staticmethod
    def normalize_semantic_score(similarity: float) -> float:
        """Normalize semantic similarity score (already 0-1)."""
        return max(0.0, min(1.0, similarity))
    
    @staticmethod
    def normalize_keyword_score(matches: int, total_keywords: int, query_length: int) -> float:
        """Normalize keyword matching score to 0-1 scale."""
        if total_keywords == 0:
            return 0.0
        
        # Base score from keyword matches
        base_score = matches / total_keywords
        
        # Boost for query length (longer queries are more specific)
        length_boost = min(0.2, query_length / 100)
        
        # Apply diminishing returns
        normalized = base_score + length_boost
        return max(0.0, min(1.0, normalized))
    
    @staticmethod
    def normalize_intent_score(pattern_matches: int, total_patterns: int, confidence_modifier: float = 1.0) -> float:
        """Normalize intent classification score to 0-1 scale."""
        if total_patterns == 0:
            return 0.0
        
        base_score = pattern_matches / total_patterns
        adjusted_score = base_score * confidence_modifier
        return max(0.0, min(1.0, adjusted_score))
    
    @staticmethod
    def get_confidence_tier(score: float, tiers: List[Dict[str, Any]]) -> str:
        """Get confidence tier based on score and configuration."""
        for tier in sorted(tiers, key=lambda x: x['min_score'], reverse=True):
            if score >= tier['min_score']:
                return tier['tier']
        return 'fallback'

class SemanticToolSelector:
    """
    Production-ready semantic tool selector with:
    - Configuration-based tool profiles
    - Consistent scoring normalization
    - Robust fallback mechanisms
    - Language detection
    - Performance optimization
    - User feedback integration
    """
    
    def __init__(self, config_path: Optional[str] = None, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize semantic tool selector."""
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), '..', 'config', 'tool_profiles.json')
        self.model_name = model_name
        
        # Initialize components
        self.language_detector = LanguageDetector()
        self.scoring_normalizer = ScoringNormalizer()
        
        # Load configuration
        self.config = self._load_configuration()
        self.tool_profiles = self._load_tool_profiles()
        
        # Initialize semantic model if available
        self.encoder = None
        self._initialize_semantic_model()
        
        # Performance tracking
        self.performance_stats = {
            'total_queries': 0,
            'avg_response_time_ms': 0,
            'cache_hits': 0,
            'fallback_usage': 0
        }
        
        logger.info(f"Enhanced Semantic Tool Selector initialized with {len(self.tool_profiles)} tools")
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Return minimal default configuration
            return {
                "version": "1.0",
                "default_language": "fr",
                "supported_languages": ["fr", "en"],
                "scoring_config": {
                    "semantic_weight": 0.4,
                    "keyword_weight": 0.35,
                    "intent_weight": 0.25,
                    "confidence_tiers": [
                        {"min_score": 0.8, "tier": "high"},
                        {"min_score": 0.6, "tier": "medium"},
                        {"min_score": 0.4, "tier": "low"},
                        {"min_score": 0.0, "tier": "fallback"}
                    ]
                },
                "tools": {}
            }
    
    def _load_tool_profiles(self) -> Dict[str, ToolProfile]:
        """Load tool profiles from configuration."""
        profiles = {}
        
        for tool_id, tool_data in self.config.get('tools', {}).items():
            try:
                profile = ToolProfile(
                    id=tool_data['id'],
                    name=tool_data['name'],
                    description=tool_data['description'],
                    domain=tool_data['domain'],
                    subdomain=tool_data['subdomain'],
                    complexity=tool_data['complexity'],
                    priority=tool_data['priority'],
                    keywords=tool_data['keywords'],
                    intent_patterns=tool_data['intent_patterns'],
                    use_cases=tool_data['use_cases'],
                    input_parameters=tool_data['input_parameters'],
                    output_types=tool_data['output_types'],
                    related_tools=tool_data['related_tools'],
                    exclusions=tool_data['exclusions'],
                    performance_metrics=tool_data['performance_metrics']
                )
                profiles[tool_id] = profile
                
            except Exception as e:
                logger.error(f"Failed to load profile for tool {tool_id}: {e}")
        
        logger.info(f"Loaded {len(profiles)} tool profiles")
        return profiles
    
    def _initialize_semantic_model(self):
        """Initialize semantic model with error handling."""
        if not SEMANTIC_AVAILABLE:
            logger.info("Sentence transformers not available, using keyword/intent methods only")
            return
        
        try:
            self.encoder = SentenceTransformer(self.model_name)
            logger.info(f"Loaded semantic model: {self.model_name}")
            
            # Pre-generate embeddings for tool profiles
            self._generate_embeddings()
            
        except Exception as e:
            logger.warning(f"Failed to load semantic model: {e}, falling back to keyword/intent methods")
            self.encoder = None
    
    @lru_cache(maxsize=1000)
    def _get_embedding(self, text: str, language: str) -> Optional[Any]:
        """Get cached embedding for text."""
        if not self.encoder:
            return None
        
        try:
            return self.encoder.encode(text)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def _generate_embeddings(self):
        """Pre-generate embeddings for all tool profiles."""
        if not self.encoder:
            return
        
        for tool_id, profile in self.tool_profiles.items():
            for lang in self.config['supported_languages']:
                if lang in profile.description:
                    # Create comprehensive text for embedding
                    text_parts = [
                        profile.description[lang],
                        ' '.join(profile.keywords.get(lang, {}).get('primary', [])),
                        ' '.join(profile.use_cases.get(lang, []))
                    ]
                    text = ' '.join(text_parts)
                    
                    # Generate and cache embedding
                    embedding = self._get_embedding(text, lang)
                    if embedding is not None:
                        profile.embedding_cache[lang] = embedding
        
        logger.info("Generated embeddings for all tool profiles")
    
    def select_tools(
        self,
        message: str,
        available_tools: List[str],
        method: str = "hybrid",
        threshold: float = 0.4,
        max_tools: int = 3,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ToolSelectionResult:
        """
        Enhanced tool selection with comprehensive error handling and performance tracking.
        """
        start_time = time.time()
        
        try:
            # Detect language
            detected_language = self.language_detector.detect_language(message)
            
            # Filter available tools to only those in our profiles
            valid_tools = [tool for tool in available_tools if tool in self.tool_profiles]
            
            if not valid_tools:
                return self._create_empty_result(message, method, detected_language, start_time)
            
            # Select appropriate method
            if method == "semantic" and self.encoder:
                result = self._select_tools_semantic(message, valid_tools, threshold, max_tools, detected_language)
            elif method == "keyword":
                result = self._select_tools_keyword(message, valid_tools, threshold, max_tools, detected_language)
            elif method == "intent":
                result = self._select_tools_intent(message, valid_tools, threshold, max_tools, detected_language)
            elif method == "hybrid":
                result = self._select_tools_hybrid(message, valid_tools, threshold, max_tools, detected_language)
            else:
                # Fallback to best available method
                if self.encoder:
                    result = self._select_tools_hybrid(message, valid_tools, threshold, max_tools, detected_language)
                else:
                    result = self._select_tools_keyword(message, valid_tools, threshold, max_tools, detected_language)
            
            # Apply gradual fallback if no tools selected
            if not result.selected_tools:
                result = self._apply_gradual_fallback(message, valid_tools, detected_language, result)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time
            
            # Update performance stats
            self._update_performance_stats(execution_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Tool selection failed: {e}")
            return self._create_error_result(message, method, detected_language, start_time, str(e))
    
    def _create_empty_result(self, message: str, method: str, language: str, start_time: float) -> ToolSelectionResult:
        """Create empty result for edge cases."""
        return ToolSelectionResult(
            selected_tools=[],
            tool_scores={},
            selection_method=method,
            confidence_tier="fallback",
            overall_confidence=0.0,
            reasoning="No valid tools available for selection",
            alternative_tools=[],
            execution_time_ms=(time.time() - start_time) * 1000,
            language_detected=language,
            fallback_applied=True
        )

    def _create_error_result(self, message: str, method: str, language: str, start_time: float, error: str) -> ToolSelectionResult:
        """Create error result for exception cases."""
        return ToolSelectionResult(
            selected_tools=[],
            tool_scores={},
            selection_method=f"{method}_error",
            confidence_tier="fallback",
            overall_confidence=0.0,
            reasoning=f"Selection failed due to error: {error}",
            alternative_tools=[],
            execution_time_ms=(time.time() - start_time) * 1000,
            language_detected=language,
            fallback_applied=True
        )

    def _select_tools_semantic(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int,
        language: str
    ) -> ToolSelectionResult:
        """Select tools using semantic similarity with consistent scoring."""
        if not self.encoder:
            return self._select_tools_keyword(message, available_tools, threshold, max_tools, language)

        try:
            # Generate message embedding
            message_embedding = self._get_embedding(message, language)
            if message_embedding is None:
                return self._select_tools_keyword(message, available_tools, threshold, max_tools, language)

            tool_scores = {}

            for tool_id in available_tools:
                profile = self.tool_profiles[tool_id]

                # Get cached embedding for this language
                tool_embedding = profile.embedding_cache.get(language)
                if tool_embedding is not None:
                    # Calculate cosine similarity
                    similarity = cosine_similarity(
                        message_embedding.reshape(1, -1),
                        tool_embedding.reshape(1, -1)
                    )[0][0]

                    # Normalize score
                    normalized_score = self.scoring_normalizer.normalize_semantic_score(similarity)
                    tool_scores[tool_id] = normalized_score

            return self._create_selection_result(
                tool_scores, threshold, max_tools, "semantic", language,
                "Semantic similarity analysis using sentence transformers"
            )

        except Exception as e:
            logger.error(f"Semantic selection failed: {e}")
            return self._select_tools_keyword(message, available_tools, threshold, max_tools, language)

    def _select_tools_keyword(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int,
        language: str
    ) -> ToolSelectionResult:
        """Select tools using enhanced keyword matching with consistent scoring."""
        message_lower = message.lower()
        message_words = re.findall(r'\b\w+\b', message_lower)
        tool_scores = {}

        for tool_id in available_tools:
            profile = self.tool_profiles[tool_id]
            keywords_data = profile.keywords.get(language, {})

            total_matches = 0
            total_keywords = 0

            # Score different keyword categories with weights
            category_weights = {
                'primary': 3.0,
                'secondary': 2.0,
                'symptoms': 1.5,
                'diseases': 1.5,
                'operations': 1.5,
                'objectives': 1.0
            }

            for category, keywords in keywords_data.items():
                weight = category_weights.get(category, 1.0)
                category_matches = sum(1 for keyword in keywords if keyword.lower() in message_lower)
                total_matches += category_matches * weight
                total_keywords += len(keywords) * weight

            # Normalize score
            if total_keywords > 0:
                normalized_score = self.scoring_normalizer.normalize_keyword_score(
                    total_matches, total_keywords, len(message)
                )
                tool_scores[tool_id] = normalized_score

        return self._create_selection_result(
            tool_scores, threshold, max_tools, "keyword", language,
            "Enhanced keyword matching with weighted categories"
        )

    def _select_tools_intent(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int,
        language: str
    ) -> ToolSelectionResult:
        """Select tools using intent pattern matching with consistent scoring."""
        message_lower = message.lower()
        tool_scores = {}

        for tool_id in available_tools:
            profile = self.tool_profiles[tool_id]
            patterns = profile.intent_patterns.get(language, [])

            if not patterns:
                continue

            pattern_matches = 0
            for pattern in patterns:
                try:
                    if re.search(pattern, message_lower):
                        pattern_matches += 1
                except re.error:
                    # Skip invalid regex patterns
                    continue

            # Calculate confidence modifier based on tool priority and performance
            confidence_modifier = 1.0
            if profile.priority == 1:
                confidence_modifier += 0.1
            if profile.performance_metrics.get('success_rate', 0) > 0.9:
                confidence_modifier += 0.05

            # Normalize score
            normalized_score = self.scoring_normalizer.normalize_intent_score(
                pattern_matches, len(patterns), confidence_modifier
            )
            tool_scores[tool_id] = normalized_score

        return self._create_selection_result(
            tool_scores, threshold, max_tools, "intent", language,
            "Intent pattern matching with priority weighting"
        )

    def _select_tools_hybrid(
        self,
        message: str,
        available_tools: List[str],
        threshold: float,
        max_tools: int,
        language: str
    ) -> ToolSelectionResult:
        """Select tools using hybrid approach with consistent score combination."""
        # Get results from all methods
        semantic_result = self._select_tools_semantic(message, available_tools, 0.0, len(available_tools), language)
        keyword_result = self._select_tools_keyword(message, available_tools, 0.0, len(available_tools), language)
        intent_result = self._select_tools_intent(message, available_tools, 0.0, len(available_tools), language)

        # Get weights from configuration
        scoring_config = self.config['scoring_config']
        weights = {
            'semantic': scoring_config['semantic_weight'],
            'keyword': scoring_config['keyword_weight'],
            'intent': scoring_config['intent_weight']
        }

        # Combine scores with weights
        combined_scores = {}
        all_tools = set(available_tools)

        for tool_id in all_tools:
            score = 0.0

            # Add weighted scores (all scores are now normalized to 0-1)
            score += semantic_result.tool_scores.get(tool_id, 0.0) * weights['semantic']
            score += keyword_result.tool_scores.get(tool_id, 0.0) * weights['keyword']
            score += intent_result.tool_scores.get(tool_id, 0.0) * weights['intent']

            combined_scores[tool_id] = score

        # Create reasoning
        method_contributions = []
        if semantic_result.tool_scores:
            method_contributions.append("semantic similarity")
        if keyword_result.tool_scores:
            method_contributions.append("keyword matching")
        if intent_result.tool_scores:
            method_contributions.append("intent patterns")

        reasoning = f"Hybrid selection combining {', '.join(method_contributions)}"

        return self._create_selection_result(
            combined_scores, threshold, max_tools, "hybrid", language, reasoning
        )

    def _create_selection_result(
        self,
        tool_scores: Dict[str, float],
        threshold: float,
        max_tools: int,
        method: str,
        language: str,
        reasoning: str
    ) -> ToolSelectionResult:
        """Create standardized selection result with consistent processing."""

        # Filter tools above threshold
        qualified_tools = {tool: score for tool, score in tool_scores.items() if score >= threshold}

        # Sort by score and limit
        sorted_tools = sorted(qualified_tools.items(), key=lambda x: x[1], reverse=True)
        selected_tools = [tool for tool, _ in sorted_tools[:max_tools]]

        # Calculate overall confidence
        if selected_tools:
            overall_confidence = sum(tool_scores[tool] for tool in selected_tools) / len(selected_tools)
        else:
            overall_confidence = 0.0

        # Determine confidence tier
        confidence_tiers = self.config['scoring_config']['confidence_tiers']
        confidence_tier = self.scoring_normalizer.get_confidence_tier(overall_confidence, confidence_tiers)

        # Get alternatives (tools not selected but with scores)
        alternatives = [
            (tool, score) for tool, score in sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
            if tool not in selected_tools
        ][:3]

        return ToolSelectionResult(
            selected_tools=selected_tools,
            tool_scores=tool_scores,
            selection_method=method,
            confidence_tier=confidence_tier,
            overall_confidence=overall_confidence,
            reasoning=reasoning,
            alternative_tools=alternatives,
            execution_time_ms=0.0,  # Will be set by caller
            language_detected=language,
            fallback_applied=False
        )

    def _apply_gradual_fallback(
        self,
        message: str,
        available_tools: List[str],
        language: str,
        original_result: ToolSelectionResult
    ) -> ToolSelectionResult:
        """Apply gradual fallback strategy when no tools are selected."""

        # Try with progressively lower thresholds
        fallback_thresholds = [0.3, 0.2, 0.1, 0.05]

        for threshold in fallback_thresholds:
            # Try hybrid method first
            if self.encoder:
                result = self._select_tools_hybrid(message, available_tools, threshold, 2, language)
            else:
                result = self._select_tools_keyword(message, available_tools, threshold, 2, language)

            if result.selected_tools:
                result.fallback_applied = True
                result.reasoning = f"Fallback applied with threshold {threshold}: {result.reasoning}"
                self.performance_stats['fallback_usage'] += 1
                return result

        # Final fallback: select highest scoring tool if any scores exist
        if original_result.tool_scores:
            best_tool = max(original_result.tool_scores.items(), key=lambda x: x[1])
            if best_tool[1] > 0:
                return ToolSelectionResult(
                    selected_tools=[best_tool[0]],
                    tool_scores=original_result.tool_scores,
                    selection_method=f"{original_result.selection_method}_final_fallback",
                    confidence_tier="fallback",
                    overall_confidence=best_tool[1],
                    reasoning=f"Final fallback: selected highest scoring tool {best_tool[0]} (score: {best_tool[1]:.3f})",
                    alternative_tools=[],
                    execution_time_ms=0.0,
                    language_detected=language,
                    fallback_applied=True
                )

        # No tools could be selected
        original_result.fallback_applied = True
        original_result.reasoning = "No tools could be selected even with fallback strategies"
        return original_result

    def _update_performance_stats(self, execution_time_ms: float):
        """Update performance statistics."""
        self.performance_stats['total_queries'] += 1

        # Update average response time
        total_queries = self.performance_stats['total_queries']
        current_avg = self.performance_stats['avg_response_time_ms']
        new_avg = ((current_avg * (total_queries - 1)) + execution_time_ms) / total_queries
        self.performance_stats['avg_response_time_ms'] = new_avg

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return self.performance_stats.copy()

    def add_tool_profile(self, tool_data: Dict[str, Any]) -> bool:
        """Add a new tool profile dynamically."""
        try:
            tool_id = tool_data['id']
            profile = ToolProfile(
                id=tool_data['id'],
                name=tool_data['name'],
                description=tool_data['description'],
                domain=tool_data['domain'],
                subdomain=tool_data['subdomain'],
                complexity=tool_data['complexity'],
                priority=tool_data['priority'],
                keywords=tool_data['keywords'],
                intent_patterns=tool_data['intent_patterns'],
                use_cases=tool_data['use_cases'],
                input_parameters=tool_data['input_parameters'],
                output_types=tool_data['output_types'],
                related_tools=tool_data['related_tools'],
                exclusions=tool_data['exclusions'],
                performance_metrics=tool_data['performance_metrics']
            )

            self.tool_profiles[tool_id] = profile

            # Generate embeddings for new tool
            if self.encoder:
                for lang in self.config['supported_languages']:
                    if lang in profile.description:
                        text_parts = [
                            profile.description[lang],
                            ' '.join(profile.keywords.get(lang, {}).get('primary', [])),
                            ' '.join(profile.use_cases.get(lang, []))
                        ]
                        text = ' '.join(text_parts)
                        embedding = self._get_embedding(text, lang)
                        if embedding is not None:
                            profile.embedding_cache[lang] = embedding

            logger.info(f"Added tool profile: {tool_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add tool profile: {e}")
            return False

    def update_tool_performance(self, tool_id: str, metrics: Dict[str, float]):
        """Update performance metrics for a tool."""
        if tool_id in self.tool_profiles:
            self.tool_profiles[tool_id].performance_metrics.update(metrics)
            logger.info(f"Updated performance metrics for {tool_id}")

    def get_tool_profile(self, tool_id: str) -> Optional[ToolProfile]:
        """Get tool profile by ID."""
        return self.tool_profiles.get(tool_id)

    def list_tools_by_domain(self, domain: str) -> List[str]:
        """List tools by domain."""
        return [
            tool_id for tool_id, profile in self.tool_profiles.items()
            if profile.domain == domain
        ]

    def get_available_domains(self) -> List[str]:
        """Get list of available domains."""
        return list(set(profile.domain for profile in self.tool_profiles.values()))

    def reload_configuration(self) -> bool:
        """Reload configuration from file."""
        try:
            self.config = self._load_configuration()
            self.tool_profiles = self._load_tool_profiles()

            # Regenerate embeddings if semantic model is available
            if self.encoder:
                self._generate_embeddings()

            logger.info("Configuration reloaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False


# Global instance for backward compatibility
semantic_tool_selector = SemanticToolSelector()

# Convenience functions
def select_tools_enhanced(
    message: str,
    available_tools: List[str],
    method: str = "hybrid",
    threshold: float = 0.4,
    max_tools: int = 3,
    user_context: Optional[Dict[str, Any]] = None
) -> ToolSelectionResult:
    """Enhanced tool selection with production-ready features."""
    return enhanced_semantic_tool_selector.select_tools(
        message, available_tools, method, threshold, max_tools, user_context
    )
