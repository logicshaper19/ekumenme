-- Rollback Migration: Remove Organizations and Knowledge Base
-- Date: 2024
-- Description: Safely rollback migration 02 if needed

-- ============================================================================
-- ROLLBACK IN REVERSE ORDER (to respect foreign key constraints)
-- ============================================================================

-- 1. Drop indexes on existing tables
DROP INDEX IF EXISTS idx_messages_conversation_created;
DROP INDEX IF EXISTS idx_conversations_user_org_time;
DROP INDEX IF EXISTS idx_conversations_status;
DROP INDEX IF EXISTS idx_conversations_last_message;
DROP INDEX IF EXISTS idx_conversations_organization;

-- 2. Remove columns from conversations table
ALTER TABLE conversations 
DROP COLUMN IF EXISTS deleted_at,
DROP COLUMN IF EXISTS status,
DROP COLUMN IF EXISTS last_message_at,
DROP COLUMN IF EXISTS title,
DROP COLUMN IF EXISTS organization_id;

-- 3. Drop weather cache
DROP TABLE IF EXISTS weather_cache CASCADE;

-- 4. Drop voice journal entries
DROP TABLE IF EXISTS voice_journal_entries CASCADE;

-- 5. Drop knowledge base documents
DROP TABLE IF EXISTS knowledge_base_documents CASCADE;

-- 6. Drop response feedback
DROP TABLE IF EXISTS response_feedback CASCADE;

-- 7. Drop organization farm access
DROP TABLE IF EXISTS organization_farm_access CASCADE;

-- 8. Drop organization memberships
DROP TABLE IF EXISTS organization_memberships CASCADE;

-- 9. Drop organizations
DROP TABLE IF EXISTS organizations CASCADE;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Rollback complete! Removed:';
    RAISE NOTICE '  ✅ organizations';
    RAISE NOTICE '  ✅ organization_memberships';
    RAISE NOTICE '  ✅ organization_farm_access';
    RAISE NOTICE '  ✅ response_feedback';
    RAISE NOTICE '  ✅ knowledge_base_documents';
    RAISE NOTICE '  ✅ voice_journal_entries';
    RAISE NOTICE '  ✅ weather_cache';
    RAISE NOTICE '';
    RAISE NOTICE 'Reverted conversations table to original state';
END $$;

