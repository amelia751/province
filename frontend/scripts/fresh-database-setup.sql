-- Fresh Database Setup Script
-- This script drops all existing tables and recreates the entire schema from scratch
-- Use this when you want to start completely fresh with no existing data

-- Drop all tables in dependency order (reverse of creation order)
DROP TABLE IF EXISTS retrieval_log CASCADE;
DROP TABLE IF EXISTS prompt_run CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS lead CASCADE;
DROP TABLE IF EXISTS embedding CASCADE;
DROP TABLE IF EXISTS chunk CASCADE;
DROP TABLE IF EXISTS doc_text CASCADE;
DROP TABLE IF EXISTS document CASCADE;
DROP TABLE IF EXISTS practice_area CASCADE;
DROP TABLE IF EXISTS org_user CASCADE;
DROP TABLE IF EXISTS organization CASCADE;

-- Drop any existing functions
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Organization table with Clerk ID support
CREATE TABLE organization (
    id TEXT PRIMARY KEY, -- Use Clerk org ID directly (e.g., "org_31owG6R7MT3GfUxcYFIB9HqMHji")
    region TEXT DEFAULT '',
    website TEXT,
    timezone TEXT DEFAULT 'America/Chicago',
    practice_areas TEXT[] DEFAULT '{}',
    jurisdictions TEXT[] DEFAULT '{}',
    keywords_include TEXT[] DEFAULT '{}',
    keywords_exclude TEXT[] DEFAULT '{}',
    -- Source configuration
    source_courtlistener BOOLEAN DEFAULT true,
    source_openfda BOOLEAN DEFAULT true,
    source_doj BOOLEAN DEFAULT true,
    source_rss BOOLEAN DEFAULT false,
    -- Digest settings
    digest_enabled BOOLEAN DEFAULT true,
    digest_cadence TEXT DEFAULT 'weekly' CHECK (digest_cadence IN ('daily', 'weekly')),
    digest_hour_local INTEGER DEFAULT 9 CHECK (digest_hour_local >= 0 AND digest_hour_local <= 23),
    -- Billing
    billing TEXT DEFAULT 'trial' CHECK (billing IN ('trial', 'active', 'past_due')),
    trial_ends_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User-organization mapping
CREATE TABLE org_user (
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL, -- Clerk user ID
    role TEXT NOT NULL CHECK (role IN ('admin', 'attorney', 'analyst')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (org_id, user_id)
);

-- Practice area configuration
CREATE TABLE practice_area (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document storage and processing
CREATE TABLE document (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    object_key TEXT NOT NULL,
    mime_type TEXT,
    hash TEXT NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    UNIQUE(org_id, hash) -- Prevent duplicate documents per org
);

CREATE TABLE doc_text (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    document_id UUID REFERENCES document(id) ON DELETE CASCADE,
    version INTEGER DEFAULT 1,
    text TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chunk (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    document_id UUID REFERENCES document(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    text TEXT NOT NULL,
    tokens INTEGER,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, idx) -- Ensure chunk ordering
);

-- Vector embeddings
CREATE TABLE embedding (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES chunk(id) ON DELETE CASCADE,
    vector vector(1536), -- pgvector extension for OpenAI embeddings
    model TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    hash TEXT NOT NULL, -- Hash of chunk content + model for deduplication
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(hash, model) -- Prevent duplicate embeddings
);

-- Lead management
CREATE TABLE lead (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    practice_area_id UUID REFERENCES practice_area(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    summary TEXT,
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    jurisdiction TEXT,
    source_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'contacted', 'dismissed'))
);

-- User feedback and observability
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES lead(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL, -- Clerk user ID
    label TEXT CHECK (label IN ('useful', 'not_useful')),
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prompt_run (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    user_id TEXT, -- Clerk user ID (nullable for system runs)
    model TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10,6),
    task_type TEXT, -- e.g., 'brief_generation', 'embedding', 'rerank'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Retrieval logging for analytics
CREATE TABLE retrieval_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    user_id TEXT, -- Clerk user ID (nullable for system queries)
    query TEXT NOT NULL,
    filters JSONB DEFAULT '{}',
    selected_chunk_ids UUID[] DEFAULT '{}',
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_org_user_org_id ON org_user(org_id);
CREATE INDEX idx_org_user_user_id ON org_user(user_id);

CREATE INDEX idx_practice_area_org_id ON practice_area(org_id);
CREATE INDEX idx_practice_area_enabled ON practice_area(enabled);

CREATE INDEX idx_document_org_id ON document(org_id);
CREATE INDEX idx_document_source ON document(source);
CREATE INDEX idx_document_hash ON document(hash);
CREATE INDEX idx_document_ingested_at ON document(ingested_at);

CREATE INDEX idx_doc_text_org_id ON doc_text(org_id);
CREATE INDEX idx_doc_text_document_id ON doc_text(document_id);

CREATE INDEX idx_chunk_org_id ON chunk(org_id);
CREATE INDEX idx_chunk_document_id ON chunk(document_id);
CREATE INDEX idx_chunk_idx ON chunk(idx);

CREATE INDEX idx_embedding_org_id ON embedding(org_id);
CREATE INDEX idx_embedding_chunk_id ON embedding(chunk_id);
CREATE INDEX idx_embedding_hash_model ON embedding(hash, model);
CREATE INDEX idx_embedding_model ON embedding(model);

CREATE INDEX idx_lead_org_id ON lead(org_id);
CREATE INDEX idx_lead_practice_area_id ON lead(practice_area_id);
CREATE INDEX idx_lead_status ON lead(status);
CREATE INDEX idx_lead_confidence ON lead(confidence);
CREATE INDEX idx_lead_created_at ON lead(created_at);
CREATE INDEX idx_lead_jurisdiction ON lead(jurisdiction);

CREATE INDEX idx_feedback_org_id ON feedback(org_id);
CREATE INDEX idx_feedback_lead_id ON feedback(lead_id);
CREATE INDEX idx_feedback_user_id ON feedback(user_id);
CREATE INDEX idx_feedback_label ON feedback(label);

CREATE INDEX idx_prompt_run_org_id ON prompt_run(org_id);
CREATE INDEX idx_prompt_run_user_id ON prompt_run(user_id);
CREATE INDEX idx_prompt_run_model ON prompt_run(model);
CREATE INDEX idx_prompt_run_task_type ON prompt_run(task_type);
CREATE INDEX idx_prompt_run_created_at ON prompt_run(created_at);

CREATE INDEX idx_retrieval_log_org_id ON retrieval_log(org_id);
CREATE INDEX idx_retrieval_log_user_id ON retrieval_log(user_id);
CREATE INDEX idx_retrieval_log_created_at ON retrieval_log(created_at);

-- Enable Row Level Security (RLS) on all tenant tables
ALTER TABLE organization ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE practice_area ENABLE ROW LEVEL SECURITY;
ALTER TABLE document ENABLE ROW LEVEL SECURITY;
ALTER TABLE doc_text ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunk ENABLE ROW LEVEL SECURITY;
ALTER TABLE embedding ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_run ENABLE ROW LEVEL SECURITY;
ALTER TABLE retrieval_log ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for tenant isolation
-- Note: These policies assume app.org_id is set to the Clerk organization ID

-- Organization policies: Allow inserts for any authenticated user, but restrict reads/updates to own org
CREATE POLICY org_select_policy ON organization 
    FOR SELECT USING (id = current_setting('app.org_id', true));

CREATE POLICY org_insert_policy ON organization 
    FOR INSERT WITH CHECK (true); -- Allow inserts (will be restricted by application logic)

CREATE POLICY org_update_policy ON organization 
    FOR UPDATE USING (id = current_setting('app.org_id', true));

CREATE POLICY org_delete_policy ON organization 
    FOR DELETE USING (id = current_setting('app.org_id', true));

-- Org user policies
CREATE POLICY org_user_select_policy ON org_user 
    FOR SELECT USING (org_id = current_setting('app.org_id', true));

CREATE POLICY org_user_insert_policy ON org_user 
    FOR INSERT WITH CHECK (org_id = current_setting('app.org_id', true));

CREATE POLICY org_user_update_policy ON org_user 
    FOR UPDATE USING (org_id = current_setting('app.org_id', true));

CREATE POLICY org_user_delete_policy ON org_user 
    FOR DELETE USING (org_id = current_setting('app.org_id', true));

-- Practice area policies
CREATE POLICY practice_area_isolation ON practice_area 
    USING (org_id = current_setting('app.org_id', true));

-- Document policies
CREATE POLICY document_isolation ON document 
    USING (org_id = current_setting('app.org_id', true));

-- Doc text policies
CREATE POLICY doc_text_isolation ON doc_text 
    USING (org_id = current_setting('app.org_id', true));

-- Chunk policies
CREATE POLICY chunk_isolation ON chunk 
    USING (org_id = current_setting('app.org_id', true));

-- Embedding policies
CREATE POLICY embedding_isolation ON embedding 
    USING (org_id = current_setting('app.org_id', true));

-- Lead policies
CREATE POLICY lead_isolation ON lead 
    USING (org_id = current_setting('app.org_id', true));

-- Feedback policies
CREATE POLICY feedback_isolation ON feedback 
    USING (org_id = current_setting('app.org_id', true));

-- Prompt run policies
CREATE POLICY prompt_run_isolation ON prompt_run 
    USING (org_id = current_setting('app.org_id', true));

-- Retrieval log policies
CREATE POLICY retrieval_log_isolation ON retrieval_log 
    USING (org_id = current_setting('app.org_id', true));

-- Create function to automatically update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a helper function for setting configuration (if not exists)
CREATE OR REPLACE FUNCTION set_config(setting_name text, setting_value text, is_local boolean DEFAULT false)
RETURNS text
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config(setting_name, setting_value, is_local);
    RETURN setting_value;
END;
$$;

-- Create a function to get organization by ID that bypasses RLS
CREATE OR REPLACE FUNCTION get_organization_by_id(org_id TEXT)
RETURNS TABLE(
    id TEXT,
    region TEXT,
    website TEXT,
    timezone TEXT,
    practice_areas TEXT[],
    jurisdictions TEXT[],
    keywords_include TEXT[],
    keywords_exclude TEXT[],
    source_courtlistener BOOLEAN,
    source_openfda BOOLEAN,
    source_doj BOOLEAN,
    source_rss BOOLEAN,
    digest_enabled BOOLEAN,
    digest_cadence TEXT,
    digest_hour_local INTEGER,
    billing TEXT,
    trial_ends_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
SECURITY DEFINER -- This allows the function to bypass RLS
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        o.id,
        o.region,
        o.website,
        o.timezone,
        o.practice_areas,
        o.jurisdictions,
        o.keywords_include,
        o.keywords_exclude,
        o.source_courtlistener,
        o.source_openfda,
        o.source_doj,
        o.source_rss,
        o.digest_enabled,
        o.digest_cadence,
        o.digest_hour_local,
        o.billing,
        o.trial_ends_at,
        o.created_at,
        o.updated_at
    FROM organization o
    WHERE o.id = org_id;
END;
$$;

-- Create a function to create organizations that bypasses RLS
CREATE OR REPLACE FUNCTION create_organization_bypass_rls(
    org_id TEXT,
    org_region TEXT DEFAULT '',
    org_website TEXT DEFAULT NULL,
    org_timezone TEXT DEFAULT 'America/Chicago',
    org_practice_areas TEXT[] DEFAULT '{}',
    org_jurisdictions TEXT[] DEFAULT '{}',
    org_keywords_include TEXT[] DEFAULT '{}',
    org_keywords_exclude TEXT[] DEFAULT '{}',
    org_digest_cadence TEXT DEFAULT 'weekly',
    org_digest_hour_local INTEGER DEFAULT 9
)
RETURNS TABLE(
    id TEXT,
    region TEXT,
    website TEXT,
    timezone TEXT,
    practice_areas TEXT[],
    jurisdictions TEXT[],
    keywords_include TEXT[],
    keywords_exclude TEXT[],
    source_courtlistener BOOLEAN,
    source_openfda BOOLEAN,
    source_doj BOOLEAN,
    source_rss BOOLEAN,
    digest_enabled BOOLEAN,
    digest_cadence TEXT,
    digest_hour_local INTEGER,
    billing TEXT,
    trial_ends_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
SECURITY DEFINER -- This allows the function to bypass RLS
LANGUAGE plpgsql
AS $$
DECLARE
    trial_end_date TIMESTAMPTZ;
    new_org organization%ROWTYPE;
BEGIN
    -- Calculate trial end date (14 days from now)
    trial_end_date := NOW() + INTERVAL '14 days';
    
    -- Insert the organization (bypasses RLS due to SECURITY DEFINER)
    INSERT INTO organization (
        id, region, website, timezone,
        practice_areas, jurisdictions, keywords_include, keywords_exclude,
        source_courtlistener, source_openfda, source_doj, source_rss,
        digest_enabled, digest_cadence, digest_hour_local,
        billing, trial_ends_at
    ) VALUES (
        org_id, org_region, org_website, org_timezone,
        org_practice_areas, org_jurisdictions, org_keywords_include, org_keywords_exclude,
        true, true, true, false,
        true, org_digest_cadence, org_digest_hour_local,
        'trial', trial_end_date
    ) RETURNING * INTO new_org;
    
    -- Return the created organization
    RETURN QUERY SELECT 
        new_org.id,
        new_org.region,
        new_org.website,
        new_org.timezone,
        new_org.practice_areas,
        new_org.jurisdictions,
        new_org.keywords_include,
        new_org.keywords_exclude,
        new_org.source_courtlistener,
        new_org.source_openfda,
        new_org.source_doj,
        new_org.source_rss,
        new_org.digest_enabled,
        new_org.digest_cadence,
        new_org.digest_hour_local,
        new_org.billing,
        new_org.trial_ends_at,
        new_org.created_at,
        new_org.updated_at;
END;
$$;

-- Add triggers for updated_at
CREATE TRIGGER update_organization_updated_at BEFORE UPDATE ON organization 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lead_updated_at BEFORE UPDATE ON lead 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create some helpful views for analytics
CREATE VIEW org_stats AS
SELECT 
    o.id as org_id,
    o.billing,
    o.trial_ends_at,
    COUNT(DISTINCT d.id) as total_documents,
    COUNT(DISTINCT l.id) as total_leads,
    COUNT(DISTINCT f.id) as total_feedback,
    SUM(pr.cost_usd) as total_cost_usd,
    o.created_at as org_created_at
FROM organization o
LEFT JOIN document d ON o.id = d.org_id
LEFT JOIN lead l ON o.id = l.org_id
LEFT JOIN feedback f ON o.id = f.org_id
LEFT JOIN prompt_run pr ON o.id = pr.org_id
GROUP BY o.id, o.billing, o.trial_ends_at, o.created_at;

-- Enable RLS on the view
ALTER VIEW org_stats SET (security_invoker = true);

-- Add helpful comments
COMMENT ON TABLE organization IS 'Organizations using Clerk org IDs as primary keys';
COMMENT ON TABLE org_user IS 'User-organization membership mapping';
COMMENT ON TABLE practice_area IS 'Practice areas configured per organization';
COMMENT ON TABLE document IS 'Raw documents ingested from various sources';
COMMENT ON TABLE doc_text IS 'Normalized text extracted from documents';
COMMENT ON TABLE chunk IS 'Text chunks for vector search and RAG';
COMMENT ON TABLE embedding IS 'Vector embeddings for semantic search';
COMMENT ON TABLE lead IS 'Potential litigation leads identified by the system';
COMMENT ON TABLE feedback IS 'User feedback on lead quality';
COMMENT ON TABLE prompt_run IS 'LLM usage tracking for cost monitoring';
COMMENT ON TABLE retrieval_log IS 'Search and retrieval analytics';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Database schema created successfully!';
    RAISE NOTICE '📊 Tables created: organization, org_user, practice_area, document, doc_text, chunk, embedding, lead, feedback, prompt_run, retrieval_log';
    RAISE NOTICE '🔒 RLS policies enabled for tenant isolation';
    RAISE NOTICE '📈 Indexes created for optimal performance';
    RAISE NOTICE '🔧 Triggers and functions set up for automatic timestamps';
    RAISE NOTICE '📋 Ready for organization onboarding!';
END $$;