#!/usr/bin/env python3
"""
Examine the new Bedrock Data Automation project and blueprints.
"""

import boto3
import os
import sys
import json
from botocore.exceptions import ClientError

def get_bedrock_client():
    """Get Bedrock Data Automation client with proper credentials."""
    
    data_automation_access_key = os.getenv('DATA_AUTOMATION_AWS_ACCESS_KEY_ID')
    data_automation_secret_key = os.getenv('DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not data_automation_access_key or not data_automation_secret_key:
        print("❌ Error: Data Automation AWS credentials not found")
        return None
    
    return boto3.client(
        'bedrock-data-automation',
        region_name=aws_region,
        aws_access_key_id=data_automation_access_key,
        aws_secret_access_key=data_automation_secret_key
    )

def examine_project():
    """Examine the new project details."""
    
    client = get_bedrock_client()
    if not client:
        return None
    
    project_arn = os.getenv('BEDROCK_DATA_AUTOMATION_PROJECT_ARN')
    if not project_arn:
        print("❌ Error: BEDROCK_DATA_AUTOMATION_PROJECT_ARN not found")
        return None
    
    try:
        print(f"📋 Examining project: {project_arn}")
        
        response = client.get_data_automation_project(projectArn=project_arn)
        project = response['project']
        
        print(f"✅ Project Details:")
        print(f"   Name: {project.get('projectName', 'Unknown')}")
        print(f"   Description: {project.get('projectDescription', 'No description')}")
        print(f"   Status: {project.get('projectStatus', 'Unknown')}")
        print(f"   Stage: {project.get('projectStage', 'Unknown')}")
        print(f"   Created: {project.get('creationTime', 'Unknown')}")
        print(f"   Updated: {project.get('lastModifiedTime', 'Unknown')}")
        
        # Check for configuration details
        if 'standardOutputConfiguration' in project:
            print(f"   Has Standard Output Config: ✅")
        if 'customOutputConfiguration' in project:
            print(f"   Has Custom Output Config: ✅")
        
        return project
        
    except ClientError as e:
        print(f"❌ Error examining project: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def list_all_blueprints():
    """List all available blueprints."""
    
    client = get_bedrock_client()
    if not client:
        return []
    
    try:
        print("\n📋 Listing all available blueprints...")
        
        response = client.list_blueprints()
        blueprints = response.get('blueprints', [])
        
        print(f"✅ Found {len(blueprints)} total blueprints:")
        
        standard_blueprints = []
        custom_blueprints = []
        
        for i, blueprint in enumerate(blueprints, 1):
            name = blueprint.get('blueprintName', 'Unknown')
            arn = blueprint.get('blueprintArn', 'Unknown')
            stage = blueprint.get('blueprintStage', 'Unknown')
            version = blueprint.get('blueprintVersion', 'Unknown')
            blueprint_type = blueprint.get('type', 'Unknown')
            
            print(f"\n   {i}. {name}")
            print(f"      ARN: {arn}")
            print(f"      Type: {blueprint_type}")
            print(f"      Stage: {stage}")
            print(f"      Version: {version}")
            
            # Categorize blueprints
            if 'standard' in name.lower() or blueprint_type == 'STANDARD':
                standard_blueprints.append(blueprint)
            else:
                custom_blueprints.append(blueprint)
        
        print(f"\n📊 Blueprint Summary:")
        print(f"   Standard Blueprints: {len(standard_blueprints)}")
        print(f"   Custom Blueprints: {len(custom_blueprints)}")
        
        # Show categorized blueprints
        if standard_blueprints:
            print(f"\n🔧 Standard Blueprints:")
            for bp in standard_blueprints:
                print(f"   - {bp.get('blueprintName')}")
        
        if custom_blueprints:
            print(f"\n🎯 Custom Blueprints:")
            for bp in custom_blueprints:
                print(f"   - {bp.get('blueprintName')}")
        
        return blueprints
        
    except ClientError as e:
        print(f"❌ Error listing blueprints: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []

def examine_profile():
    """Examine the profile configuration."""
    
    profile_arn = os.getenv('BEDROCK_DATA_AUTOMATION_PROFILE_ARN')
    if not profile_arn:
        print("❌ Error: BEDROCK_DATA_AUTOMATION_PROFILE_ARN not found")
        return None
    
    print(f"\n📋 Profile ARN: {profile_arn}")
    
    # Extract information from the ARN
    if 'us.data-automation-v1' in profile_arn:
        print("   Type: Standard US Data Automation Profile")
        print("   Supports: General document processing")
    else:
        print("   Type: Custom Profile")
    
    return profile_arn

def check_s3_buckets():
    """Check the S3 buckets configuration."""
    
    input_bucket = os.getenv('DOCUMENTS_BUCKET_NAME')
    output_bucket = os.getenv('BEDROCK_OUTPUT_BUCKET_NAME')
    
    print(f"\n📋 S3 Configuration:")
    print(f"   Input Bucket: {input_bucket}")
    print(f"   Output Bucket: {output_bucket}")
    
    # Test bucket access
    s3_client = boto3.client('s3', region_name='us-east-1')
    
    try:
        # Test input bucket
        if input_bucket:
            s3_client.head_bucket(Bucket=input_bucket)
            print(f"   ✅ Input bucket accessible")
        
        # Test output bucket
        if output_bucket:
            s3_client.head_bucket(Bucket=output_bucket)
            print(f"   ✅ Output bucket accessible")
            
    except Exception as e:
        print(f"   ⚠️ Bucket access issue: {e}")

def main():
    """Main function."""
    print("🏗️ New Bedrock Data Automation Project Examination")
    print("=" * 60)
    
    # Check environment variables
    required_vars = [
        'BEDROCK_DATA_AUTOMATION_PROJECT_ARN',
        'BEDROCK_DATA_AUTOMATION_PROFILE_ARN',
        'BEDROCK_OUTPUT_BUCKET_NAME',
        'DATA_AUTOMATION_AWS_ACCESS_KEY_ID',
        'DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return 1
    
    # Step 1: Examine the project
    print("\n" + "="*60)
    project = examine_project()
    
    # Step 2: List all blueprints
    print("\n" + "="*60)
    blueprints = list_all_blueprints()
    
    # Step 3: Examine the profile
    print("\n" + "="*60)
    profile = examine_profile()
    
    # Step 4: Check S3 buckets
    print("\n" + "="*60)
    check_s3_buckets()
    
    # Summary and recommendations
    print("\n" + "="*60)
    print("📊 Summary and Recommendations:")
    
    if project:
        print(f"✅ Project is accessible and configured")
    
    if blueprints:
        print(f"✅ Found {len(blueprints)} blueprints available")
        
        # Recommend blueprint usage strategy
        standard_count = len([bp for bp in blueprints if 'standard' in bp.get('blueprintName', '').lower()])
        custom_count = len(blueprints) - standard_count
        
        print(f"\n📋 Blueprint Usage Strategy:")
        if custom_count > 0:
            print(f"   🎯 Use custom blueprints for specific document types ({custom_count} available)")
        if standard_count > 0:
            print(f"   🔧 Use standard blueprint as fallback ({standard_count} available)")
        
        print(f"\n💡 Code Update Recommendations:")
        print(f"   1. Update _get_blueprint_profile() to map document types to specific blueprints")
        print(f"   2. Implement fallback to standard blueprint for unknown document types")
        print(f"   3. Test with W-2 documents from the S3 dataset")
    
    if profile:
        print(f"✅ Profile is configured")
    
    print(f"\n🧪 Next Steps:")
    print(f"   1. Test W-2 ingestion with the new configuration")
    print(f"   2. Update code to use appropriate blueprints")
    print(f"   3. Verify document processing results")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
