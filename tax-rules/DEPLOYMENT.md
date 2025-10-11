# Deployment Guide for Tax Rules Connector

This guide covers deploying the Tax Rules Connector to Fivetran and setting up the complete data pipeline.

## Prerequisites

- Fivetran account with custom connector support
- Google Cloud Platform account
- BigQuery dataset configured
- dbt Cloud or dbt Core setup (optional but recommended)

## Step 1: Package the Connector

```bash
# Build the deployment package
make package

# This creates: dist/tax-rules-connector-v1.0.0.tar.gz
```

## Step 2: Deploy to Fivetran

### 2.1 Create Custom Connector

1. Log into your Fivetran dashboard
2. Go to **Connectors** → **Add Connector** → **Custom Connector**
3. Upload the `tax-rules-connector-v1.0.0.tar.gz` file
4. Fill in connector details:
   - **Name**: IRS Tax Rules Connector
   - **Description**: Extracts authoritative tax rules from IRS sources
   - **Version**: 1.0.0

### 2.2 Configure Connector Instance

Create a new connector instance with these settings:

```yaml
# Basic Configuration
jurisdiction_level: "federal"
jurisdiction_code: "US"
enabled_streams:
  - "newsroom_releases"
  - "revproc_items" 
  - "irb_bulletins"
  - "draft_forms"
  - "mef_summaries"

# Advanced Settings (optional)
request_timeout: 30
max_retries: 3
base_urls:
  newsroom: "https://www.irs.gov/newsroom"
  irb: "https://www.irs.gov/irb"
  draft_forms: "https://www.irs.gov/forms-pubs/draft-tax-forms"
  mef: "https://www.irs.gov/modernized-e-file-mf-business-rules-and-schemas"
```

### 2.3 Set Up BigQuery Destination

1. **Create BigQuery Destination** in Fivetran:
   - Project ID: Your GCP project
   - Dataset: `tax_rules_raw` (or your preferred name)
   - Service Account: JSON key with BigQuery permissions

2. **Required BigQuery Permissions**:
   ```json
   {
     "roles": [
       "roles/bigquery.dataEditor",
       "roles/bigquery.jobUser"
     ]
   }
   ```

### 2.4 Configure Sync Schedule

Recommended sync frequencies:
- **Regular Period**: Daily at 6 AM UTC
- **October-November**: Every 4 hours (inflation adjustment season)
- **Backfill**: Full historical sync on first run

## Step 3: Set Up dbt Transformations

### 3.1 dbt Project Structure

```
tax_rules_dbt/
├── models/
│   ├── staging/
│   │   ├── stg_newsroom_releases.sql
│   │   ├── stg_revproc_items.sql
│   │   └── stg_irb_bulletins.sql
│   ├── marts/
│   │   ├── rules_packages.sql
│   │   ├── rules_current.sql
│   │   └── rules_diff.sql
│   └── exports/
│       └── export_to_gcs.sql
├── macros/
│   └── generate_rules_json.sql
└── dbt_project.yml
```

### 3.2 Key dbt Models

**rules_packages.sql** - Canonical tax rules by year/version:
```sql
{{ config(materialized='table') }}

WITH revproc_aggregated AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    published_date,
    revproc_number,
    -- Aggregate standard deduction amounts
    JSON_OBJECT(
      'single', MAX(CASE WHEN section = 'standard_deduction' AND key LIKE '%single%' THEN CAST(value AS INT64) END),
      'married_filing_jointly', MAX(CASE WHEN section = 'standard_deduction' AND key LIKE '%married_filing_jointly%' THEN CAST(value AS INT64) END),
      'married_filing_separately', MAX(CASE WHEN section = 'standard_deduction' AND key LIKE '%married_filing_separately%' THEN CAST(value AS INT64) END),
      'head_of_household', MAX(CASE WHEN section = 'standard_deduction' AND key LIKE '%head_of_household%' THEN CAST(value AS INT64) END)
    ) AS standard_deduction,
    -- Aggregate tax brackets
    ARRAY_AGG(
      CASE WHEN section = 'tax_brackets' THEN
        JSON_OBJECT(
          'rate', CAST(value AS FLOAT64),
          'min_income', income_range_min,
          'max_income', income_range_max,
          'filing_status', filing_status
        )
      END IGNORE NULLS
    ) AS brackets,
    -- Source tracking
    ARRAY_AGG(DISTINCT 
      JSON_OBJECT(
        'url', source_url,
        'published_date', published_date,
        'revproc_number', revproc_number
      )
    ) AS sources
  FROM {{ ref('stg_revproc_items') }}
  WHERE tax_year IS NOT NULL
  GROUP BY tax_year, jurisdiction_level, jurisdiction_code, published_date, revproc_number
)

SELECT 
  'federal' as tax_form,
  tax_year,
  CONCAT(tax_year, '.', ROW_NUMBER() OVER (PARTITION BY tax_year ORDER BY published_date DESC)) as tables_version,
  published_date as effective_date,
  standard_deduction,
  brackets,
  JSON_OBJECT() as credits, -- Placeholder for credit calculations
  sources,
  SHA256(TO_JSON_STRING(STRUCT(standard_deduction, brackets))) as checksum_sha256,
  FALSE as promoted,
  CAST(NULL AS STRING) as promoted_by,
  CAST(NULL AS TIMESTAMP) as promoted_at,
  jurisdiction_level,
  jurisdiction_code
FROM revproc_aggregated
```

