# Tax Forms Inventory

## Overview
This document lists all the IRS tax forms and templates available in the Province Tax Filing System templates bucket for the 2024 tax year.

**S3 Location**: `s3://province-templates-[REDACTED-ACCOUNT-ID]-us-east-2/tax_forms/2024/`

## Core Tax Forms

### Form 1040 and Schedules
- **f1040.pdf** (159.5 KiB) - U.S. Individual Income Tax Return
- **f1040s1.pdf** (88.8 KiB) - Schedule 1: Additional Income and Adjustments to Income
- **f1040s2.pdf** (229.1 KiB) - Schedule 2: Additional Taxes
- **f1040s3.pdf** (68.3 KiB) - Schedule 3: Additional Credits and Payments

### Itemized Deductions and Income Schedules
- **f1040sa.pdf** (77.1 KiB) - Schedule A: Itemized Deductions
- **f1040sb.pdf** (74.5 KiB) - Schedule B: Interest and Ordinary Dividends
- **f1040sc.pdf** (119.4 KiB) - Schedule C: Profit or Loss From Business
- **f1040sd.pdf** (94.9 KiB) - Schedule D: Capital Gains and Losses
- **f1040se.pdf** (144.7 KiB) - Schedule E: Supplemental Income and Loss

## Tax Credits and Special Forms

### Child and Family Credits
- **f8812.pdf** (112.5 KiB) - Credits for Qualifying Children and Other Dependents
- **f2441.pdf** (118.4 KiB) - Child and Dependent Care Expenses

### Education and Retirement Credits
- **f8863.pdf** (116.1 KiB) - Education Credits (American Opportunity and Lifetime Learning Credits)
- **f8880.pdf** (93.4 KiB) - Credit for Qualified Retirement Savings Contributions (Saver's Credit)

### Healthcare and Other Credits
- **f8962.pdf** (115.1 KiB) - Premium Tax Credit (PTC)
- **f8867.pdf** (131.5 KiB) - Paid Preparer's Due Diligence Checklist

## Information Returns (1099 Forms)
- **f1099int.pdf** (526.1 KiB) - Interest Income
- **f1099div.pdf** (527.1 KiB) - Dividends and Distributions
- **f1099r.pdf** (586.9 KiB) - Distributions From Pensions, Annuities, Retirement Plans, etc.
- **f1099g.pdf** (511.0 KiB) - Certain Government Payments

## Employment Forms
- **fw2.pdf** (1.3 MiB) - Wage and Tax Statement

## Instructions and Reference Materials
- **i1040gi.pdf** (4.2 MiB) - Instructions for Form 1040 and 1040-SR
- **i1040tt.pdf** (2.8 MiB) - Tax Table for 2024

## Usage in Province Tax System

### For Simple W-2 Returns (Primary Use Case)
The following forms are essential for basic W-2 employee returns:
- Form 1040 (main return)
- Schedule 1 (if additional income/adjustments)
- Schedule 2 (if additional taxes)
- Schedule 3 (if additional credits)
- Form 8812 (Child Tax Credit)
- Form W-2 (wage statements)
- Instructions (i1040gi.pdf)
- Tax Tables (i1040tt.pdf)

### For More Complex Returns (Future Enhancement)
Additional schedules and forms are available for:
- Business income (Schedule C)
- Investment income (Schedules B, D)
- Rental income (Schedule E)
- Itemized deductions (Schedule A)
- Various tax credits (Forms 8863, 8880, 8962, 2441)

## Access Methods

### Via S3 API
```python
import boto3

s3 = boto3.client('s3')
bucket = 'province-templates-[REDACTED-ACCOUNT-ID]-us-east-2'
key = 'tax_forms/2024/f1040.pdf'

# Download form
s3.download_file(bucket, key, 'local_form.pdf')

# Get signed URL for direct access
url = s3.generate_presigned_url('get_object', 
    Params={'Bucket': bucket, 'Key': key}, 
    ExpiresIn=3600)
```

### Via AWS CLI
```bash
# List all forms
aws s3 ls s3://province-templates-[REDACTED-ACCOUNT-ID]-us-east-2/tax_forms/2024/

# Download specific form
aws s3 cp s3://province-templates-[REDACTED-ACCOUNT-ID]-us-east-2/tax_forms/2024/f1040.pdf ./
```

## Metadata
All forms include the following S3 metadata:
- `source`: IRS
- `tax_year`: 2024
- `uploaded_by`: province_tax_system
- `content_type`: application/pdf

## Updates and Maintenance
- Forms are current as of October 2025
- IRS typically releases updated forms in late December/early January
- Forms should be refreshed annually for the new tax year
- Missing forms (like f1040eic.pdf) may become available later in the tax season

## Total Inventory
- **22 tax forms and documents**
- **Total size**: ~12.5 MB
- **Coverage**: Complete set for federal individual tax returns
- **Compliance**: All forms sourced directly from IRS official publications
