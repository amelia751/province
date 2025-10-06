# Required IAM Permissions for Tax System Deployment

## Current Issue
The `province` user needs additional IAM permissions to create the necessary roles and deploy Bedrock agents.

## Required Permissions to Add

Please add these permissions to the `province` user's IAM policy:

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
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:ListAttachedRolePolicies"
            ],
            "Resource": [
                "arn:aws:iam::*:role/BedrockAgentRole",
                "arn:aws:iam::*:role/TaxFilingLambdaRole"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:CreateAgent",
                "bedrock:CreateAgentAlias",
                "bedrock:CreateAgentActionGroup",
                "bedrock:PrepareAgent",
                "bedrock:ListAgents",
                "bedrock:GetAgent",
                "bedrock:UpdateAgent",
                "bedrock:DeleteAgent"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:GetFunction",
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
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

## Alternative: Manual Role Creation

If you prefer to create the roles manually in the AWS console, here are the exact roles needed:

### 1. BedrockAgentRole

**Trust Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Permissions Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::province-documents-storage",
                "arn:aws:s3:::province-documents-storage/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/province-tax-*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "textract:AnalyzeDocument",
                "textract:DetectDocumentText"
            ],
            "Resource": "*"
        }
    ]
}
```

### 2. TaxFilingLambdaRole

**Trust Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Permissions Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::province-documents-storage",
                "arn:aws:s3:::province-documents-storage/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/province-tax-*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "textract:AnalyzeDocument",
                "textract:DetectDocumentText"
            ],
            "Resource": "*"
        }
    ]
}
```

## Next Steps

1. **Add the IAM permissions** above to the `province` user
2. **Run the deployment script** again: `python scripts/deploy_complete_tax_system.py`

OR

1. **Create the roles manually** using the AWS console with the policies above
2. **Run the simplified deployment script** (I'll create this next)

Let me know which approach you prefer!
