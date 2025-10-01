"""
Test script for 19 real farmer queries.
Tests current system performance before any fixes.

Usage:
    python test_farmer_queries.py

Output:
    - Results for each query
    - Success/Partial/Fail categorization
    - Overall success rate
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime

# Import the services
from app.services.optimized_streaming_service import OptimizedStreamingService
from app.services.tool_registry_service import get_tool_registry

# Test queries from real farmer
FARMER_QUERIES = [
    {
        "id": 1,
        "category": "farm_data",
        "query": "Combien de tonnes de blé ai-je déjà vendu pour la récolte 2025 ?",
        "expected_needs": ["farm_data"],
        "prediction": "FAIL - No farm data access"
    },
    {
        "id": 2,
        "category": "farm_data",
        "query": "Quel est mon prix moyen de vente de blé à ce jour?",
        "expected_needs": ["farm_data"],
        "prediction": "FAIL - No farm data access"
    },
    {
        "id": 3,
        "category": "farm_data_calculation",
        "query": "Si je vendais mon blé (restant à vendre) à 170€/t, quel serait mon prix moyen de vente?",
        "expected_needs": ["farm_data", "calculation"],
        "prediction": "FAIL - Needs farm data + calculation"
    },
    {
        "id": 4,
        "category": "market_supplier",
        "query": "Quelles sont les propositions de prix d'achat d'engrais ammonitrate 33,5% en big bag livraison spot?",
        "expected_needs": ["market_prices", "supplier"],
        "prediction": "PARTIAL - Might find generic prices"
    },
    {
        "id": 5,
        "category": "farm_data_calculation",
        "query": "Combien d'azote sous forme de solution azotée dois je acheter en tenant compte de mes stocks et mes achats d'azote sous toutes les formes? Hypothèse de 240 unités d'azote sur les blés, 160 unités en colza et 160 unités en orges",
        "expected_needs": ["farm_data", "planning", "calculation"],
        "prediction": "FAIL - Complex multi-step"
    },
    {
        "id": 6,
        "category": "agronomic_advice",
        "query": "Combien d'unités d'azote dois mettre sur mes blés tendre améliorants variété Izalco, précédent colza ?",
        "expected_needs": ["planning", "farm_context"],
        "prediction": "PARTIAL - Might give generic advice"
    },
    {
        "id": 7,
        "category": "agronomic_advice",
        "query": "Quelles variétés de blé sont conseillées de semer après un blé en sol limoneux argileux, potentiel de terre moyen, mi-précoce, productive, sur ma ferme de Corbreuse ?",
        "expected_needs": ["planning", "farm_context"],
        "prediction": "PARTIAL - Might give generic varieties"
    },
    {
        "id": 8,
        "category": "equipment",
        "query": "Quel entretien dois je prévoir sur mon Fendt 312 cet hiver? Donnne moi les références des pièces et les quantités",
        "expected_needs": ["internet"],
        "prediction": "WORK - Internet search should find this"
    },
    {
        "id": 9,
        "category": "equipment",
        "query": "Quelle huile moteur dois je mettre dans mon compresseur à air comprimé ? Quantité et référence",
        "expected_needs": ["internet"],
        "prediction": "WORK - Internet search should find this"
    },
    {
        "id": 10,
        "category": "farm_data",
        "query": "A quelle densité le colza Bessito l'année dernière a-t-il été semé dans la parcelle des Ramonts? En grains par m2",
        "expected_needs": ["farm_data"],
        "prediction": "FAIL - Specific parcel data"
    },
    {
        "id": 11,
        "category": "farm_data",
        "query": "Combien de mm de pluie sont ils tombés depuis le 01/09/25 ?",
        "expected_needs": ["weather", "farm_location"],
        "prediction": "PARTIAL - Needs farm location"
    },
    {
        "id": 12,
        "category": "farm_data",
        "query": "Combien m'a couté la location de la station sencrop l'année dernière?",
        "expected_needs": ["farm_data"],
        "prediction": "FAIL - Specific expense data"
    },
    {
        "id": 13,
        "category": "farm_data_calculation",
        "query": "Comment a évolué la consommation de GNR de ma ferme cette année par rapport à N-1 ?",
        "expected_needs": ["farm_data", "calculation"],
        "prediction": "FAIL - Needs historical comparison"
    },
    {
        "id": 14,
        "category": "financial",
        "query": "Quelles aides financières ou subventions sont disponibles pour investir dans un scalpeur type Finer de chez Horsh?",
        "expected_needs": ["internet"],
        "prediction": "PARTIAL - Generic subsidy info"
    },
    {
        "id": 15,
        "category": "regulatory",
        "query": "Quel est le cahier des charges de la certification Label rouge en blé améliorant ?",
        "expected_needs": ["regulatory", "internet"],
        "prediction": "PARTIAL - Might find general info"
    },
    {
        "id": 16,
        "category": "regulatory",
        "query": "Est ce possible/homologué de mélanger du karaté zeon avec du select en déherbage colza?",
        "expected_needs": ["regulatory"],
        "prediction": "WORK - EPHY database should have this"
    },
    {
        "id": 17,
        "category": "agronomic_regulatory",
        "query": "Dois je semer une CIPAN entre mon colza et un blé semé en octobre 2025?",
        "expected_needs": ["regulatory", "farm_context"],
        "prediction": "PARTIAL - Generic regulatory answer"
    },
    {
        "id": 18,
        "category": "regulatory",
        "query": "A quel stade le Biplay SX est homologué sur les blés?",
        "expected_needs": ["regulatory"],
        "prediction": "WORK - EPHY database should have this"
    },
    {
        "id": 19,
        "category": "farm_data",
        "query": "sors moi l'état des stocks de produits phytosanitaires et engrais à date",
        "expected_needs": ["farm_data"],
        "prediction": "FAIL - Inventory data"
    }
]


class FarmerQueryTester:
    """Test harness for farmer queries"""
    
    def __init__(self):
        self.tool_registry = get_tool_registry()
        self.streaming_service = OptimizedStreamingService(
            tool_executor=self.tool_registry
        )
        self.results = []
    
    async def test_query(
        self, 
        query_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a single query and return results"""
        
        print(f"\n{'='*80}")
        print(f"Query #{query_data['id']}: {query_data['category']}")
        print(f"{'='*80}")
        print(f"Q: {query_data['query']}")
        print(f"Prediction: {query_data['prediction']}")
        print(f"-" * 80)
        
        start_time = time.time()
        
        try:
            # Collect streaming response
            response_text = ""
            routing_info = None
            tools_used = []
            
            async for chunk in self.streaming_service.stream_response(
                query=query_data['query'],
                context=context,
                use_workflow=True
            ):
                if chunk.get("type") == "workflow_step" and chunk.get("step") == "routing":
                    routing_info = chunk.get("message")
                
                if chunk.get("type") == "workflow_step" and chunk.get("step") == "tools":
                    tools_used = chunk.get("message", "")
                
                if chunk.get("type") in ["workflow_result", "advanced_result"]:
                    response_text = chunk.get("response", "")
            
            elapsed_time = time.time() - start_time
            
            # Analyze response quality
            quality = self._assess_response_quality(
                query_data, 
                response_text,
                routing_info,
                tools_used
            )
            
            result = {
                "query_id": query_data['id'],
                "category": query_data['category'],
                "query": query_data['query'],
                "prediction": query_data['prediction'],
                "response": response_text[:500],  # First 500 chars
                "routing": routing_info,
                "tools_used": tools_used,
                "elapsed_time": elapsed_time,
                "quality": quality,
                "expected_needs": query_data['expected_needs']
            }
            
            print(f"Response: {response_text[:200]}...")
            print(f"Routing: {routing_info}")
            print(f"Tools: {tools_used}")
            print(f"Quality: {quality}")
            print(f"Time: {elapsed_time:.2f}s")
            
            return result
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return {
                "query_id": query_data['id'],
                "category": query_data['category'],
                "query": query_data['query'],
                "prediction": query_data['prediction'],
                "error": str(e),
                "quality": "ERROR"
            }
    
    def _assess_response_quality(
        self,
        query_data: Dict,
        response: str,
        routing: str,
        tools: str
    ) -> str:
        """Assess response quality: WORK, PARTIAL, FAIL"""

        response_lower = response.lower()

        # Check for deflection patterns
        deflection_patterns = [
            "consulter",
            "contacter",
            "agronomist",
            "je ne peux pas",
            "je n'ai pas accès",
            "données non disponibles",
            "outils ne fournissent pas",
            "outils ne sont pas disponibles"
        ]

        if any(pattern in response_lower for pattern in deflection_patterns):
            return "FAIL"

        # Check for mock data indicators (PHASE 2/3 SUCCESS!)
        mock_data_indicators = [
            "15.5 tonnes",  # Mock wheat quantity
            "15,5 hectares",  # Mock area
            "72,3 quintaux",  # Mock yield
            "450,00 euros",  # Mock price
            "parcelle a",  # Mock parcel name
            "fr_farm_123456"  # Mock farm ID
        ]

        has_mock_data = any(indicator in response_lower for indicator in mock_data_indicators)

        # If query needs farm data and response has mock data = PARTIAL SUCCESS
        # (Tools are working, but returning mock data instead of real data)
        if "farm_data" in query_data['expected_needs'] and has_mock_data:
            return "PARTIAL"

        # Check for generic responses
        generic_patterns = [
            "en général",
            "typiquement",
            "habituellement",
            "il est recommandé de"
        ]

        if any(pattern in response_lower for pattern in generic_patterns):
            if query_data['category'] in ['farm_data', 'farm_data_calculation']:
                return "PARTIAL"

        # If response has specific numbers/data, likely good
        if any(char.isdigit() for char in response):
            return "WORK"

        return "PARTIAL"
    
    async def run_all_tests(self, sample_size: int = None):
        """Run all tests or a sample"""
        
        # Mock user context (replace with real user data)
        context = {
            "user_id": "test_farmer_123",
            "farm_siret": "12345678901234",
            "farm_id": "12345678901234",  # Add both keys for compatibility
            "conversation_id": "test_conversation",
            "agent_type": "general"
        }
        
        queries_to_test = FARMER_QUERIES[:sample_size] if sample_size else FARMER_QUERIES
        
        print(f"\n{'#'*80}")
        print(f"# PHASE 1: Testing {len(queries_to_test)} Farmer Queries")
        print(f"# Current System (Before Fixes)")
        print(f"{'#'*80}\n")
        
        for query_data in queries_to_test:
            result = await self.test_query(query_data, context)
            self.results.append(result)
            
            # Small delay between queries
            await asyncio.sleep(1)
        
        self._print_summary()
        self._save_results()
    
    def _print_summary(self):
        """Print test summary"""
        
        total = len(self.results)
        work_count = sum(1 for r in self.results if r.get('quality') == 'WORK')
        partial_count = sum(1 for r in self.results if r.get('quality') == 'PARTIAL')
        fail_count = sum(1 for r in self.results if r.get('quality') == 'FAIL')
        error_count = sum(1 for r in self.results if r.get('quality') == 'ERROR')
        
        print(f"\n{'='*80}")
        print(f"PHASE 1 RESULTS SUMMARY")
        print(f"{'='*80}")
        print(f"Total Queries: {total}")
        print(f"✅ WORK:    {work_count:2d} ({work_count/total*100:.1f}%)")
        print(f"⚠️  PARTIAL: {partial_count:2d} ({partial_count/total*100:.1f}%)")
        print(f"❌ FAIL:    {fail_count:2d} ({fail_count/total*100:.1f}%)")
        print(f"🔥 ERROR:   {error_count:2d} ({error_count/total*100:.1f}%)")
        print(f"{'='*80}\n")
        
        # Breakdown by category
        categories = {}
        for result in self.results:
            cat = result.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = {'WORK': 0, 'PARTIAL': 0, 'FAIL': 0, 'ERROR': 0}
            quality = result.get('quality', 'ERROR')
            categories[cat][quality] += 1
        
        print("Breakdown by Category:")
        print("-" * 80)
        for cat, counts in sorted(categories.items()):
            total_cat = sum(counts.values())
            print(f"{cat:25s}: {counts['WORK']}/{total_cat} work, "
                  f"{counts['PARTIAL']}/{total_cat} partial, "
                  f"{counts['FAIL']}/{total_cat} fail")
        print()
    
    def _save_results(self):
        """Save results to JSON file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_phase1_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "phase": "PHASE_1_BASELINE",
                "total_queries": len(self.results),
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {filename}\n")


async def main():
    """Main test runner"""

    import sys

    tester = FarmerQueryTester()

    # Check command line args
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        print("Testing ALL 19 queries...")
        await tester.run_all_tests()
    else:
        # Test a sample first (5 queries)
        print("Testing sample of 5 queries...")
        print("(Run with 'python test_farmer_queries.py all' to test all 19)")
        await tester.run_all_tests(sample_size=5)


if __name__ == "__main__":
    asyncio.run(main())

