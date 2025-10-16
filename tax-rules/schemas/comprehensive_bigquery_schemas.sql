-- Comprehensive BigQuery schemas for IRS Tax Rules Connector
-- These schemas are designed to be future-proof and avoid the need for frequent additions

-- 1. NEWSROOM RELEASES - Enhanced schema for comprehensive news tracking
CREATE TABLE IF NOT EXISTS `province-development.raw.newsroom_releases` (
  -- Primary identifiers
  release_id STRING NOT NULL,
  
  -- Core content
  title STRING,
  url STRING,
  published_date DATE,
  
  -- Content analysis
  content_summary STRING,
  content_full_text STRING,  -- Full article text for search/analysis
  content_type STRING,  -- newsroom_release, announcement, notice
  content_length INTEGER,
  
  -- Linked documents
  linked_revproc_url STRING,
  linked_documents JSON,  -- Array of {type, url, title, description}
  
  -- Relevance and categorization
  keywords_matched JSON,  -- Array of matched keywords
  tax_topics JSON,  -- Array of tax topics (inflation, brackets, credits, etc.)
  relevance_score FLOAT64,  -- AI-determined relevance score
  is_inflation_related BOOLEAN,
  is_tax_year_update BOOLEAN,
  
  -- Document hashes for change detection
  content_sha256 STRING,
  html_sha256 STRING,
  
  -- Metadata
  jurisdiction_level STRING,
  jurisdiction_code STRING,
  
  -- Processing metadata
  extraction_method STRING,  -- manual, ai_parsed, regex_parsed
  processing_notes STRING,
  last_updated TIMESTAMP,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN
)
PARTITION BY DATE(published_date)
CLUSTER BY jurisdiction_level, jurisdiction_code, is_inflation_related;

-- 2. IRB BULLETINS - Enhanced for comprehensive bulletin tracking
CREATE TABLE IF NOT EXISTS `province-development.raw.irb_bulletins` (
  -- Primary identifiers
  bulletin_no STRING NOT NULL,
  doc_number STRING NOT NULL,
  
  -- Publication info
  published_date DATE,
  doc_type STRING,  -- revenue_ruling, revenue_procedure, notice, announcement, etc.
  title STRING,
  
  -- URLs and content
  url_html STRING,
  url_pdf STRING,
  
  -- Content metadata
  content_length INTEGER,
  pdf_pages INTEGER,
  pdf_size_bytes INTEGER,
  
  -- Document hashes
  sha256 STRING,
  html_sha256 STRING,
  pdf_sha256 STRING,
  
  -- Content analysis
  summary STRING,
  key_topics JSON,  -- Array of identified topics
  affected_forms JSON,  -- Array of form numbers affected
  effective_date DATE,
  expiration_date DATE,
  
  -- Cross-references
  supersedes JSON,  -- Array of {type, number, date} for superseded documents
  superseded_by JSON,  -- Array of {type, number, date} for superseding documents
  related_documents JSON,  -- Array of related doc references
  
  -- Tax year and applicability
  tax_year INTEGER,
  applies_to_tax_years JSON,  -- Array of applicable tax years
  
  -- GCS storage (for archival)
  gcs_pdf_uri STRING,
  gcs_text_uri STRING,
  gcs_text_jsonl_uri STRING,  -- Per-page text chunks
  
  -- Processing metadata
  extraction_status STRING,  -- pending, extracted, failed
  extraction_notes STRING,
  ai_analysis_complete BOOLEAN,
  
  -- Metadata
  jurisdiction_level STRING,
  jurisdiction_code STRING,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN
)
PARTITION BY DATE(published_date)
CLUSTER BY jurisdiction_level, jurisdiction_code, doc_type, tax_year;

