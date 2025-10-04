# Ekumen Platform - Key Architectural Decisions

**Date:** 2024  
**Status:** Approved  
**Context:** Strategic backend architecture discussion

---

## 🎯 Core Principles

1. **Follow ChatGPT's Pattern** - Don't reinvent the wheel, use familiar UX
2. **Leverage Existing LangChain Infrastructure** - No new frameworks or tools
3. **Keep It Simple** - Pragmatic over perfect
4. **Multi-Tenancy First** - Organizations are core to the platform

---

## 📋 Key Decisions

### 1. ❌ NO Organization Selector Dropdown

**Decision:** Users stay in ONE organization per session (like ChatGPT Teams).

**Rationale:**
- ChatGPT doesn't let you switch workspaces mid-session
- Simpler UX - no confusion about current context
- Simpler implementation - org_id in JWT token
- More secure - can't accidentally leak data between orgs

**Implementation:**
```
User with ONE org → Auto-login to that org
User with MULTIPLE orgs → Select org ONCE at login
To switch → Log out and log back in (or use different browser tab)
```

**Rejected Alternative:** Dropdown selector in UI (too complex, not standard)

---

### 2. ✅ Use Existing LangChain Infrastructure

**Decision:** NO new infrastructure. Use what we already have.

**What We Already Have:**
- ✅ `RunnableWithMessageHistory` - Automatic conversation memory
- ✅ `Chroma` vector store - For RAG
- ✅ `PostgresChatMessageHistory` - Saves to messages table
- ✅ `PyPDFLoader`, `RecursiveCharacterTextSplitter` - Document processing
- ✅ `create_retrieval_chain` - RAG with history

**What We Add:**
- ✅ Permission filtering in retriever (simple SQL + filter)
- ✅ Organization-specific document access
- ✅ Track usage in existing message_metadata

**Rejected Alternative:** Build custom RAG system (unnecessary, LangChain works)

---

### 3. ✅ Knowledge Base with Three Visibility Levels

**Decision:** Documents can be internal, shared, or public.

**Visibility Levels:**

#### INTERNAL (Default)
- Only organization members can access
- Example: Farmer's invoices, internal records

#### SHARED
- Shared with specific organizations or users
- Example: Phyto company shares product specs with customers
- Example: Cooperative shares best practices with members

#### PUBLIC (Ekumen-provided)
- Available to ALL authenticated Ekumen users
- Example: Regulations, general agricultural guides
- Curated by Ekumen team

**Implementation:**
```sql
knowledge_base_documents:
  - visibility: 'internal' | 'shared' | 'public'
  - shared_with_organizations: UUID[]
  - shared_with_users: UUID[]
  - is_ekumen_provided: BOOLEAN
```

**Permission Filtering:**
```python
# LangChain retriever with permission filter
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {"doc_id": {"$in": accessible_docs}}
    }
)
```

**Rejected Alternative:** Single global knowledge base (no privacy control)

---

### 4. ✅ Voice Journal Auto-Creates Interventions

**Decision:** Voice journal entries automatically create interventions in MesParcelles.

**Rationale:**
- Farmers record field work via voice
- System validates and structures the data
- Auto-creates intervention with ALL required fields
- Links back to journal entry for audit trail

**Required Fields Captured:**
```python
intervention = Intervention(
    parcelle_id=journal.parcel_id,
    siret=journal.farm_siret,
    type_intervention=journal.intervention_type,
    date_intervention=journal.intervention_date,
    description=journal.content,
    intrants=journal.products_used,  # Validated against EPHY
    extra_data={
        "weather_conditions": journal.weather_conditions,
        "temperature_celsius": journal.temperature_celsius,
        "humidity_percent": journal.humidity_percent,
        "wind_speed_kmh": journal.wind_speed_kmh,
        "source": "voice_journal",
        "journal_entry_id": journal.id,
        "validation_status": journal.validation_status
    }
)
```

**Rejected Alternative:** Manual intervention creation (too much friction)

---

### 5. ✅ Analytics Focus on Knowledge Base

**Decision:** Track how well knowledge base is being used, identify gaps.

**Key Metrics:**

#### For Ekumen Admin:
- Most used documents
- Knowledge gaps (questions with no KB results)
- Query coverage (% of questions answered by KB)
- User satisfaction (thumbs up/down)

#### For Phyto Companies:
- How often their shared documents are used
- Which products are mentioned most
- Customer questions about their products
- Effectiveness of shared technical sheets

#### For Cooperatives:
- Member engagement with shared best practices
- Most common questions from members
- Knowledge gaps to fill

**Implementation:**
```sql
-- Track in message_metadata
{
    "knowledge_base_used": true,
    "documents_retrieved": [
        {"doc_id": "uuid", "filename": "roundup_spec.pdf", "relevance": 0.89}
    ]
}

-- Analytics queries
SELECT filename, query_count FROM knowledge_base_documents ORDER BY query_count DESC;
SELECT content FROM messages WHERE (metadata->>'knowledge_base_used')::boolean = false;
```

