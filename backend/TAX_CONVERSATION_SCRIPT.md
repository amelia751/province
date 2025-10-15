# Tax Filing Conversation Script

This script provides realistic user messages you can copy-paste to test the tax filing agent in the frontend. Each message represents what a typical user would say during the tax filing process.

## 🎯 **Complete Tax Filing Flow**

### **Step 1: Start the Conversation**
```
Hi, I need help filing my taxes for 2024. Can you walk me through the process?
```

### **Step 2: Filing Status**
```
I'm single and filing by myself this year.
```

### **Step 3: Dependents**
```
No, I don't have any dependents to claim.
```

### **Step 4: Income Information**
```
I made $75,000 in wages this year and had $11,200 in federal taxes withheld from my paychecks.
```

### **Step 5: Request Tax Calculation**
```
Can you calculate my taxes based on this information?
```

### **Step 6: Fill Out Form**
```
Great! Please fill out my 1040 form with all this information.
```

### **Step 7: Check Version History**
```
Can you show me the version history for my tax form?
```

### **Step 8: Update Information (Creates New Version)**
```
Actually, I need to update my information. My wages were actually $78,000 and my withholding was $12,000.
```

### **Step 9: Fill Form Again (New Version)**
```
Please update my 1040 form with the corrected information.
```

### **Step 10: Final Version History**
```
Show me the updated version history to see all the changes.
```

### **Step 11: Save Document**
```
Perfect! Please save this final version to my documents.
```

---

## 🔄 **Alternative Scenarios**

### **Scenario A: Married Filing Jointly**
```
I'm married and we're filing jointly. My spouse and I together made $95,000 in wages with $14,500 in federal withholding.
```

### **Scenario B: With Dependents**
```
I'm single but I have 2 dependent children I'd like to claim on my taxes.
```

### **Scenario C: Multiple Income Updates**
```
Wait, let me correct that again. Our total wages were actually $98,500 and withholding was $15,200.
```

### **Scenario D: Request Specific Information**
```
What's my estimated refund amount based on these numbers?
```

### **Scenario E: Form Details**
```
Can you explain what information is filled out on my 1040 form?
```

---

## 🧪 **Testing Different Features**

### **Version Management Testing**
```
How many versions of my tax form do I have?
```

```
Can you show me the differences between version 1 and the current version?
```

### **State Management Testing**
```
What information do you have stored about my tax situation?
```

```
Can you remind me what my filing status is?
```

### **Error Handling Testing**
```
I think I made a mistake with my income. Can we start over with the form?
```

```
What happens if I need to change my filing status from single to married?
```

---

## 💡 **Quick Test Messages**

### **Fast Complete Flow (Copy All at Once)**
If you want to test the entire flow quickly, copy these messages one by one:

1. `Hi, I need help with my 2024 taxes.`
2. `I'm single.`
3. `No dependents.`
4. `I made $65,000 with $9,500 withheld.`
5. `Please calculate my taxes.`
6. `Fill out my 1040 form.`
7. `Show version history.`
8. `Update: wages were $70,000 and withholding was $10,000.`
9. `Fill the form again with updated info.`
10. `Show final version history.`
11. `Save the document.`

### **Edge Case Testing**
```
What if I have no income to report?
```

```
I need to file but I'm not sure about my filing status.
```

```
Can you help me if I only have W-2 income?
```

```
What forms do you support besides 1040?
```

---

## 🎨 **Natural Conversation Variations**

### **More Casual/Natural Responses**
```
Hey, can you help me with taxes?
```

```
I'm not married, so I guess single?
```

```
Nope, no kids or anything like that.
```

```
I think I made around 75k this year, and they took out like 11 grand in taxes.
```

```
Sounds good, let's do the calculation.
```

```
Yeah, go ahead and fill out the form for me.
```

```
Actually wait, I need to fix something. The numbers were different.
```

```
OK cool, update it with the new numbers.
```

```
Perfect, let's save this thing.
```

### **More Formal/Detailed Responses**
```
Good afternoon. I would like assistance with preparing my 2024 federal income tax return.
```

```
My filing status is single. I am not married and do not qualify for head of household.
```

```
I do not have any qualifying dependents to claim on my tax return.
```

```
According to my W-2 form, my total wages for 2024 were $75,000, and my employer withheld $11,200 in federal income taxes.
```

```
Please proceed with calculating my tax liability based on the information provided.
```

```
I would like you to complete Form 1040 using all the information we have discussed.
```

```
Could you please provide the version history for my tax document?
```

```
I need to make a correction to my previously reported income and withholding amounts.
```

```
Please update the form with the corrected financial information.
```

```
I would like to review the complete version history to ensure accuracy.
```

```
Please finalize and save this completed tax return to my document repository.
```

---

## 🔍 **Debugging/Development Messages**

### **System State Queries**
```
What's the current state of our conversation?
```

```
Show me all the tools you have available.
```

```
What version of my form are we currently working on?
```

### **Technical Testing**
```
Can you process a W-2 document if I upload one?
```

```
What happens if the form filling fails?
```

```
How do you handle version conflicts?
```

---

## 📝 **Expected Agent Responses**

The agent should respond with:
- ✅ Conversational acknowledgments
- ✅ Tool usage notifications (e.g., "Tool #1: manage_state_tool")
- ✅ Tax calculations with breakdowns
- ✅ Version information (e.g., "Version v1 created")
- ✅ Form filling confirmations with field counts
- ✅ Version history with timestamps and file sizes
- ✅ Download URLs for completed forms
- ✅ Next step suggestions

## 🚨 **What to Watch For**

### **Success Indicators:**
- Agent uses tools (you'll see "Tool #X: tool_name")
- Forms show "Successfully filled X form widgets"
- Version numbers increment (v1 → v2 → v3)
- File sizes change when content is updated
- Download URLs are provided
- Conversation state is maintained

### **Potential Issues:**
- "ModuleNotFoundError" - backend not running properly
- "0 form widgets filled" - form filling not working
- No version information - versioning system issue
- Agent doesn't use tools - Strands SDK integration problem

---

## 🎯 **Pro Tips for Testing**

1. **Start Simple**: Use the "Fast Complete Flow" first
2. **Test Variations**: Try different income amounts and filing statuses
3. **Check Versions**: Always verify version numbers increment
4. **Verify Forms**: Download and check that PDFs are actually filled
5. **Test Edge Cases**: Try the error scenarios to ensure robustness
6. **Monitor Logs**: Watch the backend logs for detailed debugging info

---

*This script covers the complete tax filing workflow with versioning. Copy and paste these messages to thoroughly test your frontend integration with the tax filing agent!* 🎉
