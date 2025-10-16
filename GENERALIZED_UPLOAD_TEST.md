# Generalized Document Upload Test Script

The agent now has a generalized `request_document_upload` tool that can handle any document type. Here's how to test it:

## 🎯 Test Messages

Copy and paste these messages **one at a time** into the frontend chat:

### Message 1: Initial Setup
```
Hi! I'm John Smith and I need help with my 2024 tax return. I'm filing as Single with no dependents.
```
**Expected**: Agent should greet you and ask about your tax situation

---

### Message 2: Request W-2 Processing
```
Yes, I have my W-2 form ready. Can you help me process it?
```
**Expected**: Agent should use `request_document_upload` tool for W-2 documents

---

### Message 3: Request 1099 Processing  
```
I also have a 1099-INT form from my bank. Can you help me upload that too?
```
**Expected**: Agent should use `request_document_upload` tool for 1099 documents

---

### Message 4: Request Receipt Upload
```
I have some business expense receipts I need to upload. Where should I put them?
```
**Expected**: Agent should use `request_document_upload` tool for receipts

---

## 🔧 Expected Tool Calls

The agent should call `request_document_upload` with different parameters:

### For W-2:
```json
{
  "document_type": "w2",
  "folder_path": "/Documents/W2", 
  "description": "W-2 form from your employer"
}
```

### For 1099:
```json
{
  "document_type": "1099",
  "folder_path": "/Documents/1099",
  "description": "1099 form"
}
```

### For Receipts:
```json
{
  "document_type": "receipt", 
  "folder_path": "/Documents/Receipts",
  "description": "receipt or expense document"
}
```

---

## 🎨 Frontend Behavior

When the agent calls the tool, the frontend should:

1. **Parse the agent response** for `action: "request_document_upload"`
2. **Open upload dialog** with the correct document type and folder
3. **Show appropriate messaging** based on the description
4. **Handle file validation** for the document type
5. **Upload to correct S3 path** when user selects files

---

## 🚀 Current Status

- ✅ **Backend**: Generalized `request_document_upload` tool created
- ✅ **Agent Instructions**: Updated to use the generalized tool
- ✅ **Tool Testing**: Confirmed tool works for W-2, 1099, receipts
- ✅ **Frontend Integration**: Upload dialog and agent actions hook ready
- ⏳ **Tool Deployment**: Tool needs to be deployed to Bedrock Lambda function

---

## 🔧 Next Steps

1. **Test in Frontend**: Try the messages above in your chat interface
2. **Check Agent Response**: Look for the `request_document_upload` action in responses
3. **Verify Upload Dialog**: Confirm dialog opens with correct document type
4. **Test File Upload**: Upload test files and verify they go to correct S3 paths

---

**The generalized approach is much better!** 🎉 

Now the agent can handle any document type with a single, flexible tool instead of having separate tools for each document type.
