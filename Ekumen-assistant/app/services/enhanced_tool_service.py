"""
Enhanced Tool Service for Agricultural AI
Advanced tool integration with validation and error handling
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import inspect

from langchain.tools import BaseTool, tool
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field, validator

from app.services.unified_regulatory_service import UnifiedRegulatoryService
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    """Structured tool result"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float
    tool_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolValidationError(Exception):
    """Tool validation error"""
    pass


class EnhancedAgriculturalTool(BaseTool):
    """Base class for enhanced agricultural tools"""

    # Define as class attributes to avoid Pydantic field validation issues
    regulatory_service: Optional[UnifiedRegulatoryService] = None
    execution_count: int = 0
    last_execution: Optional[datetime] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize services after Pydantic validation
        if self.regulatory_service is None:
            object.__setattr__(self, 'regulatory_service', UnifiedRegulatoryService())
        if self.execution_count == 0:
            object.__setattr__(self, 'execution_count', 0)
        object.__setattr__(self, 'last_execution', None)
    
    def _validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate tool inputs"""
        # Override in subclasses
        return kwargs
    
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs
    ) -> str:
        """Enhanced run method with validation and error handling"""
        start_time = datetime.now()
        self.execution_count += 1
        self.last_execution = start_time
        
        try:
            # Validate inputs
            validated_inputs = self._validate_inputs(**kwargs)
            
            # Execute tool logic
            result = self._execute(**validated_inputs)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create structured result
            tool_result = ToolResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=self.name,
                metadata={
                    "execution_count": self.execution_count,
                    "inputs": validated_inputs
                }
            )
            
            return json.dumps(tool_result.dict(), ensure_ascii=False, indent=2)
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Tool {self.name} failed: {e}")
            
            error_result = ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                tool_name=self.name,
                metadata={
                    "execution_count": self.execution_count,
                    "inputs": kwargs
                }
            )
            
            return json.dumps(error_result.dict(), ensure_ascii=False, indent=2)
    
    def _execute(self, **kwargs) -> Any:
        """Override this method in subclasses"""
        raise NotImplementedError


class WeatherAnalysisTool(EnhancedAgriculturalTool):
    """Enhanced weather analysis tool"""

    name: str = "weather_analysis"
    description: str = "Analyse météorologique avancée pour l'agriculture avec recommandations d'intervention"
    
    def _validate_inputs(self, **kwargs) -> Dict[str, Any]:
        location = kwargs.get('location', 'France')
        days = kwargs.get('days', 7)
        
        if not isinstance(days, int) or days < 1 or days > 14:
            raise ToolValidationError("Days must be between 1 and 14")
        
        return {"location": location, "days": days}
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        from app.tools.weather_agent.get_weather_data_tool import GetWeatherDataTool
        
        weather_tool = GetWeatherDataTool()
        weather_result = weather_tool._run(
            location=kwargs['location'],
            days=kwargs['days']
        )
        
        # Parse and enhance weather data
        try:
            weather_data = json.loads(weather_result)
        except:
            weather_data = {"raw_result": weather_result}
        
        # Add agricultural analysis
        agricultural_analysis = self._analyze_for_agriculture(weather_data)
        
        return {
            "weather_data": weather_data,
            "agricultural_analysis": agricultural_analysis,
            "location": kwargs['location'],
            "forecast_days": kwargs['days']
        }
    
    def _analyze_for_agriculture(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze weather data for agricultural implications"""
        analysis = {
            "intervention_windows": [],
            "risks": [],
            "recommendations": []
        }
        
        # Extract forecast data
        forecasts = weather_data.get('previsions', [])
        if not forecasts:
            return analysis
        
        for day_data in forecasts[:7]:  # Analyze first 7 days
            date = day_data.get('date', 'Unknown')
            
            # Check for good spraying conditions
            wind_speed = day_data.get('wind_speed', 999)
            precipitation = day_data.get('precipitation', 999)
            humidity = day_data.get('humidity', 0)
            
            if wind_speed < 10 and precipitation < 2 and humidity > 50:
                analysis["intervention_windows"].append({
                    "date": date,
                    "type": "pulvérisation",
                    "conditions": "optimales",
                    "details": f"Vent: {wind_speed}km/h, Pluie: {precipitation}mm"
                })
            
            # Check for risks
            if wind_speed > 20:
                analysis["risks"].append({
                    "date": date,
                    "type": "vent_fort",
                    "severity": "élevé" if wind_speed > 30 else "modéré",
                    "impact": "Éviter les pulvérisations"
                })
            
            if precipitation > 10:
                analysis["risks"].append({
                    "date": date,
                    "type": "forte_pluie",
                    "severity": "élevé",
                    "impact": "Risque de lessivage des traitements"
                })
        
        # Generate recommendations
        if analysis["intervention_windows"]:
            analysis["recommendations"].append(
                f"Fenêtres d'intervention favorables: {len(analysis['intervention_windows'])} jours"
            )
        
        if analysis["risks"]:
            analysis["recommendations"].append(
                f"Attention: {len(analysis['risks'])} risques météorologiques identifiés"
            )
        
        return analysis


