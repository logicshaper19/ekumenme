# Chat Context Management Guide

**Last Updated:** 2025-09-30  
**Status:** Multi-layered context system with database persistence and LangChain memory

---

## 🎯 Overview

Your chat system manages context through **multiple layers**:

1. **Database Persistence** - PostgreSQL stores all messages
2. **LangChain Memory** - In-memory conversation buffers
3. **Agricultural Context** - Domain-specific context tracking
4. **Performance Optimization** - Caching and query optimization

---

## 📊 Architecture Layers

### **Layer 1: Database Persistence** (PostgreSQL)

**Models:** `app/models/conversation.py`

#### **Conversation Model**
```python
class Conversation(Base):
    id: UUID                          # Unique conversation ID
    user_id: UUID                     # User who owns conversation
    farm_siret: String(14)            # Associated farm (optional)
    title: String(255)                # Conversation title
    agent_type: AgentType             # Which agent (weather, regulatory, etc.)
    status: ConversationStatus        # active, archived, deleted
    
    # Context storage
    context_data: JSONB               # Additional context (JSON)
    summary: Text                     # Conversation summary
    
    # Timestamps
    created_at: DateTime
    updated_at: DateTime
    last_message_at: DateTime
    
    # Relationships
    messages: List[Message]           # All messages in conversation
```

#### **Message Model**
```python
class Message(Base):
    id: UUID                          # Unique message ID
    conversation_id: UUID             # Parent conversation
    content: Text                     # Message content
    sender: String(20)                # "user" or "agent"
    agent_type: AgentType             # Agent that responded (if agent message)
    
    # Threading
    thread_id: String(100)            # For message threads
    parent_message_id: UUID           # For replies
    
    # Metadata
    message_type: String(50)          # "text", "voice", "image"
    message_metadata: JSONB           # Additional data (JSON)
    
    # Performance tracking
    processing_time_ms: Integer       # Response time
    token_count: Integer              # Tokens used
    cost_usd: Numeric(10, 6)          # Cost of processing
    
    created_at: DateTime
```

**Key Features:**
- ✅ All messages persisted to database
- ✅ Full conversation history retrievable
- ✅ JSONB for flexible metadata storage
- ✅ Performance metrics tracked per message
- ✅ Soft delete (status = "deleted")

---

### **Layer 2: LangChain Memory** (In-Memory)

**Service:** `app/services/memory_service.py`

#### **AgriculturalMemory Class**
```python
class AgriculturalMemory(BaseChatMemory):
    conversation_id: str
    user_id: str
    farm_siret: str
    
    # Agricultural-specific context
    agricultural_context: Dict        # Farm data, crops, etc.
    intervention_history: List        # Recent interventions
    regulatory_context: Dict          # Compliance info
    weather_context: Dict             # Weather data
    
    # LangChain chat memory
    chat_memory: ChatMessageHistory   # Recent messages
```

**Memory Types:**

1. **ConversationBufferWindowMemory**
   - Keeps last **20 messages** in memory
   - Fast access for recent context
   - Used for most conversations

2. **ConversationSummaryMemory**
   - Creates AI-generated summaries
   - Used for long conversations (>20 messages)
   - Reduces token usage

**How it works:**
```python
# Get memory for conversation
memory = memory_service.get_memory(
    conversation_id="abc-123",
    user_id="user-456",
    farm_siret="12345678901234"
)

# Save conversation turn
memory.save_context(
    inputs={"input": "Quel temps fait-il?"},
    outputs={"output": "Il fait beau aujourd'hui..."}
)

# Get recent messages (last 10)
recent_messages = memory.chat_memory.messages[-10:]
```

---

### **Layer 3: Context Retrieval Flow**

**When a user sends a message:**

#### **Step 1: Load Conversation**
```python
# app/services/chat_service.py - process_message_with_agent()

conversation = await self.get_conversation(db, conversation_id, user_id)
# Loads conversation with .options(selectinload(Conversation.messages))
# This eagerly loads all messages to avoid N+1 queries
```

