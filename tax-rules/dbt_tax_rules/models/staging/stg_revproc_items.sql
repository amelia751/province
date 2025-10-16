{{ config(materialized='view') }}

-- Staging model for revenue procedure items
SELECT
  tax_year,
  section,
  key,
  value,
  value_numeric,
  units,
  data_type,
  filing_status,
  income_range_min,
  income_range_max,
  tax_rate,
  source_url,
  revproc_number,
  published_date,
  description,
  extraction_method,
  confidence_score,
  jurisdiction_level,
  jurisdiction_code

FROM {{ source('raw', 'revproc_items') }}

-- Basic data quality filters
WHERE tax_year IS NOT NULL
  AND section IS NOT NULL
  AND key IS NOT NULL
  AND value IS NOT NULL
