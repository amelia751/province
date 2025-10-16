

-- Create canonical tax rules packages by jurisdiction and tax year
WITH standard_deductions AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    STRUCT(
      COALESCE(MAX(CASE WHEN filing_status = 'S' THEN value_numeric END), 0) AS single,
      COALESCE(MAX(CASE WHEN filing_status = 'MFJ' THEN value_numeric END), 0) AS married_filing_jointly,
      COALESCE(MAX(CASE WHEN filing_status = 'MFS' THEN value_numeric END), 0) AS married_filing_separately,
      COALESCE(MAX(CASE WHEN filing_status = 'HOH' THEN value_numeric END), 0) AS head_of_household
    ) AS standard_deduction
  FROM `province-development`.`mart`.`stg_revproc_items`
  WHERE section = 'standard_deduction'
    AND _fivetran_deleted = false
  GROUP BY tax_year, jurisdiction_level, jurisdiction_code
),

tax_brackets AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    filing_status,
    ARRAY_AGG(
      STRUCT(
        tax_rate AS rate,
        income_range_min AS min,
        income_range_max AS max,
        description AS description
      )
      ORDER BY income_range_min
    ) AS brackets
  FROM `province-development`.`mart`.`stg_revproc_items`
  WHERE section = 'tax_brackets'
    AND _fivetran_deleted = false
    AND tax_rate IS NOT NULL
  GROUP BY tax_year, jurisdiction_level, jurisdiction_code, filing_status
),

tax_brackets_combined AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    STRUCT(
      COALESCE(MAX(CASE WHEN filing_status = 'S' THEN brackets END), []) AS single,
      COALESCE(MAX(CASE WHEN filing_status = 'MFJ' THEN brackets END), []) AS married_filing_jointly,
      COALESCE(MAX(CASE WHEN filing_status = 'MFS' THEN brackets END), []) AS married_filing_separately,
      COALESCE(MAX(CASE WHEN filing_status = 'HOH' THEN brackets END), []) AS head_of_household
    ) AS tax_brackets
  FROM tax_brackets
  GROUP BY tax_year, jurisdiction_level, jurisdiction_code
),

source_documents AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    ARRAY_AGG(
      DISTINCT STRUCT(
        'revenue_procedure' AS type,
        revproc_number AS number,
        source_url AS url,
        CAST(published_date AS STRING) AS published_date,
        CONCAT('Rev. Proc. ', revproc_number) AS title
      )
    ) AS sources
  FROM `province-development`.`mart`.`stg_revproc_items`
  WHERE _fivetran_deleted = false
    AND revproc_number IS NOT NULL
  GROUP BY tax_year, jurisdiction_level, jurisdiction_code
),

rules_metadata AS (
  SELECT 
    tax_year,
    jurisdiction_level,
    jurisdiction_code,
    MIN(published_date) AS earliest_published_date,
    MAX(published_date) AS latest_published_date,
    COUNT(DISTINCT revproc_number) AS source_count,
    COUNT(*) AS total_items
  FROM `province-development`.`mart`.`stg_revproc_items`
  WHERE _fivetran_deleted = false
  GROUP BY tax_year, jurisdiction_level, jurisdiction_code
)

SELECT 
  -- Primary identifiers
  rm.tax_year,
  rm.jurisdiction_level,
  rm.jurisdiction_code,
  
  -- Package metadata
  CONCAT(rm.jurisdiction_code, '_', rm.tax_year, '_v1') AS package_id,
  '1.0' AS package_version,
  rm.earliest_published_date AS effective_date,
  rm.latest_published_date AS last_updated,
  
  -- Tax rules content
  COALESCE(sd.standard_deduction, STRUCT(0 AS single, 0 AS married_filing_jointly, 0 AS married_filing_separately, 0 AS head_of_household)) AS standard_deduction,
  COALESCE(tb.tax_brackets, STRUCT([] AS single, [] AS married_filing_jointly, [] AS married_filing_separately, [] AS head_of_household)) AS tax_brackets,
  STRUCT() AS credits,  -- Placeholder for future credits data
  STRUCT() AS deductions,  -- Placeholder for future deductions data
  
  -- Source information
  COALESCE(src.sources, []) AS sources,
  
  -- Quality metrics
  rm.source_count,
  rm.total_items,
  
  -- Package integrity
  TO_HEX(SHA256(CONCAT(
    CAST(sd.standard_deduction AS STRING),
    CAST(tb.tax_brackets AS STRING)
  ))) AS checksum_sha256,
  
  -- Status
  true AS is_active,
  false AS is_promoted,  -- Manual promotion process
  
  -- Timestamps
  CURRENT_TIMESTAMP() AS created_at,
  CURRENT_TIMESTAMP() AS updated_at

FROM rules_metadata rm
LEFT JOIN standard_deductions sd USING (tax_year, jurisdiction_level, jurisdiction_code)
LEFT JOIN tax_brackets_combined tb USING (tax_year, jurisdiction_level, jurisdiction_code)
LEFT JOIN source_documents src USING (tax_year, jurisdiction_level, jurisdiction_code)

-- Only include packages with actual data
WHERE rm.total_items > 0

ORDER BY rm.tax_year DESC, rm.jurisdiction_level, rm.jurisdiction_code