# Getting Started with Phase 2 Implementation

**Goal:** Get from documentation to first line of code in 30 minutes

---

## 🎯 Where to Start

You have **excellent documentation** ready. Here's the exact order to follow:

### Step 1: Read Documentation (15 minutes)

**Read these in order:**

1. **[KEY_DECISIONS.md](KEY_DECISIONS.md)** (5 min)
   - Understand WHY we made each decision
   - Key takeaway: Custom JWT, no org selector, 6 org types

2. **[BACKEND_IMPLEMENTATION_PLAN.md](BACKEND_IMPLEMENTATION_PLAN.md)** (10 min)
   - Skim the whole document
   - Focus on:
     - Pre-Implementation Requirements (lines 70-123)
     - Service Layer Architecture (lines 250-278)
     - Error Handling Strategy (lines 1016-1242)

3. **[IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md)** (bookmark for later)
   - This is your daily checklist
   - Update it as you complete tasks

---

### Step 2: Set Up Environment (10 minutes)

**Run these commands:**

```bash
# 1. Navigate to project
cd /Users/elisha/ekumenme/Ekumen-assistant

# 2. Check .gitignore
cat .gitignore | grep "^\.env$"
# If not found:
echo ".env" >> .gitignore

# 3. Check Chroma version
pip show chromadb | grep Version
# If < 0.4.0:
pip install --upgrade chromadb>=0.4.0

# 4. Install bcrypt
pip show bcrypt || pip install passlib[bcrypt]

# 5. Create .env file
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.ghsfhuekuebwnrjhlitr.supabase.co:5432/postgres

# Supabase Storage
SUPABASE_URL=https://ghsfhuekuebwnrjhlitr.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY

# Custom JWT
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
EOF

# 6. Edit .env with real values
nano .env  # or: code .env

# 7. Verify no secrets in git
git status | grep ".env"
# Should NOT appear (means it's ignored)
```

**Get your Supabase credentials:**
1. Go to https://supabase.com/dashboard
2. Select your project: `ekumen-agri`
3. Go to **Settings** → **Database** → Copy connection string
4. Go to **Settings** → **API** → Copy `service_role` key (NOT anon key!)

---

### Step 3: Run Database Migration (5 minutes)

```bash
# 1. Navigate to migration scripts
cd scripts/migration

# 2. Load environment
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.ghsfhuekuebwnrjhlitr.supabase.co:5432/postgres"

# 3. Run migration
psql $DATABASE_URL -f 02_add_organizations_and_knowledge_base.sql

# 4. Load test data
psql $DATABASE_URL -f 03_seed_test_data.sql

# 5. Verify it worked
psql $DATABASE_URL -c "\dt" | grep organizations
# Should show: organizations, organization_memberships, organization_farm_access

psql $DATABASE_URL -c "SELECT email FROM users WHERE email LIKE '%@test.com';"
# Should return: farmer@test.com, advisor@test.com, coop@test.com
```

**If migration fails:**
- Check DATABASE_URL is correct
- Check you have permissions
- See troubleshooting section below

---

## 🚀 Start Coding (Day 1)

### Your First Task: Create OrganizationService

**File to create:** `app/services/organization_service.py`

**What to implement:**

```python
# app/services/organization_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.organization import Organization, OrganizationMembership
from typing import List, Optional
from uuid import UUID

class OrganizationService:
    """Service for managing organizations and memberships"""
    
    async def get_user_organizations(
        self, 
        db: AsyncSession, 
        user_id: UUID
    ) -> List[Organization]:
        """Get all organizations a user belongs to"""
        # TODO: Implement
        pass
    
    async def create_organization(
        self,
        db: AsyncSession,
        user_id: UUID,
        name: str,
        organization_type: str,
        siret: Optional[str] = None
    ) -> Organization:
        """Create a new organization and add creator as owner"""
        # TODO: Implement
        pass
    
    async def add_member(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        role: str
    ) -> OrganizationMembership:
        """Add a member to an organization"""
        # TODO: Implement
        pass
    
    async def check_user_permission(
        self,
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        permission: str
    ) -> bool:
        """Check if user has permission in organization"""
        # TODO: Implement
        # Permissions: read, write, admin
        # Roles: owner, admin, member, viewer
        pass
```

**Reference:**
- See `BACKEND_IMPLEMENTATION_PLAN.md` lines 279-320 for complete implementation
- See `ORGANIZATION_MODEL.md` for role/permission mapping

---

### Your Second Task: Write Unit Tests

**File to create:** `tests/unit/services/test_organization_service.py`

```python
import pytest
from app.services.organization_service import OrganizationService
from uuid import uuid4

@pytest.mark.asyncio
async def test_user_can_access_own_organization(db_session):
    """Test that user can access organization they belong to"""
    service = OrganizationService()
    
    # Use test user from seed data
    user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # farmer@test.com
    org_id = "11111111-1111-1111-1111-111111111111"   # Ferme Test Dupont
    
    has_access = await service.check_user_permission(
        db_session,
        user_id=user_id,
        org_id=org_id,
        permission="read"
    )
    
    assert has_access == True

@pytest.mark.asyncio
async def test_user_cannot_access_other_organization(db_session):
    """Test that user cannot access organization they don't belong to"""
    service = OrganizationService()
    
    user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # farmer@test.com
    org_id = "44444444-4444-4444-4444-444444444444"   # PhytoTest Company (not a member)
    
    has_access = await service.check_user_permission(
        db_session,
        user_id=user_id,
        org_id=org_id,
        permission="read"
    )
    
    assert has_access == False
```

