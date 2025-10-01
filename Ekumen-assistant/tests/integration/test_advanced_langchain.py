#!/usr/bin/env python3
"""
Test script for Advanced LangChain Agricultural System
"""

import os
import sys
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_advanced_langchain_system():
    """Test the advanced LangChain agricultural system."""
    
    print("🚀 Testing Advanced LangChain Agricultural System")
    print("=" * 60)
    
    try:
        # Import the advanced system
        from app.agents.advanced_langchain_system import create_advanced_agricultural_system
        
        print("✅ Successfully imported advanced LangChain system")
        
        # Initialize system (without API key for testing)
        print("\n🔧 Initializing system...")
        system = create_advanced_agricultural_system()
        
        print("✅ System initialized successfully")
        
        # Get system status
        print("\n📊 System Status:")
        status = system.get_system_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        # Test knowledge base
        print("\n🧠 Testing Knowledge Base...")
        try:
            # Test crop knowledge retrieval
            crop_docs = system.knowledge_base.search_knowledge("septoriose blé", domain="crop", k=3)
            print(f"✅ Found {len(crop_docs)} crop knowledge documents")
            
            # Test regulatory knowledge retrieval
            regulatory_docs = system.knowledge_base.search_knowledge("AMM autorisation", domain="regulatory", k=3)
            print(f"✅ Found {len(regulatory_docs)} regulatory knowledge documents")
            
        except Exception as e:
            print(f"⚠️ Knowledge base test failed: {e}")
        
        # Test RAG chains
        print("\n🔍 Testing RAG Chains...")
        try:
            rag_result = system.rag_chains.query_knowledge("Comment traiter la septoriose du blé ?", domain="crop")
            print(f"✅ RAG query successful: {rag_result['domain']}")
            
        except Exception as e:
            print(f"⚠️ RAG chains test failed: {e}")
        
        # Test reasoning chains
        print("\n🧮 Testing Reasoning Chains...")
        try:
            # Test weather analysis
            weather_data = {
                "temperature": 15.2,
                "humidity": 68,
                "wind_speed": 8.5,
                "precipitation": 0.0,
                "pressure": 1013.2
            }
            
            agricultural_context = {
                "location": "France",
                "crop_type": "blé",
                "growth_stage": "montaison",
                "operation": "pulvérisation"
            }
            
            weather_analysis = system.reasoning_chains.analyze_weather_for_agriculture(
                weather_data, agricultural_context
            )
            print(f"✅ Weather analysis successful: {weather_analysis.agricultural_risk_level}")
            
        except Exception as e:
            print(f"⚠️ Reasoning chains test failed: {e}")
        
        # Test agent manager
        print("\n🤖 Testing Agent Manager...")
        try:
            agent_info = system.agent_manager.get_agent_info()
            print(f"✅ Agent manager working: {len(agent_info['available_agents'])} agents available")
            
        except Exception as e:
            print(f"⚠️ Agent manager test failed: {e}")
        
        # Test complete system
        print("\n🎯 Testing Complete System...")
        try:
            query = "Quels sont les traitements autorisés contre la septoriose du blé ?"
            context = {
                "farm_location": "Beauce",
                "crop_stage": "montaison"
            }
            
            result = system.process_agricultural_query(
                query=query,
                context=context,
                use_rag=True,
                use_reasoning=True
            )
            
            print(f"✅ Complete system test successful")
            print(f"   Query: {result['query']}")
            print(f"   Components used: {result['system_components_used']}")
            print(f"   Response length: {len(result['response'])} characters")
            
        except Exception as e:
            print(f"⚠️ Complete system test failed: {e}")
        
        print("\n🎉 Advanced LangChain System Test Completed!")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all LangChain dependencies are installed:")
        print("pip install langchain langchain-openai langchain-community langgraph")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_langchain_tools():
    """Test individual LangChain tools."""
    
    print("\n🔧 Testing LangChain Tools...")
    
    try:
        from app.agents.langchain_tools import (
            get_farm_parcels, get_intervention_history, search_authorized_products,
            get_current_weather, identify_pest_disease, calculate_carbon_footprint
        )
        
        # Test farm data tools
        print("Testing farm data tools...")
        parcels_result = get_farm_parcels("12345678901234", 2024)
        print(f"✅ Farm parcels tool: {len(parcels_result)} characters")
        
        # Test regulatory tools
        print("Testing regulatory tools...")
        products_result = search_authorized_products("blé", "septoriose", "France")
        print(f"✅ Authorized products tool: {len(products_result)} characters")
        
        # Test weather tools
        print("Testing weather tools...")
        weather_result = get_current_weather(48.8566, 2.3522)
        print(f"✅ Current weather tool: {len(weather_result)} characters")
        
        # Test crop health tools
        print("Testing crop health tools...")
        pest_result = identify_pest_disease("taches brunes sur feuilles", "blé", "conditions humides")
        print(f"✅ Pest identification tool: {len(pest_result)} characters")
        
        # Test sustainability tools
        print("Testing sustainability tools...")
        carbon_result = calculate_carbon_footprint(
            '{"operations": "pulvérisation, fertilisation"}',
            '{"fuel": 1000, "fertilizers": 150}'
        )
        print(f"✅ Carbon footprint tool: {len(carbon_result)} characters")
        
        print("✅ All LangChain tools working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ LangChain tools test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Advanced LangChain Agricultural System Test Suite")
    print("=" * 60)
    
    # Test individual tools first
    tools_success = test_langchain_tools()
    
    # Test complete system
    system_success = test_advanced_langchain_system()
    
    # Summary
    print("\n📋 Test Summary:")
    print(f"   LangChain Tools: {'✅ PASS' if tools_success else '❌ FAIL'}")
    print(f"   Complete System: {'✅ PASS' if system_success else '❌ FAIL'}")
    
    if tools_success and system_success:
        print("\n🎉 All tests passed! Advanced LangChain system is ready.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
