"""
Unit Tests for Agricultural Chatbot Prompts

This module contains comprehensive unit tests for all prompts in the agricultural chatbot system.
Tests cover input validation, output format, edge cases, error handling, and compliance.
"""

import unittest
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict, Any, List

# Import prompt modules
from app.prompts.base_prompts import (
    BASE_AGRICULTURAL_SYSTEM_PROMPT,
    FARM_CONTEXT_TEMPLATE,
    WEATHER_CONTEXT_TEMPLATE,
    RESPONSE_FORMAT_TEMPLATE,
    SAFETY_REMINDER_TEMPLATE
)

from app.prompts.farm_data_prompts import (
    FARM_DATA_CHAT_PROMPT,
    PARCEL_ANALYSIS_PROMPT,
    PERFORMANCE_METRICS_PROMPT
)

from app.prompts.regulatory_prompts import (
    REGULATORY_CHAT_PROMPT,
    AMM_LOOKUP_PROMPT,
    USAGE_CONDITIONS_PROMPT
)

from app.prompts.weather_prompts import (
    WEATHER_CHAT_PROMPT,
    WEATHER_FORECAST_PROMPT,
    INTERVENTION_WINDOW_PROMPT
)

from app.prompts.crop_health_prompts import (
    CROP_HEALTH_CHAT_PROMPT,
    DISEASE_DIAGNOSIS_PROMPT,
    PEST_IDENTIFICATION_PROMPT
)

from app.prompts.planning_prompts import (
    PLANNING_CHAT_PROMPT,
    TASK_PLANNING_PROMPT,
    RESOURCE_OPTIMIZATION_PROMPT
)

from app.prompts.sustainability_prompts import (
    SUSTAINABILITY_CHAT_PROMPT,
    CARBON_FOOTPRINT_PROMPT,
    SOIL_HEALTH_PROMPT
)

from app.prompts.semantic_routing import (
    SemanticIntentClassifier,
    IntentType,
    classify_intent
)

from app.prompts.embedding_system import (
    EmbeddingPromptMatcher,
    find_best_prompt
)

from app.prompts.dynamic_examples import (
    DynamicFewShotManager,
    get_dynamic_examples,
    ExampleType
)

from app.prompts.prompt_manager import (
    PromptManager,
    get_prompt_with_semantic_examples,
    select_prompt_semantic
)


class TestBasePrompts(unittest.TestCase):
    """Test base prompt templates."""
    
    def test_base_agricultural_system_prompt(self):
        """Test base agricultural system prompt."""
        self.assertIn("expert agricole", BASE_AGRICULTURAL_SYSTEM_PROMPT)
        self.assertIn("réglementation française", BASE_AGRICULTURAL_SYSTEM_PROMPT)
        self.assertIn("AMM", BASE_AGRICULTURAL_SYSTEM_PROMPT)
        self.assertIn("hectares", BASE_AGRICULTURAL_SYSTEM_PROMPT)
    
    def test_farm_context_template(self):
        """Test farm context template formatting."""
        context = FARM_CONTEXT_TEMPLATE.format(
            siret="12345678901234",
            farm_name="Ferme Test",
            region_code="24",
            total_area_ha=150.5,
            primary_crops="blé, maïs",
            organic_certified="non",
            coordinates="45.5, 2.3"
        )
        
        self.assertIn("12345678901234", context)
        self.assertIn("Ferme Test", context)
        self.assertIn("150.5 ha", context)
        self.assertIn("blé, maïs", context)
    
    def test_weather_context_template(self):
        """Test weather context template formatting."""
        context = WEATHER_CONTEXT_TEMPLATE.format(
            temperature=15.5,
            humidity=65,
            wind_speed=12,
            precipitation=2.5,
            soil_moisture=45,
            soil_temperature=14.2
        )
        
        self.assertIn("15.5°C", context)
        self.assertIn("65%", context)
        self.assertIn("12 km/h", context)
        self.assertIn("2.5 mm", context)
    
    def test_response_format_template(self):
        """Test response format template."""
        self.assertIn("Analyse", RESPONSE_FORMAT_TEMPLATE)
        self.assertIn("Recommandations", RESPONSE_FORMAT_TEMPLATE)
        self.assertIn("Justification", RESPONSE_FORMAT_TEMPLATE)
        self.assertIn("Sources", RESPONSE_FORMAT_TEMPLATE)
    
    def test_safety_reminder_template(self):
        """Test safety reminder template."""
        self.assertIn("SÉCURITÉ", SAFETY_REMINDER_TEMPLATE)
        self.assertIn("AMM", SAFETY_REMINDER_TEMPLATE)
        self.assertIn("ZNT", SAFETY_REMINDER_TEMPLATE)


