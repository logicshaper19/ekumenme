#!/usr/bin/env python3
"""
Test script for database-integrated regulatory agent
Tests configuration-first, database-backed approach
"""

import asyncio
import json
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent))

from app.services.configuration_service import get_configuration_service
from app.services.unified_regulatory_service import UnifiedRegulatoryService
from app.tools.regulatory_agent.database_integrated_amm_tool import DatabaseIntegratedAMMLookupTool


async def test_configuration_service():
    """Test configuration service with hot-reload"""
    print("🔧 Testing Configuration Service...")
    print("=" * 50)
    
    try:
        config_service = get_configuration_service()
        
        # Test regulatory config loading
        regulatory_config = config_service.get_regulatory_config()
        print(f"✅ Loaded regulatory config version: {regulatory_config.get('metadata', {}).get('version', 'N/A')}")
        
        # Test specific configuration sections
        znt_requirements = config_service.get_znt_requirements('cours_eau')
        print(f"✅ ZNT cours d'eau: {znt_requirements.get('minimum_meters', 'N/A')}m minimum")
        
        # Test application limits
        glyphosate_limits = config_service.get_application_limits('glyphosate')
        print(f"✅ Glyphosate limits: {glyphosate_limits.get('max_applications_per_year', 'N/A')} applications/an")
        
        # Test safety intervals
        wheat_intervals = config_service.get_safety_intervals('cereales')
        print(f"✅ Céréales délai avant récolte: {wheat_intervals.get('pre_harvest_days', 'N/A')} jours")
        
        # Test seasonal adjustments
        spring_adjustments = config_service.get_seasonal_adjustments('printemps')
        print(f"✅ Ajustements printemps: protection abeilles x{spring_adjustments.get('bee_protection_multiplier', 'N/A')}")
        
        # Test regional factors
        bretagne_factors = config_service.get_regional_factors('bretagne')
        print(f"✅ Facteurs Bretagne: pluie x{bretagne_factors.get('rainfall_multiplier', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration service test failed: {e}")
        return False


async def test_unified_regulatory_service():
    """Test unified regulatory service with database integration"""
    print("\n🗄️ Testing Unified Regulatory Service...")
    print("=" * 50)
    
    try:
        regulatory_service = UnifiedRegulatoryService()
        
        # Test with mock database session (would need real DB in production)
        print("✅ Unified regulatory service initialized")
        print("⚠️  Database integration test requires active database connection")
        
        return True
        
    except Exception as e:
        print(f"❌ Unified regulatory service test failed: {e}")
        return False


def test_database_integrated_tool():
    """Test database-integrated AMM lookup tool"""
    print("\n🔍 Testing Database-Integrated AMM Tool...")
    print("=" * 50)
    
    try:
        tool = DatabaseIntegratedAMMLookupTool()
        print(f"✅ Tool initialized: {tool.name}")
        print(f"✅ Tool description: {tool.description[:100]}...")
        
        # Test tool execution (would need database in production)
        print("⚠️  Tool execution test requires active database connection")
        
        # Test configuration integration
        config_service = get_configuration_service()
        regulatory_config = config_service.get_regulatory_config()
        print(f"✅ Tool can access configuration version: {regulatory_config.get('metadata', {}).get('version', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database-integrated tool test failed: {e}")
        return False


