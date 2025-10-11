-- Create simple tables for personal accounts and organizations

-- Simple personal accounts table
CREATE TABLE personal_accounts (
    user_id TEXT PRIMARY KEY, -- Clerk user ID
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Simple organizations table
CREATE TABLE organizations (
    org_id TEXT PRIMARY KEY, -- Clerk organization ID
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Junction table for organization membership
CREATE TABLE organization_members (
    org_id TEXT REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL, -- Clerk user ID
    role TEXT DEFAULT 'member' CHECK (role IN ('admin', 'member')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (org_id, user_id)
);

-- Create indexes
CREATE INDEX idx_personal_accounts_user_id ON personal_accounts(user_id);
CREATE INDEX idx_organizations_org_id ON organizations(org_id);
CREATE INDEX idx_organization_members_org_id ON organization_members(org_id);
CREATE INDEX idx_organization_members_user_id ON organization_members(user_id);

-- Enable Row Level Security
ALTER TABLE personal_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

-- RLS Policies for personal_accounts
CREATE POLICY personal_accounts_policy ON personal_accounts 
    FOR ALL USING (user_id = current_setting('app.user_id', true));

-- RLS Policies for organizations (members can read, admins can modify)
CREATE POLICY organizations_select_policy ON organizations 
    FOR SELECT USING (
        org_id IN (
            SELECT om.org_id 
            FROM organization_members om 
            WHERE om.user_id = current_setting('app.user_id', true)
        )
    );

CREATE POLICY organizations_modify_policy ON organizations 
    FOR ALL USING (
        org_id IN (
            SELECT om.org_id 
            FROM organization_members om 
            WHERE om.user_id = current_setting('app.user_id', true) 
            AND om.role = 'admin'
        )
    );

-- RLS Policies for organization_members
CREATE POLICY organization_members_policy ON organization_members 
    FOR ALL USING (
        org_id IN (
            SELECT om.org_id 
            FROM organization_members om 
            WHERE om.user_id = current_setting('app.user_id', true)
        )
    );

-- Create function to automatically update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    return NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_personal_accounts_updated_at BEFORE UPDATE ON personal_accounts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Helper functions that bypass RLS

-- Function to get personal account by user ID
CREATE OR REPLACE FUNCTION get_personal_account_by_id(user_id TEXT)
RETURNS SETOF personal_accounts
SECURITY DEFINER
LANGUAGE sql
AS $$
    SELECT * FROM personal_accounts pa WHERE pa.user_id = get_personal_account_by_id.user_id;
$$;

-- Function to create personal account
CREATE OR REPLACE FUNCTION create_personal_account_bypass_rls(user_id TEXT)
RETURNS SETOF personal_accounts
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO personal_accounts (user_id) 
    VALUES (create_personal_account_bypass_rls.user_id)
    ON CONFLICT (user_id) DO NOTHING;
    
    RETURN QUERY SELECT * FROM personal_accounts WHERE personal_accounts.user_id = create_personal_account_bypass_rls.user_id;
END;
$$;

-- Function to get organization by org ID
CREATE OR REPLACE FUNCTION get_organization_by_id(org_id TEXT)
RETURNS SETOF organizations
SECURITY DEFINER
LANGUAGE sql
AS $$
    SELECT * FROM organizations o WHERE o.org_id = get_organization_by_id.org_id;
$$;

-- Function to create organization
CREATE OR REPLACE FUNCTION create_organization_bypass_rls(org_id TEXT)
RETURNS SETOF organizations
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO organizations (org_id) 
    VALUES (create_organization_bypass_rls.org_id)
    ON CONFLICT (org_id) DO NOTHING;
    
    RETURN QUERY SELECT * FROM organizations WHERE organizations.org_id = create_organization_bypass_rls.org_id;
END;
$$;

-- Add helpful comments
COMMENT ON TABLE personal_accounts IS 'Simple personal accounts using Clerk user IDs';
COMMENT ON TABLE organizations IS 'Simple organizations using Clerk organization IDs';
COMMENT ON TABLE organization_members IS 'Organization membership mapping';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Simple account schema created successfully!';
    RAISE NOTICE '👤 personal_accounts table: stores user_id from Clerk';
    RAISE NOTICE '🏢 organizations table: stores org_id from Clerk';
    RAISE NOTICE '👥 organization_members table: maps users to organizations';
    RAISE NOTICE '🔒 RLS policies enabled for secure access';
    RAISE NOTICE '🎯 Ready for simple account management!';
END $$;
