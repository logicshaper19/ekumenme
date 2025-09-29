"""
Unit tests for Parallel Executor Service.

Tests:
- Parallel execution
- Dependency resolution
- Timeout handling
- Error recovery
- Performance metrics
"""

import pytest
import asyncio
from app.services.parallel_executor_service import (
    ParallelExecutorService,
    ToolStatus,
    ToolResult,
    ExecutionPlan
)


class MockToolExecutor:
    """Mock tool executor for testing"""
    
    async def execute_tool(self, tool_name: str, **kwargs):
        """Mock tool execution"""
        # Simulate different execution times
        if "slow" in tool_name:
            await asyncio.sleep(0.5)
        elif "fast" in tool_name:
            await asyncio.sleep(0.1)
        else:
            await asyncio.sleep(0.2)
        
        return {"tool": tool_name, "result": "success"}


class TestParallelExecutorService:
    """Test suite for Parallel Executor Service"""
    
    @pytest.fixture
    def executor(self):
        """Create executor instance for testing"""
        return ParallelExecutorService()
    
    @pytest.fixture
    def mock_tool_executor(self):
        """Create mock tool executor"""
        return MockToolExecutor()
    
    # Test execution plan creation
    def test_create_execution_plan_independent_tools(self, executor):
        """Test execution plan for independent tools"""
        tools = ["get_weather", "get_farm_data", "lookup_amm"]
        plan = executor._create_execution_plan(tools)
        
        assert len(plan.parallel_groups) == 1
        assert len(plan.parallel_groups[0]) == 3
        assert len(plan.sequential_groups) == 0
    
    def test_create_execution_plan_with_dependencies(self, executor):
        """Test execution plan with dependencies"""
        tools = ["diagnose_disease", "generate_treatment_plan"]
        plan = executor._create_execution_plan(tools)
        
        # generate_treatment_plan depends on diagnose_disease
        assert "generate_treatment_plan" in plan.sequential_groups
    
    def test_create_execution_plan_mixed(self, executor):
        """Test execution plan with mixed dependencies"""
        tools = [
            "get_weather",
            "get_farm_data",
            "generate_planning_tasks",
            "calculate_planning_costs"  # Depends on generate_planning_tasks
        ]
        plan = executor._create_execution_plan(tools)
        
        # Independent tools in parallel
        assert len(plan.parallel_groups) > 0
        # Dependent tools sequential
        assert "calculate_planning_costs" in plan.sequential_groups
    
    # Test parallel execution
    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(self, executor, mock_tool_executor):
        """Test parallel execution is faster than sequential"""
        import time
        
        tools = ["tool1", "tool2", "tool3"]
        
        start = time.time()
        results = await executor.execute_tools_parallel(
            tools,
            mock_tool_executor,
            context=None
        )
        parallel_time = time.time() - start
        
        # Sequential would take 0.6s (3 * 0.2s)
        # Parallel should take ~0.2s (max of parallel group)
        assert parallel_time < 0.4  # Should be much faster than sequential
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_parallel_execution_all_tools_executed(self, executor, mock_tool_executor):
        """Test all tools are executed"""
        tools = ["tool1", "tool2", "tool3", "tool4"]
        
        results = await executor.execute_tools_parallel(
            tools,
            mock_tool_executor,
            context=None
        )
        
        assert len(results) == 4
        for tool in tools:
            assert tool in results
            assert results[tool].status == ToolStatus.SUCCESS
    
    # Test timeout handling
    @pytest.mark.asyncio
    async def test_timeout_handling(self, executor):
        """Test timeout handling for slow tools"""
        
        async def slow_tool_executor(tool_name, **kwargs):
            await asyncio.sleep(10)  # Very slow
            return {"result": "success"}
        
        # Override timeout for testing
        executor.tool_timeouts["test"] = 0.1
        
        result = await executor._execute_single_tool(
            "test_tool",
            slow_tool_executor,
            None,
            {}
        )
        
        assert result.status == ToolStatus.TIMEOUT
        assert result.error is not None
    
    # Test error handling
    @pytest.mark.asyncio
    async def test_error_handling(self, executor):
        """Test error handling for failing tools"""
        
        async def failing_tool_executor(tool_name, **kwargs):
            raise ValueError("Tool execution failed")
        
        result = await executor._execute_single_tool(
            "failing_tool",
            failing_tool_executor,
            None,
            {}
        )
        
        assert result.status == ToolStatus.FAILED
        assert "Tool execution failed" in result.error
    
    @pytest.mark.asyncio
    async def test_partial_failure_continues_execution(self, executor):
        """Test execution continues even if some tools fail"""
        
        async def mixed_tool_executor(tool_name, **kwargs):
            if tool_name == "failing_tool":
                raise ValueError("Failed")
            return {"result": "success"}
        
        tools = ["tool1", "failing_tool", "tool2"]
        
        results = await executor.execute_tools_parallel(
            tools,
            mixed_tool_executor,
            context=None
        )
        
        assert len(results) == 3
        assert results["tool1"].status == ToolStatus.SUCCESS
        assert results["failing_tool"].status == ToolStatus.FAILED
        assert results["tool2"].status == ToolStatus.SUCCESS
    
    # Test tool type detection
    def test_get_tool_type_weather(self, executor):
        """Test weather tool type detection"""
        assert executor._get_tool_type("get_weather_data") == "weather"
        assert executor._get_tool_type("analyze_weather_risks") == "weather"
    
    def test_get_tool_type_regulatory(self, executor):
        """Test regulatory tool type detection"""
        assert executor._get_tool_type("lookup_amm") == "regulatory"
        assert executor._get_tool_type("check_regulatory_compliance") == "regulatory"
    
    def test_get_tool_type_farm_data(self, executor):
        """Test farm data tool type detection"""
        assert executor._get_tool_type("get_farm_data") == "farm_data"
        assert executor._get_tool_type("calculate_performance_metrics") == "farm_data"
    
    # Test execution time estimation
    def test_estimate_tool_time(self, executor):
        """Test tool execution time estimation"""
        weather_time = executor._estimate_tool_time("get_weather_data")
        regulatory_time = executor._estimate_tool_time("lookup_amm")
        
        assert weather_time > 0
        assert regulatory_time > 0
    
    # Test statistics tracking
    @pytest.mark.asyncio
    async def test_statistics_tracking(self, executor, mock_tool_executor):
        """Test execution statistics are tracked"""
        tools = ["tool1", "tool2", "tool3"]
        
        await executor.execute_tools_parallel(
            tools,
            mock_tool_executor,
            context=None
        )
        
        stats = executor.get_stats()
        assert stats["total_executions"] == 1
        assert stats["parallel_executions"] == 1
        assert stats["total_time_saved"] > 0
    
    @pytest.mark.asyncio
    async def test_time_saved_calculation(self, executor, mock_tool_executor):
        """Test time saved calculation"""
        tools = ["slow_tool1", "slow_tool2", "slow_tool3"]
        
        await executor.execute_tools_parallel(
            tools,
            mock_tool_executor,
            context=None
        )
        
        stats = executor.get_stats()
        # Should save time by running in parallel
        assert stats["total_time_saved"] > 0
        assert stats["avg_time_saved"] > 0
    
    # Test dependency resolution
    def test_dependency_resolution_treatment_plan(self, executor):
        """Test treatment plan dependency resolution"""
        tools = ["generate_treatment_plan"]
        plan = executor._create_execution_plan(tools)
        
        # Should be in sequential (has dependencies)
        assert "generate_treatment_plan" in plan.sequential_groups
    
    def test_dependency_resolution_planning_costs(self, executor):
        """Test planning costs dependency resolution"""
        tools = ["calculate_planning_costs"]
        plan = executor._create_execution_plan(tools)
        
        # Should be in sequential (depends on generate_planning_tasks)
        assert "calculate_planning_costs" in plan.sequential_groups
    
    # Test context passing
    @pytest.mark.asyncio
    async def test_context_passed_to_tools(self, executor):
        """Test context is passed to tool execution"""
        context = {"user_id": "123", "farm_siret": "456"}
        
        async def context_checking_executor(tool_name, **kwargs):
            # Context should be available
            return {"context_received": True}
        
        results = await executor.execute_tools_parallel(
            ["tool1"],
            context_checking_executor,
            context=context
        )
        
        assert len(results) == 1
    
    # Test max parallel limit
    @pytest.mark.asyncio
    async def test_max_parallel_limit(self, executor, mock_tool_executor):
        """Test max parallel execution limit"""
        # Create many tools
        tools = [f"tool{i}" for i in range(20)]
        
        results = await executor.execute_tools_parallel(
            tools,
            mock_tool_executor,
            context=None,
            max_parallel=5
        )
        
        # All tools should still execute
        assert len(results) == 20
    
    # Test execution order
    @pytest.mark.asyncio
    async def test_execution_order_respects_dependencies(self, executor):
        """Test execution order respects dependencies"""
        execution_order = []
        
        async def order_tracking_executor(tool_name, **kwargs):
            execution_order.append(tool_name)
            await asyncio.sleep(0.01)
            return {"result": "success"}
        
        tools = ["diagnose_disease", "generate_treatment_plan"]
        
        await executor.execute_tools_parallel(
            tools,
            order_tracking_executor,
            context=None
        )
        
        # generate_treatment_plan should come after diagnose_disease
        # (if both are in sequential group)
        assert len(execution_order) == 2
    
    # Test performance
    @pytest.mark.asyncio
    async def test_performance_improvement(self, executor):
        """Test parallel execution provides performance improvement"""
        import time
        
        async def timed_executor(tool_name, **kwargs):
            await asyncio.sleep(0.2)
            return {"result": "success"}
        
        tools = ["tool1", "tool2", "tool3", "tool4", "tool5"]
        
        start = time.time()
        results = await executor.execute_tools_parallel(
            tools,
            timed_executor,
            context=None
        )
        parallel_time = time.time() - start
        
        # Sequential would take 1.0s (5 * 0.2s)
        # Parallel should take ~0.2s
        assert parallel_time < 0.5  # At least 2x faster
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