#### **Step 2: Build Context**
```python
context = {
    "conversation_id": conversation_id,
    "user_id": user_id,
    "farm_siret": farm_siret or conversation.farm_siret,
    "agent_type": conversation.agent_type,
    "conversation_title": conversation.title
}
```

#### **Step 3: Get Memory Context**
```python
# app/services/memory_service.py

conversation_context = await memory_service.get_conversation_context(
    conversation_id=conversation_id,
    user_id=user_id,
    farm_siret=farm_siret
)

# Returns:
{
    "recent_messages": [
        {"type": "human", "content": "...", "timestamp": "..."},
        {"type": "ai", "content": "...", "timestamp": "..."}
    ],
    "agricultural_context": {...},
    "agricultural_summary": "...",
    "intervention_history": [...],
    "regulatory_context": {...},
    "weather_context": {...},
    "farm_data": {...},
    "conversation_length": 42
}
```

#### **Step 4: Pass to LLM**
```python
# Context is passed to agent processing
result = await self.advanced_langchain_service.process_query(
    query=message_content,
    context=context,  # Includes conversation history
    use_rag=True,
    use_reasoning_chains=True,
    use_tools=True
)
```

---

## 🔄 Message Processing Flow

### **Complete Flow:**

```
User sends message
    ↓
1. Verify conversation exists and belongs to user
    ↓
2. Load conversation with messages (selectinload)
    ↓
3. Build context dict with conversation metadata
    ↓
4. Get memory context (recent messages + agricultural context)
    ↓
5. Determine processing strategy (multi-agent, workflow, or basic)
    ↓
6. Process with appropriate service:
   - Multi-Agent Service (complex queries)
   - LangGraph Workflow (structured queries)
   - Advanced LangChain (general queries)
   - Basic Orchestrator (fallback)
    ↓
7. Save user message to database
    ↓
8. Save AI response to database
    ↓
9. Update memory with conversation turn
    ↓
10. Return response to user
```

---

## 💾 Context Storage Locations

### **1. PostgreSQL Database**

**Table: `conversations`**
- Conversation metadata
- `context_data` (JSONB) - Custom context
- `summary` (Text) - AI-generated summary

**Table: `messages`**
- All messages (user + agent)
- `message_metadata` (JSONB) - Per-message metadata
- Performance metrics (tokens, cost, time)

**Table: `conversation_history`** (via memory_persistence_service)
- Duplicate storage for LangChain integration
- Used by `MemoryPersistenceService`

### **2. In-Memory (Python)**

**MemoryService cache:**
```python
self.memories: Dict[str, AgriculturalMemory] = {}
# Key: conversation_id
# Value: AgriculturalMemory instance
```

**Performance cache:**
```python
# app/services/performance_optimization_service.py
self.query_cache: Dict[str, Any] = {}
# Caches query results for 5 minutes
```

### **3. File System** (Pickle files)

**Location:** `./memory/{conversation_id}.pkl`

**Contents:**
- `chat_memory` - LangChain ChatMessageHistory
- `agricultural_context` - Farm-specific data
- `intervention_history` - Recent interventions
- `regulatory_context` - Compliance info
- `weather_context` - Weather data
- `last_updated` - Timestamp

**Note:** This is a backup/persistence mechanism for memory

---

## 🎯 How Context is Passed to LLM

### **Method 1: Direct Message History**

```python
# app/agents/weather_agent.py (example)

# Get last 6 messages from memory
chat_history = self.memory.chat_memory.messages[-6:]

# Format for LLM
messages = []
for msg in chat_history:
    if isinstance(msg, HumanMessage):
        messages.append({"role": "user", "content": msg.content})
    elif isinstance(msg, AIMessage):
        messages.append({"role": "assistant", "content": msg.content})

# Add to prompt
response = llm.chat(messages)
```

### **Method 2: LangChain Memory Integration**

