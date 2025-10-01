"""
Enhanced Optimize Task Sequence Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (30min TTL for sequence optimization)
- Topological sort with dependency resolution
- Parallel task identification
- Start/end day calculation
- Efficiency gain metrics
"""

import logging
from typing import Optional, List, Dict, Any, Set, Tuple
from collections import defaultdict, deque
from langchain.tools import StructuredTool

from app.tools.schemas.planning_schemas import (
    TaskSequenceInput,
    TaskSequenceOutput,
    OptimizedTask,
    OptimizationConstraint
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


# Type alias for clarity
DependencyGraph = Dict[str, List[str]]  # task_id -> list of tasks it depends on
ReverseDependencyGraph = Dict[str, List[str]]  # task_id -> list of tasks that depend on it


class TaskSequenceService:
    """
    Service for optimizing task sequences with caching.
    
    Features:
    - Topological sort respecting dependencies
    - Parallel task identification
    - Start/end day calculation
    - Multiple optimization strategies (time, cost, resources)
    - Cycle detection in dependencies
    - Efficiency gain calculation
    
    Cache Strategy:
    - TTL: 30 minutes (1800s) - sequences change with task updates
    - Category: planning
    - Keys include task IDs and optimization goal
    """
    
    @redis_cache(ttl=1800, model_class=TaskSequenceOutput, category="planning")
    async def optimize_sequence(self, input_data: TaskSequenceInput) -> TaskSequenceOutput:
        """
        Optimize task sequence based on dependencies and goal.
        
        Args:
            input_data: Validated input with tasks and optimization goal
            
        Returns:
            TaskSequenceOutput with optimized sequence
            
        Raises:
            ValueError: If circular dependencies detected or optimization fails
        """
        try:
            warnings = []
            
            # Extract task information
            tasks = input_data.tasks

            # Validate tasks have required fields
            for idx, task in enumerate(tasks):
                if 'task_id' not in task or 'task_name' not in task:
                    raise ValueError(f"Tâche {idx}: doit avoir 'task_id' et 'task_name'")

                # Validate duration
                duration = task.get('estimated_duration_days', 1)
                if not isinstance(duration, (int, float)) or duration <= 0:
                    raise ValueError(f"Tâche '{task['task_name']}': durée invalide ({duration})")

                # Validate dependencies is a list
                dependencies = task.get('dependencies', [])
                if not isinstance(dependencies, list):
                    raise ValueError(f"Tâche '{task['task_name']}': dependencies doit être une liste")
            
            # Build dependency graphs (both forward and reverse)
            dependency_graph, reverse_graph = self._build_dependency_graphs(tasks)

            # Detect cycles
            if self._has_cycle(dependency_graph):
                return TaskSequenceOutput(
                    success=False,
                    optimization_goal=input_data.optimization_goal.value,
                    error="Dépendances circulaires détectées dans les tâches",
                    error_type="circular_dependency"
                )

            # Perform topological sort
            sorted_task_ids = self._topological_sort(dependency_graph, tasks, input_data.optimization_goal)

            # Build transitive closure for efficient parallel task identification
            transitive_closure = self._build_transitive_closure(dependency_graph)

            # Identify parallel tasks
            parallel_groups = self._identify_parallel_tasks(transitive_closure, sorted_task_ids)
            
            # Calculate start/end days
            optimized_tasks, truncation_count = self._calculate_schedule(
                tasks,
                sorted_task_ids,
                parallel_groups,
                dependency_graph
            )

            # Add warning if parallel tasks were truncated
            if truncation_count > 0:
                warnings.append(f"ℹ️ {truncation_count} tâche(s) parallèle(s) supplémentaire(s) non affichée(s)")

            # Calculate total duration
            total_duration = max(task.end_day for task in optimized_tasks) if optimized_tasks else 0

            # Calculate efficiency gain vs critical path without parallelization
            # (not vs sum of all durations, which is misleading)
            critical_path_duration = self._calculate_critical_path_duration(dependency_graph, tasks)
            efficiency_gain = None
            if critical_path_duration > 0 and total_duration < critical_path_duration:
                efficiency_gain = round(
                    ((critical_path_duration - total_duration) / critical_path_duration) * 100,
                    1
                )
                warnings.append(f"✅ Gain d'efficacité: {efficiency_gain}% vs chemin critique séquentiel")
            
            # Add warnings for constraints
            if input_data.constraints:
                warnings.append(f"ℹ️ Contraintes appliquées: {', '.join(input_data.constraints)}")

            # Add warnings for unimplemented optimization goals
            if input_data.optimization_goal == OptimizationConstraint.COST:
                warnings.append("⚠️ Optimisation par coût simplifiée - Données de coût détaillées non disponibles")
            elif input_data.optimization_goal == OptimizationConstraint.WEATHER:
                warnings.append("⚠️ Optimisation météo simplifiée - Prévisions météo non intégrées")

            logger.info(f"✅ Optimized {len(tasks)} tasks, duration: {total_duration} days")
            
            return TaskSequenceOutput(
                success=True,
                optimized_tasks=optimized_tasks,
                total_duration_days=total_duration,
                optimization_goal=input_data.optimization_goal.value,
                efficiency_gain_percent=efficiency_gain,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Task sequence optimization error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de l'optimisation de la séquence: {str(e)}")
    
    def _build_dependency_graphs(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Tuple[DependencyGraph, ReverseDependencyGraph]:
        """
        Build both forward and reverse dependency graphs.

        Forward graph: task_id -> list of task_ids it depends on (prerequisites)
        Reverse graph: task_id -> list of task_ids that depend on it (dependents)

        Returns:
            (forward_graph, reverse_graph)
        """
        forward_graph = defaultdict(list)
        reverse_graph = defaultdict(list)
        task_names_to_ids = {}

        # Build name to ID mapping
        for task in tasks:
            task_names_to_ids[task['task_name']] = task['task_id']

        # Build both graphs
        for task in tasks:
            task_id = task['task_id']
            dependencies = task.get('dependencies', [])

            # Convert dependency names to IDs
            for dep_name in dependencies:
                dep_id = task_names_to_ids.get(dep_name)
                if dep_id:
                    # Forward: task depends on dep_id
                    forward_graph[task_id].append(dep_id)
                    # Reverse: dep_id is depended on by task
                    reverse_graph[dep_id].append(task_id)
                else:
                    logger.warning(f"Task '{task['task_name']}' has unknown dependency: '{dep_name}'")

        return dict(forward_graph), dict(reverse_graph)
    
    def _has_cycle(self, graph: Dict[str, List[str]]) -> bool:
        """
        Detect cycles in dependency graph using DFS.
        
        Returns True if cycle detected, False otherwise.
        """
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def _topological_sort(
        self,
        graph: Dict[str, List[str]],
        tasks: List[Dict[str, Any]],
        optimization_goal: OptimizationConstraint
    ) -> List[str]:
        """
        Perform topological sort with optimization goal.
        
        Uses Kahn's algorithm with priority queue based on optimization goal.
        """
        # Calculate in-degree for each task
        in_degree = defaultdict(int)
        all_tasks = {task['task_id'] for task in tasks}
        
        for task_id in all_tasks:
            in_degree[task_id] = 0
        
        for task_id, dependencies in graph.items():
            for dep in dependencies:
                in_degree[task_id] += 1
        
        # Start with tasks that have no dependencies
        queue = deque([task_id for task_id in all_tasks if in_degree[task_id] == 0])
        sorted_tasks = []
        
        # Create task lookup
        task_lookup = {task['task_id']: task for task in tasks}
        
        while queue:
            # Sort queue based on optimization goal
            queue = deque(sorted(
                queue,
                key=lambda tid: self._get_priority_key(task_lookup[tid], optimization_goal)
            ))
            
            current = queue.popleft()
            sorted_tasks.append(current)
            
            # Reduce in-degree for dependent tasks
            for task_id, dependencies in graph.items():
                if current in dependencies:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        
        return sorted_tasks
    
    def _get_priority_key(self, task: Dict[str, Any], goal: OptimizationConstraint) -> Tuple[int, int]:
        """
        Get priority key for sorting based on optimization goal.

        Returns tuple for sorting (lower is higher priority).

        Note: COST and WEATHER optimizations are simplified.
        Full implementation would require cost data and weather forecasts.
        """
        priority_map = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        priority = priority_map.get(task.get('priority', 'medium'), 2)

        if goal == OptimizationConstraint.TIME:
            # Prioritize shorter tasks
            return (priority, task.get('estimated_duration_days', 1))
        elif goal == OptimizationConstraint.COST:
            # TODO: Implement cost-based optimization when cost data available
            # For now, prioritize by priority only
            return (priority, 0)
        elif goal == OptimizationConstraint.RESOURCES:
            # Prioritize tasks with fewer resource requirements
            resources = len(task.get('resources_required', []))
            return (priority, resources)
        else:
            # WEATHER and default: priority only
            # TODO: Implement weather-based optimization with forecast data
            return (priority, 0)

    def _build_transitive_closure(self, graph: DependencyGraph) -> Dict[str, Set[str]]:
        """
        Build transitive closure of dependency graph.

        For each task, finds all tasks it transitively depends on.
        This enables O(1) dependency checks for parallel task identification.

        Returns:
            Dict mapping task_id -> set of all task_ids it depends on (directly or transitively)
        """
        closure = defaultdict(set)

        # For each node, do DFS to find all reachable nodes
        for start_node in graph:
            visited = set()
            stack = [start_node]

            while stack:
                current = stack.pop()
                if current in visited:
                    continue

                visited.add(current)

                # Add all dependencies
                for dep in graph.get(current, []):
                    stack.append(dep)

            # Remove self from closure
            visited.discard(start_node)
            closure[start_node] = visited

        return dict(closure)

    def _identify_parallel_tasks(
        self,
        transitive_closure: Dict[str, Set[str]],
        sorted_task_ids: List[str]
    ) -> Dict[str, List[str]]:
        """
        Identify tasks that can run in parallel using transitive closure.

        Tasks can run in parallel if:
        1. Neither task depends on the other (directly or transitively)
        2. They don't share critical resources (future enhancement)

        Complexity: O(n²) using precomputed transitive closure
        (vs O(n³) with repeated path searches)

        Returns dict mapping task_id -> list of parallel task_ids
        """
        parallel_groups = defaultdict(list)

        for i, task_id in enumerate(sorted_task_ids):
            task_deps = transitive_closure.get(task_id, set())

            # Check all subsequent tasks
            for j in range(i + 1, len(sorted_task_ids)):
                other_task_id = sorted_task_ids[j]
                other_deps = transitive_closure.get(other_task_id, set())

                # Tasks are parallel if neither depends on the other
                if task_id not in other_deps and other_task_id not in task_deps:
                    parallel_groups[task_id].append(other_task_id)

        return dict(parallel_groups)

    def _calculate_schedule(
        self,
        tasks: List[Dict[str, Any]],
        sorted_task_ids: List[str],
        parallel_groups: Dict[str, List[str]],
        graph: Dict[str, List[str]]
    ) -> Tuple[List[OptimizedTask], int]:
        """
        Calculate start and end days for each task.

        Respects dependencies and identifies parallel execution opportunities.

        Returns:
            (optimized_tasks, truncation_count) - count of parallel tasks not shown
        """
        task_lookup = {task['task_id']: task for task in tasks}
        task_schedule = {}  # task_id -> (start_day, end_day)
        optimized_tasks = []
        total_truncated = 0

        for sequence_order, task_id in enumerate(sorted_task_ids, start=1):
            task = task_lookup[task_id]
            duration = task.get('estimated_duration_days', 1)

            # Calculate earliest start day based on dependencies
            earliest_start = 0
            dependencies = graph.get(task_id, [])

            for dep_id in dependencies:
                if dep_id in task_schedule:
                    dep_end = task_schedule[dep_id][1]
                    earliest_start = max(earliest_start, dep_end)

            start_day = earliest_start
            end_day = start_day + duration

            task_schedule[task_id] = (start_day, end_day)

            # Get parallel tasks (show up to 5, count the rest)
            parallel_task_names = []
            parallel_ids = parallel_groups.get(task_id, [])

            for parallel_id in parallel_ids[:5]:  # Show max 5
                if parallel_id in task_lookup:
                    parallel_task_names.append(task_lookup[parallel_id]['task_name'])

            # Count truncated parallel tasks
            if len(parallel_ids) > 5:
                total_truncated += len(parallel_ids) - 5

            optimized_task = OptimizedTask(
                task_id=task_id,
                task_name=task['task_name'],
                sequence_order=sequence_order,
                start_day=start_day,
                end_day=end_day,
                parallel_tasks=parallel_task_names
            )

            optimized_tasks.append(optimized_task)

        return optimized_tasks, total_truncated

    def _calculate_critical_path_duration(
        self,
        graph: DependencyGraph,
        tasks: List[Dict[str, Any]]
    ) -> int:
        """
        Calculate critical path duration (longest path through dependency graph).

        This is the baseline for efficiency gain calculation.
        """
        task_lookup = {task['task_id']: task for task in tasks}
        memo = {}

        def longest_path(task_id: str) -> int:
            """Calculate longest path from task_id to end"""
            if task_id in memo:
                return memo[task_id]

            task = task_lookup.get(task_id)
            if not task:
                return 0

            duration = task.get('estimated_duration_days', 1)

            # Find longest path through dependencies
            max_dep_path = 0
            for dep_id in graph.get(task_id, []):
                dep_path = longest_path(dep_id)
                max_dep_path = max(max_dep_path, dep_path)

            result = duration + max_dep_path
            memo[task_id] = result
            return result

        # Find maximum path from any task
        max_path = 0
        for task in tasks:
            path_length = longest_path(task['task_id'])
            max_path = max(max_path, path_length)

        return max_path


async def optimize_task_sequence_enhanced(
    tasks: List[Dict[str, Any]],
    optimization_goal: str = "time",
    constraints: Optional[List[str]] = None
) -> str:
    """
    Async wrapper for optimize task sequence tool

    Args:
        tasks: List of tasks to optimize (from generate_planning_tasks)
        optimization_goal: Optimization goal ("time", "cost", "resources", "weather")
        constraints: Additional constraints

    Returns:
        JSON string with optimized sequence
    """
    try:
        # Map string to enum
        goal_map = {
            "time": OptimizationConstraint.TIME,
            "cost": OptimizationConstraint.COST,
            "resources": OptimizationConstraint.RESOURCES,
            "weather": OptimizationConstraint.WEATHER
        }

        goal_enum = goal_map.get(optimization_goal.lower(), OptimizationConstraint.TIME)

        # Validate inputs
        input_data = TaskSequenceInput(
            tasks=tasks,
            optimization_goal=goal_enum,
            constraints=constraints or []
        )

        # Execute service
        service = TaskSequenceService()
        result = await service.optimize_sequence(input_data)

        return result.model_dump_json(indent=2, exclude_none=True)

    except ValueError as e:
        # Validation or business logic error
        error_result = TaskSequenceOutput(
            success=False,
            optimization_goal=optimization_goal,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in optimize_task_sequence_enhanced: {e}", exc_info=True)
        error_result = TaskSequenceOutput(
            success=False,
            optimization_goal=optimization_goal,
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
optimize_task_sequence_tool = StructuredTool.from_function(
    func=optimize_task_sequence_enhanced,
    name="optimize_task_sequence",
    description="""Optimise la séquence des tâches de planification agricole.

Analyse:
- Tri topologique respectant les dépendances
- Identification des tâches parallélisables
- Calcul des dates de début/fin
- Optimisation selon l'objectif (temps, coût, ressources)
- Détection des dépendances circulaires
- Calcul du gain d'efficacité

Retourne une séquence optimisée avec ordonnancement détaillé.""",
    args_schema=TaskSequenceInput,
    return_direct=False,
    coroutine=optimize_task_sequence_enhanced,
    handle_validation_error=True
)


