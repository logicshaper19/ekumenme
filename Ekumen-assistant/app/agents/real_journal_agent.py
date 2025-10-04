"""
Real Journal Agent - Proper LangChain Agent with Atomic Tools
This agent actually reasons about journal entries using simple tools
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, date
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.tools.atomic_tools import ATOMIC_TOOLS
from app.core.config import settings

logger = logging.getLogger(__name__)


class RealJournalAgent:
    """
    A REAL agent that reasons about journal entries using atomic tools.
    
    This agent:
    - Understands what farmers are saying
    - Decides which tools to use based on context
    - Validates facts using EPHY, weather, and database tools
    - Saves valid entries
    - Flags issues for review
    
    It does NOT:
    - Have mega-tools that do everything
    - Follow step-by-step scripts
    - Wrap services in tool decorators
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        max_iterations: int = 10
    ):
        """
        Initialize the real journal agent.
        
        Args:
            llm: Language model (defaults to GPT-4)
            tools: List of atomic tools (defaults to all atomic tools)
            max_iterations: Maximum reasoning iterations
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        
        self.tools = tools or ATOMIC_TOOLS
        self.max_iterations = max_iterations
        
        # Create the agent
        self._create_agent()
    
    def _create_agent(self):
        """Create the agent with proper reasoning capabilities"""
        
        system_prompt = """You are an agricultural expert assistant that helps farmers record their farm activities.

YOUR ROLE:
- Listen to what farmers describe about their farm work
- Use available tools to verify facts and check compliance
- Save valid entries to the database
- Flag issues that need farmer attention

AVAILABLE TOOLS:
You have access to these atomic tools:

EPHY Database Tools:
- get_product_by_amm(amm_code): Get product info by AMM code
- check_product_authorized(amm_code): Check if product is authorized
- get_max_dose_for_crop(amm_code, crop_type): Get max dose for product on crop
- check_crop_authorization(amm_code, crop_type): Check if product authorized for crop
- get_pre_harvest_interval(amm_code, crop_type): Get days before harvest (DAR)
- search_products_by_name(product_name): Search products by name

Weather Tools:
- get_wind_speed(date, location): Get wind speed for date/location
- get_temperature(date, location): Get temperature for date/location
- check_rain_forecast(date, location): Check if rain expected
- is_weather_safe_for_treatment(date, location): Check if weather safe for phyto treatment

Database Tools:
- save_journal_entry(entry_data, user_id): Save entry to database
- get_farm_parcels(org_id): Get farm parcels
- get_journal_entry(entry_id): Get existing entry

Validation Tools:
- validate_dose(dose, max_dose, unit): Check if dose is valid
- check_date_validity(date, intervention_type): Check if date is valid
- validate_surface(surface_ha): Check if surface is reasonable

Utility Tools:
- extract_date_from_text(text): Extract date from text
- extract_number_from_text(text, unit): Extract numbers from text

HOW TO REASON:
1. **Understand**: What did the farmer do? What products? What crops? What dates?
2. **Extract**: Use utility tools to extract specific information (dates, numbers, etc.)
3. **Verify**: Use EPHY tools to check products, doses, authorizations
4. **Validate**: Use weather tools to check conditions, validation tools for data quality
5. **Save**: Use database tools to save valid entries
6. **Report**: Tell farmer what was saved and any issues found

EXAMPLES OF REASONING:

Farmer says: "J'ai appliqué Saracen Delta sur la parcelle Nord"
Your reasoning:
1. This is a phytosanitary treatment
2. Product: Saracen Delta (need to find AMM code)
3. Parcel: Nord
4. Need to check: product authorization, dose limits, weather conditions
5. Use tools: search_products_by_name("Saracen Delta") → get AMM → check authorization → save

Farmer says: "Semis de blé sur 5 hectares"
Your reasoning:
1. This is planting (semis)
2. Crop: blé (wheat)
3. Surface: 5 hectares
4. Need to check: date validity, surface reasonableness
5. Use tools: validate_surface(5.0) → check_date_validity → save

Farmer says: "Traitement fongicide avec produit AMM 2190312, 2.5L/ha sur blé"
Your reasoning:
1. Phytosanitary treatment
2. AMM code: 2190312
3. Dose: 2.5L/ha
4. Crop: blé
5. Need to check: product authorization, dose limits, crop authorization
6. Use tools: get_product_by_amm("2190312") → check_crop_authorization → get_max_dose_for_crop → validate_dose → save

