-- Seed Test Data for Development
-- Date: 2024
-- Description: Create consistent test data for all developers
--
-- IMPORTANT NOTES:
-- 1. Password hash is bcrypt for "Test1234!" - verify compatibility with your AuthService
-- 2. Hardcoded UUIDs are for testing only - use ON CONFLICT to prevent duplicates
-- 3. References existing farm SIRET: 93429231900019 (must exist in exploitations table)
-- 4. Run AFTER 02_add_organizations_and_knowledge_base.sql

-- ============================================================================
-- 1. TEST ORGANIZATIONS
-- ============================================================================

-- Ekumen Platform (already created in migration)
-- Type: government_agency

-- Test Farm
INSERT INTO organizations (id, name, legal_name, siret, organization_type, status)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Ferme Test Dupont',
    'EARL Dupont',
    '12345678901234',
    'farm',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Test Cooperative
INSERT INTO organizations (id, name, legal_name, siret, organization_type, status)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'Coopérative Test ABC',
    'Coopérative Agricole ABC',
    '23456789012345',
    'cooperative',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Test Advisory Firm
INSERT INTO organizations (id, name, legal_name, siret, organization_type, status)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    'AgroConseil Test',
    'AgroConseil SAS',
    '34567890123456',
    'advisor',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Test Phyto Company
INSERT INTO organizations (id, name, legal_name, siret, organization_type, status)
VALUES (
    '44444444-4444-4444-4444-444444444444',
    'PhytoTest Company',
    'PhytoTest SAS',
    '45678901234567',
    'input_company',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 2. TEST USERS
-- ============================================================================

-- Test Farmer (password: Test1234!)
INSERT INTO users (id, email, hashed_password, role, first_name, last_name, phone, status)
VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'farmer@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MHS.K2',  -- Test1234!
    'farmer',
    'Jean',
    'Dupont',
    '+33612345678',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Test Advisor (password: Test1234!)
INSERT INTO users (id, email, hashed_password, role, first_name, last_name, phone, status)
VALUES (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'advisor@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MHS.K2',  -- Test1234!
    'advisor',
    'Marie',
    'Martin',
    '+33623456789',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Test Cooperative Member (password: Test1234!)
INSERT INTO users (id, email, hashed_password, role, first_name, last_name, phone, status)
VALUES (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'coop@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MHS.K2',  -- Test1234!
    'farmer',
    'Pierre',
    'Bernard',
    '+33634567890',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 3. ORGANIZATION MEMBERSHIPS
-- ============================================================================

-- Farmer owns farm
INSERT INTO organization_memberships (organization_id, user_id, role, status)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'owner',
    'active'
) ON CONFLICT (organization_id, user_id) DO NOTHING;

-- Advisor owns advisory firm
INSERT INTO organization_memberships (organization_id, user_id, role, status)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'owner',
    'active'
) ON CONFLICT (organization_id, user_id) DO NOTHING;

-- Farmer is also member of cooperative
INSERT INTO organization_memberships (organization_id, user_id, role, status)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'member',
    'active'
) ON CONFLICT (organization_id, user_id) DO NOTHING;

-- Coop member owns cooperative
INSERT INTO organization_memberships (organization_id, user_id, role, status)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'owner',
    'active'
) ON CONFLICT (organization_id, user_id) DO NOTHING;

-- ============================================================================
-- 4. FARM ACCESS
-- ============================================================================

-- Farm owns its own farm (from existing exploitations table - SIRET: 93429231900019)
INSERT INTO organization_farm_access (organization_id, farm_siret, access_type)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    '93429231900019',
    'owner'
) ON CONFLICT (organization_id, farm_siret) DO NOTHING;

-- Advisor has advisor access to farm
INSERT INTO organization_farm_access (organization_id, farm_siret, access_type)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    '93429231900019',
    'advisor'
) ON CONFLICT (organization_id, farm_siret) DO NOTHING;

-- Cooperative has viewer access to farm
INSERT INTO organization_farm_access (organization_id, farm_siret, access_type)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    '93429231900019',
    'viewer'
) ON CONFLICT (organization_id, farm_siret) DO NOTHING;

-- ============================================================================
-- 5. TEST CONVERSATIONS
-- ============================================================================

