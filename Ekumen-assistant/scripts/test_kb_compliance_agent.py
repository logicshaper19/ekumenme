#!/usr/bin/env python3
"""
Test script for the Knowledge Base Compliance Agent
Demonstrates the new regulatory compliance validation system using proper LangChain patterns
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.knowledge_base_compliance_agent import KnowledgeBaseComplianceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_compliance_agent():
    """Test the compliance agent with sample agricultural documents"""
    
    print("🧪 Testing Knowledge Base Compliance Agent")
    print("=" * 60)
    print("Using existing regulatory tools with proper LangChain patterns")
    print()
    
    # Initialize the compliance agent
    agent = KnowledgeBaseComplianceAgent(
        enable_dynamic_examples=False,  # Disable for token optimization
        max_iterations=6,  # Optimized for document validation
        enable_metrics=True
    )
    
    # Test documents with different compliance scenarios
    test_documents = [
        {
            "id": "test_001",
            "type": "product_manual",
            "content": """
            PRODUIT: ROUNDUP CLASSIC
            SUBSTANCE ACTIVE: Glyphosate 360 g/L
            
            DOSAGE RECOMMANDÉ:
            - Blé: 2.5 L/ha en post-levée
            - Maïs: 3.0 L/ha avant semis
            - Fréquence: Maximum 2 applications par saison
            
            RESTRICTIONS:
            - ZNT: 5 m des cours d'eau
            - DAR: 7 jours avant récolte
            - Ne pas appliquer par vent fort
            """
        },
        {
            "id": "test_002", 
            "type": "technical_sheet",
            "content": """
            PRODUIT: OPUS
            SUBSTANCE ACTIVE: Epoxiconazole 125 g/L
            
            UTILISATION:
            - Blé tendre: 1.0 L/ha
            - Blé dur: 1.2 L/ha
            - Application foliaire uniquement
            
            DÉLAIS:
            - DAR: 35 jours avant récolte
            - Intervalle entre applications: 14 jours minimum
            - Maximum 3 applications par saison
            """
        },
        {
            "id": "test_003",
            "type": "product_manual", 
            "content": """
            PRODUIT: PRODUIT_INTERDIT
            SUBSTANCE ACTIVE: Substance non autorisée
            
            DOSAGE:
            - Blé: 5.0 L/ha (dépassement des limites)
            - Application tous les 3 jours (fréquence excessive)
            
            RESTRICTIONS IGNORÉES:
            - Pas de ZNT mentionnée
            - DAR non respecté
            """
        }
    ]
    
    # Test each document
    for i, doc in enumerate(test_documents, 1):
        print(f"\n📄 Test Document {i}: {doc['id']}")
        print(f"Type: {doc['type']}")
        print("-" * 40)
        
        try:
            # Validate document
            result = await agent.validate_document(
                document_content=doc["content"],
                document_type=doc["type"],
                document_id=doc["id"]
            )
            
            # Display results
            print(f"✅ Decision: {result.get('decision', 'UNKNOWN')}")
            print(f"🎯 Confidence: {result.get('confidence', 0.0):.2f}")
            
            violations = result.get('violations', [])
            warnings = result.get('warnings', [])
            recommendations = result.get('recommendations', [])
            
            if violations:
                print(f"❌ Violations ({len(violations)}):")
                for violation in violations[:3]:  # Show first 3
                    if isinstance(violation, dict):
                        print(f"   • {violation.get('description', str(violation))}")
                    else:
                        print(f"   • {violation}")
            
            if warnings:
                print(f"⚠️  Warnings ({len(warnings)}):")
                for warning in warnings[:3]:  # Show first 3
                    if isinstance(warning, dict):
                        print(f"   • {warning.get('description', str(warning))}")
                    else:
                        print(f"   • {warning}")
            
            if recommendations:
                print(f"💡 Recommendations ({len(recommendations)}):")
                for rec in recommendations[:3]:  # Show first 3
                    print(f"   • {rec}")
            
            # Show tool results summary
            tool_results = result.get('tool_results', {})
            if tool_results:
                print(f"🔧 Tools Used: {len(tool_results)}")
                for tool_name in tool_results.keys():
                    print(f"   • {tool_name}")
            
        except Exception as e:
            print(f"❌ Error testing document {doc['id']}: {e}")
            logger.error(f"Error in compliance validation: {e}")
    
    # Show metrics
    print("\n📊 Agent Metrics:")
    print("-" * 40)
    metrics = agent.get_metrics()
    if not metrics.get("metrics_disabled"):
        print(f"Total Calls: {metrics.get('total_calls', 0)}")
        print(f"Successful: {metrics.get('successful_calls', 0)}")
        print(f"Failed: {metrics.get('failed_calls', 0)}")
        print(f"Avg Iterations: {metrics.get('avg_iterations', 0):.1f}")
        
        tool_usage = metrics.get('tool_usage', {})
        if tool_usage:
            print("Tool Usage:")
            for tool, count in tool_usage.items():
                print(f"  • {tool}: {count}")
    
    print("\n" + "=" * 60)
    print("🎉 Knowledge Base Compliance Agent Testing Complete!")
    print()
    print("🔄 IMPROVEMENTS IMPLEMENTED:")
    print("✅ Uses existing production-ready regulatory tools")
    print("✅ Follows proper LangChain ReAct agent patterns")
    print("✅ No custom tool implementations (uses proven tools)")
    print("✅ Proper error handling and metrics tracking")
    print("✅ Structured output parsing")
    print("✅ Integration with EPHY database services")
    print("✅ No fragile string matching - uses tool outputs")
    print()
    print("🛡️ SAFETY BENEFITS:")
    print("• Real EPHY database validation")
    print("• Binary compliance decisions")
    print("• Transparent audit trail")
    print("• Prevents dangerous auto-approvals")


if __name__ == "__main__":
    asyncio.run(test_compliance_agent())
