"""
Test Tavily Integration
Quick test to verify Tavily agents are working
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.tavily_service import get_tavily_service
from app.agents.internet_agent import InternetAgent
from app.agents.supplier_agent import SupplierAgent


async def test_tavily_service():
    """Test basic Tavily service functionality"""
    print("=" * 80)
    print("TEST 1: Tavily Service Availability")
    print("=" * 80)
    
    tavily = get_tavily_service()
    
    if tavily.is_available():
        print("✅ Tavily service is available")
        print(f"   API Key: {tavily.api_key[:20]}...")
    else:
        print("❌ Tavily service is NOT available")
        return False
    
    return True


async def test_internet_search():
    """Test internet search functionality"""
    print("\n" + "=" * 80)
    print("TEST 2: Internet Search")
    print("=" * 80)
    
    tavily = get_tavily_service()
    
    # Test a simple search
    query = "prix du blé France 2024"
    print(f"\n🔍 Searching: {query}")
    
    result = await tavily.search_internet(query, max_results=3)
    
    if result.get("success"):
        print(f"✅ Search successful!")
        print(f"   Query: {result.get('query')}")
        print(f"   Results: {len(result.get('results', []))}")
        
        if result.get("answer"):
            print(f"\n   AI Summary:")
            print(f"   {result['answer'][:200]}...")
        
        print(f"\n   Top Results:")
        for i, item in enumerate(result.get("results", [])[:3], 1):
            print(f"   {i}. {item.get('title', 'No title')}")
            print(f"      {item.get('url', 'No URL')}")
        
        return True
    else:
        print(f"❌ Search failed: {result.get('error')}")
        return False


async def test_supplier_search():
    """Test supplier search functionality"""
    print("\n" + "=" * 80)
    print("TEST 3: Supplier Search")
    print("=" * 80)
    
    tavily = get_tavily_service()
    
    # Test supplier search
    query = "fournisseur semences blé"
    location = "Bordeaux"
    print(f"\n🎁 Searching: {query} near {location}")
    
    result = await tavily.search_suppliers(query, location=location, max_results=3)
    
    if result.get("success"):
        print(f"✅ Supplier search successful!")
        print(f"   Query: {result.get('query')}")
        print(f"   Suppliers found: {len(result.get('suppliers', []))}")
        
        if result.get("summary"):
            print(f"\n   Summary:")
            print(f"   {result['summary'][:200]}...")
        
        print(f"\n   Top Suppliers:")
        for i, supplier in enumerate(result.get("suppliers", [])[:3], 1):
            print(f"   {i}. {supplier.get('name', 'No name')}")
            print(f"      {supplier.get('url', 'No URL')}")
            print(f"      Score: {supplier.get('relevance_score', 0):.2f}")
        
        return True
    else:
        print(f"❌ Supplier search failed: {result.get('error')}")
        return False


async def test_market_prices():
    """Test market prices search"""
    print("\n" + "=" * 80)
    print("TEST 4: Market Prices Search")
    print("=" * 80)
    
    tavily = get_tavily_service()
    
    # Test market prices
    commodity = "blé"
    print(f"\n💰 Searching prices for: {commodity}")
    
    result = await tavily.search_market_prices(commodity, max_results=3)
    
    if result.get("success"):
        print(f"✅ Market prices search successful!")
        print(f"   Commodity: {result.get('commodity')}")
        print(f"   Price sources: {len(result.get('prices', []))}")
        
        if result.get("summary"):
            print(f"\n   Summary:")
            print(f"   {result['summary'][:200]}...")
        
        print(f"\n   Price Sources:")
        for i, price in enumerate(result.get("prices", [])[:3], 1):
            print(f"   {i}. {price.get('source', 'No source')}")
            print(f"      {price.get('url', 'No URL')}")
        
        return True
    else:
        print(f"❌ Market prices search failed: {result.get('error')}")
        return False


async def test_internet_agent():
    """Test Internet Agent"""
    print("\n" + "=" * 80)
    print("TEST 5: Internet Agent")
    print("=" * 80)
    
    agent = InternetAgent()
    
    query = "Quelles sont les dernières actualités agricoles en France?"
    print(f"\n🌐 Agent query: {query}")
    
    result = await agent.process(query)
    
    if result.get("success"):
        print(f"✅ Internet Agent successful!")
        print(f"   Agent: {result.get('agent')}")
        print(f"\n   Response:")
        response = result.get("response", "")
        print(f"   {response[:300]}...")
        return True
    else:
        print(f"❌ Internet Agent failed: {result.get('response')}")
        return False


async def test_supplier_agent():
    """Test Supplier Agent"""
    print("\n" + "=" * 80)
    print("TEST 6: Supplier Agent")
    print("=" * 80)
    
    agent = SupplierAgent()
    
    query = "Où puis-je acheter des semences de maïs près de Bordeaux?"
    print(f"\n🎁 Agent query: {query}")
    
    result = await agent.process(query)
    
    if result.get("success"):
        print(f"✅ Supplier Agent successful!")
        print(f"   Agent: {result.get('agent')}")
        print(f"\n   Response:")
        response = result.get("response", "")
        print(f"   {response[:300]}...")
        return True
    else:
        print(f"❌ Supplier Agent failed: {result.get('response')}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("TAVILY INTEGRATION TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Test 1: Service availability
    results.append(await test_tavily_service())
    
    if not results[0]:
        print("\n❌ Tavily service not available. Stopping tests.")
        return
    
    # Test 2-6: Functionality tests
    results.append(await test_internet_search())
    results.append(await test_supplier_search())
    results.append(await test_market_prices())
    results.append(await test_internet_agent())
    results.append(await test_supplier_agent())
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED! Tavily integration is working perfectly!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())

