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
import math
from typing import Optional, List, Dict, Any, Set
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

# Config directory from environment or default
CONFIG_DIR = os.environ.get('PLANNING_CONFIG_DIR', os.path.join(
    os.path.dirname(__file__), '..', '..', 'config'
))


class PlanningTasksService:
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
        """Load and validate planning tasks configuration from JSON file"""
        config_path = os.path.join(CONFIG_DIR, 'planning_tasks_config.json')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate config structure
            if not self._validate_config(config):
                logger.error("Config validation failed, using fallback")
                self._config = self._get_fallback_config()
                return

            self._config = config
            logger.info(f"✅ Loaded and validated planning tasks config from {config_path}")

        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using fallback")
            self._config = self._get_fallback_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}, using fallback")
            self._config = self._get_fallback_config()
        except Exception as e:
            logger.error(f"Failed to load planning tasks config: {e}, using fallback")
            self._config = self._get_fallback_config()

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate config structure.

        Checks:
        - Has task_templates key
        - Each crop has tasks list
        - Each task has required fields
        """
        if "task_templates" not in config:
            logger.error("Config missing 'task_templates' key")
            return False

        for crop, crop_config in config["task_templates"].items():
            if not isinstance(crop_config, dict):
                logger.error(f"Crop '{crop}' config is not a dict")
                return False

            if "tasks" not in crop_config:
                logger.error(f"Crop '{crop}' missing 'tasks' list")
                return False

            if not isinstance(crop_config["tasks"], list):
                logger.error(f"Crop '{crop}' tasks is not a list")
                return False

            # Validate each task
            for idx, task in enumerate(crop_config["tasks"]):
                required_fields = ["name", "duration_hours"]
                for field in required_fields:
                    if field not in task:
                        logger.error(f"Crop '{crop}' task {idx} missing required field: {field}")
                        return False

                # Validate priority if present
                if "priority" in task:
                    priority = task["priority"]
                    if not isinstance(priority, int) or priority not in [1, 2, 3, 4, 5]:
                        logger.error(f"Crop '{crop}' task {idx} has invalid priority: {priority}")
                        return False

        logger.info("✅ Config validation passed")
        return True
    
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

        Note:
            start_date parameter is accepted but not yet implemented.
            Tasks are generated without specific scheduling dates.
            Future enhancement will add date scheduling based on:
            - Start date
            - Task dependencies
            - Optimal periods
        """
        try:
            warnings = []

            # Warn if start_date provided but not implemented
            if input_data.start_date:
                warnings.append("⚠️ Planification par date non encore implémentée - Les tâches sont générées sans dates spécifiques")

            # Get task templates for crop
            task_templates = self._config.get("task_templates", {})
            crop_lower = input_data.crop.lower()

            # Try to find crop config
            crop_config = task_templates.get(crop_lower)

            if not crop_config:
                # Show available crops
                available_crops = ", ".join(sorted(task_templates.keys()))
                logger.warning(f"No task templates found for crop: {input_data.crop}")
                return PlanningTasksOutput(
                    success=False,
                    crop=input_data.crop,
                    surface_ha=input_data.surface_ha,
                    error=f"Culture '{input_data.crop}' non reconnue. Cultures disponibles: {available_crops}",
                    error_type="unknown_crop"
                )

            # Generate tasks from templates
            tasks = self._generate_tasks_from_templates(
                crop_config,
                input_data.crop,
                input_data.surface_ha,
                input_data.organic
            )

            # Add warning if organic filtering removed tasks
            if input_data.organic:
                total_templates = len(crop_config.get("tasks", []))
                if len(tasks) < total_templates:
                    removed = total_templates - len(tasks)
                    warnings.append(f"ℹ️ {removed} tâche(s) non compatible(s) avec l'agriculture biologique exclue(s)")

            # Calculate total duration
            total_duration = sum(task.estimated_duration_days for task in tasks)

            logger.info(f"✅ Generated {len(tasks)} tasks for {input_data.crop} ({input_data.surface_ha} ha)")

            return PlanningTasksOutput(
                success=True,
                crop=input_data.crop,
                surface_ha=input_data.surface_ha,
                tasks=tasks,
                total_tasks=len(tasks),
                estimated_total_duration_days=total_duration,
                warnings=warnings
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

        Features:
        - Filters out non-organic tasks if organic=True
        - Scales duration by surface area (sublinear scaling)
        - Validates and maps priorities
        - Collects comprehensive resources
        - Validates dependencies after all tasks created
        """
        tasks = []
        task_templates = crop_config.get("tasks", [])

        # Priority mapping with validation
        priority_map = {
            1: TaskPriority.CRITICAL,
            2: TaskPriority.HIGH,
            3: TaskPriority.MEDIUM,
            4: TaskPriority.LOW,
            5: TaskPriority.LOW
        }

        for idx, template in enumerate(task_templates):
            # Skip non-organic tasks if organic farming
            if organic and template.get("organic_compatible", True) is False:
                continue

            # Generate unique task ID
            task_id = f"{crop_name.lower()}_{template['name'].lower().replace(' ', '_')}_{idx}"

            # Calculate duration scaled by surface area
            # Base duration is for 1 hectare, scales sublinearly (economy of scale)
            base_duration_hours = template.get("duration_hours", 8.0)
            scaled_hours = base_duration_hours * (surface_ha ** 0.8)  # Sublinear scaling
            duration_days = math.ceil(scaled_hours / 8.0)  # Round up to full days

            # Map priority number to enum with validation
            priority_num = template.get("priority", 3)
            if priority_num not in priority_map:
                logger.warning(f"Invalid priority {priority_num} for task '{template['name']}', defaulting to MEDIUM")
                priority_num = 3
            priority = priority_map[priority_num]

            # Collect comprehensive resources
            resources = []
            if template.get("equipment"):
                resources.append(f"Équipement: {template['equipment']}")
            if template.get("personnel"):
                resources.append(f"Personnel: {template['personnel']}")
            if template.get("materials"):
                materials = template["materials"]
                if isinstance(materials, list):
                    resources.extend([f"Matériel: {m}" for m in materials])
                else:
                    resources.append(f"Matériel: {materials}")
            if template.get("weather_constraints"):
                constraints = template["weather_constraints"]
                if isinstance(constraints, list):
                    resources.append(f"Conditions: {', '.join(constraints)}")
                else:
                    resources.append(f"Conditions: {constraints}")

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

        # Validate dependencies after all tasks created
        self._validate_task_dependencies(tasks)

        return tasks

    def _validate_task_dependencies(self, tasks: List[PlanningTask]) -> None:
        """
        Validate that all task dependencies reference existing tasks.

        Removes invalid dependencies and logs warnings.
        """
        task_names: Set[str] = {task.task_name for task in tasks}

        for task in tasks:
            invalid_deps = []
            for dep in task.dependencies:
                if dep not in task_names:
                    logger.warning(f"Task '{task.task_name}' has invalid dependency: '{dep}' (not found in task list)")
                    invalid_deps.append(dep)

            # Remove invalid dependencies
            for invalid_dep in invalid_deps:
                task.dependencies.remove(invalid_dep)
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """
        Fallback configuration if config file cannot be loaded.

        Provides basic wheat (blé) tasks as minimum viable configuration.
        Includes comprehensive resource information.
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
                            "personnel": "1 chauffeur",
                            "priority": 1,
                            "dependencies": [],
                            "description": "Préparation du sol pour le semis",
                            "optimal_period": "septembre-octobre",
                            "weather_constraints": ["sol_sec", "pas_de_gel"],
                            "organic_compatible": True
                        },
                        {
                            "name": "Semis",
                            "duration_hours": 24.0,
                            "equipment": "semoir",
                            "personnel": "1 chauffeur",
                            "materials": ["semences certifiées"],
                            "priority": 2,
                            "dependencies": ["Préparation sol"],
                            "description": "Semis du blé",
                            "optimal_period": "octobre-novembre",
                            "weather_constraints": ["sol_ressuyé", "température_positive"],
                            "organic_compatible": True
                        },
                        {
                            "name": "Fertilisation",
                            "duration_hours": 8.0,
                            "equipment": "épandeur",
                            "personnel": "1 chauffeur",
                            "materials": ["engrais azoté"],
                            "priority": 3,
                            "dependencies": ["Semis"],
                            "description": "Fertilisation azotée",
                            "optimal_period": "février-mars",
                            "weather_constraints": ["pas_de_pluie_prévue"],
                            "organic_compatible": False
                        },
                        {
                            "name": "Récolte",
                            "duration_hours": 32.0,
                            "equipment": "moissonneuse",
                            "personnel": "1 chauffeur, 1 aide",
                            "priority": 1,
                            "dependencies": ["Semis"],
                            "description": "Récolte du blé",
                            "optimal_period": "juillet-août",
                            "weather_constraints": ["temps_sec", "grain_mûr"],
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
        service = PlanningTasksService()
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
generate_planning_tasks_tool = StructuredTool.from_function(
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

