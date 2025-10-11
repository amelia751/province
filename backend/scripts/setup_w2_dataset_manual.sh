#!/bin/bash

# Manual setup script for W2 dataset upload
# This script provides instructions and handles the upload after manual download

set -e

echo "🚀 W2 Dataset Manual Setup"
echo "=========================="

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

# Install dependencies (without kaggle)
echo "📥 Installing dependencies..."
pip install boto3 python-dotenv

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured or invalid"
    echo "Please configure your AWS credentials using 'aws configure'"
    exit 1
fi

echo "✅ AWS credentials verified"

# Check for dataset directory
DATASET_DIR=""
POSSIBLE_DIRS=(
    "$HOME/Downloads/fake-w2-us-tax-form-dataset"
    "./fake-w2-us-tax-form-dataset"
    "./w2-dataset"
    "$HOME/Downloads/archive"
)

echo ""
echo "🔍 Looking for W2 dataset directory..."

for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ Found dataset directory: $dir"
        DATASET_DIR="$dir"
        break
    fi
done

if [ -z "$DATASET_DIR" ]; then
    echo ""
    echo "📥 Dataset not found. Please download it manually:"
    echo ""
    echo "1. Go to: https://www.kaggle.com/datasets/mcvishnu1/fake-w2-us-tax-form-dataset"
    echo "2. Click 'Download' (requires free Kaggle account)"
    echo "3. Extract the ZIP file to one of these locations:"
    echo "   - $HOME/Downloads/fake-w2-us-tax-form-dataset"
    echo "   - ./fake-w2-us-tax-form-dataset"
    echo "   - ./w2-dataset"
    echo ""
    echo "Then run this script again, or use:"
    echo "python scripts/upload_w2_dataset_manual.py <path-to-dataset-directory>"
    echo ""
    exit 1
fi

# Count files in dataset
FILE_COUNT=$(find "$DATASET_DIR" -type f \( -name "*.pdf" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.tiff" -o -name "*.tif" -o -name "*.csv" -o -name "*.json" \) | wc -l)

echo "📊 Found $FILE_COUNT files in dataset directory"

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "⚠️  No W2 files found in $DATASET_DIR"
    echo "Please check that the dataset was extracted correctly."
    exit 1
fi

# Run the upload script
echo ""
echo "🎯 Starting dataset upload..."
echo "This may take a few minutes depending on dataset size..."
echo ""

python scripts/upload_w2_dataset_manual.py "$DATASET_DIR"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Dataset upload completed successfully!"
    echo ""
    echo "📊 Next steps:"
    echo "1. Check the w2_dataset_manifest.json file for upload details"
    echo "2. Test the W2 ingest agent with the uploaded files"
    echo "3. Verify the files are accessible in your S3 bucket"
    echo ""
    echo "🔗 S3 Location: s3://$(python -c "from province.core.config import get_settings; print(get_settings().documents_bucket_name)")/datasets/w2-forms/"
    echo ""
else
    echo ""
    echo "❌ Dataset upload failed!"
    echo "Check the logs above for error details."
    exit 1
fi
