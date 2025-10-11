#!/usr/bin/env python3
"""
Test W2 Dataset Integration

This script tests the uploaded W2 dataset with the W2 ingest agent
to verify compatibility and processing capabilities.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from province.core.config import get_settings
from province.agents.tax.w2_ingest_agent import W2IngestAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class W2DatasetTester:
    """Tests W2 dataset integration with the ingest agent."""
    
    def __init__(self):
        self.settings = get_settings()
        self.s3_client = boto3.client('s3')
        self.bucket_name = self.settings.documents_bucket_name
        self.s3_prefix = "datasets/w2-forms/"
        
    def list_dataset_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List files in the W2 dataset S3 location."""
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.s3_prefix,
                MaxKeys=limit
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'filename': Path(obj['Key']).name
                    })
            
            logger.info(f"Found {len(files)} files in S3 dataset location")
            return files
            
        except ClientError as e:
            logger.error(f"Error listing S3 files: {e}")
            return []
    
    def check_file_types(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze file types in the dataset."""
        
        file_types = {}
        
        for file_info in files:
            filename = file_info['filename']
            extension = Path(filename).suffix.lower()
            
            if extension in file_types:
                file_types[extension] += 1
            else:
                file_types[extension] = 1
        
        logger.info("File type distribution:")
        for ext, count in file_types.items():
            logger.info(f"  {ext}: {count} files")
        
        return file_types
    
    async def test_w2_agent_creation(self) -> bool:
        """Test creating the W2 ingest agent."""
        
        try:
            logger.info("Testing W2 ingest agent creation...")
            agent = W2IngestAgent()
            
            # Note: We won't actually create the agent to avoid AWS costs
            # Just test that the class can be instantiated
            logger.info("✅ W2IngestAgent class instantiated successfully")
            
            # Test validation methods with sample data
            sample_boxes = {
                "1": "50000.00",
                "2": "7500.00",
                "3": "50000.00",
                "4": "3100.00",
                "5": "50000.00",
                "6": "725.00"
            }
            
            anomalies = agent.validate_w2_boxes(sample_boxes, 2024)
            logger.info(f"✅ W2 validation test completed - found {len(anomalies)} anomalies")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ W2 agent test failed: {e}")
            return False
    
    def generate_test_report(self, files: List[Dict[str, Any]], file_types: Dict[str, int]) -> Dict[str, Any]:
        """Generate a test report."""
        
        total_size = sum(f['size'] for f in files)
        
        # Check for expected W2 file types
        expected_types = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif']
        w2_files = sum(count for ext, count in file_types.items() if ext in expected_types)
        
        report = {
            'dataset_location': f"s3://{self.bucket_name}/{self.s3_prefix}",
            'total_files': len(files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_types': file_types,
            'w2_compatible_files': w2_files,
            'compatibility_score': round((w2_files / len(files)) * 100, 1) if files else 0,
            'sample_files': [f['filename'] for f in files[:5]],
            'recommendations': []
        }
        
        # Add recommendations
        if report['w2_compatible_files'] == 0:
            report['recommendations'].append("No W2-compatible files found. Check dataset contents.")
        elif report['compatibility_score'] < 50:
            report['recommendations'].append("Low compatibility score. Dataset may contain non-W2 files.")
        else:
            report['recommendations'].append("Dataset appears compatible with W2 processing.")
        
        if '.pdf' in file_types:
            report['recommendations'].append("PDF files found - ideal for OCR processing with Textract.")
        
        if any(ext in file_types for ext in ['.png', '.jpg', '.jpeg', '.tiff']):
            report['recommendations'].append("Image files found - can be processed with Textract.")
        
        return report
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        
        logger.info("Starting W2 dataset integration tests")
        
        # List dataset files
        files = self.list_dataset_files(limit=50)
        if not files:
            logger.error("No files found in dataset location")
            return {'success': False, 'error': 'No files found'}
        
        # Analyze file types
        file_types = self.check_file_types(files)
        
        # Test W2 agent
        agent_test_passed = await self.test_w2_agent_creation()
        
        # Generate report
        report = self.generate_test_report(files, file_types)
        report['agent_test_passed'] = agent_test_passed
        report['success'] = agent_test_passed and len(files) > 0
        
        return report


async def main():
    """Main function."""
    
    tester = W2DatasetTester()
    results = await tester.run_tests()
    
    # Save results to file
    report_path = Path("w2_dataset_test_report.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*50)
    print("W2 DATASET TEST SUMMARY")
    print("="*50)
    
    if results.get('success'):
        print("✅ Overall Status: PASSED")
    else:
        print("❌ Overall Status: FAILED")
    
    print(f"📊 Dataset Location: {results.get('dataset_location', 'Unknown')}")
    print(f"📁 Total Files: {results.get('total_files', 0)}")
    print(f"💾 Total Size: {results.get('total_size_mb', 0)} MB")
    print(f"🎯 W2 Compatible Files: {results.get('w2_compatible_files', 0)}")
    print(f"📈 Compatibility Score: {results.get('compatibility_score', 0)}%")
    
    if results.get('agent_test_passed'):
        print("🤖 W2 Agent Test: PASSED")
    else:
        print("🤖 W2 Agent Test: FAILED")
    
    print("\n📋 File Types:")
    for ext, count in results.get('file_types', {}).items():
        print(f"   {ext}: {count} files")
    
    print("\n💡 Recommendations:")
    for rec in results.get('recommendations', []):
        print(f"   • {rec}")
    
    print("\n📄 Sample Files:")
    for filename in results.get('sample_files', []):
        print(f"   • {filename}")
    
    print("="*50)
    
    if results.get('success'):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