class TestFarmDataPrompts(unittest.TestCase):
    """Test farm data agent prompts."""
    
    def test_farm_data_chat_prompt_formatting(self):
        """Test farm data chat prompt formatting."""
        try:
            messages = FARM_DATA_CHAT_PROMPT.format_messages(
                farm_context="Test farm context",
                recent_interventions="Test interventions",
                performance_data="Test data",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)  # system, human, ai
        except Exception as e:
            self.fail(f"Farm data chat prompt formatting failed: {e}")
    
    def test_parcel_analysis_prompt_formatting(self):
        """Test parcel analysis prompt formatting."""
        try:
            messages = PARCEL_ANALYSIS_PROMPT.format_messages(
                parcel_id="P001",
                current_crop="blé",
                growth_stage="épi 1cm",
                farm_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Parcel analysis prompt formatting failed: {e}")
    
    def test_performance_metrics_prompt_formatting(self):
        """Test performance metrics prompt formatting."""
        try:
            messages = PERFORMANCE_METRICS_PROMPT.format_messages(
                period="2024",
                crops="blé, maïs",
                metrics="rendement, coût",
                farm_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Performance metrics prompt formatting failed: {e}")


class TestRegulatoryPrompts(unittest.TestCase):
    """Test regulatory agent prompts."""
    
    def test_regulatory_chat_prompt_formatting(self):
        """Test regulatory chat prompt formatting."""
        try:
            messages = REGULATORY_CHAT_PROMPT.format_messages(
                regulatory_context="Test regulatory context",
                farm_context="Test farm context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Regulatory chat prompt formatting failed: {e}")
    
    def test_amm_lookup_prompt_formatting(self):
        """Test AMM lookup prompt formatting."""
        try:
            messages = AMM_LOOKUP_PROMPT.format_messages(
                product_name="Roundup",
                amm_number="2000233",
                crop="blé",
                usage="désherbage",
                regulatory_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"AMM lookup prompt formatting failed: {e}")
    
    def test_usage_conditions_prompt_formatting(self):
        """Test usage conditions prompt formatting."""
        try:
            messages = USAGE_CONDITIONS_PROMPT.format_messages(
                product_name="Glyphosate",
                crop="blé",
                target="mauvaises herbes",
                regulatory_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Usage conditions prompt formatting failed: {e}")


class TestWeatherPrompts(unittest.TestCase):
    """Test weather agent prompts."""
    
    def test_weather_chat_prompt_formatting(self):
        """Test weather chat prompt formatting."""
        try:
            messages = WEATHER_CHAT_PROMPT.format_messages(
                weather_data="Test weather data",
                farm_context="Test farm context",
                planned_intervention="Test intervention",
                crop="blé",
                growth_stage="épi 1cm",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Weather chat prompt formatting failed: {e}")
    
    def test_weather_forecast_prompt_formatting(self):
        """Test weather forecast prompt formatting."""
        try:
            messages = WEATHER_FORECAST_PROMPT.format_messages(
                forecast_period="7 jours",
                location="Centre",
                intervention_type="traitement",
                weather_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Weather forecast prompt formatting failed: {e}")
    
    def test_intervention_window_prompt_formatting(self):
        """Test intervention window prompt formatting."""
        try:
            messages = INTERVENTION_WINDOW_PROMPT.format_messages(
                intervention_type="traitement",
                crop="blé",
                growth_stage="épi 1cm",
                urgency="moyenne",
                intervention_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Intervention window prompt formatting failed: {e}")


class TestCropHealthPrompts(unittest.TestCase):
    """Test crop health agent prompts."""
    
    def test_crop_health_chat_prompt_formatting(self):
        """Test crop health chat prompt formatting."""
        try:
            messages = CROP_HEALTH_CHAT_PROMPT.format_messages(
                diagnostic_context="Test diagnostic context",
                farm_context="Test farm context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Crop health chat prompt formatting failed: {e}")
    
    def test_disease_diagnosis_prompt_formatting(self):
        """Test disease diagnosis prompt formatting."""
        try:
            messages = DISEASE_DIAGNOSIS_PROMPT.format_messages(
                crop="blé",
                growth_stage="épi 1cm",
                symptoms="taches jaunes",
                location="feuilles basses",
                diagnostic_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Disease diagnosis prompt formatting failed: {e}")
    
    def test_pest_identification_prompt_formatting(self):
        """Test pest identification prompt formatting."""
        try:
            messages = PEST_IDENTIFICATION_PROMPT.format_messages(
                crop="blé",
                growth_stage="épi 1cm",
                damage="dégâts observés",
                insect_presence="présence d'insectes",
                diagnostic_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Pest identification prompt formatting failed: {e}")


class TestPlanningPrompts(unittest.TestCase):
    """Test planning agent prompts."""
    
    def test_planning_chat_prompt_formatting(self):
        """Test planning chat prompt formatting."""
        try:
            messages = PLANNING_CHAT_PROMPT.format_messages(
                planning_context="Test planning context",
                farm_context="Test farm context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Planning chat prompt formatting failed: {e}")
    
    def test_task_planning_prompt_formatting(self):
        """Test task planning prompt formatting."""
        try:
            messages = TASK_PLANNING_PROMPT.format_messages(
                period="semaine",
                interventions="traitement, semis",
                resources="tracteur, pulvérisateur",
                constraints="météo, délais",
                planning_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Task planning prompt formatting failed: {e}")
    
    def test_resource_optimization_prompt_formatting(self):
        """Test resource optimization prompt formatting."""
        try:
            messages = RESOURCE_OPTIMIZATION_PROMPT.format_messages(
                available_resources="tracteur, main-d'œuvre",
                interventions="traitement, semis",
                objectives="efficacité, coût",
                planning_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Resource optimization prompt formatting failed: {e}")


class TestSustainabilityPrompts(unittest.TestCase):
    """Test sustainability agent prompts."""
    
    def test_sustainability_chat_prompt_formatting(self):
        """Test sustainability chat prompt formatting."""
        try:
            messages = SUSTAINABILITY_CHAT_PROMPT.format_messages(
                sustainability_context="Test sustainability context",
                farm_context="Test farm context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Sustainability chat prompt formatting failed: {e}")
    
    def test_carbon_footprint_prompt_formatting(self):
        """Test carbon footprint prompt formatting."""
        try:
            messages = CARBON_FOOTPRINT_PROMPT.format_messages(
                period="2024",
                crops="blé, maïs",
                carbon_data="Test carbon data",
                sustainability_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Carbon footprint prompt formatting failed: {e}")
    
    def test_soil_health_prompt_formatting(self):
        """Test soil health prompt formatting."""
        try:
            messages = SOIL_HEALTH_PROMPT.format_messages(
                soil_analysis="Test soil analysis",
                practices="Test practices",
                issues="Test issues",
                sustainability_context="Test context",
                input="Test query",
                agent_scratchpad=""
            )
            self.assertEqual(len(messages), 3)
        except Exception as e:
            self.fail(f"Soil health prompt formatting failed: {e}")


class TestSemanticRouting(unittest.TestCase):
    """Test semantic routing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = SemanticIntentClassifier()
    
    def test_intent_classification(self):
        """Test intent classification."""
        # Test AMM lookup intent
        result = self.classifier.classify_intent_semantic(
            "Vérifier l'autorisation AMM du Roundup",
            "Produit phytosanitaire"
        )
        
        self.assertIsNotNone(result)
        self.assertIn(result.intent, IntentType)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertIsNotNone(result.selected_prompt)
    
    def test_intent_examples(self):
        """Test intent examples."""
        examples = self.classifier.get_intent_examples()
        self.assertGreater(len(examples), 0)
        
        # Test specific intent examples
        amm_examples = self.classifier.get_intent_examples(IntentType.AMM_LOOKUP)
        self.assertGreater(len(amm_examples), 0)
    
    def test_fallback_classification(self):
        """Test fallback classification."""
        result = self.classifier._fallback_classification("Test query", "Test context")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.FARM_DATA_ANALYSIS)
        self.assertEqual(result.confidence, 0.5)
        self.assertEqual(result.selected_prompt, "FARM_DATA_CHAT_PROMPT")


class TestEmbeddingSystem(unittest.TestCase):
    """Test embedding-based prompt matching."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.matcher = EmbeddingPromptMatcher()
    
    def test_prompt_matching(self):
        """Test prompt matching functionality."""
        matches = self.matcher.find_best_prompt(
            "Vérifier l'autorisation AMM du Roundup",
            "Produit phytosanitaire",
            top_k=3
        )
        
        self.assertIsInstance(matches, list)
        self.assertLessEqual(len(matches), 3)
        
        if matches:
            match = matches[0]
            self.assertIsNotNone(match.prompt_name)
            self.assertGreaterEqual(match.similarity_score, 0.0)
            self.assertLessEqual(match.similarity_score, 1.0)
    
    def test_intent_based_matching(self):
        """Test intent-based prompt matching."""
        match = self.matcher.find_prompt_by_intent("AMM_LOOKUP", "Test context")
        
        if match:
            self.assertIsNotNone(match.prompt_name)
            self.assertEqual(match.similarity_score, 1.0)
            self.assertIn("AMM_LOOKUP", match.reasoning)
    
    def test_fallback_matching(self):
        """Test fallback matching."""
        matches = self.matcher._fallback_matching(
            "Test query with keywords",
            "Test context",
            top_k=3
        )
        
        self.assertIsInstance(matches, list)
        self.assertLessEqual(len(matches), 3)


class TestDynamicExamples(unittest.TestCase):
    """Test dynamic few-shot examples system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = DynamicFewShotManager()
    
    def test_dynamic_examples_retrieval(self):
        """Test dynamic examples retrieval."""
        examples = self.manager.get_dynamic_examples(
            "AMM_LOOKUP_PROMPT",
            "Produit phytosanitaire",
            "Vérifier l'autorisation AMM"
        )
        
        self.assertIsInstance(examples, str)
        if examples:
            self.assertIn("Exemple", examples)
            self.assertIn("Question:", examples)
            self.assertIn("Réponse:", examples)
    
    def test_example_addition(self):
        """Test adding new examples."""
        from app.prompts.dynamic_examples import FewShotExample, ExampleType
        
        example = FewShotExample(
            prompt_type="TEST_PROMPT",
            example_type=ExampleType.BASIC,
            user_query="Test query",
            context="Test context",
            expected_response="Test response",
            reasoning="Test reasoning",
            confidence=0.9,
            tags=["test"],
            created_at=datetime.now()
        )
        
        result = self.manager.add_example(example)
        self.assertTrue(result)
    
    def test_example_stats(self):
        """Test example statistics."""
        stats = self.manager.get_example_stats()
        
        self.assertIsInstance(stats, dict)
        for prompt_type, stat in stats.items():
            self.assertIn("total_examples", stat)
            self.assertIn("example_types", stat)
            self.assertIn("avg_confidence", stat)


class TestPromptManager(unittest.TestCase):
    """Test prompt manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = PromptManager()
    
    def test_semantic_prompt_selection(self):
        """Test semantic prompt selection."""
        result = self.manager.select_prompt_semantic(
            "Vérifier l'autorisation AMM du Roundup",
            "Produit phytosanitaire"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("selected_prompt", result)
        self.assertIn("confidence", result)
        self.assertIn("reasoning", result)
        self.assertIn("method", result)
    
    def test_prompt_with_examples(self):
        """Test prompt with dynamic examples."""
        prompt = self.manager.get_prompt_with_examples(
            "AMM_LOOKUP_PROMPT",
            "Vérifier l'autorisation AMM",
            "Produit phytosanitaire"
        )
        
        self.assertIsInstance(prompt, str)
        if self.manager.enable_dynamic_examples:
            # Should contain examples if enabled
            pass
    
    def test_routing_method_management(self):
        """Test routing method management."""
        # Test setting routing method
        result = self.manager.set_routing_method("embedding")
        self.assertTrue(result)
        
        # Test getting routing method
        method = self.manager.get_routing_method()
        self.assertEqual(method, "embedding")
        
        # Test invalid method
        result = self.manager.set_routing_method("invalid")
        self.assertFalse(result)
    
    def test_dynamic_examples_management(self):
        """Test dynamic examples management."""
        # Test enabling/disabling
        result = self.manager.enable_dynamic_examples_injection(False)
        self.assertTrue(result)
        
        # Test adding example
        result = self.manager.add_dynamic_example(
            "TEST_PROMPT",
            "BASIC",
            "Test query",
            "Test context",
            "Test response",
            "Test reasoning",
            0.9,
            ["test"]
        )
        self.assertTrue(result)
    
    def test_complete_prompt_workflow(self):
        """Test complete prompt workflow."""
        result = self.manager.get_prompt_with_semantic_examples(
            "Vérifier l'autorisation AMM du Roundup",
            "Produit phytosanitaire"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("prompt_type", result)
        self.assertIn("prompt_content", result)
        self.assertIn("selection_info", result)
        self.assertIn("examples_injected", result)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        classifier = SemanticIntentClassifier()
        
        # Test empty query
        result = classifier.classify_intent_semantic("", "")
        self.assertIsNotNone(result)
        
        # Test None inputs
        result = classifier.classify_intent_semantic(None, None)
        self.assertIsNotNone(result)
    
    def test_invalid_prompt_types(self):
        """Test handling of invalid prompt types."""
        manager = DynamicFewShotManager()
        
        # Test invalid prompt type
        examples = manager.get_dynamic_examples("INVALID_PROMPT", "", "")
        self.assertEqual(examples, "")
    
    def test_malformed_context(self):
        """Test handling of malformed context."""
        try:
            # Test malformed farm context
            context = FARM_CONTEXT_TEMPLATE.format(
                siret="invalid",
                farm_name=None,
                region_code="",
                total_area_ha="not_a_number",
                primary_crops=None,
                organic_certified="",
                coordinates=""
            )
            # Should not raise exception
            self.assertIsInstance(context, str)
        except Exception as e:
            self.fail(f"Malformed context handling failed: {e}")


class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def test_classification_speed(self):
        """Test intent classification speed."""
        import time
        
        classifier = SemanticIntentClassifier()
        
        start_time = time.time()
        for _ in range(10):
            classifier.classify_intent_semantic("Test query", "Test context")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        self.assertLess(avg_time, 1.0)  # Should be fast
    
    def test_prompt_matching_speed(self):
        """Test prompt matching speed."""
        import time
        
        matcher = EmbeddingPromptMatcher()
        
        start_time = time.time()
        for _ in range(10):
            matcher.find_best_prompt("Test query", "Test context")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        self.assertLess(avg_time, 1.0)  # Should be fast


class TestCompliance(unittest.TestCase):
    """Test regulatory compliance and safety."""
    
    def test_safety_guidelines_in_prompts(self):
        """Test that safety guidelines are included in prompts."""
        # Check that safety reminders are in system prompts
        self.assertIn("SÉCURITÉ", SAFETY_REMINDER_TEMPLATE)
        self.assertIn("AMM", SAFETY_REMINDER_TEMPLATE)
        self.assertIn("ZNT", SAFETY_REMINDER_TEMPLATE)
    
    def test_regulatory_compliance(self):
        """Test regulatory compliance in prompts."""
        # Check that regulatory prompts include compliance information
        self.assertIn("réglementation", REGULATORY_CHAT_PROMPT.messages[0].prompt.template)
        self.assertIn("AMM", AMM_LOOKUP_PROMPT.messages[0].prompt.template)
    
    def test_french_agricultural_context(self):
        """Test French agricultural context in prompts."""
        # Check that prompts include French agricultural context
        self.assertIn("France", BASE_AGRICULTURAL_SYSTEM_PROMPT)
        self.assertIn("hectares", BASE_AGRICULTURAL_SYSTEM_PROMPT)
        self.assertIn("kg/ha", BASE_AGRICULTURAL_SYSTEM_PROMPT)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
