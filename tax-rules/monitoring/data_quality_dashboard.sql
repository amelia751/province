-- Data Quality Dashboard Queries for Tax Rules Pipeline

-- 1. Data Freshness Check
CREATE OR REPLACE VIEW `province-development.mart.data_freshness_check` AS
SELECT 
  'newsroom_releases' as stream_name,
  COUNT(*) as total_records,
  MAX(published_date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) as days_since_latest,
  CASE 
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) <= 7 THEN 'FRESH'
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) <= 30 THEN 'STALE'
    ELSE 'VERY_STALE'
  END as freshness_status
FROM `province-development.raw.newsroom_releases`
WHERE _fivetran_deleted = false

UNION ALL

SELECT 
  'revproc_items' as stream_name,
  COUNT(*) as total_records,
  MAX(published_date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) as days_since_latest,
  CASE 
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) <= 7 THEN 'FRESH'
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) <= 30 THEN 'STALE'
    ELSE 'VERY_STALE'
  END as freshness_status
FROM `province-development.raw.revproc_items`
WHERE _fivetran_deleted = false

UNION ALL

SELECT 
  'irb_bulletins' as stream_name,
  COUNT(*) as total_records,
  MAX(published_date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) as days_since_latest,
  CASE 
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) <= 7 THEN 'FRESH'
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(published_date), DAY) <= 30 THEN 'STALE'
    ELSE 'VERY_STALE'
  END as freshness_status
FROM `province-development.raw.irb_bulletins`
WHERE _fivetran_deleted = false

ORDER BY days_since_latest DESC;

-- 2. Data Quality Metrics
CREATE OR REPLACE VIEW `province-development.mart.data_quality_metrics` AS
SELECT 
  'newsroom_releases' as stream_name,
  COUNT(*) as total_records,
  COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as missing_titles,
  COUNT(CASE WHEN content_summary IS NULL OR content_summary = '' THEN 1 END) as missing_content,
  COUNT(CASE WHEN published_date IS NULL THEN 1 END) as missing_dates,
  COUNT(CASE WHEN is_inflation_related IS NULL THEN 1 END) as missing_flags,
  ROUND(100.0 * COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) / COUNT(*), 2) as title_completeness_pct
FROM `province-development.raw.newsroom_releases`
WHERE _fivetran_deleted = false

UNION ALL

SELECT 
  'revproc_items' as stream_name,
  COUNT(*) as total_records,
  COUNT(CASE WHEN value IS NULL OR value = '' THEN 1 END) as missing_values,
  COUNT(CASE WHEN section IS NULL OR section = '' THEN 1 END) as missing_sections,
  COUNT(CASE WHEN published_date IS NULL THEN 1 END) as missing_dates,
  COUNT(CASE WHEN value_numeric IS NULL AND data_type = 'amount' THEN 1 END) as missing_numeric_values,
  ROUND(100.0 * COUNT(CASE WHEN value IS NOT NULL AND value != '' THEN 1 END) / COUNT(*), 2) as value_completeness_pct
FROM `province-development.raw.revproc_items`
WHERE _fivetran_deleted = false

UNION ALL

SELECT 
  'irb_bulletins' as stream_name,
  COUNT(*) as total_records,
  COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as missing_titles,
  COUNT(CASE WHEN url_html IS NULL OR url_html = '' THEN 1 END) as missing_urls,
  COUNT(CASE WHEN published_date IS NULL THEN 1 END) as missing_dates,
  COUNT(CASE WHEN doc_type IS NULL OR doc_type = '' THEN 1 END) as missing_doc_types,
  ROUND(100.0 * COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) / COUNT(*), 2) as title_completeness_pct
FROM `province-development.raw.irb_bulletins`
WHERE _fivetran_deleted = false;

-- 3. Rules Package Status
CREATE OR REPLACE VIEW `province-development.mart.rules_package_status` AS
SELECT 
  tax_year,
  jurisdiction_level,
  jurisdiction_code,
  package_id,
  package_version,
  effective_date,
  last_updated,
  source_count,
  total_items,
  is_active,
  is_promoted,
  CASE 
    WHEN is_promoted THEN 'PROMOTED'
    WHEN is_active THEN 'ACTIVE'
    ELSE 'INACTIVE'
  END as status,
  DATE_DIFF(CURRENT_DATE(), last_updated, DAY) as days_since_update
FROM `province-development.mart.rules_packages_simple`
ORDER BY tax_year DESC, jurisdiction_level, jurisdiction_code;

-- 4. Tax Season Monitoring (October-December)
CREATE OR REPLACE VIEW `province-development.mart.tax_season_monitoring` AS
WITH monthly_stats AS (
  SELECT 
    EXTRACT(YEAR FROM published_date) as year,
    EXTRACT(MONTH FROM published_date) as month,
    'newsroom_releases' as stream_name,
    COUNT(*) as records_count,
    COUNT(CASE WHEN is_inflation_related = true THEN 1 END) as inflation_related_count
  FROM `province-development.raw.newsroom_releases`
  WHERE _fivetran_deleted = false
    AND published_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
  GROUP BY year, month
  
  UNION ALL
  
  SELECT 
    EXTRACT(YEAR FROM published_date) as year,
    EXTRACT(MONTH FROM published_date) as month,
    'revproc_items' as stream_name,
    COUNT(*) as records_count,
    COUNT(CASE WHEN section LIKE '%standard_deduction%' OR section LIKE '%bracket%' THEN 1 END) as inflation_related_count
  FROM `province-development.raw.revproc_items`
  WHERE _fivetran_deleted = false
    AND published_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
  GROUP BY year, month
)
SELECT 
  year,
  month,
  CASE 
    WHEN month IN (10, 11, 12) THEN 'TAX_SEASON'
    ELSE 'OFF_SEASON'
  END as season,
  stream_name,
  records_count,
  inflation_related_count,
  CASE 
    WHEN month IN (10, 11, 12) AND records_count = 0 THEN 'ALERT'
    WHEN month IN (10, 11, 12) AND records_count < 5 THEN 'WARNING'
    ELSE 'OK'
  END as alert_status
FROM monthly_stats
ORDER BY year DESC, month DESC, stream_name;

-- 5. Export Status Monitoring
CREATE OR REPLACE VIEW `province-development.mart.export_status` AS
SELECT 
  package_id,
  tax_year,
  jurisdiction_code,
  last_updated,
  checksum_sha256,
  DATE_DIFF(CURRENT_TIMESTAMP(), updated_at, HOUR) as hours_since_export,
  CASE 
    WHEN DATE_DIFF(CURRENT_TIMESTAMP(), updated_at, HOUR) <= 24 THEN 'FRESH'
    WHEN DATE_DIFF(CURRENT_TIMESTAMP(), updated_at, HOUR) <= 72 THEN 'STALE'
    ELSE 'VERY_STALE'
  END as export_freshness
FROM `province-development.mart.rules_packages_simple`
WHERE is_active = true
ORDER BY hours_since_export DESC;
