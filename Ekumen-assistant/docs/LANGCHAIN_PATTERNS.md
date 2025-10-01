# LangChain Patterns & Best Practices

**Last Updated:** 2025-10-01

---

## ReAct Agent Pattern

All agents use the ReAct (Reasoning + Action) pattern.

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# 1. Create prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an agricultural AI assistant..."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])

# 2. Create agent
llm = ChatOpenAI(model="gpt-4", temperature=0)
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

# 3. Create executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# 4. Invoke
result = await agent_executor.ainvoke({
    "input": "user query",
    "chat_history": []
})
```

---

## Tool Pattern

```python
from langchain.tools import tool
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    param: str = Field(description="Parameter description")

@tool(args_schema=ToolInput)
async def my_tool(param: str) -> dict:
    """Tool description for LLM"""
    return {"success": True, "data": "..."}
```

---

## Prompt Pattern

```python
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])
```

---

## Memory Pattern

```python
from langchain.memory import ChatMessageHistory

history = ChatMessageHistory()
history.add_user_message("Hello")
history.add_ai_message("Hi there!")
```

---

## Streaming Pattern

```python
async for chunk in agent_executor.astream({
    "input": query,
    "chat_history": history
}):
    if "output" in chunk:
        yield chunk["output"]
```

---

## Error Handling

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=True,
    max_iterations=10
)
```

---

## Deprecation Handling

```python
# Old (deprecated)
from langchain.vectorstores import Chroma
from langchain.memory import ConversationBufferWindowMemory

# New
from langchain_community.vectorstores import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
```

---

For more details, see [Architecture](ARCHITECTURE.md) and [Agents Reference](AGENTS_REFERENCE.md).
