-- Migration: Add Organizations, Knowledge Base, and Enhanced Chat Features
-- Date: 2024
-- Description: Adds multi-tenancy, knowledge base with sharing, and conversation enhancements
--
-- AUTHENTICATION STRATEGY:
-- - Uses CUSTOM JWT (not Supabase Auth)
-- - Backend uses Supabase SERVICE ROLE KEY
-- - NO RLS policies (backend handles ALL permissions)
-- - organization_id embedded in JWT payload for multi-tenancy

-- ============================================================================
-- 1. ORGANIZATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    siret VARCHAR(14) UNIQUE,
    organization_type VARCHAR(50) NOT NULL, -- 'farm', 'cooperative', 'advisor', 'input_company', 'research_institute', 'government_agency'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'suspended', 'pending_approval'
    
    -- Contact info
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    address TEXT,
    region_code VARCHAR(20),
    
    -- Metadata
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_organizations_siret ON organizations(siret);
CREATE INDEX idx_organizations_type ON organizations(organization_type);
CREATE INDEX idx_organizations_status ON organizations(status);

COMMENT ON TABLE organizations IS 'Multi-tenant organizations (farms, cooperatives, advisors, phyto companies)';
COMMENT ON COLUMN organizations.organization_type IS 'farm, cooperative, advisor, input_company, research_institute, government_agency';

-- ============================================================================
-- 2. ORGANIZATION MEMBERSHIPS
-- ============================================================================

CREATE TABLE IF NOT EXISTS organization_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role in organization
    role VARCHAR(50) NOT NULL, -- 'owner', 'admin', 'advisor', 'member', 'viewer', 'worker', 'sales_rep', 'researcher'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'pending_invitation'
    
    -- Invitation tracking
    invited_by UUID REFERENCES users(id),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, user_id)
);

CREATE INDEX idx_memberships_org ON organization_memberships(organization_id);
CREATE INDEX idx_memberships_user ON organization_memberships(user_id);
CREATE INDEX idx_memberships_role ON organization_memberships(role);

COMMENT ON TABLE organization_memberships IS 'Links users to organizations with roles';
COMMENT ON COLUMN organization_memberships.role IS 'owner, admin, advisor, member, viewer, worker, sales_rep, researcher';

-- ============================================================================
-- 3. ORGANIZATION FARM ACCESS
-- ============================================================================

CREATE TABLE IF NOT EXISTS organization_farm_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    farm_siret VARCHAR(14) REFERENCES exploitations(siret) ON DELETE CASCADE,
    
    -- Access level
    access_type VARCHAR(50) NOT NULL, -- 'owner', 'advisor', 'viewer'
    
    -- Audit
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, farm_siret)
);

CREATE INDEX idx_farm_access_org ON organization_farm_access(organization_id);
CREATE INDEX idx_farm_access_farm ON organization_farm_access(farm_siret);

COMMENT ON TABLE organization_farm_access IS 'Controls which organizations can access which farms';
COMMENT ON COLUMN organization_farm_access.access_type IS 'owner (full control), advisor (view + recommend), viewer (read-only)';

-- ============================================================================
-- 4. UPDATE CONVERSATIONS TABLE
-- ============================================================================

-- Add organization context to conversations
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id),
ADD COLUMN IF NOT EXISTS title VARCHAR(500),
ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active',
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS idx_conversations_organization ON conversations(organization_id);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations(last_message_at);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_user_org_time ON conversations(user_id, organization_id, last_message_at DESC);

COMMENT ON COLUMN conversations.organization_id IS 'Organization context for this conversation (from JWT token)';
COMMENT ON COLUMN conversations.title IS 'Auto-generated from first messages';
COMMENT ON COLUMN conversations.status IS 'active, archived, deleted (soft delete)';
COMMENT ON COLUMN conversations.deleted_at IS 'Timestamp when conversation was soft deleted';

-- ============================================================================
-- 5. RESPONSE FEEDBACK
-- ============================================================================

CREATE TABLE IF NOT EXISTS response_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Feedback
    feedback_type VARCHAR(20) NOT NULL, -- 'thumbs_up', 'thumbs_down'
    feedback_category VARCHAR(50), -- 'incorrect', 'incomplete', 'irrelevant', 'unclear', 'slow', 'other'
    comment TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_message ON response_feedback(message_id);
CREATE INDEX idx_feedback_type ON response_feedback(feedback_type);
CREATE INDEX idx_feedback_user ON response_feedback(user_id);
CREATE INDEX idx_feedback_conversation_type ON response_feedback(conversation_id, feedback_type);

COMMENT ON TABLE response_feedback IS 'User feedback on AI responses (thumbs up/down)';

