{{ config(materialized='view') }}

-- Current active rules - one per jurisdiction/tax_year combination
SELECT 
  *
FROM {{ ref('rules_packages') }}
WHERE is_active = true
  AND tax_year >= EXTRACT(YEAR FROM CURRENT_DATE()) - 2  -- Current and previous 2 years
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY jurisdiction_level, jurisdiction_code, tax_year 
  ORDER BY last_updated DESC
) = 1
