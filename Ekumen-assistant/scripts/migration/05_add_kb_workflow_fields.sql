-- Add Knowledge Base Workflow Fields
-- Date: 2024
-- Description: Add fields to support superadmin validation workflow for knowledge base documents

-- ============================================================================
-- 1. ADD WORKFLOW FIELDS TO KNOWLEDGE BASE DOCUMENTS
-- ============================================================================

-- Add workflow metadata field for storing approval/rejection information
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS workflow_metadata JSONB DEFAULT '{}';

-- Add submission status field
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS submission_status VARCHAR(50) DEFAULT 'draft';

-- Add approval fields
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES users(id);
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- Add expiration fields for time-bound documents
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS expiration_date DATE;
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS auto_renewal BOOLEAN DEFAULT FALSE;

-- Add quality scoring fields
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS quality_score DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS quality_issues JSONB DEFAULT '[]';
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS quality_recommendations JSONB DEFAULT '[]';

-- Add version control
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS parent_document_id UUID REFERENCES knowledge_base_documents(id);

-- Add indexing for workflow fields
CREATE INDEX IF NOT EXISTS idx_kb_docs_submission_status ON knowledge_base_documents(submission_status);
CREATE INDEX IF NOT EXISTS idx_kb_docs_approved_by ON knowledge_base_documents(approved_by);
CREATE INDEX IF NOT EXISTS idx_kb_docs_expiration ON knowledge_base_documents(expiration_date);
CREATE INDEX IF NOT EXISTS idx_kb_docs_quality_score ON knowledge_base_documents(quality_score);
CREATE INDEX IF NOT EXISTS idx_kb_docs_version ON knowledge_base_documents(version);

-- Add composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_kb_docs_workflow_status ON knowledge_base_documents(submission_status, processing_status);
CREATE INDEX IF NOT EXISTS idx_kb_docs_org_workflow ON knowledge_base_documents(organization_id, submission_status);
CREATE INDEX IF NOT EXISTS idx_kb_docs_expiring ON knowledge_base_documents(expiration_date) WHERE expiration_date IS NOT NULL;

-- ============================================================================
-- 2. CREATE WORKFLOW STATUS ENUM
-- ============================================================================

-- Create enum for submission status
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'submission_status') THEN
        CREATE TYPE submission_status AS ENUM (
            'draft',           -- Document is being prepared
            'submitted',       -- Document submitted for review
            'under_review',    -- Document is being reviewed by superadmin
            'approved',        -- Document approved and available in RAG
            'rejected',        -- Document rejected with reason
            'expired',         -- Document has expired
            'renewal_pending', -- Document needs renewal
            'archived'         -- Document archived (no longer active)
        );
    END IF;
END $$;

-- Update the column to use the enum
ALTER TABLE knowledge_base_documents 
ALTER COLUMN submission_status TYPE submission_status USING submission_status::submission_status;

-- ============================================================================
-- 3. ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON COLUMN knowledge_base_documents.workflow_metadata IS 'JSON metadata for workflow tracking (review notes, quality scores, etc.)';
COMMENT ON COLUMN knowledge_base_documents.submission_status IS 'Current status in the approval workflow';
COMMENT ON COLUMN knowledge_base_documents.approved_by IS 'User ID of superadmin who approved the document';
COMMENT ON COLUMN knowledge_base_documents.approved_at IS 'Timestamp when document was approved';
COMMENT ON COLUMN knowledge_base_documents.rejection_reason IS 'Reason for rejection if document was rejected';
COMMENT ON COLUMN knowledge_base_documents.expiration_date IS 'Date when document expires (for time-bound content)';
COMMENT ON COLUMN knowledge_base_documents.auto_renewal IS 'Whether document should auto-renew before expiration';
COMMENT ON COLUMN knowledge_base_documents.quality_score IS 'Quality score from 0.0 to 1.0';
COMMENT ON COLUMN knowledge_base_documents.quality_issues IS 'Array of quality issues identified during review';
COMMENT ON COLUMN knowledge_base_documents.quality_recommendations IS 'Array of recommendations for improvement';
COMMENT ON COLUMN knowledge_base_documents.version IS 'Document version number';
COMMENT ON COLUMN knowledge_base_documents.parent_document_id IS 'Reference to parent document for versioning';

-- ============================================================================
-- 4. CREATE WORKFLOW AUDIT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_base_workflow_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES knowledge_base_documents(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'submitted', 'reviewed', 'approved', 'rejected', 'expired', 'renewed'
    performed_by UUID REFERENCES users(id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    details JSONB DEFAULT '{}',
    comments TEXT
);

CREATE INDEX idx_kb_audit_document ON knowledge_base_workflow_audit(document_id);
CREATE INDEX idx_kb_audit_action ON knowledge_base_workflow_audit(action);
CREATE INDEX idx_kb_audit_performed_by ON knowledge_base_workflow_audit(performed_by);
CREATE INDEX idx_kb_audit_performed_at ON knowledge_base_workflow_audit(performed_at);

COMMENT ON TABLE knowledge_base_workflow_audit IS 'Audit trail for knowledge base document workflow actions';

-- ============================================================================
-- 5. CREATE NOTIFICATION TABLE FOR WORKFLOW
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_base_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES knowledge_base_documents(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- 'submission_received', 'approval_needed', 'document_approved', 'document_rejected', 'expiration_warning'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_kb_notifications_user ON knowledge_base_notifications(user_id);
CREATE INDEX idx_kb_notifications_document ON knowledge_base_notifications(document_id);
CREATE INDEX idx_kb_notifications_type ON knowledge_base_notifications(notification_type);
CREATE INDEX idx_kb_notifications_unread ON knowledge_base_notifications(user_id, is_read) WHERE is_read = FALSE;

COMMENT ON TABLE knowledge_base_notifications IS 'Notifications for knowledge base workflow events';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Knowledge base workflow fields added successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'New fields added to knowledge_base_documents:';
    RAISE NOTICE '  - workflow_metadata (JSONB)';
    RAISE NOTICE '  - submission_status (enum)';
    RAISE NOTICE '  - approved_by, approved_at, rejection_reason';
    RAISE NOTICE '  - expiration_date, auto_renewal';
    RAISE NOTICE '  - quality_score, quality_issues, quality_recommendations';
    RAISE NOTICE '  - version, parent_document_id';
    RAISE NOTICE '';
    RAISE NOTICE 'New tables created:';
    RAISE NOTICE '  - knowledge_base_workflow_audit';
    RAISE NOTICE '  - knowledge_base_notifications';
    RAISE NOTICE '';
    RAISE NOTICE 'Workflow statuses: draft, submitted, under_review, approved, rejected, expired, renewal_pending, archived';
END $$;