class RegulatoryComplianceTool(EnhancedAgriculturalTool):
    """Enhanced regulatory compliance tool"""

    name: str = "regulatory_compliance"
    description: str = "Vérification de conformité réglementaire EPHY avec analyse détaillée"
    
    def _validate_inputs(self, **kwargs) -> Dict[str, Any]:
        product_name = kwargs.get('product_name')
        if not product_name:
            raise ToolValidationError("Product name is required")
        
        return {
            "product_name": product_name,
            "crop_type": kwargs.get('crop_type'),
            "dosage": kwargs.get('dosage'),
            "application_method": kwargs.get('application_method')
        }
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        # Use regulatory service
        compliance_result = self.regulatory_service.validate_product_usage(
            product_name=kwargs['product_name'],
            crop_type=kwargs.get('crop_type'),
            dosage=kwargs.get('dosage'),
            application_method=kwargs.get('application_method')
        )
        
        # Enhance with additional analysis
        enhanced_result = self._enhance_compliance_analysis(compliance_result, kwargs)
        
        return enhanced_result
    
    def _enhance_compliance_analysis(
        self,
        compliance_result: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance compliance analysis with additional insights"""
        
        enhanced = {
            "compliance_status": compliance_result,
            "product_name": inputs['product_name'],
            "analysis": {
                "is_compliant": compliance_result.get('is_compliant', False),
                "risk_level": "low",
                "recommendations": [],
                "restrictions": []
            }
        }
        
        # Analyze compliance status
        if not compliance_result.get('is_compliant', False):
            enhanced["analysis"]["risk_level"] = "high"
            enhanced["analysis"]["recommendations"].append(
                "Produit non conforme - chercher une alternative autorisée"
            )
        
        # Add specific recommendations based on product
        product_lower = inputs['product_name'].lower()
        
        if "glyphosate" in product_lower:
            enhanced["analysis"]["restrictions"].extend([
                "Maximum 2 applications par an",
                "Dose maximale 3L/ha",
                "ZNT de 5m minimum"
            ])
        
        if "cuivre" in product_lower:
            enhanced["analysis"]["restrictions"].extend([
                "Maximum 4 kg/ha/an en conventionnel",
                "Maximum 6 kg/ha/an en agriculture biologique"
            ])
        
        return enhanced


class FarmDataAnalysisTool(EnhancedAgriculturalTool):
    """Enhanced farm data analysis tool"""

    name: str = "farm_data_analysis"
    description: str = "Analyse avancée des données d'exploitation avec insights opérationnels"
    
    def _validate_inputs(self, **kwargs) -> Dict[str, Any]:
        return {
            "siret": kwargs.get('siret'),
            "parcel_id": kwargs.get('parcel_id'),
            "analysis_type": kwargs.get('analysis_type', 'general')
        }
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        return asyncio.run(self._async_execute(**kwargs))
    
    async def _async_execute(self, **kwargs) -> Dict[str, Any]:
        """Async execution for database operations"""
        siret = kwargs.get('siret')
        analysis_type = kwargs.get('analysis_type', 'general')
        
        async with AsyncSessionLocal() as session:
            if siret:
                return await self._analyze_specific_farm(session, siret, analysis_type)
            else:
                return await self._analyze_general_statistics(session, analysis_type)
    
    async def _analyze_specific_farm(
        self,
        session,
        siret: str,
        analysis_type: str
    ) -> Dict[str, Any]:
        """Analyze specific farm data"""
        
        # Get farm basic info
        result = await session.execute(text("""
            SELECT e.nom, e.adresse, COUNT(DISTINCT p.id) as parcelles_count,
                   COUNT(DISTINCT i.uuid_intervention) as interventions_count
            FROM farm_operations.exploitations e
            LEFT JOIN farm_operations.parcelles p ON e.siret = p.siret_exploitation
            LEFT JOIN farm_operations.interventions i ON p.id = i.id_parcelle
            WHERE e.siret = :siret
            GROUP BY e.siret, e.nom, e.adresse
        """), {"siret": siret})
        
        farm_info = result.fetchone()
        if not farm_info:
            return {"error": f"Farm with SIRET {siret} not found"}
        
        # Get intervention analysis
        result = await session.execute(text("""
            SELECT ti.libelle, COUNT(*) as count,
                   AVG(EXTRACT(EPOCH FROM (i.date_fin - i.date_debut))/3600) as avg_duration_hours
            FROM farm_operations.interventions i
            JOIN reference.types_intervention ti ON i.id_type_intervention = ti.id_type_intervention
            WHERE i.siret_exploitation = :siret
            GROUP BY ti.libelle
            ORDER BY count DESC
        """), {"siret": siret})
        
        interventions = [
            {
                "type": row[0],
                "count": row[1],
                "avg_duration_hours": round(float(row[2]) if row[2] else 0, 2)
            }
            for row in result.fetchall()
        ]
        
        # Get compliance analysis
        result = await session.execute(text("""
            SELECT COUNT(DISTINCT ii.id) as total_product_uses,
                   COUNT(DISTINCT CASE WHEN p.mentions_autorisees LIKE '%jardins%' 
                         THEN ii.id END) as garden_authorized_uses
            FROM farm_operations.intervention_intrants ii
            JOIN farm_operations.interventions i ON ii.uuid_intervention = i.uuid_intervention
            JOIN reference.intrants inp ON ii.id_intrant = inp.id_intrant
            LEFT JOIN regulatory.produits p ON inp.code_amm = p.numero_amm
            WHERE i.siret_exploitation = :siret
        """), {"siret": siret})
        
        compliance_data = result.fetchone()
        
        compliance_rate = 0
        if compliance_data and compliance_data[0] > 0:
            compliance_rate = round((compliance_data[1] / compliance_data[0]) * 100, 1)
        
        return {
            "farm_info": {
                "name": farm_info[0],
                "address": farm_info[1],
                "parcelles_count": farm_info[2],
                "interventions_count": farm_info[3]
            },
            "intervention_analysis": interventions,
            "compliance_analysis": {
                "total_product_uses": compliance_data[0] if compliance_data else 0,
                "garden_authorized_uses": compliance_data[1] if compliance_data else 0,
                "compliance_rate_percent": compliance_rate
            },
            "insights": self._generate_farm_insights(farm_info, interventions, compliance_rate)
        }
    
    async def _analyze_general_statistics(self, session, analysis_type: str) -> Dict[str, Any]:
        """Analyze general farm statistics"""
        
        # Get overall statistics
        result = await session.execute(text("""
            SELECT COUNT(DISTINCT e.siret) as total_farms,
                   COUNT(DISTINCT p.id) as total_parcelles,
                   COUNT(DISTINCT i.uuid_intervention) as total_interventions,
                   AVG(p.surface_ha) as avg_parcel_size
            FROM farm_operations.exploitations e
            LEFT JOIN farm_operations.parcelles p ON e.siret = p.siret_exploitation
            LEFT JOIN farm_operations.interventions i ON p.id = i.id_parcelle
        """))
        
        stats = result.fetchone()
        
        return {
            "general_statistics": {
                "total_farms": stats[0],
                "total_parcelles": stats[1],
                "total_interventions": stats[2],
                "avg_parcel_size_ha": round(float(stats[3]) if stats[3] else 0, 2)
            },
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_farm_insights(
        self,
        farm_info,
        interventions: List[Dict],
        compliance_rate: float
    ) -> List[str]:
        """Generate insights from farm analysis"""
        insights = []
        
        # Parcel insights
        parcel_count = farm_info[2]
        if parcel_count > 20:
            insights.append("Grande exploitation avec gestion complexe des parcelles")
        elif parcel_count > 10:
            insights.append("Exploitation de taille moyenne nécessitant une planification structurée")
        else:
            insights.append("Petite exploitation permettant une gestion personnalisée")
        
        # Intervention insights
        if interventions:
            most_common = interventions[0]
            insights.append(f"Intervention principale: {most_common['type']} ({most_common['count']} fois)")
            
            if most_common['avg_duration_hours'] > 8:
                insights.append("Interventions longues - optimisation possible")
        
        # Compliance insights
        if compliance_rate > 80:
            insights.append("Excellent taux de conformité réglementaire")
        elif compliance_rate > 60:
            insights.append("Bon taux de conformité, quelques améliorations possibles")
        else:
            insights.append("Taux de conformité à améliorer - révision des pratiques recommandée")
        
        return insights


class EnhancedToolService:
    """Service for managing enhanced agricultural tools"""
    
    def __init__(self):
        self.tools = {
            "weather_analysis": WeatherAnalysisTool(),
            "regulatory_compliance": RegulatoryComplianceTool(),
            "farm_data_analysis": FarmDataAnalysisTool()
        }
        self.execution_stats = {}
    
    def get_tool(self, tool_name: str) -> Optional[EnhancedAgriculturalTool]:
        """Get tool by name"""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> List[EnhancedAgriculturalTool]:
        """Get all available tools"""
        return list(self.tools.values())
    
    def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """Execute tool with enhanced error handling"""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found",
                execution_time=0.0,
                tool_name=tool_name
            )
        
        try:
            result_json = tool._run(**kwargs)
            result_data = json.loads(result_json)
            return ToolResult(**result_data)
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=0.0,
                tool_name=tool_name
            )
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all tools"""
        return {
            name: tool.description
            for name, tool in self.tools.items()
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics for all tools"""
        stats = {}
        for name, tool in self.tools.items():
            stats[name] = {
                "execution_count": tool.execution_count,
                "last_execution": tool.last_execution.isoformat() if tool.last_execution else None
            }
        return stats
