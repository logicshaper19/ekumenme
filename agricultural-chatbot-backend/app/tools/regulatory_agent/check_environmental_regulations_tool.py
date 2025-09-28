"""
Check Environmental Regulations Tool - Single Purpose Tool

Job: Check environmental regulations for agricultural practices.
Input: practice_type, location, environmental_impact
Output: JSON string with environmental regulation compliance

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentalRegulation:
    """Structured environmental regulation."""
    regulation_type: str
    regulation_name: str
    compliance_status: str
    environmental_impact: str
    required_measures: List[str]
    restrictions: List[str]
    penalties: List[str]

class CheckEnvironmentalRegulationsTool(BaseTool):
    """
    Tool: Check environmental regulations for agricultural practices.
    
    Job: Take agricultural practices and check environmental regulation compliance.
    Input: practice_type, location, environmental_impact
    Output: JSON string with environmental regulation compliance
    """
    
    name: str = "check_environmental_regulations_tool"
    description: str = "Vérifie la conformité aux réglementations environnementales"
    
    def _run(
        self,
        practice_type: str,
        location: str = None,
        environmental_impact: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        Check environmental regulations for agricultural practices.
        
        Args:
            practice_type: Type of agricultural practice (spraying, fertilization, etc.)
            location: Location of the practice
            environmental_impact: Environmental impact assessment
        """
        try:
            # Get environmental regulations database
            environmental_database = self._get_environmental_database()
            
            # Check environmental compliance
            environmental_regulations = self._check_environmental_compliance(practice_type, location, environmental_impact or {}, environmental_database)
            
            # Calculate environmental risk
            environmental_risk = self._calculate_environmental_risk(environmental_regulations)
            
            # Generate environmental recommendations
            environmental_recommendations = self._generate_environmental_recommendations(environmental_regulations)
            
            result = {
                "practice_type": practice_type,
                "location": location,
                "environmental_impact": environmental_impact or {},
                "environmental_regulations": [asdict(regulation) for regulation in environmental_regulations],
                "environmental_risk": environmental_risk,
                "environmental_recommendations": environmental_recommendations,
                "total_regulations": len(environmental_regulations)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Check environmental regulations error: {e}")
            return json.dumps({"error": f"Erreur lors de la vérification des réglementations environnementales: {str(e)}"})
    
    def _get_environmental_database(self) -> Dict[str, Any]:
        """Get environmental regulations database."""
        environmental_database = {
            "spraying": {
                "water_protection": {
                    "regulation_name": "Protection des eaux",
                    "compliance_status": "required",
                    "environmental_impact": "high",
                    "required_measures": ["ZNT_5m", "éviter_ruissellement", "respecter_doses"],
                    "restrictions": ["interdiction_proche_cours_eau", "interdiction_pluie"],
                    "penalties": ["amende_3000€", "suspension_autorisation"]
                },
                "biodiversity_protection": {
                    "regulation_name": "Protection de la biodiversité",
                    "compliance_status": "required",
                    "environmental_impact": "moderate",
                    "required_measures": ["éviter_abeilles", "respecter_cycles", "alternatives_biologiques"],
                    "restrictions": ["interdiction_floraison", "interdiction_nidification"],
                    "penalties": ["amende_2000€", "compensation_écologique"]
                },
                "air_quality": {
                    "regulation_name": "Qualité de l'air",
                    "compliance_status": "required",
                    "environmental_impact": "moderate",
                    "required_measures": ["éviter_dérive", "vent_favorable", "équipement_contrôlé"],
                    "restrictions": ["interdiction_vent_fort", "interdiction_proche_habitations"],
                    "penalties": ["amende_1500€", "suspension_activité"]
                }
            },
            "fertilization": {
                "nitrate_directive": {
                    "regulation_name": "Directive Nitrates",
                    "compliance_status": "required",
                    "environmental_impact": "high",
                    "required_measures": ["plafond_azote", "plan_épandage", "cahier_charges"],
                    "restrictions": ["interdiction_hiver", "interdiction_proche_eau"],
                    "penalties": ["amende_5000€", "suspension_aides"]
                },
                "phosphorus_management": {
                    "regulation_name": "Gestion du phosphore",
                    "compliance_status": "required",
                    "environmental_impact": "moderate",
                    "required_measures": ["plafond_phosphore", "analyse_sol", "rotation_cultures"],
                    "restrictions": ["interdiction_surplus", "interdiction_proche_eau"],
                    "penalties": ["amende_3000€", "suspension_aides"]
                }
            },
            "irrigation": {
                "water_usage": {
                    "regulation_name": "Usage de l'eau",
                    "compliance_status": "required",
                    "environmental_impact": "high",
                    "required_measures": ["compteur_eau", "plafond_usage", "efficacité_irrigation"],
                    "restrictions": ["interdiction_été", "interdiction_sécheresse"],
                    "penalties": ["amende_4000€", "suspension_prélèvement"]
                },
                "groundwater_protection": {
                    "regulation_name": "Protection des eaux souterraines",
                    "compliance_status": "required",
                    "environmental_impact": "high",
                    "required_measures": ["éviter_contamination", "surveillance_qualité", "zones_protection"],
                    "restrictions": ["interdiction_proche_captage", "interdiction_contamination"],
                    "penalties": ["amende_5000€", "suspension_activité"]
                }
            }
        }
        
        return environmental_database
    
    def _check_environmental_compliance(self, practice_type: str, location: str, environmental_impact: Dict[str, Any], environmental_database: Dict[str, Any]) -> List[EnvironmentalRegulation]:
        """Check environmental compliance for specific practice."""
        regulations = []
        
        if practice_type not in environmental_database:
            return regulations
        
        practice_regulations = environmental_database[practice_type]
        
        for regulation_type, regulation_data in practice_regulations.items():
            # Check compliance based on environmental impact
            compliance_status = self._assess_compliance(regulation_data, environmental_impact)
            
            regulation = EnvironmentalRegulation(
                regulation_type=regulation_type,
                regulation_name=regulation_data["regulation_name"],
                compliance_status=compliance_status,
                environmental_impact=regulation_data["environmental_impact"],
                required_measures=regulation_data["required_measures"],
                restrictions=regulation_data["restrictions"],
                penalties=regulation_data["penalties"]
            )
            regulations.append(regulation)
        
        return regulations
    
    def _assess_compliance(self, regulation_data: Dict[str, Any], environmental_impact: Dict[str, Any]) -> str:
        """Assess compliance status based on environmental impact."""
        # Simulate compliance assessment based on environmental impact
        if not environmental_impact:
            return "unknown"
        
        # Check if environmental impact is within acceptable limits
        impact_level = environmental_impact.get("impact_level", "moderate")
        
        if impact_level == "low":
            return "compliant"
        elif impact_level == "moderate":
            return "partially_compliant"
        else:
            return "non_compliant"
    
    def _calculate_environmental_risk(self, environmental_regulations: List[EnvironmentalRegulation]) -> Dict[str, Any]:
        """Calculate environmental risk based on regulations."""
        if not environmental_regulations:
            return {"risk_level": "unknown", "risk_score": 0.0}
        
        # Calculate risk based on compliance status and environmental impact
        risk_score = 0.0
        high_impact_count = 0
        
        for regulation in environmental_regulations:
            if regulation.environmental_impact == "high":
                high_impact_count += 1
                if regulation.compliance_status == "non_compliant":
                    risk_score += 0.8
                elif regulation.compliance_status == "partially_compliant":
                    risk_score += 0.5
                else:
                    risk_score += 0.2
            elif regulation.environmental_impact == "moderate":
                if regulation.compliance_status == "non_compliant":
                    risk_score += 0.5
                elif regulation.compliance_status == "partially_compliant":
                    risk_score += 0.3
                else:
                    risk_score += 0.1
        
        # Normalize risk score
        if high_impact_count > 0:
            risk_score = risk_score / high_impact_count
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2)
        }
    
    def _generate_environmental_recommendations(self, environmental_regulations: List[EnvironmentalRegulation]) -> List[str]:
        """Generate environmental recommendations based on regulations."""
        recommendations = []
        
        for regulation in environmental_regulations:
            if regulation.compliance_status == "non_compliant":
                recommendations.append(f"⚠️ Non-conformité: {regulation.regulation_name}")
                recommendations.extend([f"Mesure requise: {measure}" for measure in regulation.required_measures])
                recommendations.extend([f"Restriction: {restriction}" for restriction in regulation.restrictions])
            elif regulation.compliance_status == "partially_compliant":
                recommendations.append(f"⚠️ Conformité partielle: {regulation.regulation_name}")
                recommendations.extend([f"Amélioration: {measure}" for measure in regulation.required_measures])
            else:
                recommendations.append(f"✅ Conforme: {regulation.regulation_name}")
        
        if not recommendations:
            recommendations.append("✅ Toutes les réglementations environnementales sont respectées")
        
        return recommendations
