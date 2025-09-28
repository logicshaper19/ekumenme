"""
Agricultural Agent Prompts

This module contains all prompt templates for the agricultural chatbot agents.
Each agent has specialized prompts designed for French agricultural context.

PHASE 3 COMPLETE - PROMPT CENTRALIZATION:
- Centralized prompt management
- Version control and A/B testing
- Performance tracking
- Clean separation of concerns
"""

# Base Prompts - Shared Templates
from .base_prompts import (
    BASE_AGRICULTURAL_SYSTEM_PROMPT,
    FARM_CONTEXT_TEMPLATE,
    WEATHER_CONTEXT_TEMPLATE,
    INTERVENTION_CONTEXT_TEMPLATE,
    REGULATORY_CONTEXT_TEMPLATE,
    DIAGNOSTIC_CONTEXT_TEMPLATE,
    PLANNING_CONTEXT_TEMPLATE,
    SUSTAINABILITY_CONTEXT_TEMPLATE,
    RESPONSE_FORMAT_TEMPLATE,
    SAFETY_REMINDER_TEMPLATE,
    FEW_SHOT_EXAMPLES
)

# Farm Data Agent Prompts
from .farm_data_prompts import (
    FARM_DATA_SYSTEM_PROMPT,
    FARM_DATA_CHAT_PROMPT,
    PARCEL_ANALYSIS_PROMPT,
    PERFORMANCE_METRICS_PROMPT,
    INTERVENTION_TRACKING_PROMPT,
    COST_ANALYSIS_PROMPT,
    TREND_ANALYSIS_PROMPT
)

# Regulatory Agent Prompts
from .regulatory_prompts import (
    REGULATORY_SYSTEM_PROMPT,
    REGULATORY_CHAT_PROMPT,
    AMM_LOOKUP_PROMPT,
    USAGE_CONDITIONS_PROMPT,
    SAFETY_CLASSIFICATIONS_PROMPT,
    PRODUCT_SUBSTITUTION_PROMPT,
    COMPLIANCE_CHECK_PROMPT,
    ENVIRONMENTAL_REGULATIONS_PROMPT
)

# Weather Agent Prompts
from .weather_prompts import (
    WEATHER_SYSTEM_PROMPT,
    WEATHER_CHAT_PROMPT,
    WEATHER_FORECAST_PROMPT,
    INTERVENTION_WINDOW_PROMPT,
    WEATHER_RISK_ANALYSIS_PROMPT,
    IRRIGATION_PLANNING_PROMPT,
    EVAPOTRANSPIRATION_PROMPT,
    CLIMATE_ADAPTATION_PROMPT
)

# Crop Health Agent Prompts
from .crop_health_prompts import (
    CROP_HEALTH_SYSTEM_PROMPT,
    CROP_HEALTH_CHAT_PROMPT,
    DISEASE_DIAGNOSIS_PROMPT,
    PEST_IDENTIFICATION_PROMPT,
    NUTRIENT_DEFICIENCY_PROMPT,
    TREATMENT_PLAN_PROMPT,
    RESISTANCE_MANAGEMENT_PROMPT,
    BIOLOGICAL_CONTROL_PROMPT,
    THRESHOLD_MANAGEMENT_PROMPT
)

# Planning Agent Prompts
from .planning_prompts import (
    PLANNING_SYSTEM_PROMPT,
    PLANNING_CHAT_PROMPT,
    TASK_PLANNING_PROMPT,
    RESOURCE_OPTIMIZATION_PROMPT,
    SEASONAL_PLANNING_PROMPT,
    WEATHER_DEPENDENT_PLANNING_PROMPT,
    COST_OPTIMIZATION_PROMPT,
    EMERGENCY_PLANNING_PROMPT,
    WORKFLOW_OPTIMIZATION_PROMPT
)

# Sustainability Agent Prompts
from .sustainability_prompts import (
    SUSTAINABILITY_SYSTEM_PROMPT,
    SUSTAINABILITY_CHAT_PROMPT,
    CARBON_FOOTPRINT_PROMPT,
    BIODIVERSITY_ASSESSMENT_PROMPT,
    SOIL_HEALTH_PROMPT,
    WATER_MANAGEMENT_PROMPT,
    ENERGY_EFFICIENCY_PROMPT,
    CERTIFICATION_SUPPORT_PROMPT,
    CIRCULAR_ECONOMY_PROMPT,
    CLIMATE_ADAPTATION_PROMPT
)

