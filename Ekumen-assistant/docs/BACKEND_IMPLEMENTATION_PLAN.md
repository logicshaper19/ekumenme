# Ekumen Backend Implementation Plan

## Current Status: ✅ What We Have

### Database (Supabase)
- ✅ **Users** table (authentication, roles, profiles)
- ✅ **Conversations** table (chat sessions)
- ✅ **Messages** table (chat history)
- ✅ **Exploitations** (farms with SIRET)
- ✅ **Parcelles** (fields/parcels)
- ✅ **Interventions** (field operations)
- ✅ **EPHY Products** (15,006 regulatory products)
- ✅ **EPHY Substances** (1,440 active substances)
- ✅ **EPHY Usages** (233 approved uses)
- ✅ **Crops, Diseases, Pests** (reference tables - empty)

### Services
- ✅ **AuthService** (JWT authentication)
  - **IMPORTANT:** Must use bcrypt for password hashing (compatible with seed data)
  - Install: `pip install passlib[bcrypt]`
  - Usage: `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`
- ✅ **ChatService** (conversation management)
- ✅ **JournalService** (voice journal - partial)
- ✅ **VoiceService** (Whisper/ElevenLabs - stubs)
- ✅ **ProductService** (EPHY product search)
- ✅ **Weather integration** (weatherapi.com)

### APIs
- ✅ `/api/v1/auth` (register, login, refresh)
- ✅ `/api/v1/chat` (conversations, messages)
- ✅ `/api/v1/journal` (voice entries - partial)
- ✅ `/api/v1/products` (EPHY search)

---

## 🔐 Authentication Strategy (CRITICAL DECISION)

### Custom JWT + Supabase Service Role Key (CHOSEN)

**Why NOT Supabase Auth:**
- Need custom organization context in JWT payload
- Multi-tenancy requires `organization_id` in every request
- Supabase Auth doesn't support custom claims without workarounds

**Implementation:**
```python
# Use custom JWT (see CONVERSATION_ARCHITECTURE.md section 9)
{
    "user_id": "uuid",
    "organization_id": "uuid",  # Custom claim
    "organization_role": "owner",
    "exp": timestamp
}

# Use Supabase Storage with SERVICE ROLE KEY (bypasses RLS)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)  # Not anon key!
```

**RLS Policies:** REMOVE from migration - we handle ALL permissions in backend code

**Storage Access:** Backend uses service role key → uploads/downloads on behalf of users → checks permissions in Python

---

## 📅 REALISTIC Implementation Timeline (12 Weeks)

**Original estimate: 8 weeks**
**Realistic estimate: 12 weeks** (50% buffer for unknowns)

---

## ⚠️ Pre-Implementation Requirements

**Before starting Phase 1, verify these dependencies:**

### Python Packages

```bash
# Check versions
pip show chromadb | grep Version    # Must be >= 0.4.0
pip show bcrypt | grep Version      # Required for password hashing
pip show passlib | grep Version     # Required for password context

# Install/upgrade if needed
pip install --upgrade chromadb>=0.4.0
pip install passlib[bcrypt]
```

**Why these versions matter:**
- **chromadb >= 0.4.0**: Uses `where` parameter (not `filter`) for metadata filtering
- **bcrypt**: Seed data uses bcrypt hashes - must match AuthService
- **passlib**: Provides `CryptContext` for password hashing

### Environment Variables

```bash
# Verify .env file exists and contains:
cat .env | grep -E "DATABASE_URL|SUPABASE_SERVICE_ROLE_KEY|SECRET_KEY"

# Required variables:
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...  # NOT anon key!
SECRET_KEY=...                  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Security Checklist

```bash
# Verify .gitignore includes .env
cat .gitignore | grep "^\.env$"
# If not found: echo ".env" >> .gitignore

# Verify no secrets in git history
git log --all --full-history --source -- .env
# Should return nothing (file never committed)
```

---

## 🎯 Phase 1: Organizations & Auth (Week 1-3)

### 1.1 Database Schema Updates

#### Add Missing Fields to Conversations
```sql
ALTER TABLE conversations
ADD COLUMN organization_id UUID REFERENCES organizations(id),
ADD COLUMN title VARCHAR(500),
ADD COLUMN last_message_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX idx_conversations_organization ON conversations(organization_id);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at);
```

#### Create Organizations Table
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    siret VARCHAR(14) UNIQUE,
    organization_type VARCHAR(50) NOT NULL, -- 'farm', 'cooperative', 'advisor', 'input_company'
    status VARCHAR(20) DEFAULT 'active',
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    address TEXT,
    region_code VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_organizations_siret ON organizations(siret);
CREATE INDEX idx_organizations_type ON organizations(organization_type);
```

#### Create Organization Memberships
```sql
CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'owner', 'admin', 'member', 'viewer'
    status VARCHAR(20) DEFAULT 'active',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

CREATE INDEX idx_memberships_org ON organization_memberships(organization_id);
CREATE INDEX idx_memberships_user ON organization_memberships(user_id);
```

