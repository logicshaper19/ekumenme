# LangChain Context Features - Usage Analysis

**Date:** 2025-09-30  
**Status:** Partial implementation - Missing key LangChain context features

---

## 🎯 Executive Summary

**Current State:** You're using **basic LangChain memory** but **NOT leveraging** many of LangChain's advanced context management features.

**What You're Using:** ✅
- `ConversationBufferWindowMemory` - Basic message buffer
- `ConversationSummaryMemory` - AI-generated summaries
- `ConversationalRetrievalChain` - RAG with memory
- Manual message history management

**What You're MISSING:** ❌
- `RunnableWithMessageHistory` - Automatic history management
- `create_history_aware_retriever` - Context-aware RAG
- LCEL (LangChain Expression Language) chains
- Automatic context injection
- Message history persistence integration

---

## 📊 Current Implementation

### **What You Have:**

#### **1. Basic Memory (✅ Using)**

<augment_code_snippet path="Ekumen-assistant/app/services/advanced_langchain_service.py" mode="EXCERPT">
````python
# Initialize memory
self.memory = ConversationBufferWindowMemory(
    k=10,  # Last 10 messages
    memory_key="chat_history",
    return_messages=True
)
````
</augment_code_snippet>

**Issue:** This memory is **NOT connected to your database**. It's only in-memory and gets lost when service restarts.

#### **2. ConversationalRetrievalChain (✅ Using)**

<augment_code_snippet path="Ekumen-assistant/app/services/advanced_langchain_service.py" mode="EXCERPT">
````python
self.rag_chain = ConversationalRetrievalChain.from_llm(
    llm=self.llm,
    retriever=retriever,
    memory=self.memory,  # Uses in-memory only
    return_source_documents=True,
    verbose=True
)
````
</augment_code_snippet>

**Issue:** Memory is not persisted. Each conversation starts fresh.

#### **3. Manual Context Passing (✅ Using)**

You're manually loading messages from database and formatting them:

<augment_code_snippet path="Ekumen-assistant/app/services/memory_service.py" mode="EXCERPT">
````python
# Get recent messages
recent_messages = memory.chat_memory.messages[-10:]

# Format for LLM
for msg in recent_messages:
    if isinstance(msg, HumanMessage):
        messages.append({"role": "user", "content": msg.content})
    elif isinstance(msg, AIMessage):
        messages.append({"role": "assistant", "content": msg.content})
````
</augment_code_snippet>

**Issue:** This is manual work that LangChain can do automatically.

---

## ❌ What You're MISSING

### **1. RunnableWithMessageHistory** (NOT USING)

**What it does:**
- Automatically loads conversation history from database
- Automatically saves new messages
- Handles session management
- Integrates with any storage backend

**Example of what you SHOULD be doing:**

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory

# Create a chain
chain = prompt | llm | output_parser

# Wrap with automatic history management
chain_with_history = RunnableWithMessageHistory(
    chain,
    # Function to get message history for a session
    lambda session_id: SQLChatMessageHistory(
        session_id=session_id,
        connection_string="postgresql://..."
    ),
    input_messages_key="input",
    history_messages_key="chat_history",
)

# Use it - history is automatically loaded and saved!
response = chain_with_history.invoke(
    {"input": "What's the weather?"},
    config={"configurable": {"session_id": conversation_id}}
)
```

**Benefits:**
- ✅ Automatic history loading from database
- ✅ Automatic history saving
- ✅ No manual message formatting
- ✅ Works with any storage backend
- ✅ Session management built-in

### **2. create_history_aware_retriever** (NOT USING)

**What it does:**
- Makes RAG context-aware of conversation history
- Reformulates queries based on chat history
- Better retrieval results

**Example:**

```python
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Create context-aware retriever
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", "Given chat history and latest question, reformulate it as standalone question."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

history_aware_retriever = create_history_aware_retriever(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    prompt=contextualize_q_prompt
)

# Now retrieval considers conversation context!
```

**Benefits:**
- ✅ Better RAG results with context
- ✅ Handles follow-up questions ("What about that?")
- ✅ Automatic query reformulation

### **3. create_retrieval_chain** (NOT USING)

**What it does:**
- Combines retrieval + generation in one chain
- Handles context passing automatically
- Built-in history awareness

**Example:**

```python
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Create QA chain
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using the following context:\n\n{context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

# Combine with retriever
rag_chain = create_retrieval_chain(
    history_aware_retriever,
    question_answer_chain
)

# Use with history
response = rag_chain.invoke({
    "input": "What's the weather?",
    "chat_history": chat_history
})
```

### **4. LCEL (LangChain Expression Language)** (NOT USING)

**What it is:**
- Modern way to build LangChain chains
- Uses `|` operator to chain components
- Automatic streaming, batching, async support

**Example:**

```python
from langchain_core.runnables import RunnablePassthrough

# LCEL chain
chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
        "chat_history": lambda x: get_chat_history(x["session_id"])
    }
    | prompt
    | llm
    | StrOutputParser()
)

# Automatic streaming support
for chunk in chain.stream({"question": "What's the weather?", "session_id": "123"}):
    print(chunk, end="", flush=True)
```

**Benefits:**
- ✅ Cleaner code
- ✅ Automatic streaming
- ✅ Automatic batching
- ✅ Better error handling
- ✅ Easier to compose

### **5. BaseChatMessageHistory Integration** (PARTIALLY USING)

You have `AgriculturalMemory(BaseChatMemory)` but it's not integrated with LangChain's automatic history management.

**What you should do:**

```python
from langchain_community.chat_message_histories import SQLChatMessageHistory

