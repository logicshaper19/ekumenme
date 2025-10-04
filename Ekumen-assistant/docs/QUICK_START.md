# Ekumen Backend - Quick Start Guide

**Last Updated:** 2024  
**Status:** Ready for Implementation

---

## 🚀 Getting Started

### 0. Pre-Implementation Checklist ⚠️

**Before running migrations, verify:**

```bash
# 1. Check .gitignore includes .env
cat .gitignore | grep ".env"
# Should show: .env

# 2. Verify Chroma version (must be >= 0.4.0)
pip show chromadb | grep Version
# Should show: Version: 0.4.x or higher

# 3. Verify bcrypt is installed (for password hashing)
pip show bcrypt
# If not installed: pip install bcrypt passlib[bcrypt]

# 4. Create .env file (NEVER commit this!)
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
EOF
```

**CRITICAL SECURITY:**
- ✅ `.env` file MUST be in `.gitignore`
- ✅ Use `SUPABASE_SERVICE_ROLE_KEY` (NOT anon key)
- ✅ Generate unique `SECRET_KEY` with `openssl rand -hex 32`
- ✅ Use separate keys for dev/staging/prod
- ✅ Rotate service role key every 90 days

---

### 1. Run Database Migration

```bash
cd Ekumen-assistant/scripts/migration

# Load environment variables
source ../../.env  # Or: export DATABASE_URL="..."

# Run migration
psql $DATABASE_URL -f 02_add_organizations_and_knowledge_base.sql

# Load test data
psql $DATABASE_URL -f 03_seed_test_data.sql
```

**Verify migration succeeded:**
```bash
# Check tables were created
psql $DATABASE_URL -c "\dt" | grep organizations
# Should show: organizations, organization_memberships, organization_farm_access

# Check test users were created
psql $DATABASE_URL -c "SELECT email FROM users WHERE email LIKE '%@test.com';"
# Should return: farmer@test.com, advisor@test.com, coop@test.com
```

**What this creates:**
- ✅ `organizations` table
- ✅ `organization_memberships` table
- ✅ `organization_farm_access` table
- ✅ `response_feedback` table
- ✅ `knowledge_base_documents` table
- ✅ `voice_journal_entries` table
- ✅ `weather_cache` table
- ✅ Updates `conversations` table (adds organization_id, title, last_message_at)

---

## 📚 Documentation Overview

### Core Documents (Read in This Order)

1. **`KEY_DECISIONS.md`** ⭐ **START HERE**
   - All architectural decisions
   - What we're doing and NOT doing
   - Rationale for each decision

2. **`CONVERSATION_ARCHITECTURE.md`**
   - How chat works (ChatGPT pattern)
   - LangChain integration (no new infrastructure)
   - Knowledge base with sharing
   - **JWT token structure** (CRITICAL)
   - **Message metadata schema** (CRITICAL)
   - Auto-title generation
   - Analytics approach

3. **`ORGANIZATION_MODEL.md`**
   - Organization types and roles
   - Permission system
   - Farm access control
   - No mid-session switching

4. **`BACKEND_IMPLEMENTATION_PLAN.md`**
   - 8-week implementation roadmap
   - **Interventions table schema** (CRITICAL)
   - Database schemas
   - API endpoints
   - Service layer design
   - **Error handling patterns** (CRITICAL)
   - **Rate limiting** (CRITICAL)

5. **`QUICK_START.md`** (This document)
   - Quick reference
   - Testing checklist

---

## 🎯 Key Concepts

### Organizations (Multi-Tenancy)

```
User logs in → Selects organization (if multiple) → Gets JWT with org_id
All API calls filtered by organization_id from JWT token
No mid-session switching (like ChatGPT Teams)
```

**Organization Types:**
- `farm` - Individual farm
- `cooperative` - Agricultural cooperative
- `advisor` - Advisory firm
- `input_company` - Phyto product supplier
- `research_institute` - Research organization

### Knowledge Base (RAG with Permissions)

```
Documents have 3 visibility levels:
  - INTERNAL: Only org members
  - SHARED: Specific orgs/users
  - PUBLIC: All authenticated Ekumen users

LangChain retriever filters by permissions automatically
```

**Example Use Cases:**
- Phyto company shares product specs with customers
- Cooperative shares best practices with members
- Farmer keeps invoices private
- Ekumen provides regulations to all

### Conversations (ChatGPT Pattern)

