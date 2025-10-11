#!/usr/bin/env python3
"""
Download Kaggle W2 dataset and upload to S3 documents bucket.

This script downloads the fake W-2 US tax form dataset from Kaggle
and uploads it to the configured S3 documents bucket for processing
by the W2 ingest agent.

Requirements:
- Kaggle API credentials configured (~/.kaggle/kaggle.json)
- AWS credentials configured
- boto3 installed
"""

import os
import sys
import json
import zipfile
import tempfile
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


class KaggleW2DatasetDownloader:
    """Downloads Kaggle W2 dataset and uploads to S3."""
    
    def __init__(self):
        self.settings = get_settings()
        self.s3_client = boto3.client('s3')
        self.bucket_name = self.settings.documents_bucket_name
        
        # Kaggle dataset details
        self.dataset_name = "mcvishnu1/fake-w2-us-tax-form-dataset"
        self.s3_prefix = "datasets/w2-forms/"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        
        # Check Kaggle API credentials
        kaggle_config_path = Path.home() / ".kaggle" / "kaggle.json"
        if not kaggle_config_path.exists():
            logger.error("Kaggle API credentials not found. Please set up ~/.kaggle/kaggle.json")
            logger.error("Visit https://www.kaggle.com/account to get your API token")
            return False
            
        # Check AWS credentials by checking the specific bucket
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("AWS credentials and bucket access verified")
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
    
    def install_kaggle_api(self) -> bool:
        """Install Kaggle API if not available."""
        
        try:
            import kaggle
            logger.info("Kaggle API already available")
            return True
        except ImportError:
            logger.info("Installing Kaggle API...")
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "kaggle"])
                logger.info("Kaggle API installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install Kaggle API: {e}")
                return False
    
    def download_dataset(self, download_dir: Path) -> bool:
        """Download the Kaggle dataset."""
        
        try:
            import kaggle
            
            logger.info(f"Downloading dataset: {self.dataset_name}")
            kaggle.api.dataset_download_files(
                self.dataset_name,
                path=str(download_dir),
                unzip=True
            )
            
            logger.info(f"Dataset downloaded to: {download_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            return False
    
    def get_dataset_files(self, dataset_dir: Path) -> List[Path]:
        """Get list of dataset files."""
        
        # Look for common file extensions
        extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif']
        files = []
        
        for ext in extensions:
            files.extend(dataset_dir.glob(f"**/*{ext}"))
            files.extend(dataset_dir.glob(f"**/*{ext.upper()}"))
        
        logger.info(f"Found {len(files)} dataset files")
        return files
    
    def upload_to_s3(self, files: List[Path], base_dir: Path) -> Dict[str, Any]:
        """Upload files to S3."""
        
        results = {
            'uploaded': 0,
            'failed': 0,
            'files': []
        }
        
        for file_path in files:
            try:
                # Create S3 key maintaining directory structure
                relative_path = file_path.relative_to(base_dir)
                s3_key = f"{self.s3_prefix}{relative_path}"
                
                # Determine content type
                content_type = self._get_content_type(file_path)
                
                # Upload file
                logger.info(f"Uploading: {file_path.name} -> s3://{self.bucket_name}/{s3_key}")
                
                with open(file_path, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=f,
                        ContentType=content_type,
                        Metadata={
                            'source': 'kaggle-w2-dataset',
                            'dataset': self.dataset_name,
                            'original_filename': file_path.name,
                            'upload_timestamp': str(int(os.path.getmtime(file_path)))
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
            '.tif': 'image/tiff'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def create_manifest(self, results: Dict[str, Any], manifest_path: Path) -> None:
        """Create a manifest file with upload results."""
        
        manifest = {
            'dataset_name': self.dataset_name,
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
    
    def run(self) -> bool:
        """Run the complete download and upload process."""
        
        logger.info("Starting Kaggle W2 dataset download and S3 upload")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Install Kaggle API if needed
        if not self.install_kaggle_api():
            return False
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download dataset
            if not self.download_dataset(temp_path):
                return False
            
            # Get dataset files
            files = self.get_dataset_files(temp_path)
            if not files:
                logger.error("No dataset files found")
                return False
            
            # Upload to S3
            results = self.upload_to_s3(files, temp_path)
            
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
    
    downloader = KaggleW2DatasetDownloader()
    success = downloader.run()
    
    if success:
        logger.info("Dataset download and upload completed successfully!")
        sys.exit(0)
    else:
        logger.error("Dataset download and upload failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
