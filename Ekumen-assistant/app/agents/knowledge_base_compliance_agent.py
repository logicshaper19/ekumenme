"""
Knowledge Base Compliance Agent - Using existing regulatory tools and structured outputs for reliable validation

This agent:
1. Uses correct LangChain ReAct prompt format with {tools} and {tool_names}
2. Adds Pydantic models for type safety (internal, backward compatible)
3. Enhanced metrics with token/cost tracking
4. Retry logic and better error handling
5. Batch processing capability
6. 100% backward compatible - returns same dict structure
"""

import logging
from typing import Dict, List, Any, Optional, Literal
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.callbacks import get_openai_callback

from ..tools.regulatory_agent import (
    database_integrated_amm_tool,
    check_regulatory_compliance_tool,
    get_safety_guidelines_tool,
    check_environmental_regulations_tool
)
from ..prompts.knowledge_base_compliance_prompts import get_compliance_agent_prompt
from ..core.config import settings

logger = logging.getLogger(__name__)


# Internal Pydantic models (not exposed to maintain backward compatibility)
class ComplianceDecision(str, Enum):
    """Enumeration of possible compliance decisions."""
    AUTO_APPROVE = "auto_approve"
    FLAG_FOR_REVIEW = "flag_for_review"
    UNCERTAIN = "uncertain"


class ComplianceResult(BaseModel):
    """Internal structured compliance validation result."""
    decision: ComplianceDecision
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('confidence')
    def validate_confidence(cls, v, values):
        """Ensure confidence aligns with decision type."""
        decision = values.get('decision')
        if decision == ComplianceDecision.AUTO_APPROVE and v < 0.7:
            logger.warning(f"Low confidence ({v}) for AUTO_APPROVE decision")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "violations": self.violations,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "tool_results": self.tool_results,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    class Config:
        use_enum_values = True


