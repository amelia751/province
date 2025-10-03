# AWS Infrastructure Setup Guide for Province

## Current Issue: DynamoDB Permissions

The Province backend is currently unable to save generated templates to DynamoDB due to insufficient AWS IAM permissions. Here's what's happening and how to fix it.

## 🚨 Current Error

```
AccessDeniedException: User: arn:aws:iam::[REDACTED-ACCOUNT-ID]:user/province is not authorized to perform: dynamodb:PutItem on resource: arn:aws:dynamodb:us-east-2:[REDACTED-ACCOUNT-ID]:table/province-templates
```

## 🔍 Root Cause Analysis

The current AWS user (`province`) has limited permissions that only allow:
- ✅ **Bedrock access** (working perfectly)
- ✅ **STS operations** (identity verification)
- ❌ **DynamoDB operations** (missing permissions)
- ❌ **S3 operations** (missing permissions)
- ❌ **CloudFormation operations** (missing permissions)

## 🛠️ Solution Options

### Option 1: Add Permissions to Existing User (Recommended for Development)

#### Step 1: Optimized Single Inline Policy (Under 2048 chars)

**OPTIMIZED POLICY**: Compressed to fit exactly under 2048 characters:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["dynamodb:*","s3:*","cloudformation:*","iam:CreateRole","iam:DeleteRole","iam:GetRole","iam:PassRole","iam:*RolePolicy","iam:List*Policies","lambda:*","apigateway:*","logs:*"],"Resource":["arn:aws:dynamodb:us-east-2:[REDACTED-ACCOUNT-ID]:table/province-*","arn:aws:dynamodb:us-east-2:[REDACTED-ACCOUNT-ID]:table/province-*/index/*","arn:aws:s3:::province-*","arn:aws:s3:::province-*/*","arn:aws:cloudformation:us-east-2:[REDACTED-ACCOUNT-ID]:stack/Province*","arn:aws:cloudformation:us-east-2:[REDACTED-ACCOUNT-ID]:stack/CDKToolkit*","arn:aws:iam::[REDACTED-ACCOUNT-ID]:role/Province*","arn:aws:iam::[REDACTED-ACCOUNT-ID]:role/cdk-*","arn:aws:lambda:us-east-2:[REDACTED-ACCOUNT-ID]:function:province-*","arn:aws:apigateway:us-east-2::*","arn:aws:logs:us-east-2:[REDACTED-ACCOUNT-ID]:*"]}]}
```

**Character Count**: ~1,789 characters (under 2048 limit!)

**Alternative: Readable Version (if you prefer formatting)**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "dynamodb:*",
      "s3:*", 
      "cloudformation:*",
      "iam:CreateRole",
      "iam:DeleteRole", 
      "iam:GetRole",
      "iam:PassRole",
      "iam:*RolePolicy",
      "iam:List*Policies",
      "lambda:*",
      "apigateway:*",
      "logs:*"
    ],
    "Resource": [
      "arn:aws:dynamodb:us-east-2:[REDACTED-ACCOUNT-ID]:table/province-*",
      "arn:aws:dynamodb:us-east-2:[REDACTED-ACCOUNT-ID]:table/province-*/index/*",
      "arn:aws:s3:::province-*",
      "arn:aws:s3:::province-*/*",
      "arn:aws:cloudformation:us-east-2:[REDACTED-ACCOUNT-ID]:stack/Province*",
      "arn:aws:cloudformation:us-east-2:[REDACTED-ACCOUNT-ID]:stack/CDKToolkit*",
      "arn:aws:iam::[REDACTED-ACCOUNT-ID]:role/Province*",
      "arn:aws:iam::[REDACTED-ACCOUNT-ID]:role/cdk-*",
      "arn:aws:lambda:us-east-2:[REDACTED-ACCOUNT-ID]:function:province-*",
      "arn:aws:apigateway:us-east-2::*",
      "arn:aws:logs:us-east-2:[REDACTED-ACCOUNT-ID]:*"
    ]
  }]
}
```

**Optimizations Made:**
- ✅ **Wildcards**: Used `dynamodb:*`, `s3:*`, `lambda:*` instead of listing individual actions
- ✅ **Compressed JSON**: Removed all unnecessary whitespace in the minified version
- ✅ **Consolidated Resources**: Combined similar ARN patterns
- ✅ **Shorter IAM Actions**: Used `iam:*RolePolicy` and `iam:List*Policies` wildcards

