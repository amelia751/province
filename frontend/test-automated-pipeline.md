# 🧪 Automated Document Processing Pipeline - Test Script

## Overview
This script tests the complete automated document processing pipeline from frontend to backend, including S3 uploads, Lambda processing, and chat integration.

## Prerequisites
- ✅ Backend server running on port 8000
- ✅ Frontend server running on port 3000
- ✅ Lambda function deployed (`ProvinceDocumentProcessor`)
- ✅ S3 bucket configured with event notifications
- ✅ DynamoDB tables created

## Test Scenarios

### 🎯 Test 1: Basic Pipeline Verification

**Objective**: Verify the complete automated pipeline works end-to-end

**Steps**:
1. **Navigate to the app**: Go to `http://localhost:3000/app`
2. **Create a new engagement**: Click "Start Filing" to create a new tax engagement
3. **Open the Debug Tab**: Click on "🐛 Debug Info" tab in the main editor
4. **Copy initial state**: Click "📋 Copy Debug Info" and paste the result below:

```
[PASTE DEBUG INFO HERE - Initial State]
```

5. **Test backend connection**: Click "Test Backend" button
6. **Test notifications**: Click "Test Notifications" button  
7. **Test simulation**: Click "Simulate Processing" button

**Expected Results**:
- Backend health check should return 200 OK
- Notifications should return mock data with W-2 processing results
- Simulation should return structured W-2 data with wages and withholding

---

### 🎯 Test 2: Document Upload and Processing

**Objective**: Test real document upload through the chat interface

**Steps**:
1. **Navigate to chat**: Go to the chat interface in your tax engagement
2. **Upload a document**: 
   - Drag and drop a PDF/image file into the chat input area
   - OR use the document upload button
3. **Send the message**: Press Enter to upload the document
4. **Monitor processing**: Watch for:
   - Upload confirmation
   - S3 storage confirmation
   - Lambda function trigger (check AWS CloudWatch logs)
   - Processing notifications

**Expected Results**:
- Document should upload to S3 under `tax-engagements/{engagement_id}/chat-uploads/`
- Lambda function should be triggered automatically
- Processing notifications should appear in the chat

**Debug Info After Upload**:
```
[PASTE DEBUG INFO HERE - After Document Upload]
```

---

### 🎯 Test 3: Chat Integration with Processed Documents

**Objective**: Verify the agent can access and discuss processed documents

**Steps**:
1. **Start a conversation**: In the chat, type:
   ```
   "I just uploaded a W-2 document. Can you tell me about the wages and withholding information?"
   ```

2. **Provide details**: When the agent asks, respond with:
   ```
   "My name is [Your Name] and this is for tax year 2024."
   ```

3. **Monitor the conversation**: Check if the agent can:
   - Acknowledge the document upload
   - Access the processed document data
   - Provide specific information about wages and withholding

**Expected Results**:
- Agent should recognize the document upload
- Agent should be able to discuss specific W-2 information
- No "document not found" errors

**Debug Info After Chat**:
```
[PASTE DEBUG INFO HERE - After Chat Interaction]
```

---

### 🎯 Test 4: Document Management

**Objective**: Test document listing and deletion functionality

**Steps**:
1. **Open Documents Tab**: Click on "📄 My Documents" tab
2. **Refresh documents**: Click "Refresh" button
3. **Verify document listing**: Check that uploaded documents appear
4. **Test individual delete**: Click "Delete" on one document
5. **Test bulk delete**: Click "Delete All" (if you have multiple documents)

**Expected Results**:
- Documents should be listed with correct metadata
- Individual delete should remove the document from both S3 and DynamoDB
- Bulk delete should remove all user documents

**Debug Info After Document Management**:
```
[PASTE DEBUG INFO HERE - After Document Management]
```

---

### 🎯 Test 5: Error Scenarios

**Objective**: Test error handling and recovery

**Steps**:
1. **Test unsupported file**: Try uploading a .txt file
2. **Test large file**: Try uploading a file > 10MB
3. **Test network issues**: Disconnect internet briefly during upload
4. **Test backend offline**: Stop the backend server and try operations

**Expected Results**:
- Unsupported files should be rejected with clear error messages
- Large files should be handled gracefully
- Network issues should show appropriate error messages
- Backend offline should show connection errors

**Debug Info After Error Testing**:
```
[PASTE DEBUG INFO HERE - After Error Testing]
```

---

## 🔍 Monitoring and Debugging

### AWS CloudWatch Logs
Monitor the Lambda function logs:
```bash
aws logs tail /aws/lambda/ProvinceDocumentProcessor --follow --region us-east-1
```

### Backend Logs
Check the backend server logs:
```bash
tail -f /Users/anhlam/province/backend/server.log
```

### S3 Bucket Contents
Verify documents are uploaded:
```bash
aws s3 ls s3://province-documents-<account-id>-<region>/tax-engagements/ --recursive --region us-east-1
```

### DynamoDB Tables
Check document metadata:
```bash
aws dynamodb scan --table-name province-tax-documents --region us-east-1
aws dynamodb scan --table-name province-document-notifications --region us-east-1
```

---

## 📊 Test Results Template

### Test Summary
- **Date**: [DATE]
- **Tester**: [YOUR NAME]
- **Environment**: Development
- **Backend Version**: [VERSION]
- **Frontend Version**: [VERSION]

### Results
| Test | Status | Notes |
|------|--------|-------|
| Basic Pipeline | ✅/❌ | |
| Document Upload | ✅/❌ | |
| Chat Integration | ✅/❌ | |
| Document Management | ✅/❌ | |
| Error Handling | ✅/❌ | |

### Issues Found
1. **Issue**: [Description]
   - **Severity**: High/Medium/Low
   - **Steps to Reproduce**: [Steps]
   - **Expected**: [Expected behavior]
   - **Actual**: [Actual behavior]
   - **Debug Info**: [Paste debug info]

### Performance Metrics
- **Document Upload Time**: [TIME]
- **Lambda Processing Time**: [TIME]
- **Chat Response Time**: [TIME]
- **Document List Load Time**: [TIME]

---

## 🚨 Common Issues and Solutions

### Issue: "Backend connection failed"
**Solution**: 
1. Check if backend server is running on port 8000
2. Verify CORS configuration
3. Check firewall settings

### Issue: "Document upload failed"
**Solution**:
1. Check S3 permissions
2. Verify bucket exists and is accessible
3. Check file size limits

### Issue: "Lambda function not triggered"
**Solution**:
1. Verify S3 event notifications are configured
2. Check Lambda function permissions
3. Verify S3 key prefix matches trigger configuration

### Issue: "Agent can't access document data"
**Solution**:
1. Check if document was processed successfully
2. Verify DynamoDB permissions
3. Check engagement ID mapping

---

## 📝 Notes
- Always run tests in a clean environment
- Clear browser cache between test runs
- Monitor AWS costs during testing
- Keep debug info for troubleshooting
- Test with different file types and sizes
- Verify cleanup after tests

---

## 🎯 Success Criteria
The automated document processing pipeline is considered successful when:

1. ✅ Documents upload successfully to S3
2. ✅ Lambda function processes documents automatically
3. ✅ Structured data is extracted from documents
4. ✅ Notifications are generated and displayed
5. ✅ Chat agent can access and discuss document data
6. ✅ Document management (list/delete) works correctly
7. ✅ Error handling is robust and user-friendly
8. ✅ Performance is acceptable (< 30s for processing)

---

**Happy Testing! 🚀**
