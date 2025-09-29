"""
Optimized LLM Service - Smart LLM selection and batching.

Features:
- Use GPT-3.5 for simple tasks (10x faster, 20x cheaper)
- Use GPT-4 only for complex analysis
- Batch multiple LLM calls when possible
- Reduce total LLM calls per query

Goal: Reduce LLM time from 21-34s to 8-12s
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMComplexity(Enum):
    """LLM task complexity levels"""
    SIMPLE = "simple"       # GPT-3.5, < 2s
    MEDIUM = "medium"       # GPT-3.5, < 5s
    COMPLEX = "complex"     # GPT-4, < 15s


@dataclass
class LLMTask:
    """Single LLM task"""
    task_id: str
    prompt: str
    complexity: LLMComplexity
    max_tokens: int = 500
    temperature: float = 0.3
    system_message: Optional[str] = None


@dataclass
class LLMResult:
    """Result from LLM execution"""
    task_id: str
    response: str
    model_used: str
    execution_time: float
    tokens_used: int
    cost: float


class OptimizedLLMService:
    """
    Service for optimized LLM usage.
    
    Features:
    - Smart model selection (GPT-3.5 vs GPT-4)
    - Batch processing for multiple tasks
    - Token optimization
    - Cost tracking
    """
    
    def __init__(self):
        # Initialize GPT-3.5 (fast, cheap)
        self.gpt35 = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=500,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize GPT-4 (slow, expensive, high quality)
        self.gpt4 = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.1,
            max_tokens=1000,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Cost tracking
        self.costs = {
            "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},  # per token
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000}
        }
        
        # Statistics
        self.stats = {
            "total_calls": 0,
            "gpt35_calls": 0,
            "gpt4_calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_time": 0.0
        }
        
        logger.info("Initialized Optimized LLM Service")
    
    async def execute_task(
        self,
        task: LLMTask
    ) -> LLMResult:
        """
        Execute a single LLM task with optimal model selection.
        """
        start_time = time.time()
        
        # Select model based on complexity
        if task.complexity == LLMComplexity.COMPLEX:
            llm = self.gpt4
            model_name = "gpt-4"
            self.stats["gpt4_calls"] += 1
        else:
            llm = self.gpt35
            model_name = "gpt-3.5-turbo"
            self.stats["gpt35_calls"] += 1
        
        # Configure LLM for this task
        llm.max_tokens = task.max_tokens
        llm.temperature = task.temperature
        
        # Prepare messages
        messages = []
        if task.system_message:
            messages.append(SystemMessage(content=task.system_message))
        messages.append(HumanMessage(content=task.prompt))
        
        # Execute
        try:
            response = await llm.agenerate([messages])
            response_text = response.generations[0][0].text
            
            # Estimate tokens (rough approximation)
            input_tokens = len(task.prompt.split()) * 1.3
            output_tokens = len(response_text.split()) * 1.3
            total_tokens = int(input_tokens + output_tokens)
            
            # Calculate cost
            cost = (
                input_tokens * self.costs[model_name]["input"] +
                output_tokens * self.costs[model_name]["output"]
            )
            
            execution_time = time.time() - start_time
            
            # Update stats
            self.stats["total_calls"] += 1
            self.stats["total_tokens"] += total_tokens
            self.stats["total_cost"] += cost
            self.stats["total_time"] += execution_time
            
            logger.info(
                f"✅ LLM task {task.task_id}: {model_name}, "
                f"{execution_time:.2f}s, {total_tokens} tokens, ${cost:.4f}"
            )
            
            return LLMResult(
                task_id=task.task_id,
                response=response_text,
                model_used=model_name,
                execution_time=execution_time,
                tokens_used=total_tokens,
                cost=cost
            )
            
        except Exception as e:
            logger.error(f"LLM task {task.task_id} failed: {e}")
            raise
    
    async def execute_batch(
        self,
        tasks: List[LLMTask]
    ) -> List[LLMResult]:
        """
        Execute multiple LLM tasks in parallel.
        
        Groups tasks by complexity and executes in parallel.
        """
        if not tasks:
            return []
        
        logger.info(f"📦 Executing batch of {len(tasks)} LLM tasks")
        
        # Group tasks by complexity
        simple_tasks = [t for t in tasks if t.complexity == LLMComplexity.SIMPLE]
        medium_tasks = [t for t in tasks if t.complexity == LLMComplexity.MEDIUM]
        complex_tasks = [t for t in tasks if t.complexity == LLMComplexity.COMPLEX]
        
        logger.info(
            f"  Simple: {len(simple_tasks)} (GPT-3.5), "
            f"Medium: {len(medium_tasks)} (GPT-3.5), "
            f"Complex: {len(complex_tasks)} (GPT-4)"
        )
        
        # Execute all tasks in parallel
        all_task_coroutines = [self.execute_task(task) for task in tasks]
        results = await asyncio.gather(*all_task_coroutines, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, LLMResult)]
        
        # Log batch results
        total_time = max(r.execution_time for r in valid_results) if valid_results else 0
        total_cost = sum(r.cost for r in valid_results)
        
        logger.info(
            f"✅ Batch complete: {len(valid_results)}/{len(tasks)} successful, "
            f"{total_time:.2f}s, ${total_cost:.4f}"
        )
        
        return valid_results
    
    async def synthesize_response(
        self,
        query: str,
        tool_results: Dict[str, Any],
        complexity: LLMComplexity = LLMComplexity.MEDIUM,
        max_tokens: int = 800
    ) -> str:
        """
        Synthesize final response from tool results.

        This is the main synthesis step that combines all tool outputs.
        """
        # Adjust max_tokens based on complexity
        if complexity == LLMComplexity.COMPLEX:
            max_tokens = max(max_tokens, 1500)  # Ensure detailed responses for complex queries
        elif complexity == LLMComplexity.SIMPLE:
            max_tokens = min(max_tokens, 300)   # Keep simple responses concise

        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(query, tool_results, complexity)

        # Create synthesis task with complexity-appropriate system message
        system_message = self._get_system_message(complexity)

        task = LLMTask(
            task_id="synthesis",
            prompt=prompt,
            complexity=complexity,
            max_tokens=max_tokens,
            temperature=0.3,
            system_message=system_message
        )

        # Execute
        result = await self.execute_task(task)

        return result.response

    def _get_system_message(self, complexity: LLMComplexity) -> str:
        """Get appropriate system message based on complexity"""
        if complexity == LLMComplexity.COMPLEX:
            return (
                "Tu es un assistant agricole expert spécialisé dans l'analyse de données. "
                "Pour les questions analytiques complexes:\n"
                "1. Analyse en détail toutes les données fournies\n"
                "2. Effectue les calculs nécessaires (moyennes, totaux, comparaisons)\n"
                "3. Explique ton raisonnement étape par étape\n"
                "4. Fournis des réponses complètes avec contexte et justifications\n"
                "5. Si des données semblent incohérentes, explique les possibilités\n"
                "Sois précis, détaillé et pédagogique."
            )
        elif complexity == LLMComplexity.SIMPLE:
            return (
                "Tu es un assistant agricole amical. "
                "Réponds de manière concise et directe."
            )
        else:  # MEDIUM
            return (
                "Tu es un assistant agricole expert. "
                "Synthétise les informations des outils pour répondre à la question de l'agriculteur. "
                "Sois clair, précis et pratique."
            )

    def _build_synthesis_prompt(
        self,
        query: str,
        tool_results: Dict[str, Any],
        complexity: LLMComplexity = LLMComplexity.MEDIUM
    ) -> str:
        """Build prompt for synthesis"""
        prompt = f"Question de l'agriculteur: {query}\n\n"
        prompt += "Résultats des outils:\n"

        for tool_name, result in tool_results.items():
            prompt += f"\n{tool_name}:\n{result}\n"

        # Add complexity-specific instructions
        if complexity == LLMComplexity.COMPLEX:
            prompt += (
                "\nCette question nécessite une analyse approfondie. "
                "Fournis une réponse détaillée qui:\n"
                "- Analyse toutes les données pertinentes\n"
                "- Effectue les calculs nécessaires\n"
                "- Explique le raisonnement\n"
                "- Répond complètement à la question posée"
            )
        else:
            prompt += "\nSynthétise ces informations pour répondre à la question de manière claire et pratique."

        return prompt
    
    async def classify_query_complexity(
        self,
        query: str
    ) -> LLMComplexity:
        """
        Classify query complexity to determine which LLM to use.
        
        Uses fast GPT-3.5 for classification.
        """
        task = LLMTask(
            task_id="classify_complexity",
            prompt=f"Classifie la complexité de cette question agricole (simple/medium/complex): {query}",
            complexity=LLMComplexity.SIMPLE,
            max_tokens=10,
            temperature=0,
            system_message="Tu es un classificateur de complexité. Réponds uniquement: simple, medium, ou complex."
        )
        
        result = await self.execute_task(task)
        
        # Parse response
        response_lower = result.response.lower().strip()
        if "simple" in response_lower:
            return LLMComplexity.SIMPLE
        elif "complex" in response_lower:
            return LLMComplexity.COMPLEX
        else:
            return LLMComplexity.MEDIUM
    
    def get_stats(self) -> Dict[str, Any]:
        """Get LLM usage statistics"""
        return {
            **self.stats,
            "avg_time_per_call": (
                self.stats["total_time"] / self.stats["total_calls"]
                if self.stats["total_calls"] > 0 else 0
            ),
            "avg_cost_per_call": (
                self.stats["total_cost"] / self.stats["total_calls"]
                if self.stats["total_calls"] > 0 else 0
            ),
            "gpt35_percentage": (
                self.stats["gpt35_calls"] / self.stats["total_calls"] * 100
                if self.stats["total_calls"] > 0 else 0
            ),
            "gpt4_percentage": (
                self.stats["gpt4_calls"] / self.stats["total_calls"] * 100
                if self.stats["total_calls"] > 0 else 0
            )
        }
    
    def estimate_cost_savings(self) -> Dict[str, Any]:
        """
        Estimate cost savings from using GPT-3.5 instead of GPT-4.
        """
        # Calculate what it would cost if all calls were GPT-4
        gpt4_cost_per_call = 0.05  # Rough estimate
        all_gpt4_cost = self.stats["total_calls"] * gpt4_cost_per_call
        
        # Actual cost
        actual_cost = self.stats["total_cost"]
        
        # Savings
        savings = all_gpt4_cost - actual_cost
        savings_percentage = (savings / all_gpt4_cost * 100) if all_gpt4_cost > 0 else 0
        
        return {
            "all_gpt4_cost": all_gpt4_cost,
            "actual_cost": actual_cost,
            "savings": savings,
            "savings_percentage": savings_percentage
        }