#### Step 2: Add All Inline Policies to User

For each policy above, follow these steps:

1. Go to AWS IAM Console
2. Navigate to Users → `province`
3. Click "Add permissions" → "Add inline policy"
4. Click "JSON" tab
5. Paste one of the policies from Step 1
6. Click "Review policy"
7. Give it the name shown (e.g., "AILegalOS-DynamoDB")
8. Click "Create policy"
9. **Repeat for all 7 policies**

**Priority Order** (add these first for basic functionality):
1. ✅ **AILegalOS-DynamoDB** (Required for template saving)
2. ✅ **AILegalOS-S3** (Required for document storage)
3. **AILegalOS-CloudFormation** (For CDK deployment)
4. **AILegalOS-IAM** (For CDK deployment)
5. **AILegalOS-Lambda** (For API deployment)
6. **AILegalOS-APIGateway** (For API deployment)
7. **AILegalOS-Logs** (For monitoring)

### Option 2: Create Dedicated Service User (Recommended for Production)

#### Step 1: Create New IAM User

```bash
aws iam create-user --user-name ai-legal-os-service
```

#### Step 2: Create and Attach Policy

```bash
# Create the policy (save JSON above as policy.json)
aws iam create-policy \
    --policy-name AILegalOSFullAccess \
    --policy-document file://policy.json

# Attach to user
aws iam attach-user-policy \
    --user-name ai-legal-os-service \
    --policy-arn arn:aws:iam::[REDACTED-ACCOUNT-ID]:policy/AILegalOSFullAccess
```

#### Step 3: Create Access Keys

```bash
aws iam create-access-key --user-name ai-legal-os-service
```

## 🚀 Manual Infrastructure Setup (Alternative to CDK)

If CDK deployment continues to have permission issues, you can create the infrastructure manually:

### Step 1: Create DynamoDB Tables

```bash
# Templates table
aws dynamodb create-table \
    --table-name province-templates \
    --attribute-definitions \
        AttributeName=template_id,AttributeType=S \
        AttributeName=name,AttributeType=S \
        AttributeName=version,AttributeType=S \
        AttributeName=is_active,AttributeType=S \
        AttributeName=usage_count,AttributeType=N \
    --key-schema \
        AttributeName=template_id,KeyType=HASH \
    --global-secondary-indexes \
        IndexName=NameIndex,KeySchema=[{AttributeName=name,KeyType=HASH},{AttributeName=version,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
        IndexName=ActiveIndex,KeySchema=[{AttributeName=is_active,KeyType=HASH},{AttributeName=usage_count,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-2

# Matters table
aws dynamodb create-table \
    --table-name province-matters \
    --attribute-definitions \
        AttributeName=tenant_id_matter_id,AttributeType=S \
        AttributeName=created_by,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
    --key-schema \
        AttributeName=tenant_id_matter_id,KeyType=HASH \
    --global-secondary-indexes \
        IndexName=UserIndex,KeySchema=[{AttributeName=created_by,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-2

# Documents table
aws dynamodb create-table \
    --table-name province-documents \
    --attribute-definitions \
        AttributeName=matter_id_path,AttributeType=S \
        AttributeName=document_id,AttributeType=S \
        AttributeName=matter_id,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
    --key-schema \
        AttributeName=matter_id_path,KeyType=HASH \
    --global-secondary-indexes \
        IndexName=DocumentIdIndex,KeySchema=[{AttributeName=document_id,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
        IndexName=MatterIndex,KeySchema=[{AttributeName=matter_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-2
```

### Step 2: Create S3 Buckets

```bash
# Documents bucket
aws s3 mb s3://province-documents-[REDACTED-ACCOUNT-ID]-us-east-2 --region us-east-2

# Templates bucket  
aws s3 mb s3://province-templates-[REDACTED-ACCOUNT-ID]-us-east-2 --region us-east-2

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket province-documents-[REDACTED-ACCOUNT-ID]-us-east-2 \
    --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
    --bucket province-templates-[REDACTED-ACCOUNT-ID]-us-east-2 \
    --versioning-configuration Status=Enabled
```

