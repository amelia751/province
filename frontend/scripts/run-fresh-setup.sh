#!/bin/bash

# Script to run fresh database setup (drops all tables and recreates from scratch)
# Use this when you want to start completely fresh with no existing data

set -e  # Exit on any error

echo "🔄 Running fresh database setup..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo "Please set it to your Postgres connection string, e.g.:"
    echo "export DATABASE_URL='postgresql://user:password@localhost:5432/dbname'"
    exit 1
fi

# Confirm before running (this will drop all data!)
echo "⚠️  WARNING: This will DROP ALL EXISTING TABLES and recreate the entire schema!"
echo "⚠️  ALL DATA WILL BE PERMANENTLY LOST!"
echo ""
read -p "Are you sure you want to continue? (type 'FRESH' to confirm): " confirm

if [ "$confirm" != "FRESH" ]; then
    echo "❌ Setup cancelled"
    exit 1
fi

# Run the fresh setup
echo "🚀 Executing fresh database setup..."
psql "$DATABASE_URL" -f scripts/fresh-database-setup.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Fresh database setup completed successfully!"
    echo ""
    echo "📋 What was created:"
    echo "   • All tables dropped and recreated"
    echo "   • RLS policies configured for tenant isolation"
    echo "   • Performance indexes added"
    echo "   • Triggers for automatic timestamps"
    echo "   • Analytics views for reporting"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Test the onboarding flow with a Clerk organization"
    echo "2. Verify organization creation works without RLS errors"
    echo "3. Check that tenant isolation is working properly"
    echo ""
    echo "🔧 Environment variables needed:"
    echo "   • NEXT_PUBLIC_SUPABASE_URL"
    echo "   • NEXT_PUBLIC_SUPABASE_KEY (anon key)"
    echo "   • SUPABASE_SERVICE_ROLE_KEY (for admin operations)"
else
    echo "❌ Fresh setup failed!"
    exit 1
fi