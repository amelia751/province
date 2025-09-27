#!/bin/bash

# Script to run the organization schema migration
# Make sure to set your database connection details

set -e  # Exit on any error

echo "🔄 Running organization schema migration..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo "Please set it to your Postgres connection string, e.g.:"
    echo "export DATABASE_URL='postgresql://user:password@localhost:5432/dbname'"
    exit 1
fi

# Confirm before running (this will drop all data!)
echo "⚠️  WARNING: This will DROP ALL EXISTING TABLES and recreate them!"
echo "⚠️  ALL DATA WILL BE LOST!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 1
fi

# Run the migration
echo "🚀 Executing migration..."
psql "$DATABASE_URL" -f scripts/fix-organization-schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update your application code to use TEXT for org_id instead of UUID"
    echo "2. Test the onboarding flow with a Clerk organization"
    echo "3. Verify RLS policies are working correctly"
else
    echo "❌ Migration failed!"
    exit 1
fi