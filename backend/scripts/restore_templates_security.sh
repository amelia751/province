#!/bin/bash
# Script to restore security settings for the templates S3 bucket

echo "🔒 Restoring security settings for templates bucket..."

# Remove the public bucket policy
echo "Removing public bucket policy..."
aws s3api delete-bucket-policy --bucket province-templates-[REDACTED-ACCOUNT-ID]-us-east-2

# Re-enable public access blocks
echo "Re-enabling public access blocks..."
aws s3api put-public-access-block \
    --bucket province-templates-[REDACTED-ACCOUNT-ID]-us-east-2 \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "✅ Templates bucket security restored!"
echo "📋 The bucket is now private again."