-- Conversation 1: Farmer asking about wheat
INSERT INTO conversations (id, user_id, organization_id, farm_siret, title, agent_type, status, last_message_at)
VALUES (
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '11111111-1111-1111-1111-111111111111',
    '93429231900019',
    'Wheat fungicide recommendations',
    'crop_health',
    'active',
    NOW() - INTERVAL '1 hour'
) ON CONFLICT (id) DO NOTHING;

-- Conversation 2: Advisor planning intervention
INSERT INTO conversations (id, user_id, organization_id, farm_siret, title, agent_type, status, last_message_at)
VALUES (
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '33333333-3333-3333-3333-333333333333',
    '93429231900019',
    'Intervention planning for wheat',
    'planning',
    'active',
    NOW() - INTERVAL '2 hours'
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 6. TEST MESSAGES
-- ============================================================================

-- Message 1: User question
INSERT INTO messages (id, conversation_id, content, sender, created_at, message_metadata)
VALUES (
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'Quel fongicide recommandez-vous pour le blé?',
    'user',
    NOW() - INTERVAL '1 hour',
    '{}'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- Message 2: Agent response
INSERT INTO messages (id, conversation_id, content, sender, created_at, message_metadata)
VALUES (
    '10101010-1010-1010-1010-101010101010',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'Pour le blé, je recommande OPUS (Epoxiconazole) à 1.5 L/ha au stade BBCH 30-39.',
    'agent',
    NOW() - INTERVAL '1 hour' + INTERVAL '5 seconds',
    '{
        "tool_calls": [
            {
                "tool_name": "search_ephy_products",
                "arguments": {"crop": "wheat", "pest": "fusarium"},
                "result": {"products": [{"name": "OPUS", "amm": "2070024"}]},
                "execution_time_ms": 85,
                "status": "success"
            }
        ],
        "knowledge_base_used": false,
        "documents_retrieved": [],
        "processing_time_ms": 1200,
        "token_count": {"prompt_tokens": 250, "completion_tokens": 150, "total_tokens": 400},
        "model": "gpt-4",
        "temperature": 0.1,
        "cost_usd": 0.0165
    }'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 7. TEST KNOWLEDGE BASE DOCUMENTS
-- ============================================================================

-- Internal document (farm only)
INSERT INTO knowledge_base_documents (
    id, organization_id, uploaded_by, filename, file_path, file_type,
    document_type, visibility, processing_status, chunk_count
)
VALUES (
    '20202020-2020-2020-2020-202020202020',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'farm_records_2024.pdf',
    'knowledge-base/11111111-1111-1111-1111-111111111111/farm_records_2024.pdf',
    'pdf',
    'invoice',
    'internal',
    'completed',
    15
) ON CONFLICT (id) DO NOTHING;

-- Shared document (phyto company shares with farm)
INSERT INTO knowledge_base_documents (
    id, organization_id, uploaded_by, filename, file_path, file_type,
    document_type, visibility, processing_status, chunk_count,
    shared_with_organizations
)
VALUES (
    '30303030-3030-3030-3030-303030303030',
    '44444444-4444-4444-4444-444444444444',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'roundup_technical_sheet.pdf',
    'knowledge-base/44444444-4444-4444-4444-444444444444/roundup_technical_sheet.pdf',
    'pdf',
    'product_spec',
    'shared',
    'completed',
    25,
    ARRAY['11111111-1111-1111-1111-111111111111'::uuid, '22222222-2222-2222-2222-222222222222'::uuid]
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Seed data created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Test Users:';
    RAISE NOTICE '  farmer@test.com (password: Test1234!)';
    RAISE NOTICE '  advisor@test.com (password: Test1234!)';
    RAISE NOTICE '  coop@test.com (password: Test1234!)';
    RAISE NOTICE '';
    RAISE NOTICE 'Test Organizations:';
    RAISE NOTICE '  Ferme Test Dupont (farm)';
    RAISE NOTICE '  Coopérative Test ABC (cooperative)';
    RAISE NOTICE '  AgroConseil Test (advisor)';
    RAISE NOTICE '  PhytoTest Company (input_company)';
    RAISE NOTICE '';
    RAISE NOTICE 'Test Data:';
    RAISE NOTICE '  2 conversations with messages';
    RAISE NOTICE '  2 knowledge base documents';
    RAISE NOTICE '  Farm access permissions configured';
END $$;

