"""
Simple test script to verify LangChain agents are working.
Run this to test the agent system without the full API.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.agents import orchestrator

def test_agent_system():
    """Test the agricultural agent system."""
    print("🤖 Testing Agricultural Agent System")
    print("=" * 50)
    
    # Test 1: Get available agents
    print("\n1. Available Agents:")
    agents = orchestrator.get_available_agents()
    for agent in agents:
        print(f"   - {agent}")
    
    # Test 2: Test agent selection and response
    test_messages = [
        "Quels sont les rendements de mes parcelles de blé cette année ?",
        "Puis-je utiliser le produit Karate Zeon sur mes cultures de colza ?",
        "Quelles sont les prévisions météo pour la semaine prochaine ?"
    ]
    
    print("\n2. Testing Agent Responses:")
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Test {i}: {message}")
        try:
            response = orchestrator.process_message(
                message=message,
                user_id="test_user",
                farm_id="test_farm",
                context={"location": {"coordinates": {"lat": 48.8566, "lon": 2.3522}}}
            )
            print(f"   Agent: {response.get('agent', 'unknown')}")
            print(f"   Response: {response.get('response', 'No response')[:100]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n✅ Agent system test completed!")

if __name__ == "__main__":
    test_agent_system()
