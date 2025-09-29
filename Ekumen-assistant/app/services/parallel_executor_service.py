"""
Parallel Executor Service - Execute tools and agents in parallel.

Replaces sequential execution with parallel execution using asyncio.gather.

Goal: Reduce tool execution time from 15-30s to 5-10s
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Tool execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class ToolResult:
    """Result from tool execution"""
    tool_name: str
    status: ToolStatus
    result: Any
    execution_time: float
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Plan for parallel execution"""
    parallel_groups: List[List[str]]  # Groups of tools that can run in parallel
    sequential_groups: List[str]       # Tools that must run sequentially
    estimated_time: float


class ParallelExecutorService:
    """
    Service for executing tools and agents in parallel.
    
    Features:
    - Parallel execution of independent tools
    - Dependency-aware execution ordering
    - Timeout handling
    - Error recovery
    - Performance monitoring
    """
    
    def __init__(self):
        self.execution_stats = {
            "total_executions": 0,
            "parallel_executions": 0,
            "sequential_executions": 0,
            "total_time_saved": 0.0
        }
        
        # Tool dependencies (which tools depend on others)
        self.tool_dependencies = {
            "generate_treatment_plan": ["diagnose_disease", "identify_pest"],
            "calculate_planning_costs": ["generate_planning_tasks"],
            "optimize_task_sequence": ["generate_planning_tasks"],
            "generate_farm_report": ["get_farm_data", "calculate_performance_metrics"],
            "generate_planning_report": ["generate_planning_tasks", "calculate_planning_costs"]
        }
        
        # Default timeouts per tool type (seconds)
        self.tool_timeouts = {
            "weather": 5.0,
            "regulatory": 10.0,
            "farm_data": 5.0,
            "crop_health": 3.0,
            "planning": 5.0,
            "sustainability": 5.0
        }
        
        logger.info("Initialized Parallel Executor Service")
    
    async def execute_tools_parallel(
        self,
        tools: List[str],
        tool_executor: Any,
        context: Optional[Dict[str, Any]] = None,
        max_parallel: int = 5
    ) -> Dict[str, ToolResult]:
        """
        Execute tools in parallel with dependency awareness.
        
        Args:
            tools: List of tool names to execute
            tool_executor: Tool executor instance
            context: Execution context
            max_parallel: Maximum number of parallel executions
        
        Returns:
            Dictionary of tool results
        """
        start_time = time.time()
        
        # Create execution plan
        execution_plan = self._create_execution_plan(tools)
        
        logger.info(
            f"📊 Execution plan: "
            f"{len(execution_plan.parallel_groups)} parallel groups, "
            f"{len(execution_plan.sequential_groups)} sequential tools, "
            f"estimated {execution_plan.estimated_time:.1f}s"
        )
        
        results = {}
        
        # Execute parallel groups
        for group_idx, tool_group in enumerate(execution_plan.parallel_groups):
            logger.info(f"⚡ Executing parallel group {group_idx + 1}: {tool_group}")
            
            # Execute tools in this group in parallel
            group_results = await self._execute_tool_group_parallel(
                tool_group,
                tool_executor,
                context,
                results  # Pass previous results for dependencies
            )
            
            results.update(group_results)
        
        # Execute sequential tools
        for tool_name in execution_plan.sequential_groups:
            logger.info(f"🔄 Executing sequential tool: {tool_name}")
            
            tool_result = await self._execute_single_tool(
                tool_name,
                tool_executor,
                context,
                results
            )
            
            results[tool_name] = tool_result
        
        # Calculate time saved
        total_time = time.time() - start_time
        sequential_time = sum(r.execution_time for r in results.values())
        time_saved = sequential_time - total_time
        
        self.execution_stats["total_executions"] += 1
        self.execution_stats["parallel_executions"] += len(execution_plan.parallel_groups)
        self.execution_stats["sequential_executions"] += len(execution_plan.sequential_groups)
        self.execution_stats["total_time_saved"] += time_saved
        
        logger.info(
            f"✅ Executed {len(tools)} tools in {total_time:.2f}s "
            f"(sequential would be {sequential_time:.2f}s, saved {time_saved:.2f}s)"
        )
        
        return results
    
    def _create_execution_plan(self, tools: List[str]) -> ExecutionPlan:
        """
        Create execution plan with parallel groups.
        
        Groups tools that can run in parallel vs those that must run sequentially.
        """
        # Separate tools with dependencies from independent tools
        independent_tools = []
        dependent_tools = []
        
        for tool in tools:
            if tool in self.tool_dependencies:
                dependent_tools.append(tool)
            else:
                independent_tools.append(tool)
        
        # Create parallel groups
        parallel_groups = []
        
        # Group 1: All independent tools can run in parallel
        if independent_tools:
            parallel_groups.append(independent_tools)
        
        # Dependent tools run sequentially (for now - could be optimized)
        sequential_groups = dependent_tools
        
        # Estimate execution time
        # Parallel: max of group times
        # Sequential: sum of tool times
        parallel_time = max([self._estimate_tool_time(t) for t in independent_tools]) if independent_tools else 0
        sequential_time = sum([self._estimate_tool_time(t) for t in dependent_tools])
        estimated_time = parallel_time + sequential_time
        
        return ExecutionPlan(
            parallel_groups=parallel_groups,
            sequential_groups=sequential_groups,
            estimated_time=estimated_time
        )
    
    async def _execute_tool_group_parallel(
        self,
        tool_group: List[str],
        tool_executor: Any,
        context: Optional[Dict[str, Any]],
        previous_results: Dict[str, ToolResult]
    ) -> Dict[str, ToolResult]:
        """Execute a group of tools in parallel"""
        
        # Create tasks for all tools in the group
        tasks = []
        tool_names = []
        
        for tool_name in tool_group:
            task = self._execute_single_tool(
                tool_name,
                tool_executor,
                context,
                previous_results
            )
            tasks.append(task)
            tool_names.append(tool_name)
        
        # Execute all tasks in parallel
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        results = {}
        for tool_name, result in zip(tool_names, results_list):
            if isinstance(result, Exception):
                logger.error(f"Tool {tool_name} failed with exception: {result}")
                results[tool_name] = ToolResult(
                    tool_name=tool_name,
                    status=ToolStatus.FAILED,
                    result=None,
                    execution_time=0.0,
                    error=str(result)
                )
            else:
                results[tool_name] = result
        
        return results
    
    async def _execute_single_tool(
        self,
        tool_name: str,
        tool_executor: Any,
        context: Optional[Dict[str, Any]],
        previous_results: Dict[str, ToolResult]
    ) -> ToolResult:
        """
        Execute a single tool with timeout and error handling.
        """
        start_time = time.time()
        
        # Get timeout for this tool type
        tool_type = self._get_tool_type(tool_name)
        timeout = self.tool_timeouts.get(tool_type, 10.0)
        
        try:
            # Execute tool with timeout
            result = await asyncio.wait_for(
                self._call_tool(tool_name, tool_executor, context, previous_results),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.SUCCESS,
                result=result,
                execution_time=execution_time
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"Tool {tool_name} timed out after {timeout}s")
            
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.TIMEOUT,
                result=None,
                execution_time=execution_time,
                error=f"Timeout after {timeout}s"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool {tool_name} failed: {e}")
            
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.FAILED,
                result=None,
                execution_time=execution_time,
                error=str(e)
            )
    
    async def _call_tool(
        self,
        tool_name: str,
        tool_executor: Any,
        context: Optional[Dict[str, Any]],
        previous_results: Dict[str, ToolResult]
    ) -> Any:
        """
        Call the actual tool.

        Supports multiple tool executor interfaces:
        - ToolRegistryService (preferred)
        - Any object with execute_tool method
        - Callable function
        """
        # Try ToolRegistryService interface (preferred)
        if hasattr(tool_executor, 'execute_tool'):
            return await tool_executor.execute_tool(
                tool_name,
                context=context,
                previous_results=previous_results
            )
        # Try callable interface
        elif callable(tool_executor):
            return await tool_executor(
                tool_name,
                context=context,
                previous_results=previous_results
            )
        else:
            raise ValueError(f"Invalid tool executor: {tool_executor}")
    
    def _get_tool_type(self, tool_name: str) -> str:
        """Get tool type from tool name"""
        # Extract type from tool name (e.g., "get_weather_data" -> "weather")
        if "weather" in tool_name.lower():
            return "weather"
        elif "regulatory" in tool_name.lower() or "amm" in tool_name.lower():
            return "regulatory"
        elif "farm" in tool_name.lower() or "data" in tool_name.lower():
            return "farm_data"
        elif "crop" in tool_name.lower() or "disease" in tool_name.lower() or "pest" in tool_name.lower():
            return "crop_health"
        elif "planning" in tool_name.lower() or "task" in tool_name.lower():
            return "planning"
        elif "sustainability" in tool_name.lower() or "carbon" in tool_name.lower():
            return "sustainability"
        else:
            return "unknown"
    
    def _estimate_tool_time(self, tool_name: str) -> float:
        """Estimate execution time for a tool"""
        tool_type = self._get_tool_type(tool_name)
        
        # Estimated times based on tool type
        estimates = {
            "weather": 2.0,
            "regulatory": 3.0,
            "farm_data": 2.0,
            "crop_health": 1.0,
            "planning": 2.0,
            "sustainability": 2.0,
            "unknown": 3.0
        }
        
        return estimates.get(tool_type, 3.0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            **self.execution_stats,
            "avg_time_saved": (
                self.execution_stats["total_time_saved"] / self.execution_stats["total_executions"]
                if self.execution_stats["total_executions"] > 0 else 0
            )
        }