**Run tests:**
```bash
pytest tests/unit/services/test_organization_service.py -v
```

---

## 📋 Daily Workflow

### Every Morning:
1. Open `IMPLEMENTATION_TRACKER.md`
2. Check "Current Sprint" section
3. Pick next unchecked task
4. Update status to 🟡 In Progress

### While Coding:
1. Reference `BACKEND_IMPLEMENTATION_PLAN.md` for implementation details
2. Follow error handling patterns (lines 1016-1242)
3. Write tests as you go (aim for > 80% coverage)

### Every Evening:
1. Update `IMPLEMENTATION_TRACKER.md`
2. Mark completed tasks as ✅
3. Add any blockers or notes
4. Commit your work

### Every Week:
1. Review completed tasks
2. Update progress percentages
3. Document lessons learned
4. Plan next week's tasks

---

## 🧪 Testing Strategy

**Test as you build:**

```bash
# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Test users (from seed data):**
- `farmer@test.com` / `Test1234!` - Farm owner
- `advisor@test.com` / `Test1234!` - Advisor
- `coop@test.com` / `Test1234!` - Cooperative member

---

## 🚨 Troubleshooting

### Migration fails with "relation already exists"
```bash
# Rollback and try again
psql $DATABASE_URL -f 02_rollback_organizations_and_knowledge_base.sql
psql $DATABASE_URL -f 02_add_organizations_and_knowledge_base.sql
```

### Password verification fails
```python
# Test bcrypt compatibility
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MHS.K2"
result = pwd_context.verify("Test1234!", hash)
print(f"Verification: {result}")  # Should be True
```

### Chroma filter not working
```bash
# Check version
pip show chromadb | grep Version
# Must be >= 0.4.0

# Upgrade if needed
pip install --upgrade chromadb>=0.4.0
```

### Can't connect to database
```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"

# If fails, check:
# 1. DATABASE_URL is correct
# 2. Password is correct
# 3. Supabase project is running
```

---

## 📚 Quick Reference

### Key Files to Know

**Models:**
- `app/models/organization.py` - Organization, OrganizationMembership
- `app/models/user.py` - User model
- `app/models/conversation.py` - Conversation, Message

**Services:**
- `app/services/organization_service.py` - (YOU'LL CREATE THIS)
- `app/services/auth_service.py` - Existing auth
- `app/services/chat_service.py` - Existing chat

**API Routes:**
- `app/api/v1/organizations.py` - (YOU'LL CREATE THIS)
- `app/api/v1/auth.py` - Existing auth endpoints
- `app/api/v1/chat.py` - Existing chat endpoints

### Important Patterns

**Error Handling:**
```python
from app.core.exceptions import ForbiddenException

if not has_permission:
    raise ForbiddenException(
        code="INSUFFICIENT_PERMISSIONS",
        message="You don't have permission to access this organization",
        details={"required_role": "admin", "your_role": "viewer"}
    )
```

**JWT Middleware:**
```python
from app.core.security import get_current_user, get_org_context

@router.get("/api/v1/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    org_context: OrganizationContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db)
):
    # org_context.organization_id is from JWT
    # Filter by organization_id
    pass
```

---

## ✅ Success Checklist

**You're ready to code when:**
- [x] You've read KEY_DECISIONS.md
- [x] You've skimmed BACKEND_IMPLEMENTATION_PLAN.md
- [x] .env file is created and .gitignored
- [x] Chroma >= 0.4.0 installed
- [x] bcrypt installed
- [x] Migration ran successfully
- [x] Test users exist in database
- [x] You know where to find implementation details
- [x] You have IMPLEMENTATION_TRACKER.md open

**Now start with:**
1. Create `app/services/organization_service.py`
2. Implement `get_user_organizations()` method
3. Write unit test
4. Run test
5. Iterate until it passes
6. Update IMPLEMENTATION_TRACKER.md
7. Commit

---

## 🎯 Your Goal for Week 1

**By end of Week 1, you should have:**
- ✅ OrganizationService fully implemented
- ✅ Unit tests passing (> 80% coverage)
- ✅ JWT middleware updated
- ✅ Organization API endpoints created
- ✅ Integration test for auth flow

**That's it! Start with OrganizationService and build from there.** 🚀

---

**Questions?**
- Check `BACKEND_IMPLEMENTATION_PLAN.md` for implementation details
- Check `CONVERSATION_ARCHITECTURE.md` for chat/RAG details
- Check `ORGANIZATION_MODEL.md` for permission logic
- Update `IMPLEMENTATION_TRACKER.md` with blockers

**Good luck! You've got this!** 💪