IMPORTANT RULES:
- Always use tools to verify facts, don't assume
- If a product is mentioned without AMM code, try to find it
- If dose is mentioned, check it against limits
- If weather matters (phyto treatments), check conditions
- Save entries even if there are warnings (flag warnings for farmer)
- Be specific about what you're checking and why

RESPONSE FORMAT:
After processing, provide a clear summary:
- What was recorded
- Any issues found
- What the farmer should know
- Entry ID if saved

Be conversational and helpful, not robotic."""

        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=self.max_iterations,
            handle_parsing_errors=True
        )
        
        logger.info(f"Real Journal Agent created with {len(self.tools)} atomic tools")
    
    async def process_journal_entry(
        self, 
        transcript: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a journal entry transcript.
        
        The agent will:
        1. Understand what the farmer described
        2. Use appropriate tools to verify facts
        3. Save valid entries
        4. Report any issues
        
        Args:
            transcript: What the farmer said
            user_context: User and farm context (user_id, org_id, etc.)
            
        Returns:
            Processing result with entry details and any issues
        """
        try:
            # Build the input for the agent
            user_id = user_context.get("user_id", "unknown") if user_context else "unknown"
            org_id = user_context.get("org_id", "unknown") if user_context else "unknown"
            
            agent_input = f"""
            Process this farm journal entry:
            
            TRANSCRIPT: "{transcript}"
            
            USER CONTEXT:
            - User ID: {user_id}
            - Organization ID: {org_id}
            
            Please:
            1. Understand what the farmer did
            2. Use tools to verify any products, doses, dates, weather
            3. Save the entry to the database
            4. Report any issues or warnings
            
            Be thorough but efficient. Use the tools to check facts, don't guess.
            """
            
            # Let the agent reason and use tools
            result = await self.agent_executor.ainvoke({
                "input": agent_input
            })
            
            return {
                "success": True,
                "transcript": transcript,
                "user_context": user_context,
                "agent_output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing journal entry: {e}")
            return {
                "success": False,
                "transcript": transcript,
                "user_context": user_context,
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    async def validate_existing_entry(
        self, 
        entry_id: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate an existing journal entry using tools.
        
        This is useful for:
        - Re-validating entries when new data becomes available
        - Checking compliance after entry creation
        - Batch validation of historical entries
        
        Args:
            entry_id: ID of the journal entry to validate
            user_context: User context for validation
            
        Returns:
            Validation results with any issues found
        """
        try:
            agent_input = f"""
            Validate this existing journal entry:
            
            ENTRY ID: {entry_id}
            
            Please:
            1. Get the entry details
            2. Check all products against EPHY database
            3. Validate doses, dates, weather conditions
            4. Report any compliance issues
            
            Use the tools to verify everything thoroughly.
            """
            
            result = await self.agent_executor.ainvoke({
                "input": agent_input
            })
            
            return {
                "success": True,
                "entry_id": entry_id,
                "user_context": user_context,
                "validation_output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "validated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating entry {entry_id}: {e}")
            return {
                "success": False,
                "entry_id": entry_id,
                "user_context": user_context,
                "error": str(e),
                "validated_at": datetime.now().isoformat()
            }
    
    async def search_and_validate_product(
        self, 
        product_name: str, 
        crop_type: str = None
    ) -> Dict[str, Any]:
        """
        Search for a product and validate its usage.
        
        Useful when farmers mention products without AMM codes.
        
        Args:
            product_name: Name of the product to search
            crop_type: Crop type for validation (optional)
            
        Returns:
            Search results and validation information
        """
        try:
            agent_input = f"""
            Search and validate this product:
            
            PRODUCT NAME: "{product_name}"
            CROP TYPE: {crop_type or "Not specified"}
            
            Please:
            1. Search for the product in EPHY database
            2. If found, check authorization status
            3. If crop specified, check crop authorization
            4. Report findings and any issues
            
            Use the search and validation tools.
            """
            
            result = await self.agent_executor.ainvoke({
                "input": agent_input
            })
            
            return {
                "success": True,
                "product_name": product_name,
                "crop_type": crop_type,
                "search_output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "searched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching product {product_name}: {e}")
            return {
                "success": False,
                "product_name": product_name,
                "crop_type": crop_type,
                "error": str(e),
                "searched_at": datetime.now().isoformat()
            }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools"""
        return {tool.name: tool.description for tool in self.tools}
