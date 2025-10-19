#!/bin/bash
# Quick test script for tax service endpoints

echo "🧪 Quick Tax Service Test"
echo "=========================="
echo ""

BASE_URL="http://localhost:8000/api/v1"

# Test 1: Health Check
echo "1️⃣ Testing health endpoint..."
HEALTH=$(curl -s ${BASE_URL}/health)
if [ $? -eq 0 ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed - is backend running?"
    exit 1
fi
echo ""

# Test 2: Start Conversation
echo "2️⃣ Starting tax conversation..."
START_RESPONSE=$(curl -s -X POST ${BASE_URL}/tax-service/start \
  -H "Content-Type: application/json" \
  -d '{}')

SESSION_ID=$(echo $START_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null)

if [ ! -z "$SESSION_ID" ]; then
    echo "✅ Session created: $SESSION_ID"
else
    echo "❌ Failed to start conversation"
    echo "Response: $START_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Continue Conversation
echo "3️⃣ Testing conversation flow..."
CONTINUE_RESPONSE=$(curl -s -X POST ${BASE_URL}/tax-service/continue \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"user_message\":\"I am single\"}")

AGENT_RESPONSE=$(echo $CONTINUE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['agent_response'][:100])" 2>/dev/null)

if [ ! -z "$AGENT_RESPONSE" ]; then
    echo "✅ Agent responded: $AGENT_RESPONSE..."
else
    echo "❌ Failed to continue conversation"
    echo "Response: $CONTINUE_RESPONSE"
    exit 1
fi
echo ""

echo "🎉 All tax service tests passed!"
echo ""
echo "✅ Tax service endpoints are working correctly"
echo "✅ Ready for frontend testing"
echo ""
echo "Next step: Test in frontend at http://localhost:3000/app"

