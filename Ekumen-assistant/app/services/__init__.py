"""
Services Package - Organized by Agent/Domain

This package contains all services organized by agent and domain for better maintainability.

Structure:
- shared/          - Cross-cutting services used by multiple agents
- weather/         - Weather Agent services
- regulatory/      - Regulatory Agent services  
- crop_health/     - Crop Health Agent services
- farm_data/       - Farm Data Agent services
- planning/        - Planning Agent services
- sustainability/  - Sustainability Agent services
- external/        - External API services
- knowledge_base/  - Knowledge Base services
- admin/           - Admin services
- infrastructure/  - Core infrastructure services
"""

# Import from organized subpackages
from .shared import (
    AuthService,
    ChatService,
    NotificationService,
    SchedulerService,
    ToolRegistryService
)

from .weather import (
    SolarRadiationEstimator,
    PenmanMonteithET0
)

from .regulatory import (
    ConfigurationService,
    get_configuration_service,
    UnifiedRegulatoryService
)

from .crop_health import (
    KnowledgeBaseService
)

from .farm_data import (
    AnalyticsService
)

from .admin import (
    AdminService
)

from .external import (
    TavilyService,
    get_tavily_service
)

from .knowledge_base import (
    KnowledgeBaseWorkflowService,
    RAGService
)

from .infrastructure import (
    AdvancedLangChainService,
    AgentService,
    ErrorRecoveryService,
    FastQueryService,
    JournalService,
    LangGraphWorkflowService,
    LCELChatService,
    get_lcel_chat_service,
    # MemoryPersistenceService removed to avoid circular import
    MultiAgentConversationService,
    # MultiAgentService removed to avoid circular import
    MultiLayerCacheService,
    OptimizedDatabaseService,
    OptimizedLLMService,
    OptimizedStreamingService,
    ParallelExecutorService,
    PerformanceOptimizationService,
    performance_monitor,
    PostgresChatMessageHistory,
    AsyncPostgresChatMessageHistory,
    ProductService,
    QueryComplexityClassifier,
    get_classifier,
    SmartToolSelectorService,
    StreamingService,
    VoiceService
)

__all__ = [
    # Shared Services
    "AuthService",
    "ChatService",
    "NotificationService",
    "SchedulerService",
    "ToolRegistryService",
    
    # Weather Services
    "SolarRadiationEstimator",
    "PenmanMonteithET0",
    
    # Regulatory Services
    "ConfigurationService",
    "get_configuration_service",
    "UnifiedRegulatoryService",
    
    # Crop Health Services
    "KnowledgeBaseService",
    
    # Farm Data Services
    "AnalyticsService",
    
    # Admin Services
    "AdminService",
    
    # External Services
    "TavilyService",
    "get_tavily_service",
    
    # Knowledge Base Services
    "KnowledgeBaseWorkflowService",
    "RAGService",
    
    # Infrastructure Services
    "AdvancedLangChainService",
    "AgentService",
    "ErrorRecoveryService",
    "FastQueryService",
    "JournalService",
    "LangGraphWorkflowService",
    "LCELChatService",
    "get_lcel_chat_service",
    # "MemoryPersistenceService",  # Removed to avoid circular import
    "MultiAgentConversationService",
    # "MultiAgentService",  # Removed to avoid circular import
    "MultiLayerCacheService",
    "OptimizedDatabaseService",
    "OptimizedLLMService",
    "OptimizedStreamingService",
    "ParallelExecutorService",
    "PerformanceOptimizationService",
    "performance_monitor",
    "PostgresChatMessageHistory",
    "AsyncPostgresChatMessageHistory",
    "ProductService",
    "QueryComplexityClassifier",
    "get_classifier",
    "SmartToolSelectorService",
    "StreamingService",
    "VoiceService"
]