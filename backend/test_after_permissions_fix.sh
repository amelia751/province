#!/bin/bash
# Test script to run after fixing Bedrock permissions

echo "🧪 Testing Bedrock Setup After Permissions Fix"
echo "================================================"
echo ""

# Set environment variables
export AWS_ACCESS_KEY_ID=[REDACTED-AWS-KEY-1]
export AWS_SECRET_ACCESS_KEY='[REDACTED-AWS-SECRET-1]'
export AWS_DEFAULT_REGION=us-east-1
export AWS_REGION=us-east-1
export BEDROCK_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Activate virtual environment
source venv/bin/activate

echo "Step 1: Testing basic Bedrock connectivity..."
echo "----------------------------------------------"
python3 test_direct_invoke.py
RESULT1=$?

if [ $RESULT1 -ne 0 ]; then
    echo ""
    echo "❌ Basic connectivity test failed!"
    echo "Please ensure you've completed BOTH steps in BEDROCK_SETUP_GUIDE.md"
    exit 1
fi

echo ""
echo "Step 2: Testing template generation..."
echo "----------------------------------------------"
python3 -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('src')))

from ai_legal_os.services.ai_template_generator import AITemplateGenerator

async def test():
    print('🔄 Initializing AI Template Generator...')
    generator = AITemplateGenerator()
    
    print('🔄 Generating a simple template...')
    template = await generator.generate_template_from_description(
        description='A basic personal injury case template for automobile accidents',
        practice_area='Personal Injury',
        matter_type='Motor Vehicle Accident',
        jurisdiction='US-CA',
        user_id='test_user'
    )
    
    print(f'✅ Template Generated: {template.name}')
    print(f'   - Folders: {len(template.folders)}')
    print(f'   - Documents: {len(template.starter_docs)}')
    print(f'   - Deadlines: {len(template.deadlines)}')
    print(f'   - Agents: {len(template.agents)}')
    
    return True

try:
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
RESULT2=$?

echo ""
echo "================================================"
if [ $RESULT2 -eq 0 ]; then
    echo "🎉 SUCCESS! Bedrock is fully working!"
    echo ""
    echo "Your backend can now:"
    echo "  ✅ Connect to AWS Bedrock"
    echo "  ✅ Invoke Claude AI models"
    echo "  ✅ Generate legal matter templates"
    echo ""
    echo "Next steps:"
    echo "  - Run 'make test' to run all backend tests"
    echo "  - Use the API endpoints to generate templates"
    echo "  - Integrate with your frontend application"
else
    echo "❌ Template generation failed"
    echo ""
    echo "Possible issues:"
    echo "  - Model not enabled (check Bedrock console)"
    echo "  - Wrong model ID for your region"
    echo "  - IAM policies still propagating (wait 5-10 minutes)"
fi

exit $RESULT2

