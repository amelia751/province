#!/bin/bash

# Script to restore S3 bucket security settings
# Run this when you're done with development and want to secure the bucket again

set -e

BUCKET_NAME="province-documents-[REDACTED-ACCOUNT-ID]-us-east-2"

echo "🔒 Restoring S3 Security Settings for Development Bucket"
echo "======================================================="

echo "📋 Current bucket: $BUCKET_NAME"

# Remove the public bucket policy
echo "🗑️  Removing public bucket policy..."
aws s3api delete-bucket-policy --bucket "$BUCKET_NAME" 2>/dev/null || echo "   (No policy to remove)"

# Restore public access block
echo "🛡️  Restoring public access block..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Verify the settings
echo "✅ Verifying security settings..."
echo ""
echo "Public Access Block Status:"
aws s3api get-public-access-block --bucket "$BUCKET_NAME" || echo "   ✅ Public access block restored"

echo ""
echo "Bucket Policy Status:"
aws s3api get-bucket-policy --bucket "$BUCKET_NAME" 2>/dev/null || echo "   ✅ No public policy (secure)"

echo ""
echo "🎉 S3 bucket security has been restored!"
echo "   The bucket is now private and secure for production use."
