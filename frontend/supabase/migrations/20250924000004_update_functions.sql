-- Update functions to use correct parameter names

-- Drop old functions with wrong parameter names
DROP FUNCTION IF EXISTS get_personal_account_by_id(TEXT);
DROP FUNCTION IF EXISTS create_personal_account_bypass_rls(TEXT);
DROP FUNCTION IF EXISTS get_organization_by_id(TEXT);
DROP FUNCTION IF EXISTS create_organization_bypass_rls(TEXT);

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

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Functions updated with correct parameter names!';
    RAISE NOTICE '🔧 Now using org_id and user_id parameters as expected by the code';
END $$;