-- 3. IRB ARTICLES - Separate table for article content (HTML/text analysis)
CREATE TABLE IF NOT EXISTS `province-development.raw.irb_articles` (
  -- Primary identifier (links to irb_bulletins)
  doc_key STRING NOT NULL,  -- bulletin_no#doc_number
  
  -- Article content
  url_html STRING,
  title STRING,
  published_date DATE,
  
  -- Full content
  body_text STRING,  -- Cleaned article text
  body_html STRING,  -- Raw HTML for reference
  summary STRING,  -- First 500-1000 chars
  
  -- Content analysis
  word_count INTEGER,
  reading_time_minutes INTEGER,
  language STRING DEFAULT 'en',
  
  -- Extracted entities
  mentioned_forms JSON,  -- Array of form numbers mentioned
  mentioned_sections JSON,  -- Array of tax code sections
  mentioned_dates JSON,  -- Array of important dates
  mentioned_amounts JSON,  -- Array of dollar amounts/thresholds
  
  -- Change detection
  sha256_html STRING,
  content_last_modified TIMESTAMP,
  
  -- Processing metadata
  fetched_at TIMESTAMP,
  processed_at TIMESTAMP,
  processing_version STRING,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN
)
PARTITION BY DATE(published_date)
CLUSTER BY doc_key;

-- 4. IRB PDF TEXT PAGES - For searchable PDF content
CREATE TABLE IF NOT EXISTS `province-development.raw.irb_pdf_text_pages` (
  -- Identifiers
  doc_key STRING NOT NULL,  -- bulletin_no#doc_number
  page_no INTEGER NOT NULL,
  
  -- Content
  text STRING,  -- Plain text from PDF page
  
  -- Page metadata
  page_width FLOAT64,
  page_height FLOAT64,
  
  -- Tables detected on page
  tables_detected JSON,  -- Array of table boundaries/content
  
  -- Processing metadata
  extraction_method STRING,  -- pdfminer, pypdf, etc.
  extraction_confidence FLOAT64,
  
  -- Timestamps
  _ingested_at TIMESTAMP,
  _fivetran_synced TIMESTAMP
)
PARTITION BY DATE(_ingested_at)
CLUSTER BY doc_key, page_no;

-- 5. REVPROC DOCUMENTS - Metadata for Revenue Procedure PDFs
CREATE TABLE IF NOT EXISTS `province-development.raw.revproc_docs` (
  -- Primary identifier
  revproc_number STRING NOT NULL,
  
  -- Document info
  title STRING,
  published_date DATE,
  tax_year INTEGER,
  
  -- URLs
  url_html STRING,
  url_pdf STRING,
  
  -- File metadata
  pdf_size_bytes INTEGER,
  pdf_pages INTEGER,
  pdf_sha256 STRING,
  
  -- GCS storage
  gcs_pdf_uri STRING,
  gcs_text_uri STRING,
  gcs_text_jsonl_uri STRING,
  
  -- Content analysis
  document_type STRING,  -- inflation_adjustment, guidance, procedure
  key_topics JSON,
  affected_tax_years JSON,
  
  -- Processing status
  text_extracted BOOLEAN DEFAULT FALSE,
  tables_parsed BOOLEAN DEFAULT FALSE,
  items_extracted BOOLEAN DEFAULT FALSE,
  
  -- Metadata
  jurisdiction_level STRING,
  jurisdiction_code STRING,
  
  -- Timestamps
  fetched_at TIMESTAMP,
  last_processed TIMESTAMP,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN
)
PARTITION BY DATE(published_date)
CLUSTER BY jurisdiction_level, jurisdiction_code, tax_year;

