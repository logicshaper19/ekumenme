"""
Error Recovery Service for Agricultural AI
Built-in fallback systems and comprehensive error handling
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
import json
import traceback
from enum import Enum
from dataclasses import dataclass, asdict

from app.core.config import settings

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategy types"""
    RETRY = "retry"
    FALLBACK = "fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"
    ALTERNATIVE_SERVICE = "alternative_service"


@dataclass
class ErrorContext:
    """Error context information"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: datetime
    service_name: str
    operation: str
    user_id: Optional[str] = None
    query: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    recovery_attempts: int = 0


@dataclass
class RecoveryResult:
    """Recovery operation result"""
    success: bool
    strategy_used: RecoveryStrategy
    result: Optional[Any] = None
    error_message: Optional[str] = None
    recovery_time: float = 0.0
    fallback_used: bool = False


class ErrorRecoveryService:
    """Comprehensive error recovery and fallback system"""
    
    def __init__(self):
        self.error_history = []
        self.circuit_breakers = {}
        self.fallback_strategies = {}
        self.recovery_statistics = {}
        self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self):
        """Initialize recovery strategies for different error types"""
        self.fallback_strategies = {
            "langchain_service_error": {
                "strategy": RecoveryStrategy.FALLBACK,
                "fallback_service": "basic_orchestrator",
                "max_retries": 2,
                "timeout": 30.0
            },
            "database_connection_error": {
                "strategy": RecoveryStrategy.RETRY,
                "max_retries": 3,
                "retry_delay": 2.0,
                "exponential_backoff": True
            },
            "tool_execution_error": {
                "strategy": RecoveryStrategy.GRACEFUL_DEGRADATION,
                "fallback_response": "Service temporairement indisponible. Veuillez réessayer.",
                "alternative_tools": ["basic_response_generator"]
            },
            "api_timeout_error": {
                "strategy": RecoveryStrategy.CIRCUIT_BREAKER,
                "failure_threshold": 5,
                "recovery_timeout": 60.0
            },
            "memory_error": {
                "strategy": RecoveryStrategy.GRACEFUL_DEGRADATION,
                "reduce_context": True,
                "simplified_response": True
            },
            "validation_error": {
                "strategy": RecoveryStrategy.ALTERNATIVE_SERVICE,
                "alternative_service": "simple_validation",
                "max_retries": 1
            }
        }
    
    async def handle_error_with_recovery(
        self,
        error: Exception,
        context: ErrorContext,
        recovery_function: Optional[Callable] = None
    ) -> RecoveryResult:
        """Handle error with appropriate recovery strategy"""
        try:
            start_time = datetime.now()
            
            # Log error
            self._log_error(error, context)
            
            # Determine error type and severity
            error_type = self._classify_error(error)
            severity = self._assess_severity(error, context)
            
            # Update error context
            context.error_type = error_type
            context.severity = severity
            context.stack_trace = traceback.format_exc()
            
            # Get recovery strategy
            strategy_config = self.fallback_strategies.get(
                error_type, 
                self.fallback_strategies["tool_execution_error"]  # Default fallback
            )
            
            # Execute recovery strategy
            recovery_result = await self._execute_recovery_strategy(
                error, context, strategy_config, recovery_function
            )
            
            # Calculate recovery time
            recovery_result.recovery_time = (datetime.now() - start_time).total_seconds()
            
            # Update statistics
            self._update_recovery_statistics(error_type, recovery_result)
            
            # Store error in history
            self.error_history.append(context)
            
            return recovery_result
            
        except Exception as recovery_error:
            logger.error(f"Recovery system failed: {recovery_error}")
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK,
                error_message=f"Recovery failed: {str(recovery_error)}",
                fallback_used=True
            )
    
    async def _execute_recovery_strategy(
        self,
        error: Exception,
        context: ErrorContext,
        strategy_config: Dict[str, Any],
        recovery_function: Optional[Callable]
    ) -> RecoveryResult:
        """Execute specific recovery strategy"""
        strategy = strategy_config["strategy"]
        
        if strategy == RecoveryStrategy.RETRY:
            return await self._retry_strategy(error, context, strategy_config, recovery_function)
        
        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._fallback_strategy(error, context, strategy_config)
        
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return await self._graceful_degradation_strategy(error, context, strategy_config)
        
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            return await self._circuit_breaker_strategy(error, context, strategy_config)
        
        elif strategy == RecoveryStrategy.ALTERNATIVE_SERVICE:
            return await self._alternative_service_strategy(error, context, strategy_config)
        
        else:
            return RecoveryResult(
                success=False,
                strategy_used=strategy,
                error_message="Unknown recovery strategy"
            )
    
    async def _retry_strategy(
        self,
        error: Exception,
        context: ErrorContext,
        config: Dict[str, Any],
        recovery_function: Optional[Callable]
    ) -> RecoveryResult:
        """Implement retry strategy with exponential backoff"""
        max_retries = config.get("max_retries", 3)
        base_delay = config.get("retry_delay", 1.0)
        exponential_backoff = config.get("exponential_backoff", False)
        
        for attempt in range(max_retries):
            try:
                # Calculate delay
                if exponential_backoff:
                    delay = base_delay * (2 ** attempt)
                else:
                    delay = base_delay
                
                # Wait before retry
                if attempt > 0:
                    await asyncio.sleep(delay)
                
                # Attempt recovery
                if recovery_function:
                    result = await recovery_function()
                    return RecoveryResult(
                        success=True,
                        strategy_used=RecoveryStrategy.RETRY,
                        result=result
                    )
                
            except Exception as retry_error:
                logger.warning(f"Retry attempt {attempt + 1} failed: {retry_error}")
                context.recovery_attempts += 1
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.RETRY,
            error_message=f"All {max_retries} retry attempts failed"
        )
    
    async def _fallback_strategy(
        self,
        error: Exception,
        context: ErrorContext,
        config: Dict[str, Any]
    ) -> RecoveryResult:
        """Implement fallback to alternative service"""
        try:
            fallback_service = config.get("fallback_service", "basic_orchestrator")
            
            # Execute fallback service
            if fallback_service == "basic_orchestrator":
                result = await self._execute_basic_orchestrator_fallback(context)
            else:
                result = await self._execute_generic_fallback(fallback_service, context)
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                result=result,
                fallback_used=True
            )
            
        except Exception as fallback_error:
            logger.error(f"Fallback strategy failed: {fallback_error}")
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK,
                error_message=f"Fallback failed: {str(fallback_error)}",
                fallback_used=True
            )
    
    async def _graceful_degradation_strategy(
        self,
        error: Exception,
        context: ErrorContext,
        config: Dict[str, Any]
    ) -> RecoveryResult:
        """Implement graceful degradation with reduced functionality"""
        try:
            fallback_response = config.get(
                "fallback_response",
                "Je rencontre des difficultés techniques. Voici une réponse simplifiée."
            )
            
            # Create simplified response
            simplified_result = {
                "response": fallback_response,
                "agent_type": "error_recovery",
                "confidence": 0.3,
                "processing_method": "graceful_degradation",
                "metadata": {
                    "original_error": str(error),
                    "degraded_service": True,
                    "recovery_strategy": "graceful_degradation"
                }
            }
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
                result=simplified_result,
                fallback_used=True
            )
            
        except Exception as degradation_error:
            logger.error(f"Graceful degradation failed: {degradation_error}")
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
                error_message=f"Graceful degradation failed: {str(degradation_error)}"
            )
    
    async def _circuit_breaker_strategy(
        self,
        error: Exception,
        context: ErrorContext,
        config: Dict[str, Any]
    ) -> RecoveryResult:
        """Implement circuit breaker pattern"""
        service_name = context.service_name
        failure_threshold = config.get("failure_threshold", 5)
        recovery_timeout = config.get("recovery_timeout", 60.0)
        
        # Initialize circuit breaker if not exists
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure_time": None,
                "next_attempt_time": None
            }
        
        breaker = self.circuit_breakers[service_name]
        
        # Update failure count
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = datetime.now()
        
        # Check if threshold exceeded
        if breaker["failure_count"] >= failure_threshold:
            breaker["state"] = "open"
            breaker["next_attempt_time"] = datetime.now() + timedelta(seconds=recovery_timeout)
            
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.CIRCUIT_BREAKER,
                error_message=f"Circuit breaker opened for {service_name}. Service temporarily unavailable."
            )
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.CIRCUIT_BREAKER,
            error_message=f"Service failure recorded. {failure_threshold - breaker['failure_count']} failures until circuit opens."
        )

    async def _alternative_service_strategy(
        self,
        error: Exception,
        context: ErrorContext,
        config: Dict[str, Any]
    ) -> RecoveryResult:
        """Implement alternative service strategy"""
        try:
            alternative_service = config.get("alternative_service", "simple_validation")

            # Execute alternative service
            result = await self._execute_alternative_service(alternative_service, context)

            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.ALTERNATIVE_SERVICE,
                result=result
            )

        except Exception as alt_error:
            logger.error(f"Alternative service strategy failed: {alt_error}")
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.ALTERNATIVE_SERVICE,
                error_message=f"Alternative service failed: {str(alt_error)}"
            )

    async def _execute_basic_orchestrator_fallback(self, context: ErrorContext) -> Dict[str, Any]:
        """Execute basic error response as final fallback"""
        try:
            return {
                "response": "Je suis désolé, je rencontre des difficultés techniques. Veuillez réessayer dans quelques instants.",
                "agent_type": "error_fallback",
                "confidence": 0.0,
                "processing_method": "error_fallback",
                "metadata": {
                    "fallback_reason": "Advanced service failure",
                    "original_error": context.error_message
                }
            }

        except Exception as e:
            logger.error(f"Basic orchestrator fallback failed: {e}")
            return {
                "response": "Service temporairement indisponible. Veuillez réessayer plus tard.",
                "agent_type": "error_recovery",
                "confidence": 0.1,
                "processing_method": "emergency_fallback",
                "metadata": {"error": str(e)}
            }

    async def _execute_generic_fallback(self, service_name: str, context: ErrorContext) -> Dict[str, Any]:
        """Execute generic fallback service"""
        return {
            "response": f"Service {service_name} activé en mode de récupération.",
            "agent_type": service_name,
            "confidence": 0.5,
            "processing_method": "generic_fallback",
            "metadata": {"fallback_service": service_name}
        }

    async def _execute_alternative_service(self, service_name: str, context: ErrorContext) -> Dict[str, Any]:
        """Execute alternative service"""
        return {
            "response": f"Service alternatif {service_name} utilisé pour traiter votre demande.",
            "agent_type": service_name,
            "confidence": 0.6,
            "processing_method": "alternative_service",
            "metadata": {"alternative_service": service_name}
        }

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for recovery strategy selection"""
        error_type = type(error).__name__.lower()
        error_message = str(error).lower()

        if "connection" in error_message or "timeout" in error_message:
            return "database_connection_error"
        elif "langchain" in error_message or "llm" in error_message:
            return "langchain_service_error"
        elif "tool" in error_message or "execution" in error_message:
            return "tool_execution_error"
        elif "timeout" in error_message or "api" in error_message:
            return "api_timeout_error"
        elif "memory" in error_message or "resource" in error_message:
            return "memory_error"
        elif "validation" in error_message or "invalid" in error_message:
            return "validation_error"
        else:
            return "unknown_error"

    def _assess_severity(self, error: Exception, context: ErrorContext) -> ErrorSeverity:
        """Assess error severity"""
        error_message = str(error).lower()

        if any(word in error_message for word in ["critical", "fatal", "emergency"]):
            return ErrorSeverity.CRITICAL
        elif any(word in error_message for word in ["connection", "database", "timeout"]):
            return ErrorSeverity.HIGH
        elif any(word in error_message for word in ["validation", "format", "parsing"]):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _log_error(self, error: Exception, context: ErrorContext):
        """Log error with context"""
        logger.error(
            f"Error in {context.service_name}.{context.operation}: {str(error)}",
            extra={
                "service": context.service_name,
                "operation": context.operation,
                "user_id": context.user_id,
                "error_type": type(error).__name__,
                "query": context.query
            }
        )

    def _update_recovery_statistics(self, error_type: str, result: RecoveryResult):
        """Update recovery statistics"""
        if error_type not in self.recovery_statistics:
            self.recovery_statistics[error_type] = {
                "total_attempts": 0,
                "successful_recoveries": 0,
                "failed_recoveries": 0,
                "avg_recovery_time": 0.0
            }

        stats = self.recovery_statistics[error_type]
        stats["total_attempts"] += 1

        if result.success:
            stats["successful_recoveries"] += 1
        else:
            stats["failed_recoveries"] += 1

        # Update average recovery time
        n = stats["total_attempts"]
        stats["avg_recovery_time"] = ((n-1) * stats["avg_recovery_time"] + result.recovery_time) / n

    async def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery system statistics"""
        return {
            "total_errors": len(self.error_history),
            "recovery_statistics": self.recovery_statistics,
            "circuit_breakers": self.circuit_breakers,
            "recent_errors": [asdict(error) for error in self.error_history[-10:]]  # Last 10 errors
        }

    async def reset_circuit_breaker(self, service_name: str) -> bool:
        """Manually reset circuit breaker"""
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure_time": None,
                "next_attempt_time": None
            }
            logger.info(f"Circuit breaker reset for {service_name}")
            return True
        return False
