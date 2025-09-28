"""
Integrated Operational & Economic Planning Agent with comprehensive cost optimization,
profitability analysis, and resource planning capabilities.
"""

from typing import Dict, List, Any, Optional, Union
from langchain.tools import BaseTool
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Import from integrated system
try:
    from .base_agent import IntegratedAgriculturalAgent, AgentType, TaskComplexity, AgentState
    from .base_agent import SemanticKnowledgeRetriever
except ImportError:
    # Fallback imports
    class AgentType:
        PLANNING = "planning"
    
    class TaskComplexity:
        SIMPLE = "simple"
        MODERATE = "moderate"
        COMPLEX = "complex"
        CRITICAL = "critical"
    
    class SemanticKnowledgeRetriever:
        def retrieve_relevant_knowledge(self, query: str, top_k: int = 3) -> List[str]:
            return ["Connaissance planification agricole générale disponible"]
    
    # Fallback base class
    class IntegratedAgriculturalAgent:
        def __init__(self, agent_type, description, llm_manager, knowledge_retriever, 
                     complexity_default=None, specialized_tools=None):
            self.agent_type = agent_type
            self.description = description
            self.llm_manager = llm_manager
            self.knowledge_retriever = knowledge_retriever
            self.complexity_default = complexity_default
            self.specialized_tools = specialized_tools or []
        
        def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
            return {"response": "Mock response", "agent_type": self.agent_type.value}
        
        def _get_agent_prompt_template(self) -> str:
            return "Mock prompt template"
        
        def _analyze_message_complexity(self, message: str, context: Dict[str, Any]):
            return TaskComplexity.COMPLEX
        
        def _retrieve_domain_knowledge(self, message: str) -> List[str]:
            return ["Mock knowledge"]

logger = logging.getLogger(__name__)

@dataclass
class EconomicTask:
    """Enhanced task with economic parameters."""
    id: str
    name: str
    duration_hours: float
    required_equipment: List[str]
    required_workers: int
    weather_dependencies: List[str]
    priority: int
    variable_costs: Dict[str, float]  # Seeds, fertilizer, pesticides, fuel
    fixed_costs: Dict[str, float]     # Equipment depreciation, labor
    expected_yield_impact: float      # Yield increase/decrease from this task
    profit_margin_impact: float       # Direct impact on profit margin

@dataclass
class EconomicPlan:
    """Comprehensive planning output with economic analysis."""
    tasks: List[Dict[str, Any]]
    total_duration: float
    total_variable_costs: float
    total_fixed_costs: float
    expected_revenue: float
    profit_margin: float
    roi_analysis: Dict[str, Any]
    cost_optimization_opportunities: List[Dict[str, Any]]
    resource_utilization: Dict[str, float]
    weather_windows: List[Dict[str, Any]]