-- 6. REVPROC ITEMS - Enhanced for comprehensive tax data extraction
CREATE TABLE IF NOT EXISTS `province-development.raw.revproc_items` (
  -- Primary identifiers
  tax_year INTEGER NOT NULL,
  section STRING NOT NULL,
  key STRING NOT NULL,
  
  -- Core data
  value STRING,  -- Stored as string to handle various data types
  value_numeric NUMERIC,  -- Parsed numeric value when applicable
  units STRING,
  data_type STRING,  -- amount, percentage, threshold, text, boolean
  
  -- Tax bracket specific fields
  filing_status STRING,  -- S, MFJ, MFS, HOH, QW
  income_range_min INTEGER,
  income_range_max INTEGER,
  tax_rate NUMERIC,
  
  -- Credit/deduction specific fields
  phase_out_start INTEGER,
  phase_out_end INTEGER,
  max_credit_amount NUMERIC,
  
  -- Source information
  source_url STRING,
  revproc_number STRING,
  published_date DATE,
  
  -- Context and validation
  description STRING,  -- Human-readable description
  formula STRING,  -- Calculation formula if applicable
  conditions JSON,  -- Array of conditions/limitations
  
  -- Cross-references
  related_sections JSON,  -- Array of related section keys
  supersedes JSON,  -- Array of {tax_year, section, key} for superseded items
  
  -- Quality assurance
  extraction_method STRING,  -- regex, ai_parsed, manual
  confidence_score FLOAT64,
  validation_status STRING,  -- pending, validated, flagged
  validation_notes STRING,
  
  -- Effective dates
  effective_date DATE,
  expiration_date DATE,
  
  -- Metadata
  jurisdiction_level STRING,
  jurisdiction_code STRING,
  
  -- Processing metadata
  extracted_at TIMESTAMP,
  last_validated TIMESTAMP,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN
)
PARTITION BY RANGE_BUCKET(tax_year, GENERATE_ARRAY(2000, 2050, 1))
CLUSTER BY jurisdiction_level, jurisdiction_code, section, filing_status;

-- 7. DRAFT FORMS - Enhanced for comprehensive form tracking
CREATE TABLE IF NOT EXISTS `province-development.raw.draft_forms` (
  -- Primary identifiers
  form_number STRING NOT NULL,
  revision STRING NOT NULL,
  
  -- Form metadata
  status STRING,  -- draft, final, revised, withdrawn
  published_date DATE,
  tax_year INTEGER,
  form_title STRING,
  form_series STRING,  -- 1040, 1120, 1065, etc.
  
  -- URLs and files
  url_pdf STRING,
  url_instructions STRING,
  url_schedules JSON,  -- Array of related schedule URLs
  
  -- File metadata
  pdf_sha256 STRING,
  instructions_sha256 STRING,
  pdf_size_bytes INTEGER,
  instructions_size_bytes INTEGER,
  pdf_pages INTEGER,
  instructions_pages INTEGER,
  
  -- Content analysis
  changes_summary STRING,
  major_changes JSON,  -- Array of significant changes
  new_fields JSON,  -- Array of new fields added
  removed_fields JSON,  -- Array of fields removed
  modified_fields JSON,  -- Array of fields modified
  
  -- Form structure
  total_lines INTEGER,
  has_schedules BOOLEAN,
  schedule_list JSON,  -- Array of included schedules
  
  -- Comparison with previous version
  previous_revision STRING,
  changes_from_previous JSON,  -- Detailed change analysis
  
  -- Processing metadata
  ocr_processed BOOLEAN DEFAULT FALSE,
  field_extraction_complete BOOLEAN DEFAULT FALSE,
  change_analysis_complete BOOLEAN DEFAULT FALSE,
  
  -- GCS storage
  gcs_pdf_uri STRING,
  gcs_instructions_uri STRING,
  gcs_ocr_results_uri STRING,
  
  -- Metadata
  jurisdiction_level STRING,
  jurisdiction_code STRING,
  
  -- Timestamps
  first_seen TIMESTAMP,
  last_updated TIMESTAMP,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN
)
PARTITION BY RANGE_BUCKET(tax_year, GENERATE_ARRAY(2000, 2050, 1))
CLUSTER BY jurisdiction_level, jurisdiction_code, form_series, status;

