#!/bin/bash
# Setup environment variables for backend testing
# Source this file with: source setup_env.sh

export AWS_ACCESS_KEY_ID=[REDACTED-AWS-KEY-1]
export AWS_SECRET_ACCESS_KEY='[REDACTED-AWS-SECRET-1]'
export AWS_DEFAULT_REGION=us-east-1
export AWS_REGION=us-east-1
export BEDROCK_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
export ENVIRONMENT=development
export DEBUG=true

echo "✅ Environment variables configured"
echo ""
echo "AWS Region: $AWS_REGION"
echo "Bedrock Region: $BEDROCK_REGION"
echo "Bedrock Model: $BEDROCK_MODEL_ID"
echo ""
echo "Note: These credentials are set for this terminal session only."
echo "To make them permanent, add them to ~/.bashrc or ~/.zshrc"

