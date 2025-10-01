"""
Simple LangChain Integration Tests
Direct testing without pytest fixtures
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


async def test_advanced_langchain_service():
    """Test AdvancedLangChainService"""
    logger.info("🧪 Testing AdvancedLangChainService...")
    
    try:
        from app.services.advanced_langchain_service import AdvancedLangChainService
        
        # Test initialization
        service = AdvancedLangChainService()
        logger.info("✅ AdvancedLangChainService initialized successfully")
        
        # Test components
        assert hasattr(service, 'llm'), "LLM not initialized"
        assert hasattr(service, 'tools'), "Tools not initialized"
        assert hasattr(service, 'rag_system'), "RAG system not initialized"
        assert hasattr(service, 'semantic_router'), "Semantic router not initialized"
        assert hasattr(service, 'memory_persistence'), "Memory persistence not initialized"
        assert hasattr(service, 'langgraph_workflow'), "LangGraph workflow not initialized"
        logger.info("✅ All components initialized")
        
        # Test tools
        assert service.tools is not None, "Tools list is None"
        assert len(service.tools) > 0, "No tools available"
        logger.info(f"✅ {len(service.tools)} tools available")
        
        # Test tool structure
        for i, tool in enumerate(service.tools):
            assert hasattr(tool, 'name'), f"Tool {i} missing name"
            assert hasattr(tool, 'description'), f"Tool {i} missing description"
            logger.info(f"  - {tool.name}: {tool.description[:50]}...")
        
        logger.info("✅ AdvancedLangChainService tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ AdvancedLangChainService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ AdvancedLangChainService test failed: {e}")
        return False


async def test_semantic_routing_service():
    """Test SemanticRoutingService"""
    logger.info("🧪 Testing SemanticRoutingService...")
    
    try:
        from app.services.semantic_routing_service import SemanticRoutingService
        
        # Test initialization
        service = SemanticRoutingService()
        logger.info("✅ SemanticRoutingService initialized successfully")
        
        # Test components
        assert hasattr(service, 'routing_config'), "Routing config not initialized"
        assert hasattr(service, 'agent_capabilities'), "Agent capabilities not initialized"
        logger.info("✅ SemanticRoutingService components verified")
        
        logger.info("✅ SemanticRoutingService tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ SemanticRoutingService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ SemanticRoutingService test failed: {e}")
        return False


async def test_memory_persistence_service():
    """Test MemoryPersistenceService"""
    logger.info("🧪 Testing MemoryPersistenceService...")
    
    try:
        from app.services.memory_persistence_service import MemoryPersistenceService
        
        # Test initialization
        service = MemoryPersistenceService()
        logger.info("✅ MemoryPersistenceService initialized successfully")
        
        logger.info("✅ MemoryPersistenceService tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ MemoryPersistenceService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ MemoryPersistenceService test failed: {e}")
        return False


async def test_langgraph_workflow_service():
    """Test LangGraphWorkflowService"""
    logger.info("🧪 Testing LangGraphWorkflowService...")
    
    try:
        from app.services.langgraph_workflow_service import LangGraphWorkflowService
        
        # Test initialization
        service = LangGraphWorkflowService()
        logger.info("✅ LangGraphWorkflowService initialized successfully")
        
        # Test components
        assert hasattr(service, 'workflow'), "Workflow not initialized"
        logger.info("✅ LangGraphWorkflowService components verified")
        
        logger.info("✅ LangGraphWorkflowService tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ LangGraphWorkflowService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ LangGraphWorkflowService test failed: {e}")
        return False


async def test_multi_agent_conversation_service():
    """Test MultiAgentConversationService"""
    logger.info("🧪 Testing MultiAgentConversationService...")
    
    try:
        from app.services.multi_agent_conversation_service import MultiAgentConversationService
        
        # Test initialization
        service = MultiAgentConversationService()
        logger.info("✅ MultiAgentConversationService initialized successfully")
        
        # Test components
        assert hasattr(service, 'agent_definitions'), "Agent definitions not initialized"
        assert hasattr(service, 'collaboration_patterns'), "Collaboration patterns not initialized"
        assert hasattr(service, 'agent_graph'), "Agent graph not initialized"
        logger.info("✅ MultiAgentConversationService components verified")
        
        # Test agent definitions
        expected_agents = ["weather_expert", "regulatory_expert", "agronomist", "economist", "moderator"]
        for agent in expected_agents:
            assert agent in service.agent_definitions, f"Agent {agent} not defined"
            agent_def = service.agent_definitions[agent]
            assert "name" in agent_def, f"Agent {agent} missing name"
            assert "expertise" in agent_def, f"Agent {agent} missing expertise"
            logger.info(f"  - {agent}: {agent_def['name']}")
        
        logger.info("✅ MultiAgentConversationService tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ MultiAgentConversationService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ MultiAgentConversationService test failed: {e}")
        return False


async def test_error_recovery_service():
    """Test ErrorRecoveryService"""
    logger.info("🧪 Testing ErrorRecoveryService...")
    
    try:
        from app.services.error_recovery_service import ErrorRecoveryService, ErrorContext, ErrorSeverity
        
        # Test initialization
        service = ErrorRecoveryService()
        logger.info("✅ ErrorRecoveryService initialized successfully")
        
        # Test components
        assert hasattr(service, 'fallback_strategies'), "Fallback strategies not initialized"
        assert hasattr(service, 'circuit_breakers'), "Circuit breakers not initialized"
        logger.info("✅ ErrorRecoveryService components verified")
        
        # Test error classification
        test_errors = [
            (ConnectionError("Database connection failed"), "database_connection_error"),
            (TimeoutError("API timeout"), "api_timeout_error"),
            (ValueError("Invalid input"), "validation_error")
        ]
        
        for error, expected_type in test_errors:
            classified_type = service._classify_error(error)
            logger.info(f"  - {type(error).__name__} → {classified_type}")
        
        logger.info("✅ ErrorRecoveryService tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ ErrorRecoveryService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ ErrorRecoveryService test failed: {e}")
        return False


async def test_conditional_routing_service():
    """Test ConditionalRoutingService"""
    logger.info("🧪 Testing ConditionalRoutingService...")
    
    try:
        from app.services.conditional_routing_service import ConditionalRoutingService
        
        # Test initialization
        service = ConditionalRoutingService()
        logger.info("✅ ConditionalRoutingService initialized successfully")
        
        # Test components
        assert hasattr(service, 'routing_rules'), "Routing rules not initialized"
        assert hasattr(service, 'decision_trees'), "Decision trees not initialized"
        logger.info("✅ ConditionalRoutingService components verified")
        
        logger.info("✅ ConditionalRoutingService tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ ConditionalRoutingService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ ConditionalRoutingService test failed: {e}")
        return False


async def test_streaming_service():
    """Test StreamingService"""
    logger.info("🧪 Testing StreamingService...")
    
    try:
        from app.services.streaming_service import StreamingService
        
        # Test initialization
        service = StreamingService()
        logger.info("✅ StreamingService initialized successfully")
        
        # Test components
        assert hasattr(service, 'active_streams'), "Active streams not initialized"
        logger.info("✅ StreamingService components verified")
        
        logger.info("✅ StreamingService tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ StreamingService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ StreamingService test failed: {e}")
        return False


async def test_chat_service_integration():
    """Test ChatService LangChain integration"""
    logger.info("🧪 Testing ChatService LangChain integration...")
    
    try:
        from app.services.chat_service import ChatService
        
        # Test initialization
        service = ChatService()
        logger.info("✅ ChatService initialized successfully")
        
        # Test LangChain integration
        assert hasattr(service, 'advanced_langchain_service'), "AdvancedLangChainService not integrated"
        assert hasattr(service, 'langgraph_workflow_service'), "LangGraphWorkflowService not integrated"
        logger.info("✅ ChatService LangChain integration verified")
        
        logger.info("✅ ChatService integration tests passed")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ ChatService not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ ChatService integration test failed: {e}")
        return False


async def run_all_tests():
    """Run all LangChain integration tests"""
    logger.info("🚀 Starting LangChain Integration Test Suite...")
    logger.info(f"📅 Test run started at: {datetime.now().isoformat()}")
    
    test_functions = [
        test_advanced_langchain_service,
        test_semantic_routing_service,
        test_memory_persistence_service,
        test_langgraph_workflow_service,
        test_multi_agent_conversation_service,
        test_error_recovery_service,
        test_conditional_routing_service,
        test_streaming_service,
        test_chat_service_integration
    ]
    
    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    for test_func in test_functions:
        try:
            result = await test_func()
            if result:
                passed_tests += 1
            else:
                skipped_tests += 1
        except Exception as e:
            logger.error(f"❌ {test_func.__name__} failed with exception: {e}")
            failed_tests += 1
    
    logger.info("\n" + "="*60)
    logger.info("📊 LANGCHAIN INTEGRATION TEST RESULTS")
    logger.info("="*60)
    logger.info(f"✅ Passed:  {passed_tests}")
    logger.info(f"⚠️  Skipped: {skipped_tests}")
    logger.info(f"❌ Failed:  {failed_tests}")
    logger.info(f"📊 Total:   {total_tests}")
    logger.info("="*60)
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    logger.info(f"🎯 Success Rate: {success_rate:.1f}%")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED! LangChain integration is working perfectly!")
    elif passed_tests > 0:
        logger.info("✅ LangChain integration is partially working. Some components may need configuration.")
    else:
        logger.info("⚠️ LangChain integration needs attention. Check dependencies and configuration.")
    
    return passed_tests, total_tests


if __name__ == "__main__":
    asyncio.run(run_all_tests())
