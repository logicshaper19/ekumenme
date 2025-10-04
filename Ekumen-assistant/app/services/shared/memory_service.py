"""
Advanced Memory Service for Agricultural AI
Implements persistent conversation memory with agricultural context
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pickle
import os

from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AgriculturalMemory(BaseChatMemory):
    """Agricultural-specific memory with context awareness"""
    
    def __init__(self, conversation_id: str, user_id: str, farm_siret: str = None):
        super().__init__()
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.farm_siret = farm_siret
        self.agricultural_context = {}
        self.intervention_history = []
        self.regulatory_context = {}
        self.weather_context = {}
        self.memory_file = f"./memory/{conversation_id}.pkl"
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from persistent storage"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'rb') as f:
                    data = pickle.load(f)
                    self.chat_memory = data.get('chat_memory', self.chat_memory)
                    self.agricultural_context = data.get('agricultural_context', {})
                    self.intervention_history = data.get('intervention_history', [])
                    self.regulatory_context = data.get('regulatory_context', {})
                    self.weather_context = data.get('weather_context', {})
                logger.info(f"Memory loaded for conversation {self.conversation_id}")
        except Exception as e:
            logger.warning(f"Failed to load memory: {e}")
    
    def _save_memory(self):
        """Save memory to persistent storage"""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            data = {
                'chat_memory': self.chat_memory,
                'agricultural_context': self.agricultural_context,
                'intervention_history': self.intervention_history,
                'regulatory_context': self.regulatory_context,
                'weather_context': self.weather_context,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.memory_file, 'wb') as f:
                pickle.dump(data, f)
            logger.debug(f"Memory saved for conversation {self.conversation_id}")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context with agricultural awareness"""
        super().save_context(inputs, outputs)
        
        # Extract agricultural context
        user_input = inputs.get('input', '')
        ai_output = outputs.get('output', '')
        
        # Update agricultural context
        self._update_agricultural_context(user_input, ai_output)
        
        # Save to persistent storage
        self._save_memory()
    
    def _update_agricultural_context(self, user_input: str, ai_output: str):
        """Update agricultural context from conversation"""
        user_lower = user_input.lower()
        
        # Track mentioned crops
        crops = ['blé', 'maïs', 'tournesol', 'colza', 'orge', 'avoine', 'soja', 'betterave']
        for crop in crops:
            if crop in user_lower:
                self.agricultural_context['current_crop'] = crop
                break
        
        # Track mentioned products
        products = ['glyphosate', 'cuivre', 'soufre', 'azote', 'phosphore', 'potasse']
        mentioned_products = [p for p in products if p in user_lower]
        if mentioned_products:
            self.agricultural_context['mentioned_products'] = mentioned_products
        
        # Track interventions
        interventions = ['traitement', 'pulvérisation', 'semis', 'récolte', 'labour', 'fertilisation']
        for intervention in interventions:
            if intervention in user_lower:
                self.intervention_history.append({
                    'type': intervention,
                    'mentioned_at': datetime.now().isoformat(),
                    'context': user_input[:100]
                })
                break
        
        # Track regulatory mentions
        regulatory_terms = ['amm', 'znt', 'conformité', 'autorisé', 'interdit', 'délai']
        if any(term in user_lower for term in regulatory_terms):
            self.regulatory_context['last_regulatory_query'] = {
                'query': user_input,
                'response': ai_output[:200],
                'timestamp': datetime.now().isoformat()
            }
        
        # Track weather mentions
        weather_terms = ['météo', 'pluie', 'vent', 'température', 'humidité']
        if any(term in user_lower for term in weather_terms):
            self.weather_context['last_weather_query'] = {
                'query': user_input,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_agricultural_summary(self) -> str:
        """Get summary of agricultural context"""
        summary_parts = []
        
        if self.agricultural_context.get('current_crop'):
            summary_parts.append(f"Culture actuelle: {self.agricultural_context['current_crop']}")
        
        if self.agricultural_context.get('mentioned_products'):
            products = ', '.join(self.agricultural_context['mentioned_products'])
            summary_parts.append(f"Produits mentionnés: {products}")
        
        if self.intervention_history:
            recent_interventions = [i['type'] for i in self.intervention_history[-3:]]
            summary_parts.append(f"Interventions récentes: {', '.join(recent_interventions)}")
        
        if self.farm_siret:
            summary_parts.append(f"Exploitation: {self.farm_siret}")
        
        return " | ".join(summary_parts) if summary_parts else "Pas de contexte agricole spécifique"


class MemoryService:
    """Service for managing conversation memory"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.memories: Dict[str, AgriculturalMemory] = {}
        self._cleanup_old_memories()
    
    def get_memory(
        self,
        conversation_id: str,
        user_id: str,
        farm_siret: str = None
    ) -> AgriculturalMemory:
        """Get or create memory for conversation"""
        if conversation_id not in self.memories:
            self.memories[conversation_id] = AgriculturalMemory(
                conversation_id=conversation_id,
                user_id=user_id,
                farm_siret=farm_siret
            )
        
        return self.memories[conversation_id]
    
    async def get_conversation_context(
        self,
        conversation_id: str,
        user_id: str,
        farm_siret: str = None
    ) -> Dict[str, Any]:
        """Get comprehensive conversation context"""
        memory = self.get_memory(conversation_id, user_id, farm_siret)
        
        # Get recent messages
        recent_messages = memory.chat_memory.messages[-10:] if memory.chat_memory.messages else []
        
        # Get agricultural context
        agricultural_summary = memory.get_agricultural_summary()
        
        # Get farm data if available
        farm_data = await self._get_farm_context(farm_siret) if farm_siret else {}
        
        return {
            "recent_messages": [
                {
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', datetime.now().isoformat())
                }
                for msg in recent_messages
            ],
            "agricultural_context": memory.agricultural_context,
            "agricultural_summary": agricultural_summary,
            "intervention_history": memory.intervention_history[-5:],  # Last 5 interventions
            "regulatory_context": memory.regulatory_context,
            "weather_context": memory.weather_context,
            "farm_data": farm_data,
            "conversation_length": len(memory.chat_memory.messages)
        }
    
    async def _get_farm_context(self, farm_siret: str) -> Dict[str, Any]:
        """Get farm context from database"""
        try:
            async with AsyncSessionLocal() as session:
                # Get farm basic info
                result = await session.execute(text("""
                    SELECT e.nom, e.adresse, COUNT(DISTINCT p.id) as parcelles_count
                    FROM farm_operations.exploitations e
                    LEFT JOIN farm_operations.parcelles p ON e.siret = p.siret_exploitation
                    WHERE e.siret = :siret
                    GROUP BY e.siret, e.nom, e.adresse
                """), {"siret": farm_siret})
                
                farm_info = result.fetchone()
                if not farm_info:
                    return {}
                
                # Get recent interventions
                result = await session.execute(text("""
                    SELECT ti.libelle, i.date_debut, COUNT(*) as count
                    FROM farm_operations.interventions i
                    JOIN reference.types_intervention ti ON i.id_type_intervention = ti.id_type_intervention
                    WHERE i.siret_exploitation = :siret
                    AND i.date_debut >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY ti.libelle, i.date_debut
                    ORDER BY i.date_debut DESC
                    LIMIT 5
                """), {"siret": farm_siret})
                
                recent_interventions = [
                    {
                        "type": row[0],
                        "date": row[1].isoformat() if row[1] else None,
                        "count": row[2]
                    }
                    for row in result.fetchall()
                ]
                
                return {
                    "farm_name": farm_info[0],
                    "address": farm_info[1],
                    "parcelles_count": farm_info[2],
                    "recent_interventions": recent_interventions
                }
                
        except Exception as e:
            logger.error(f"Failed to get farm context: {e}")
            return {}
    
    def save_conversation_turn(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        ai_response: str,
        farm_siret: str = None
    ):
        """Save a conversation turn"""
        memory = self.get_memory(conversation_id, user_id, farm_siret)
        
        memory.save_context(
            inputs={"input": user_message},
            outputs={"output": ai_response}
        )
    
    def get_memory_summary(self, conversation_id: str) -> Optional[str]:
        """Get memory summary for conversation"""
        if conversation_id not in self.memories:
            return None
        
        memory = self.memories[conversation_id]
        
        # Create summary using LLM
        if len(memory.chat_memory.messages) > 10:
            try:
                summary_memory = ConversationSummaryMemory(
                    llm=self.llm,
                    return_messages=True
                )
                
                # Add messages to summary memory
                for msg in memory.chat_memory.messages:
                    if isinstance(msg, HumanMessage):
                        summary_memory.chat_memory.add_user_message(msg.content)
                    elif isinstance(msg, AIMessage):
                        summary_memory.chat_memory.add_ai_message(msg.content)
                
                return summary_memory.buffer
                
            except Exception as e:
                logger.error(f"Failed to create memory summary: {e}")
                return None
        
        return None
    
    def _cleanup_old_memories(self):
        """Cleanup old memory files"""
        try:
            memory_dir = "./memory"
            if not os.path.exists(memory_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for filename in os.listdir(memory_dir):
                if filename.endswith('.pkl'):
                    filepath = os.path.join(memory_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old memory file: {filename}")
                        
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    def clear_memory(self, conversation_id: str):
        """Clear memory for conversation"""
        if conversation_id in self.memories:
            del self.memories[conversation_id]
        
        memory_file = f"./memory/{conversation_id}.pkl"
        if os.path.exists(memory_file):
            os.remove(memory_file)
            logger.info(f"Memory cleared for conversation {conversation_id}")
    
    def get_active_conversations(self) -> List[str]:
        """Get list of active conversation IDs"""
        return list(self.memories.keys())
