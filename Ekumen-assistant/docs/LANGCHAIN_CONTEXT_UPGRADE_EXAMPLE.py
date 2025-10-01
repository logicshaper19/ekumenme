"""
LangChain Context Management Upgrade Example
Shows how to properly use LangChain's context features
"""

from typing import List, Optional
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json


# ============================================================================
# STEP 1: Create PostgreSQL-backed Message History
# ============================================================================

class PostgresChatMessageHistory(BaseChatMessageHistory):
    """
    Chat message history backed by PostgreSQL
    Integrates with your existing messages table
    """
    
    def __init__(self, session_id: str, db_session: AsyncSession):
        self.session_id = session_id  # This is your conversation_id
        self.db_session = db_session
        self._messages: Optional[List[BaseMessage]] = None
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Lazy load messages from database"""
        if self._messages is None:
            import asyncio
            self._messages = asyncio.run(self._load_messages())
        return self._messages
    
    async def _load_messages(self) -> List[BaseMessage]:
        """Load messages from PostgreSQL"""
        query = text("""
            SELECT content, sender, created_at
            FROM messages
            WHERE conversation_id = :conversation_id
            ORDER BY created_at ASC
        """)
        
        result = await self.db_session.execute(
            query,
            {"conversation_id": self.session_id}
        )
        
        messages = []
        for row in result.fetchall():
            content, sender, created_at = row
            if sender == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
        
        return messages
    
    def add_message(self, message: BaseMessage) -> None:
        """Add message to database"""
        import asyncio
        asyncio.run(self._add_message(message))
    
    async def _add_message(self, message: BaseMessage) -> None:
        """Async add message to database"""
        query = text("""
            INSERT INTO messages (conversation_id, content, sender, message_type)
            VALUES (:conversation_id, :content, :sender, 'text')
        """)
        
        sender = "user" if isinstance(message, HumanMessage) else "agent"
        
        await self.db_session.execute(query, {
            "conversation_id": self.session_id,
            "content": message.content,
            "sender": sender
        })
        await self.db_session.commit()
        
        # Update cache
        if self._messages is not None:
            self._messages.append(message)
    
    def clear(self) -> None:
        """Clear all messages for this conversation"""
        import asyncio
        asyncio.run(self._clear())
    
    async def _clear(self) -> None:
        """Async clear messages"""
        query = text("""
            DELETE FROM messages
            WHERE conversation_id = :conversation_id
        """)
        
        await self.db_session.execute(
            query,
            {"conversation_id": self.session_id}
        )
        await self.db_session.commit()
        self._messages = []


# ============================================================================
# STEP 2: Create Session History Factory
# ============================================================================

def get_session_history(session_id: str, db_session: AsyncSession) -> BaseChatMessageHistory:
    """
    Factory function to get message history for a session
    Used by RunnableWithMessageHistory
    """
    return PostgresChatMessageHistory(session_id, db_session)


# ============================================================================
# STEP 3: Create LCEL Chain with Automatic History
# ============================================================================

def create_agricultural_chat_chain(llm: ChatOpenAI, db_session: AsyncSession):
    """
    Create a chat chain with automatic history management
    Uses LCEL (LangChain Expression Language)
    """
    
    # Create prompt with history placeholder
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Tu es un assistant agricole expert.
        
Utilise l'historique de la conversation pour fournir des réponses contextuelles.
Si l'utilisateur fait référence à quelque chose mentionné précédemment, utilise ce contexte.

Réponds de manière claire, précise et professionnelle."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    # Create chain using LCEL
    chain = prompt | llm | StrOutputParser()
    
    # Wrap with automatic history management
    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: get_session_history(session_id, db_session),
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    
    return chain_with_history


# ============================================================================
# STEP 4: Create Context-Aware RAG Chain
# ============================================================================

def create_context_aware_rag_chain(
    llm: ChatOpenAI,
    vectorstore,
    db_session: AsyncSession
):
    """
    Create RAG chain that's aware of conversation history
    Uses create_history_aware_retriever for better results
    """
    
    # Step 1: Create history-aware retriever
    # This reformulates queries based on chat history
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", """Étant donné l'historique de la conversation et la dernière question de l'utilisateur,
reformule la question pour qu'elle soit compréhensible sans l'historique.

Si la question fait référence à quelque chose mentionné précédemment, inclus ce contexte dans la reformulation.

NE réponds PAS à la question, reformule-la seulement."""),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = create_history_aware_retriever(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        prompt=contextualize_q_prompt
    )
    
    # Step 2: Create QA chain
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", """Tu es un assistant agricole expert.
        
Utilise le contexte suivant pour répondre à la question:

{context}

