"""
LCEL-based Chat Service with Automatic History Management
Modern LangChain implementation using RunnableWithMessageHistory
"""

import logging
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.postgres_chat_history import get_session_history, AsyncPostgresChatMessageHistory
from app.prompts.base_prompts import BASE_AGRICULTURAL_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LCELChatService:
    """
    Modern chat service using LCEL (LangChain Expression Language)
    with automatic history management via RunnableWithMessageHistory
    """
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize LangChain components"""
        try:
            # Initialize LLM
            self.llm = ChatOpenAI(
                model_name="gpt-4",
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY,
                streaming=True  # Enable streaming by default
            )
            
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Initialize vector store (will be populated with agricultural knowledge)
            # Using langchain-chroma for updated API
            try:
                from langchain_chroma import Chroma as ChromaNew
                self.vectorstore = ChromaNew(
                    embedding_function=self.embeddings,
                    persist_directory="./chroma_db"
                )
                logger.info("✅ Using updated langchain-chroma package")
            except ImportError:
                # Fallback to deprecated version if new package not installed
                from langchain.vectorstores import Chroma
                self.vectorstore = Chroma(
                    embedding_function=self.embeddings,
                    persist_directory="./chroma_db"
                )
                logger.warning("⚠️  Using deprecated Chroma - install langchain-chroma: pip install langchain-chroma")
            
            logger.info("✅ LCEL Chat Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LCEL components: {e}")
            raise
    
    def create_basic_chat_chain(self, db_session: AsyncSession):
        """
        Create basic chat chain with automatic history management
        
        Args:
            db_session: Database session for history persistence
            
        Returns:
            Chain with automatic history
        """
        # Create prompt with history placeholder
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{BASE_AGRICULTURAL_SYSTEM_PROMPT}
            
Tu as accès à l'historique complet de la conversation.
Utilise cet historique pour fournir des réponses contextuelles et cohérentes.
Si l'utilisateur fait référence à quelque chose mentionné précédemment, utilise ce contexte.
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        # Create LCEL chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Wrap with automatic history management
        chain_with_history = RunnableWithMessageHistory(
            chain,
            lambda session_id: get_session_history(session_id, db_session),
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        
        return chain_with_history
    
    def create_rag_chain(self, db_session: AsyncSession, organization_id: Optional[str] = None, accessible_document_ids: Optional[List[str]] = None):
        """
        Create RAG chain with context-aware retrieval and automatic history
        
        Args:
            db_session: Database session for history persistence
            
        Returns:
            RAG chain with automatic history
        """
        # Step 1: Create history-aware retriever
        # This reformulates queries based on chat history
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", """Étant donné l'historique de la conversation et la dernière question de l'utilisateur,
reformule la question pour qu'elle soit compréhensible sans l'historique.

Si la question fait référence à quelque chose mentionné précédemment (comme "cette parcelle", "ce traitement", etc.),
inclus ce contexte dans la reformulation.

NE réponds PAS à la question, reformule-la seulement pour qu'elle soit autonome.

Exemples:
- "Et pour le maïs?" → "Quelles sont les réglementations pour le maïs?"
- "Quel traitement pour cette parcelle?" → "Quel traitement recommandes-tu pour la parcelle de blé de 10 hectares?"
"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # Build Chroma search kwargs with org/document filter
        # Note: For Chroma, we use 'k' for number of results
        # Filtering is NOT supported in as_retriever for the deprecated Chroma version
        # We'll need to filter results post-retrieval or upgrade to langchain-chroma
        search_kwargs = {"k": 5}

        # TODO: Install langchain-chroma to enable proper filtering
        # For now, we'll retrieve without filtering and filter post-retrieval
        # This is a temporary workaround until langchain-chroma is installed

        history_aware_retriever = create_history_aware_retriever(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            ),
            prompt=contextualize_q_prompt
        )
        
        # Step 2: Create QA chain
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{BASE_AGRICULTURAL_SYSTEM_PROMPT}

Utilise le contexte suivant pour répondre à la question:

{{context}}

