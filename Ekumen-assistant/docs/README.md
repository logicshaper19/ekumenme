# Ekumen Assistant Documentation

**Version:** 2.0.0
**Last Updated:** 2024
**Status:** Phase 2 - Adding Multi-Tenancy & Knowledge Base

---

## 🎯 **START HERE: New Features Documentation**

**If you're implementing the new multi-tenancy, knowledge base, and voice journal features:**

### 🚀 Ready to Code?

1. **[GETTING_STARTED.md](GETTING_STARTED.md)** ⭐ **START HERE - 30 MIN TO FIRST CODE**
   - Step-by-step setup (environment, migration, first task)
   - Your first task: Create OrganizationService
   - Daily workflow and testing strategy

2. **[IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md)** 📋 **YOUR DAILY CHECKLIST**
   - Track progress through all 4 phases
   - Update as you complete tasks
   - Document blockers and lessons learned

### 📖 Architecture & Design Docs

3. **[KEY_DECISIONS.md](KEY_DECISIONS.md)**
   - All architectural decisions for Phase 2
   - What we're doing and NOT doing
   - Why we chose custom JWT over Supabase Auth
   - Organization types (6 types)

4. **[CONVERSATION_ARCHITECTURE.md](CONVERSATION_ARCHITECTURE.md)**
   - ChatGPT-style conversation pattern
   - LangChain integration (no new infrastructure)
   - Knowledge base with sharing permissions
   - **JWT token structure** (CRITICAL)
   - **Message metadata schema** (CRITICAL)
   - **RAG configuration** (chunking, prompt)

5. **[ORGANIZATION_MODEL.md](ORGANIZATION_MODEL.md)**
   - Multi-tenancy model
   - 6 organization types (farm, cooperative, advisor, input_company, research_institute, government_agency)
   - Permission system
   - Farm access control

6. **[BACKEND_IMPLEMENTATION_PLAN.md](BACKEND_IMPLEMENTATION_PLAN.md)**
   - 12-week implementation roadmap
   - Complete database schemas
   - **Service layer architecture** (CRITICAL)
   - **Error handling standards** (CRITICAL)
   - API endpoints
   - Rate limiting

7. **[QUICK_START.md](QUICK_START.md)**
   - Quick reference guide
   - Migration instructions
   - **Testing strategy** (CRITICAL)
   - Testing checklist

---

## 📚 Existing System Documentation

**For understanding the current system (9 agents, 25 tools):**

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Current system architecture
2. **[API_REFERENCE.md](API_REFERENCE.md)** - Current API documentation
3. **[AGENTS_REFERENCE.md](AGENTS_REFERENCE.md)** - All 9 production agents
4. **[TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)** - All 25 agricultural tools
5. **[LANGCHAIN_PATTERNS.md](LANGCHAIN_PATTERNS.md)** - LangChain best practices

---

## 🔧 Development & Deployment

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development setup and guidelines
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment instructions
- **[TESTING.md](TESTING.md)** - Testing guide (may be outdated - see QUICK_START.md for Phase 2 testing)
- **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)** - Supabase configuration

---

## 📜 Historical Documentation

- **[CLEANUP_HISTORY.md](CLEANUP_HISTORY.md)** - Architectural cleanup performed on 2025-10-01

---

## 🎯 System Status

### Phase 1 (Complete) ✅
**Architecture:** Clean ReAct-based with orchestrator
**Agents:** 9 production-ready agents
**Tools:** 25 agricultural tools
**Status:** ✅ Production Ready

### Phase 2 (In Progress) 🚧
**Features:** Multi-tenancy, Knowledge Base, Voice Journal
**Timeline:** 12 weeks
**Status:** 🚧 Documentation Complete, Implementation Starting

**New Features:**
- ✅ Organizations (6 types with multi-tenancy)
- ✅ Knowledge base with RAG (permission-filtered)
- ✅ Voice journal → Auto-create interventions
- ✅ Analytics (KB usage, gaps, coverage)
- ✅ Custom JWT authentication
- ✅ Conversation management (ChatGPT pattern)

### Code Statistics
- **Python Files:** 182 files, 58,405 lines
- **Tests:** 86 files, 26,468 lines
- **Documentation:** 16 files (5 new for Phase 2)

---

## 🚀 Quick Start

### For Phase 2 Implementation (Multi-Tenancy & Knowledge Base)

```bash
# 1. Run Phase 2 migration
cd Ekumen-assistant/scripts/migration
export DATABASE_URL="postgresql://..."
psql $DATABASE_URL -f 02_add_organizations_and_knowledge_base.sql

# 2. Load test data
psql $DATABASE_URL -f 03_seed_test_data.sql

# 3. Read documentation in order
# See "START HERE: New Features Documentation" section above
```

**See [QUICK_START.md](QUICK_START.md) for complete Phase 2 setup guide.**

---

### For Existing System (Phase 1)

```bash
# 1. Clone and setup
git clone https://github.com/logicshaper19/ekumenme.git
cd ekumenme/Ekumen-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run
python -m uvicorn app.main:app --reload

# 4. Test
python tests/test_critical_imports.py
```

---

## 🆘 Support

- **Issues:** GitHub Issues
- **Documentation:** This directory
- **Tests:** Run `python tests/test_critical_imports.py`