-- ============================================================================
-- 6. KNOWLEDGE BASE DOCUMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_base_documents (
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
CREATE INDEX idx_kb_docs_type ON knowledge_base_documents(document_type);
CREATE INDEX idx_kb_docs_org_status_visibility ON knowledge_base_documents(organization_id, processing_status, visibility);

COMMENT ON TABLE knowledge_base_documents IS 'PDFs and documents for RAG with permission-based sharing';
COMMENT ON COLUMN knowledge_base_documents.visibility IS 'internal (org only), shared (specific orgs/users), public (all Ekumen users)';
COMMENT ON COLUMN knowledge_base_documents.is_ekumen_provided IS 'True for Ekumen-curated content (regulations, guides)';

-- ============================================================================
-- 7. VOICE JOURNAL ENTRIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS voice_journal_entries (
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
    
    -- Intervention details (for auto-creating intervention)
    products_used JSONB,
    equipment_used JSONB,
    weather_conditions VARCHAR(50),
    temperature_celsius NUMERIC(4, 1),
    humidity_percent NUMERIC(5, 2),
    wind_speed_kmh NUMERIC(5, 2),
    
    -- Validation
    validation_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'validated', 'rejected'
    validation_notes TEXT,
    compliance_issues JSONB,
    safety_alerts JSONB,
    
    -- Link to created intervention
    intervention_id UUID REFERENCES interventions(id),
    
    -- Metadata
    notes TEXT,
    intervention_metadata JSONB,
    intervention_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_journal_user ON voice_journal_entries(user_id);
CREATE INDEX idx_journal_org ON voice_journal_entries(organization_id);
CREATE INDEX idx_journal_farm ON voice_journal_entries(farm_siret);
CREATE INDEX idx_journal_parcel ON voice_journal_entries(parcel_id);
CREATE INDEX idx_journal_date ON voice_journal_entries(intervention_date);
CREATE INDEX idx_journal_intervention ON voice_journal_entries(intervention_id);

COMMENT ON TABLE voice_journal_entries IS 'Voice-recorded field notes with auto-intervention creation';
COMMENT ON COLUMN voice_journal_entries.intervention_id IS 'Link to auto-created intervention in interventions table';

-- ============================================================================
-- 8. WEATHER CACHE (Optional - for performance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS weather_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_lat NUMERIC(10, 6),
    location_lon NUMERIC(10, 6),
    commune_insee VARCHAR(5),
    date DATE,

    -- Weather data
    temperature_celsius NUMERIC(4, 1),
    humidity_percent NUMERIC(5, 2),
    wind_speed_kmh NUMERIC(5, 2),
    precipitation_mm NUMERIC(6, 2),
    weather_condition VARCHAR(50),
    forecast_data JSONB,

    -- Cache management
    data_type VARCHAR(20) DEFAULT 'current',  -- 'historical', 'current', 'forecast'
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(location_lat, location_lon, date, data_type)
);

CREATE INDEX idx_weather_location_date ON weather_cache(location_lat, location_lon, date);
CREATE INDEX idx_weather_commune_date ON weather_cache(commune_insee, date);
CREATE INDEX idx_weather_expires ON weather_cache(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE weather_cache IS 'Cache for weatherapi.com data to reduce API calls';
COMMENT ON COLUMN weather_cache.data_type IS 'historical (never expires), current (1 hour), forecast (6 hours)';
COMMENT ON COLUMN weather_cache.expires_at IS 'When cache entry expires (NULL for historical data)';

-- ============================================================================
-- 9. ADD MISSING INDEXES TO EXISTING TABLES
-- ============================================================================

-- Messages table - for efficient conversation loading
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at);

-- ============================================================================
-- 10. SAMPLE DATA - Create Ekumen Admin Organization
-- ============================================================================

-- Create Ekumen admin organization
INSERT INTO organizations (name, legal_name, organization_type, status)
VALUES (
    'Ekumen Platform',
    'Ekumen SAS',
    'government_agency',
    'active'
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables created
DO $$
BEGIN
    RAISE NOTICE 'Migration complete! Created tables:';
    RAISE NOTICE '  ✅ organizations';
    RAISE NOTICE '  ✅ organization_memberships';
    RAISE NOTICE '  ✅ organization_farm_access';
    RAISE NOTICE '  ✅ response_feedback';
    RAISE NOTICE '  ✅ knowledge_base_documents';
    RAISE NOTICE '  ✅ voice_journal_entries';
    RAISE NOTICE '  ✅ weather_cache';
    RAISE NOTICE '';
    RAISE NOTICE 'Updated tables:';
    RAISE NOTICE '  ✅ conversations (added organization_id, title, last_message_at)';
END $$;