#### Create Organization Farm Access
```sql
CREATE TABLE organization_farm_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    farm_siret VARCHAR(14) REFERENCES exploitations(siret) ON DELETE CASCADE,
    access_type VARCHAR(50) NOT NULL, -- 'owner', 'advisor', 'viewer'
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, farm_siret)
);

CREATE INDEX idx_farm_access_org ON organization_farm_access(organization_id);
CREATE INDEX idx_farm_access_farm ON organization_farm_access(farm_siret);
```

#### Create Response Feedback Table
```sql
CREATE TABLE response_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    feedback_type VARCHAR(20) NOT NULL, -- 'thumbs_up', 'thumbs_down'
    feedback_category VARCHAR(50), -- 'incorrect', 'incomplete', 'irrelevant', 'unclear', 'slow', 'other'
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_message ON response_feedback(message_id);
CREATE INDEX idx_feedback_type ON response_feedback(feedback_type);
```

#### Create Knowledge Base Documents Table
```sql
CREATE TABLE knowledge_base_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES users(id),

    -- Document info
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(500) NOT NULL,  -- Supabase Storage path
    file_type VARCHAR(50),  -- 'pdf', 'docx', 'txt', 'api'
    file_size_bytes INTEGER,

    -- Processing
    processing_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    chunk_count INTEGER,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-ada-002',

    -- Metadata
    document_type VARCHAR(50),  -- 'invoice', 'product_spec', 'regulation', 'manual', 'technical_sheet', 'other'
    tags JSONB,
    description TEXT,

    -- SHARING PERMISSIONS
    visibility VARCHAR(50) DEFAULT 'internal',  -- 'internal', 'shared', 'public'
    shared_with_organizations UUID[],  -- Array of org IDs that can access
    shared_with_users UUID[],  -- Array of user IDs that can access
    is_ekumen_provided BOOLEAN DEFAULT FALSE,  -- Ekumen-curated content

    -- Analytics
    query_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_kb_docs_org ON knowledge_base_documents(organization_id);
CREATE INDEX idx_kb_docs_status ON knowledge_base_documents(processing_status);
CREATE INDEX idx_kb_docs_visibility ON knowledge_base_documents(visibility);
CREATE INDEX idx_kb_docs_ekumen ON knowledge_base_documents(is_ekumen_provided);
```

### 1.2 API Endpoints to Implement

#### Authentication with Organization Selection
```python
POST   /api/v1/auth/login                 # Login (returns orgs if multiple)
POST   /api/v1/auth/select-organization   # Select org (if user has multiple)
POST   /api/v1/auth/register              # Register new user
POST   /api/v1/auth/refresh               # Refresh token
```

#### Organization Management
```python
POST   /api/v1/organizations              # Create organization
GET    /api/v1/organizations              # List user's organizations
GET    /api/v1/organizations/:id          # Get organization details
PATCH  /api/v1/organizations/:id          # Update organization
DELETE /api/v1/organizations/:id          # Delete organization

POST   /api/v1/organizations/:id/members  # Add member
DELETE /api/v1/organizations/:id/members/:user_id  # Remove member
PATCH  /api/v1/organizations/:id/members/:user_id  # Update member role

POST   /api/v1/organizations/:id/farms    # Grant farm access
DELETE /api/v1/organizations/:id/farms/:siret  # Revoke farm access
```

#### Enhanced Conversation Management
```python
POST   /api/v1/conversations              # Create new conversation
GET    /api/v1/conversations              # List conversations (filtered by org from JWT)
GET    /api/v1/conversations/:id          # Get conversation with messages
PATCH  /api/v1/conversations/:id          # Update conversation (title, status)
DELETE /api/v1/conversations/:id          # Delete conversation
GET    /api/v1/conversations/search       # Search conversations

POST   /api/v1/conversations/:id/messages # Send message
POST   /api/v1/messages/:id/feedback      # Thumbs up/down
```

#### Knowledge Base Management
```python
POST   /api/v1/knowledge-base/upload      # Upload document (PDF, DOCX, TXT)
GET    /api/v1/knowledge-base              # List accessible documents
GET    /api/v1/knowledge-base/:id          # Get document details
PATCH  /api/v1/knowledge-base/:id/share   # Update sharing settings
DELETE /api/v1/knowledge-base/:id          # Delete document

# Analytics (Admin/Org Owner)
GET    /api/v1/knowledge-base/analytics/usage     # Document usage stats
GET    /api/v1/knowledge-base/analytics/gaps      # Knowledge gaps
GET    /api/v1/knowledge-base/analytics/coverage  # Query coverage
```

### 1.3 Service Layer Architecture (CRITICAL)

**Key Principle:** Assistants/Agents are **consumers** of models, NOT creators.

```
Models (SQLAlchemy)          Services (Business Logic)       Assistants (LangChain Agents)
├── Exploitation             ├── OrganizationService         ├── AgriculturalAssistant
├── Parcelle                 ├── KnowledgeBaseService        │   └── Uses services via tools
├── Intervention             ├── VoiceJournalService         ├── CropHealthAssistant
├── Organization             ├── WeatherService              └── PlanningAssistant
├── User                     └── ProductValidationService
└── Message

Location: app/models/       Location: app/services/          Location: app/agents/
```

**NO separate models for assistants!** They use the same shared models.