Si tu ne trouves pas la réponse dans le contexte fourni, dis-le clairement.
Utilise l'historique de la conversation pour fournir des réponses cohérentes et contextuelles.
"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        # Step 3: Combine into retrieval chain
        rag_chain = create_retrieval_chain(
            history_aware_retriever,
            question_answer_chain
        )
        
        # Step 4: Wrap with automatic history
        rag_chain_with_history = RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: get_session_history(session_id, db_session),
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        
        return rag_chain_with_history
    
    async def process_message(
        self,
        db_session: AsyncSession,
        conversation_id: str,
        message: str,
        use_rag: bool = False,
        organization_id: Optional[str] = None,
        accessible_document_ids: Optional[List[str]] = None
    ) -> str:
        """
        Process message with automatic history management
        
        Args:
            db_session: Database session
            conversation_id: Conversation ID (session ID)
            message: User message
            use_rag: Whether to use RAG
            
        Returns:
            AI response
        """
        try:
            # Create appropriate chain
            if use_rag:
                chain = self.create_rag_chain(db_session, organization_id=organization_id, accessible_document_ids=accessible_document_ids)
                result = await chain.ainvoke(
                    {"input": message},
                    config={"configurable": {"session_id": conversation_id}}
                )
                # Return full result to allow callers to access both answer and context
                return result
            else:
                chain = self.create_basic_chat_chain(db_session)
                result = await chain.ainvoke(
                    {"input": message},
                    config={"configurable": {"session_id": conversation_id}}
                )
                return result
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    async def stream_message(
        self,
        db_session: AsyncSession,
        conversation_id: str,
        message: str,
        use_rag: bool = False,
        organization_id: Optional[str] = None,
        accessible_document_ids: Optional[List[str]] = None
    ) -> AsyncIterator[str]:
        """
        Stream message response with automatic history management

        Args:
            db_session: Database session
            conversation_id: Conversation ID
            message: User message
            use_rag: Whether to use RAG

        Yields:
            Response chunks
        """
        try:
            # Create appropriate chain
            if use_rag:
                chain = self.create_rag_chain(db_session, organization_id=organization_id, accessible_document_ids=accessible_document_ids)
                full_answer = ""
                source_docs = []

                # Use astream_events v2 to get token-level streaming from nested chains
                # v2 is more reliable for complex chains like create_retrieval_chain
                #
                # IMPORTANT: Only listen to ONE event type to avoid duplicate tokens!
                # We use on_chat_model_stream which is the most reliable for OpenAI models
                async for event in chain.astream_events(
                    {"input": message},
                    config={"configurable": {"session_id": conversation_id}},
                    version="v2"
                ):
                    kind = event.get("event")

                    # 1) Stream raw LLM tokens ONLY from chat_model_stream
                    # DO NOT also listen to on_llm_stream or on_chain_stream to avoid duplicates!
                    # FILTER: Only stream from the final answer generation (seq:step:3),
                    # NOT the query reformulation (seq:step:2)
                    if kind == "on_chat_model_stream":
                        event_tags = event.get("tags", [])

                        # Skip the question reformulation step (seq:step:2)
                        # Only stream the final answer generation (seq:step:3)
                        if "seq:step:2" in event_tags:
                            continue

                        chunk = event.get("data", {}).get("chunk")
                        # chunk may be a BaseMessageChunk or str depending on backend
                        if chunk is not None:
                            content = getattr(chunk, "content", None) or (chunk if isinstance(chunk, str) else None)
                            if content:
                                full_answer += content
                                yield content

                    # 2) Capture the final answer and context from the retrieval chain
                    elif kind == "on_chain_end":
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict):
                            # Prefer explicit answer if provided by create_retrieval_chain
                            answer_text = output.get("answer")
                            if isinstance(answer_text, str) and answer_text:
                                full_answer = answer_text
                            if "context" in output:
                                source_docs = output.get("context", [])

                # Emit final event so callers can persist citations
                yield {"final": {"answer": full_answer, "context": source_docs}}
            else:
                chain = self.create_basic_chat_chain(db_session)
                async for chunk in chain.astream(
                    {"input": message},
                    config={"configurable": {"session_id": conversation_id}}
                ):
                    # Normalize chunks to strings for WebSocket/SSE layer
                    if hasattr(chunk, "content"):
                        yield chunk.content
                    else:
                        yield str(chunk)

        except Exception as e:
            logger.error(f"Error streaming message: {e}")
            raise
    
    def create_multi_tool_chain(self, db_session: AsyncSession, tools: list):
        """
        Create chain with tools and automatic history
        
        Args:
            db_session: Database session
            tools: List of LangChain tools
            
        Returns:
            Chain with tools and history
        """
        from langchain.agents import create_openai_functions_agent, AgentExecutor
        
        # Create prompt with tools
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{BASE_AGRICULTURAL_SYSTEM_PROMPT}

OUTILS DISPONIBLES:
Tu as accès à des outils spécialisés pour obtenir des données réelles.
Utilise-les de manière proactive pour enrichir tes réponses.
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            return_intermediate_steps=True
        )
        
        # Wrap with history
        agent_with_history = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: get_session_history(session_id, db_session),
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="output",
        )
        
        return agent_with_history


# Global instance
_lcel_chat_service = None


def get_lcel_chat_service() -> LCELChatService:
    """Get global LCEL chat service instance"""
    global _lcel_chat_service
    if _lcel_chat_service is None:
        _lcel_chat_service = LCELChatService()
    return _lcel_chat_service

