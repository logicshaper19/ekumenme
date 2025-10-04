-- Add New Users and Organizations
-- Date: 2024
-- Description: Add Dijon Céréales cooperative and DE SANGOSSE EPHY company with users
--
-- IMPORTANT NOTES:
-- 1. Password hash is bcrypt for "Test1234!" - verify compatibility with your AuthService
-- 2. Hardcoded UUIDs are for testing only - use ON CONFLICT to prevent duplicates
-- 3. Run AFTER 03_seed_test_data.sql

-- ============================================================================
-- 1. NEW ORGANIZATIONS
-- ============================================================================

-- Dijon Céréales Cooperative
INSERT INTO organizations (
    id, name, legal_name, siret, organization_type, status,
    email, phone, website, address, postal_code, city, region_code, country,
    legal_form, specialization, services_offered, description
)
VALUES (
    '55555555-5555-5555-5555-555555555555',
    'Dijon Céréales',
    'Coopérative Dijon Céréales',
    '12345678901235',
    'COOPERATIVE',
    'ACTIVE',
    'contact@dijon-cereales.fr',
    '+33380123456',
    'https://www.dijon-cereales.fr',
    '123 Rue de la Coopérative',
    '21000',
    'Dijon',
    'BFC',
    'France',
    'Coopérative',
    '["cereals", "oilseeds", "protein_crops"]'::jsonb,
    '["grain_collection", "technical_advice", "input_supply", "storage"]'::jsonb,
    'Coopérative agricole spécialisée dans la collecte et la commercialisation de céréales en Bourgogne-Franche-Comté'
) ON CONFLICT (id) DO NOTHING;

-- DE SANGOSSE EPHY Company
INSERT INTO organizations (
    id, name, legal_name, siret, organization_type, status,
    email, phone, website, address, postal_code, city, region_code, country,
    legal_form, specialization, services_offered, description
)
VALUES (
    '66666666-6666-6666-6666-666666666666',
    'DE SANGOSSE',
    'DE SANGOSSE SAS',
    '12345678901236',
    'INPUT_COMPANY',
    'ACTIVE',
    'contact@desangosse.com',
    '+33512345678',
    'https://www.desangosse.com',
    '456 Avenue des Produits Phytosanitaires',
    '31000',
    'Toulouse',
    'OCC',
    'France',
    'SAS',
    '["crop_protection", "plant_health", "biocontrol"]'::jsonb,
    '["product_development", "technical_support", "regulatory_compliance", "training"]'::jsonb,
    'Entreprise spécialisée dans la protection des cultures et la santé des plantes'
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 2. NEW USERS
-- ============================================================================

-- Martin - Dijon Céréales Cooperative Member
INSERT INTO users (
    id, email, hashed_password, full_name, phone, role, status,
    language_preference, timezone, region_code, department_code,
    is_active, is_verified, is_superuser, specialization
)
VALUES (
    '77777777-7777-7777-7777-777777777777',
    'martin@dijon-cereales.fr',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MHS.K2',  -- Test1234!
    'Martin Dubois',
    '+33612345679',
    'ADVISOR',
    'ACTIVE',
    'fr',
    'Europe/Paris',
    'BFC',
    '21',
    true,
    true,
    false,
    ARRAY['cereals', 'technical_advice', 'cooperative_management']
) ON CONFLICT (id) DO NOTHING;

-- Mathieu - DE SANGOSSE EPHY Company Employee
INSERT INTO users (
    id, email, hashed_password, full_name, phone, role, status,
    language_preference, timezone, region_code, department_code,
    is_active, is_verified, is_superuser, specialization
)
VALUES (
    '88888888-8888-8888-8888-888888888888',
    'mathieu@desangosse.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MHS.K2',  -- Test1234!
    'Mathieu Leroy',
    '+33623456780',
    'ADVISOR',
    'ACTIVE',
    'fr',
    'Europe/Paris',
    'OCC',
    '31',
    true,
    true,
    false,
    ARRAY['crop_protection', 'regulatory_compliance', 'product_development']
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 3. ORGANIZATION MEMBERSHIPS
-- ============================================================================

-- Martin is owner/admin of Dijon Céréales
INSERT INTO organization_memberships (id, organization_id, user_id, role, access_level, is_active)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    '55555555-5555-5555-5555-555555555555',
    '77777777-7777-7777-7777-777777777777',
    'admin',
    'ADMIN',
    true
);

-- Mathieu is admin of DE SANGOSSE
INSERT INTO organization_memberships (id, organization_id, user_id, role, access_level, is_active)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    '66666666-6666-6666-6666-666666666666',
    '88888888-8888-8888-8888-888888888888',
    'admin',
    'ADMIN',
    true
);

-- ============================================================================
-- 4. USER NAVIGATION PREFERENCES
-- ============================================================================

-- Martin's navigation preferences (Assistant, Knowledge Base, Analytics)
UPDATE users 
SET notification_preferences = '{
    "navigation_items": ["assistant", "knowledge_base", "analytics"],
    "default_landing": "assistant",
    "sidebar_collapsed": false,
    "theme": "light"
}'::jsonb
WHERE id = '77777777-7777-7777-7777-777777777777';

-- Mathieu's navigation preferences (Assistant, Knowledge Base, Analytics)
UPDATE users 
SET notification_preferences = '{
    "navigation_items": ["assistant", "knowledge_base", "analytics"],
    "default_landing": "assistant",
    "sidebar_collapsed": false,
    "theme": "light"
}'::jsonb
WHERE id = '88888888-8888-8888-8888-888888888888';

-- ============================================================================
-- 5. SAMPLE KNOWLEDGE BASE DOCUMENTS
-- ============================================================================
-- Note: Knowledge base documents will be added when the knowledge_base_documents table is created

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'New users and organizations created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'New Organizations:';
    RAISE NOTICE '  Dijon Céréales (cooperative) - ID: 55555555-5555-5555-5555-555555555555';
    RAISE NOTICE '  DE SANGOSSE (input_company) - ID: 66666666-6666-6666-6666-666666666666';
    RAISE NOTICE '';
    RAISE NOTICE 'New Users:';
    RAISE NOTICE '  martin@dijon-cereales.fr (password: Test1234!) - Dijon Céréales admin';
    RAISE NOTICE '  mathieu@desangosse.com (password: Test1234!) - DE SANGOSSE admin';
    RAISE NOTICE '';
    RAISE NOTICE 'Navigation Items:';
    RAISE NOTICE '  Both users have: Assistant, Knowledge Base, Analytics';
    RAISE NOTICE '';
    RAISE NOTICE 'Sample Documents:';
    RAISE NOTICE '  Knowledge base documents will be added when the table is created';
END $$;
