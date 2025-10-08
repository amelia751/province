# Tax System Deployment Guide

This guide provides step-by-step CLI instructions for deploying the complete tax filing system with AWS Bedrock agents and action groups.

## 🏗️ **System Architecture**

The tax system consists of:
- **8 Bedrock Agents** with Claude 3.5 Sonnet
- **1 Lambda Function** with 7 tax filing tools
- **2 IAM Roles** (Agent execution + Lambda execution)
- **5 DynamoDB Tables** for tax data storage
- **Comprehensive Action Groups** with full parameter specifications

## 📋 **Prerequisites**

### 1. Environment Setup
```bash
# Navigate to backend directory
cd /Users/anhlam/province/backend

# Activate Python virtual environment
source venv/bin/activate

# Set Bedrock credentials for agent deployment
export BEDROCK_AWS_ACCESS_KEY_ID=your_bedrock_access_key_here
export BEDROCK_AWS_SECRET_ACCESS_KEY=your_bedrock_secret_key_here
```

### 2. Required AWS Permissions

**For `province` user (DynamoDB tables):**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
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
                "arn:aws:dynamodb:us-east-2:YOUR_ACCOUNT_ID:table/province-*",
                "arn:aws:iam::YOUR_ACCOUNT_ID:role/Province*",
                "arn:aws:lambda:us-east-2:YOUR_ACCOUNT_ID:function:province-*",
                "arn:aws:s3:::province-*/*"
            ]
        }
    ]
}
```

**For `BedrockAPIKey-5rpi` user (Bedrock agents):**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:CreateAgent",
                "bedrock:CreateAgentAlias",
                "bedrock:CreateAgentActionGroup",
                "bedrock:UpdateAgentActionGroup",
                "bedrock:DeleteAgentActionGroup",
                "bedrock:ListAgentActionGroups",
                "bedrock:GetAgentActionGroup",
                "bedrock:PrepareAgent",
                "bedrock:ListAgents",
                "bedrock:GetAgent",
                "bedrock:UpdateAgent",
                "iam:CreateRole",
                "iam:PutRolePolicy",
                "iam:GetRole",
                "iam:PassRole",
                "lambda:CreateFunction",
                "lambda:InvokeFunction",
                "lambda:GetFunction",
                "lambda:AddPermission"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🚀 **Complete Deployment Process**

### Step 1: Create DynamoDB Tables
```bash
# Create all tax-specific DynamoDB tables
python scripts/create_tax_tables.py

# Create connections table with TTL (if needed separately)
python scripts/create_connections_table.py
```

**Expected Output:**
```
✅ Created table: province-tax-engagements
✅ Created table: province-tax-documents  
✅ Created table: province-tax-permissions
✅ Created table: province-tax-deadlines
✅ Created table: province-tax-connections
```

### Step 2: Deploy Complete Tax System
```bash
# Deploy IAM roles, Lambda function, and all Bedrock agents
# Set your credentials first:
export BEDROCK_AWS_ACCESS_KEY_ID=your_bedrock_access_key_here
export BEDROCK_AWS_SECRET_ACCESS_KEY=your_bedrock_secret_key_here