class ValidationMetrics(BaseModel):
    """Performance metrics for the compliance agent."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_iterations: float = 0.0
    avg_tokens_used: float = 0.0
    avg_cost: float = 0.0
    tool_usage: Dict[str, int] = Field(default_factory=lambda: defaultdict(int))
    error_types: Dict[str, int] = Field(default_factory=lambda: defaultdict(int))
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class KnowledgeBaseComplianceAgent:
    """
    Knowledge Base Compliance Agent using existing production-ready regulatory tools.
    
    Enhanced with:
    - Correct LangChain ReAct prompt format
    - Pydantic models for internal type safety
    - Token and cost tracking
    - Automatic retry logic
    - Batch processing
    - Backward compatible dict returns
    
    Tools:
    - lookup_amm_database_enhanced: Look up AMM codes using real EPHY database
    - check_regulatory_compliance: Check compliance with French agricultural regulations
    - get_safety_guidelines: Get safety guidelines with PPE recommendations
    - check_environmental_regulations_enhanced: Check environmental compliance with ZNT zones
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        config: Optional[Dict[str, Any]] = None,
        enable_dynamic_examples: bool = False,
        max_iterations: int = 8,  # Optimized for document validation
        enable_metrics: bool = True,
        max_retries: int = 2,  # NEW: retry logic
        timeout: float = 30.0
    ):
        """
        Initialize Knowledge Base Compliance Agent.

        Args:
            llm: Language model to use (if None, creates default ChatOpenAI)
            tools: List of tools to use (if None, uses 4 production regulatory tools)
            config: Additional configuration (optional)
            enable_dynamic_examples: Whether to include few-shot examples (default False)
            max_iterations: Maximum ReAct iterations (default 8 for document validation)
            enable_metrics: Whether to track performance metrics
            max_retries: Number of retries on failure (NEW)
            timeout: Execution timeout in seconds
        """
        # Use provided LLM or create default
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",  # Efficient model for document validation
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )

        # Use provided tools or default production tools
        self.tools = tools or [
            database_integrated_amm_tool,
            check_regulatory_compliance_tool,
            get_safety_guidelines_tool,
            check_environmental_regulations_tool
        ]

        self.config = config or {}
        self.enable_dynamic_examples = enable_dynamic_examples
        self.max_iterations = max_iterations
        self.enable_metrics = enable_metrics
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize metrics tracking (enhanced with Pydantic)
        if self.enable_metrics:
            self.metrics = ValidationMetrics()
        else:
            self.metrics = None

        # Create LangChain ReAct agent with compliance-specific prompt
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=self.max_iterations,
            max_execution_time=self.timeout
        )

        logger.info(
            f"✅ Knowledge Base Compliance Agent initialized: "
            f"{len(self.tools)} tools, "
            f"max_iterations={self.max_iterations}, "
            f"retries={self.max_retries}, "
            f"examples={'enabled' if self.enable_dynamic_examples else 'disabled'}, "
            f"metrics={'enabled' if self.enable_metrics else 'disabled'}"
        )
    
    def _create_agent(self):
        """Create LangChain ReAct agent with compliance-specific prompt."""
        prompt = self._get_prompt_template()
        return create_react_agent(self.llm, self.tools, prompt)

    def _get_prompt_template(self) -> ChatPromptTemplate:
        """
        Get compliance-specific prompt template for ReAct agent.
        Uses the specialized compliance prompt with proper French regulatory expertise.
        
        Returns:
            ChatPromptTemplate configured for knowledge base compliance validation
        """

        return get_compliance_agent_prompt(include_examples=self.enable_dynamic_examples)
    
    def _update_metrics(
        self,
        success: bool,
        error_type: Optional[str] = None,
        iterations: int = 0,
        tools_used: Optional[List[str]] = None,
        tokens_used: int = 0,
        cost: float = 0.0
    ):
        """
        Update performance metrics.

        Args:
            success: Whether the operation was successful
            error_type: Type of error if any
            iterations: Number of iterations used
            tools_used: List of tools used in the operation
            tokens_used: Number of tokens consumed (NEW)
            cost: Cost in USD (NEW)
        """
        if not self.enable_metrics or not self.metrics:
            return

        self.metrics.total_calls += 1
        
        if success:
            self.metrics.successful_calls += 1
        else:
            self.metrics.failed_calls += 1
            if error_type:
                self.metrics.error_types[error_type] += 1

        # Update averages
        n = self.metrics.total_calls
        self.metrics.avg_iterations = (
            (self.metrics.avg_iterations * (n - 1) + iterations) / n
        )
        self.metrics.avg_tokens_used = (
            (self.metrics.avg_tokens_used * (n - 1) + tokens_used) / n
        )
        self.metrics.avg_cost = (
            (self.metrics.avg_cost * (n - 1) + cost) / n
        )

        # Update tool usage
        if tools_used:
            for tool in tools_used:
                self.metrics.tool_usage[tool] += 1

        self.metrics.last_updated = datetime.utcnow()

    async def validate_document(
        self,
        document_content: str,
        document_type: str,
        document_id: str,
        organization_id: Optional[str] = None,
        retry_count: int = 0  # NEW: internal retry counter
    ) -> Dict[str, Any]:
        """
        Validate document for regulatory compliance using existing regulatory tools
        
        Args:
            document_content: Full text content of the document
            document_type: Type of document (manual, product_spec, etc.)
            document_id: Unique identifier for the document
            organization_id: Optional organization identifier
            retry_count: Internal retry counter (do not set manually)
            
        Returns:
            Dict containing compliance decision and detailed results
            Format: {
                "decision": str,  # "auto_approve", "flag_for_review", or "uncertain"
                "confidence": float,
                "reason": str,
                "violations": List[str],
                "warnings": List[str],
                "recommendations": List[str],
                "tool_results": Dict[str, Any],
                "timestamp": str,
                "metadata": Dict[str, Any]  # NEW: includes tokens, cost, iterations
            }
        """
        try:
            logger.info(f"Starting compliance validation for document {document_id} (attempt {retry_count + 1})")
            
            # Execute agent with token tracking
            tokens_used = 0
            cost = 0.0
            
            with get_openai_callback() as cb:
                result = await self.agent_executor.ainvoke({
                    "document_content": document_content,
                    "document_type": document_type,
                    "document_id": document_id
                })
                tokens_used = cb.total_tokens
                cost = cb.total_cost
            
            # Parse agent response and extract compliance decision
            compliance_result = self._parse_agent_response(result, document_id)
            
            # Add metadata
            compliance_result.metadata.update({
                "document_id": document_id,
                "document_type": document_type,
                "organization_id": organization_id,
                "iterations": len(result.get("intermediate_steps", [])),
                "tokens_used": tokens_used,
                "cost": cost,
                "retry_count": retry_count
            })
            
            # Update metrics
            if self.enable_metrics:
                tools_used = []
                for step in result.get("intermediate_steps", []):
                    if len(step) >= 1:
                        action = step[0]
                        tool_name = action.tool if hasattr(action, 'tool') else "unknown"
                        tools_used.append(tool_name)
                
                self._update_metrics(
                    success=True,
                    iterations=len(result.get("intermediate_steps", [])),
                    tools_used=tools_used,
                    tokens_used=tokens_used,
                    cost=cost
                )
            
            logger.info(
                f"✅ Compliance validation completed for document {document_id}: "
                f"{compliance_result.decision} (confidence: {compliance_result.confidence:.2f})"
            )
            
            # Return as dict for backward compatibility
            return compliance_result.to_dict()
            
        except Exception as e:
            logger.error(f"❌ Error in compliance validation for document {document_id}: {e}")
            
            # Retry logic (NEW)
            if retry_count < self.max_retries:
                logger.info(f"Retrying validation for {document_id} ({retry_count + 1}/{self.max_retries})")
                return await self.validate_document(
                    document_content,
                    document_type,
                    document_id,
                    organization_id,
                    retry_count + 1
                )
            
            # Update metrics
            if self.enable_metrics:
                self._update_metrics(
                    success=False,
                    error_type=type(e).__name__
                )
            
            # Return error result as dict
            return {
                "decision": "uncertain",
                "confidence": 0.0,
                "reason": f"Validation failed after {self.max_retries + 1} attempts: {str(e)}",
                "violations": [],
                "warnings": [f"Validation error: {type(e).__name__}"],
                "recommendations": ["Manual review required due to validation error"],
                "tool_results": {},
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "document_id": document_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            }
    
    def _parse_agent_response(self, agent_result: Dict[str, Any], document_id: str) -> ComplianceResult:
        """
        Parse agent response and extract compliance decision
        
        Args:
            agent_result: Raw result from agent execution
            document_id: Document identifier for logging
            
        Returns:
            ComplianceResult (internal Pydantic model)
        """
        try:
            # Extract the final response from the agent
            final_response = agent_result.get("output", "")
            
            # Parse decision from response with better pattern matching
            decision = ComplianceDecision.UNCERTAIN
            confidence = 0.5
            
            response_upper = final_response.upper()
            if "DECISION: AUTO-APPROVE" in response_upper or ("AUTO-APPROVE" in response_upper and "FLAG" not in response_upper):
                decision = ComplianceDecision.AUTO_APPROVE
                confidence = 0.9
            elif "DECISION: FLAG" in response_upper or "FLAG FOR REVIEW" in response_upper:
                decision = ComplianceDecision.FLAG_FOR_REVIEW
                confidence = 0.8
            elif "DECISION: UNCERTAIN" in response_upper or "UNCERTAIN" in response_upper:
                decision = ComplianceDecision.UNCERTAIN
                confidence = 0.5
            
            # Extract confidence if explicitly stated
            if "CONFIDENCE:" in response_upper:
                try:
                    conf_line = [l for l in final_response.split("\n") if "CONFIDENCE:" in l.upper()][0]
                    confidence = float(conf_line.split(":")[-1].strip())
                except (ValueError, IndexError):
                    pass
            
            # Extract structured information
            violations = self._extract_list_from_response(final_response, "VIOLATIONS:")
            warnings = self._extract_list_from_response(final_response, "WARNINGS:")
            recommendations = self._extract_list_from_response(final_response, "RECOMMENDATIONS:")
            
            # Extract violations and warnings from tool results
            tool_results = {}
            if "intermediate_steps" in agent_result:
                for step in agent_result["intermediate_steps"]:
                    if len(step) >= 2:
                        action, observation = step[0], step[1]
                        tool_name = action.tool if hasattr(action, 'tool') else "unknown"
                        tool_results[tool_name] = observation
                        
                        # Extract violations and warnings from tool outputs
                        if isinstance(observation, dict):
                            if "violations" in observation and observation["violations"]:
                                violations.extend(observation["violations"])
                            if "warnings" in observation and observation["warnings"]:
                                warnings.extend(observation["warnings"])
                            if "recommendations" in observation and observation["recommendations"]:
                                recommendations.extend(observation["recommendations"])
            
            return ComplianceResult(
                decision=decision,
                confidence=confidence,
                reason=final_response,
                violations=violations,
                warnings=warnings,
                recommendations=recommendations,
                tool_results=tool_results
            )
            
        except Exception as e:
            logger.error(f"Error parsing agent response for {document_id}: {e}")
            return ComplianceResult(
                decision=ComplianceDecision.UNCERTAIN,
                confidence=0.0,
                reason=f"Failed to parse agent response: {str(e)}",
                violations=[],
                warnings=["Response parsing error"],
                recommendations=["Manual review required"],
                tool_results={}
            )
    
    def _extract_list_from_response(self, response: str, section_key: str) -> List[str]:
        """Extract list items from a response section."""
        items = []
        in_section = False
        
        for line in response.split("\n"):
            if section_key in line.upper():
                in_section = True
                # Check if items are on the same line
                remainder = line.split(":", 1)[-1].strip()
                if remainder and remainder.lower() != "none":
                    items.append(remainder)
                continue
            
            if in_section:
                # Stop at next section or empty line
                if ":" in line and line.strip().endswith(":") and line.strip().isupper():
                    break
                if line.strip():
                    # Remove bullet points and numbering
                    clean_line = line.strip().lstrip("-•*123456789. ")
                    if clean_line and clean_line.lower() != "none":
                        items.append(clean_line)
                else:
                    break
        
        return items
    
    async def get_compliance_summary(self, document_id: str) -> Dict[str, Any]:
        """
        Get a summary of compliance validation results for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Summary of compliance status
        """
        # This would typically query a database for stored results
        # For now, return a placeholder
        return {
            "document_id": document_id,
            "status": "pending",
            "last_validated": None,
            "compliance_score": None
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the agent.
        
        Returns:
            Dictionary containing performance metrics
        """
        if not self.enable_metrics or not self.metrics:
            return {"metrics_enabled": False}
        
        # Convert Pydantic model to dict
        return self.metrics.dict()
    
    def reset_metrics(self):
        """Reset performance metrics (NEW)."""
        if self.enable_metrics:
            self.metrics = ValidationMetrics()
            logger.info("Metrics reset")
    
    async def batch_validate(
        self,
        documents: List[Dict[str, str]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple documents concurrently (NEW).
        
        Args:
            documents: List of dicts with document_content, document_type, document_id
            max_concurrent: Maximum concurrent validations
            
        Returns:
            List of compliance result dicts
        """
        import asyncio
        from asyncio import Semaphore
        
        semaphore = Semaphore(max_concurrent)
        
        async def validate_with_semaphore(doc):
            async with semaphore:
                return await self.validate_document(
                    doc["document_content"],
                    doc["document_type"],
                    doc["document_id"],
                    doc.get("organization_id")
                )
        
        results = await asyncio.gather(
            *[validate_with_semaphore(doc) for doc in documents],
            return_exceptions=True
        )
        
        # Convert exceptions to uncertain results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "decision": "uncertain",
                    "confidence": 0.0,
                    "reason": f"Batch validation error: {str(result)}",
                    "violations": [],
                    "warnings": [],
                    "recommendations": ["Manual review required"],
                    "tool_results": {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {"document_id": documents[i].get("document_id", "unknown")}
                })
            else:
                processed_results.append(result)
        
        return processed_results