**Rejected Alternative:** No analytics (can't improve what you don't measure)

---

### 6. ✅ Conversation Pattern: Linear History

**Decision:** Follow ChatGPT's linear conversation model.

**Pattern:**
- ✅ Linear message history (no sub-threading)
- ✅ "New Chat" button creates new conversation
- ✅ Auto-generate titles from first messages
- ✅ Store tool calls in message_metadata
- ✅ Truncate old messages when context is full (no summarization)

**What We DON'T Do:**
- ❌ Sub-threading within conversations
- ❌ Message branching
- ❌ Conversation summarization (keep it simple)

**Rejected Alternative:** Complex threading model (too complicated for farmers)

---

### 7. ✅ Organization Types

**Decision:** Support 6 organization types (5 customer-facing + 1 internal).

**Customer-Facing Types:**

1. **FARM** - Individual farm enterprise
   - Roles: owner, admin, worker, viewer
   - Use case: Farmer managing their own operations

2. **COOPERATIVE** - Agricultural cooperative
   - Roles: owner, admin, advisor, member, viewer
   - Use case: Cooperative providing services to member farmers

3. **ADVISOR** - Advisory firm / consulting
   - Roles: owner, admin, advisor, viewer
   - Use case: Advisory firm managing multiple client farms

4. **INPUT_COMPANY** - Phyto product supplier
   - Roles: owner, admin, sales_rep, technical_advisor, viewer
   - Use case: Track product usage, provide technical support

5. **RESEARCH_INSTITUTE** - Research & development
   - Roles: owner, researcher, viewer
   - Use case: Agricultural research, data analysis

**Internal Type:**

6. **GOVERNMENT_AGENCY** - Ekumen platform itself
   - Roles: owner, admin
   - Use case: Platform administration, public knowledge base curation
   - Example: "Ekumen Platform" organization for Ekumen-curated content

**Rejected Alternative:** Single "organization" type (not flexible enough)

---

### 8. ✅ Authentication with Organization Context

**Decision:** Embed organization_id in JWT token.

**Flow:**
```
1. User logs in
2. If user has ONE org → Auto-select, return token with org_id
3. If user has MULTIPLE orgs → Return list, user selects
4. POST /api/v1/auth/select-organization → Return token with org_id
5. All subsequent API calls use org_id from JWT
```

