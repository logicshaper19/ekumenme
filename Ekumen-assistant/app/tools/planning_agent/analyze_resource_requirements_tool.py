"""
Enhanced Analyze Resource Requirements Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (30min TTL for resource analysis)
- Realistic resource extraction from task data
- Critical resource identification
- Bottleneck detection
- Availability warnings
"""

import logging
import re
from typing import Optional, List, Dict, Any
from langchain.tools import StructuredTool

from app.tools.schemas.planning_schemas import (
    ResourceRequirementsInput,
    ResourceRequirementsOutput,
    ResourceRequirement,
    ResourceType
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class ResourceRequirementsService:
    """
    Service for analyzing resource requirements with caching.
    
    Features:
    - Extract resources from task data (equipment, labor, materials)
    - Identify critical resources (bottlenecks, high utilization)
    - Calculate resource quantities and timing
    - Provide availability warnings
    
    Cache Strategy:
    - TTL: 30 minutes (1800s) - resource needs change with task updates
    - Category: planning
    - Keys include crop, surface, and task count
    """
    
    @redis_cache(ttl=1800, model_class=ResourceRequirementsOutput, category="planning")
    async def analyze_resources(self, input_data: ResourceRequirementsInput) -> ResourceRequirementsOutput:
        """
        Analyze resource requirements for tasks.
        
        Args:
            input_data: Validated input with crop, surface, and tasks
            
        Returns:
            ResourceRequirementsOutput with resource requirements and warnings
            
        Raises:
            ValueError: If resource analysis fails
        """
        try:
            # Validate tasks have required fields
            for idx, task in enumerate(input_data.tasks):
                if 'task_name' not in task:
                    raise ValueError(f"Tâche {idx}: doit avoir 'task_name'")

                # Validate resources_required is a list if present
                if 'resources_required' in task:
                    if not isinstance(task['resources_required'], list):
                        raise ValueError(f"Tâche '{task['task_name']}': resources_required doit être une liste")

                    # Validate each resource is a string (but don't enforce format - just warn)
                    for resource in task['resources_required']:
                        if not isinstance(resource, str):
                            raise ValueError(f"Tâche '{task['task_name']}': chaque ressource doit être une chaîne de caractères")

            # Extract resource requirements from tasks
            resource_requirements, unknown_formats = self._extract_resource_requirements(
                input_data.tasks,
                input_data.surface_ha
            )

            # Identify critical resources
            critical_resources = self._identify_critical_resources(
                resource_requirements
            )

            # Generate availability warnings
            availability_warnings = self._generate_availability_warnings(
                resource_requirements,
                critical_resources,
                input_data.surface_ha,
                unknown_formats
            )

            logger.info(f"✅ Analyzed resources for {input_data.crop}: {len(resource_requirements)} resources identified")

            return ResourceRequirementsOutput(
                success=True,
                crop=input_data.crop,
                surface_ha=input_data.surface_ha,
                resource_requirements=resource_requirements,
                total_resources=len(resource_requirements),
                critical_resources=critical_resources,
                resource_availability_warnings=availability_warnings
            )
            
        except Exception as e:
            logger.error(f"Resource requirements analysis error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de l'analyse des ressources: {str(e)}")
    
    def _extract_resource_requirements(
        self,
        tasks: List[Dict[str, Any]],
        surface_ha: float
    ) -> List[ResourceRequirement]:
        """
        Extract resource requirements from tasks.

        Parses resources_required field from each task.
        Flexible parsing - warns about unknown formats instead of failing.
        """
        requirements = []
        resource_tracker = {}  # Track cumulative quantities
        unknown_formats = []  # Track unknown resource formats

        for task in tasks:
            task_name = task.get('task_name', '')
            resources = task.get('resources_required', [])
            duration_days = task.get('estimated_duration_days', 1)

            for resource_str in resources:
                # Check for known prefixes (flexible - allows variations)
                valid_prefixes = ['Équipement:', 'Personnel:', 'Matériaux:', 'Matériel:']
                has_valid_prefix = any(prefix in resource_str for prefix in valid_prefixes)

                if not has_valid_prefix:
                    # Warn but don't fail - skip unknown formats
                    if resource_str not in unknown_formats:
                        logger.warning(f"Task '{task_name}': unknown resource format '{resource_str}' - skipping")
                        unknown_formats.append(resource_str)
                    continue
                # Parse resource string (e.g., "Équipement: tracteur_120cv")
                if 'Équipement:' in resource_str:
                    equipment_name = resource_str.split('Équipement:')[1].strip()
                    
                    # Calculate equipment hours (30% utilization of task duration)
                    equipment_hours = duration_days * 8 * 0.3
                    
                    key = f"equipment_{equipment_name}"
                    if key not in resource_tracker:
                        resource_tracker[key] = {
                            'type': ResourceType.EQUIPMENT,
                            'name': equipment_name,
                            'quantity': 0.0,
                            'unit': 'heures',
                            'timing': [],
                            'critical': False
                        }
                    
                    resource_tracker[key]['quantity'] += equipment_hours
                    resource_tracker[key]['timing'].append(task_name)
                
                elif 'Personnel:' in resource_str:
                    personnel_str = resource_str.split('Personnel:')[1].strip()
                    
                    # Extract personnel count
                    personnel_count = self._extract_personnel_count(personnel_str)
                    
                    # Calculate labor hours (50% utilization of task duration)
                    labor_hours = duration_days * 8 * 0.5 * personnel_count
                    
                    key = f"labor_{personnel_str}"
                    if key not in resource_tracker:
                        resource_tracker[key] = {
                            'type': ResourceType.LABOR,
                            'name': personnel_str,
                            'quantity': 0.0,
                            'unit': 'heures',
                            'timing': [],
                            'critical': False
                        }
                    
                    resource_tracker[key]['quantity'] += labor_hours
                    resource_tracker[key]['timing'].append(task_name)
                
                elif 'Matériaux:' in resource_str or 'Matériel:' in resource_str:
                    # Extract material name
                    if 'Matériaux:' in resource_str:
                        materials = resource_str.split('Matériaux:')[1].strip()
                    else:
                        materials = resource_str.split('Matériel:')[1].strip()

                    # Materials tracking limitation:
                    # We track SURFACE TO TREAT (hectares), not actual quantities (kg, L)
                    # Real quantities require task-specific data (seed density, fertilizer dose, etc.)
                    key = f"materials_{materials}"
                    if key not in resource_tracker:
                        resource_tracker[key] = {
                            'type': ResourceType.MATERIALS,
                            'name': materials,
                            'quantity': 0.0,
                            'unit': 'hectares (zone à traiter)',  # Honest about limitation
                            'timing': [],
                            'critical': True  # Materials are often critical
                        }

                    # Accumulate surface area requiring this material
                    resource_tracker[key]['quantity'] += surface_ha
                    resource_tracker[key]['timing'].append(task_name)
        
        # Convert tracker to ResourceRequirement objects
        for key, data in resource_tracker.items():
            timing_str = ', '.join(data['timing'][:3])  # Show first 3 tasks
            if len(data['timing']) > 3:
                timing_str += f" (+{len(data['timing']) - 3} autres)"

            requirements.append(ResourceRequirement(
                resource_type=data['type'],
                resource_name=data['name'],
                quantity=round(data['quantity'], 1),
                unit=data['unit'],
                timing=timing_str,
                critical=data['critical']
            ))

        return requirements, unknown_formats
    
    def _extract_personnel_count(self, personnel_str: str) -> int:
        """Extract personnel count from string"""
        numbers = re.findall(r'\d+', personnel_str)
        if numbers:
            return sum(int(n) for n in numbers)
        return 1
    
    def _identify_critical_resources(
        self,
        requirements: List[ResourceRequirement]
    ) -> List[str]:
        """
        Identify critical resources based on:
        - High utilization (>80 hours for equipment = >10 working days)
        - Materials (always critical - must be ordered in advance)
        - Specialized equipment (limited availability)
        - High labor requirements (>200 hours = >25 working days)

        Thresholds based on:
        - Equipment: >80h assumes 8h/day = >10 days continuous use (high for single equipment)
        - Labor: >200h assumes 8h/day = >25 days (requires dedicated team or seasonal workers)
        """
        critical = []

        for req in requirements:
            # Materials are always critical (must be ordered, delivered, stored)
            if req.resource_type == ResourceType.MATERIALS:
                critical.append(req.resource_name)
                continue

            # Equipment with high utilization
            if req.resource_type == ResourceType.EQUIPMENT:
                # >80 hours = >10 working days of continuous use
                # Indicates potential bottleneck or need for backup equipment
                if req.quantity > 80:
                    critical.append(req.resource_name)
                    continue

                # Specialized equipment with limited availability
                # (moissonneuse, pulvérisateur haute capacité, etc.)
                specialized = ['moissonneuse', 'batteuse', 'ensileuse', 'arracheuse']
                if any(spec in req.resource_name.lower() for spec in specialized):
                    critical.append(req.resource_name)
                    continue

            # Labor with high hours
            if req.resource_type == ResourceType.LABOR:
                # >200 hours = >25 working days
                # Requires dedicated team or seasonal recruitment
                if req.quantity > 200:
                    critical.append(req.resource_name)

        return critical
    
    def _generate_availability_warnings(
        self,
        requirements: List[ResourceRequirement],
        critical_resources: List[str],
        surface_ha: float,
        unknown_formats: List[str]
    ) -> List[str]:
        """
        Generate warnings about resource availability.

        Thresholds based on typical farm operations:
        - Equipment: >400h total = >50 working days across all equipment (high utilization)
        - Labor: >500h total = >60 working days across all personnel (requires team)
        - Large surface: >100 ha requires significant logistics coordination
        """
        warnings = []
        seasonal_warnings_added = set()  # Track to avoid duplicates

        # CRITICAL WARNING: Materials quantities limitation
        materials_reqs = [r for r in requirements if r.resource_type == ResourceType.MATERIALS]
        if materials_reqs:
            warnings.append(
                "⚠️ LIMITATION: Quantités de matériaux exprimées en surface à traiter (hectares) - "
                "Consulter fournisseurs pour quantités réelles (kg, L) selon densités de semis/doses d'application"
            )

        # Warn about unknown resource formats
        if unknown_formats:
            warnings.append(
                f"ℹ️ {len(unknown_formats)} format(s) de ressource non reconnu(s) - ignoré(s) dans l'analyse"
            )

        # Warn about critical resources
        if critical_resources:
            warnings.append(f"⚠️ {len(critical_resources)} ressource(s) critique(s) identifiée(s) - Vérifier disponibilité")

        # Check equipment utilization
        equipment_reqs = [r for r in requirements if r.resource_type == ResourceType.EQUIPMENT]
        total_equipment_hours = sum(r.quantity for r in equipment_reqs)

        # >400h total = >50 working days across all equipment
        # Indicates high overall equipment demand, potential scheduling conflicts
        if total_equipment_hours > 400:
            warnings.append(f"⚠️ Utilisation équipement élevée ({total_equipment_hours:.0f}h total) - Planifier maintenance et disponibilité")

        # Check labor requirements
        labor_reqs = [r for r in requirements if r.resource_type == ResourceType.LABOR]
        total_labor_hours = sum(r.quantity for r in labor_reqs)

        # >500h total = >60 working days across all personnel
        # Requires dedicated team or seasonal recruitment
        if total_labor_hours > 500:
            warnings.append(f"⚠️ Besoins en main-d'œuvre élevés ({total_labor_hours:.0f}h total) - Prévoir recrutement saisonnier")

        # Warn about large surface (>100 ha requires significant logistics)
        if surface_ha > 100:
            warnings.append(f"ℹ️ Grande surface ({surface_ha} ha) - Vérifier capacité logistique et stockage")

        # Seasonal availability warnings (avoid duplicates)
        specialized_equipment = {
            'moissonneuse': "⚠️ Moissonneuse - Réserver à l'avance (forte demande en saison de récolte)",
            'batteuse': "⚠️ Batteuse - Réserver à l'avance (forte demande en saison)",
            'ensileuse': "⚠️ Ensileuse - Réserver à l'avance (disponibilité limitée)",
            'pulvérisateur': "ℹ️ Pulvérisateur - Vérifier disponibilité pendant périodes de traitement"
        }

        for req in requirements:
            if req.resource_type == ResourceType.EQUIPMENT:
                for equipment_type, warning in specialized_equipment.items():
                    if equipment_type in req.resource_name.lower() and equipment_type not in seasonal_warnings_added:
                        warnings.append(warning)
                        seasonal_warnings_added.add(equipment_type)

        if not warnings:
            warnings.append("✅ Aucun problème de disponibilité identifié")

        return warnings


async def analyze_resource_requirements_enhanced(
    crop: str,
    surface_ha: float,
    tasks: List[Dict[str, Any]]
) -> str:
    """
    Async wrapper for analyze resource requirements tool
    
    Args:
        crop: Crop name (e.g., 'blé', 'maïs')
        surface_ha: Surface area in hectares
        tasks: List of tasks from generate_planning_tasks
        
    Returns:
        JSON string with resource analysis
    """
    try:
        # Validate inputs
        input_data = ResourceRequirementsInput(
            crop=crop,
            surface_ha=surface_ha,
            tasks=tasks
        )
        
        # Execute service
        service = ResourceRequirementsService()
        result = await service.analyze_resources(input_data)
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        # Validation or business logic error
        error_result = ResourceRequirementsOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            total_resources=0,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in analyze_resource_requirements_enhanced: {e}", exc_info=True)
        error_result = ResourceRequirementsOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            total_resources=0,
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
analyze_resource_requirements_tool = StructuredTool.from_function(
    func=analyze_resource_requirements_enhanced,
    name="analyze_resource_requirements",
    description="""Analyse les besoins en ressources pour la planification agricole.

Analyse:
- Équipement nécessaire (tracteurs, semoirs, moissonneuses, etc.)
- Main-d'œuvre requise (heures, personnel)
- Matériaux (semences, engrais, produits phyto)
- Ressources critiques (goulots d'étranglement)
- Avertissements de disponibilité

Calculs basés sur:
- Utilisation équipement: 30% du temps calendaire
- Utilisation main-d'œuvre: 50% du temps calendaire
- Identification automatique des ressources critiques

Retourne une analyse détaillée avec recommandations de disponibilité.""",
    args_schema=ResourceRequirementsInput,
    return_direct=False,
    coroutine=analyze_resource_requirements_enhanced,
    handle_validation_error=True
)