**Service Interaction Pattern:**
```
User Request → API Endpoint → Service Layer → Database
                    ↓
                Dependencies injected via FastAPI Depends()
```

---

#### OrganizationService (NEW)
```python
class OrganizationService:
    async def create_organization(db, user_id, org_data)
    async def get_user_organizations(db, user_id)
    async def add_member(db, org_id, user_id, role)
    async def grant_farm_access(db, org_id, farm_siret, access_type)
    async def check_user_access(db, user_id, org_id, required_role)
```

#### Enhanced ChatService (UPDATE EXISTING)
```python
class ChatService:
    async def create_conversation(db, user_id, org_id, farm_siret, title)
    async def list_conversations(db, user_id, org_id, limit, offset)
    async def search_conversations(db, user_id, org_id, query)
    async def auto_generate_title(db, conversation_id)  # From first messages
    async def add_feedback(db, user_id, message_id, feedback_type, comment)
```

#### KnowledgeBaseService (NEW - Uses Existing LangChain)
```python
class KnowledgeBaseService:
    """Uses existing LangChain infrastructure - NO NEW TOOLS"""

    async def upload_document(db, org_id, user_id, file, doc_type, visibility):
        """Upload PDF and process with LangChain loaders"""
        # 1. Upload to Supabase Storage
        # 2. Save to knowledge_base_documents table
        # 3. Process with PyPDFLoader (LangChain)
        # 4. Split with RecursiveCharacterTextSplitter (LangChain)
        # 5. Add to Chroma vector store (existing!)

    async def get_accessible_documents(db, user_id, org_id):
        """Get documents user can access (internal + shared + public)"""
        # SQL query with permission filtering

    async def update_sharing(db, doc_id, visibility, shared_with_orgs, shared_with_users):
        """Update document sharing settings"""

    async def track_usage(db, doc_id):
        """Increment query_count when document is retrieved"""
```

#### Enhanced LCELChatService (UPDATE EXISTING)
```python
class LCELChatService:
    """Already exists - just add permission filtering"""

    async def create_org_rag_chain_with_permissions(db, user_id, org_id):
        """Create RAG chain with permission-filtered retrieval"""
        # Get accessible documents
        accessible_docs = await kb_service.get_accessible_documents(db, user_id, org_id)

        # Use existing vectorstore with filter
        retriever = self.vectorstore.as_retriever(
            search_kwargs={
                "k": 5,
                "filter": {"doc_id": {"$in": accessible_docs}}  # Permission filter!
            }
        )

        # Rest is SAME as existing RAG chain
        # Uses existing RunnableWithMessageHistory
```

---

## 📊 Interventions Table Schema (CRITICAL REFERENCE)

### Complete Schema with Constraints

```sql
CREATE TABLE interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcelle_id UUID NOT NULL REFERENCES parcelles(id) ON DELETE CASCADE,
    siret VARCHAR(14) NOT NULL REFERENCES exploitations(siret) ON DELETE CASCADE,

    -- Intervention details
    type_intervention VARCHAR(100) NOT NULL
        CHECK (type_intervention IN (
            'semis', 'traitement', 'fertilisation', 'recolte',
            'irrigation', 'travail_sol', 'observation', 'autre'
        )),
    date_intervention TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT,

    -- Products/inputs used (JSONB array)
    intrants JSONB DEFAULT '[]'::jsonb,

    -- Equipment and conditions
    materiel_utilise VARCHAR(255),
    conditions_meteo VARCHAR(100),

    -- Additional data (JSONB object)
    extra_data JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_date CHECK (date_intervention <= NOW() + INTERVAL '7 days'),
    CONSTRAINT valid_intrants CHECK (jsonb_typeof(intrants) = 'array'),
    CONSTRAINT valid_extra_data CHECK (jsonb_typeof(extra_data) = 'object')
);

-- Performance indexes
CREATE INDEX idx_interventions_date ON interventions(date_intervention DESC);
CREATE INDEX idx_interventions_parcel_date ON interventions(parcelle_id, date_intervention DESC);
CREATE INDEX idx_interventions_siret ON interventions(siret);
CREATE INDEX idx_interventions_type ON interventions(type_intervention);

-- Full-text search on description
CREATE INDEX idx_interventions_description_fts ON interventions USING gin(to_tsvector('french', description));

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_interventions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_interventions_updated_at
    BEFORE UPDATE ON interventions
    FOR EACH ROW
    EXECUTE FUNCTION update_interventions_updated_at();
```

### intrants JSONB Structure

```json
[
  {
    "code_amm": "2070024",
    "nom_produit": "OPUS",
    "substance_active": "Epoxiconazole",
    "dose": 1.5,
    "unite": "L/ha",
    "surface_traitee_ha": 228.54
  }
]
```

### extra_data JSONB Structure (For Voice Journal)

```json
{
  "weather_conditions": "ensoleillé",
  "temperature_celsius": 18.5,
  "humidity_percent": 65.0,
  "wind_speed_kmh": 12.0,
  "source": "voice_journal",
  "journal_entry_id": "uuid",
  "validation_status": "validated",
  "compliance_issues": [],
  "safety_alerts": []
}
```

---

## 🎯 Phase 2: Conversations & Feedback (Week 4-6)

