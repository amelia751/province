import boto3
import os
from botocore.exceptions import ClientError

# Set the Data Automation credentials
os.environ['DATA_AUTOMATION_AWS_ACCESS_KEY_ID'] = '[REDACTED-AWS-KEY-3]'
os.environ['DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY'] = '[REDACTED-AWS-SECRET-3]'

def test_bedrock_invocation():
    try:
        runtime_client = boto3.client(
            'bedrock-data-automation-runtime',
            region_name='us-east-1',
            aws_access_key_id='[REDACTED-AWS-KEY-3]',
            aws_secret_access_key='[REDACTED-AWS-SECRET-3]'
        )
        
        # Try with different profile ARN patterns
        profile_arns = [
            "arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:data-automation-profile/default",
            "arn:aws:bedrock:us-east-1:aws:data-automation-profile/default",
            "arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:data-automation-profile/834f77d00483",
            "arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:data-automation-profile/ingest_w2"
        ]
        
        for profile_arn in profile_arns:
            try:
                print(f"Trying profile ARN: {profile_arn}")
                
                response = runtime_client.invoke_data_automation_async(
                    inputConfiguration={
                        's3Uri': 's3://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1/datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.jpg'
                    },
                    outputConfiguration={
                        's3Uri': 's3://[REDACTED-BEDROCK-BUCKET]/test-new-invoke/'
                    },
                    dataAutomationConfiguration={
                        'dataAutomationProjectArn': 'arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:data-automation-project/834f77d00483',
                        'stage': 'LIVE'
                    },
                    dataAutomationProfileArn=profile_arn
                )
                
                print(f"SUCCESS! Invocation ARN: {response.get('invocationArn')}")
                return response
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']
                print(f"  Failed with {error_code}: {error_msg}")
                continue
        
        print("All profile ARNs failed")
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_bedrock_invocation()
