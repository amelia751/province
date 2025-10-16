# File Structure System Test Conversation Script

Copy and paste these messages one by one into the frontend chat to test the file structure system in real-time.

## Test Script - Copy Each Message Below:

### 1. Initial Setup
```
Hi! I need help setting up my 2024 tax return. My name is John Smith and I'm filing as Single.
```

### 2. Create Engagement
```
Please create a new engagement for my 2024 individual tax return.
```

### 3. Update Profile
```
Let me give you my details: John Smith, filing Single for 2024, no dependents, email john.smith@example.com, timezone America/New_York.
```

### 4. Apply Template
```
Can you set up the standard folder structure for my 1040 return?
```

### 5. Check Current Structure
```
Show me what folders and files we have so far.
```

### 6. Create Custom Folders
```
Create a folder called "Bank Statements" under Documents.
```

### 7. Create Another Folder
```
Also create a folder called "Receipts/2024" under Documents.
```

### 8. Write a Document
```
Create a notes file at /Workpapers/tax_notes.md with some initial planning notes.
```

### 9. Write Another Document
```
Create a checklist file at /Intake/checklist.json with my tax document requirements.
```

### 10. List Updated Structure
```
Show me the complete file structure now.
```

### 11. Create Nested Folder
```
Create a folder called "Q1" under Documents/Receipts/2024.
```

### 12. Write Document in Nested Folder
```
Create a receipt summary at /Documents/Receipts/2024/Q1/summary.md.
```

### 13. Get Signed URL
```
Can you give me a signed URL to upload a W2 document to /Documents/W2/w2_2024.pdf?
```

### 14. Final Structure Check
```
Show me the final complete folder structure with all files and folders.
```

### 15. Test Cleanup (Optional - for development)
```
Clean up all my test data so I can start fresh.
```

---

## Expected Behavior:

- The agent should create an engagement and folder structure
- Each folder creation should be confirmed
- Document creation should show success messages
- The file tree should grow with each operation
- You should see real-time updates in the Dev Data Manager tab
- The backend logs should show all operations

## How to Use:

1. Make sure the backend is running (should be started automatically)
2. Open the frontend in your browser
3. Go to the chat interface
4. Copy and paste each message above, one at a time
5. Wait for the agent's response before sending the next message
6. Check the "Dev Data Manager" tab to see your data in real-time
7. Check the "Backend Logs" tab to see system activity

## Troubleshooting:

- If the agent doesn't respond, check the Backend Logs tab
- If you see connection errors, make sure the backend server is running
- If you want to start over, use the cleanup message (#15)
- Check the Dev Data Manager tab to see if data is being created

## Advanced Testing:

After the basic script, you can try:
- Moving files between folders
- Renaming files and folders  
- Deleting and restoring files
- Creating more complex folder structures
- Uploading actual documents via signed URLs

---

**Note**: This script tests the core file structure functionality. The agent should respond naturally and perform the requested operations while maintaining the conversation flow.
