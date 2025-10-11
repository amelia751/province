# W2 Dataset Setup

This directory contains scripts to download and upload the Kaggle W2 dataset for testing the W2 ingest agent.

## Dataset Information

- **Source**: [Kaggle - Fake W-2 US Tax Form Dataset](https://www.kaggle.com/datasets/mcvishnu1/fake-w2-us-tax-form-dataset)
- **Purpose**: Testing W2 document processing and OCR capabilities
- **Destination**: S3 documents bucket under `datasets/w2-forms/`

## Prerequisites

1. **Kaggle API Credentials**
   ```bash
   # 1. Go to https://www.kaggle.com/account
   # 2. Click "Create New API Token"
   # 3. Download kaggle.json
   # 4. Move to ~/.kaggle/kaggle.json
   chmod 600 ~/.kaggle/kaggle.json
   ```

2. **AWS Credentials**
   ```bash
   aws configure
   # Or ensure your AWS credentials are available via environment variables
   ```

3. **Environment Variables**
   ```bash
   # Optional - will use config defaults if not set
   export DOCUMENTS_BUCKET_NAME=province-documents-[REDACTED-ACCOUNT-ID]-us-east-2
   ```

## Quick Start (Manual Download - Recommended)

```bash
# From the backend directory
cd /Users/anhlam/province/backend

# Option 1: Manual download (no Kaggle API needed)
./scripts/setup_w2_dataset_manual.sh
```

## Manual Download Steps

1. **Download Dataset from Kaggle**
   - Go to: https://www.kaggle.com/datasets/mcvishnu1/fake-w2-us-tax-form-dataset
   - Click "Download" (requires free Kaggle account)
   - Extract the ZIP file to `~/Downloads/fake-w2-us-tax-form-dataset`

2. **Upload to S3**
   ```bash
   # Run the manual upload script
   python scripts/upload_w2_dataset_manual.py ~/Downloads/fake-w2-us-tax-form-dataset
   ```

## Automatic Download (Requires Kaggle API)

If you have Kaggle API credentials set up:

```bash
# Run the automatic setup script
./scripts/setup_w2_dataset.sh
```

## What the Script Does

1. **Validates Prerequisites**
   - Checks Kaggle API credentials
   - Verifies AWS credentials
   - Confirms S3 bucket access

2. **Downloads Dataset**
   - Downloads the Kaggle W2 dataset
   - Extracts files to temporary directory

3. **Uploads to S3**
   - Uploads all W2 files to S3 bucket
   - Maintains directory structure
   - Adds metadata for tracking

4. **Creates Manifest**
   - Generates `w2_dataset_manifest.json`
   - Contains upload summary and file details

## Expected Output

After successful completion:

- **S3 Location**: `s3://province-documents-[REDACTED-ACCOUNT-ID]-us-east-2/datasets/w2-forms/`
- **Manifest File**: `w2_dataset_manifest.json` (local)
- **File Types**: PDF, PNG, JPG, TIFF (W2 forms and images)

## Testing the Dataset

After uploading, test the dataset integration:

```bash
# Test dataset compatibility and W2 agent integration
python scripts/test_w2_dataset.py
```

This will:
- List files in the S3 dataset location
- Analyze file types and compatibility
- Test W2 ingest agent functionality
- Generate a comprehensive test report

## Testing with W2 Ingest Agent

Once uploaded, you can test the W2 ingest agent:

```python
from province.agents.tax.w2_ingest_agent import W2IngestAgent

# Initialize agent
agent = W2IngestAgent()
await agent.create_agent()

# Process a W2 document
response = await agent.invoke(
    session_id="test-session",
    input_text="Process W2 document from s3://bucket/datasets/w2-forms/sample.pdf",
    engagement_id="test-engagement"
)
```

## Troubleshooting

### Kaggle API Issues
- Ensure `~/.kaggle/kaggle.json` exists and has correct permissions (600)
- Verify your Kaggle account has API access enabled

### AWS Issues
- Check AWS credentials: `aws sts get-caller-identity`
- Verify S3 bucket permissions
- Ensure bucket exists: `aws s3 ls s3://your-bucket-name`

### Upload Issues
- Check internet connectivity
- Verify file permissions in temporary directory
- Monitor AWS CloudTrail for S3 API errors

## File Structure

```
backend/scripts/
├── download_kaggle_w2_dataset.py     # Automatic download script (requires Kaggle API)
├── upload_w2_dataset_manual.py       # Manual upload script
├── setup_w2_dataset.sh               # Automatic setup script
├── setup_w2_dataset_manual.sh        # Manual setup script
├── test_w2_dataset.py                 # Dataset testing script
└── W2_DATASET_README.md              # This file
```

## Dataset Manifest Example

```json
{
  "dataset_name": "mcvishnu1/fake-w2-us-tax-form-dataset",
  "bucket_name": "province-documents-[REDACTED-ACCOUNT-ID]-us-east-2",
  "s3_prefix": "datasets/w2-forms/",
  "upload_summary": {
    "total_files": 150,
    "uploaded": 150,
    "failed": 0
  },
  "files": [
    {
      "local_path": "/tmp/w2_001.pdf",
      "s3_key": "datasets/w2-forms/w2_001.pdf",
      "size": 245760
    }
  ]
}
```
