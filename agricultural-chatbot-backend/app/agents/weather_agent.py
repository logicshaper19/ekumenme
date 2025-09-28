"""
Weather Intelligence Agent - Specialized in agricultural weather analysis.
"""

from typing import Dict, List, Any, Optional, Union
from langchain.tools import BaseTool
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from .base_agent import IntegratedAgriculturalAgent, AgentState
from ..utils.prompts import FrenchAgriculturalPrompts
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class WeatherCondition:
    date: str
    temperature_min: float
    temperature_max: float
    humidity: float
    wind_speed: float
    wind_direction: str
    precipitation: float
    cloud_cover: float
    uv_index: float

@dataclass
class WeatherRisk:
    risk_type: str
    severity: str
    probability: float
    impact: str
    recommendations: List[str]

class EnhancedWeatherForecastTool(BaseTool):
    """Enhanced weather forecast tool with agricultural focus."""
    
    name: str = "enhanced_weather_forecast"
    description: str = "Prévisions météorologiques agricoles avec analyse des risques"
    
    def __init__(self, weather_api_config=None, **kwargs):
        super().__init__(**kwargs)
        self._weather_api_config = weather_api_config
        self._has_api_access = bool(weather_api_config)
        
        # Mock weather data - in production, connect to real weather APIs
        self._mock_forecast_data = {
            "2024-03-22": {
                "temperature_min": 8.5,
                "temperature_max": 18.2,
                "humidity": 72,
                "wind_speed": 12,
                "wind_direction": "SO",
                "precipitation": 0,
                "cloud_cover": 30,
                "uv_index": 4
            },
            "2024-03-23": {
                "temperature_min": 6.8,
                "temperature_max": 16.5,
                "humidity": 85,
                "wind_speed": 8,
                "wind_direction": "O",
                "precipitation": 5.2,
                "cloud_cover": 80,
                "uv_index": 2
            }
        }
    
    def _run(self, location: str, days: int = 7, crop_type: str = None) -> str:
        """Get enhanced weather forecast with agricultural analysis."""
        
        try:
            if not self._has_api_access:
                # Use mock data
                forecast_data = self._get_mock_forecast(location, days)
            else:
                # In production, call real weather API
                forecast_data = self._get_api_forecast(location, days)
            
            # Analyze weather risks for agriculture
            weather_risks = self._analyze_agricultural_risks(forecast_data, crop_type)
            
            # Generate intervention windows
            intervention_windows = self._identify_intervention_windows(forecast_data)
            
            # Calculate evapotranspiration
            etp_data = self._calculate_evapotranspiration(forecast_data, crop_type)
            
            response = {
                "localisation": location,
                "periode": f"{days} jours",
                "previsions": forecast_data,
                "risques_agricoles": [self._risk_to_dict(risk) for risk in weather_risks],
                "fenetres_intervention": intervention_windows,
                "evapotranspiration": etp_data,
                "recommandations": self._generate_weather_recommendations(weather_risks, crop_type),
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Weather forecast error: {e}")
            return json.dumps({"error": "Erreur lors de la récupération des prévisions météo"})
    
    def _get_mock_forecast(self, location: str, days: int) -> List[Dict[str, Any]]:
        """Get mock weather forecast data."""
        forecast = []
        current_date = datetime.now()
        
        for i in range(days):
            date_str = (current_date + timedelta(days=i)).strftime("%Y-%m-%d")
            if date_str in self._mock_forecast_data:
                day_data = self._mock_forecast_data[date_str].copy()
                day_data["date"] = date_str
                forecast.append(day_data)
            else:
                # Generate default data
                forecast.append({
                    "date": date_str,
                    "temperature_min": 10.0,
                    "temperature_max": 20.0,
                    "humidity": 70,
                    "wind_speed": 10,
                    "wind_direction": "N",
                    "precipitation": 0,
                    "cloud_cover": 50,
                    "uv_index": 3
                })
        
        return forecast
    
    def _get_api_forecast(self, location: str, days: int) -> List[Dict[str, Any]]:
        """Get weather forecast from real API (placeholder)."""
        # In production, integrate with Météo-France API or OpenWeatherMap
        return self._get_mock_forecast(location, days)
    
    def _analyze_agricultural_risks(self, forecast_data: List[Dict[str, Any]], crop_type: str = None) -> List[WeatherRisk]:
        """Analyze weather risks for agricultural activities."""
        risks = []
        
        for day in forecast_data:
            # Frost risk
            if day["temperature_min"] < 2:
                risks.append(WeatherRisk(
                    risk_type="gel",
                    severity="élevée" if day["temperature_min"] < -2 else "modérée",
                    probability=0.9,
                    impact="Dégâts sur cultures sensibles",
                    recommendations=["Protéger les cultures sensibles", "Surveiller les températures"]
                ))
            
            # Wind risk for spraying
            if day["wind_speed"] > 15:
                risks.append(WeatherRisk(
                    risk_type="vent",
                    severity="élevée" if day["wind_speed"] > 25 else "modérée",
                    probability=0.8,
                    impact="Dérive des produits phytosanitaires",
                    recommendations=["Éviter les pulvérisations", "Utiliser des buses anti-dérive"]
                ))
            
            # Heavy rain risk
            if day["precipitation"] > 10:
                risks.append(WeatherRisk(
                    risk_type="pluie",
                    severity="élevée" if day["precipitation"] > 20 else "modérée",
                    probability=0.7,
                    impact="Lessivage des sols, difficultés d'accès",
                    recommendations=["Éviter les travaux de sol", "Vérifier le drainage"]
                ))
        
        return risks
    
    def _identify_intervention_windows(self, forecast_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify optimal windows for agricultural interventions."""
        windows = []
        
        for day in forecast_data:
            # Good conditions for spraying
            if (day["wind_speed"] < 10 and 
                day["precipitation"] < 2 and 
                day["humidity"] < 80):
                windows.append({
                    "date": day["date"],
                    "type_intervention": "pulvérisation",
                    "conditions": "optimales",
                    "vent": f"{day['wind_speed']} km/h",
                    "precipitations": f"{day['precipitation']} mm",
                    "humidite": f"{day['humidity']}%"
                })
            
            # Good conditions for field work
            if (day["precipitation"] < 1 and 
                day["temperature_min"] > 5):
                windows.append({
                    "date": day["date"],
                    "type_intervention": "travaux_champ",
                    "conditions": "bonnes",
                    "precipitations": f"{day['precipitation']} mm",
                    "temperature_min": f"{day['temperature_min']}°C"
                })
        
        return windows
    
    def _calculate_evapotranspiration(self, forecast_data: List[Dict[str, Any]], crop_type: str = None) -> Dict[str, Any]:
        """Calculate evapotranspiration for crop water needs."""
        # Simplified ETP calculation - in production would use Penman-Monteith
        total_etp = 0
        daily_etp = []
        
        for day in forecast_data:
            # Simplified ETP calculation
            etp = (day["temperature_max"] + day["temperature_min"]) / 2 * 0.1
            if day["humidity"] < 60:
                etp *= 1.2  # Higher ETP in dry conditions
            
            total_etp += etp
            daily_etp.append({
                "date": day["date"],
                "etp_mm": round(etp, 1)
            })
        
        return {
            "etp_totale_mm": round(total_etp, 1),
            "etp_quotidienne": daily_etp,
            "besoins_irrigation": "Élevés" if total_etp > 5 else "Modérés" if total_etp > 3 else "Faibles"
        }
    
    def _generate_weather_recommendations(self, risks: List[WeatherRisk], crop_type: str = None) -> List[str]:
        """Generate weather-based recommendations."""
        recommendations = []
        
        if any(risk.risk_type == "gel" for risk in risks):
            recommendations.append("⚠️ Risque de gel - Protéger les cultures sensibles")
        
        if any(risk.risk_type == "vent" for risk in risks):
            recommendations.append("⚠️ Vent fort - Éviter les pulvérisations")
        
        if any(risk.risk_type == "pluie" for risk in risks):
            recommendations.append("⚠️ Pluie importante - Reporter les travaux de sol")
        
        if not risks:
            recommendations.append("✅ Conditions météo favorables pour les travaux agricoles")
        
        return recommendations
    
    def _risk_to_dict(self, risk: WeatherRisk) -> Dict[str, Any]:
        """Convert WeatherRisk to dictionary for JSON serialization."""
        return {
            "type_risque": risk.risk_type,
            "gravite": risk.severity,
            "probabilite": risk.probability,
            "impact": risk.impact,
            "recommandations": risk.recommendations
        }
    
    async def _arun(self, location: str, days: int = 7, crop_type: str = None) -> str:
        """Async version of weather forecast."""
        return self._run(location, days, crop_type)




class WeatherIntelligenceAgent(IntegratedAgriculturalAgent):
    """
    Enhanced Weather Intelligence Agent with real weather analysis capabilities.
    """
    
    def __init__(self, weather_api_config=None, **kwargs):
        self.weather_api_config = weather_api_config
        
        # Initialize enhanced tools
        tools = [
            EnhancedWeatherForecastTool(weather_api_config),
        ]
        
        super().__init__(
            name="weather_intelligence",
            description="Expert météorologique agricole français",
            system_prompt="",  # Will be set dynamically
            tools=tools,
            **kwargs
        )
        
        logger.info("Initialized Enhanced Weather Intelligence Agent")
    
    def get_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Get the system prompt for Weather Intelligence."""
        return FrenchAgriculturalPrompts.get_weather_intelligence_prompt(context)
    
    def process_message(
        self, 
        message: str, 
        state: AgentState,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Enhanced message processing with tool orchestration.
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
            
            # Determine if weather tools are needed
            tools_needed = self._analyze_message_for_tools(message)
            tool_results = []
            
            # Execute relevant tools
            for tool_name in tools_needed:
                tool_result = self._execute_tool(tool_name, message, context)
                if tool_result:
                    tool_results.append(tool_result)
            
            # Get system prompt with context
            system_prompt = self.get_system_prompt(context)
            
            # Add message to memory
            self.memory.chat_memory.add_user_message(message)
            
            # Prepare messages for LLM with tool results
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Add tool results to context
            if tool_results:
                tool_context = "\n\nRÉSULTATS MÉTÉOROLOGIQUES:\n"
                for i, result in enumerate(tool_results, 1):
                    tool_context += f"\n--- Données météo {i} ---\n{result}\n"
                messages.append({"role": "assistant", "content": tool_context})
            
            # Add conversation history
            chat_history = self.memory.chat_memory.messages[-6:]  # Last 6 messages
            for msg in chat_history:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})
            
            # Generate response
            response = self.llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Add response to memory
            self.memory.chat_memory.add_ai_message(response_text)
            
            # Update state
            state.messages.append(HumanMessage(content=message))
            state.messages.append(AIMessage(content=response_text))
            state.current_agent = self.name
            
            # Format response
            metadata = {
                "agent_type": "weather_intelligence",
                "tools_used": tools_needed,
                "context_used": context,
                "memory_summary": self.get_memory_summary()
            }
            
            return self.format_response(response_text, metadata)
            
        except Exception as e:
            logger.error(f"Error processing message in Weather Intelligence: {e}")
            error_response = "Je rencontre une difficulté technique. Pouvez-vous reformuler votre question ?"
            return self.format_response(error_response, {"error": str(e)})
    
    def _analyze_message_for_tools(self, message: str) -> List[str]:
        """Analyze message to determine which tools are needed."""
        message_lower = message.lower()
        tools_needed = []
        
        # Weather keywords
        weather_keywords = ["météo", "temps", "prévisions", "pluie", "vent", "température", "gel", "sécheresse"]
        if any(keyword in message_lower for keyword in weather_keywords):
            tools_needed.append("enhanced_weather_forecast")
        
        return tools_needed
    
    def _execute_tool(self, tool_name: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Execute a specific tool based on the message content."""
        try:
            # Find the tool
            tool = None
            for t in self.tools:
                if t.name == tool_name:
                    tool = t
                    break
            
            if not tool:
                return None
            
            # Extract parameters from message for weather forecast
            if tool_name == "enhanced_weather_forecast":
                location = self._extract_location(message, context)
                days = self._extract_forecast_days(message)
                crop_type = self._extract_crop_type(message)
                return tool._run(location, days, crop_type)
            
            return None
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return None
    
    def _extract_location(self, message: str, context: Dict[str, Any]) -> str:
        """Extract location from message and context."""
        # Get from context if available
        if 'farm_location' in context:
            return context['farm_location']
        
        # Default location
        return "France"
    
    def _extract_forecast_days(self, message: str) -> int:
        """Extract forecast period from message."""
        # Simplified extraction - in production would use NLP
        if "semaine" in message.lower() or "7 jours" in message:
            return 7
        elif "3 jours" in message:
            return 3
        elif "5 jours" in message:
            return 5
        else:
            return 7  # Default
    
    def _extract_crop_type(self, message: str) -> Optional[str]:
        """Extract crop type from message."""
        crop_types = ["blé", "orge", "maïs", "colza", "tournesol", "triticale"]
        message_lower = message.lower()
        for crop in crop_types:
            if crop in message_lower:
                return crop
        return None
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Enhanced context validation for weather operations."""
        # Weather agent needs location information
        return 'farm_location' in context or 'coordinates' in context