### 2.1 Create Voice Journal Table in Supabase
```sql
CREATE TABLE voice_journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id),
    farm_siret VARCHAR(14) REFERENCES exploitations(siret),
    parcel_id UUID REFERENCES parcelles(id),
    
    -- Voice data
    audio_file_path VARCHAR(500),
    audio_duration_seconds NUMERIC(8, 2),
    transcription_confidence NUMERIC(3, 2),
    
    -- Entry content
    content TEXT NOT NULL,
    intervention_type VARCHAR(50) NOT NULL,
    
    -- Intervention details
    products_used JSONB,
    equipment_used JSONB,
    weather_conditions VARCHAR(50),
    temperature_celsius NUMERIC(4, 1),
    humidity_percent NUMERIC(5, 2),
    wind_speed_kmh NUMERIC(5, 2),
    
    -- Validation
    validation_status VARCHAR(50) DEFAULT 'pending',
    validation_notes TEXT,
    compliance_issues JSONB,
    safety_alerts JSONB,
    
    -- Metadata
    notes TEXT,
    intervention_metadata JSONB,
    intervention_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_journal_user ON voice_journal_entries(user_id);
CREATE INDEX idx_journal_farm ON voice_journal_entries(farm_siret);
CREATE INDEX idx_journal_parcel ON voice_journal_entries(parcel_id);
CREATE INDEX idx_journal_date ON voice_journal_entries(intervention_date);
```

### 2.2 Integrate Whisper & ElevenLabs

#### Update VoiceService
```python
class VoiceService:
    async def transcribe_audio(audio_file) -> VoiceTranscriptionResult:
        # Use OpenAI Whisper API
        # Return: text, confidence, language, duration
        
    async def synthesize_speech(text, voice_id) -> bytes:
        # Use ElevenLabs API
        # Return: audio bytes (MP3)
        
    async def upload_audio_to_storage(audio_file, path) -> str:
        # Upload to Supabase Storage
        # Return: file URL
```

### 2.3 Voice Journal Workflow

```
1. User records voice note in field
2. Frontend uploads audio to Supabase Storage
3. Backend transcribes with Whisper
4. Extract structured data (products, quantities, etc.)
5. Validate against EPHY database
6. Check weather conditions
7. Generate compliance warnings
8. Store journal entry
9. AUTO-CREATE INTERVENTION in interventions table (with ALL required fields)
10. Send confirmation via ElevenLabs TTS
```

### 2.4 Voice Journal → Intervention Mapping

**CRITICAL:** Voice journal must capture ALL fields required for interventions table.

```python
# In journal_service.py
async def create_intervention_from_journal(
    db: AsyncSession,
    journal_entry: VoiceJournalEntry
) -> Intervention:
    """Auto-create intervention from validated journal entry"""

    # Prepare intrants JSONB (validated against EPHY)
    intrants = []
    if journal_entry.products_used:
        for product in journal_entry.products_used:
            intrants.append({
                "code_amm": product.get("code_amm"),
                "nom_produit": product.get("nom_produit"),
                "substance_active": product.get("substance_active"),
                "dose": product.get("dose"),
                "unite": product.get("unite", "L/ha"),
                "surface_traitee_ha": product.get("surface_traitee_ha")
            })

    # Prepare extra_data JSONB
    extra_data = {
        "weather_conditions": journal_entry.weather_conditions,
        "temperature_celsius": float(journal_entry.temperature_celsius) if journal_entry.temperature_celsius else None,
        "humidity_percent": float(journal_entry.humidity_percent) if journal_entry.humidity_percent else None,
        "wind_speed_kmh": float(journal_entry.wind_speed_kmh) if journal_entry.wind_speed_kmh else None,
        "source": "voice_journal",
        "journal_entry_id": str(journal_entry.id),
        "validation_status": journal_entry.validation_status,
        "compliance_issues": journal_entry.compliance_issues or [],
        "safety_alerts": journal_entry.safety_alerts or []
    }

    intervention = Intervention(
        # Required fields
        parcelle_id=journal_entry.parcel_id,
        siret=journal_entry.farm_siret,
        type_intervention=journal_entry.intervention_type,
        date_intervention=journal_entry.intervention_date or datetime.now(),

        # From journal content
        description=journal_entry.content,

        # Products used (JSONB array)
        intrants=intrants,

        # Equipment (if captured)
        materiel_utilise=journal_entry.equipment_used.get("name") if journal_entry.equipment_used else None,
        conditions_meteo=journal_entry.weather_conditions,

        # Additional data (JSONB)
        extra_data=extra_data
    )

    db.add(intervention)
    await db.commit()
    await db.refresh(intervention)

    # Link back to journal
    journal_entry.intervention_id = intervention.id
    await db.commit()

    return intervention
```

### 2.5 Product Validation Against EPHY (Fuzzy Matching)

**First: Add Full-Text Search to EPHY (Run Once):**

