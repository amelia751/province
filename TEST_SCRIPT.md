# Frontend Tax Filing Test Script

**Test Date**: October 21, 2025

## Quick Reference - Test Data

| Field | Value |
|-------|-------|
| **Filing Status** | Single |
| **Dependents** | 2 (Alice Smith, Bob Smith) |
| **Alice SSN** | 123-45-6789 |
| **Bob SSN** | 987-65-4321 |
| **Digital Assets** | No |
| **Bank Routing Number** | 123456789 |
| **Bank Account Number** | 987654321 |
| **Account Type** | Checking |

---

## Prerequisites

1. **Backend Running**: Port 8000
2. **Frontend Running**: Port 3000
3. **Logged In**: Clerk authentication
4. **W-2 Document**: `W2_XL_input_clean_1000.pdf` in Downloads folder
5. **Clean State**: Reset forms using "Reset Forms (1040)" button if needed

---

## Test Flow

### STEP 1: Upload W-2 Document

**Action**: Drag and drop or upload `W2_XL_input_clean_1000.pdf` to the chat

**Expected Result**:
- ✅ Upload progress indicator appears
- ✅ Document appears in Documents Management tab
- ✅ Agent responds: "I've received your W-2 document..."

**Wait Time**: ~30-60 seconds for Bedrock processing

---

### STEP 2: Agent Processes W-2

**You Say**: 
```
Please process my W-2 document
```

**Expected Agent Response**:
```
I've successfully processed your W-2 document from [Employer Name]. 
Here's what I extracted:
- Wages: $55,151.93
- Federal tax withheld: $16,606.17
- Employee: [Your Name]
- SSN: 077-49-4905
- Address: 31403 David Circles Suite 863, West Erinfort, WY 45881-3334

What is your filing status for 2024? (Single, Married filing jointly, etc.)
```

**Debug Check**:
- Open Debug Info tab
- Verify `w2_processed: true` in CHAT_STATE
- Verify document appears in STORAGE section

---

### STEP 3: Filing Status

**You Say**: 
```
I am single
```

**Expected Agent Response**:
```
Great! I've noted that you're filing as Single. 
Do you have any dependents you'd like to claim?
```

**Watch For**:
- ✅ Form 1040 tab should show v001 PDF loading (auto-refresh)
- ✅ "Single" checkbox should be ticked in the PDF
- ✅ NO other filing status boxes should be checked

**Debug Check**:
- Filing status should show in conversation state
- Form 1040 v001 should appear in S3

---

### STEP 4: Dependents - First Child

**You Say**: 
```
I have 2 dependents. My first dependent is my daughter Alice Smith with SSN 123-45-6789
```

**Expected Agent Response**:
```
Thank you. I've added Alice to your return. 
Can you provide the information for your second dependent?
```

**Watch For**:
- ✅ Form 1040 updates to v002
- ✅ Alice's name appears in dependent table
- ✅ Child tax credit checkbox ticked for Alice

---

### STEP 5: Dependents - Second Child

**You Say**: 
```
My second dependent is my son Bob Smith with SSN 987-65-4321
```

**Expected Agent Response**:
```
Perfect! I've added Bob to your return as well. 
At any time during 2024, did you receive, sell, exchange, or dispose of any digital assets?
```

**Watch For**:
- ✅ Form 1040 updates to v003
- ✅ Both Alice and Bob appear in dependent table
- ✅ Child tax credit checked for both

---

### STEP 6: Digital Assets

**You Say**: 
```
No, I don't have any digital assets
```

**Expected Agent Response**:
```
Thank you. Can anyone claim you as a dependent on their tax return?
```

**Watch For**:
- ✅ Form 1040 updates to v004
- ✅ Digital Assets "No" checkbox is checked
- ✅ Digital Assets "Yes" checkbox is NOT checked

---

### STEP 7: Standard Deduction

**You Say**: 
```
No one can claim me as a dependent
```

**Expected Agent Response**:
```
Great! Now, for your refund - would you like to receive it via direct deposit?
If so, I'll need your routing number and account number.
```

**Watch For**:
- ✅ Form 1040 updates to v005
- ✅ Standard deduction checkboxes remain unchecked (correct for this case)

---

### STEP 8: Banking Information (Direct Deposit)

**You Say**: 
```
For my refund, use routing number 123456789, account number 987654321, checking account
```

**Alternative Phrasing** (any of these should work):
```
I'd like direct deposit. My routing number is 123456789 and account number is 987654321. It's a checking account.
```
```
Please deposit my refund to my checking account. Routing: 123456789, Account: 987654321
```

**Expected Agent Response**:
```
Perfect! I've saved your direct deposit information for your refund:
- Routing Number: 123456789
- Account Number: 987654321
- Account Type: Checking

Your Form 1040 is now complete with all the information. 
Would you like me to show you the final version?
```

**Watch For**:
- ✅ Form 1040 updates to v006
- ✅ **Routing number** filled: `123456789` (9 digits)
- ✅ **Account number** filled: `987654321` (can be 4-17 digits)
- ✅ **Checking account** checkbox is checked (Line 35c)
- ✅ **Savings account** checkbox is NOT checked
- ✅ Refund amount appears on Line 35a

**Important Notes**:
- Routing numbers are always 9 digits
- Account numbers vary by bank (typically 8-12 digits)
- Only one account type (checking OR savings) should be selected

---

### STEP 9: Request Final Form

**You Say**: 
```
Please fill out my Form 1040 and show me the completed form
```

**Expected Agent Response**:
```
Great! I've successfully filled out your Form 1040. This is version [7-8].

You can view your completed Form 1040 at:
[S3 URL]

Here's a summary:
1. Filing Status: Single ✓
2. Your name and SSN from W-2 ✓
3. Address from W-2 ✓
4. 2 dependents (Alice and Bob) ✓
5. Wages: $55,151.93 ✓
6. Federal withholding: $16,606.17 ✓
7. Calculated refund: $15,971.94 ✓
8. Direct deposit: Routing 123456789, Account 987654321 (Checking) ✓
```

**Watch For**:
- ✅ Form 1040 updates to v007 or v008
- ✅ PDF viewer automatically reloads to show latest version
- ✅ All fields are properly filled (see detailed verification below)

