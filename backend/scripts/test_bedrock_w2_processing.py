#!/usr/bin/env python3
"""
Test AWS Bedrock Data Automation for W2 processing.

This script tests the existing Bedrock Data Automation project with W2 files
from our dataset to evaluate processing quality and structure extraction.
"""

import os
import json
import boto3
import logging
import asyncio
import time
from typing import Dict, Any, List
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockW2Tester:
    """Test Bedrock Data Automation for W2 processing."""
    
    def __init__(self):
        """Initialize the tester with AWS credentials from environment."""
        # Use general AWS credentials
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.aws_account_id = os.getenv('AWS_ACCOUNT_ID')
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.aws_account_id]):
            raise ValueError("Missing required AWS credentials in environment variables")
        
        # Initialize clients
        self.runtime_client = boto3.client(
            'bedrock-data-automation-runtime',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        
        self.s3_client = boto3.client(
            's3',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        
        # Configuration
        self.project_arn = "arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:data-automation-project/834f77d00483"
        self.documents_bucket = os.getenv('DOCUMENTS_BUCKET_NAME', 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1')
        self.output_bucket = self.documents_bucket  # Use same bucket for output
        
        logger.info(f"Initialized Bedrock W2 Tester for region: {self.aws_region}")
        logger.info(f"Project ARN: {self.project_arn}")
        logger.info(f"Documents bucket: {self.documents_bucket}")
    
    def get_sample_w2_files(self, limit: int = 5) -> List[Dict[str, str]]:
        """Get sample W2 files from our dataset."""
        
        try:
            # List files from the W2 dataset
            response = self.s3_client.list_objects_v2(
                Bucket=self.documents_bucket,
                Prefix='datasets/w2-forms/',
                MaxKeys=limit * 2  # Get more to filter for both PDF and JPG
            )
            
            files = []
            pdf_files = []
            jpg_files = []
            
            for obj in response.get('Contents', []):
                key = obj['Key']
                if key.endswith('.pdf'):
                    pdf_files.append({
                        'key': key,
                        'type': 'PDF',
                        'size': obj['Size']
                    })
                elif key.endswith('.jpg'):
                    jpg_files.append({
                        'key': key,
                        'type': 'JPG',
                        'size': obj['Size']
                    })
            
            # Take equal numbers of PDF and JPG files
            files.extend(pdf_files[:limit//2 + 1])
            files.extend(jpg_files[:limit//2 + 1])
            
            return files[:limit]
            
        except ClientError as e:
            logger.error(f"Failed to list W2 files: {e}")
            return []
    
    def process_w2_document(self, s3_key: str, file_type: str) -> Dict[str, Any]:
        """Process a single W2 document using Bedrock Data Automation."""
        
        try:
            logger.info(f"Processing W2 document: {s3_key} ({file_type})")
            
            # Create output key
            output_key = f"bedrock-output/w2-processing/{os.path.basename(s3_key)}_output/"
            
            # Invoke Bedrock Data Automation
            # Use default profile ARN format
            profile_arn = f"arn:aws:bedrock:{self.aws_region}:{self.aws_account_id}:data-automation-profile/default"
            
            response = self.runtime_client.invoke_data_automation_async(
                inputConfiguration={
                    's3Uri': f"s3://{self.documents_bucket}/{s3_key}"
                },
                outputConfiguration={
                    's3Uri': f"s3://{self.output_bucket}/{output_key}"
                },
                dataAutomationConfiguration={
                    'dataAutomationProjectArn': self.project_arn,
                    'stage': 'LIVE'
                },
                dataAutomationProfileArn=profile_arn
            )
            
            invocation_arn = response['invocationArn']
            logger.info(f"Started processing with invocation ARN: {invocation_arn}")
            
            return {
                'success': True,
                'invocation_arn': invocation_arn,
                'input_s3_key': s3_key,
                'output_s3_key': output_key,
                'file_type': file_type
            }
            
        except ClientError as e:
            logger.error(f"Failed to process W2 document {s3_key}: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_s3_key': s3_key,
                'file_type': file_type
            }
    
    def check_processing_status(self, invocation_arn: str) -> Dict[str, Any]:
        """Check the status of a processing job."""
        
        try:
            response = self.runtime_client.get_invocation_status(
                invocationArn=invocation_arn
            )
            
            return {
                'success': True,
                'status': response.get('status'),
                'invocation_arn': invocation_arn
            }
            
        except ClientError as e:
            logger.error(f"Failed to check status for {invocation_arn}: {e}")
            return {
                'success': False,
                'error': str(e),
                'invocation_arn': invocation_arn
            }
    
    def wait_for_completion(self, invocation_arn: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """Wait for processing to complete."""
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_result = self.check_processing_status(invocation_arn)
            
            if not status_result['success']:
                return status_result
            
            status = status_result['status']
            logger.info(f"Processing status: {status}")
            
            if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                return {
                    'success': True,
                    'final_status': status,
                    'invocation_arn': invocation_arn,
                    'processing_time': time.time() - start_time
                }
            
            time.sleep(10)  # Wait 10 seconds before checking again
        
        return {
            'success': False,
            'error': 'Processing timeout',
            'invocation_arn': invocation_arn,
            'processing_time': time.time() - start_time
        }
    
    def get_processing_results(self, output_s3_key: str) -> Dict[str, Any]:
        """Retrieve processing results from S3."""
        
        try:
            # List files in the output directory
            response = self.s3_client.list_objects_v2(
                Bucket=self.output_bucket,
                Prefix=output_s3_key
            )
            
            results = {}
            
            for obj in response.get('Contents', []):
                key = obj['Key']
                
                # Download and parse JSON results
                if key.endswith('.json'):
                    obj_response = self.s3_client.get_object(
                        Bucket=self.output_bucket,
                        Key=key
                    )
                    
                    content = obj_response['Body'].read().decode('utf-8')
                    results[os.path.basename(key)] = json.loads(content)
            
            return {
                'success': True,
                'results': results,
                'output_files': [obj['Key'] for obj in response.get('Contents', [])]
            }
            
        except ClientError as e:
            logger.error(f"Failed to retrieve results from {output_s3_key}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_w2_extraction(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the extracted W2 data for quality and completeness."""
        
        analysis = {
            'extraction_quality': 'unknown',
            'extracted_fields': [],
            'missing_fields': [],
            'data_accuracy': 'unknown',
            'recommendations': []
        }
        
        # Look for standard output format
        if 'standardOutput.json' in results:
            standard_output = results['standardOutput.json']
            
            # Check if we have pages and elements
            if 'pages' in standard_output and len(standard_output['pages']) > 0:
                page = standard_output['pages'][0]
                
                # Analyze markdown content for W2 fields
                if 'representation' in page and 'markdown' in page['representation']:
                    markdown = page['representation']['markdown']
                    
                    # Check for key W2 fields
                    w2_fields = {
                        'employee_ssn': 'social security number',
                        'employer_ein': 'employer identification number',
                        'employer_name': 'employer.*name',
                        'employee_name': 'employee.*name',
                        'box_1_wages': 'wages.*compensation',
                        'box_2_federal_tax': 'federal income tax withheld',
                        'box_3_ss_wages': 'social security wages',
                        'box_4_ss_tax': 'social security tax withheld',
                        'box_5_medicare_wages': 'medicare wages',
                        'box_6_medicare_tax': 'medicare tax withheld'
                    }
                    
                    extracted_fields = []
                    for field, pattern in w2_fields.items():
                        if pattern.lower() in markdown.lower():
                            extracted_fields.append(field)
                    
                    analysis['extracted_fields'] = extracted_fields
                    analysis['missing_fields'] = [f for f in w2_fields.keys() if f not in extracted_fields]
                    
                    # Quality assessment
                    extraction_rate = len(extracted_fields) / len(w2_fields)
                    if extraction_rate >= 0.8:
                        analysis['extraction_quality'] = 'excellent'
                    elif extraction_rate >= 0.6:
                        analysis['extraction_quality'] = 'good'
                    elif extraction_rate >= 0.4:
                        analysis['extraction_quality'] = 'fair'
                    else:
                        analysis['extraction_quality'] = 'poor'
        
        return analysis
    
    def test_w2_processing(self) -> Dict[str, Any]:
        """Test W2 processing with sample files."""
        
        logger.info("Starting W2 processing test...")
        
        # Get sample files
        sample_files = self.get_sample_w2_files(4)  # Test with 4 files (2 PDF, 2 JPG)
        
        if not sample_files:
            return {
                'success': False,
                'error': 'No sample W2 files found'
            }
        
        test_results = []
        
        for file_info in sample_files:
            logger.info(f"Testing file: {file_info['key']} ({file_info['type']})")
            
            # Process the document
            process_result = self.process_w2_document(file_info['key'], file_info['type'])
            
            if not process_result['success']:
                test_results.append({
                    'file': file_info,
                    'processing': process_result,
                    'status': 'failed'
                })
                continue
            
            # Wait for completion
            completion_result = self.wait_for_completion(process_result['invocation_arn'])
            
            if not completion_result['success'] or completion_result['final_status'] != 'COMPLETED':
                test_results.append({
                    'file': file_info,
                    'processing': process_result,
                    'completion': completion_result,
                    'status': 'failed'
                })
                continue
            
            # Get results
            results = self.get_processing_results(process_result['output_s3_key'])
            
            if not results['success']:
                test_results.append({
                    'file': file_info,
                    'processing': process_result,
                    'completion': completion_result,
                    'results': results,
                    'status': 'failed'
                })
                continue
            
            # Analyze extraction quality
            analysis = self.analyze_w2_extraction(results['results'])
            
            test_results.append({
                'file': file_info,
                'processing': process_result,
                'completion': completion_result,
                'results': results,
                'analysis': analysis,
                'status': 'completed'
            })
            
            logger.info(f"Completed processing {file_info['key']}: {analysis['extraction_quality']} quality")
        
        # Generate summary
        successful_tests = [r for r in test_results if r['status'] == 'completed']
        failed_tests = [r for r in test_results if r['status'] == 'failed']
        
        summary = {
            'total_files_tested': len(test_results),
            'successful_processing': len(successful_tests),
            'failed_processing': len(failed_tests),
            'success_rate': len(successful_tests) / len(test_results) if test_results else 0,
            'extraction_quality_summary': {},
            'file_type_performance': {}
        }
        
        # Analyze by quality
        quality_counts = {}
        for result in successful_tests:
            quality = result['analysis']['extraction_quality']
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        summary['extraction_quality_summary'] = quality_counts
        
        # Analyze by file type
        type_performance = {}
        for result in successful_tests:
            file_type = result['file']['type']
            if file_type not in type_performance:
                type_performance[file_type] = {'count': 0, 'avg_quality': []}
            type_performance[file_type]['count'] += 1
            type_performance[file_type]['avg_quality'].append(result['analysis']['extraction_quality'])
        summary['file_type_performance'] = type_performance
        
        return {
            'success': True,
            'summary': summary,
            'detailed_results': test_results
        }


def main():
    """Main function to test Bedrock Data Automation W2 processing."""
    
    try:
        # Initialize tester
        tester = BedrockW2Tester()
        
        # Run tests
        results = tester.test_w2_processing()
        
        if not results['success']:
            print(f"\n❌ Testing failed: {results.get('error', 'Unknown error')}")
            return
        
        # Save detailed results
        output_file = "bedrock_w2_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Print summary
        summary = results['summary']
        
        print("\n" + "="*60)
        print("BEDROCK DATA AUTOMATION W2 PROCESSING TEST RESULTS")
        print("="*60)
        print(f"✅ Files tested: {summary['total_files_tested']}")
        print(f"✅ Successful processing: {summary['successful_processing']}")
        print(f"❌ Failed processing: {summary['failed_processing']}")
        print(f"📊 Success rate: {summary['success_rate']:.1%}")
        
        print(f"\n📋 Extraction Quality Summary:")
        for quality, count in summary['extraction_quality_summary'].items():
            print(f"  - {quality.title()}: {count} files")
        
        print(f"\n📄 File Type Performance:")
        for file_type, perf in summary['file_type_performance'].items():
            print(f"  - {file_type}: {perf['count']} files processed")
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Recommendations
        if summary['success_rate'] >= 0.8:
            print(f"\n🎉 Excellent! Bedrock Data Automation is working well for W2 processing.")
            print(f"   Ready to integrate with the existing ingest_w2 tool.")
        elif summary['success_rate'] >= 0.6:
            print(f"\n👍 Good results! Some optimization may be needed.")
        else:
            print(f"\n⚠️  Results need improvement. Consider adjusting the project configuration.")
        
        return results
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return None


if __name__ == "__main__":
    main()
