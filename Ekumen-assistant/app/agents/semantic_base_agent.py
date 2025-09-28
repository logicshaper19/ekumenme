"""
Semantic Base Agent with Intelligent Tool Selection
Enhanced base agent that uses semantic tool selection for intelligent tool orchestration.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain.schema import BaseMessage, HumanMessage, AIMessage

from .base_agent import IntegratedAgriculturalAgent, AgentState
from ..services.semantic_tool_selector import SemanticToolSelector, ToolSelectionResult

logger = logging.getLogger(__name__)

class SemanticAgriculturalAgent(IntegratedAgriculturalAgent):
    """
    Enhanced agricultural agent with semantic tool selection capabilities.
    
    This agent automatically selects the most appropriate tools based on:
    - Semantic similarity between user message and tool capabilities
    - Intent classification and tool mapping
    - Keyword-based matching with scoring
    - Hybrid approach combining all methods
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        tools: List[BaseTool],
        tool_selection_method: str = "hybrid",
        tool_selection_threshold: float = 0.6,
        max_tools_per_request: int = 3,
        **kwargs
    ):
        """
        Initialize semantic agricultural agent.
        
        Args:
            name: Agent name
            description: Agent description
            tools: List of available tools
            tool_selection_method: Method for tool selection ("semantic", "keyword", "intent", "hybrid")
            tool_selection_threshold: Minimum score threshold for tool selection
            max_tools_per_request: Maximum number of tools to use per request
        """
        super().__init__(
            name=name,
            description=description,
            system_prompt="",  # Will be set dynamically
            tools=tools,
            **kwargs
        )
        
        # Initialize semantic tool selector
        self.tool_selector = SemanticToolSelector()
        self.tool_selection_method = tool_selection_method
        self.tool_selection_threshold = tool_selection_threshold
        self.max_tools_per_request = max_tools_per_request
        
        # Register all tools with the semantic selector
        self._register_tools_with_selector()
        
        logger.info(f"Initialized Semantic Agricultural Agent: {name}")
    
    def _register_tools_with_selector(self):
        """Register all agent tools with the semantic tool selector."""
        for tool in self.tools:
            # Determine domain based on tool name
            domain = self._determine_tool_domain(tool.name)
            complexity = self._determine_tool_complexity(tool.name)
            
            # Add tool profile if not already exists
            if tool.name not in self.tool_selector.tool_profiles:
                self.tool_selector.add_tool_profile(tool, domain, complexity)
    
    def _determine_tool_domain(self, tool_name: str) -> str:
        """Determine tool domain based on tool name."""
        domain_mapping = {
            "diagnose_disease": "crop_health",
            "identify_pest": "crop_health",
            "nutrient_deficiency": "crop_health",
            "treatment_recommendation": "crop_health",
            "generate_planning_tasks": "planning",
            "optimize_task_sequence": "planning",
            "check_regulatory_compliance": "regulatory",
            "database_integrated_amm_lookup": "regulatory",
            "get_weather_data": "weather",
            "get_farm_data": "farm_data",
            "carbon_footprint": "sustainability",
            "biodiversity_assessment": "sustainability"
        }
        
        for key, domain in domain_mapping.items():
            if key in tool_name:
                return domain
        
        return "general"
    
    def _determine_tool_complexity(self, tool_name: str) -> str:
        """Determine tool complexity based on tool name."""
        high_complexity_tools = [
            "generate_planning_tasks", "optimize_task_sequence", 
            "carbon_footprint", "biodiversity_assessment"
        ]
        
        medium_complexity_tools = [
            "diagnose_disease", "identify_pest", "check_regulatory_compliance"
        ]
        
        for tool in high_complexity_tools:
            if tool in tool_name:
                return "high"
        
        for tool in medium_complexity_tools:
            if tool in tool_name:
                return "medium"
        
        return "low"
    
    def process_message(
        self, 
        message: str, 
        state: AgentState,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a user message with semantic tool selection.
        
        Args:
            message: User message
            state: Agent state
            context: Additional context
            
        Returns:
            Dictionary with agent response and tool execution results
        """
        try:
            # Update context with state information
            if not context:
                context = {}
            
            context.update({
                'user_id': state.user_id,
                'farm_id': state.farm_id,
                'current_agent': self.name
            })
            
            # Select tools using semantic selection
            tool_selection_result = self._select_tools_semantically(message)
            
            # Execute selected tools
            tool_results = []
            if tool_selection_result.selected_tools:
                tool_results = self._execute_selected_tools(
                    tool_selection_result.selected_tools, 
                    message, 
                    context
                )
            
            # Generate response using tool results
            response = self._generate_enhanced_response(
                message, 
                context, 
                tool_results, 
                tool_selection_result
            )
            
            return {
                "response": response,
                "tool_selection": {
                    "selected_tools": tool_selection_result.selected_tools,
                    "selection_method": tool_selection_result.selection_method,
                    "confidence": tool_selection_result.confidence,
                    "reasoning": tool_selection_result.reasoning,
                    "tool_scores": tool_selection_result.tool_scores
                },
                "tool_results": tool_results,
                "agent_name": self.name,
                "processing_metadata": {
                    "message_length": len(message),
                    "tools_executed": len(tool_results),
                    "context_keys": list(context.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message in {self.name}: {e}")
            return {
                "response": f"Désolé, une erreur s'est produite lors du traitement de votre demande: {str(e)}",
                "error": str(e),
                "agent_name": self.name
            }
    
    def _select_tools_semantically(self, message: str) -> ToolSelectionResult:
        """Select tools using semantic tool selector."""
        available_tool_names = [tool.name for tool in self.tools]
        
        return self.tool_selector.select_tools(
            message=message,
            available_tools=available_tool_names,
            method=self.tool_selection_method,
            threshold=self.tool_selection_threshold,
            max_tools=self.max_tools_per_request
        )
    
    def _execute_selected_tools(
        self, 
        selected_tools: List[str], 
        message: str, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute the selected tools with extracted parameters."""
        tool_results = []
        
        for tool_name in selected_tools:
            try:
                # Find the tool
                tool = self._find_tool_by_name(tool_name)
                if not tool:
                    logger.warning(f"Tool not found: {tool_name}")
                    continue
                
                # Extract parameters for the tool
                parameters = self._extract_tool_parameters(tool, message, context)
                
                # Execute the tool
                result = self._execute_tool_with_parameters(tool, parameters)
                
                tool_results.append({
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "result": result,
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                tool_results.append({
                    "tool_name": tool_name,
                    "error": str(e),
                    "success": False
                })
        
        return tool_results
    
    def _find_tool_by_name(self, tool_name: str) -> Optional[BaseTool]:
        """Find tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def _extract_tool_parameters(
        self, 
        tool: BaseTool, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract parameters for a specific tool from message and context."""
        # Get tool profile for parameter hints
        profile = self.tool_selector.get_tool_profile(tool.name)
        
        # Basic parameter extraction based on tool type
        parameters = {}
        
        # Common parameters
        parameters.update(self._extract_common_parameters(message, context))
        
        # Tool-specific parameter extraction
        if "disease" in tool.name:
            parameters.update(self._extract_disease_parameters(message, context))
        elif "pest" in tool.name:
            parameters.update(self._extract_pest_parameters(message, context))
        elif "planning" in tool.name:
            parameters.update(self._extract_planning_parameters(message, context))
        elif "compliance" in tool.name or "amm" in tool.name:
            parameters.update(self._extract_regulatory_parameters(message, context))
        elif "weather" in tool.name:
            parameters.update(self._extract_weather_parameters(message, context))
        elif "farm" in tool.name:
            parameters.update(self._extract_farm_parameters(message, context))
        
        return parameters
    
    def _extract_common_parameters(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract common parameters used by multiple tools."""
        parameters = {}
        
        # Extract crop type
        crop_types = ["blé", "orge", "maïs", "colza", "tournesol", "triticale", "avoine", "seigle"]
        message_lower = message.lower()
        
        for crop in crop_types:
            if crop in message_lower:
                parameters["crop_type"] = crop
                break
        
        # Extract location from context or message
        if "location" in context:
            parameters["location"] = context["location"]
        elif "farm_id" in context:
            parameters["location"] = f"Farm_{context['farm_id']}"
        else:
            parameters["location"] = "France"
        
        return parameters
    
    def _extract_disease_parameters(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for disease diagnosis tools."""
        parameters = {}
        
        # Extract symptoms
        symptom_keywords = [
            "taches", "jaunissement", "brunissement", "pourriture", "flétrissement",
            "décoloration", "nécrose", "chancre", "pustules", "moisissure"
        ]
        
        symptoms = []
        message_lower = message.lower()
        for symptom in symptom_keywords:
            if symptom in message_lower:
                symptoms.append(symptom)
        
        if symptoms:
            parameters["symptoms"] = symptoms
        
        # Extract environmental conditions
        environmental_conditions = {}
        if "humide" in message_lower or "humidité" in message_lower:
            environmental_conditions["humidity"] = "high"
        if "sec" in message_lower or "sécheresse" in message_lower:
            environmental_conditions["humidity"] = "low"
        if "chaud" in message_lower or "chaleur" in message_lower:
            environmental_conditions["temperature"] = "high"
        if "froid" in message_lower:
            environmental_conditions["temperature"] = "low"
        
        if environmental_conditions:
            parameters["environmental_conditions"] = environmental_conditions
        
        return parameters

    def _extract_pest_parameters(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for pest identification tools."""
        parameters = {}

        # Extract damage patterns
        damage_keywords = [
            "trous", "galeries", "morsures", "défoliation", "miellat",
            "excréments", "toiles", "perforations", "découpage"
        ]

        damage_patterns = []
        message_lower = message.lower()
        for damage in damage_keywords:
            if damage in message_lower:
                damage_patterns.append(damage)

        if damage_patterns:
            parameters["damage_patterns"] = damage_patterns

        # Extract pest indicators
        pest_indicators = []
        pest_keywords = [
            "insecte", "puceron", "chenille", "coléoptère", "papillon",
            "larve", "œuf", "adulte", "vol", "essaim"
        ]

        for indicator in pest_keywords:
            if indicator in message_lower:
                pest_indicators.append(indicator)

        if pest_indicators:
            parameters["pest_indicators"] = pest_indicators

        return parameters

    def _extract_planning_parameters(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for planning tools."""
        parameters = {}

        # Extract planning objective
        if "coût" in message.lower() or "économie" in message.lower():
            parameters["planning_objective"] = "reduction_couts"
        elif "rentabilité" in message.lower() or "profit" in message.lower():
            parameters["planning_objective"] = "augmentation_rentabilite"
        elif "rendement" in message.lower() or "production" in message.lower():
            parameters["planning_objective"] = "optimisation_rendement"
        else:
            parameters["planning_objective"] = "equilibre_general"

        # Extract surface area
        import re
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ha|hectare)', message.lower())
        if surface_match:
            parameters["surface"] = float(surface_match.group(1))

        # Extract crops from context or message
        if "crops" in context:
            parameters["crops"] = context["crops"]

        return parameters

    def _extract_regulatory_parameters(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for regulatory compliance tools."""
        parameters = {}

        # Extract product information
        import re

        # Look for AMM numbers
        amm_match = re.search(r'amm\s*:?\s*(\d+)', message.lower())
        if amm_match:
            parameters["amm_number"] = amm_match.group(1)

        # Extract product names (common phytosanitary products)
        product_keywords = [
            "glyphosate", "2,4-d", "dicamba", "atrazine", "metribuzine",
            "chlorothalonil", "mancozèbe", "cuivre", "soufre"
        ]

        for product in product_keywords:
            if product in message.lower():
                parameters["product_name"] = product
                break

        # Extract practice type
        practice_keywords = {
            "pulvérisation": "spraying",
            "fertilisation": "fertilization",
            "irrigation": "irrigation",
            "récolte": "harvesting",
            "semis": "seeding"
        }

        for keyword, practice in practice_keywords.items():
            if keyword in message.lower():
                parameters["practice_type"] = practice
                break

        return parameters

    def _extract_weather_parameters(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for weather tools."""
        parameters = {}

        # Extract date range
        import re
        from datetime import datetime, timedelta

        # Look for specific dates
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                day, month, year = match.groups()
                parameters["start_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                break

        # Look for relative dates
        if "demain" in message.lower():
            tomorrow = datetime.now() + timedelta(days=1)
            parameters["start_date"] = tomorrow.strftime("%Y-%m-%d")
        elif "semaine" in message.lower():
            parameters["date_range"] = "7_days"
        elif "mois" in message.lower():
            parameters["date_range"] = "30_days"

        # Extract weather type
        weather_types = {
            "température": "temperature",
            "pluie": "precipitation",
            "vent": "wind",
            "humidité": "humidity",
            "pression": "pressure"
        }

        for keyword, weather_type in weather_types.items():
            if keyword in message.lower():
                parameters["weather_type"] = weather_type
                break

        return parameters

    def _extract_farm_parameters(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for farm data tools."""
        parameters = {}

        # Extract data type
        data_types = {
            "parcelle": "parcel_data",
            "surface": "area_data",
            "sol": "soil_data",
            "culture": "crop_data",
            "rendement": "yield_data",
            "historique": "historical_data"
        }

        for keyword, data_type in data_types.items():
            if keyword in message.lower():
                parameters["data_type"] = data_type
                break

        # Extract parcel ID if mentioned
        import re
        parcel_match = re.search(r'parcelle\s*:?\s*(\w+)', message.lower())
        if parcel_match:
            parameters["parcel_id"] = parcel_match.group(1)

        return parameters

    def _execute_tool_with_parameters(self, tool: BaseTool, parameters: Dict[str, Any]) -> str:
        """Execute tool with extracted parameters."""
        try:
            # Get tool's expected parameters from its _run method signature
            import inspect
            sig = inspect.signature(tool._run)
            expected_params = list(sig.parameters.keys())

            # Filter parameters to match tool's expected parameters
            filtered_params = {}
            for param in expected_params:
                if param in parameters:
                    filtered_params[param] = parameters[param]
                elif param == "crop_type" and "crop_type" not in parameters:
                    filtered_params[param] = "blé"  # Default crop
                elif param == "location" and "location" not in parameters:
                    filtered_params[param] = "France"  # Default location
                elif param == "symptoms" and "symptoms" not in parameters:
                    filtered_params[param] = "symptômes non spécifiés"
                elif param == "damage_patterns" and "damage_patterns" not in parameters:
                    filtered_params[param] = ["dégâts observés"]

            # Execute tool with filtered parameters
            return tool._run(**filtered_params)

        except Exception as e:
            logger.error(f"Error executing tool {tool.name} with parameters {parameters}: {e}")
            return f"Erreur lors de l'exécution de l'outil {tool.name}: {str(e)}"

    def _generate_enhanced_response(
        self,
        message: str,
        context: Dict[str, Any],
        tool_results: List[Dict[str, Any]],
        tool_selection_result: ToolSelectionResult
    ) -> str:
        """Generate enhanced response with tool results and selection reasoning."""

        # Start with tool selection information
        response_parts = []

        if tool_selection_result.selected_tools:
            response_parts.append(
                f"🔧 **Outils sélectionnés** ({tool_selection_result.selection_method}): "
                f"{', '.join(tool_selection_result.selected_tools)}"
            )
            response_parts.append(f"📊 **Confiance**: {tool_selection_result.confidence:.2f}")
            response_parts.append("")

        # Add tool results
        for tool_result in tool_results:
            if tool_result.get("success", False):
                response_parts.append(f"### 🛠️ {tool_result['tool_name']}")
                response_parts.append(tool_result["result"])
                response_parts.append("")
            else:
                response_parts.append(f"⚠️ **Erreur avec {tool_result['tool_name']}**: {tool_result.get('error', 'Erreur inconnue')}")
                response_parts.append("")

        # Add reasoning if available
        if tool_selection_result.reasoning:
            response_parts.append(f"💡 **Raisonnement**: {tool_selection_result.reasoning}")

        # Add alternatives if available
        if tool_selection_result.alternative_tools:
            alternatives = [f"{tool} ({score:.2f})" for tool, score in tool_selection_result.alternative_tools[:2]]
            response_parts.append(f"🔄 **Alternatives**: {', '.join(alternatives)}")

        return "\n".join(response_parts)

    def update_tool_selection_settings(
        self,
        method: Optional[str] = None,
        threshold: Optional[float] = None,
        max_tools: Optional[int] = None
    ):
        """Update tool selection settings dynamically."""
        if method:
            self.tool_selection_method = method
        if threshold is not None:
            self.tool_selection_threshold = threshold
        if max_tools is not None:
            self.max_tools_per_request = max_tools

        logger.info(f"Updated tool selection settings for {self.name}: "
                   f"method={self.tool_selection_method}, "
                   f"threshold={self.tool_selection_threshold}, "
                   f"max_tools={self.max_tools_per_request}")

    def get_tool_selection_stats(self) -> Dict[str, Any]:
        """Get statistics about tool selection and usage."""
        return {
            "total_tools": len(self.tools),
            "tool_names": [tool.name for tool in self.tools],
            "selection_method": self.tool_selection_method,
            "selection_threshold": self.tool_selection_threshold,
            "max_tools_per_request": self.max_tools_per_request,
            "available_domains": list(set(
                self.tool_selector.get_tool_profile(tool.name).domain
                for tool in self.tools
                if self.tool_selector.get_tool_profile(tool.name)
            ))
        }