python scripts/deploy_complete_tax_system.py
```

**Expected Output:**
```
🏗️  DEPLOYING COMPLETE TAX SYSTEM
✅ Created IAM role: ProvinceBedrockAgentRole
✅ Created IAM role: ProvinceTaxFilingLambdaRole  
✅ Created Lambda function: province-tax-filing-tools
✅ Created agent: TaxPlannerAgent (AGENT_ID)
✅ Created agent: TaxIntakeAgent (AGENT_ID)
✅ Created agent: W2IngestAgent (AGENT_ID)
✅ Created agent: Calc1040Agent (AGENT_ID)
✅ Created agent: ReviewAgent (AGENT_ID)
✅ Created agent: ReturnRenderAgent (AGENT_ID)
✅ Created agent: DeadlinesAgent (AGENT_ID)
✅ Created agent: ComplianceAgent (AGENT_ID)
🎉 ALL AGENTS DEPLOYED SUCCESSFULLY!
```

### Step 3: Create Comprehensive Action Groups
```bash
# Create comprehensive action groups directly (recommended approach)
python scripts/create_comprehensive_action_groups_direct.py
```

### Step 4: Update Agents to Use Inference Profile
```bash
# Update all agents to use the correct inference profile for Claude 3.5 Sonnet
python scripts/update_agent_models.py
```

### Step 5: Verify Deployment
```bash
# Check final status of all agents
python scripts/quick_agent_status.py
```

**Expected Output:**
```
🔍 Checking agent status...
TaxPlannerAgent: PREPARED ✅ DRAFT alias already exists
TaxIntakeAgent: PREPARED ✅ DRAFT alias already exists
W2IngestAgent: PREPARED ✅ DRAFT alias already exists
Calc1040Agent: PREPARED ✅ DRAFT alias already exists
ReviewAgent: PREPARED ✅ DRAFT alias already exists
ReturnRenderAgent: PREPARED ✅ DRAFT alias already exists
DeadlinesAgent: PREPARED ✅ DRAFT alias already exists
ComplianceAgent: PREPARED ✅ DRAFT alias already exists
✅ Status check complete!
```

## 🛠️ **Individual Component Deployment**

### Deploy Only IAM Roles and Lambda
```bash
python scripts/create_roles_only.py
```

### Deploy Only Bedrock Agents
```bash
python scripts/deploy_agents_only.py
```

### Check Bedrock Permissions
```bash
python scripts/check_bedrock_permissions.py
```

## 📊 **Deployed Components**

### Bedrock Agents
| Agent | Purpose | Status |
|-------|---------|--------|
| TaxPlannerAgent | Router/orchestrator | ✅ Ready |
| TaxIntakeAgent | Collect filing info | ✅ Ready |
| W2IngestAgent | Process W-2 PDFs | ✅ Ready |
| Calc1040Agent | Tax calculations | ✅ Ready |
| ReviewAgent | Generate summaries | ✅ Ready |
| ReturnRenderAgent | Create PDF returns | ✅ Ready |
| DeadlinesAgent | Calendar reminders | ✅ Ready |
| ComplianceAgent | PII scanning | ✅ Ready |

### Lambda Tools
| Tool | Purpose | Parameters |
|------|---------|------------|
| `save_document` | Save to S3 | `engagement_id, path, content_b64, mime` |
| `get_signed_url` | Upload/download URLs | `engagement_id, path, mode, mime?` |
| `ingest_w2_pdf` | OCR W-2 processing | `s3_key, taxpayer_name, tax_year` |
| `calc_1040` | Tax calculations | `engagement_id, filing_status, dependents_count` |
| `render_1040_draft` | Generate PDF | `engagement_id` |
| `create_deadline` | Calendar events | `engagement_id, title, due_at_iso, reminders[]` |
| `pii_scan` | Security scanning | `s3_key` |

### DynamoDB Tables
- `province-tax-engagements` - Tax filing cases
- `province-tax-documents` - Document metadata  
- `province-tax-permissions` - Access control
- `province-tax-deadlines` - Filing deadlines
- `province-tax-connections` - User sessions

## 🔧 **Troubleshooting**

### Common Issues

**1. Agent Creation Fails**
```bash
# Check Bedrock permissions
python scripts/check_bedrock_permissions.py
```

**2. Action Group Creation Fails**
- Ensure Lambda function exists: `province-tax-filing-tools`
- Verify IAM role exists: `ProvinceBedrockAgentRole`
- Check function schema format (use function definitions, not OpenAPI)

**3. Agents in FAILED Status**
This typically occurs when agents have conflicting action groups. **Solution:**
```bash
# Clean deployment - delete and recreate agents with comprehensive action groups
python scripts/redeploy_agents_clean.py
```

**4. Agent Not Prepared**
```bash
# Manually prepare agents
python scripts/finalize_agents.py
```

**5. Model Configuration Issues**
If you get "model ID with on-demand throughput isn't supported" errors:
```bash
# Update agents to use inference profile
python scripts/update_agent_models.py
```

**6. DynamoDB Table Creation Fails**
- Check `province` user has DynamoDB permissions
- Verify table names don't already exist
- Ensure region is `us-east-2`

### Verification Commands

**Check agent status:**
```bash
aws bedrock-agent list-agents --region us-east-2
```

**Check action groups:**
```bash
aws bedrock-agent list-agent-action-groups --agent-id AGENT_ID --agent-version DRAFT --region us-east-2
```

**Check Lambda function:**
```bash
aws lambda get-function --function-name province-tax-filing-tools --region us-east-2
```

**Check DynamoDB tables:**
```bash
aws dynamodb list-tables --region us-east-2 | grep province-tax
```

## 🎯 **Success Criteria**

✅ **Deployment Complete When:**
- All 8 agents show `PREPARED` status
- All agents have `TSTALIASID` aliases working
- All agents have `ComprehensiveTaxTools` action groups
- Lambda function `province-tax-filing-tools` exists
- All 5 DynamoDB tables exist
- All agents use inference profile ARN for Claude 3.5 Sonnet
- Chat functionality works without model configuration errors

## 🚀 **Next Steps**

After successful deployment:
1. **Integrate with frontend** using agent IDs
2. **Test tax filing workflow** with sample W-2s
3. **Configure S3 bucket** `province-documents-storage`
4. **Set up monitoring** for Lambda and DynamoDB
5. **Test end-to-end** tax return generation

## 📋 **Quick Reference Commands**

### Complete Fresh Deployment
```bash
cd /Users/anhlam/province/backend
source venv/bin/activate
export BEDROCK_AWS_ACCESS_KEY_ID=your_bedrock_access_key_here
export BEDROCK_AWS_SECRET_ACCESS_KEY=your_bedrock_secret_key_here

# Run deployment steps in order
python scripts/create_tax_tables.py
python scripts/deploy_complete_tax_system.py
python scripts/create_comprehensive_action_groups_direct.py
python scripts/update_agent_models.py
python scripts/quick_agent_status.py
```

### Verify Deployment
```bash
python scripts/verify_deployment.py
```

### Check Agent Status
```bash
python scripts/quick_agent_status.py
```

## 🎯 **Current System Status**

As of the latest deployment:
- ✅ **DynamoDB Tables**: 5 tables created and active
- ✅ **IAM Roles**: ProvinceBedrockAgentRole and ProvinceTaxFilingLambdaRole created
- ✅ **Lambda Function**: province-tax-filing-tools deployed with 7 tools
- ✅ **Bedrock Agents**: 8 agents created with comprehensive action groups
- ✅ **Model Configuration**: All agents updated to use inference profile ARN
- ✅ **Agent Status**: All agents PREPARED and working
- ✅ **Chat Integration**: Frontend successfully connected to TaxPlannerAgent

**System is fully operational and ready for tax filing!**

---

**📝 Note:** Always run commands from `/Users/anhlam/province/backend` with the virtual environment activated and proper AWS credentials set. Never commit actual AWS credentials to version control.