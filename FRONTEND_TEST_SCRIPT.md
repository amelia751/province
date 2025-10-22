# Frontend Tax Filing Test Script

**Test Date**: October 21, 2025  
**User ID**: `user_33w9KAn1gw3xXSa6MnBsySAQIIm`  
**Engagement ID**: `ea3b3a4f-c877-4d29-bd66-2cff2aa77476`

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
3. **Logged In**: Clerk authentication (user_33w9KAn1gw3xXSa6MnBsySAQIIm)
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

---

## Detailed Form Verification Checklist

### Page 1 - Top Section
- [ ] **Name**: April Hensley (or name from your W-2)
- [ ] **SSN**: 077494905 (no dashes, 9 digits)
- [ ] **Address**: 31403 David Circles Suite 863
- [ ] **City/State/ZIP**: West Erinfort, WY 45881-3334

### Filing Status (Page 1, Top)
- [ ] **Single**: ✅ CHECKED
- [ ] **Married filing jointly**: ❌ NOT CHECKED
- [ ] **Married filing separately**: ❌ NOT CHECKED
- [ ] **Head of household**: ❌ NOT CHECKED
- [ ] **Qualifying surviving spouse**: ❌ NOT CHECKED

### Digital Assets (Page 1, Below Filing Status)
- [ ] **At any time during 2024...**
  - [ ] **Yes**: ❌ NOT CHECKED
  - [ ] **No**: ✅ CHECKED

### Dependents Section (Page 1, Middle)
- [ ] **Dependent 1**:
  - Name: Alice Smith
  - SSN: 123456789
  - Relationship: daughter
  - Child tax credit: ✅ CHECKED
  - Other credit: ❌ NOT CHECKED
- [ ] **Dependent 2**:
  - Name: Bob Smith
  - SSN: 987654321
  - Relationship: son
  - Child tax credit: ✅ CHECKED
  - Other credit: ❌ NOT CHECKED

### Income Section (Page 1, Bottom)
- [ ] **Line 1a (Wages)**: $55,151.93
- [ ] **Line 9 (Total income)**: $55,151.93
- [ ] **Line 11 (Adjusted Gross Income)**: $55,151.93

### Standard Deduction (Page 1, Bottom)
- [ ] **Line 12 (Standard deduction)**: $14,600.00 (2024 single)
- [ ] **Checkboxes**: All unchecked (correct - no one claims you)

### Tax and Credits (Page 2, Top)
- [ ] **Line 15 (Taxable income)**: $40,551.93
- [ ] **Line 16 (Tax)**: $4,634.23
- [ ] **Child tax credit**: Calculated based on 2 children

### Payments (Page 2, Middle)
- [ ] **Line 25a (Federal withholding)**: $16,606.17

### Refund Section (Page 2, Bottom) - DIRECT DEPOSIT DETAILS
- [ ] **Line 34 (Overpayment/Refund)**: $15,971.94
- [ ] **Line 35a (Amount to be refunded)**: $15,971.94
- [ ] **Line 35b (Routing number)**: `021000021` (9 digits, no dashes)
- [ ] **Line 35c (Account type)**: 
  - Checking: ✅ CHECKED
  - Savings: ❌ NOT CHECKED
- [ ] **Line 35d (Account number)**: `987654321` (no dashes or special characters)

**💡 Important**: The routing number field should show all 9 digits clearly. The account number should be clearly legible.

---

## Auto-Reload Test

**Purpose**: Verify the form auto-reloads when new versions are created

**Test Steps**:
1. Click "Reset Forms (1040)" button
2. Wait for confirmation
3. Start conversation again from STEP 2
4. **Watch the Form 1040 tab carefully**
5. You should see the PDF viewer automatically reload every time the agent fills a new version

**Expected Behavior**:
- Console logs: `🔄 New form version detected!`
- PDF viewer should smoothly transition to new version
- Version counter should update (v001 → v002 → v003...)
- NO page flickering or reloading unless there's a new version

**If Reloading Too Often**:
- Check browser console for logs
- Should only reload when version count increases
- Should NOT reload every 5 seconds if no new version

---

## Troubleshooting

### W-2 Processing Fails
**Symptom**: Agent says "There was an issue processing the W2 document"  
**Fix**: 
1. Check Bedrock role permissions in AWS Console
2. See `BEDROCK_W2_PROCESSING_FIX.md`
3. Wait 60 seconds and try again

### Form Not Auto-Loading
**Symptom**: Form 1040 tab shows "No Form 1040 Available"  
**Fix**:
1. Check Debug Info tab → USER_ID (should be your Clerk ID)
2. Click manual refresh button (↻)
3. Check console for API errors

### Wrong Checkbox Checked
**Symptom**: "Married filing jointly" checked instead of "Single"  
**Fix**:
1. Copy Debug Info (full text)
2. Share with developer
3. Check DynamoDB mapping for filing status fields

### Form Reloads Every 5 Seconds
**Symptom**: PDF keeps reloading even when idle  
**Fix**:
1. Check browser console for logs
2. Should see "No changes detected" message
3. If still reloading, check `form-1040-viewer.tsx` for stale closure

### Banking Info Not Filled
**Symptom**: Routing/account numbers missing  
**Fix**:
1. Check if you said "checking" or "savings"
2. Agent needs explicit account type
3. Retry with full sentence

---

## Success Criteria

✅ **W-2 Processing**: Name, SSN, address extracted correctly  
✅ **Filing Status**: "Single" checkbox checked, all others unchecked  
✅ **Dependents**: Both children listed with correct SSNs  
✅ **Digital Assets**: "No" checkbox checked  
✅ **Income**: Wages, withholding, refund calculated correctly  
✅ **Banking**: Routing number, account number, checking box filled  
✅ **Auto-Reload**: Form updates automatically as agent fills it  
✅ **Version History**: Can navigate between versions (v001 → v008)

---

## Debug Info Copy Template

**If anything goes wrong, copy this from Debug Info tab:**

```
USER_ID: [copy here]
ENGAGEMENT_ID: [copy here]
FORM_STATUS: [copy here]
CHAT_STATE: [copy full JSON here]
RECENT_API_CALLS: [copy last 5-10 calls]
ERRORS: [copy any errors]
```

**Then share with developer for investigation.**

---

## Expected Timeline

| Step | Time | Cumulative |
|------|------|------------|
| Upload W-2 | 5s | 5s |
| Bedrock Processing | 30-60s | 35-65s |
| Filing Status | 10s | 45-75s |
| Dependents (2) | 20s | 65-95s |
| Digital Assets | 10s | 75-105s |
| Standard Deduction | 10s | 85-115s |
| Banking Info | 10s | 95-125s |
| Final Form Fill | 15s | 110-140s |
| **Total** | **~2-3 minutes** | |

---

## Notes

- **Auto-Refresh**: Form checks for new versions every 5 seconds
- **Polling**: Bedrock waits up to 3 minutes for processing
- **Version Numbers**: May not be sequential if you're retesting
- **Cache Busting**: Each PDF has unique URL to prevent browser caching
- **PII Safety**: All forms saved under Clerk user ID, not name

---

## End of Test

**If all checkboxes pass**, your system is working perfectly! 🎉

**If any fail**, use the Debug Info template above to investigate.