**rules_current.sql** - Current promoted rules:
```sql
{{ config(materialized='view') }}

SELECT *
FROM {{ ref('rules_packages') }}
WHERE promoted = TRUE
QUALIFY ROW_NUMBER() OVER (PARTITION BY tax_year ORDER BY effective_date DESC) = 1
```

### 3.3 GCS Export Configuration

Set up a scheduled BigQuery job to export to GCS:

```sql
-- Export current rules to GCS
EXPORT DATA OPTIONS(
  uri='gs://tax-rules-bucket/1040/*/rules.json',
  format='JSON',
  overwrite=true
) AS
SELECT 
  tax_year,
  tables_version,
  TO_JSON_STRING(STRUCT(
    standard_deduction,
    brackets,
    credits,
    sources,
    checksum_sha256,
    effective_date
  )) as rules_json
FROM {{ ref('rules_current') }}
```

## Step 4: Set Up Cross-Cloud Integration

### 4.1 Cloud Run Service (GCS → AWS Bridge)

Deploy a simple Cloud Run service to provide signed URLs:

```python
# main.py
from flask import Flask, jsonify
from google.cloud import storage
import os

app = Flask(__name__)
client = storage.Client()
bucket = client.bucket('tax-rules-bucket')

@app.route('/rules/1040/<int:year>/current')
def get_current_rules(year):
    blob_name = f'1040/{year}/rules.json'
    blob = bucket.blob(blob_name)
    
    if not blob.exists():
        return jsonify({'error': 'Rules not found'}), 404
    
    # Generate signed URL (valid for 1 hour)
    signed_url = blob.generate_signed_url(
        expiration=3600,
        method='GET'
    )
    
    return jsonify({
        'year': year,
        'signed_url': signed_url,
        'checksum': blob.md5_hash,
        'updated': blob.updated.isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
```

### 4.2 AWS Integration

Your AWS Bedrock application can fetch rules via:

```python
import requests

def get_tax_rules(year: int) -> dict:
    """Fetch current tax rules for a given year."""
    response = requests.get(
        f'https://your-cloud-run-service.run.app/rules/1040/{year}/current'
    )
    response.raise_for_status()
    
    data = response.json()
    
    # Fetch the actual rules JSON
    rules_response = requests.get(data['signed_url'])
    rules_response.raise_for_status()
    
    return {
        'rules': rules_response.json(),
        'checksum': data['checksum'],
        'updated': data['updated']
    }
```

## Step 5: Monitoring and Alerting

### 5.1 Fivetran Monitoring

Set up alerts for:
- Sync failures
- Row count anomalies
- Schema changes
- Connection timeouts

### 5.2 BigQuery Monitoring

Monitor:
- Data freshness (last sync timestamp)
- Row counts by stream
- Data quality checks (missing tax years, invalid amounts)

### 5.3 Cloud Monitoring

Create alerts for:
- GCS export job failures
- Cloud Run service errors
- Signed URL generation failures

## Step 6: Testing the Pipeline

### 6.1 End-to-End Test

```bash
# 1. Trigger Fivetran sync
curl -X POST "https://api.fivetran.com/v1/connectors/{connector_id}/sync" \
  -H "Authorization: Bearer {api_key}"

# 2. Wait for sync completion and check BigQuery
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM tax_rules_raw.newsroom_releases WHERE DATE(_fivetran_synced) = CURRENT_DATE()"

# 3. Run dbt transformations
dbt run --models rules_packages rules_current

# 4. Test GCS export
gsutil ls gs://tax-rules-bucket/1040/

# 5. Test Cloud Run service
curl https://your-cloud-run-service.run.app/rules/1040/2024/current
```

### 6.2 Data Quality Checks

```sql
-- Check for missing standard deductions
SELECT tax_year, COUNT(*) as missing_std_deductions
FROM tax_rules_raw.revproc_items 
WHERE section = 'standard_deduction' 
  AND (value IS NULL OR value = '')
GROUP BY tax_year
HAVING COUNT(*) > 0;

-- Check for unrealistic tax bracket rates
SELECT tax_year, section, key, value
FROM tax_rules_raw.revproc_items
WHERE section = 'tax_brackets' 
  AND (CAST(value AS FLOAT64) > 50 OR CAST(value AS FLOAT64) < 0);
```

## Troubleshooting

### Common Issues

1. **Sync Failures**
   - Check IRS website structure changes
   - Verify network connectivity
   - Review connector logs in Fivetran

2. **Schema Mismatches**
   - Update connector schema definitions
   - Re-deploy connector if needed
   - Check BigQuery table schemas

3. **Data Quality Issues**
   - Review parsing logic in stream implementations
   - Add validation rules in dbt
   - Set up data quality alerts

4. **Performance Issues**
   - Adjust sync frequency
   - Optimize BigQuery queries
   - Consider partitioning large tables

### Support Contacts

- Fivetran Support: For connector deployment issues
- Google Cloud Support: For BigQuery/GCS issues
- Internal Team: For business logic and data quality questions

## Maintenance

### Regular Tasks

- **Weekly**: Review sync logs and data quality
- **Monthly**: Update connector if IRS website changes
- **Quarterly**: Review and optimize dbt transformations
- **Annually**: Update for new tax year requirements

### Version Updates

When updating the connector:

1. Test changes locally
2. Package new version
3. Deploy to staging environment
4. Run end-to-end tests
5. Deploy to production
6. Monitor for issues