```
Linear message history (no sub-threading)
"New Chat" creates new conversation
Auto-generate titles from first messages
Store tool calls in message_metadata
Truncate old messages when context full
```

**Already Implemented:**
- ✅ `RunnableWithMessageHistory` (LangChain)
- ✅ `PostgresChatMessageHistory` (saves to DB)
- ✅ `Chroma` vector store (for RAG)

### Voice Journal → Interventions

```
User records voice → Whisper transcribes → Extract data → Validate
→ Auto-create intervention with ALL required fields → Link to journal
```

**All Required Fields Captured:**
- parcelle_id, siret, type_intervention, date_intervention
- description, intrants (products), weather data
- validation_status, compliance_issues, safety_alerts

---

## 🔧 Implementation Phases

### Phase 1: Organizations & Chat (Weeks 1-2)
```
[ ] Create organizations table
[ ] Create memberships table
[ ] Update auth endpoints (org selection)
[ ] Add organization_id to conversations
[ ] Implement auto-title generation
[ ] Add feedback (thumbs up/down)
```

### Phase 2: Knowledge Base (Weeks 3-4)
```
[ ] Create knowledge_base_documents table
[ ] Implement PDF upload
[ ] Process with LangChain (PyPDFLoader)
[ ] Add to Chroma vector store
[ ] Add permission filtering to retriever
[ ] Test internal/shared/public docs
```

### Phase 3: Voice Journal (Weeks 5-6)
```
[ ] Create voice_journal_entries table
[ ] Integrate Whisper API
[ ] Integrate ElevenLabs API
[ ] Implement auto-create intervention
[ ] Test end-to-end workflow
```

### Phase 4: Analytics (Weeks 7-8)
```
[ ] Implement KB usage tracking
[ ] Build admin dashboard APIs
[ ] Track knowledge gaps
[ ] Calculate query coverage
[ ] Performance optimization
```

---

## 📊 Database Schema Quick Reference

### Core Tables

```sql
-- Multi-tenancy
organizations (id, name, type, status)
organization_memberships (org_id, user_id, role)
organization_farm_access (org_id, farm_siret, access_type)

-- Enhanced chat
conversations (id, user_id, organization_id, title, last_message_at)
messages (id, conversation_id, content, sender, message_metadata)
response_feedback (id, message_id, feedback_type, comment)

-- Knowledge base
knowledge_base_documents (
    id, organization_id, filename, file_path,
    visibility, shared_with_organizations, shared_with_users,
    is_ekumen_provided, query_count
)

-- Voice journal
voice_journal_entries (
    id, user_id, organization_id, farm_siret, parcel_id,
    content, intervention_type, products_used,
    weather_conditions, temperature_celsius,
    intervention_id  -- Link to auto-created intervention
)

-- Existing (already in DB)
users, exploitations, parcelles, interventions, intrants
ephy_products, ephy_substances, ephy_usages
crops, diseases, pests
```

---

## 🔑 API Endpoints Quick Reference

### Authentication
```
POST   /api/v1/auth/login                 # Returns orgs if multiple
POST   /api/v1/auth/select-organization   # Select org, get JWT with org_id
POST   /api/v1/auth/register
POST   /api/v1/auth/refresh
```

### Organizations
```
POST   /api/v1/organizations              # Create org
GET    /api/v1/organizations              # List user's orgs
POST   /api/v1/organizations/:id/members  # Add member
POST   /api/v1/organizations/:id/farms    # Grant farm access
```

### Conversations
```
POST   /api/v1/conversations              # Create conversation
GET    /api/v1/conversations              # List (filtered by org from JWT)
GET    /api/v1/conversations/search       # Search conversations
POST   /api/v1/conversations/:id/messages # Send message
POST   /api/v1/messages/:id/feedback      # Thumbs up/down
```

### Knowledge Base
```
POST   /api/v1/knowledge-base/upload      # Upload PDF
GET    /api/v1/knowledge-base              # List accessible docs
PATCH  /api/v1/knowledge-base/:id/share   # Update sharing
GET    /api/v1/knowledge-base/analytics/usage  # Admin analytics
```

### Voice Journal
```
POST   /api/v1/journal/upload             # Upload audio
GET    /api/v1/journal                    # List entries
POST   /api/v1/journal/:id/create-intervention  # Auto-create intervention
```

---

## 🧪 Testing Strategy (CRITICAL)

### 1. Load Test Data

```bash
# Load seed data for consistent testing
psql $DATABASE_URL -f scripts/migration/03_seed_test_data.sql
```

