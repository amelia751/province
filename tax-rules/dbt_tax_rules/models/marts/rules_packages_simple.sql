{{ config(materialized='table') }}

-- Simplified canonical tax rules packages
WITH base_data AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    section,
    filing_status,
    key,
    value_numeric,
    revproc_number,
    published_date,
    source_url
  FROM {{ ref('stg_revproc_items') }}
),

standard_deductions AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    MAX(CASE WHEN filing_status = 'S' THEN value_numeric END) AS single,
    MAX(CASE WHEN filing_status = 'MFJ' THEN value_numeric END) AS married_filing_jointly,
    MAX(CASE WHEN filing_status = 'MFS' THEN value_numeric END) AS married_filing_separately,
    MAX(CASE WHEN filing_status = 'HOH' THEN value_numeric END) AS head_of_household
  FROM base_data
  WHERE section = 'standard_deduction'
  GROUP BY tax_year, jurisdiction_level, jurisdiction_code
),

package_metadata AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    MIN(published_date) AS earliest_published_date,
    MAX(published_date) AS latest_published_date,
    COUNT(DISTINCT revproc_number) AS source_count,
    COUNT(*) AS total_items,
    ARRAY_AGG(DISTINCT revproc_number IGNORE NULLS) AS revproc_numbers,
    ARRAY_AGG(DISTINCT source_url IGNORE NULLS) AS source_urls
  FROM base_data
  GROUP BY tax_year, jurisdiction_level, jurisdiction_code
)

SELECT 
  -- Primary identifiers
  pm.tax_year,
  pm.jurisdiction_level,
  pm.jurisdiction_code,
  
  -- Package metadata
  CONCAT(pm.jurisdiction_code, '_', pm.tax_year, '_v1') AS package_id,
  '1.0' AS package_version,
  pm.earliest_published_date AS effective_date,
  pm.latest_published_date AS last_updated,
  
  -- Standard deductions (as JSON for compatibility)
  TO_JSON_STRING(STRUCT(
    COALESCE(sd.single, 0) AS single,
    COALESCE(sd.married_filing_jointly, 0) AS married_filing_jointly,
    COALESCE(sd.married_filing_separately, 0) AS married_filing_separately,
    COALESCE(sd.head_of_household, 0) AS head_of_household
  )) AS standard_deduction_json,
  
  -- Placeholder for tax brackets (JSON format)
  '{}' AS tax_brackets_json,
  
  -- Source information (as JSON)
  TO_JSON_STRING(STRUCT(
    pm.revproc_numbers AS revproc_numbers,
    pm.source_urls AS source_urls
  )) AS sources_json,
  
  -- Quality metrics
  pm.source_count,
  pm.total_items,
  
  -- Package integrity
  TO_HEX(SHA256(CONCAT(
    CAST(COALESCE(sd.single, 0) AS STRING),
    CAST(COALESCE(sd.married_filing_jointly, 0) AS STRING)
  ))) AS checksum_sha256,
  
  -- Status
  true AS is_active,
  false AS is_promoted,
  
  -- Timestamps
  CURRENT_TIMESTAMP() AS created_at,
  CURRENT_TIMESTAMP() AS updated_at

FROM package_metadata pm
LEFT JOIN standard_deductions sd USING (tax_year, jurisdiction_level, jurisdiction_code)

-- Only include packages with actual data
WHERE pm.total_items > 0

ORDER BY pm.tax_year DESC, pm.jurisdiction_level, pm.jurisdiction_code