# Orchestrator Prompts
from .orchestrator_prompts import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    ORCHESTRATOR_ROUTING_PROMPT,
    AGENT_SELECTION_PROMPT,
    RESPONSE_SYNTHESIS_PROMPT,
    CONFLICT_RESOLUTION_PROMPT,
    QUALITY_ASSURANCE_PROMPT,
    PERFORMANCE_MONITORING_PROMPT,
    ERROR_HANDLING_PROMPT,
    LOAD_BALANCING_PROMPT
)

# Prompt Management
from .prompt_manager import (
    PromptManager,
    PromptVersion,
    PromptMetrics,
    PromptConfig,
    prompt_manager,
    get_prompt,
    update_prompt_version,
    log_prompt_performance,
    select_prompt_semantic,
    get_prompt_semantic,
    set_routing_method,
    get_routing_method,
    add_intent_example,
    get_semantic_analytics
)

# Semantic Routing
from .semantic_routing import (
    SemanticIntentClassifier,
    IntentType,
    IntentExample,
    IntentClassification,
    semantic_classifier,
    classify_intent,
    get_prompt_for_query
)

# Embedding System
from .embedding_system import (
    EmbeddingPromptMatcher,
    PromptEmbedding,
    PromptMatch,
    embedding_matcher,
    find_best_prompt,
    find_prompt_by_intent,
    get_prompt_name_for_query
)

# Semantic Orchestrator Prompts
from .semantic_orchestrator_prompts import (
    SEMANTIC_ORCHESTRATOR_SYSTEM_PROMPT,
    SEMANTIC_INTENT_CLASSIFICATION_PROMPT,
    SEMANTIC_AGENT_SELECTION_PROMPT,
    SEMANTIC_RESPONSE_SYNTHESIS_PROMPT,
    SEMANTIC_CONFLICT_RESOLUTION_PROMPT,
    SEMANTIC_QUALITY_ASSURANCE_PROMPT,
    SEMANTIC_PERFORMANCE_MONITORING_PROMPT
)

# Dynamic Examples System
from .dynamic_examples import (
    DynamicFewShotManager,
    FewShotExample,
    DynamicExampleConfig,
    ExampleType,
    dynamic_examples_manager,
    get_dynamic_examples,
    add_few_shot_example,
    get_example_stats
)