class PostgresChatMessageHistory(BaseChatMessageHistory):
    """Custom message history backed by PostgreSQL"""
    
    def __init__(self, session_id: str, connection_string: str):
        self.session_id = session_id
        self.connection_string = connection_string
    
    @property
    def messages(self) -> List[BaseMessage]:
        # Load from database
        return self._load_messages_from_db()
    
    def add_message(self, message: BaseMessage) -> None:
        # Save to database
        self._save_message_to_db(message)
    
    def clear(self) -> None:
        # Clear from database
        self._clear_messages_from_db()

# Use with RunnableWithMessageHistory
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: PostgresChatMessageHistory(
        session_id=session_id,
        connection_string=DATABASE_URL
    ),
    input_messages_key="input",
    history_messages_key="chat_history",
)
```

---

## 🔍 Comparison: Current vs. Recommended

### **Current Approach:**

```python
# 1. Manually load conversation
conversation = await get_conversation(db, conversation_id, user_id)

# 2. Manually load messages
messages = await get_conversation_messages(db, conversation_id)

# 3. Manually format messages
chat_history = []
for msg in messages:
    if msg.sender == "user":
        chat_history.append(HumanMessage(content=msg.content))
    else:
        chat_history.append(AIMessage(content=msg.content))

# 4. Manually pass to LLM
response = llm.invoke([
    SystemMessage(content="You are an assistant"),
    *chat_history,
    HumanMessage(content=user_message)
])

# 5. Manually save response
await save_message(db, conversation_id, response.content, "agent")
```

**Issues:**
- ❌ Lots of manual work
- ❌ Error-prone
- ❌ Not using LangChain features
- ❌ Hard to maintain

### **Recommended Approach:**

```python
# 1. Create chain with automatic history
chain = prompt | llm | output_parser

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,  # Function to get history
    input_messages_key="input",
    history_messages_key="chat_history",
)

# 2. Use it - everything automatic!
response = chain_with_history.invoke(
    {"input": user_message},
    config={"configurable": {"session_id": conversation_id}}
)

# History is automatically loaded and saved!
```

**Benefits:**
- ✅ Automatic history loading
- ✅ Automatic history saving
- ✅ Less code
- ✅ Fewer bugs
- ✅ Uses LangChain features

---

## 📋 Recommendations

### **Priority 1: Implement RunnableWithMessageHistory**

**Why:** Automatic history management, less manual work

**How:**
1. Create `PostgresChatMessageHistory` class
2. Wrap your chains with `RunnableWithMessageHistory`
3. Remove manual message loading/saving code

**Impact:** 🔥🔥🔥 High - Reduces code by 50%, fewer bugs

### **Priority 2: Use LCEL Chains**

**Why:** Modern, cleaner, automatic streaming

**How:**
1. Rewrite chains using `|` operator
2. Use `RunnablePassthrough` for context
3. Enable automatic streaming

**Impact:** 🔥🔥 Medium - Better code quality, streaming support

### **Priority 3: Implement create_history_aware_retriever**

**Why:** Better RAG with conversation context

**How:**
1. Create contextualize prompt
2. Use `create_history_aware_retriever`
3. Integrate with RAG chain

**Impact:** 🔥🔥 Medium - Better RAG results

### **Priority 4: Use create_retrieval_chain**

**Why:** Simplified RAG implementation

**How:**
1. Replace `ConversationalRetrievalChain`
2. Use `create_retrieval_chain` + `create_stuff_documents_chain`
3. Integrate with history-aware retriever

**Impact:** 🔥 Low - Cleaner code, same functionality

---

## 🎯 Summary

### **Current State:**

| Feature | Status | Notes |
|---------|--------|-------|
| Basic Memory | ✅ Using | In-memory only, not persisted |
| ConversationalRetrievalChain | ✅ Using | Old API, not context-aware |
| Manual History Management | ✅ Using | Lots of manual code |
| RunnableWithMessageHistory | ❌ NOT Using | Missing automatic history |
| LCEL Chains | ❌ NOT Using | Using old chain API |
| create_history_aware_retriever | ❌ NOT Using | RAG not context-aware |
| Automatic Streaming | ❌ NOT Using | Manual streaming implementation |

### **What You're Missing:**

1. **Automatic history management** - Doing it manually
2. **Context-aware RAG** - RAG doesn't consider chat history
3. **LCEL chains** - Using old chain API
4. **Automatic streaming** - Manual implementation
5. **Integrated persistence** - Memory not connected to database

### **Impact:**

- 🔴 **More code to maintain** - Manual history management
- 🔴 **More bugs** - Manual formatting, saving, loading
- 🔴 **Worse RAG results** - Not context-aware
- 🔴 **Missing features** - No automatic streaming
- 🔴 **Not using LangChain power** - Doing manually what LangChain does automatically

---

## 🚀 Next Steps

1. **Study LangChain docs** on `RunnableWithMessageHistory`
2. **Implement PostgresChatMessageHistory** class
3. **Refactor chains** to use LCEL
4. **Add history-aware retriever** for better RAG
5. **Remove manual history code** - let LangChain handle it

**Estimated effort:** 2-3 days  
**Impact:** Significant - Better code, fewer bugs, more features

---

**Bottom Line:** You're using LangChain but not leveraging its context management features. You're doing manually what LangChain can do automatically and better.