**Benefits:**
- ✅ Stateless (no server-side session)
- ✅ Secure (can't forge org_id)
- ✅ Simple (no complex state management)

**Rejected Alternative:** Session-based org selection (stateful, complex)

---

## 🚫 What We're NOT Doing (For Now)

1. ❌ **Notifications** (email, push, SMS)
2. ❌ **Billing & Subscriptions**
3. ❌ **GDPR compliance features** (data export, deletion)
4. ❌ **Mobile app**
5. ❌ **Conversation sharing** (share with advisor)
6. ❌ **Message bookmarks**
7. ❌ **PDF/CSV export** (just copy to clipboard)
8. ❌ **Organization selector dropdown** (one org per session)
9. ❌ **Conversation summarization** (truncate instead)
10. ❌ **Sub-threading** (linear history only)

---

## ✅ What We ARE Doing

1. ✅ **Organizations** (multi-tenancy)
2. ✅ **Knowledge base** (PDFs with sharing)
3. ✅ **Voice journal** (with auto-intervention creation)
4. ✅ **Analytics** (KB usage, gaps, coverage)
5. ✅ **Conversation search** (find past discussions)
6. ✅ **Feedback** (thumbs up/down)
7. ✅ **File storage** (Supabase Storage)
8. ✅ **Weather integration** (weatherapi.com)
9. ✅ **EPHY integration** (15,006 products)
10. ✅ **MesParcelles integration** (farm data)

---

## 🔐 Authentication: Custom JWT (NOT Supabase Auth)

**Decision:** Use custom JWT with organization context

**Why:**
- Need `organization_id` in JWT payload for multi-tenancy
- Supabase Auth doesn't support custom claims easily
- Backend handles ALL permissions (not RLS)

**Implementation:**
```python
# Custom JWT payload
{
    "user_id": "uuid",
    "organization_id": "uuid",  # Required for multi-tenancy
    "organization_role": "owner",
    "exp": timestamp
}

# Supabase Storage with SERVICE ROLE KEY
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

**RLS Policies:** REMOVED - backend handles permissions

---

## 🔧 Critical Implementation Details (ALL P0/P1 Fixes Applied)

### 1. Conversations Table - Soft Delete

```sql
ALTER TABLE conversations
ADD COLUMN status VARCHAR(20) DEFAULT 'active',  -- 'active', 'archived', 'deleted'
ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
```

### 2. Chroma Vector Store - Correct Filter Syntax (FIXED)

**WRONG:**
```python
search_kwargs={"filter": {"document_id": {"$in": accessible_docs}}}  # ❌ Wrong parameter
```

**CORRECT:**
```python
# When ingesting, store document_id in metadata:
chunk.metadata["document_id"] = str(doc.id)

# When retrieving, use 'where' parameter (not 'filter'):
search_kwargs={
    "k": 5,
    "where": {
        "document_id": {"$in": accessible_docs}  # ✅ Use 'where', not 'filter'
    }
}
```

### 3. Message Metadata - Exact Schema

**All developers MUST use this structure:**
```json
{
  "tool_calls": [...],
  "knowledge_base_used": true,
  "documents_retrieved": [...],
  "processing_time_ms": 1250,
  "token_count": {"prompt_tokens": 450, "completion_tokens": 120, "total_tokens": 570},
  "model": "gpt-4",
  "temperature": 0.1,
  "cost_usd": 0.0342
}
```

See `CONVERSATION_ARCHITECTURE.md` section 7 for complete schema.

### 4. JWT Token Structure

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "organization_id": "uuid",
  "organization_role": "owner",
  "user_role": "farmer",
  "iat": 1234567890,
  "exp": 1234571490
}
```

See `CONVERSATION_ARCHITECTURE.md` section 9 for auth flows and middleware.

### 5. Interventions Table Schema

```sql
CREATE TABLE interventions (
    parcelle_id UUID,
    siret VARCHAR(14),
    type_intervention VARCHAR(100),
    date_intervention TIMESTAMP,
    description TEXT,
    intrants JSONB,  -- Array of {code_amm, nom_produit, dose, unite}
    extra_data JSONB  -- Weather, validation, compliance
);
```

See `BACKEND_IMPLEMENTATION_PLAN.md` for complete schema and voice journal mapping.

### 6. Error Handling Patterns

- **Whisper API**: Retry 3 times with exponential backoff, save audio if all fail
- **PDF Processing**: Mark as failed, clean up partial data from vector store
- **Unauthorized Access**: Return 403 with clear message about organization context

See `BACKEND_IMPLEMENTATION_PLAN.md` section on Error Handling.

### 7. Rate Limiting

```python
RATE_LIMITS = {
    "whisper_transcription": "10/hour",
    "pdf_upload": "20/day",
    "chat_messages": "100/hour"
}
```

See `BACKEND_IMPLEMENTATION_PLAN.md` section on Rate Limiting.

### 8. Missing Indexes Added

```sql
CREATE INDEX idx_conversations_user_org_time ON conversations(user_id, organization_id, last_message_at DESC);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);
CREATE INDEX idx_kb_docs_org_status_visibility ON knowledge_base_documents(organization_id, processing_status, visibility);
```

### 9. Weather Cache Expiration

```sql
ALTER TABLE weather_cache
ADD COLUMN data_type VARCHAR(20),  -- 'historical', 'current', 'forecast'
ADD COLUMN expires_at TIMESTAMP;
```

### 10. LangChain Chunking & RAG Prompt

**Chunking parameters:**
```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

**RAG prompt:** Prevents hallucinations, requires source citations

See CONVERSATION_ARCHITECTURE.md section 6 for complete implementation.

### 11. File Upload Flow

**Direct upload to Supabase Storage** (not through backend)
1. Request signed URL
2. Upload directly
3. Notify backend
4. Process in background

### 12. Product Validation - Fuzzy Matching

**Uses PostgreSQL full-text search + trigrams:**
- Exact match first (fastest)
- Full-text search (handles variations)
- Fuzzy match (handles typos like "Rondup" → "ROUNDUP")

See BACKEND_IMPLEMENTATION_PLAN.md section 2.5 for complete implementation.

### 13. Rollback Script & Seed Data

- `02_rollback_organizations_and_knowledge_base.sql` - Safe rollback
- `03_seed_test_data.sql` - Consistent test data for all developers

### 14. Realistic Timeline

**12 weeks** (not 8) - includes 50% buffer for unknowns

---

## 📊 Success Metrics

### Phase 1 (Weeks 1-2): Organizations & Chat
- [ ] Users can create organizations
- [ ] Users can invite members
- [ ] Conversations scoped to organization
- [ ] Auto-generated conversation titles

### Phase 2 (Weeks 3-4): Knowledge Base
- [ ] Users can upload PDFs
- [ ] Documents processed into vector store
- [ ] Permission-filtered retrieval works
- [ ] Shared documents accessible to customers

### Phase 3 (Weeks 5-6): Voice Journal
- [ ] Users can record voice notes
- [ ] Whisper transcription works
- [ ] Auto-create interventions with all fields
- [ ] ElevenLabs TTS confirmation

### Phase 4 (Weeks 7-8): Analytics & Polish
- [ ] Knowledge base usage tracked
- [ ] Knowledge gaps identified
- [ ] Admin dashboard shows metrics
- [ ] Performance optimized

---

## 🎯 Next Steps

1. ✅ **Review this document** - Confirm all decisions
2. ✅ **Run SQL migration** - Create all tables in Supabase
3. ✅ **Start Phase 1** - Organizations & enhanced chat
4. ✅ **Iterate quickly** - Get feedback early

**All decisions documented and approved!** 🚀

