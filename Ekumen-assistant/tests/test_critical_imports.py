"""
Critical Import Tests for CI/CD Pipeline

This test ensures all critical imports work before deployment.
Run this as a pre-commit hook or CI test to catch broken imports early.

Usage:
    python tests/test_critical_imports.py
    pytest tests/test_critical_imports.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest


def test_agent_manager_import():
    """Test that AgentManager imports successfully"""
    try:
        from app.agents.agent_manager import AgentManager
        manager = AgentManager()
        assert manager is not None
        assert len(manager.agent_profiles) > 0
        print("✅ AgentManager imports successfully")
    except Exception as e:
        pytest.fail(f"AgentManager import failed: {e}")


def test_prompt_registry_import():
    """Test that prompt registry imports successfully"""
    try:
        from app.prompts.prompt_registry import get_agent_prompt
        prompt = get_agent_prompt('orchestrator')
        assert prompt is not None
        print("✅ Prompt registry imports successfully")
    except Exception as e:
        pytest.fail(f"Prompt registry import failed: {e}")


def test_main_app_import():
    """Test that main FastAPI app imports successfully"""
    try:
        import app.main
        assert app.main.app is not None
        print("✅ Main app imports successfully")
    except Exception as e:
        pytest.fail(f"Main app import failed: {e}")


def test_chat_service_import():
    """Test that ChatService imports successfully"""
    try:
        from app.services.chat_service import ChatService
        service = ChatService()
        assert service is not None
        print("✅ ChatService imports successfully")
    except Exception as e:
        pytest.fail(f"ChatService import failed: {e}")


def test_streaming_service_import():
    """Test that OptimizedStreamingService imports successfully"""
    try:
        from app.services.optimized_streaming_service import OptimizedStreamingService
        # Don't instantiate - just test import
        assert OptimizedStreamingService is not None
        print("✅ OptimizedStreamingService imports successfully")
    except Exception as e:
        pytest.fail(f"OptimizedStreamingService import failed: {e}")


def test_all_agents_import():
    """Test that all agent classes import successfully"""
    agents = [
        ("FarmDataIntelligenceAgent", "app.agents.farm_data_agent"),
        ("WeatherIntelligenceAgent", "app.agents.weather_agent"),
        ("CropHealthIntelligenceAgent", "app.agents.crop_health_agent"),
        ("PlanningIntelligenceAgent", "app.agents.planning_agent"),
        ("RegulatoryIntelligenceAgent", "app.agents.regulatory_agent"),
        ("SustainabilityIntelligenceAgent", "app.agents.sustainability_agent"),
        ("SupplierAgent", "app.agents.supplier_agent"),
        ("InternetAgent", "app.agents.internet_agent"),
    ]
    
    for agent_name, module_path in agents:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent_class = getattr(module, agent_name)
            assert agent_class is not None
            print(f"✅ {agent_name} imports successfully")
        except Exception as e:
            pytest.fail(f"{agent_name} import failed: {e}")


def test_no_deleted_imports():
    """Test that deleted modules are not imported anywhere"""
    import os
    import re
    
    # Patterns that should NOT exist in the codebase
    forbidden_patterns = [
        r"from app\.agents\.agent_selector import",
        r"from app\.agents\.base_agent import",
        r"from app\.agents\.orchestrator import",
        r"from app\.services\.agent_orchestrator import",
        r"from app\.agents import orchestrator",
    ]
    
    # Search in app/ directory
    app_dir = "app"
    violations = []
    
    for root, dirs, files in os.walk(app_dir):
        # Skip __pycache__ and venv
        dirs[:] = [d for d in dirs if d not in ['__pycache__', 'venv', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for pattern in forbidden_patterns:
                        if re.search(pattern, content):
                            violations.append(f"{filepath}: {pattern}")
    
    if violations:
        error_msg = "Found imports of deleted modules:\n" + "\n".join(violations)
        pytest.fail(error_msg)
    else:
        print("✅ No deleted module imports found")


def test_get_available_agents():
    """Test that get_available_agents returns correct format"""
    try:
        from app.services.chat_service import ChatService
        service = ChatService()
        agents = service.get_available_agents()
        
        assert isinstance(agents, list)
        assert len(agents) > 0
        
        # Check format of first agent
        first_agent = agents[0]
        assert "name" in first_agent
        assert "type" in first_agent
        assert "description" in first_agent
        assert "capabilities" in first_agent
        
        print(f"✅ get_available_agents() returns {len(agents)} agents in correct format")
    except Exception as e:
        pytest.fail(f"get_available_agents test failed: {e}")


if __name__ == "__main__":
    """Run tests directly without pytest"""
    print("=" * 80)
    print("CRITICAL IMPORT TESTS")
    print("=" * 80)
    print()
    
    tests = [
        ("AgentManager Import", test_agent_manager_import),
        ("Prompt Registry Import", test_prompt_registry_import),
        ("Main App Import", test_main_app_import),
        ("ChatService Import", test_chat_service_import),
        ("StreamingService Import", test_streaming_service_import),
        ("All Agents Import", test_all_agents_import),
        ("No Deleted Imports", test_no_deleted_imports),
        ("get_available_agents Format", test_get_available_agents),
    ]
    
    failed = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}...")
            test_func()
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
            failed.append(test_name)
    
    print()
    print("=" * 80)
    if failed:
        print(f"❌ {len(failed)} TEST(S) FAILED:")
        for test in failed:
            print(f"   - {test}")
        print("=" * 80)
        sys.exit(1)
    else:
        print("✅ ALL CRITICAL IMPORT TESTS PASSED")
        print("=" * 80)
        sys.exit(0)

