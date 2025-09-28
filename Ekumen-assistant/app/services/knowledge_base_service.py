"""
Knowledge Base Service for Disease and Pest Management

This service provides semantic search and intelligent matching for diseases and pests,
supporting the enhanced crop health tools with database-backed knowledge.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from ..core.database import AsyncSessionLocal
from ..models.disease import Disease
from ..models.pest import Pest

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """
    Service for intelligent disease and pest identification using database knowledge.
    
    Provides semantic search, symptom matching, and confidence scoring for
    accurate agricultural diagnosis and pest identification.
    """
    
    def __init__(self):
        self.confidence_threshold = 0.3  # Minimum confidence for results
        self.max_results = 10  # Maximum results to return
    
    async def search_diseases(
        self,
        crop_type: str,
        symptoms: List[str],
        conditions: Optional[Dict[str, Any]] = None,
        severity_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for diseases based on crop type, symptoms, and conditions.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            symptoms: List of observed symptoms
            conditions: Environmental conditions (humidity, temperature, etc.)
            severity_filter: Filter by severity level
            
        Returns:
            Dictionary with search results and confidence scores
        """
        try:
            async with AsyncSessionLocal() as db:
                # Build base query
                query = select(Disease).where(
                    and_(
                        Disease.is_active == True,
                        or_(
                            Disease.primary_crop == crop_type,
                            Disease.affected_crops.contains([crop_type])
                        )
                    )
                )
                
                # Add severity filter if specified
                if severity_filter:
                    query = query.where(Disease.severity_level == severity_filter)
                
                # Execute query
                result = await db.execute(query)
                diseases = result.scalars().all()
                
                # Calculate confidence scores based on symptom matching
                scored_diseases = []
                for disease in diseases:
                    confidence = self._calculate_disease_confidence(
                        disease, symptoms, conditions
                    )
                    
                    if confidence >= self.confidence_threshold:
                        scored_diseases.append({
                            "disease": disease.to_dict(),
                            "confidence_score": confidence,
                            "matching_symptoms": self._get_matching_symptoms(disease, symptoms),
                            "condition_match": self._evaluate_condition_match(disease, conditions)
                        })
                
                # Sort by confidence score
                scored_diseases.sort(key=lambda x: x["confidence_score"], reverse=True)
                
                return {
                    "crop_type": crop_type,
                    "search_symptoms": symptoms,
                    "search_conditions": conditions,
                    "total_results": len(scored_diseases),
                    "diseases": scored_diseases[:self.max_results],
                    "search_metadata": {
                        "confidence_threshold": self.confidence_threshold,
                        "max_results": self.max_results,
                        "database_diseases_count": len(diseases)
                    }
                }
                
        except Exception as e:
            logger.error(f"Disease search error: {e}")
            return {
                "error": f"Erreur lors de la recherche de maladies: {str(e)}",
                "crop_type": crop_type,
                "total_results": 0,
                "diseases": []
            }
    
    async def search_pests(
        self,
        crop_type: str,
        damage_patterns: List[str],
        pest_indicators: List[str],
        severity_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for pests based on crop type, damage patterns, and indicators.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            damage_patterns: List of observed damage patterns
            pest_indicators: List of pest presence indicators
            severity_filter: Filter by severity level
            
        Returns:
            Dictionary with search results and confidence scores
        """
        try:
            async with AsyncSessionLocal() as db:
                # Build base query
                query = select(Pest).where(
                    and_(
                        Pest.is_active == True,
                        or_(
                            Pest.primary_crop == crop_type,
                            Pest.affected_crops.contains([crop_type])
                        )
                    )
                )
                
                # Add severity filter if specified
                if severity_filter:
                    query = query.where(Pest.severity_level == severity_filter)
                
                # Execute query
                result = await db.execute(query)
                pests = result.scalars().all()
                
                # Calculate confidence scores based on damage and indicator matching
                scored_pests = []
                for pest in pests:
                    confidence = self._calculate_pest_confidence(
                        pest, damage_patterns, pest_indicators
                    )
                    
                    if confidence >= self.confidence_threshold:
                        scored_pests.append({
                            "pest": pest.to_dict(),
                            "confidence_score": confidence,
                            "matching_damage": self._get_matching_damage(pest, damage_patterns),
                            "matching_indicators": self._get_matching_indicators(pest, pest_indicators)
                        })
                
                # Sort by confidence score
                scored_pests.sort(key=lambda x: x["confidence_score"], reverse=True)
                
                return {
                    "crop_type": crop_type,
                    "search_damage_patterns": damage_patterns,
                    "search_pest_indicators": pest_indicators,
                    "total_results": len(scored_pests),
                    "pests": scored_pests[:self.max_results],
                    "search_metadata": {
                        "confidence_threshold": self.confidence_threshold,
                        "max_results": self.max_results,
                        "database_pests_count": len(pests)
                    }
                }
                
        except Exception as e:
            logger.error(f"Pest search error: {e}")
            return {
                "error": f"Erreur lors de la recherche de ravageurs: {str(e)}",
                "crop_type": crop_type,
                "total_results": 0,
                "pests": []
            }
    
    def _calculate_disease_confidence(
        self, 
        disease: Disease, 
        symptoms: List[str], 
        conditions: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for disease match."""
        if not symptoms:
            return 0.0
        
        # Symptom matching (70% weight)
        symptom_matches = 0
        disease_symptoms = disease.symptoms or []
        
        for symptom in symptoms:
            for disease_symptom in disease_symptoms:
                if self._fuzzy_match(symptom, disease_symptom):
                    symptom_matches += 1
                    break
        
        symptom_score = symptom_matches / len(symptoms) if symptoms else 0
        
        # Condition matching (30% weight)
        condition_score = 0.5  # Default neutral score
        if conditions and disease.favorable_conditions:
            condition_score = self._evaluate_condition_match(disease, conditions)
        
        # Weighted final score
        confidence = (symptom_score * 0.7) + (condition_score * 0.3)
        
        return min(confidence, 1.0)
    
    def _calculate_pest_confidence(
        self, 
        pest: Pest, 
        damage_patterns: List[str], 
        pest_indicators: List[str]
    ) -> float:
        """Calculate confidence score for pest match."""
        if not damage_patterns and not pest_indicators:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        # Damage pattern matching (60% weight)
        if damage_patterns:
            damage_matches = 0
            pest_damage = pest.damage_patterns or []
            
            for pattern in damage_patterns:
                for pest_pattern in pest_damage:
                    if self._fuzzy_match(pattern, pest_pattern):
                        damage_matches += 1
                        break
            
            damage_score = damage_matches / len(damage_patterns)
            total_score += damage_score * 0.6
            total_weight += 0.6
        
        # Indicator matching (40% weight)
        if pest_indicators:
            indicator_matches = 0
            pest_indicators_db = pest.pest_indicators or []
            
            for indicator in pest_indicators:
                for pest_indicator in pest_indicators_db:
                    if self._fuzzy_match(indicator, pest_indicator):
                        indicator_matches += 1
                        break
            
            indicator_score = indicator_matches / len(pest_indicators)
            total_score += indicator_score * 0.4
            total_weight += 0.4
        
        # Normalize by total weight
        confidence = total_score / total_weight if total_weight > 0 else 0.0
        
        return min(confidence, 1.0)
    
    def _fuzzy_match(self, term1: str, term2: str) -> bool:
        """Simple fuzzy matching for terms."""
        term1_clean = term1.lower().replace("_", " ").replace("-", " ")
        term2_clean = term2.lower().replace("_", " ").replace("-", " ")
        
        # Exact match
        if term1_clean == term2_clean:
            return True
        
        # Substring match
        if term1_clean in term2_clean or term2_clean in term1_clean:
            return True
        
        # Word overlap
        words1 = set(term1_clean.split())
        words2 = set(term2_clean.split())
        overlap = len(words1.intersection(words2))
        
        return overlap > 0
    
    def _get_matching_symptoms(self, disease: Disease, symptoms: List[str]) -> List[str]:
        """Get list of matching symptoms."""
        matches = []
        disease_symptoms = disease.symptoms or []
        
        for symptom in symptoms:
            for disease_symptom in disease_symptoms:
                if self._fuzzy_match(symptom, disease_symptom):
                    matches.append(disease_symptom)
                    break
        
        return matches
    
    def _get_matching_damage(self, pest: Pest, damage_patterns: List[str]) -> List[str]:
        """Get list of matching damage patterns."""
        matches = []
        pest_damage = pest.damage_patterns or []
        
        for pattern in damage_patterns:
            for pest_pattern in pest_damage:
                if self._fuzzy_match(pattern, pest_pattern):
                    matches.append(pest_pattern)
                    break
        
        return matches
    
    def _get_matching_indicators(self, pest: Pest, pest_indicators: List[str]) -> List[str]:
        """Get list of matching pest indicators."""
        matches = []
        pest_indicators_db = pest.pest_indicators or []
        
        for indicator in pest_indicators:
            for pest_indicator in pest_indicators_db:
                if self._fuzzy_match(indicator, pest_indicator):
                    matches.append(pest_indicator)
                    break
        
        return matches
    
    def _evaluate_condition_match(self, disease: Disease, conditions: Optional[Dict[str, Any]]) -> float:
        """Evaluate how well conditions match disease preferences."""
        if not conditions or not disease.favorable_conditions:
            return 0.5  # Neutral score
        
        matches = 0
        total_conditions = 0
        
        disease_conditions = disease.favorable_conditions
        
        for condition, value in conditions.items():
            if condition in disease_conditions:
                total_conditions += 1
                disease_value = disease_conditions[condition]
                
                # Simple matching logic
                if isinstance(disease_value, str) and isinstance(value, str):
                    if disease_value.lower() == value.lower():
                        matches += 1
                elif isinstance(disease_value, (int, float)) and isinstance(value, (int, float)):
                    # For numeric values, consider close matches
                    if abs(disease_value - value) <= disease_value * 0.2:  # 20% tolerance
                        matches += 1
        
        return matches / total_conditions if total_conditions > 0 else 0.5
