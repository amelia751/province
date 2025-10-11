# IRS Tax Rules Connector

A Fivetran Connector SDK implementation that extracts authoritative tax rules from IRS sources including newsroom releases, revenue procedures, Internal Revenue Bulletins, draft forms, and Modernized e-File schemas.

## Overview

This connector provides a clean, Google-first pipeline that syncs IRS tax rule data to BigQuery via Fivetran, enabling downstream dbt transformations and canonical rules.json exports for AWS Bedrock integration.

### Architecture

```
IRS Sources → Custom Connector (Fivetran SDK) → BigQuery → dbt models → GCS export → AWS Bedrock
```

## Data Sources

The connector extracts data from five authoritative IRS streams:

1. **Newsroom Releases** (`newsroom_releases`) - IRS announcements and inflation adjustments
2. **Revenue Procedure Items** (`revproc_items`) - Structured tax tables and thresholds from Rev. Procs
3. **IRB Bulletins** (`irb_bulletins`) - Internal Revenue Bulletin index and documents
4. **Draft Forms** (`draft_forms`) - Form 1040 series drafts and finals with change tracking
5. **MeF Summaries** (`mef_summaries`) - Modernized e-File schema versions and business rules

## Features

- **Incremental Syncs**: Stateful cursors per stream with automatic backfill
- **Schema Management**: Primary keys and idempotent merges
- **Error Handling**: Built-in retries and HTTP backoff
- **Content Hashing**: SHA256 hashing for PDF change detection
- **Jurisdiction Support**: Configurable for federal, state, and city levels
- **Relevance Filtering**: Keyword-based filtering for tax rule changes

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd tax-rules-connector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Configuration

The connector supports the following configuration options:

```yaml
jurisdiction_level: "federal"  # federal, state, city
jurisdiction_code: "US"        # US, CA, NY, NYC, PHL, etc.
enabled_streams:               # Which streams to sync
  - newsroom_releases
  - revproc_items
  - irb_bulletins
  - draft_forms
  - mef_summaries
base_urls:                     # Override default IRS URLs if needed
  newsroom: "https://www.irs.gov/newsroom"
  irb: "https://www.irs.gov/irb"
  draft_forms: "https://www.irs.gov/forms-pubs/draft-tax-forms"
  mef: "https://www.irs.gov/modernized-e-file-mf-business-rules-and-schemas"
request_timeout: 30            # HTTP timeout in seconds
max_retries: 3                 # Max retry attempts
```

## Usage

### Local Testing

```bash
# Test connection
python -m tax_rules_connector.connector test

# Run sync
python -m tax_rules_connector.connector sync
```

### Fivetran Deployment

1. Package the connector:
```bash
tar -czf tax-rules-connector.tar.gz src/ connector.yaml requirements.txt
```

2. Upload to Fivetran and configure with your BigQuery destination

3. Set sync schedule (recommended: daily with October-November emphasis)

## Data Schemas

### newsroom_releases
- `release_id` (STRING, PK) - Unique release identifier
- `title` (STRING) - Release title
- `url` (STRING) - Release URL
- `published_date` (DATE) - Publication date
- `linked_revproc_url` (STRING) - Link to related Rev. Proc
- `content_summary` (STRING) - Brief content summary
- `keywords_matched` (STRING) - JSON array of matched keywords

### revproc_items
- `tax_year` (INTEGER, PK) - Tax year
- `section` (STRING, PK) - Section name (e.g., "standard_deduction")
- `key` (STRING, PK) - Item key
- `value` (STRING) - Item value
- `units` (STRING) - Value units
- `source_url` (STRING) - Source Rev. Proc URL
- `published_date` (DATE) - Publication date
- `revproc_number` (STRING) - Rev. Proc number