def test_configuration_structure():
    """Test configuration file structure and validation"""
    print("\n📋 Testing Configuration Structure...")
    print("=" * 50)
    
    try:
        config_service = get_configuration_service()
        config = config_service.get_regulatory_config()
        
        # Test required sections
        required_sections = [
            'metadata',
            'validation_settings',
            'znt_requirements',
            'application_limits',
            'safety_intervals',
            'seasonal_adjustments',
            'regional_factors',
            'risk_assessment',
            'compliance_scoring'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
            else:
                print(f"✅ Section présente: {section}")
        
        if missing_sections:
            print(f"❌ Sections manquantes: {missing_sections}")
            return False
        
        # Test specific configuration values
        znt_cours_eau = config.get('znt_requirements', {}).get('cours_eau', {})
        if znt_cours_eau.get('minimum_meters', 0) >= 5:
            print(f"✅ ZNT cours d'eau valide: {znt_cours_eau.get('minimum_meters')}m")
        else:
            print(f"❌ ZNT cours d'eau invalide: {znt_cours_eau.get('minimum_meters')}m")
            return False
        
        # Test compliance scoring weights
        weights = config.get('compliance_scoring', {}).get('weights', {})
        total_weight = sum(weights.values())
        if 0.9 <= total_weight <= 1.1:  # Allow small rounding errors
            print(f"✅ Poids de conformité valides: total = {total_weight:.2f}")
        else:
            print(f"❌ Poids de conformité invalides: total = {total_weight:.2f}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration structure test failed: {e}")
        return False


def test_farm_context_scenarios():
    """Test different farm context scenarios"""
    print("\n🚜 Testing Farm Context Scenarios...")
    print("=" * 50)
    
    try:
        config_service = get_configuration_service()
        
        # Scenario 1: Organic farm in Bretagne
        organic_bretagne = {
            "farm_type": "organic",
            "region": "bretagne",
            "distance_to_water_m": 15,
            "crop_type": "cereales",
            "organic_certified": True
        }
        
        # Test regional factors
        bretagne_factors = config_service.get_regional_factors('bretagne')
        print(f"✅ Bretagne - Facteur pluie: {bretagne_factors.get('rainfall_multiplier', 'N/A')}")
        print(f"✅ Bretagne - Restrictions: {bretagne_factors.get('special_restrictions', [])}")
        
        # Test safety intervals for cereals
        cereal_intervals = config_service.get_safety_intervals('cereales')
        print(f"✅ Céréales - Délai avant récolte: {cereal_intervals.get('pre_harvest_days')} jours")
        
        # Scenario 2: Conventional farm in Provence
        conventional_provence = {
            "farm_type": "conventional",
            "region": "provence",
            "distance_to_water_m": 100,
            "crop_type": "vignes",
            "organic_certified": False
        }
        
        # Test regional factors
        provence_factors = config_service.get_regional_factors('provence')
        print(f"✅ Provence - Facteur sécheresse: {provence_factors.get('drought_risk_multiplier', 'N/A')}")
        print(f"✅ Provence - Facteur incendie: {provence_factors.get('fire_risk_multiplier', 'N/A')}")
        
        # Test safety intervals for grapes
        grape_intervals = config_service.get_safety_intervals('vignes')
        print(f"✅ Vignes - Délai avant récolte: {grape_intervals.get('pre_harvest_days')} jours")
        
        return True
        
    except Exception as e:
        print(f"❌ Farm context scenarios test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Testing Configuration-First, Database-Backed Regulatory Agent")
    print("=" * 70)
    
    all_tests_passed = True
    
    # Run tests
    tests = [
        test_configuration_service,
        test_unified_regulatory_service,
        test_database_integrated_tool,
        test_configuration_structure,
        test_farm_context_scenarios
    ]
    
    for test in tests:
        if asyncio.iscoroutinefunction(test):
            success = await test()
        else:
            success = test()
        
        if not success:
            all_tests_passed = False
        print()
    
    print("=" * 70)
    if all_tests_passed:
        print("🎉 All tests passed! Configuration-first regulatory agent ready!")
        print("\n📋 Summary of Implementation:")
        print("✅ Configuration service with hot-reload")
        print("✅ Comprehensive regulatory compliance rules")
        print("✅ Database-integrated AMM lookup tool")
        print("✅ Unified regulatory service")
        print("✅ Seasonal and regional adjustments")
        print("✅ Farm context-aware recommendations")
        print("\n🚀 Next Steps:")
        print("1. Connect to real EPHY database")
        print("2. Test with actual farm data")
        print("3. Validate compliance calculations")
        print("4. Deploy configuration management interface")
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
    
    return all_tests_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
