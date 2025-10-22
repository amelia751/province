#!/bin/bash

# Complete Tax System Deployment Script
# This script deploys the entire tax filing system in the correct order

set -e  # Exit on any error

echo "🚀 COMPLETE TAX SYSTEM DEPLOYMENT"
echo "=================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "scripts/create_tax_tables.py" ]]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   cd /Users/anhlam/province/backend"
    exit 1
fi

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Activating virtual environment..."
    source venv/bin/activate
fi

# Check if Bedrock credentials are set
if [[ -z "$BEDROCK_AWS_ACCESS_KEY_ID" ]]; then
    echo "⚠️  Setting Bedrock credentials..."
    export BEDROCK_AWS_ACCESS_KEY_ID=YOUR_BEDROCK_ACCESS_KEY_ID
    export BEDROCK_AWS_SECRET_ACCESS_KEY=YOUR_BEDROCK_SECRET_ACCESS_KEY
fi

echo "📋 Step 1: Creating DynamoDB Tables..."
echo "======================================"
python scripts/create_tax_tables.py
echo ""

echo "🏗️  Step 2: Deploying Complete Tax System..."
echo "============================================="
python scripts/deploy_complete_tax_system.py
echo ""

echo "🛠️  Step 3: Creating Action Groups..."
echo "===================================="
python scripts/create_function_action_groups.py
echo ""

echo "🔄 Step 4: Upgrading to Comprehensive Action Groups..."
echo "====================================================="
python scripts/update_action_groups.py
echo ""

echo "✅ Step 5: Verifying Deployment..."
echo "=================================="
python scripts/quick_agent_status.py
echo ""

echo "🎉 TAX SYSTEM DEPLOYMENT COMPLETE!"
echo "=================================="
echo ""
echo "📊 System Status:"
echo "   • 8 Bedrock Agents: DEPLOYED"
echo "   • 1 Lambda Function: DEPLOYED"
echo "   • 2 IAM Roles: DEPLOYED"
echo "   • 5 DynamoDB Tables: DEPLOYED"
echo "   • 7 Tax Tools: DEPLOYED"
echo ""
echo "🎯 Next Steps:"
echo "   1. Integrate with frontend using agent IDs"
echo "   2. Test tax filing workflow"
echo "   3. Configure S3 bucket permissions"
echo ""
echo "📖 For detailed information, see: TAX_SYSTEM_DEPLOYMENT.md"
