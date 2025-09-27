-- Migration script to fix Clerk organization ID integration
-- This script drops existing tables and recreates them with proper Clerk ID support

-- Drop all tables in dependency order (reverse of creation order)
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

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Organization table with Clerk ID support
CREATE TABLE organization (
    id TEXT PRIMARY KEY, -- Use Clerk org ID directly (e.g., "org_31owG6R7MT3GfUxcYFIB9HqMHji")
    name TEXT NOT NULL,
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
CREATE INDEX idx_practice_area_org_id ON practice_area(org_id);
CREATE INDEX idx_document_org_id ON document(org_id);
CREATE INDEX idx_document_hash ON document(hash);
CREATE INDEX idx_doc_text_org_id ON doc_text(org_id);
CREATE INDEX idx_doc_text_document_id ON doc_text(document_id);
CREATE INDEX idx_chunk_org_id ON chunk(org_id);
CREATE INDEX idx_chunk_document_id ON chunk(document_id);
CREATE INDEX idx_embedding_org_id ON embedding(org_id);
CREATE INDEX idx_embedding_chunk_id ON embedding(chunk_id);
CREATE INDEX idx_embedding_hash_model ON embedding(hash, model);
CREATE INDEX idx_lead_org_id ON lead(org_id);
CREATE INDEX idx_lead_status ON lead(status);
CREATE INDEX idx_lead_created_at ON lead(created_at);
CREATE INDEX idx_feedback_org_id ON feedback(org_id);
CREATE INDEX idx_feedback_lead_id ON feedback(lead_id);
CREATE INDEX idx_prompt_run_org_id ON prompt_run(org_id);
CREATE INDEX idx_prompt_run_created_at ON prompt_run(created_at);
CREATE INDEX idx_retrieval_log_org_id ON retrieval_log(org_id);

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

-- Organization policy: Allow inserts for any authenticated user, but restrict reads/updates to own org
CREATE POLICY org_isolation ON organization 
    FOR SELECT USING (id = current_setting('app.org_id', true));

CREATE POLICY org_insert_policy ON organization 
    FOR INSERT WITH CHECK (true); -- Allow inserts (will be restricted by application logic)

CREATE POLICY org_update_policy ON organization 
    FOR UPDATE USING (id = current_setting('app.org_id', true));

CREATE POLICY org_user_isolation ON org_user 
    USING (org_id = current_setting('app.org_id', true));

CREATE POLICY practice_area_isolation ON practice_area 
    USING (org_id = current_setting('app.org_id', true));

CREATE POLICY document_isolation ON document 
    USING (org_id = current_setting('app.org_id', true));

CREATE POLICY doc_text_isolation ON doc_text 
    USING (org_id = current_setting('app.org_id', true));

CREATE POLICY chunk_isolation ON chunk 
    USING (org_id = current_setting('app.org_id', true));

CREATE POLICY embedding_isolation ON embedding 
    USING (org_id = current_setting('app.org_id', true));

CREATE POLICY lead_isolation ON lead 
    USING (org_id = current_setting('app.org_id', true));

CREATE POLICY feedback_isolation ON feedback 
    USING (org_id = current_setting('app.org_id', true));

CREATE POLICY prompt_run_isolation ON prompt_run 
    USING (org_id = current_setting('app.org_id', true));

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

-- Add triggers for updated_at
CREATE TRIGGER update_organization_updated_at BEFORE UPDATE ON organization 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lead_updated_at BEFORE UPDATE ON lead 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some default practice areas for testing
-- These will be created when an organization is first set up
-- INSERT INTO practice_area (org_id, name, keywords) VALUES 
-- ('your_org_id_here', 'ADA Title III', ARRAY['ADA', 'accessibility', 'Title III', 'website accessibility', 'digital accessibility']),
-- ('your_org_id_here', 'Product Liability', ARRAY['product liability', 'defective product', 'recall', 'FDA', 'consumer protection']);

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