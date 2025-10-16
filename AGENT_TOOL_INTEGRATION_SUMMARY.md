# Agent Tool Integration Summary & Next Steps

## 🎯 **Current Issue**
The Bedrock agent is NOT using the `recent_uploads` and `ingest_documents` tools despite being deployed. The throttling errors have been resolved, but the agent still asks users to upload files instead of checking for existing uploads.

## ✅ **What's Been Completed**

### 1. **Tool Naming Fixed**
- ✅ Renamed `check_recent_uploads` → `recent_uploads`
- ✅ Renamed `ingest_w2` → `ingest_documents`
- ✅ Updated all imports and references

### 2. **Agent Instructions Updated**
- ✅ Updated Bedrock agent instructions to mention `recent_uploads` and `ingest_documents`
- ✅ Agent prepared and deployed with new instructions

### 3. **Lambda Function Deployed**
- ✅ Updated `province-tax-filing-tools` Lambda function with new tools
- ✅ Fixed import errors (time module)
- ✅ Lambda function deploys successfully

### 4. **Action Groups Updated**
- ✅ Updated Bedrock action groups to point to new Lambda function
- ✅ Agent prepared with updated action groups

### 5. **Upload System Working**
- ✅ Drag-and-drop frontend upload works
- ✅ Files upload to S3 successfully
- ✅ Simple upload endpoint caches upload info

## ❌ **Critical Issues Remaining**

### 1. **Agent Not Using Tools**
**Problem**: Agent responds with "Please drag and drop your W-2" instead of using `recent_uploads` tool
**Evidence**: Even when explicitly asked to "use recent_uploads tool", agent ignores the request

### 2. **Mock Data in Lambda** 🚨
**Problem**: Lambda `recent_uploads` function returns hardcoded mock data instead of real upload info
**Code Location**: `/backend/scripts/deploy_updated_tax_tools.py` lines 130-139
```python
# BAD: Mock data instead of real data
mock_uploads = [
    {
        "s3_key": "test_uploads/Documents/W2/my_w2_2024.pdf",
        # ... hardcoded mock data
    }
]
```

### 3. **No Real Integration**
**Problem**: Lambda can't access the backend's upload cache (localhost:8000 not reachable from AWS)
**Need**: Direct S3/DynamoDB integration for real upload data

## 🔧 **Required Fixes**

### **PRIORITY 1: Fix Mock Data Issue**
Replace mock data in Lambda with real S3/DynamoDB queries:
```python
# Instead of mock data, query S3 for recent uploads
s3_client = boto3.client('s3')
bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'
prefix = 'test_uploads/'
# List objects with recent timestamps
```

### **PRIORITY 2: Debug Agent Tool Usage**
The agent has the tools but won't use them. Possible causes:
1. **Tool Schema Issues**: OpenAPI schema might be malformed
2. **Action Group Mapping**: Tools not properly mapped to action groups
3. **Agent Instructions**: Need more explicit trigger conditions
4. **Bedrock Caching**: Agent might be using cached old version

### **PRIORITY 3: Real Upload Integration**
Connect the frontend upload system with the Lambda tools:
1. Store upload metadata in DynamoDB (not just memory cache)
2. Lambda queries DynamoDB for recent uploads
3. Agent can access real upload data

## 📋 **Immediate Action Plan**

### **Step 1: Fix Mock Data (URGENT)**
- Replace hardcoded mock data in Lambda `recent_uploads` function
- Query S3 directly for files uploaded in last hour
- Return real S3 keys and metadata

### **Step 2: Debug Agent Behavior**
- Check Bedrock action group schemas
- Verify tool mappings are correct
- Test individual tools via Lambda console
- Check CloudWatch logs for tool invocation attempts

### **Step 3: Test End-to-End Flow**
1. Upload file via frontend drag-and-drop
2. Agent uses `recent_uploads` to find it
3. Agent uses `ingest_documents` to process it
4. Agent continues with tax filing workflow

## 🗂️ **Key Files**

### **Backend**
- `/backend/scripts/deploy_updated_tax_tools.py` - Lambda function (FIX MOCK DATA)
- `/backend/src/province/agents/agent_service.py` - Agent configuration
- `/backend/src/province/api/v1/simple_upload.py` - Upload endpoint

### **Frontend**
- `/frontend/src/components/chat/chat.tsx` - Drag-and-drop upload

### **AWS Resources**
- **Agent**: `YLNFZM0YEM` (TaxPlannerAgent)
- **Lambda**: `province-tax-filing-tools`
- **S3 Bucket**: `province-documents-[REDACTED-ACCOUNT-ID]-us-east-1`

## 🎯 **Success Criteria**

1. **Agent uses `recent_uploads`** when user mentions uploading files
2. **Real S3 data returned** (not mock data)
3. **Agent processes uploaded W-2** using `ingest_documents` with real S3 key
4. **No more throttling errors**
5. **Complete tax filing workflow** works end-to-end

## 🚨 **Request for New AI Session**

**Please fix the mock data issue first** - the Lambda function should query real S3 data, not return hardcoded mock uploads. Then debug why the Bedrock agent won't use the `recent_uploads` tool even when explicitly requested.

The upload system works, the tools are deployed, but the agent behavior and real data integration are broken.