```sql
-- Add search vector column
ALTER TABLE ephy_products ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Populate search vector
UPDATE ephy_products SET search_vector =
    to_tsvector('french', COALESCE(nom_produit, ''));

-- Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_ephy_products_fts
    ON ephy_products USING gin(search_vector);

-- Add trigram extension for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create trigram index for typo tolerance
CREATE INDEX IF NOT EXISTS idx_ephy_products_trgm
    ON ephy_products USING gin(nom_produit gin_trgm_ops);

-- Trigger to keep search_vector updated
CREATE OR REPLACE FUNCTION update_ephy_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = to_tsvector('french', COALESCE(NEW.nom_produit, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ephy_search_vector
    BEFORE INSERT OR UPDATE ON ephy_products
    FOR EACH ROW
    EXECUTE FUNCTION update_ephy_search_vector();
```

**Then: Implement Smart Product Validation:**

```python
async def validate_products_against_ephy(
    db: AsyncSession,
    products_mentioned: List[str],
    crop: str = None
) -> List[Dict]:
    """
    Validate products with fuzzy matching and full-text search

    Strategy:
    1. Try exact match
    2. Try full-text search (handles stemming)
    3. Try fuzzy match (handles typos)

    Returns: List of validated products with confidence scores
    """
    validated_products = []

    for product_name in products_mentioned:
        # Clean input
        clean_name = product_name.strip()

        # Strategy 1: Exact match (fastest)
        exact_query = text("""
            SELECT
                numero_amm,
                nom_produit,
                (SELECT nom_substance
                 FROM ephy_substances
                 WHERE numero_cas = ANY(ephy_products.substances_actives)
                 LIMIT 1) as substance_active,
                1.0 as score
            FROM ephy_products
            WHERE LOWER(nom_produit) = LOWER(:product_name)
            LIMIT 1
        """)

        result = await db.execute(exact_query, {"product_name": clean_name})
        match = result.fetchone()

        if match:
            validated_products.append({
                "code_amm": match[0],
                "nom_produit": match[1],
                "substance_active": match[2],
                "original_mention": product_name,
                "confidence": "high",
                "match_score": 1.0,
                "match_type": "exact"
            })
            continue

        # Strategy 2: Full-text search (handles variations)
        fts_query = text("""
            SELECT
                numero_amm,
                nom_produit,
                (SELECT nom_substance
                 FROM ephy_substances
                 WHERE numero_cas = ANY(ephy_products.substances_actives)
                 LIMIT 1) as substance_active,
                ts_rank(search_vector, query) as score
            FROM ephy_products,
                 to_tsquery('french', :search_term) query
            WHERE search_vector @@ query
            ORDER BY score DESC
            LIMIT 5
        """)

        # Convert to tsquery format (handle spaces)
        search_term = ' & '.join(clean_name.split())
        result = await db.execute(fts_query, {"search_term": search_term})
        matches = result.fetchall()

        if matches and matches[0][3] > 0.1:  # Minimum relevance threshold
            validated_products.append({
                "code_amm": matches[0][0],
                "nom_produit": matches[0][1],
                "substance_active": matches[0][2],
                "original_mention": product_name,
                "confidence": "high" if matches[0][3] > 0.5 else "medium",
                "match_score": float(matches[0][3]),
                "match_type": "full_text",
                "alternatives": [
                    {"name": m[1], "score": float(m[3])}
                    for m in matches[1:3]
                ] if len(matches) > 1 else []
            })
            continue

        # Strategy 3: Fuzzy match (handles typos)
        fuzzy_query = text("""
            SELECT
                numero_amm,
                nom_produit,
                (SELECT nom_substance
                 FROM ephy_substances
                 WHERE numero_cas = ANY(ephy_products.substances_actives)
                 LIMIT 1) as substance_active,
                similarity(nom_produit, :product_name) as score
            FROM ephy_products
            WHERE similarity(nom_produit, :product_name) > 0.3
            ORDER BY score DESC
            LIMIT 5
        """)

        result = await db.execute(fuzzy_query, {"product_name": clean_name})
        matches = result.fetchall()

        if matches:
            validated_products.append({
                "code_amm": matches[0][0],
                "nom_produit": matches[0][1],
                "substance_active": matches[0][2],
                "original_mention": product_name,
                "confidence": "high" if matches[0][3] > 0.7 else "medium" if matches[0][3] > 0.5 else "low",
                "match_score": float(matches[0][3]),
                "match_type": "fuzzy",
                "alternatives": [
                    {"name": m[1], "score": float(m[3])}
                    for m in matches[1:3]
                ] if len(matches) > 1 else []
            })
        else:
            # No match found
            validated_products.append({
                "code_amm": None,
                "nom_produit": product_name,
                "substance_active": None,
                "original_mention": product_name,
                "confidence": "none",
                "match_score": 0.0,
                "match_type": "no_match",
                "warning": "Product not found in EPHY database. Please verify spelling."
            })

    return validated_products
```

**Usage Example:**

```python
# In voice journal processing
products = await validate_products_against_ephy(
    db,
    products_mentioned=["Rondup", "OPUS", "Karate Zon"],  # With typos
    crop="wheat"
)

# Results:
# [
#   {"nom_produit": "ROUNDUP", "confidence": "high", "match_type": "fuzzy", "match_score": 0.85},
#   {"nom_produit": "OPUS", "confidence": "high", "match_type": "exact", "match_score": 1.0},
#   {"nom_produit": "KARATE ZEON", "confidence": "medium", "match_type": "fuzzy", "match_score": 0.72}
# ]
```

