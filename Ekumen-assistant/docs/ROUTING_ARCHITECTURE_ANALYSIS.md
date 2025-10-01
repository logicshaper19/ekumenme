# Routing Architecture Analysis

## 🤔 Question: Do we route everything through the orchestrator?

**Short Answer**: **NO** - The system has **multiple routing layers** and the orchestrator is NOT the only routing mechanism.

---

## 📊 Current Routing Architecture (Multi-Layered)

### Layer 1: **User-Selected Agent** (Conversation Level)
- **Location**: `chat.py` → `chat_service.py`
- **How it works**: User creates a conversation with a specific `agent_type`
- **Example**: User selects "crop_health" agent when creating conversation
- **Code**: `conversation.agent_type` is stored and used throughout the conversation

### Layer 2: **Processing Strategy Router** (Message Level)
- **Location**: `chat_service.py` → `_determine_processing_strategy()`
- **How it works**: Analyzes message complexity and routes to different processing systems
- **Routes to**:
  - `multi_agent` - Complex queries (3+ domain indicators)
  - `workflow` - Medium complexity (2+ domain indicators)
  - `advanced` - Simple queries (< 2 domain indicators)

### Layer 3: **Service-Level Routers** (Multiple Systems)
The system has **at least 3 different routing services**:

#### A. **UnifiedRouterService** (3-Tier Hybrid)
- **File**: `unified_router_service.py`
- **Tiers**:
  1. Pattern matching (< 1ms, ~70% coverage)
  2. Semantic embeddings (10-50ms, ~20% coverage)
  3. LLM fallback (1-2s, ~10% coverage)
- **Routes to**: `ExecutionPath` (DIRECT_ANSWER, SINGLE_TOOL, MULTI_TOOL, WORKFLOW, ORCHESTRATOR)

#### B. **ConditionalRoutingService** (Decision Tree)
- **File**: `conditional_routing_service.py`
- **How it works**: Decision tree based on query characteristics
- **Routes to**: Specific service endpoints (weather_agent, regulatory_agent, planning_agent, etc.)

#### C. **MultiAgentConversationService** (Sequential Routing)
- **File**: `multi_agent_conversation_service.py`
- **How it works**: Routes between specialized experts in sequence
- **Routes**: weather → regulatory → agronomist → economist → consensus

### Layer 4: **Orchestrator Agent** (When Invoked)
- **File**: `app/agents/orchestrator.py`
- **When used**: Only when routing decision determines orchestrator is needed
- **What it does**: Coordinates multiple specialized agents using ReAct reasoning
- **NOT used for**: Simple single-domain queries

### Layer 5: **Simple Router** (Currently UNUSED)
- **File**: `prompts/simple_router.py`
- **Status**: ⚠️ **Created but NOT integrated into any service**
- **Purpose**: Keyword-based fallback routing
- **Functions**: `route_to_agent()`, `should_use_orchestrator()`
- **Problem**: No service is actually calling these functions!

---

## 🔍 Current Flow Example

```
User Query: "Puis-je traiter mes tomates cette semaine?"
    ↓
[Layer 1] Conversation has agent_type = "general"
    ↓
[Layer 2] _determine_processing_strategy() → "workflow" (2 domains: treatment + weather)
    ↓
[Layer 3] LangGraphWorkflowService.process_query()
    ↓
[Layer 4] Orchestrator coordinates: regulatory + weather + crop_health agents
    ↓
Response synthesized and returned
```

---

## ❌ Problems with Current Architecture

### 1. **simple_router.py is NOT being used**
- We created `simple_router.py` and `prompt_registry.py`
- **NO service is importing or using them**
- They exist only in `prompts/__init__.py` exports
- **Dead code** that doesn't affect the system

### 2. **Multiple Overlapping Routers**
- `UnifiedRouterService` (3-tier hybrid)
- `ConditionalRoutingService` (decision tree)
- `MultiAgentConversationService` (sequential)
- `simple_router.py` (unused)
- Each has different logic and routes to different destinations

### 3. **Inconsistent Routing Logic**
- `chat_service.py` uses keyword counting
- `unified_router_service.py` uses pattern matching + embeddings + LLM
- `conditional_routing_service.py` uses decision trees
- No single source of truth

### 4. **Orchestrator is NOT the Central Router**
- Orchestrator is just **one of many routing destinations**
- It's invoked **after** routing decisions are made
- It doesn't handle ALL routing - only multi-agent coordination

---

## ✅ Recommended Architecture (Two Options)

### Option 1: **Orchestrator-First (Simplest)**
Route **everything** through the orchestrator agent, let it decide:

```
User Query
    ↓
Orchestrator Agent (ReAct)
    ↓
Decides: Single agent? Multiple agents? Direct answer?
    ↓
Executes and returns
```

**Pros**:
- Single routing logic (in orchestrator prompt)
- Leverages LLM intelligence
- Consistent decision-making
- Simpler architecture

**Cons**:
- Higher latency (LLM call for every query)
- Higher cost (GPT-4 for routing)
- Overkill for simple queries

### Option 2: **Hybrid with Orchestrator as Fallback**
Use fast routing for simple cases, orchestrator for complex:

```
User Query
    ↓
Fast Pattern Matching (simple_router.py)
    ↓
├─ Simple single-domain → Direct to specialized agent
├─ Multi-domain/complex → Orchestrator
└─ Uncertain → Orchestrator
```

**Pros**:
- Fast for simple queries (< 1ms)
- Intelligent for complex queries
- Cost-effective
- Best of both worlds

**Cons**:
- More complex architecture
- Need to maintain pattern matching rules
- Two routing systems to test

---

## 🎯 Recommendation

**Use Option 2 (Hybrid)** but **actually integrate simple_router.py**:

1. **Delete unused routers**:
   - `unified_router_service.py` (overlaps with simple_router)
   - `conditional_routing_service.py` (overlaps with simple_router)

2. **Integrate simple_router.py** into `chat_service.py`:
   ```python
   from app.prompts.simple_router import route_to_agent, should_use_orchestrator
   
   if should_use_orchestrator(message_content):
       # Use orchestrator for complex queries
       agent_type = "orchestrator"
   else:
       # Use specialized agent for simple queries
       agent_type = route_to_agent(message_content)
   ```

3. **Keep orchestrator** for multi-domain coordination

4. **Result**: Clean 2-tier routing
   - Tier 1: Fast keyword matching (simple_router.py)
   - Tier 2: Intelligent orchestration (orchestrator agent)

---

## 📋 Action Items

- [ ] Decide: Option 1 (Orchestrator-First) or Option 2 (Hybrid)?
- [ ] If Option 1: Delete all routers, route everything to orchestrator
- [ ] If Option 2: Integrate simple_router.py, delete overlapping routers
- [ ] Update chat_service.py to use chosen routing strategy
- [ ] Remove unused routing services
- [ ] Test routing decisions with real queries
- [ ] Document final routing architecture

---

## 🚨 Current Status

**The simple_router.py we just created is NOT being used anywhere!**

We need to either:
1. **Integrate it** into the actual services, OR
2. **Delete it** if we're going orchestrator-first

The current system has **too many routers** doing similar things with different logic.

