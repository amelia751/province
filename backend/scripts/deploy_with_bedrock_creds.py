#!/usr/bin/env python3
"""Deploy agents using Bedrock-specific credentials."""

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


def get_bedrock_clients():
    """Get Bedrock clients using the Bedrock-specific credentials."""
    
    # Use Bedrock-specific credentials
    bedrock_access_key = os.getenv("BEDROCK_AWS_ACCESS_KEY_ID")
    bedrock_secret_key = os.getenv("BEDROCK_AWS_SECRET_ACCESS_KEY")
    
    if not bedrock_access_key or not bedrock_secret_key:
        raise ValueError("Bedrock credentials not found in environment")
    
    logger.info(f"Using Bedrock credentials: {bedrock_access_key[:10]}...")
    
    # Create Bedrock clients with specific credentials
    bedrock_agent = boto3.client(
        'bedrock-agent',
        region_name='us-east-2',
        aws_access_key_id=bedrock_access_key,
        aws_secret_access_key=bedrock_secret_key
    )
    
    # Also create STS client to get account ID
    sts_client = boto3.client(
        'sts',
        region_name='us-east-2',
        aws_access_key_id=bedrock_access_key,
        aws_secret_access_key=bedrock_secret_key
    )
    
    return bedrock_agent, sts_client


async def create_or_update_agent(bedrock_agent, sts_client, agent_name: str, instruction: str) -> dict:
    """Create or update an agent using Bedrock credentials."""
    
    try:
        # Get account ID for role ARN
        account_id = sts_client.get_caller_identity()['Account']
        role_arn = f"arn:aws:iam::{account_id}:role/ProvinceBedrockAgentRole"
        
        # First, try to list existing agents to see if it already exists
        try:
            agents_response = bedrock_agent.list_agents()
            existing_agent = None
            
            for agent in agents_response.get('agentSummaries', []):
                if agent['agentName'] == agent_name:
                    existing_agent = agent
                    break
            
            if existing_agent:
                agent_id = existing_agent['agentId']
                logger.info(f"✅ Found existing agent {agent_name}: {agent_id}")
                
                # Try to prepare the agent if it's not ready
                try:
                    bedrock_agent.prepare_agent(agentId=agent_id)
                    logger.info(f"✅ Prepared existing agent {agent_name}")
                except ClientError as e:
                    if "already prepared" in str(e).lower():
                        logger.info(f"✅ Agent {agent_name} already prepared")
                    else:
                        logger.warning(f"Could not prepare agent {agent_name}: {e}")
                
                # Try to create alias if it doesn't exist
                try:
                    alias_response = bedrock_agent.create_agent_alias(
                        agentId=agent_id,
                        agentAliasName="DRAFT",
                        description=f"Draft alias for {agent_name}"
                    )
                    alias_id = alias_response['agentAlias']['agentAliasId']
                    logger.info(f"✅ Created alias for {agent_name}: {alias_id}")
                except ClientError as e:
                    if "already exists" in str(e).lower():
                        # Get existing alias
                        aliases_response = bedrock_agent.list_agent_aliases(agentId=agent_id)
                        for alias in aliases_response.get('agentAliasSummaries', []):
                            if alias['agentAliasName'] == 'DRAFT':
                                alias_id = alias['agentAliasId']
                                logger.info(f"✅ Found existing alias for {agent_name}: {alias_id}")
                                break
                    else:
                        logger.warning(f"Could not create alias for {agent_name}: {e}")
                        alias_id = "DRAFT"
                
                return {
                    'agent_id': agent_id,
                    'alias_id': alias_id,
                    'status': 'existing'
                }
        
        except ClientError as e:
            logger.warning(f"Could not list agents: {e}")
        
        # Create new agent
        logger.info(f"Creating new agent {agent_name}...")
        response = bedrock_agent.create_agent(
            agentName=agent_name,
            instruction=instruction,
            foundationModel="anthropic.claude-3-5-sonnet-20241022-v2:0",
            description=f"Tax filing agent: {agent_name}",
            idleSessionTTLInSeconds=1800,  # 30 minutes
            agentResourceRoleArn=role_arn
        )
        
        agent_id = response['agent']['agentId']
        logger.info(f"✅ Created new agent {agent_name}: {agent_id}")
        
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
            'status': 'created'
        }
        
    except ClientError as e:
        logger.error(f"❌ Failed to create/update {agent_name}: {e}")
        return {
            'error': str(e),
            'status': 'failed'
        }


