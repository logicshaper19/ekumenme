"""
Agent Selector - Single Purpose Component

Job: Select the most appropriate agent for a given task.
Input: Task description and requirements
Output: Selected agent type and reasoning

This component does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Task type classification."""
    DATA_ANALYSIS = "data_analysis"
    WEATHER_FORECAST = "weather_forecast"
    CROP_HEALTH = "crop_health"
    PLANNING = "planning"
    COMPLIANCE = "compliance"
    SUSTAINABILITY = "sustainability"

@dataclass
class TaskRequirements:
    """Task requirements for agent selection."""
    task_type: TaskType
    complexity: str  # "simple", "moderate", "complex"
    urgency: str     # "low", "medium", "high"
    data_requirements: List[str]
    output_format: str

class AgentSelector:
    """
    Selector for agricultural agents.
    
    Job: Select the most appropriate agent for a given task.
    Input: Task description and requirements
    Output: Selected agent type and reasoning
    """
    
    def __init__(self):
        self.selection_rules = self._initialize_selection_rules()
    
    def _initialize_selection_rules(self) -> Dict[TaskType, str]:
        """Initialize agent selection rules."""
        return {
            TaskType.DATA_ANALYSIS: "farm_data",
            TaskType.WEATHER_FORECAST: "weather",
            TaskType.CROP_HEALTH: "crop_health",
            TaskType.PLANNING: "planning",
            TaskType.COMPLIANCE: "regulatory",
            TaskType.SUSTAINABILITY: "sustainability"
        }
    
    def select_agent(self, task_description: str, requirements: TaskRequirements) -> Dict[str, Any]:
        """
        Select the most appropriate agent for a task.
        
        Args:
            task_description: Description of the task
            requirements: Task requirements
            
        Returns:
            Dictionary with selected agent and reasoning
        """
        try:
            # Determine task type from description
            task_type = self._classify_task_type(task_description)
            
            # Select agent based on task type
            selected_agent = self.selection_rules.get(task_type, "farm_data")
            
            # Generate selection reasoning
            reasoning = self._generate_selection_reasoning(task_type, selected_agent, requirements)
            
            return {
                "selected_agent": selected_agent,
                "task_type": task_type.value,
                "reasoning": reasoning,
                "confidence": self._calculate_selection_confidence(task_type, requirements)
            }
            
        except Exception as e:
            logger.error(f"Agent selection error: {e}")
            return {
                "selected_agent": "farm_data",
                "task_type": "data_analysis",
                "reasoning": f"Default selection due to error: {str(e)}",
                "confidence": 0.5
            }
    
    def _classify_task_type(self, task_description: str) -> TaskType:
        """Classify task type from description."""
        description_lower = task_description.lower()
        
        # Weather-related keywords
        if any(keyword in description_lower for keyword in ["weather", "forecast", "rain", "temperature", "wind"]):
            return TaskType.WEATHER_FORECAST
        
        # Crop health keywords
        if any(keyword in description_lower for keyword in ["disease", "pest", "nutrient", "health", "symptom"]):
            return TaskType.CROP_HEALTH
        
        # Planning keywords
        if any(keyword in description_lower for keyword in ["plan", "schedule", "optimize", "task", "workflow"]):
            return TaskType.PLANNING
        
        # Compliance keywords
        if any(keyword in description_lower for keyword in ["compliance", "regulation", "safety", "amm", "legal"]):
            return TaskType.COMPLIANCE
        
        # Sustainability keywords
        if any(keyword in description_lower for keyword in ["sustainability", "carbon", "biodiversity", "environment"]):
            return TaskType.SUSTAINABILITY
        
        # Default to data analysis
        return TaskType.DATA_ANALYSIS
    
    def _generate_selection_reasoning(self, task_type: TaskType, selected_agent: str, requirements: TaskRequirements) -> str:
        """Generate reasoning for agent selection."""
        reasoning_templates = {
            TaskType.DATA_ANALYSIS: f"Selected {selected_agent} agent for data analysis task. Complexity: {requirements.complexity}",
            TaskType.WEATHER_FORECAST: f"Selected {selected_agent} agent for weather forecasting. Urgency: {requirements.urgency}",
            TaskType.CROP_HEALTH: f"Selected {selected_agent} agent for crop health analysis. Data requirements: {', '.join(requirements.data_requirements)}",
            TaskType.PLANNING: f"Selected {selected_agent} agent for planning task. Output format: {requirements.output_format}",
            TaskType.COMPLIANCE: f"Selected {selected_agent} agent for compliance check. Urgency: {requirements.urgency}",
            TaskType.SUSTAINABILITY: f"Selected {selected_agent} agent for sustainability analysis. Complexity: {requirements.complexity}"
        }
        
        return reasoning_templates.get(task_type, f"Selected {selected_agent} agent for {task_type.value} task")
    
    def _calculate_selection_confidence(self, task_type: TaskType, requirements: TaskRequirements) -> float:
        """Calculate confidence in agent selection."""
        base_confidence = 0.8
        
        # Adjust based on complexity
        if requirements.complexity == "simple":
            base_confidence += 0.1
        elif requirements.complexity == "complex":
            base_confidence -= 0.1
        
        # Adjust based on urgency
        if requirements.urgency == "high":
            base_confidence -= 0.05
        
        return max(0.0, min(1.0, base_confidence))
