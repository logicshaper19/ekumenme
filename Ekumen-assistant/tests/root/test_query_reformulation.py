#!/usr/bin/env python3
"""
Test script to verify query reformulation is working
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.infrastructure.lcel_chat_service import LCELChatService
from app.core.database import AsyncSessionLocal


async def test_query_reformulation():
    """Test that query reformulation works correctly"""
    
    print("🧪 Testing Query Reformulation Feature")
    print("=" * 50)
    
    # Initialize the service
    lcel_service = LCELChatService()
    
    # Test cases
    test_cases = [
        {
            "name": "Simple question (no reformulation needed)",
            "query": "Quelles sont les réglementations pour le maïs?",
            "expected_reformulation": None  # Should not be reformulated
        },
        {
            "name": "Context-dependent question (needs reformulation)",
            "query": "Et pour le maïs?",
            "expected_reformulation": "Quelles sont les réglementations pour le maïs?"  # Should be reformulated
        },
        {
            "name": "Pronoun reference (needs reformulation)",
            "query": "Quel traitement pour cette parcelle?",
            "expected_reformulation": "Quel traitement recommandes-tu pour la parcelle de blé de 10 hectares?"  # Should be reformulated
        }
    ]
    
    async with AsyncSessionLocal() as db:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['name']}")
            print(f"   Query: '{test_case['query']}'")
            
            try:
                # Create a test conversation ID
                conversation_id = f"test-reformulation-{i}-{int(datetime.now().timestamp())}"
                
                # First, add some context to the conversation
                if "maïs" in test_case['query']:
                    # Add context about wheat first
                    context_message = "Je cultive du blé sur ma parcelle de 10 hectares"
                    print(f"   Adding context: '{context_message}'")
                    
                    # Process context message first
                    context_result = await lcel_service.process_message(
                        db_session=db,
                        conversation_id=conversation_id,
                        message=context_message,
                        use_rag=False  # Don't use RAG for context
                    )
                
                # Now test the actual query
                print(f"   Processing query...")
                
                # Use stream_message to capture reformulation
                reformulated_query = None
                final_answer = ""
                
                async for event in lcel_service.stream_message(
                    db_session=db,
                    conversation_id=conversation_id,
                    message=test_case['query'],
                    use_rag=True
                ):
                    if isinstance(event, dict) and "final" in event:
                        final_payload = event.get("final", {})
                        reformulated_query = final_payload.get("reformulated_query")
                        final_answer = final_payload.get("answer", "")
                    elif isinstance(event, str):
                        final_answer += event
                
                # Check results
                print(f"   ✅ Reformulated: '{reformulated_query}'")
                print(f"   ✅ Answer: '{final_answer[:100]}...'")
                
                # Verify reformulation
                if test_case['expected_reformulation'] is None:
                    if reformulated_query is None or reformulated_query == test_case['query']:
                        print(f"   ✅ PASS: No reformulation needed (as expected)")
                    else:
                        print(f"   ❌ FAIL: Expected no reformulation, got: '{reformulated_query}'")
                else:
                    if reformulated_query and reformulated_query != test_case['query']:
                        print(f"   ✅ PASS: Query was reformulated (as expected)")
                        print(f"   📊 Original: '{test_case['query']}'")
                        print(f"   📊 Reformulated: '{reformulated_query}'")
                    else:
                        print(f"   ❌ FAIL: Expected reformulation, but got: '{reformulated_query}'")
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
    
    print(f"\n🎉 Query reformulation test completed!")


if __name__ == "__main__":
    asyncio.run(test_query_reformulation())
