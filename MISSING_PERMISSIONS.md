# Missing Permissions for Bedrock User

Based on the deployment attempt, the `province` user needs these additional permissions:

## Lambda Permissions Needed
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:GetFunction",
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:InvokeFunction",
                "lambda:AddPermission",
                "lambda:RemovePermission"
            ],
            "Resource": "*"
        }
    ]
}
```

## IAM Role Permissions Needed
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:PutRolePolicy",
                "iam:GetRole",
                "iam:PassRole",
                "iam:AttachRolePolicy"
            ],
            "Resource": [
                "arn:aws:iam::*:role/BedrockAgentRole",
                "arn:aws:iam::*:role/TaxFilingLambdaRole"
            ]
        }
    ]
}
```

## Bedrock Permissions Needed
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
                "bedrock:PrepareAgent",
                "bedrock:ListAgents",
                "bedrock:GetAgent",
                "bedrock:UpdateAgent"
            ],
            "Resource": "*"
        }
    ]
}
```

## Complete Policy for Province User

Here's the complete policy to add to the `province` user:

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
                "bedrock:PrepareAgent",
                "bedrock:ListAgents",
                "bedrock:GetAgent",
                "bedrock:UpdateAgent"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:GetFunction",
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:InvokeFunction",
                "lambda:AddPermission",
                "lambda:RemovePermission"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:PutRolePolicy",
                "iam:GetRole",
                "iam:PassRole",
                "iam:AttachRolePolicy"
            ],
            "Resource": [
                "arn:aws:iam::*:role/BedrockAgentRole",
                "arn:aws:iam::*:role/TaxFilingLambdaRole"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

## Next Steps

1. **Add these permissions** to the `province` user in AWS IAM
2. **Run the deployment script** again: `python scripts/deploy_complete_tax_system.py`

The deployment will then:
1. ✅ Create the necessary IAM roles
2. ✅ Create the Lambda function for tools
3. ✅ Deploy all 8 tax agents to Bedrock
4. ✅ Set up action groups with tools

Once you add these permissions, the system should deploy successfully!