```python
# LangChain automatically injects memory into prompts

memory = ConversationBufferWindowMemory(
    k=20,  # Last 20 messages
    memory_key="chat_history",
    return_messages=True
)

# Memory is automatically added to chain
chain = LLMChain(llm=llm, memory=memory, prompt=prompt)
response = chain.run(query)
```

### **Method 3: Context in Prompt**

```python
# app/agents/base_agent.py

prompt = f"""
You are an agricultural AI assistant.

Context:
- Conversation ID: {context['conversation_id']}
- Farm SIRET: {context['farm_siret']}
- Agent Type: {context['agent_type']}

Recent conversation:
{format_recent_messages(recent_messages)}

Agricultural context:
{agricultural_summary}

User query: {message}

Provide a helpful response.
"""
```

---

## 📈 Context Window Management

### **Token Limits:**

| Model | Max Tokens | Context Strategy |
|-------|-----------|------------------|
| GPT-4 | 8,192 | Last 20 messages |
| GPT-4-Turbo | 128,000 | Last 50 messages + summary |
| GPT-3.5-Turbo | 16,385 | Last 20 messages |

### **Strategies:**

**1. Window Memory (Default)**
- Keep last 20 messages
- Drop older messages
- Fast and efficient

**2. Summary Memory (Long conversations)**
- Triggered when >20 messages
- AI generates summary of old messages
- Keep summary + recent messages

**3. Selective Context**
- Only include relevant messages
- Use semantic search to find related messages
- Reduces token usage

---

## 🔍 Retrieving Context

### **Get Conversation Messages:**

```python
# API: GET /api/v1/chat/conversations/{conversation_id}/messages

messages = await chat_service.get_conversation_messages(
    db=db,
    conversation_id=conversation_id,
    skip=0,
    limit=100  # Last 100 messages
)
```

### **Get Conversation Context:**

```python
context = await memory_service.get_conversation_context(
    conversation_id=conversation_id,
    user_id=user_id,
    farm_siret=farm_siret
)

# Returns:
# - recent_messages (last 10)
# - agricultural_context
# - intervention_history (last 5)
# - regulatory_context
# - weather_context
# - farm_data
# - conversation_length
```

### **Search Conversations:**

```python
# API: GET /api/v1/chat/conversations/search?query=blé

conversations = await chat_service.search_conversations(
    db=db,
    user_id=user_id,
    query="blé",
    agent_type="farm_data",
    limit=20
)
```

---

## ⚡ Performance Optimizations

### **1. Eager Loading**
```python
# Load conversation with messages in one query
.options(selectinload(Conversation.messages))
```

### **2. Query Caching**
```python
# Cache query results for 5 minutes
result = await performance_service.optimize_query_execution(
    query_func=process_query,
    cache_category="general_query"
)
```

### **3. Message Pagination**
```python
# Don't load all messages at once
messages = await get_conversation_messages(
    skip=0,
    limit=100  # Paginate
)
```

### **4. Selective Context Loading**
```python
# Only load what's needed
recent_messages = memory.chat_memory.messages[-10:]  # Last 10 only
```

---

## 🎯 Summary

### **Context is managed through:**

1. ✅ **PostgreSQL** - Permanent storage of all messages
2. ✅ **LangChain Memory** - In-memory buffer (last 20 messages)
3. ✅ **Agricultural Context** - Domain-specific data tracking
4. ✅ **File System** - Pickle backup of memory
5. ✅ **Performance Cache** - Query result caching

### **Context is passed to LLM via:**

1. ✅ **Direct message history** - Last N messages formatted
2. ✅ **LangChain memory** - Automatic injection
3. ✅ **Context dict** - Metadata and agricultural data
4. ✅ **Prompt engineering** - Formatted context in prompt

### **Key Features:**

- ✅ Full conversation history preserved
- ✅ Efficient context window management
- ✅ Agricultural-specific context tracking
- ✅ Performance optimization with caching
- ✅ Multiple processing strategies
- ✅ Scalable architecture

---

**Your context management is comprehensive and production-ready!** 🎉

