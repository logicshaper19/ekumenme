"""
Agricultural Orchestrator - Single Purpose Component

Job: Orchestrate agricultural agent workflows and coordinate responses.
Input: User requests and agent configurations
Output: Coordinated agent responses

This component does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WorkflowStep:
    """Workflow step definition."""
    step_id: str
    agent_type: str
    input_data: Dict[str, Any]
    expected_output: str
    dependencies: List[str]

@dataclass
class WorkflowResult:
    """Workflow execution result."""
    workflow_id: str
    status: str
    results: Dict[str, Any]
    execution_time: float
    errors: List[str]

class AgriculturalOrchestrator:
    """
    Orchestrator for agricultural agent workflows.
    
    Job: Orchestrate agricultural agent workflows and coordinate responses.
    Input: User requests and agent configurations
    Output: Coordinated agent responses
    """
    
    def __init__(self):
        self.workflows = {}
        self.active_workflows = {}
    
    def create_workflow(self, workflow_id: str, steps: List[WorkflowStep]) -> Dict[str, Any]:
        """
        Create a new workflow.
        
        Args:
            workflow_id: Unique workflow identifier
            steps: List of workflow steps
            
        Returns:
            Workflow creation result
        """
        try:
            # Validate workflow steps
            validation_result = self._validate_workflow_steps(steps)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Workflow validation failed: {validation_result['errors']}"
                }
            
            # Store workflow
            self.workflows[workflow_id] = {
                "steps": steps,
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "steps_count": len(steps),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow creation error: {e}")
            return {
                "success": False,
                "error": f"Failed to create workflow: {str(e)}"
            }
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any] = None) -> WorkflowResult:
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow identifier
            input_data: Input data for workflow execution
            
        Returns:
            Workflow execution result
        """
        start_time = datetime.now()
        
        try:
            if workflow_id not in self.workflows:
                return WorkflowResult(
                    workflow_id=workflow_id,
                    status="failed",
                    results={},
                    execution_time=0.0,
                    errors=[f"Workflow {workflow_id} not found"]
                )
            
            workflow = self.workflows[workflow_id]
            steps = workflow["steps"]
            
            # Execute workflow steps
            results = {}
            errors = []
            
            for step in steps:
                try:
                    # Check dependencies
                    if not self._check_dependencies(step, results):
                        errors.append(f"Step {step.step_id}: Dependencies not met")
                        continue
                    
                    # Execute step (simplified - in real implementation would call actual agents)
                    step_result = self._execute_step(step, input_data, results)
                    results[step.step_id] = step_result
                    
                except Exception as e:
                    error_msg = f"Step {step.step_id} failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Determine final status
            status = "completed" if not errors else "failed"
            
            return WorkflowResult(
                workflow_id=workflow_id,
                status=status,
                results=results,
                execution_time=execution_time,
                errors=errors
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Workflow execution error: {e}")
            return WorkflowResult(
                workflow_id=workflow_id,
                status="failed",
                results={},
                execution_time=execution_time,
                errors=[f"Workflow execution failed: {str(e)}"]
            )
    
    def _validate_workflow_steps(self, steps: List[WorkflowStep]) -> Dict[str, Any]:
        """Validate workflow steps."""
        errors = []
        
        # Check for duplicate step IDs
        step_ids = [step.step_id for step in steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Duplicate step IDs found")
        
        # Check dependencies
        for step in steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    errors.append(f"Step {step.step_id}: Dependency {dep} not found")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _check_dependencies(self, step: WorkflowStep, results: Dict[str, Any]) -> bool:
        """Check if step dependencies are met."""
        for dep in step.dependencies:
            if dep not in results:
                return False
        return True
    
    def _execute_step(self, step: WorkflowStep, input_data: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow step."""
        # Simplified step execution - in real implementation would call actual agents
        return {
            "step_id": step.step_id,
            "agent_type": step.agent_type,
            "output": f"Mock output from {step.agent_type} agent",
            "executed_at": datetime.now().isoformat()
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status."""
        if workflow_id not in self.workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        workflow = self.workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "status": workflow["status"],
            "created_at": workflow["created_at"],
            "steps_count": len(workflow["steps"])
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows."""
        return [
            {
                "workflow_id": workflow_id,
                "status": workflow["status"],
                "created_at": workflow["created_at"],
                "steps_count": len(workflow["steps"])
            }
            for workflow_id, workflow in self.workflows.items()
        ]