### Step 3: Update Environment Variables

Update your `.env.local` file:

```bash
# Add the new bucket names
DOCUMENTS_BUCKET_NAME=province-documents-[REDACTED-ACCOUNT-ID]-us-east-2
TEMPLATES_BUCKET_NAME=province-templates-[REDACTED-ACCOUNT-ID]-us-east-2

# Add table names
MATTERS_TABLE_NAME=province-matters
DOCUMENTS_TABLE_NAME=province-documents
TEMPLATES_TABLE_NAME=province-templates
PERMISSIONS_TABLE_NAME=province-permissions
DEADLINES_TABLE_NAME=province-deadlines
```

## 🧪 Test the Setup

After setting up permissions and infrastructure, run the test:

```bash
cd backend
source venv/bin/activate
python test_real_api_functionality.py
```

You should see:
```
✅ Template generation successful!
✅ Template saved to DynamoDB!
✅ Matter creation successful!
✅ Documents stored in S3!
```

## 🔒 Security Best Practices

1. **Principle of Least Privilege**: Only grant permissions needed for the application
2. **Resource-Specific ARNs**: Use specific resource ARNs instead of wildcards
3. **Environment Separation**: Use different IAM users/roles for dev/staging/prod
4. **Access Key Rotation**: Regularly rotate access keys
5. **CloudTrail Logging**: Enable CloudTrail to monitor API calls

## ⚡ Quick Start (5 Minutes)

If you just want to get template saving working immediately:

1. **Add DynamoDB Inline Policy**:
   - Go to IAM Console → Users → `province`
   - Click "Add permissions" → "Add inline policy" 
   - Use JSON editor, paste **AILegalOS-DynamoDB** policy from above
   - Name it "AILegalOS-DynamoDB"

2. **Create Templates Table**:
   ```bash
   aws dynamodb create-table \
       --table-name province-templates \
       --attribute-definitions AttributeName=template_id,AttributeType=S \
       --key-schema AttributeName=template_id,KeyType=HASH \
       --billing-mode PAY_PER_REQUEST \
       --region us-east-2
   ```

3. **Test It**:
   ```bash
   cd backend
   python test_real_api_functionality.py
   ```

You should now see: `✅ Template saved to DynamoDB!`

## 🔄 Add More Policies as Needed

- **For S3 document storage**: Add "AILegalOS-S3" policy
- **For CDK deployment**: Add "AILegalOS-CloudFormation" + "AILegalOS-IAM" policies  
- **For Lambda API**: Add "AILegalOS-Lambda" + "AILegalOS-APIGateway" + "AILegalOS-Logs" policies

## 🚨 Troubleshooting

### Policy Character Limit Issues:

- **Inline Policy Limit**: 2048 characters max
- **Solution**: Use managed policies for complex permissions
- **Quick Fix**: Use the minimal policy above for basic functionality

### Common Issues:

1. **"Policy exceeds character limit"**: Use managed policy instead of inline
2. **"Table already exists"**: Check with `aws dynamodb list-tables --region us-east-2`
3. **"Access Denied"**: Wait 5 minutes for IAM propagation
4. **"Region mismatch"**: Ensure all resources are in `us-east-2`

### Debug Commands:

```bash
# Check current permissions
aws sts get-caller-identity

# List DynamoDB tables
aws dynamodb list-tables --region us-east-2

# Test DynamoDB access
aws dynamodb describe-table --table-name province-templates --region us-east-2

# Test template creation
aws dynamodb put-item \
    --table-name province-templates \
    --item '{"template_id":{"S":"test-123"},"name":{"S":"Test Template"}}' \
    --region us-east-2
```

## 📞 Next Steps

1. **Choose Option 1 or 2** above based on your needs
2. **Set up the IAM permissions**
3. **Create the infrastructure** (manually or via CDK)
4. **Update environment variables**
5. **Run the test suite** to verify everything works
6. **Proceed to Step 3** of the implementation plan

Once this is set up, the AI Legal OS will be able to:
- ✅ Generate templates with AI
- ✅ Save templates to DynamoDB
- ✅ Create and manage matters
- ✅ Store documents in S3
- ✅ Full CRUD operations on all entities

The system will then be ready for production deployment with proper AWS infrastructure!