**All required fields captured!** ✅

---

## 📤 File Upload Flow (CRITICAL)

### Direct Upload to Supabase Storage

**Flow:** Frontend → Signed URL → Direct Upload → Backend Validation → Processing

```python
# Step 1: Request upload URL
@router.post("/api/v1/knowledge-base/request-upload")
async def request_upload_url(request: UploadRequest, org_context: OrganizationContext = Depends(get_org_context)):
    # Validate file size (max 50MB) and type (PDF/DOCX only)
    doc_id = uuid.uuid4()
    storage_path = f"knowledge-base/{org_context.organization_id}/{doc_id}.pdf"

    # Create DB record (status='pending_upload')
    # Generate signed URL (24h expiry)
    signed_url = supabase.storage.from_("documents").create_signed_upload_url(storage_path, expires_in=86400)

    return {"document_id": doc_id, "upload_url": signed_url}

# Step 2: Frontend uploads directly to Supabase (not through backend)

# Step 3: Notify backend of completion
@router.post("/api/v1/knowledge-base/{document_id}/upload-complete")
async def upload_complete(document_id: str, background_tasks: BackgroundTasks):
    # Verify file exists in storage
    # Update status to 'processing'
    # Trigger background processing
    background_tasks.add_task(process_pdf_document, document_id)
```

See CONVERSATION_ARCHITECTURE.md section 6 for complete implementation.

---

## ☁️ Weather Cache Expiration (CRITICAL)

```python
async def get_weather_with_cache(location: str, date: str, data_type: str, db: AsyncSession):
    # Check cache (not expired)
    # If miss, fetch from API

    # Set expiration based on type:
    if data_type == 'historical':
        expires_at = None  # Never expires
    elif data_type == 'current':
        expires_at = datetime.now() + timedelta(hours=1)
    elif data_type == 'forecast':
        expires_at = datetime.now() + timedelta(hours=6)

    # Store with expiration
    cache_entry = WeatherCache(cache_key=key, data=data, expires_at=expires_at)

# Cleanup (run daily at 3 AM)
async def cleanup_expired_weather_cache(db: AsyncSession):
    await db.execute(delete(WeatherCache).where(WeatherCache.expires_at < datetime.now()))
```

---

## 🎯 Phase 3: Voice Journal Integration (Week 7-8)

### 3.1 Analytics Tables

#### Conversation Analytics
```sql
CREATE TABLE conversation_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    total_messages INTEGER,
    total_tokens INTEGER,
    total_cost_usd NUMERIC(10, 6),
    tools_used JSONB,
    avg_response_time_ms INTEGER,
    user_satisfaction NUMERIC(3, 2), -- Average of thumbs up/down
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Usage Tracking
```sql
CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(50), -- 'message_sent', 'voice_entry', 'product_search'
    event_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_usage_org ON usage_tracking(organization_id);
CREATE INDEX idx_usage_date ON usage_tracking(created_at);
```

### 3.2 Admin Dashboard APIs

```python
GET /api/v1/admin/analytics/conversations  # Conversation stats
GET /api/v1/admin/analytics/users          # User activity
GET /api/v1/admin/analytics/products       # Product mentions
GET /api/v1/admin/analytics/feedback       # User feedback summary
GET /api/v1/admin/organizations            # All organizations
GET /api/v1/admin/users                    # All users
```

---

## 🎯 Phase 4: File Storage & Weather (Week 7)

### 4.1 Supabase Storage Buckets

```sql
-- Create storage buckets
INSERT INTO storage.buckets (id, name, public) VALUES
  ('voice-journal', 'voice-journal', false),
  ('field-photos', 'field-photos', false),
  ('reports', 'reports', false);

-- Set up RLS policies
CREATE POLICY "Users can upload their own voice notes"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'voice-journal' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can read their own voice notes"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'voice-journal' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
```

### 4.2 Weather Data Caching

```sql
CREATE TABLE weather_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_lat NUMERIC(10, 6),
    location_lon NUMERIC(10, 6),
    commune_insee VARCHAR(5),
    date DATE,
    temperature_celsius NUMERIC(4, 1),
    humidity_percent NUMERIC(5, 2),
    wind_speed_kmh NUMERIC(5, 2),
    precipitation_mm NUMERIC(6, 2),
    weather_condition VARCHAR(50),
    forecast_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(location_lat, location_lon, date)
);