**Test Users Created:**
- `farmer@test.com` (password: `Test1234!`) - Farm owner
- `advisor@test.com` (password: `Test1234!`) - Advisor
- `coop@test.com` (password: `Test1234!`) - Cooperative member

### 2. Unit Tests (pytest)

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run unit tests
pytest tests/unit/ -v --cov=app
```

**What to Test:**
- ✅ Service layer logic (OrganizationService, KnowledgeBaseService)
- ✅ Permission checking (check_user_permission)
- ✅ Product validation fuzzy matching
- ✅ JWT token creation/validation
- ✅ Message metadata schema validation

### 3. Integration Tests

```bash
# Run integration tests (requires test database)
pytest tests/integration/ -v
```

**What to Test:**
- ✅ Full API flows (register → create org → upload PDF → ask question)
- ✅ Organization isolation (user A can't see user B's data)
- ✅ Knowledge base permissions (shared documents work correctly)
- ✅ JWT authentication flow

### 4. E2E Test Scenarios

**Scenario 1: Farmer Journey**
```
1. User registers → Creates farm organization
2. Uploads invoice PDF to knowledge base
3. Asks "How much did I spend on fertilizer?"
4. Gets answer from uploaded invoice
```

**Scenario 2: Cooperative Sharing**
```
1. Cooperative uploads best practices guide
2. Shares with member farmers
3. Farmer asks question
4. Gets answer from cooperative's shared document
```

**Scenario 3: Voice Journal**
```
1. Farmer records: "Applied Roundup on parcel Tuferes today"
2. System transcribes, validates product
3. Auto-creates intervention
4. Links back to journal entry
```

### 5. Testing Checklist

**Before Committing:**
- [ ] All unit tests pass
- [ ] Code coverage > 80%
- [ ] No exposed secrets in code
- [ ] Error handling tested (401, 403, 404, 422)

**Before Deploying:**
- [ ] Migration runs successfully on staging
- [ ] Seed data loads correctly
- [ ] E2E scenarios work end-to-end
- [ ] Rate limiting works
- [ ] JWT expiration works
- [ ] Organization isolation verified

**Phase 1: Organizations**
- [ ] User can create organization
- [ ] User can invite members
- [ ] JWT token contains org_id
- [ ] Conversations filtered by org_id
- [ ] Auto-generated conversation titles work

**Phase 2: Knowledge Base**
- [ ] Upload PDF → processes successfully
- [ ] Internal doc only visible to org members
- [ ] Shared doc visible to specified orgs
- [ ] Public doc visible to all users
- [ ] AI retrieves from accessible docs only
- [ ] Source attribution shown in response

**Phase 3: Voice Journal**
- [ ] Upload audio → Whisper transcribes
- [ ] Extract products → validate against EPHY
- [ ] Auto-create intervention with all fields
- [ ] Link intervention back to journal entry

**Phase 4: Analytics**
- [ ] Track document usage in message_metadata
- [ ] Admin can see most used documents
- [ ] Admin can see knowledge gaps
- [ ] Query coverage calculated correctly

---

## 🚨 Common Pitfalls to Avoid

1. ❌ **Don't add organization selector dropdown** - One org per session!
2. ❌ **Don't build custom RAG** - Use existing LangChain infrastructure
3. ❌ **Don't forget permission filtering** - Always filter by accessible docs
4. ❌ **Don't skip intervention fields** - Voice journal must capture ALL fields
5. ❌ **Don't ignore analytics** - Track KB usage from day one

---

## 📞 Need Help?

**Read these first:**
1. `KEY_DECISIONS.md` - Why we made these choices
2. `CONVERSATION_ARCHITECTURE.md` - How chat works
3. `ORGANIZATION_MODEL.md` - How multi-tenancy works

**Still stuck?**
- Check existing LangChain services: `lcel_chat_service.py`, `postgres_chat_history.py`
- Review existing models: `app/models/`
- Look at existing APIs: `app/api/v1/`

---

## ✅ Ready to Start?

```bash
# 1. Run migration
psql "postgresql://..." -f 02_add_organizations_and_knowledge_base.sql

# 2. Start with Phase 1
# Implement OrganizationService
# Update auth endpoints
# Add organization_id to conversations

# 3. Test as you go
# Write unit tests for each service
# Test with real data

# 4. Iterate quickly
# Get feedback early
# Adjust as needed
```

**Let's build! 🚀**