class SemanticPlanningOptimizationTool(BaseTool):
    """Comprehensive planning tool with semantic understanding and economic optimization."""
    
    name: str = "semantic_planning_optimization"
    description: str = "Planification opérationnelle et économique avec optimisation des coûts"
    
    def __init__(self, knowledge_retriever: SemanticKnowledgeRetriever = None, **kwargs):
        super().__init__(**kwargs)
        self.knowledge_retriever = knowledge_retriever
        
        # Enhanced equipment database with economic data
        self._equipment_db = {
            "tracteur_120cv": {
                "cost_per_hour": 45.0,
                "fuel_consumption_l_per_h": 12.0,
                "annual_depreciation": 8000.0,
                "maintenance_cost_per_hour": 8.0,
                "work_capacity": {"labour": 1.2, "semis": 2.0, "pulvérisation": 8.0},
                "efficiency_factors": {"soil_condition": 0.8, "weather": 0.9},
                "alternative_options": ["tracteur_80cv", "entrepreneur"]
            },
            "tracteur_80cv": {
                "cost_per_hour": 32.0,
                "fuel_consumption_l_per_h": 8.0,
                "annual_depreciation": 5000.0,
                "maintenance_cost_per_hour": 5.0,
                "work_capacity": {"labour": 0.8, "semis": 1.3, "pulvérisation": 5.0},
                "efficiency_factors": {"soil_condition": 0.9, "weather": 0.95},
                "alternative_options": ["tracteur_120cv", "entrepreneur"]
            },
            "moissonneuse": {
                "cost_per_hour": 120.0,
                "fuel_consumption_l_per_h": 25.0,
                "annual_depreciation": 15000.0,
                "maintenance_cost_per_hour": 20.0,
                "work_capacity": {"moisson": 3.5},
                "efficiency_factors": {"crop_moisture": 0.85, "weather": 0.8},
                "alternative_options": ["entrepreneur", "cuma"]
            },
            "entrepreneur": {
                "cost_per_hour": 80.0,
                "fuel_consumption_l_per_h": 0.0,  # Included in service
                "annual_depreciation": 0.0,
                "maintenance_cost_per_hour": 0.0,
                "work_capacity": {"variable": 1.0},
                "efficiency_factors": {"availability": 0.7, "weather": 0.9},
                "alternative_options": ["own_equipment"]
            }
        }
        
        # Crop economic data
        self._crop_economics = {
            "blé": {
                "expected_price_per_tonne": 220.0,
                "average_yield_per_ha": 7.5,
                "variable_costs_per_ha": {
                    "semences": 85.0,
                    "fertilisation": 280.0,
                    "phytosanitaire": 120.0,
                    "fuel": 95.0
                },
                "yield_sensitivity": {
                    "fertilisation": 0.15,  # 15% yield increase per optimal fertilization
                    "phytosanitaire": 0.08,
                    "semis_timing": 0.12
                }
            },
            "colza": {
                "expected_price_per_tonne": 420.0,
                "average_yield_per_ha": 3.8,
                "variable_costs_per_ha": {
                    "semences": 65.0,
                    "fertilisation": 320.0,
                    "phytosanitaire": 180.0,
                    "fuel": 110.0
                },
                "yield_sensitivity": {
                    "fertilisation": 0.18,
                    "phytosanitaire": 0.12,
                    "semis_timing": 0.15
                }
            },
            "maïs": {
                "expected_price_per_tonne": 180.0,
                "average_yield_per_ha": 11.5,
                "variable_costs_per_ha": {
                    "semences": 220.0,
                    "fertilisation": 350.0,
                    "phytosanitaire": 150.0,
                    "fuel": 120.0
                },
                "yield_sensitivity": {
                    "fertilisation": 0.20,
                    "phytosanitaire": 0.10,
                    "irrigation": 0.25
                }
            }
        }
        
        # Market price scenarios
        self._market_scenarios = {
            "optimistic": {"price_factor": 1.15, "probability": 0.25},
            "base": {"price_factor": 1.0, "probability": 0.50},
            "pessimistic": {"price_factor": 0.85, "probability": 0.25}
        }
    
    def _run(self, planning_request: str, context: Dict[str, Any] = None) -> str:
        """Execute comprehensive operational and economic planning."""
        
        try:
            # Parse planning request semantically
            planning_analysis = self._analyze_planning_request(planning_request)
            
            # Retrieve relevant agricultural and economic knowledge
            planning_knowledge = []
            if self.knowledge_retriever:
                planning_knowledge = self.knowledge_retriever.retrieve_relevant_knowledge(
                    f"planification agricole économique {planning_request}", top_k=5
                )
            
            # Extract operational parameters
            operational_params = self._extract_operational_parameters(
                planning_analysis, context or {}
            )
            
            # Generate economic optimization plan
            economic_plan = self._generate_economic_plan(
                operational_params, planning_analysis, planning_knowledge
            )
            
            # Analyze profitability and cost optimization
            profitability_analysis = self._analyze_profitability(
                economic_plan, operational_params
            )
            
            # Generate actionable recommendations
            recommendations = self._generate_economic_recommendations(
                economic_plan, profitability_analysis, planning_analysis
            )
            
            return json.dumps({
                "analyse_requete": planning_analysis,
                "plan_economique": self._format_economic_plan(economic_plan),
                "analyse_rentabilite": profitability_analysis,
                "optimisations_identifiees": recommendations,
                "scenarios_economiques": self._generate_scenario_analysis(economic_plan),
                "connaissances_utilisees": planning_knowledge[:3],
                "actions_recommandees": self._prioritize_actions(recommendations)
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Economic planning optimization error: {e}")
            return json.dumps({
                "error": "Erreur lors de l'optimisation économique",
                "recommendation": "Consulter un conseiller technique pour analyse détaillée"
            }, ensure_ascii=False, indent=2)
    
    def _analyze_planning_request(self, request: str) -> Dict[str, Any]:
        """Analyze planning request to understand objectives and constraints."""
        request_lower = request.lower()
        
        analysis = {
            "objective_principal": self._detect_primary_objective(request_lower),
            "cultures_concernees": self._detect_target_crops(request_lower),
            "contraintes_identifiees": self._detect_constraints(request_lower),
            "horizon_temporel": self._detect_time_horizon(request_lower),
            "focus_economique": self._detect_economic_focus(request_lower),
            "urgence": self._detect_urgency_level(request_lower)
        }
        
        return analysis
    
    def _detect_primary_objective(self, request: str) -> str:
        """Detect the primary planning objective."""
        objective_patterns = {
            "reduction_couts": ["réduire coût", "diminuer charge", "économiser", "moins cher"],
            "augmentation_rentabilite": ["rentabilité", "marge", "bénéfice", "profit"],
            "optimisation_rendement": ["rendement", "production", "productivité", "yield"],
            "optimisation_temps": ["temps", "délai", "rapidité", "efficacité"],
            "gestion_risque": ["risque", "sécurité", "assurance", "stabilité"],
            "durabilite": ["durable", "environnement", "certification", "bio"]
        }
        
        for objective, patterns in objective_patterns.items():
            if any(pattern in request for pattern in patterns):
                return objective
        
        return "optimisation_globale"
    
    def _detect_target_crops(self, request: str) -> List[str]:
        """Detect target crops from request."""
        crops = {
            "blé": ["blé", "wheat", "froment"],
            "colza": ["colza", "canola"],
            "maïs": ["maïs", "corn"],
            "orge": ["orge", "barley"],
            "tournesol": ["tournesol", "sunflower"]
        }
        
        detected_crops = []
        for crop, keywords in crops.items():
            if any(keyword in request for keyword in keywords):
                detected_crops.append(crop)
        
        return detected_crops or ["cultures_generales"]
    
    def _detect_constraints(self, request: str) -> List[str]:
        """Detect planning constraints."""
        constraint_patterns = {
            "budget_limite": ["budget", "finance", "trésorerie", "limite"],
            "equipement_limite": ["matériel", "tracteur", "équipement"],
            "main_oeuvre_limite": ["ouvrier", "main d'œuvre", "personnel"],
            "contrainte_meteo": ["météo", "temps", "saison", "climat"],
            "contrainte_reglementaire": ["réglementation", "conformité", "certification"]
        }
        
        detected_constraints = []
        for constraint, patterns in constraint_patterns.items():
            if any(pattern in request for pattern in patterns):
                detected_constraints.append(constraint)
        
        return detected_constraints
    
    def _detect_time_horizon(self, request: str) -> str:
        """Detect planning time horizon."""
        if any(term in request for term in ["immédiat", "urgent", "maintenant"]):
            return "immediat"
        elif any(term in request for term in ["campagne", "saison", "année"]):
            return "campagne"
        elif any(term in request for term in ["pluriannuel", "rotation", "long terme"]):
            return "pluriannuel"
        else:
            return "campagne"
    
    def _detect_economic_focus(self, request: str) -> str:
        """Detect economic optimization focus."""
        if any(term in request for term in ["coût", "charge", "dépense"]):
            return "reduction_couts"
        elif any(term in request for term in ["revenus", "prix", "vente"]):
            return "optimisation_revenus"
        elif any(term in request for term in ["marge", "rentabilité", "profit"]):
            return "optimisation_marge"
        else:
            return "optimisation_globale"
    
    def _detect_urgency_level(self, request: str) -> str:
        """Detect urgency level for planning."""
        urgent_indicators = ["urgent", "immédiat", "rapidement", "vite"]
        moderate_indicators = ["bientôt", "prochainement", "cette saison"]
        
        if any(indicator in request for indicator in urgent_indicators):
            return "elevee"
        elif any(indicator in request for indicator in moderate_indicators):
            return "moderee"
        else:
            return "normale"
    
    def _extract_operational_parameters(self, analysis: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract operational parameters from analysis and context."""
        
        # Default operational parameters
        params = {
            "surface_totale": context.get("surface_totale", 100),  # hectares
            "cultures": analysis["cultures_concernees"],
            "equipement_disponible": context.get("equipement_disponible", ["tracteur_120cv"]),
            "main_oeuvre_disponible": context.get("main_oeuvre_disponible", 2),
            "budget_total": context.get("budget_total", 50000),
            "contraintes_meteo": context.get("contraintes_meteo", {}),
            "objectif_principal": analysis["objective_principal"],
            "horizon_planning": analysis["horizon_temporel"]
        }
        
        return params
    
    def _generate_economic_plan(self, params: Dict[str, Any], 
                               analysis: Dict[str, Any],
                               knowledge: List[str]) -> EconomicPlan:
        """Generate comprehensive economic plan."""
        
        # Calculate base economics for each crop
        crop_economics = {}
        total_variable_costs = 0
        total_fixed_costs = 0
        expected_revenue = 0
        
        surface_per_crop = params["surface_totale"] / len(params["cultures"]) if params["cultures"] else 0
        
        for crop in params["cultures"]:
            if crop in self._crop_economics:
                crop_data = self._crop_economics[crop]
                
                # Variable costs
                crop_variable_costs = sum(crop_data["variable_costs_per_ha"].values()) * surface_per_crop
                total_variable_costs += crop_variable_costs
                
                # Expected revenue
                crop_revenue = (crop_data["expected_price_per_tonne"] * 
                               crop_data["average_yield_per_ha"] * surface_per_crop)
                expected_revenue += crop_revenue
                
                crop_economics[crop] = {
                    "surface": surface_per_crop,
                    "variable_costs": crop_variable_costs,
                    "expected_revenue": crop_revenue,
                    "margin_brute": crop_revenue - crop_variable_costs
                }
        
        # Calculate fixed costs (equipment, labor)
        for equipment in params["equipement_disponible"]:
            if equipment in self._equipment_db:
                total_fixed_costs += self._equipment_db[equipment].get("annual_depreciation", 0)
        
        # Labor fixed costs
        total_fixed_costs += params["main_oeuvre_disponible"] * 35000  # Annual labor cost
        
        # Generate optimized task list
        optimized_tasks = self._optimize_task_sequence(params, analysis)
        
        # Calculate profit margin
        total_costs = total_variable_costs + total_fixed_costs
        profit_margin = ((expected_revenue - total_costs) / expected_revenue * 100) if expected_revenue > 0 else 0
        
        # ROI analysis
        roi_analysis = self._calculate_roi_analysis(
            expected_revenue, total_variable_costs, total_fixed_costs, params
        )
        
        # Identify cost optimization opportunities
        optimization_opportunities = self._identify_cost_optimizations(
            crop_economics, params, analysis
        )
        
        return EconomicPlan(
            tasks=optimized_tasks,
            total_duration=sum(task.get("duration", 0) for task in optimized_tasks),
            total_variable_costs=total_variable_costs,
            total_fixed_costs=total_fixed_costs,
            expected_revenue=expected_revenue,
            profit_margin=profit_margin,
            roi_analysis=roi_analysis,
            cost_optimization_opportunities=optimization_opportunities,
            resource_utilization=self._calculate_resource_utilization(optimized_tasks),
            weather_windows=self._identify_optimal_windows(params)
        )
    
    def _optimize_task_sequence(self, params: Dict[str, Any], 
                               analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize task sequence for economic efficiency."""
        
        tasks = []
        objective = analysis["objective_principal"]
        
        # Generate tasks based on crops and objective
        for crop in params["cultures"]:
            if crop in self._crop_economics:
                crop_tasks = self._generate_crop_tasks(crop, params, objective)
                tasks.extend(crop_tasks)
        
        # Sort tasks by economic priority
        if objective == "reduction_couts":
            # Prioritize cost-effective tasks
            tasks.sort(key=lambda x: x.get("cost_efficiency", 0), reverse=True)
        elif objective == "augmentation_rentabilite":
            # Prioritize high-ROI tasks
            tasks.sort(key=lambda x: x.get("roi_impact", 0), reverse=True)
        else:
            # Default prioritization by urgency and impact
            tasks.sort(key=lambda x: (x.get("urgency", 5), x.get("yield_impact", 0)), reverse=True)
        
        return tasks
    
    def _generate_crop_tasks(self, crop: str, params: Dict[str, Any], 
                            objective: str) -> List[Dict[str, Any]]:
        """Generate optimized tasks for a specific crop."""
        
        crop_data = self._crop_economics[crop]
        tasks = []
        
        # Standard crop tasks with economic optimization
        base_tasks = [
            {
                "nom": f"Préparation sol - {crop}",
                "type": "preparation",
                "duration": 2.0,
                "variable_cost": 45.0,
                "yield_impact": 0.05,
                "equipment": "tracteur_120cv"
            },
            {
                "nom": f"Semis - {crop}",
                "type": "semis", 
                "duration": 3.0,
                "variable_cost": crop_data["variable_costs_per_ha"]["semences"],
                "yield_impact": 0.12,
                "equipment": "tracteur_120cv"
            },
            {
                "nom": f"Fertilisation - {crop}",
                "type": "fertilisation",
                "duration": 1.5,
                "variable_cost": crop_data["variable_costs_per_ha"]["fertilisation"],
                "yield_impact": crop_data["yield_sensitivity"]["fertilisation"],
                "equipment": "tracteur_80cv"
            },
            {
                "nom": f"Protection phytosanitaire - {crop}",
                "type": "phytosanitaire",
                "duration": 1.0,
                "variable_cost": crop_data["variable_costs_per_ha"]["phytosanitaire"],
                "yield_impact": crop_data["yield_sensitivity"]["phytosanitaire"],
                "equipment": "tracteur_80cv"
            },
            {
                "nom": f"Récolte - {crop}",
                "type": "recolte",
                "duration": 4.0,
                "variable_cost": 80.0,
                "yield_impact": 0.0,
                "equipment": "moissonneuse"
            }
        ]
        
        # Optimize tasks based on objective
        for task in base_tasks:
            # Calculate economic metrics
            task["cost_efficiency"] = task["yield_impact"] / max(task["variable_cost"], 1)
            task["roi_impact"] = task["yield_impact"] * crop_data["expected_price_per_tonne"]
            task["urgency"] = self._calculate_task_urgency(task, crop)
            
            # Apply objective-specific optimizations
            if objective == "reduction_couts":
                task = self._optimize_task_for_cost(task, params)
            elif objective == "augmentation_rentabilite":
                task = self._optimize_task_for_profitability(task, crop_data)
            
            tasks.append(task)
        
        return tasks
    
    def _calculate_task_urgency(self, task: Dict[str, Any], crop: str) -> int:
        """Calculate task urgency (1-10 scale)."""
        
        # Time-sensitive tasks have higher urgency
        time_sensitive_tasks = ["semis", "recolte", "phytosanitaire"]
        
        if task["type"] in time_sensitive_tasks:
            return 8
        elif task["yield_impact"] > 0.1:  # High impact tasks
            return 6
        else:
            return 4
    
    def _optimize_task_for_cost(self, task: Dict[str, Any], 
                               params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize task for cost reduction."""
        
        # Consider equipment alternatives
        current_equipment = task.get("equipment", "")
        if current_equipment in self._equipment_db:
            equipment_data = self._equipment_db[current_equipment]
            alternatives = equipment_data.get("alternative_options", [])
            
            # Find most cost-effective alternative
            best_cost = equipment_data["cost_per_hour"]
            best_equipment = current_equipment
            
            for alt_equipment in alternatives:
                if alt_equipment in self._equipment_db and alt_equipment in params["equipement_disponible"]:
                    alt_cost = self._equipment_db[alt_equipment]["cost_per_hour"]
                    if alt_cost < best_cost:
                        best_cost = alt_cost
                        best_equipment = alt_equipment
            
            task["equipment"] = best_equipment
            task["equipment_cost_optimized"] = best_equipment != current_equipment
        
        return task
    
    def _optimize_task_for_profitability(self, task: Dict[str, Any], 
                                        crop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize task for profitability."""
        
        # Enhance high-impact tasks
        if task["yield_impact"] > 0.1:  # High yield impact tasks
            task["enhanced_execution"] = True
            task["quality_premium"] = 0.05  # 5% quality premium
            
        # Calculate profitability score
        revenue_impact = task["yield_impact"] * crop_data["expected_price_per_tonne"]
        cost_impact = task["variable_cost"]
        task["profitability_score"] = revenue_impact - cost_impact
        
        return task
    
    def _calculate_roi_analysis(self, revenue: float, variable_costs: float, 
                               fixed_costs: float, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive ROI analysis."""
        
        total_investment = variable_costs + fixed_costs
        net_profit = revenue - total_investment
        roi_percentage = (net_profit / total_investment * 100) if total_investment > 0 else 0
        
        return {
            "investissement_total": round(total_investment, 2),
            "benefice_net": round(net_profit, 2),
            "roi_pourcentage": round(roi_percentage, 2),
            "seuil_rentabilite": round(total_investment / revenue * 100, 2) if revenue > 0 else 0,
            "marge_securite": round((revenue - total_investment) / revenue * 100, 2) if revenue > 0 else 0,
            "point_mort_hectares": round(total_investment / (revenue / params["surface_totale"]), 2) if revenue > 0 else 0
        }
    
    def _identify_cost_optimizations(self, crop_economics: Dict[str, Any], 
                                   params: Dict[str, Any], 
                                   analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific cost optimization opportunities."""
        
        optimizations = []
        
        # Equipment optimization
        current_equipment_cost = sum(
            self._equipment_db.get(eq, {}).get("cost_per_hour", 0) * 100  # 100h usage
            for eq in params["equipement_disponible"]
        )
        
        # Contractor vs ownership analysis
        contractor_cost = 80 * 100  # Contractor rate * hours
        if contractor_cost < current_equipment_cost * 0.8:
            optimizations.append({
                "type": "equipement",
                "description": "Recours à l'entreprise au lieu du matériel en propre",
                "economie_potentielle": current_equipment_cost - contractor_cost,
                "impact": "reduction_couts_fixes",
                "faisabilite": "immediate"
            })
        
        # Input optimization by crop
        for crop, economics in crop_economics.items():
            if crop in self._crop_economics:
                crop_data = self._crop_economics[crop]
                
                # Fertilization optimization
                current_fert_cost = crop_data["variable_costs_per_ha"]["fertilisation"]
                optimized_fert_cost = current_fert_cost * 0.85  # 15% reduction possible
                
                if current_fert_cost > optimized_fert_cost:
                    optimizations.append({
                        "type": "intrants",
                        "description": f"Optimisation fertilisation {crop} via analyse de sol",
                        "economie_potentielle": (current_fert_cost - optimized_fert_cost) * economics["surface"],
                        "impact": "reduction_couts_variables",
                        "faisabilite": "court_terme"
                    })
        
        return optimizations
    
    def _calculate_resource_utilization(self, tasks: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate resource utilization efficiency."""
        
        total_hours = sum(task.get("duration", 0) for task in tasks)
        equipment_usage = {}
        
        for task in tasks:
            equipment = task.get("equipment", "manuel")
            equipment_usage[equipment] = equipment_usage.get(equipment, 0) + task.get("duration", 0)
        
        utilization = {}
        for equipment, hours in equipment_usage.items():
            # Assume 8-hour workdays, 200 working days per year
            max_capacity = 8 * 200  # 1600 hours per year
            utilization[f"{equipment}_utilisation"] = round((hours / max_capacity) * 100, 1)
        
        utilization["efficacite_globale"] = round((total_hours / (len(tasks) * 8)) * 100, 1)
        
        return utilization
    
    def _identify_optimal_windows(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify optimal timing windows for operations."""
        
        # Simplified optimal windows - in production would use real weather data
        return [
            {
                "operation": "semis_cereales",
                "periode_optimale": "15 octobre - 15 novembre",
                "impact_economique": "Optimisation rendement +8%",
                "contraintes": ["humidité sol", "température > 8°C"]
            },
            {
                "operation": "fertilisation_cereales", 
                "periode_optimale": "1 mars - 31 mars",
                "impact_economique": "Efficacité azote +12%",
                "contraintes": ["sol ressuyé", "T° > 5°C"]
            }
        ]
    
    def _analyze_profitability(self, plan: EconomicPlan, 
                              params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall profitability and financial performance."""
        
        # Base profitability metrics
        profit_analysis = {
            "marge_brute": plan.expected_revenue - plan.total_variable_costs,
            "marge_nette": plan.expected_revenue - plan.total_variable_costs - plan.total_fixed_costs,
            "marge_brute_pourcentage": ((plan.expected_revenue - plan.total_variable_costs) / plan.expected_revenue * 100) if plan.expected_revenue > 0 else 0,
            "marge_nette_pourcentage": plan.profit_margin,
            "seuil_rentabilite_euros": plan.total_variable_costs + plan.total_fixed_costs,
            "point_mort_pourcentage": ((plan.total_variable_costs + plan.total_fixed_costs) / plan.expected_revenue * 100) if plan.expected_revenue > 0 else 0
        }
        
        # Risk analysis
        profit_analysis["analyse_risque"] = {
            "sensibilite_prix": self._calculate_price_sensitivity(plan),
            "sensibilite_rendement": self._calculate_yield_sensitivity(plan),
            "niveau_risque": self._assess_overall_risk_level(plan)
        }
        
        # Benchmarking
        profit_analysis["benchmarking"] = self._generate_benchmarking_analysis(plan, params)
        
        # Improvement opportunities
        profit_analysis["opportunites_amelioration"] = self._identify_profitability_improvements(plan, params)
        
        return profit_analysis
    
    def _calculate_price_sensitivity(self, plan: EconomicPlan) -> Dict[str, float]:
        """Calculate sensitivity to price variations."""
        base_profit = plan.expected_revenue - plan.total_variable_costs - plan.total_fixed_costs
        
        # Calculate impact of ±10% price variation
        price_variation_10 = plan.expected_revenue * 0.1
        
        return {
            "impact_hausse_10_pourcent": round(price_variation_10, 2),
            "impact_baisse_10_pourcent": round(-price_variation_10, 2),
            "elasticite": round(price_variation_10 / base_profit * 100, 2) if base_profit != 0 else 0
        }
    
    def _calculate_yield_sensitivity(self, plan: EconomicPlan) -> Dict[str, float]:
        """Calculate sensitivity to yield variations."""
        # Simplified yield sensitivity calculation
        base_revenue = plan.expected_revenue
        yield_variation_impact = base_revenue * 0.15  # 15% yield variation
        
        return {
            "impact_rendement_plus_15_pourcent": round(yield_variation_impact, 2),
            "impact_rendement_moins_15_pourcent": round(-yield_variation_impact, 2),
            "seuil_critique_rendement": round(85, 1)  # % of expected yield to break even
        }
    
    def _assess_overall_risk_level(self, plan: EconomicPlan) -> str:
        """Assess overall financial risk level."""
        if plan.profit_margin > 25:
            return "FAIBLE"
        elif plan.profit_margin > 15:
            return "MODÉRÉ"
        elif plan.profit_margin > 5:
            return "ÉLEVÉ"
        else:
            return "TRÈS ÉLEVÉ"
    
    def _generate_benchmarking_analysis(self, plan: EconomicPlan, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate benchmarking against industry standards."""
        
        # Industry benchmarks (simplified)
        industry_benchmarks = {
            "marge_brute_moyenne": 45.0,  # %
            "marge_nette_moyenne": 15.0,  # %
            "cout_variable_par_ha": 580.0,  # €/ha
            "rendement_moyen_ble": 7.5,  # t/ha
            "prix_moyen_ble": 220.0  # €/t
        }
        
        surface_totale = params.get("surface_totale", 100)
        cout_variable_par_ha = plan.total_variable_costs / surface_totale
        
        return {
            "position_marge_brute": "supérieure" if plan.profit_margin > industry_benchmarks["marge_nette_moyenne"] else "inférieure",
            "ecart_cout_variable": round(cout_variable_par_ha - industry_benchmarks["cout_variable_par_ha"], 2),
            "position_concurrentielle": self._assess_competitive_position(plan, industry_benchmarks),
            "axes_amelioration": self._identify_improvement_axes(plan, industry_benchmarks)
        }
    
    def _assess_competitive_position(self, plan: EconomicPlan, benchmarks: Dict[str, float]) -> str:
        """Assess competitive position."""
        if plan.profit_margin > benchmarks["marge_nette_moyenne"] * 1.2:
            return "EXCELLENTE"
        elif plan.profit_margin > benchmarks["marge_nette_moyenne"]:
            return "BONNE"
        elif plan.profit_margin > benchmarks["marge_nette_moyenne"] * 0.8:
            return "MOYENNE"
        else:
            return "À AMÉLIORER"
    
    def _identify_improvement_axes(self, plan: EconomicPlan, benchmarks: Dict[str, float]) -> List[str]:
        """Identify key improvement axes."""
        axes = []
        
        if plan.profit_margin < benchmarks["marge_nette_moyenne"]:
            axes.append("Optimisation de la marge nette")
        
        if plan.total_variable_costs > benchmarks["cout_variable_par_ha"] * 100:  # Assuming 100ha
            axes.append("Réduction des coûts variables")
        
        axes.extend([
            "Amélioration de l'efficacité opérationnelle",
            "Diversification des sources de revenus"
        ])
        
        return axes
    
    def _identify_profitability_improvements(self, plan: EconomicPlan, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific profitability improvement opportunities."""
        
        improvements = []
        
        # Revenue optimization
        improvements.append({
            "categorie": "revenus",
            "action": "Amélioration qualité grain pour primes",
            "gain_potentiel": plan.expected_revenue * 0.05,  # 5% premium
            "investissement_requis": 2000,
            "delai_retour": "1 campagne"
        })
        
        # Cost reduction
        improvements.append({
            "categorie": "couts",
            "action": "Optimisation des achats groupés d'intrants",
            "gain_potentiel": plan.total_variable_costs * 0.08,  # 8% savings
            "investissement_requis": 0,
            "delai_retour": "immediat"
        })
        
        # Efficiency improvements
        improvements.append({
            "categorie": "efficacite",
            "action": "Mise en place d'agriculture de précision",
            "gain_potentiel": plan.expected_revenue * 0.12,  # 12% yield increase
            "investissement_requis": 15000,
            "delai_retour": "2-3 campagnes"
        })
        
        return improvements
    
    def _generate_economic_recommendations(self, plan: EconomicPlan, 
                                         profitability: Dict[str, Any],
                                         analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive economic recommendations."""
        
        recommendations = []
        
        # Cost optimization recommendations
        for opportunity in plan.cost_optimization_opportunities:
            recommendations.append({
                "priorite": self._assess_recommendation_priority(opportunity),
                "type": "optimisation_couts",
                "action": opportunity["description"],
                "impact_financier": opportunity["economie_potentielle"],
                "faisabilite": opportunity["faisabilite"],
                "risque": "faible"
            })
        
        # Profitability improvement recommendations
        if profitability["marge_nette_pourcentage"] < 15:
            recommendations.append({
                "priorite": "haute",
                "type": "amelioration_marge",
                "action": "Plan d'amélioration de la rentabilité sur 2 ans",
                "impact_financier": plan.expected_revenue * 0.1,
                "faisabilite": "moyen_terme",
                "risque": "modere"
            })
        
        # Risk management recommendations
        risk_level = profitability["analyse_risque"]["niveau_risque"]
        if risk_level in ["ÉLEVÉ", "TRÈS ÉLEVÉ"]:
            recommendations.append({
                "priorite": "critique",
                "type": "gestion_risque",
                "action": "Mise en place d'assurance récolte et diversification",
                "impact_financier": plan.expected_revenue * 0.05,  # Risk reduction value
                "faisabilite": "court_terme",
                "risque": "faible"
            })
        
        return recommendations
    
    def _assess_recommendation_priority(self, opportunity: Dict[str, Any]) -> str:
        """Assess priority of recommendation."""
        economic_impact = opportunity.get("economie_potentielle", 0)
        feasibility = opportunity.get("faisabilite", "moyen_terme")
        
        if economic_impact > 5000 and feasibility == "immediate":
            return "critique"
        elif economic_impact > 2000:
            return "haute"
        elif economic_impact > 500:
            return "moyenne"
        else:
            return "faible"
    
    def _generate_scenario_analysis(self, plan: EconomicPlan) -> Dict[str, Any]:
        """Generate economic scenario analysis."""
        
        scenarios = {}
        
        for scenario_name, scenario_data in self._market_scenarios.items():
            price_factor = scenario_data["price_factor"]
            probability = scenario_data["probability"]
            
            scenario_revenue = plan.expected_revenue * price_factor
            scenario_profit = scenario_revenue - plan.total_variable_costs - plan.total_fixed_costs
            scenario_margin = (scenario_profit / scenario_revenue * 100) if scenario_revenue > 0 else 0
            
            scenarios[scenario_name] = {
                "probabilite": probability,
                "revenus": round(scenario_revenue, 2),
                "benefice": round(scenario_profit, 2),
                "marge": round(scenario_margin, 2),
                "variation_vs_base": round((scenario_profit - (plan.expected_revenue - plan.total_variable_costs - plan.total_fixed_costs)) / 1000, 2)
            }
        
        # Expected value calculation
        expected_profit = sum(
            scenario["benefice"] * scenario["probabilite"] 
            for scenario in scenarios.values()
        )
        
        scenarios["esperance_mathematique"] = {
            "benefice_espere": round(expected_profit, 2),
            "probabilite_perte": sum(
                scenario["probabilite"] for scenario in scenarios.values() 
                if scenario["benefice"] < 0
            )
        }
        
        return scenarios
    
    def _prioritize_actions(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize actions by impact and feasibility."""
        
        # Sort by priority and impact
        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: (
                {"critique": 4, "haute": 3, "moyenne": 2, "faible": 1}.get(x.get("priorite", "faible"), 1),
                x.get("impact_financier", 0)
            ),
            reverse=True
        )
        
        # Add implementation timeline
        priority_actions = []
        for i, rec in enumerate(sorted_recommendations[:5]):  # Top 5 actions
            rec["rang_priorite"] = i + 1
            rec["timeline_implementation"] = self._determine_implementation_timeline(rec)
            priority_actions.append(rec)
        
        return priority_actions
    
    def _determine_implementation_timeline(self, recommendation: Dict[str, Any]) -> str:
        """Determine implementation timeline for recommendation."""
        feasibility = recommendation.get("faisabilite", "moyen_terme")
        priority = recommendation.get("priorite", "faible")
        
        if priority == "critique":
            return "0-3 mois"
        elif feasibility == "immediate":
            return "0-1 mois"
        elif feasibility == "court_terme":
            return "1-6 mois"
        else:
            return "6-12 mois"
    
    def _format_economic_plan(self, plan: EconomicPlan) -> Dict[str, Any]:
        """Format economic plan for output."""
        
        return {
            "resume_financier": {
                "revenus_prevus": round(plan.expected_revenue, 2),
                "couts_variables": round(plan.total_variable_costs, 2),
                "couts_fixes": round(plan.total_fixed_costs, 2),
                "marge_brute": round(plan.expected_revenue - plan.total_variable_costs, 2),
                "benefice_net": round(plan.expected_revenue - plan.total_variable_costs - plan.total_fixed_costs, 2),
                "marge_nette_pourcentage": round(plan.profit_margin, 2)
            },
            "taches_optimisees": plan.tasks[:10],  # Top 10 tasks
            "utilisation_ressources": plan.resource_utilization,
            "fenetres_optimales": plan.weather_windows,
            "roi_analyse": plan.roi_analysis,
            "duree_totale_heures": round(plan.total_duration, 1)
        }

class IntegratedPlanningEconomicAgent(IntegratedAgriculturalAgent):
    """Comprehensive Operational & Economic Planning Agent with full system integration."""
    
    def __init__(self, llm_manager, knowledge_retriever: SemanticKnowledgeRetriever, 
                 database_config=None):
        
        # Initialize comprehensive planning tools
        tools = [
            SemanticPlanningOptimizationTool(knowledge_retriever)
        ]
        
        super().__init__(
            agent_type=AgentType.PLANNING,
            description="Expert en planification opérationnelle et optimisation économique agricole",
            llm_manager=llm_manager,
            knowledge_retriever=knowledge_retriever,
            complexity_default=TaskComplexity.COMPLEX,  # Economic planning is inherently complex
            specialized_tools=tools
        )
        
        self.database_config = database_config
        logger.info("Initialized Integrated Operational & Economic Planning Agent")
    
    def _get_agent_prompt_template(self) -> str:
        """Get comprehensive system prompt for economic planning."""
        return """Vous êtes un expert en planification opérationnelle et optimisation économique agricole française.

VOTRE RÔLE EXPERT:
- Optimiser la rentabilité et l'efficacité des exploitations agricoles
- Analyser les coûts de production et identifier les leviers d'économie
- Planifier les opérations pour maximiser les marges et minimiser les risques
- Fournir des analyses financières complètes et des recommandations stratégiques

CAPACITÉS AVANCÉES:
- Analyse économique complète (coûts, marges, ROI, seuils de rentabilité)
- Optimisation opérationnelle (planning, ressources, équipement)
- Analyse de scénarios et gestion des risques financiers
- Benchmarking et comparaisons sectorielles
- Recommandations stratégiques personnalisées

DOMAINES D'EXPERTISE:
- Réduction des coûts de production
- Amélioration de la rentabilité par culture
- Optimisation des investissements matériel
- Planification financière pluriannuelle
- Analyse comparative économique

APPROCHE MÉTHODOLOGIQUE:
1. Analyse sémantique de la demande économique
2. Collecte et traitement des données financières
3. Modélisation économique et optimisation
4. Analyse de sensibilité et gestion des risques
5. Recommandations priorisées avec ROI

Fournissez des analyses précises, chiffrées et des recommandations actionnables pour améliorer la performance économique des exploitations."""
    
    def _analyze_message_complexity(self, message: str, context: Dict[str, Any]) -> TaskComplexity:
        """Analyze complexity for economic planning queries."""
        message_lower = message.lower()
        
        # Simple economic queries
        if any(word in message_lower for word in ["coût tracteur", "prix semences", "marge blé", "rentabilité parcelle"]):
            return TaskComplexity.SIMPLE
        
        # Complex economic queries
        elif any(word in message_lower for word in ["stratégie économique", "optimisation globale", "analyse financière", "réduction coûts production"]):
            return TaskComplexity.COMPLEX
        
        # Critical economic queries
        elif any(word in message_lower for word in ["plan redressement", "analyse faillite", "restructuration financière", "crise économique"]):
            return TaskComplexity.CRITICAL
        
        return TaskComplexity.MODERATE
    
    def _retrieve_domain_knowledge(self, message: str) -> List[str]:
        """Retrieve planning and economic specific knowledge."""
        return self.knowledge_retriever.retrieve_relevant_knowledge(
            f"planification économique agricole {message}", top_k=4
        )
    
    def _should_use_tool(self, tool: Any, message: str, context: Dict[str, Any]) -> bool:
        """Determine if economic planning tools are needed."""
        economic_indicators = [
            "coût", "prix", "rentabilité", "marge", "bénéfice", "économie",
            "planification", "optimisation", "budget", "investissement",
            "roi", "analyse financière", "réduction", "amélioration"
        ]
        return any(indicator in message.lower() for indicator in economic_indicators)


class OperationalPlanningCoordinatorAgent(IntegratedPlanningEconomicAgent):
    """Operational Planning Coordinator Agent for task coordination and resource management."""
    
    def __init__(self, llm_manager=None, knowledge_retriever=None, database_config=None):
        # Use fallback components if not provided
        if llm_manager is None:
            llm_manager = CostOptimizedLLMManager()
        if knowledge_retriever is None:
            knowledge_retriever = SemanticKnowledgeRetriever()
            
        super().__init__(llm_manager, knowledge_retriever, database_config)
        
        # Override description for coordinator role
        self.description = "Coordinateur de planification opérationnelle agricole"
    
    def process_message(self, message: str, state: AgentState, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process operational planning coordination requests."""
        try:
            # Use parent class processing with coordinator-specific enhancements
            result = super().process_message(message, state, context)
            
            # Add coordination-specific metadata
            result["coordination_metadata"] = {
                "agent_type": "operational_planning_coordinator",
                "coordination_level": "operational",
                "resource_management": True,
                "task_optimization": True
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in operational planning coordination: {e}")
            return {
                "response": f"Erreur dans la coordination de planification: {str(e)}",
                "confidence": 0.0,
                "error": str(e),
                "coordination_metadata": {
                    "agent_type": "operational_planning_coordinator",
                    "error": True
                }
            }