-- 8. MEF SUMMARIES - Enhanced for comprehensive e-file schema tracking
CREATE TABLE IF NOT EXISTS `province-development.raw.mef_summaries` (
  -- Primary identifier
  schema_version STRING NOT NULL,
  
  -- Version metadata
  published_date DATE,
  tax_year INTEGER,
  
  -- URLs and files
  url STRING,
  schema_url STRING,
  business_rules_url STRING,
  documentation_url STRING,
  
  -- Version details
  version_major INTEGER,
  version_minor INTEGER,
  version_patch INTEGER,
  version_build STRING,
  
  -- Content metadata
  schema_type STRING,  -- business_rules, schema, both, documentation
  file_format STRING,  -- xsd, pdf, xml, json
  file_size_bytes INTEGER,
  file_sha256 STRING,
  
  -- Scope and applicability
  form_types JSON,  -- Array of applicable form types
  applies_to_software JSON,  -- Array of software types/versions
  mandatory_date DATE,
  optional_start_date DATE,
  
  -- Change information
  notes STRING,
  changes_summary STRING,
  breaking_changes JSON,  -- Array of breaking changes
  new_features JSON,  -- Array of new features
  deprecated_features JSON,  -- Array of deprecated features
  
  -- Dependencies
  requires_versions JSON,  -- Array of required dependency versions
  compatible_versions JSON,  -- Array of compatible versions
  
  -- Processing metadata
  downloaded BOOLEAN DEFAULT FALSE,
  parsed BOOLEAN DEFAULT FALSE,
  validation_complete BOOLEAN DEFAULT FALSE,
  
  -- GCS storage
  gcs_schema_uri STRING,
  gcs_rules_uri STRING,
  gcs_docs_uri STRING,
  
  -- Metadata
  jurisdiction_level STRING,
  jurisdiction_code STRING,
  
  -- Timestamps
  first_available TIMESTAMP,
  last_updated TIMESTAMP,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP,
  _fivetran_deleted BOOLEAN
)
PARTITION BY DATE(published_date)
CLUSTER BY jurisdiction_level, jurisdiction_code, tax_year, schema_type;

-- 9. PROCESSING LOG - Track all processing activities
CREATE TABLE IF NOT EXISTS `province-development.raw.processing_log` (
  -- Identifiers
  log_id STRING NOT NULL,
  stream_name STRING NOT NULL,
  
  -- Processing details
  operation_type STRING,  -- sync, extract, parse, validate
  status STRING,  -- started, completed, failed, retrying
  
  -- Timing
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  duration_seconds INTEGER,
  
  -- Results
  records_processed INTEGER,
  records_inserted INTEGER,
  records_updated INTEGER,
  records_failed INTEGER,
  
  -- Error handling
  error_message STRING,
  error_details JSON,
  retry_count INTEGER,
  
  -- Context
  cursor_start STRING,
  cursor_end STRING,
  configuration JSON,
  
  -- Metadata
  connector_version STRING,
  fivetran_sync_id STRING,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP
)
PARTITION BY DATE(started_at)
CLUSTER BY stream_name, status;

-- 10. DATA QUALITY METRICS - Track data quality over time
CREATE TABLE IF NOT EXISTS `province-development.raw.data_quality_metrics` (
  -- Identifiers
  metric_id STRING NOT NULL,
  stream_name STRING NOT NULL,
  metric_date DATE NOT NULL,
  
  -- Quality metrics
  total_records INTEGER,
  records_with_missing_data INTEGER,
  records_with_invalid_data INTEGER,
  duplicate_records INTEGER,
  
  -- Content quality
  avg_content_length FLOAT64,
  records_with_empty_content INTEGER,
  records_with_extraction_errors INTEGER,
  
  -- Freshness metrics
  avg_age_days FLOAT64,
  oldest_record_days INTEGER,
  newest_record_days INTEGER,
  
  -- Processing metrics
  avg_processing_time_seconds FLOAT64,
  failed_extractions INTEGER,
  retry_rate FLOAT64,
  
  -- Metadata
  calculated_at TIMESTAMP,
  
  -- Fivetran metadata
  _fivetran_synced TIMESTAMP
)
PARTITION BY metric_date
CLUSTER BY stream_name;