Si tu ne trouves pas la réponse dans le contexte, dis-le clairement.
Utilise l'historique de la conversation pour fournir des réponses cohérentes."""),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
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


# ============================================================================
# STEP 5: Usage Examples
# ============================================================================

async def example_basic_chat(db_session: AsyncSession):
    """Example: Basic chat with automatic history"""
    
    llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    chain = create_agricultural_chat_chain(llm, db_session)
    
    conversation_id = "abc-123-def-456"
    
    # First message - history is automatically loaded and saved
    response1 = chain.invoke(
        {"input": "Bonjour, j'ai une parcelle de blé de 10 hectares"},
        config={"configurable": {"session_id": conversation_id}}
    )
    print(f"Response 1: {response1}")
    
    # Second message - previous message is automatically in context
    response2 = chain.invoke(
        {"input": "Quel traitement recommandes-tu pour cette parcelle?"},
        config={"configurable": {"session_id": conversation_id}}
    )
    print(f"Response 2: {response2}")
    # The LLM knows "cette parcelle" refers to the 10-hectare wheat field!


async def example_rag_with_history(db_session: AsyncSession, vectorstore):
    """Example: RAG with conversation context"""
    
    llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    chain = create_context_aware_rag_chain(llm, vectorstore, db_session)
    
    conversation_id = "xyz-789-abc-123"
    
    # First question
    response1 = chain.invoke(
        {"input": "Quelles sont les réglementations pour le blé?"},
        config={"configurable": {"session_id": conversation_id}}
    )
    print(f"Answer: {response1['answer']}")
    print(f"Sources: {response1['context']}")
    
    # Follow-up question - "ça" refers to previous context
    response2 = chain.invoke(
        {"input": "Et pour le maïs, c'est pareil?"},
        config={"configurable": {"session_id": conversation_id}}
    )
    print(f"Answer: {response2['answer']}")
    # The retriever knows to search for maize regulations!


async def example_streaming(db_session: AsyncSession):
    """Example: Streaming with automatic history"""
    
    llm = ChatOpenAI(model="gpt-4", temperature=0.1, streaming=True)
    chain = create_agricultural_chat_chain(llm, db_session)
    
    conversation_id = "stream-123"
    
    # Stream response
    async for chunk in chain.astream(
        {"input": "Explique-moi la rotation des cultures"},
        config={"configurable": {"session_id": conversation_id}}
    ):
        print(chunk, end="", flush=True)
    
    # History is automatically saved after streaming!


# ============================================================================
# STEP 6: Integration with Your Chat Service
# ============================================================================

class ImprovedChatService:
    """
    Example of how to integrate into your chat service
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    
    async def process_message(
        self,
        db: AsyncSession,
        conversation_id: str,
        message: str,
        use_rag: bool = False,
        vectorstore = None
    ) -> str:
        """
        Process message with automatic history management
        
        NO MANUAL MESSAGE LOADING/SAVING NEEDED!
        """
        
        # Create appropriate chain
        if use_rag and vectorstore:
            chain = create_context_aware_rag_chain(self.llm, vectorstore, db)
            result = chain.invoke(
                {"input": message},
                config={"configurable": {"session_id": conversation_id}}
            )
            return result["answer"]
        else:
            chain = create_agricultural_chat_chain(self.llm, db)
            result = chain.invoke(
                {"input": message},
                config={"configurable": {"session_id": conversation_id}}
            )
            return result
    
    async def stream_message(
        self,
        db: AsyncSession,
        conversation_id: str,
        message: str
    ):
        """
        Stream message with automatic history
        """
        chain = create_agricultural_chat_chain(self.llm, db)
        
        async for chunk in chain.astream(
            {"input": message},
            config={"configurable": {"session_id": conversation_id}}
        ):
            yield chunk


# ============================================================================
# COMPARISON: Before vs After
# ============================================================================

"""
BEFORE (Manual):
-----------------
# Load conversation
conversation = await get_conversation(db, conversation_id, user_id)

# Load messages
messages = await get_conversation_messages(db, conversation_id)

# Format messages
chat_history = []
for msg in messages:
    if msg.sender == "user":
        chat_history.append(HumanMessage(content=msg.content))
    else:
        chat_history.append(AIMessage(content=msg.content))

# Call LLM
response = llm.invoke([
    SystemMessage(content="You are an assistant"),
    *chat_history,
    HumanMessage(content=user_message)
])

# Save response
await save_message(db, conversation_id, response.content, "agent")


AFTER (Automatic):
------------------
# Just invoke the chain - everything else is automatic!
response = chain.invoke(
    {"input": user_message},
    config={"configurable": {"session_id": conversation_id}}
)

# History is automatically:
# - Loaded from database
# - Passed to LLM
# - Saved back to database
"""