CREATE INDEX idx_weather_location_date ON weather_cache(location_lat, location_lon, date);
CREATE INDEX idx_weather_commune_date ON weather_cache(commune_insee, date);
```

---

## 📋 Implementation Checklist

### Week 1-2: Core Chat + Organizations
- [ ] Create organizations table
- [ ] Create organization_memberships table
- [ ] Create organization_farm_access table
- [ ] Create response_feedback table
- [ ] Create knowledge_base_documents table
- [ ] Add organization_id to conversations
- [ ] Add title to conversations
- [ ] Update auth endpoints (login with org selection)
- [ ] Implement OrganizationService
- [ ] Implement organization APIs
- [ ] Update ChatService for org context (from JWT)
- [ ] Implement conversation search
- [ ] Implement auto-title generation
- [ ] Implement feedback APIs

### Week 3-4: Knowledge Base (Using Existing LangChain)
- [ ] Implement KnowledgeBaseService
- [ ] Add PDF upload endpoint
- [ ] Integrate PyPDFLoader (LangChain - already available)
- [ ] Process documents into Chroma (existing vectorstore)
- [ ] Add permission filtering to retriever
- [ ] Update LCELChatService with permission-filtered RAG
- [ ] Implement sharing endpoints
- [ ] Test internal/shared/public documents
- [ ] Track document usage in message_metadata
- [ ] Test end-to-end: upload PDF → ask question → get answer

### Week 5-6: Voice Journal
- [ ] Create voice_journal_entries table
- [ ] Add intervention_id link field
- [ ] Set up Supabase Storage buckets
- [ ] Integrate Whisper API (replace stub)
- [ ] Integrate ElevenLabs API (replace stub)
- [ ] Implement audio upload/download
- [ ] Implement transcription service
- [ ] Implement TTS service
- [ ] Implement journal validation
- [ ] **Implement auto-create intervention with ALL required fields**
- [ ] Test end-to-end voice workflow

### Week 7: Analytics & Admin
- [ ] Implement knowledge base analytics queries
- [ ] Build admin dashboard APIs
- [ ] Track most used documents
- [ ] Identify knowledge gaps
- [ ] Calculate query coverage
- [ ] Monitor user satisfaction (thumbs up/down)
- [ ] Create phyto company analytics (shared doc usage)

### Week 8: Storage & Polish
- [ ] Configure Supabase Storage RLS policies
- [ ] Create weather cache table
- [ ] Implement weather caching
- [ ] Test file uploads (PDFs, audio, photos)
- [ ] Performance testing
- [ ] Security audit

---

## 🚨 Error Handling Strategy (CRITICAL)

### Standard Error Response Format

**All errors MUST use this format:**

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "details": {}
    }
}
```

### HTTP Status Codes (MANDATORY)

```python
# Success
200 OK                  # Successful GET, PATCH, DELETE
201 Created             # Successful POST (organization, conversation created)
204 No Content          # Successful DELETE with no response body

# Client Errors
400 Bad Request         # Malformed request, invalid JSON
401 Unauthorized        # Missing, invalid, or expired token
403 Forbidden           # Valid token but insufficient permissions
404 Not Found           # Resource doesn't exist
409 Conflict            # Resource already exists (duplicate SIRET, email)
422 Unprocessable Entity # Business logic error (can't delete org with active members)
429 Too Many Requests   # Rate limit exceeded

# Server Errors
500 Internal Server Error # Unexpected error (log and alert)
503 Service Unavailable   # External API down (Whisper, Weather API)
```

### Error Code Examples

```python
# Authentication Errors (401)
{
    "error": {
        "code": "TOKEN_EXPIRED",
        "message": "Your session has expired. Please log in again.",
        "details": {"expired_at": "2024-03-15T10:30:00Z"}
    }
}

{
    "error": {
        "code": "INVALID_TOKEN",
        "message": "Could not validate credentials",
        "details": {}
    }
}

# Permission Errors (403)
{
    "error": {
        "code": "INSUFFICIENT_PERMISSIONS",
        "message": "You don't have permission to access this organization",
        "details": {
            "required_role": "admin",
            "your_role": "viewer"
        }
    }
}

{
    "error": {
        "code": "ORGANIZATION_MISMATCH",
        "message": "This conversation belongs to a different organization",
        "details": {
            "conversation_org": "org-123",
            "your_org": "org-456"
        }
    }
}

# Validation Errors (422)
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request data",
        "details": {
            "fields": {
                "siret": ["Must be exactly 14 digits"],
                "email": ["Invalid email format"],
                "organization_type": ["Must be one of: farm, cooperative, advisor, input_company, research_institute"]
            }
        }
    }
}

# Business Logic Errors (422)
{
    "error": {
        "code": "CANNOT_DELETE_ORG_WITH_MEMBERS",
        "message": "Cannot delete organization with active members",
        "details": {
            "active_members": 5,
            "action_required": "Remove all members before deleting organization"
        }
    }
}

# Product Validation Errors (422)
{
    "error": {
        "code": "PRODUCT_NOT_FOUND",
        "message": "Product 'Rondup' not found in EPHY database",
        "details": {
            "suggested_products": [
                {"name": "ROUNDUP", "similarity": 0.85, "amm": "2070024"},
                {"name": "ROUNDUP FLEX", "similarity": 0.72, "amm": "2070025"}
            ]
        }
    }
}

# Rate Limit Errors (429)
{
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Too many requests. Please try again later.",
        "details": {
            "limit": "10 per hour",
            "retry_after": 3600,
            "reset_at": "2024-03-15T11:00:00Z"
        }
    }
}

# External Service Errors (503)
{
    "error": {
        "code": "WHISPER_API_UNAVAILABLE",
        "message": "Voice transcription service is temporarily unavailable",
        "details": {
            "service": "OpenAI Whisper API",
            "retry_after": 60
        }
    }
}
```