### irb_bulletins
- `bulletin_no` (STRING, PK) - Bulletin number (e.g., "2024-44")
- `doc_number` (STRING, PK) - Document number
- `published_date` (DATE) - Publication date
- `doc_type` (STRING) - Document type
- `title` (STRING) - Document title
- `url_html` (STRING) - HTML URL
- `url_pdf` (STRING) - PDF URL
- `sha256` (STRING) - Content hash

### draft_forms
- `form_number` (STRING, PK) - Form number (e.g., "1040")
- `revision` (STRING, PK) - Revision identifier
- `status` (STRING) - Status (draft, final, revised)
- `published_date` (DATE) - Publication date
- `url_pdf` (STRING) - PDF URL
- `url_instructions` (STRING) - Instructions URL
- `changes_summary` (STRING) - Summary of changes
- `tax_year` (INTEGER) - Tax year

### mef_summaries
- `schema_version` (STRING, PK) - Schema version
- `published_date` (DATE) - Publication date
- `url` (STRING) - Schema URL
- `notes` (STRING) - Version notes
- `tax_year` (INTEGER) - Tax year
- `form_types` (STRING) - JSON array of form types
- `schema_type` (STRING) - Type (business_rules, schema, both)

## Development

### Project Structure

```
tax-rules-connector/
├── src/tax_rules_connector/
│   ├── __init__.py
│   ├── connector.py          # Main connector implementation
│   ├── http_client.py        # HTTP client with retries
│   ├── main.py              # Entry point
│   └── streams/             # Stream implementations
│       ├── __init__.py
│       ├── base.py          # Base stream class
│       ├── newsroom_releases.py
│       ├── revproc_items.py
│       ├── irb_bulletins.py
│       ├── draft_forms.py
│       └── mef_summaries.py
├── tests/                   # Unit tests
├── docs/                    # Documentation
├── connector.yaml           # Fivetran connector config
├── requirements.txt         # Dependencies
├── setup.py                # Package setup
└── README.md               # This file
```

### Adding New Streams

1. Create a new stream class inheriting from `BaseStream`
2. Implement required methods: `get_schema()`, `sync()`, `test_connection()`
3. Add the stream to `connector.py`
4. Update configuration schema in `connector.yaml`

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Test specific stream
python -c "
from tax_rules_connector.streams import NewsroomReleasesStream
from tax_rules_connector.http_client import IRSHttpClient
client = IRSHttpClient()
stream = NewsroomReleasesStream(client, 'https://www.irs.gov/newsroom', 'federal', 'US')
print(stream.test_connection())
"
```

## Deployment to Fivetran

1. **Package the connector**:
   ```bash
   tar -czf tax-rules-connector-v1.0.0.tar.gz src/ connector.yaml requirements.txt README.md
   ```

2. **Upload to Fivetran**:
   - Go to Fivetran dashboard
   - Create new connector → Custom Connector
   - Upload the tar.gz file
   - Configure BigQuery destination

3. **Set up sync schedule**:
   - Daily sync for most streams
   - Higher frequency (hourly) during October-November for inflation adjustments
   - Use Fivetran's "trigger transformation after load" for dbt

## Integration with dbt

After Fivetran loads raw data to BigQuery, use dbt to create canonical models:

```sql
-- models/rules_packages.sql
SELECT 
  'federal' as jurisdiction_level,
  'US' as jurisdiction_code,
  tax_year,
  '1.0' as tables_version,
  -- Assemble JSON structures from revproc_items
  -- Add provenance and checksums
FROM {{ ref('revproc_items') }}
GROUP BY tax_year
```

## Monitoring

- **Fivetran Logs**: Platform logs auto-land in BigQuery
- **Sync Monitoring**: Set up alerts on "rows written" anomalies
- **Data Quality**: Monitor for missing tax years or empty sections
- **Rate Limiting**: Connector includes respectful delays (0.5s between requests)

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create GitHub issues for bugs and feature requests
- Check Fivetran documentation for connector deployment
- Review IRS website structure changes that may affect parsing
