-- Fix ambiguous column references in functions

-- Drop and recreate functions with properly qualified column names

DROP FUNCTION IF EXISTS get_personal_account_by_id(TEXT);
DROP FUNCTION IF EXISTS create_personal_account_bypass_rls(TEXT);
DROP FUNCTION IF EXISTS get_organization_by_id(TEXT);
DROP FUNCTION IF EXISTS create_organization_bypass_rls(TEXT);

-- Function to get personal account by user ID
CREATE OR REPLACE FUNCTION get_personal_account_by_id(input_user_id TEXT)
RETURNS SETOF personal_accounts
SECURITY DEFINER
LANGUAGE sql
AS $$
    SELECT * FROM personal_accounts pa WHERE pa.user_id = input_user_id;
$$;

-- Function to create personal account
CREATE OR REPLACE FUNCTION create_personal_account_bypass_rls(input_user_id TEXT)
RETURNS SETOF personal_accounts
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO personal_accounts (user_id) 
    VALUES (input_user_id)
    ON CONFLICT (user_id) DO NOTHING;
    
    RETURN QUERY SELECT * FROM personal_accounts WHERE user_id = input_user_id;
END;
$$;

-- Function to get organization by org ID
CREATE OR REPLACE FUNCTION get_organization_by_id(input_org_id TEXT)
RETURNS SETOF organizations
SECURITY DEFINER
LANGUAGE sql
AS $$
    SELECT * FROM organizations o WHERE o.org_id = input_org_id;
$$;

-- Function to create organization
CREATE OR REPLACE FUNCTION create_organization_bypass_rls(input_org_id TEXT)
RETURNS SETOF organizations
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO organizations (org_id) 
    VALUES (input_org_id)
    ON CONFLICT (org_id) DO NOTHING;
    
    RETURN QUERY SELECT * FROM organizations WHERE org_id = input_org_id;
END;
$$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Functions fixed - ambiguous columns resolved!';
    RAISE NOTICE '🔧 Using input_user_id and input_org_id parameters to avoid conflicts';
END $$;

