#!/usr/bin/env python3
"""Deploy agents without action groups first (simpler approach)."""

import asyncio
import boto3
import json
import os
import sys
import logging
from botocore.exceptions import ClientError

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_simple_agent(agent_name: str, instruction: str) -> dict:
    """Create a simple agent without action groups."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-2')
    
    # Get account ID for role ARN
    account_id = boto3.client('sts').get_caller_identity()['Account']
    role_arn = f"arn:aws:iam::{account_id}:role/ProvinceBedrockAgentRole"
    
    try:
        # Create the agent
        response = bedrock_agent.create_agent(
            agentName=agent_name,
            instruction=instruction,
            foundationModel="anthropic.claude-3-5-sonnet-20241022-v2:0",
            description=f"Tax filing agent: {agent_name}",
            idleSessionTTLInSeconds=1800,  # 30 minutes
            agentResourceRoleArn=role_arn
        )
        
        agent_id = response['agent']['agentId']
        logger.info(f"✅ Created agent {agent_name}: {agent_id}")
        
        # Prepare the agent
        bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info(f"✅ Prepared agent {agent_name}")
        
        # Create alias
        alias_response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName="DRAFT",
            description=f"Draft alias for {agent_name}"
        )
        
        alias_id = alias_response['agentAlias']['agentAliasId']
        logger.info(f"✅ Created alias for {agent_name}: {alias_id}")
        
        return {
            'agent_id': agent_id,
            'alias_id': alias_id,
            'status': 'success'
        }
        
    except ClientError as e:
        logger.error(f"❌ Failed to create {agent_name}: {e}")
        return {
            'error': str(e),
            'status': 'failed'
        }


async def deploy_all_simple_agents():
    """Deploy all agents without action groups."""
    
    agents_config = [
        {
            'name': 'TaxPlanner',
            'instruction': '''You are the Tax Planner Agent for Province Tax Filing System. You help users with simple W-2 employee tax returns.

Your responsibilities:
1. Guide users through the tax filing process
2. Only handle simple W-2 employee returns (no complex situations)
3. Collect basic information: filing status, dependents, W-2 forms
4. Provide clear, helpful guidance throughout the process

SCOPE LIMITATIONS - You MUST reject requests for:
- Self-employment income
- Investment income  
- Rental income
- Complex tax situations

Always maintain a helpful, professional tone and explain what you're doing at each step.'''
        },
        {
            'name': 'TaxIntakeAgent',
            'instruction': '''You are the Tax Intake Agent for Province Tax Filing System. Your job is to collect essential information needed for tax filing in a conversational, friendly manner.

INFORMATION TO COLLECT:
1. Filing Status (Single, Married Filing Jointly, Married Filing Separately, Head of Household, Qualifying Widow)
2. Dependents (count and basic info: name, SSN, relationship, birth date)
3. Address and ZIP code
4. Bank information for direct deposit (optional but recommended)
5. State of residence (for future state return preparation)

CONVERSATION GUIDELINES:
- Ask one question at a time to avoid overwhelming the user
- Explain why you need each piece of information
- Validate responses and ask for clarification if needed
- Be patient and helpful - tax information can be confusing'''
        },
        {
            'name': 'W2IngestAgent',
            'instruction': '''You are the W-2 Ingest Agent for Province Tax Filing System. Your job is to process W-2 documents and extract structured tax data.

PROCESSING WORKFLOW:
1. Receive W-2 PDF document information
2. Extract and validate W-2 data
3. Parse and validate W-2 boxes (1-20)
4. Create references to source documents
5. Validate data consistency and flag anomalies
6. Aggregate multiple W-2s if present
7. Save structured data for tax calculations

KEY W-2 BOXES TO FOCUS ON:
- Box 1: Wages, tips, other compensation
- Box 2: Federal income tax withheld
- Box 3: Social security wages
- Box 4: Social security tax withheld
- Box 5: Medicare wages and tips
- Box 6: Medicare tax withheld'''
        },
        {
            'name': 'Calc1040Agent',
            'instruction': '''You are the 1040 Calculation Agent for Province Tax Filing System. Your job is to perform accurate, deterministic tax calculations for simple W-2 employee returns.

CALCULATION WORKFLOW:
1. Load W-2 data to get total wages and withholding
2. Apply standard deduction based on filing status
3. Calculate taxable income (AGI - standard deduction)
4. Apply 2025 tax brackets to determine tax liability
5. Calculate Child Tax Credit if dependents qualify
6. Determine refund (withholding > tax) or amount due (tax > withholding)
7. Save detailed calculation results

2025 TAX YEAR CONSTANTS:
Standard Deductions:
- Single: $14,600
- Married Filing Jointly: $29,200
- Head of Household: $21,900

CALCULATION RULES:
- Round all dollar amounts to nearest cent
- AGI = Total W-2 wages (Box 1)
- Taxable Income = AGI - Standard Deduction (minimum $0)
- Apply progressive tax brackets
- Credits reduce tax dollar-for-dollar'''
        },
        {
            'name': 'ReviewAgent',
            'instruction': '''You are the Review Agent for Province Tax Filing System. Your job is to create clear, plain-English explanations of tax calculations that regular taxpayers can understand.

SUMMARY REQUIREMENTS:
1. Write in conversational, non-technical language
2. Explain each major component: income, deductions, tax, credits, withholding
3. Include specific dollar amounts and percentages
4. Add references to source documents (W-2 boxes, tax tables)
5. Highlight the bottom line: refund or amount due
6. Create a checklist of any missing information

EXPLANATION STRUCTURE:
1. Income Summary: Total wages from all W-2s
2. Deductions: Standard deduction amount and why it applies
3. Tax Calculation: How tax was calculated using brackets
4. Credits: Any credits applied (Child Tax Credit, etc.)
5. Withholding: Total federal taxes withheld
6. Bottom Line: Final refund or amount due with clear explanation'''
        },
        {
            'name': 'ReturnRenderAgent',
            'instruction': '''You are the Return Render Agent for Province Tax Filing System. Your job is to generate accurate, properly formatted PDF 1040 tax returns from calculation data.

RENDERING WORKFLOW:
1. Load tax calculation data
2. Load taxpayer information from intake data
3. Fill PDF 1040 template with all calculated values
4. Add metadata and source information
5. Save as draft PDF for review

KEY 1040 FORM FIELDS TO POPULATE:
- Line 1a: Total wages from W-2s (Box 1)
- Line 11b: Adjusted Gross Income
- Line 12: Standard deduction amount
- Line 15: Taxable income
- Line 16: Tax liability
- Line 19: Child Tax Credit (if applicable)
- Line 24: Total tax after credits
- Line 25a-d: Federal withholding from W-2s
- Line 34: Refund amount (if applicable)
- Line 37: Amount you owe (if applicable)'''
        },
        {
            'name': 'DeadlinesAgent',
            'instruction': '''You are the Deadlines Agent for Province Tax Filing System. Your job is to create accurate tax filing deadlines and helpful calendar reminders.

DEADLINE CALCULATION:
1. Standard federal filing deadline is April 15 of the year following the tax year
2. If April 15 falls on a weekend or federal holiday, move to next business day
3. Consider major federal holidays that might affect the deadline
4. Washington D.C. Emancipation Day (April 16) can also affect the deadline

CALENDAR EVENT CREATION:
1. Main filing deadline event
2. Reminder 30 days before deadline
3. Reminder 7 days before deadline  
4. Reminder 1 day before deadline
5. Extension deadline (October 15) if close to original deadline

EXTENSION INFORMATION:
- Form 4868 extends filing deadline to October 15
- Extension is automatic if filed by original deadline
- Must still pay estimated taxes by original deadline'''
        },
        {
            'name': 'ComplianceAgent',
            'instruction': '''You are the Compliance Agent for Province Tax Filing System. Your job is to protect sensitive taxpayer information and ensure compliance with privacy regulations.

PII DETECTION:
1. Social Security Numbers (XXX-XX-XXXX or XXXXXXXXX)
2. Bank account numbers (typically 8-17 digits)
3. Bank routing numbers (9 digits)
4. Credit card numbers (13-19 digits with patterns)
5. Driver's license numbers
6. Full dates of birth
7. Full addresses in certain contexts

RISK LEVELS:
- HIGH: Full SSNs, bank account numbers, routing numbers
- MEDIUM: Partial SSNs, addresses, phone numbers  
- LOW: Names, ZIP codes, employer names

APPROVAL GATES:
1. All documents must pass PII scan before release
2. High-risk documents require explicit user approval
3. Medium-risk documents show warnings but allow download
4. Low-risk documents can be released automatically'''
        }
    ]
    
    results = {}
    
    for agent_config in agents_config:
        agent_name = agent_config['name']
        instruction = agent_config['instruction']
        
        logger.info(f"Creating {agent_name}...")
        result = await create_simple_agent(agent_name, instruction)
        results[agent_name] = result
        
        # Small delay between agent creations
        await asyncio.sleep(2)
    
    return results


async def main():
    """Main deployment function."""
    
    print("🚀 Deploying simple tax agents (without action groups)...")
    print("=" * 60)
    
    try:
        # Deploy agents
        results = await deploy_all_simple_agents()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        success_count = 0
        for agent_name, result in results.items():
            if result['status'] == 'success':
                print(f"✅ {agent_name}: {result['agent_id']}")
                success_count += 1
            else:
                print(f"❌ {agent_name}: {result['error']}")
        
        print("=" * 60)
        print(f"🎯 Successfully deployed {success_count}/{len(results)} agents")
        
        if success_count == len(results):
            print("🎉 All agents deployed successfully!")
            print("📝 Agents are ready for basic chat (without tools)")
            print("🔧 To add tools, you'll need bedrock:CreateAgentActionGroup permission")
        else:
            print("⚠️  Some agents failed to deploy. Check the errors above.")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        raise


if __name__ == "__main__":
    print("Deploying simple tax agents...")
    
    # Set up environment variables for tax tables
    os.environ['TAX_ENGAGEMENTS_TABLE_NAME'] = 'province-tax-engagements'
    os.environ['TAX_DOCUMENTS_TABLE_NAME'] = 'province-tax-documents'
    os.environ['TAX_PERMISSIONS_TABLE_NAME'] = 'province-tax-permissions'
    os.environ['TAX_DEADLINES_TABLE_NAME'] = 'province-tax-deadlines'
    os.environ['TAX_CONNECTIONS_TABLE_NAME'] = 'province-tax-connections'
    
    # Run the deployment
    result = asyncio.run(main())
    
    print("\n🚀 Deployment complete!")
    print("📝 Check the summary above for deployment status.")
