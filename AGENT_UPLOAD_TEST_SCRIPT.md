# Agent Document Upload Test Script

This script tests the new document upload functionality where the agent can trigger file upload dialogs in the frontend.

## 🎯 Test Conversation

Copy and paste these messages **one at a time** into the frontend chat to test the document upload flow:

### Message 1: Initial Setup
```
Hi! I'm John Smith and I need help with my 2024 tax return. I'm filing as Single with no dependents.
```
**Expected**: Agent should greet you and ask about your tax situation

---

### Message 2: Request W-2 Processing
```
Yes, I have my W-2 form ready. Can you help me process it for my tax return?
```
**Expected**: Agent should use the `request_document_upload` tool and trigger the upload dialog

---

### Message 3: If Upload Dialog Appears
- **Upload a test PDF or image file** (W-2 document)
- **Or click "Cancel" or "Skip for now"** to test the fallback flow

**Expected**: 
- If uploaded: File should be saved to S3 in `/Documents/W2/` folder
- If cancelled: Agent should mention the W2 folder for later upload

---

### Message 4: Test Fallback Message
```
I couldn't upload the file right now. Where can I upload it later?
```
**Expected**: Agent should mention the `/Documents/W2` folder location

---

### Message 5: Test Different Document Type
```
I also have a 1099 form. Can you help me upload that too?
```
**Expected**: Agent should trigger upload dialog for 1099 documents

---

## 🔧 What to Monitor

### 1. **Frontend Behavior**
- ✅ Upload dialog appears when agent requests document
- ✅ Dialog shows correct document type and folder path
- ✅ File validation works (format, size limits)
- ✅ Upload progress is shown
- ✅ Success/error states are handled
- ✅ Cancel/skip functionality works

### 2. **Backend Logs**
Watch for:
```
Document upload requested: w2 for user [user_id]
Document upload request created successfully for w2
```

### 3. **File Storage**
- Check S3 bucket: `province-documents-[REDACTED-ACCOUNT-ID]-us-east-1`
- Look for files in: `matters/[engagement_id]/Documents/W2/`
- Verify file metadata in DynamoDB

### 4. **Dev Data Manager Tab**
- Refresh after upload
- Should show increased document count
- Should show S3 objects

---

## 🎨 Expected UI Flow

1. **Agent Message**: "Please upload your W-2 form..."
2. **Upload Dialog Opens**: 
   - Title: "Upload W-2 form from your employer"
   - Accepted formats: PDF, JPG, JPEG, PNG
   - Max size: 10MB
   - Drag & drop area
3. **File Selection**: User drags file or clicks to browse
4. **Upload Progress**: Progress bar and status indicators
5. **Success**: Dialog closes, agent confirms receipt
6. **Fallback**: If cancelled, agent mentions folder location

---

## 🐛 Troubleshooting

### Upload Dialog Doesn't Appear
- Check browser console for JavaScript errors
- Verify `useAgentActions` hook is working
- Check if agent response contains `action: "request_document_upload"`

### Upload Fails
- Check backend logs for S3/DynamoDB errors
- Verify AWS credentials and permissions
- Check file size and format restrictions

### Agent Doesn't Use Tool
- Verify tool is deployed to Lambda
- Check Bedrock action group includes `request_document_upload`
- Review agent instructions for tool usage

---

## 🚀 Advanced Testing

After basic functionality works, test these scenarios:

### Multiple Files
```
I have multiple W-2 forms from different employers. Can you help me upload them all?
```

### Invalid File Types
- Try uploading .txt or .docx files
- Should show validation error

### Large Files
- Try uploading files > 10MB
- Should show size limit error

### Session Recovery
- Start upload, close browser, return
- Agent should mention folder location for manual upload

### Different Document Types
```
I need to upload my 1099-INT, 1099-DIV, and some receipts. Can you help?
```

---

## ✅ Success Criteria

- ✅ Agent triggers upload dialog when requesting documents
- ✅ Upload dialog shows correct document type and path
- ✅ Files upload successfully to correct S3 location
- ✅ File metadata is stored in DynamoDB
- ✅ Cancel/skip flow provides helpful fallback message
- ✅ Multiple document types work (W-2, 1099, receipts)
- ✅ File validation prevents invalid uploads
- ✅ Error handling is graceful and informative

---

**Ready to test!** 🎯

The backend should be running with the new `request_document_upload` tool. Start with Message 1 and work through the flow to see the upload dialog in action!
