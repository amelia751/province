#!/bin/bash

# Setup script for downloading Kaggle W2 dataset
# This script sets up the environment and runs the dataset download

set -e

echo "🚀 Setting up Kaggle W2 Dataset Download"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "requirements-dev.txt" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements-dev.txt

# Check for Kaggle credentials
KAGGLE_CONFIG="$HOME/.kaggle/kaggle.json"
if [ ! -f "$KAGGLE_CONFIG" ]; then
    echo ""
    echo "⚠️  Kaggle API credentials not found!"
    echo "Please set up your Kaggle API credentials:"
    echo ""
    echo "1. Go to https://www.kaggle.com/account"
    echo "2. Click 'Create New API Token'"
    echo "3. Download the kaggle.json file"
    echo "4. Move it to ~/.kaggle/kaggle.json"
    echo "5. Run: chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured or invalid"
    echo "Please configure your AWS credentials using 'aws configure'"
    exit 1
fi

echo "✅ AWS credentials verified"

# Check environment variables
if [ -z "$DOCUMENTS_BUCKET_NAME" ]; then
    echo "⚠️  DOCUMENTS_BUCKET_NAME environment variable not set"
    echo "Using default from config..."
fi

# Run the download script
echo ""
echo "🎯 Starting dataset download..."
echo "This may take a few minutes depending on dataset size..."
echo ""

python scripts/download_kaggle_w2_dataset.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Dataset download completed successfully!"
    echo ""
    echo "📊 Next steps:"
    echo "1. Check the w2_dataset_manifest.json file for upload details"
    echo "2. Test the W2 ingest agent with the uploaded files"
    echo "3. Verify the files are accessible in your S3 bucket"
    echo ""
else
    echo ""
    echo "❌ Dataset download failed!"
    echo "Check the logs above for error details."
    exit 1
fi