### Implementation

```python
# app/core/exceptions.py
from fastapi import HTTPException, status

class EkumenException(HTTPException):
    """Base exception for all Ekumen errors"""
    def __init__(self, code: str, message: str, details: dict = None):
        super().__init__(
            status_code=self.status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or {}
                }
            }
        )

class UnauthorizedException(EkumenException):
    status_code = status.HTTP_401_UNAUTHORIZED

class ForbiddenException(EkumenException):
    status_code = status.HTTP_403_FORBIDDEN

class NotFoundException(EkumenException):
    status_code = status.HTTP_404_NOT_FOUND

class ConflictException(EkumenException):
    status_code = status.HTTP_409_CONFLICT

class ValidationException(EkumenException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

class RateLimitException(EkumenException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS

class ServiceUnavailableException(EkumenException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

# Usage in endpoints:
@router.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    org_context: OrganizationContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db)
):
    conversation = await db.get(Conversation, conversation_id)

    if not conversation:
        raise NotFoundException(
            code="CONVERSATION_NOT_FOUND",
            message=f"Conversation {conversation_id} not found"
        )

    if conversation.user_id != current_user.id:
        raise ForbiddenException(
            code="ACCESS_DENIED",
            message="You don't have permission to access this conversation"
        )

    if conversation.organization_id != org_context.organization_id:
        raise ForbiddenException(
            code="ORGANIZATION_MISMATCH",
            message="This conversation belongs to a different organization",
            details={
                "conversation_org": str(conversation.organization_id),
                "your_org": str(org_context.organization_id)
            }
        )

    return conversation
```

---

## 🚨 Error Handling Patterns

### Whisper API Failures

```python
async def transcribe_audio_with_retry(audio_file_path: str, max_retries: int = 3):
    """Transcribe audio with retry logic"""
    for attempt in range(max_retries):
        try:
            result = await whisper_client.transcribe(audio_file_path)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                # Final failure - save audio for manual processing
                await mark_journal_entry_failed(
                    audio_file_path,
                    error="Whisper API failed after 3 attempts",
                    status="transcription_failed"
                )
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### PDF Processing Failures

```python
async def process_pdf_with_cleanup(doc_id: str, file_path: str):
    """Process PDF with proper cleanup on failure"""
    try:
        # Load PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # Split into chunks
        chunks = text_splitter.split_documents(documents)

        # Add to vector store
        vectorstore.add_documents(chunks)

        # Update status
        await update_document_status(doc_id, "completed", chunk_count=len(chunks))

    except Exception as e:
        # Mark as failed
        await update_document_status(doc_id, "failed", error=str(e))

        # Clean up partial data
        await vectorstore.delete(filter={"document_id": doc_id})

        # Log error
        logger.error(f"PDF processing failed for {doc_id}: {e}")

        raise
```

### Unauthorized Access to Conversations

```python
@router.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    org_context: OrganizationContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation - with proper access control"""

    conversation = await db.get(Conversation, conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check ownership
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check organization context
    if conversation.organization_id != org_context.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Conversation belongs to different organization"
        )

    return conversation
```

---

## ⚡ Rate Limiting

### Configuration

```python
# app/core/config.py
RATE_LIMITS = {
    "whisper_transcription": "10/hour",  # 10 transcriptions per hour per user
    "pdf_upload": "20/day",  # 20 PDFs per day per organization
    "vector_embedding": "100/hour",  # 100 embedding calls per hour per org
    "weather_api": "1000/day",  # 1000 weather API calls per day (global)
    "chat_messages": "100/hour",  # 100 messages per hour per user
}
```

### Implementation (Using slowapi)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/api/v1/journal/upload")
@limiter.limit("10/hour")
async def upload_voice_journal(
    request: Request,
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    """Upload voice journal - rate limited"""
    # Process upload...
```

### Per-Organization Rate Limiting

```python
def get_org_rate_limit_key(request: Request, org_context: OrganizationContext):
    """Rate limit by organization instead of IP"""
    return f"org:{org_context.organization_id}"

@router.post("/api/v1/knowledge-base/upload")
@limiter.limit("20/day", key_func=get_org_rate_limit_key)
async def upload_document(
    request: Request,
    file: UploadFile,
    org_context: OrganizationContext = Depends(get_org_context)
):
    """Upload document - rate limited per organization"""
    # Process upload...
```

---

## 🚀 Next Steps

### Immediate Actions
1. ✅ **Review updated documentation** - Reflects all decisions from conversation
2. ✅ **Create SQL migration script** - All new tables in one file
3. ✅ **Run migration in Supabase** - Create all tables
4. ✅ **Start with Phase 1** - Organizations & enhanced chat

### Key Decisions Confirmed
- ✅ **No organization selector** - ONE org per session (like ChatGPT Teams)
- ✅ **No new infrastructure** - Use existing LangChain (RunnableWithMessageHistory, Chroma, RAG)
- ✅ **Knowledge base sharing** - Internal/Shared/Public with permission filtering
- ✅ **Voice journal → interventions** - Auto-create with ALL required fields
- ✅ **Analytics focus** - Knowledge base usage, gaps, coverage

**Ready to start implementing?** 🎯

