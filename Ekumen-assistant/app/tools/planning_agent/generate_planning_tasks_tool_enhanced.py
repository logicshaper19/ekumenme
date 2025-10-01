"""
Enhanced Generate Planning Tasks Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (1h TTL for task generation)
- Structured error handling
- Config file validation
- Comprehensive task templates
"""

import logging
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from langchain.tools import StructuredTool

from app.tools.schemas.planning_schemas import (
    PlanningTasksInput,
    PlanningTasksOutput,
    PlanningTask,
    TaskPriority,
    TaskStatus
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedPlanningTasksService:
    """
    Service for generating planning tasks with caching.
    
    Features:
    - Loads task templates from JSON config file
    - Supports multiple crops (blé, maïs, colza, etc.)
    - Generates task dependencies
    - Calculates duration and costs
    - Fallback templates if config unavailable
    
    Cache Strategy:
    - TTL: 1 hour (3600s) - task templates change infrequently
    - Category: planning
    - Keys include crop, surface, and organic flag
    """
    
    def __init__(self):
        """Initialize service and load config"""
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load planning tasks configuration from JSON file"""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 
            'config', 
            'planning_tasks_config.json'
        )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"✅ Loaded planning tasks config from {config_path}")
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using fallback")
            self._config = self._get_fallback_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}, using fallback")
            self._config = self._get_fallback_config()
        except Exception as e:
            logger.error(f"Failed to load planning tasks config: {e}, using fallback")
            self._config = self._get_fallback_config()
    
    @redis_cache(ttl=3600, model_class=PlanningTasksOutput, category="planning")
    async def generate_tasks(self, input_data: PlanningTasksInput) -> PlanningTasksOutput:
        """
        Generate planning tasks for a crop.
        
        Args:
            input_data: Validated input
            
        Returns:
            PlanningTasksOutput with generated tasks
            
        Raises:
            ValueError: If crop not found or task generation fails
        """
        try:
            # Get task templates for crop
            task_templates = self._config.get("task_templates", {})
            crop_lower = input_data.crop.lower()
            
            # Try to find crop config
            crop_config = task_templates.get(crop_lower)
            
            if not crop_config:
                # Try fallback to wheat if crop not found
                logger.warning(f"No task templates found for crop: {input_data.crop}, checking available crops")
                available_crops = ", ".join(task_templates.keys())
                return PlanningTasksOutput(
                    success=False,
                    crop=input_data.crop,
                    surface_ha=input_data.surface_ha,
                    error=f"Culture '{input_data.crop}' non reconnue",
                    error_type="unknown_crop"
                )
            
            # Generate tasks from templates
            tasks = self._generate_tasks_from_templates(
                crop_config,
                input_data.crop,
                input_data.surface_ha,
                input_data.organic
            )
            
            # Calculate total duration
            total_duration = sum(task.estimated_duration_days for task in tasks)
            
            logger.info(f"✅ Generated {len(tasks)} tasks for {input_data.crop} ({input_data.surface_ha} ha)")
            
            return PlanningTasksOutput(
                success=True,
                crop=input_data.crop,
                surface_ha=input_data.surface_ha,
                tasks=tasks,
                total_tasks=len(tasks),
                estimated_total_duration_days=total_duration
            )
            
        except Exception as e:
            logger.error(f"Planning tasks generation error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de la génération des tâches: {str(e)}")
    
    def _generate_tasks_from_templates(
        self,
        crop_config: Dict[str, Any],
        crop_name: str,
        surface_ha: float,
        organic: bool
    ) -> List[PlanningTask]:
        """
        Generate tasks from crop configuration templates.
        
        Filters out non-organic tasks if organic=True.
        Generates unique task IDs.
        """
        tasks = []
        task_templates = crop_config.get("tasks", [])
        
        for idx, template in enumerate(task_templates):
            # Skip non-organic tasks if organic farming
            if organic and template.get("organic_compatible", True) is False:
                continue
            
            # Generate unique task ID
            task_id = f"{crop_name.lower()}_{template['name'].lower().replace(' ', '_')}_{idx}"
            
            # Convert hours to days (assuming 8-hour workday)
            duration_hours = template.get("duration_hours", 8.0)
            duration_days = max(1, int(duration_hours / 8))
            
            # Map priority number to enum
            priority_num = template.get("priority", 3)
            if priority_num == 1:
                priority = TaskPriority.CRITICAL
            elif priority_num == 2:
                priority = TaskPriority.HIGH
            elif priority_num >= 4:
                priority = TaskPriority.LOW
            else:
                priority = TaskPriority.MEDIUM
            
            # Get resources required
            resources = []
            if template.get("equipment"):
                resources.append(template["equipment"])
            
            task = PlanningTask(
                task_id=task_id,
                task_name=template["name"],
                description=template.get("description", f"{template['name']} pour {crop_name}"),
                priority=priority,
                estimated_duration_days=duration_days,
                dependencies=template.get("dependencies", []),
                resources_required=resources,
                optimal_period=template.get("optimal_period"),
                status=TaskStatus.PENDING
            )
            
            tasks.append(task)
        
        return tasks
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """
        Fallback configuration if config file cannot be loaded.
        
        Provides basic wheat (blé) tasks as minimum viable configuration.
        """
        return {
            "task_templates": {
                "blé": {
                    "crop_name": "Blé",
                    "category": "céréales",
                    "tasks": [
                        {
                            "name": "Préparation sol",
                            "duration_hours": 16.0,
                            "equipment": "tracteur_120cv",
                            "priority": 1,
                            "dependencies": [],
                            "cost_per_hectare": 45.0,
                            "yield_impact": 0.05,
                            "description": "Préparation du sol pour le semis",
                            "optimal_period": "septembre-octobre",
                            "organic_compatible": True
                        },
                        {
                            "name": "Semis",
                            "duration_hours": 24.0,
                            "equipment": "semoir",
                            "priority": 2,
                            "dependencies": ["Préparation sol"],
                            "cost_per_hectare": 85.0,
                            "yield_impact": 0.12,
                            "description": "Semis du blé",
                            "optimal_period": "octobre-novembre",
                            "organic_compatible": True
                        },
                        {
                            "name": "Fertilisation",
                            "duration_hours": 8.0,
                            "equipment": "épandeur",
                            "priority": 3,
                            "dependencies": ["Semis"],
                            "cost_per_hectare": 120.0,
                            "yield_impact": 0.15,
                            "description": "Fertilisation azotée",
                            "optimal_period": "février-mars",
                            "organic_compatible": False
                        },
                        {
                            "name": "Récolte",
                            "duration_hours": 32.0,
                            "equipment": "moissonneuse",
                            "priority": 1,
                            "dependencies": ["Semis"],
                            "cost_per_hectare": 80.0,
                            "yield_impact": 0.0,
                            "description": "Récolte du blé",
                            "optimal_period": "juillet-août",
                            "organic_compatible": True
                        }
                    ]
                }
            }
        }


async def generate_planning_tasks_enhanced(
    crop: str,
    surface_ha: float,
    start_date: Optional[str] = None,
    organic: bool = False
) -> str:
    """
    Async wrapper for generate planning tasks tool
    
    Args:
        crop: Crop name (e.g., 'blé', 'maïs', 'colza')
        surface_ha: Surface area in hectares
        start_date: Start date (ISO format, optional)
        organic: Whether organic farming
        
    Returns:
        JSON string with planning tasks
    """
    try:
        # Validate inputs
        input_data = PlanningTasksInput(
            crop=crop,
            surface_ha=surface_ha,
            start_date=start_date,
            organic=organic
        )
        
        # Execute service
        service = EnhancedPlanningTasksService()
        result = await service.generate_tasks(input_data)
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        # Validation or business logic error
        error_result = PlanningTasksOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in generate_planning_tasks_enhanced: {e}", exc_info=True)
        error_result = PlanningTasksOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
generate_planning_tasks_tool_enhanced = StructuredTool.from_function(
    func=generate_planning_tasks_enhanced,
    name="generate_planning_tasks",
    description="""Génère les tâches de planification agricole pour une culture donnée.

Analyse:
- Tâches standard par culture (préparation, semis, fertilisation, récolte, etc.)
- Dépendances entre tâches
- Durée estimée
- Ressources nécessaires
- Périodes optimales
- Compatibilité agriculture biologique

Retourne une liste complète de tâches planifiées avec priorités et dépendances.""",
    args_schema=PlanningTasksInput,
    return_direct=False,
    coroutine=generate_planning_tasks_enhanced,
    handle_validation_error=True
)

