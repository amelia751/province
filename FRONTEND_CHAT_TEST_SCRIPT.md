# Frontend Chat Test Script

**Backend Status**: ✅ Running on http://localhost:8000  
**File Structure Service**: ✅ Healthy  
**Dev Data Manager**: ✅ Available in main-editor tab

Copy and paste these messages **one at a time** into the frontend chat interface to test the file structure system.

---

## 🎯 Test Conversation Script

### Message 1: Introduction & Setup
```
Hi! I'm John Smith and I need help with my 2024 tax return. I'm filing as Single with no dependents. Can you help me get started?
```
**Expected**: Agent should greet you and offer to create an engagement

---

### Message 2: Create Engagement  
```
Yes, please create a new engagement for my 2024 individual tax return.
```
**Expected**: Agent should create engagement and confirm success

---

### Message 3: Update Profile Details
```
Let me give you my complete details: Full name is John Smith, filing status Single, tax year 2024, no dependents, email john.smith@example.com, timezone America/New_York.
```
**Expected**: Agent should update your intake profile

---

### Message 4: Apply Template
```
Can you set up the standard folder structure for my 1040 return using a template?
```
**Expected**: Agent should apply template and create initial folders

---

### Message 5: Check Structure
```
Show me what folders and files we have created so far.
```
**Expected**: Agent should list the current file tree structure

---

### Message 6: Create Custom Folder
```
I need to organize my bank statements. Please create a folder called "Bank Statements" under the Documents folder.
```
**Expected**: Agent should create the folder and confirm

---

### Message 7: Create Nested Folder
```
Also create a folder for receipts at "Documents/Receipts/2024/Q1" - I want to organize by quarter.
```
**Expected**: Agent should create nested folder structure

---

### Message 8: Create Document
```
Create a notes file at "/Workpapers/tax_planning_notes.md" with some initial planning notes about my tax situation.
```
**Expected**: Agent should create document with content

---

### Message 9: Create JSON Document
```
Create a checklist file at "/Intake/document_checklist.json" with a list of documents I need to gather.
```
**Expected**: Agent should create JSON file

---

### Message 10: List Updated Structure
```
Show me the complete file structure now with all the folders and files we've created.
```
**Expected**: Agent should show expanded file tree

---

### Message 11: Get Upload URL
```
I have a W2 document to upload. Can you give me a signed URL to upload it to "/Documents/W2/company_w2_2024.pdf"?
```
**Expected**: Agent should provide signed URL for upload

---

### Message 12: Create More Documents
```
Create a summary document at "/Documents/Bank Statements/account_summary.md" with placeholder content for my bank account information.
```
**Expected**: Agent should create document in the custom folder

---

### Message 13: Final Structure Check
```
Perfect! Show me the final complete folder structure with all files, folders, and their sizes.
```
**Expected**: Agent should show comprehensive file tree with metadata

---

### Message 14: Test Cleanup (Optional)
```
This looks great! For testing purposes, can you clean up all my test data so I can try this again?
```
**Expected**: Agent should offer to clean up test data

---

## 📊 What to Monitor During Testing

### 1. **Dev Data Manager Tab**
- Switch to the "Dev Data Manager" tab in main-editor
- Click "Refresh" after each message
- You should see:
  - Engagements count increasing
  - Documents count increasing  
  - S3 objects appearing
  - Total size growing

### 2. **Backend Logs Tab**
- Check the "Backend Logs" tab
- Look for:
  - File structure operations
  - DynamoDB operations
  - S3 operations
  - Success/error messages

### 3. **Network Tab (Browser DevTools)**
- Open browser DevTools → Network tab
- Watch for API calls to:
  - `/api/v1/file-structure/*`
  - `/api/agents/chat`
  - Backend WebSocket connections

---

## 🔧 Troubleshooting

### If Agent Doesn't Respond:
1. Check Backend Logs tab for errors
2. Verify backend server is running: http://localhost:8000/docs
3. Check browser console for JavaScript errors

### If File Operations Fail:
1. Check AWS credentials in backend/.env.local
2. Verify DynamoDB tables exist
3. Check S3 bucket permissions

### If Dev Data Manager Shows No Data:
1. Click "Refresh" button
2. Check if Clerk authentication is working
3. Verify API endpoints are accessible

---

## 🎉 Success Indicators

✅ **Agent responds naturally to each message**  
✅ **File structure operations complete successfully**  
✅ **Dev Data Manager shows increasing data counts**  
✅ **Backend logs show successful operations**  
✅ **No error messages in browser console**  
✅ **Signed URLs are generated for uploads**  
✅ **File tree grows with each operation**

---

## 🚀 Advanced Testing (After Basic Script)

Once the basic script works, try these advanced scenarios:

```
Move the tax_planning_notes.md file from Workpapers to Documents/Planning
```

```
Rename the "Bank Statements" folder to "Banking Documents"
```

```
Delete the Q1 folder and then restore it from trash
```

```
Create a complex nested structure: Documents/Tax Year 2024/Federal/Forms/1040
```

---

**Ready to test!** 🎯

1. Make sure backend is running (✅ confirmed above)
2. Open frontend in browser
3. Go to chat interface  
4. Start with Message 1 and work through sequentially
5. Monitor the Dev Data Manager tab between messages
6. Check Backend Logs for any issues

The system should create a complete file structure in real-time as you chat!
