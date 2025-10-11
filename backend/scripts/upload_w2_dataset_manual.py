#!/usr/bin/env python3
"""
Manual W2 Dataset Upload Script

This script uploads W2 dataset files to S3 documents bucket.
It can work with manually downloaded files or existing local files.

Usage:
1. Download the dataset manually from Kaggle
2. Extract to a local directory
3. Run this script pointing to that directory
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from province.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ManualW2DatasetUploader:
    """Uploads W2 dataset files from local directory to S3."""
    
    def __init__(self):
        self.settings = get_settings()
        self.s3_client = boto3.client('s3')
        self.bucket_name = self.settings.documents_bucket_name
        self.s3_prefix = "datasets/w2-forms/"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        
        # Check AWS credentials by checking the specific bucket
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"AWS credentials and S3 bucket '{self.bucket_name}' verified")
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket '{self.bucket_name}'. Check IAM permissions.")
            else:
                logger.error(f"AWS credentials error: {e}")
            return False
            
        return True
    
    def find_dataset_files(self, dataset_dir: Path) -> List[Path]:
        """Find W2 dataset files in directory."""
        
        if not dataset_dir.exists():
            logger.error(f"Dataset directory does not exist: {dataset_dir}")
            return []
        
        # Look for common file extensions
        extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.csv', '.json']
        files = []
        
        logger.info(f"Searching for files in: {dataset_dir}")
        
        for ext in extensions:
            pattern_lower = f"**/*{ext}"
            pattern_upper = f"**/*{ext.upper()}"
            
            files.extend(dataset_dir.glob(pattern_lower))
            files.extend(dataset_dir.glob(pattern_upper))
        
        # Remove duplicates
        files = list(set(files))
        
        logger.info(f"Found {len(files)} dataset files")
        
        # Log first few files for verification
        for i, file_path in enumerate(files[:5]):
            logger.info(f"  {i+1}. {file_path.name} ({file_path.stat().st_size} bytes)")
        
        if len(files) > 5:
            logger.info(f"  ... and {len(files) - 5} more files")
        
        return files
    
    def upload_to_s3(self, files: List[Path], base_dir: Path) -> Dict[str, Any]:
        """Upload files to S3."""
        
        results = {
            'uploaded': 0,
            'failed': 0,
            'files': []
        }
        
        total_files = len(files)
        logger.info(f"Starting upload of {total_files} files...")
        
        for i, file_path in enumerate(files, 1):
            try:
                # Create S3 key maintaining directory structure
                relative_path = file_path.relative_to(base_dir)
                s3_key = f"{self.s3_prefix}{relative_path}"
                
                # Determine content type
                content_type = self._get_content_type(file_path)
                
                # Upload file
                logger.info(f"[{i}/{total_files}] Uploading: {file_path.name} -> s3://{self.bucket_name}/{s3_key}")
                
                with open(file_path, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=f,
                        ContentType=content_type,
                        Metadata={
                            'source': 'manual-w2-dataset',
                            'dataset': 'fake-w2-us-tax-form-dataset',
                            'original_filename': file_path.name,
                            'upload_timestamp': str(int(file_path.stat().st_mtime))
                        }
                    )
                
                results['uploaded'] += 1
                results['files'].append({
                    'local_path': str(file_path),
                    's3_key': s3_key,
                    'size': file_path.stat().st_size
                })
                
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")
                results['failed'] += 1
        
        return results
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type for file."""
        
        extension = file_path.suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.csv': 'text/csv',
            '.json': 'application/json'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def create_manifest(self, results: Dict[str, Any], manifest_path: Path) -> None:
        """Create a manifest file with upload results."""
        
        manifest = {
            'dataset_name': 'fake-w2-us-tax-form-dataset',
            'bucket_name': self.bucket_name,
            's3_prefix': self.s3_prefix,
            'upload_summary': {
                'total_files': results['uploaded'] + results['failed'],
                'uploaded': results['uploaded'],
                'failed': results['failed']
            },
            'files': results['files']
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Manifest created: {manifest_path}")
    
    def run(self, dataset_dir: str) -> bool:
        """Run the upload process."""
        
        logger.info("Starting manual W2 dataset upload to S3")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Convert to Path object
        dataset_path = Path(dataset_dir).expanduser().resolve()
        
        # Find dataset files
        files = self.find_dataset_files(dataset_path)
        if not files:
            logger.error("No dataset files found")
            return False
        
        # Upload to S3
        results = self.upload_to_s3(files, dataset_path)
        
        # Create manifest
        manifest_path = Path("w2_dataset_manifest.json")
        self.create_manifest(results, manifest_path)
        
        # Print summary
        logger.info("Upload completed!")
        logger.info(f"Successfully uploaded: {results['uploaded']} files")
        logger.info(f"Failed uploads: {results['failed']} files")
        logger.info(f"S3 location: s3://{self.bucket_name}/{self.s3_prefix}")
        
        return results['failed'] == 0


def main():
    """Main function."""
    
    if len(sys.argv) != 2:
        print("Usage: python upload_w2_dataset_manual.py <dataset_directory>")
        print("")
        print("Examples:")
        print("  python upload_w2_dataset_manual.py ~/Downloads/fake-w2-us-tax-form-dataset")
        print("  python upload_w2_dataset_manual.py ./w2-dataset")
        print("")
        print("To get the dataset:")
        print("1. Go to: https://www.kaggle.com/datasets/mcvishnu1/fake-w2-us-tax-form-dataset")
        print("2. Click 'Download' (requires Kaggle account)")
        print("3. Extract the ZIP file")
        print("4. Run this script with the extracted directory path")
        sys.exit(1)
    
    dataset_dir = sys.argv[1]
    
    uploader = ManualW2DatasetUploader()
    success = uploader.run(dataset_dir)
    
    if success:
        logger.info("Dataset upload completed successfully!")
        sys.exit(0)
    else:
        logger.error("Dataset upload failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