__all__ = [
    # Base Prompts
    "BASE_AGRICULTURAL_SYSTEM_PROMPT",
    "FARM_CONTEXT_TEMPLATE",
    "WEATHER_CONTEXT_TEMPLATE",
    "INTERVENTION_CONTEXT_TEMPLATE",
    "REGULATORY_CONTEXT_TEMPLATE",
    "DIAGNOSTIC_CONTEXT_TEMPLATE",
    "PLANNING_CONTEXT_TEMPLATE",
    "SUSTAINABILITY_CONTEXT_TEMPLATE",
    "RESPONSE_FORMAT_TEMPLATE",
    "SAFETY_REMINDER_TEMPLATE",
    "FEW_SHOT_EXAMPLES",
    
    # Farm Data Agent Prompts
    "FARM_DATA_SYSTEM_PROMPT",
    "FARM_DATA_CHAT_PROMPT",
    "PARCEL_ANALYSIS_PROMPT",
    "PERFORMANCE_METRICS_PROMPT",
    "INTERVENTION_TRACKING_PROMPT",
    "COST_ANALYSIS_PROMPT",
    "TREND_ANALYSIS_PROMPT",
    
    # Regulatory Agent Prompts
    "REGULATORY_SYSTEM_PROMPT",
    "REGULATORY_CHAT_PROMPT",
    "AMM_LOOKUP_PROMPT",
    "USAGE_CONDITIONS_PROMPT",
    "SAFETY_CLASSIFICATIONS_PROMPT",
    "PRODUCT_SUBSTITUTION_PROMPT",
    "COMPLIANCE_CHECK_PROMPT",
    "ENVIRONMENTAL_REGULATIONS_PROMPT",
    
    # Weather Agent Prompts
    "WEATHER_SYSTEM_PROMPT",
    "WEATHER_CHAT_PROMPT",
    "WEATHER_FORECAST_PROMPT",
    "INTERVENTION_WINDOW_PROMPT",
    "WEATHER_RISK_ANALYSIS_PROMPT",
    "IRRIGATION_PLANNING_PROMPT",
    "EVAPOTRANSPIRATION_PROMPT",
    "CLIMATE_ADAPTATION_PROMPT",
    
    # Crop Health Agent Prompts
    "CROP_HEALTH_SYSTEM_PROMPT",
    "CROP_HEALTH_CHAT_PROMPT",
    "DISEASE_DIAGNOSIS_PROMPT",
    "PEST_IDENTIFICATION_PROMPT",
    "NUTRIENT_DEFICIENCY_PROMPT",
    "TREATMENT_PLAN_PROMPT",
    "RESISTANCE_MANAGEMENT_PROMPT",
    "BIOLOGICAL_CONTROL_PROMPT",
    "THRESHOLD_MANAGEMENT_PROMPT",
    
    # Planning Agent Prompts
    "PLANNING_SYSTEM_PROMPT",
    "PLANNING_CHAT_PROMPT",
    "TASK_PLANNING_PROMPT",
    "RESOURCE_OPTIMIZATION_PROMPT",
    "SEASONAL_PLANNING_PROMPT",
    "WEATHER_DEPENDENT_PLANNING_PROMPT",
    "COST_OPTIMIZATION_PROMPT",
    "EMERGENCY_PLANNING_PROMPT",
    "WORKFLOW_OPTIMIZATION_PROMPT",
    
    # Sustainability Agent Prompts
    "SUSTAINABILITY_SYSTEM_PROMPT",
    "SUSTAINABILITY_CHAT_PROMPT",
    "CARBON_FOOTPRINT_PROMPT",
    "BIODIVERSITY_ASSESSMENT_PROMPT",
    "SOIL_HEALTH_PROMPT",
    "WATER_MANAGEMENT_PROMPT",
    "ENERGY_EFFICIENCY_PROMPT",
    "CERTIFICATION_SUPPORT_PROMPT",
    "CIRCULAR_ECONOMY_PROMPT",
    "CLIMATE_ADAPTATION_PROMPT",
    
    # Orchestrator Prompts
    "ORCHESTRATOR_SYSTEM_PROMPT",
    "ORCHESTRATOR_ROUTING_PROMPT",
    "AGENT_SELECTION_PROMPT",
    "RESPONSE_SYNTHESIS_PROMPT",
    "CONFLICT_RESOLUTION_PROMPT",
    "QUALITY_ASSURANCE_PROMPT",
    "PERFORMANCE_MONITORING_PROMPT",
    "ERROR_HANDLING_PROMPT",
    "LOAD_BALANCING_PROMPT",
    
    # Prompt Management
    "PromptManager",
    "PromptVersion",
    "PromptMetrics",
    "PromptConfig",
    "prompt_manager",
    "get_prompt",
    "update_prompt_version",
    "log_prompt_performance",
    "select_prompt_semantic",
    "get_prompt_semantic",
    "set_routing_method",
    "get_routing_method",
    "add_intent_example",
    "get_semantic_analytics",
    
    # Semantic Routing
    "SemanticIntentClassifier",
    "IntentType",
    "IntentExample",
    "IntentClassification",
    "semantic_classifier",
    "classify_intent",
    "get_prompt_for_query",
    
    # Embedding System
    "EmbeddingPromptMatcher",
    "PromptEmbedding",
    "PromptMatch",
    "embedding_matcher",
    "find_best_prompt",
    "find_prompt_by_intent",
    "get_prompt_name_for_query",
    
    # Semantic Orchestrator Prompts
    "SEMANTIC_ORCHESTRATOR_SYSTEM_PROMPT",
    "SEMANTIC_INTENT_CLASSIFICATION_PROMPT",
    "SEMANTIC_AGENT_SELECTION_PROMPT",
    "SEMANTIC_RESPONSE_SYNTHESIS_PROMPT",
    "SEMANTIC_CONFLICT_RESOLUTION_PROMPT",
    "SEMANTIC_QUALITY_ASSURANCE_PROMPT",
    "SEMANTIC_PERFORMANCE_MONITORING_PROMPT",
    
    # Dynamic Examples System
    "DynamicFewShotManager",
    "FewShotExample",
    "DynamicExampleConfig",
    "ExampleType",
    "dynamic_examples_manager",
    "get_dynamic_examples",
    "add_few_shot_example",
    "get_example_stats"
]