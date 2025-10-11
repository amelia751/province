-- Drop all existing tables and start fresh
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
DROP FUNCTION IF EXISTS get_organization_by_id(TEXT) CASCADE;
DROP FUNCTION IF EXISTS create_organization_bypass_rls CASCADE;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ All tables dropped successfully!';
    RAISE NOTICE '🧹 Database is now clean and ready for new schema';
END $$;