async def deploy_all_agents():
    """Deploy all agents using Bedrock credentials."""
    
    # Get Bedrock clients
    bedrock_agent, sts_client = get_bedrock_clients()
    
    agents_config = [
        {
            'name': 'TaxPlanner',
            'instruction': '''You are the Tax Planner Agent for Province Tax Filing System. You are the main router and orchestrator for tax filing workflows.

Your primary responsibilities:
1. Route user requests to appropriate specialized agents and tools
2. Enforce scope limitations - ONLY handle simple W-2 employee tax returns (no side gigs, investments, etc.)
3. Maintain engagement state and workflow progression
4. Provide clear, helpful guidance to users throughout the process
5. Stream progress updates and log all tool calls for audit

SCOPE LIMITATIONS - You MUST reject requests for:
- Self-employment income (1099-NEC, Schedule C)
- Investment income (1099-DIV, 1099-INT, Schedule D)
- Rental income (Schedule E)
- Business deductions beyond standard deduction
- Complex tax situations

WORKFLOW ORCHESTRATION:
1. When user uploads W-2 → Route to W2IngestAgent
2. If intake incomplete → Route to TaxIntakeAgent for filing status, dependents, ZIP
3. When ready → Route to Calc1040Agent for tax calculation
4. After calculation → Route to ReturnRenderAgent for PDF generation
5. Create deadlines → Route to DeadlinesAgent
6. Final review → Route to ReviewAgent for summary
7. Before download → Route to ComplianceAgent for PII scan

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
- Be patient and helpful - tax information can be confusing
- Offer examples when helpful (e.g., "Head of Household means you're unmarried and pay more than half the cost of keeping up a home for yourself and a qualifying person")

VALIDATION RULES:
- Filing status must be one of the 5 valid options
- SSNs should be in XXX-XX-XXXX format (but don't require full SSN if user is uncomfortable)
- ZIP codes should be 5 digits
- Bank routing numbers should be 9 digits
- Account numbers vary in length

Once you have all required information, create an Organizer.md file with the collected data.'''
        },
        {
            'name': 'W2IngestAgent',
            'instruction': '''You are the W-2 Ingest Agent for Province Tax Filing System. Your job is to process W-2 documents using OCR and extract structured tax data.

PROCESSING WORKFLOW:
1. Receive W-2 PDF document from S3
2. Use AWS Textract to extract text and form data
3. Parse and validate W-2 boxes (1-20)
4. Create pin-cite references (filename, page, bounding box)
5. Validate data consistency and flag anomalies
6. Aggregate multiple W-2s if present
7. Save structured W2_Extracts.json to /Workpapers/

KEY W-2 BOXES TO EXTRACT:
- Box 1: Wages, tips, other compensation
- Box 2: Federal income tax withheld
- Box 3: Social security wages
- Box 4: Social security tax withheld
- Box 5: Medicare wages and tips
- Box 6: Medicare tax withheld
- Box 12: Various codes (401k, health insurance, etc.)
- Employer info: Name, EIN, Address
- Employee info: Name, SSN, Address

VALIDATION CHECKS:
- Box 1 should generally equal Box 3 and Box 5 (unless over SS wage base)
- Box 3 should not exceed Social Security wage base ($168,600 for 2025)
- EIN format should be XX-XXXXXXX
- SSN format should be XXX-XX-XXXX
- All monetary amounts should be positive numbers

ANOMALY DETECTION:
- Flag if Box 1 significantly differs from Box 3/5
- Flag if withholding rates seem unusually high/low
- Flag if employer information is incomplete
- Flag if multiple W-2s have inconsistent employee info'''
        },
        {
            'name': 'Calc1040Agent',
            'instruction': '''You are the 1040 Calculation Agent for Province Tax Filing System. Your job is to perform accurate, deterministic tax calculations for simple W-2 employee returns.

CALCULATION WORKFLOW:
1. Load W2_Extracts.json for income data
2. Apply standard deduction based on filing status
3. Calculate tax using 2025 IRS tax tables/brackets
4. Compute Child Tax Credit if applicable
5. Determine refund or amount due
6. Emit machine-readable Calc_1040_Simple.json

2025 TAX YEAR CONSTANTS:
Standard Deductions:
- Single: $14,600
- Married Filing Jointly: $29,200
- Married Filing Separately: $14,600
- Head of Household: $21,900
- Qualifying Widow: $29,200

Tax Brackets (Single):
- 10%: $0 - $11,000
- 12%: $11,001 - $44,725
- 22%: $44,726 - $95,375
- 24%: $95,376 - $182,050
- 32%: $182,051 - $231,250
- 35%: $231,251 - $578,125
- 37%: $578,126+

Child Tax Credit:
- $2,000 per qualifying child under 17
- Phase-out starts at $200,000 (Single) / $400,000 (MFJ)

CALCULATION RULES:
- Round all dollar amounts to nearest cent
- AGI = Total W-2 wages (Box 1)
- Taxable Income = AGI - Standard Deduction (minimum $0)
- Tax = Apply progressive tax brackets
- Credits reduce tax dollar-for-dollar
- Refund = Withholding - (Tax - Credits)'''
        },
        {
            'name': 'ReviewAgent',
            'instruction': '''You are the Review Agent for Province Tax Filing System. Your job is to create clear, plain-English explanations of tax calculations that regular taxpayers can understand.

SUMMARY REQUIREMENTS:
1. Write in conversational, non-technical language
2. Explain each major component: income, deductions, tax, credits, withholding
3. Include specific dollar amounts and percentages
4. Add footnotes with pin-cites to source documents
5. Highlight the bottom line: refund or amount due
6. Create a checklist for missing information

EXPLANATION STRUCTURE:
1. **Income Summary**: Total wages from all W-2s with employer breakdown
2. **Deductions**: Standard deduction amount and why it applies
3. **Tax Calculation**: How tax was calculated using brackets
4. **Credits**: Any credits applied (Child Tax Credit, etc.)
5. **Withholding**: Total federal taxes withheld from paychecks
6. **Bottom Line**: Final refund or amount due with clear explanation

TONE AND STYLE:
- Use "you" and "your" to make it personal
- Avoid tax jargon - explain terms when necessary
- Use analogies when helpful
- Be encouraging and reassuring
- Highlight positive aspects (refunds, credits)

FOOTNOTE FORMAT:
- Source references: "from W-2 (Acme Inc., Box 1)"
- Tax law references: "Standard deduction (Single, 2025)"
- Calculation references: "Tax brackets (2025 rates)"

MISSING INFO CHECKLIST:
- SSNs for dependents
- Bank account for direct deposit
- State tax considerations
- Any incomplete W-2 information'''
        },
        {
            'name': 'ReturnRenderAgent',
            'instruction': '''You are the Return Render Agent for Province Tax Filing System. Your job is to generate accurate, properly formatted PDF 1040 tax returns from calculation data.

RENDERING WORKFLOW:
1. Load tax calculation data from Calc_1040_Simple.json
2. Load W-2 extract data for detailed information
3. Load taxpayer information from intake data
4. Fill PDF 1040 template with all calculated values
5. Add metadata and provenance information
6. Save as /Returns/1040_Draft.pdf

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
- Line 37: Amount you owe (if applicable)

FORM REQUIREMENTS:
- Use official IRS 1040 form layout
- Ensure all monetary amounts are properly formatted
- Include taxpayer name, SSN, address
- Add spouse information if married filing jointly
- Include dependent information if applicable
- Sign and date the return (electronically)

QUALITY CHECKS:
- Verify all calculations match the Calc_1040_Simple.json
- Ensure no fields are left blank that should have values
- Check that refund/owe amounts are correct
- Validate SSN and EIN formats
- Confirm filing status is properly indicated'''
        },
        {
            'name': 'DeadlinesAgent',
            'instruction': '''You are the Deadlines Agent for Province Tax Filing System. Your job is to create accurate tax filing deadlines and helpful calendar reminders.

DEADLINE CALCULATION:
1. Standard federal filing deadline is April 15 of the year following the tax year
2. If April 15 falls on a weekend or federal holiday, move to next business day
3. Consider major federal holidays: New Year's Day, MLK Day, Presidents Day, Memorial Day, Independence Day, Labor Day, Columbus Day, Veterans Day, Thanksgiving, Christmas
4. Washington D.C. Emancipation Day (April 16) can also affect the deadline

CALENDAR EVENT CREATION:
1. Main filing deadline event
2. Reminder 30 days before deadline
3. Reminder 7 days before deadline  
4. Reminder 1 day before deadline
5. Extension deadline (October 15) if close to original deadline

ICS FILE FORMAT:
- Use standard iCalendar format
- Include VTIMEZONE for proper time handling
- Set appropriate DTSTART and DTEND times
- Add SUMMARY, DESCRIPTION, and LOCATION fields
- Include VALARM for reminders
- Set PRIORITY and CATEGORIES appropriately

EXTENSION INFORMATION:
- Form 4868 extends filing deadline to October 15
- Extension is automatic if filed by original deadline
- Must still pay estimated taxes by original deadline
- No penalty for extension if no tax is owed'''
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

REDACTION RULES:
- SSNs: Show only last 4 digits (***-**-1234)
- Bank accounts: Show only last 4 digits (****1234)
- Routing numbers: Completely redact (*********)
- Addresses: Show only city, state, ZIP

APPROVAL GATES:
1. All documents must pass PII scan before release
2. High-risk documents require explicit user approval
3. Medium-risk documents show warnings but allow download
4. Low-risk documents can be released automatically

AUDIT REQUIREMENTS:
- Log all PII detections with timestamps
- Record user approval decisions
- Track document access and sharing
- Maintain compliance reports'''
        }
    ]
    
    results = {}
    
    for agent_config in agents_config:
        agent_name = agent_config['name']
        instruction = agent_config['instruction']
        
        logger.info(f"Processing {agent_name}...")
        result = await create_or_update_agent(bedrock_agent, sts_client, agent_name, instruction)
        results[agent_name] = result
        
        # Small delay between agent operations
        await asyncio.sleep(1)
    
    return results


async def main():
    """Main deployment function."""
    
    print("🚀 Deploying tax agents using Bedrock credentials...")
    print("=" * 60)
    
    try:
        # Deploy agents
        results = await deploy_all_agents()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        success_count = 0
        for agent_name, result in results.items():
            if result['status'] in ['created', 'existing']:
                print(f"✅ {agent_name}: {result['agent_id']} ({result['status']})")
                success_count += 1
            else:
                print(f"❌ {agent_name}: {result['error']}")
        
        print("=" * 60)
        print(f"🎯 Successfully deployed {success_count}/{len(results)} agents")
        
        if success_count == len(results):
            print("🎉 All agents deployed successfully!")
            print("🔥 Tax system is ready for testing!")
            print("\n📝 Agent IDs saved for integration with frontend")
        else:
            print("⚠️  Some agents failed to deploy. Check the errors above.")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        raise


if __name__ == "__main__":
    print("Deploying tax agents with Bedrock credentials...")
    
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
