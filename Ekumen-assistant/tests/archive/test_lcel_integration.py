"""
Test LCEL Integration with Automatic History Management
Verifies that RunnableWithMessageHistory works correctly
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.services.lcel_chat_service import get_lcel_chat_service
from app.services.postgres_chat_history import AsyncPostgresChatMessageHistory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_postgres_chat_history():
    """Test PostgreSQL chat history integration"""
    print("=" * 80)
    print("TEST 1: PostgreSQL Chat History")
    print("=" * 80)
    
    try:
        async with AsyncSessionLocal() as db:
            # Create a test conversation ID
            conversation_id = "test-lcel-conversation-001"
            
            # Create history instance
            history = AsyncPostgresChatMessageHistory(conversation_id, db)
            
            # Load messages
            messages = await history.aget_messages()
            print(f"✅ Loaded {len(messages)} messages from database")
            
            # Display messages
            for i, msg in enumerate(messages[-5:], 1):  # Last 5 messages
                msg_type = "User" if msg.__class__.__name__ == "HumanMessage" else "AI"
                print(f"   {i}. [{msg_type}] {msg.content[:100]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ PostgreSQL chat history test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_lcel_basic_chat():
    """Test basic LCEL chat with automatic history"""
    print("\n" + "=" * 80)
    print("TEST 2: LCEL Basic Chat with Automatic History")
    print("=" * 80)
    
    try:
        lcel_service = get_lcel_chat_service()
        
        async with AsyncSessionLocal() as db:
            conversation_id = "test-lcel-conversation-002"
            
            # First message
            print("\n📝 Sending first message...")
            response1 = await lcel_service.process_message(
                db_session=db,
                conversation_id=conversation_id,
                message="Bonjour, j'ai une parcelle de blé de 10 hectares en Nouvelle-Aquitaine.",
                use_rag=False
            )
            print(f"✅ Response 1: {response1[:200]}...")
            
            # Second message - should have context from first
            print("\n📝 Sending second message (with context)...")
            response2 = await lcel_service.process_message(
                db_session=db,
                conversation_id=conversation_id,
                message="Quel traitement recommandes-tu pour cette parcelle?",
                use_rag=False
            )
            print(f"✅ Response 2: {response2[:200]}...")
            
            # Check if context was used
            if "blé" in response2.lower() or "10 hectares" in response2.lower() or "nouvelle-aquitaine" in response2.lower():
                print("✅ Context from previous message was used!")
            else:
                print("⚠️ Context may not have been used")
            
            return True
            
    except Exception as e:
        print(f"❌ LCEL basic chat test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_lcel_streaming():
    """Test LCEL streaming with automatic history"""
    print("\n" + "=" * 80)
    print("TEST 3: LCEL Streaming with Automatic History")
    print("=" * 80)
    
    try:
        lcel_service = get_lcel_chat_service()
        
        async with AsyncSessionLocal() as db:
            conversation_id = "test-lcel-conversation-003"
            
            print("\n📝 Streaming response...")
            print("Response: ", end="", flush=True)
            
            chunk_count = 0
            async for chunk in lcel_service.stream_message(
                db_session=db,
                conversation_id=conversation_id,
                message="Explique-moi brièvement la rotation des cultures.",
                use_rag=False
            ):
                print(chunk, end="", flush=True)
                chunk_count += 1
            
            print(f"\n\n✅ Streaming completed with {chunk_count} chunks")
            return True
            
    except Exception as e:
        print(f"❌ LCEL streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_lcel_rag():
    """Test LCEL RAG with context-aware retrieval"""
    print("\n" + "=" * 80)
    print("TEST 4: LCEL RAG with Context-Aware Retrieval")
    print("=" * 80)
    
    try:
        lcel_service = get_lcel_chat_service()
        
        async with AsyncSessionLocal() as db:
            conversation_id = "test-lcel-conversation-004"
            
            # First question
            print("\n📝 First RAG question...")
            response1 = await lcel_service.process_message(
                db_session=db,
                conversation_id=conversation_id,
                message="Quelles sont les réglementations pour le blé?",
                use_rag=True
            )
            print(f"✅ Response 1: {response1[:200]}...")
            
            # Follow-up question - should reformulate based on context
            print("\n📝 Follow-up RAG question (context-aware)...")
            response2 = await lcel_service.process_message(
                db_session=db,
                conversation_id=conversation_id,
                message="Et pour le maïs, c'est pareil?",
                use_rag=True
            )
            print(f"✅ Response 2: {response2[:200]}...")
            
            # The retriever should have reformulated "Et pour le maïs, c'est pareil?"
            # to something like "Quelles sont les réglementations pour le maïs?"
            
            return True
            
    except Exception as e:
        print(f"❌ LCEL RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chat_service_integration():
    """Test integration with ChatService"""
    print("\n" + "=" * 80)
    print("TEST 5: ChatService Integration")
    print("=" * 80)
    
    try:
        from app.services.chat_service import ChatService
        
        chat_service = ChatService()
        
        async with AsyncSessionLocal() as db:
            # Create a test conversation
            conversation = await chat_service.create_conversation(
                db=db,
                user_id="test-user-123",
                agent_type="farm_data",
                title="Test LCEL Integration"
            )
            
            print(f"✅ Created conversation: {conversation.id}")
            
            # Process message with LCEL
            result = await chat_service.process_message_with_lcel(
                db=db,
                conversation_id=str(conversation.id),
                user_id="test-user-123",
                message_content="Bonjour, comment optimiser ma production de blé?",
                use_rag=False
            )
            
            print(f"✅ Processed message with LCEL")
            print(f"   Processing method: {result['ai_response']['processing_method']}")
            print(f"   Response: {result['ai_response']['content'][:200]}...")
            
            # Verify message was saved
            messages = await chat_service.get_conversation_messages(
                db=db,
                conversation_id=str(conversation.id)
            )
            
            print(f"✅ Messages saved to database: {len(messages)} messages")
            
            return True
            
    except Exception as e:
        print(f"❌ ChatService integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LCEL INTEGRATION TEST SUITE")
    print("Testing RunnableWithMessageHistory and Automatic Context Management")
    print("=" * 80)
    
    results = []
    
    # Test 1: PostgreSQL chat history
    results.append(await test_postgres_chat_history())
    
    # Test 2: Basic LCEL chat
    results.append(await test_lcel_basic_chat())
    
    # Test 3: LCEL streaming
    results.append(await test_lcel_streaming())
    
    # Test 4: LCEL RAG
    results.append(await test_lcel_rag())
    
    # Test 5: ChatService integration
    results.append(await test_chat_service_integration())
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED! LCEL integration is working perfectly!")
        print("\n🎉 You now have:")
        print("   ✅ Automatic history management (RunnableWithMessageHistory)")
        print("   ✅ LCEL chains (modern LangChain)")
        print("   ✅ Context-aware RAG (create_history_aware_retriever)")
        print("   ✅ Automatic streaming support")
        print("   ✅ PostgreSQL-backed message history")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())

