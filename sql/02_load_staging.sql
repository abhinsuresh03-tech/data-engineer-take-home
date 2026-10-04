-- ============================================================
-- part A: load daily catalog extracts into staging
-- ============================================================
-- run this file from psql from the project root.
--
-- \copy is used instead of server-side copy so the csv files
-- are read from the client machine.
-- ============================================================
TRUNCATE TABLE stg_catalog_extract;

\copy stg_catalog_extract (
    item_code,
    variant_code,
    variant_ref,
    item_name,
    brand_name,
    category_path,
    unit_price,
    color_name,
    size_label,
    stock_status,
    new_in_stock_date
)
from 'catalog_extract_20260922_0600.csv'
with (
    format csv,
    header true
);

update stg_catalog_extract
set
    source_file = 'catalog_extract_20260922_0600.csv',
    loaded_at = timestamp '2026-09-22 06:00:00'
where source_file is null;


\copy stg_catalog_extract (
    item_code,
    variant_code,
    variant_ref,
    item_name,
    brand_name,
    category_path,
    unit_price,
    color_name,
    size_label,
    stock_status,
    new_in_stock_date
)
from 'catalog_extract_20260923_0600.csv'
with (
    format csv,
    header true
);

update stg_catalog_extract
set
    source_file = 'catalog_extract_20260923_0600.csv',
    loaded_at = timestamp '2026-09-23 06:00:00'
where source_file is null;