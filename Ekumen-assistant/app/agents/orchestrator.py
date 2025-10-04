"""
Orchestrator Agent - Master coordinator for multi-agent system

Analyzes queries, routes to specialized agents, and synthesizes responses.
"""

import logging
from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler

from app.prompts.prompt_registry import get_agent_prompt
from app.services.shared.tool_registry_service import get_tool_registry
from app.core.config import settings

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Master orchestrator agent that coordinates specialized agents.
    
    Responsibilities:
    - Analyze user queries
    - Route to appropriate specialized agents
    - Synthesize multi-agent responses
    - Ensure consistency and safety
    
    Architecture:
    - Uses create_structured_chat_agent for complex JSON tool inputs
    - Supports streaming via callbacks
    - Handles agent_scratchpad automatically via AgentExecutor
    """
    
    def __init__(self, callbacks: Optional[List[BaseCallbackHandler]] = None):
        """
        Initialize orchestrator agent.
        
        Args:
            callbacks: Optional list of callback handlers for streaming
        """
        
        # Get tools from registry
        self.tool_registry = get_tool_registry()
        self.tools = self.tool_registry.get_all_tools()
        
        logger.info(f"🔧 Initializing orchestrator with {len(self.tools)} tools")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.OPENAI_DEFAULT_MODEL,
            temperature=0,
            streaming=True,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Get orchestrator prompt (uses MessagesPlaceholder for agent_scratchpad)
        self.prompt = get_agent_prompt("orchestrator", include_examples=True)

        # Create OpenAI tools agent (supports complex JSON tool inputs via function calling)
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create executor with callbacks
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            callbacks=callbacks or []
        )
        
        logger.info(f"✅ Orchestrator initialized successfully")
        logger.info(f"   - Model: {settings.OPENAI_DEFAULT_MODEL}")
        logger.info(f"   - Tools: {len(self.tools)}")
        logger.info(f"   - Streaming: {'Enabled' if callbacks else 'Disabled'}")
    
    async def process(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query through the orchestrator.
        
        Args:
            query: User query
            context: Optional context (farm_siret, user_id, etc.)
            
        Returns:
            Dict with:
                - response: The final response text
                - metadata: Execution metadata (tools used, etc.)
                - intermediate_steps: List of tool calls made
        """
        try:
            logger.info(f"🚀 Orchestrator processing query: {query[:100]}...")

            # DEBUG: Log what context contains
            if context:
                logger.info(f"📦 Context keys received: {list(context.keys())}")
                if 'agent_scratchpad' in context:
                    logger.error(f"❌ FOUND agent_scratchpad in context! Type: {type(context['agent_scratchpad'])}")
                    logger.error(f"❌ Value: {context['agent_scratchpad']}")
                if 'intermediate_steps' in context:
                    logger.error(f"❌ FOUND intermediate_steps in context! Type: {type(context['intermediate_steps'])}")

            # Prepare input - ONLY pass the query
            # DO NOT manually pass agent_scratchpad - AgentExecutor handles it automatically
            agent_input = {
                "input": query
            }

            # Only add explicitly safe context fields if provided (whitelist approach)
            if context:
                # Whitelist of safe context keys that won't interfere with agent execution
                safe_keys = [
                    'farm_siret',
                    'user_id',
                    'conversation_id',
                    'message_id',
                    'thread_id',
                    'agent_type',
                    'farm_context',
                    'weather_context',
                    'chat_history'
                ]

                for key in safe_keys:
                    if key in context:
                        agent_input[key] = context[key]

                logger.info(f"📤 Passing to agent_executor: {list(agent_input.keys())}")
            
            # Execute orchestrator (AgentExecutor manages agent_scratchpad automatically)
            result = await self.agent_executor.ainvoke(agent_input)
            
            # Extract response
            response_text = result.get("output", "Désolé, je n'ai pas pu générer une réponse.")
            
            # Get intermediate steps (tool calls)
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Extract tool names that were called
            tools_called = []
            for step in intermediate_steps:
                if len(step) >= 1:
                    action = step[0]
                    if hasattr(action, 'tool'):
                        tools_called.append(action.tool)
            
            logger.info(f"✅ Orchestrator completed - {len(intermediate_steps)} tools executed")
            
            return {
                "response": response_text,
                "metadata": {
                    "tools_executed": len(intermediate_steps),
                    "tools_called": tools_called,
                    "model_used": settings.OPENAI_DEFAULT_MODEL
                },
                "intermediate_steps": intermediate_steps
            }
            
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}", exc_info=True)
            raise
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get dictionary of tool names and descriptions"""
        return {tool.name: tool.description for tool in self.tools}


# Export for easy import
__all__ = ["OrchestratorAgent"]

