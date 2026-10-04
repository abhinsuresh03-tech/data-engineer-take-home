-- ============================================================
-- part A: current variant summary
-- latest record wins for each variant_code.
-- window functions calculate rank and variant count per item.
-- ============================================================

truncate table variant_summary;

with latest_variants as (
    select
        *,
        row_number() over (
            partition by variant_code
            order by loaded_at desc
        ) as latest_rank
    from stg_catalog_extract
),
current_variants as (
    select
        variant_code,
        item_code,
        variant_ref,
        item_name,
        brand_name,
        category_path,
        unit_price,
        color_name,
        size_label,
        stock_status,

        row_number() over (
            partition by item_code
            order by variant_code
        ) as variant_rank_in_item,

        count(*) over (
            partition by item_code
        ) as variants_for_item

    from latest_variants
    where latest_rank = 1
)

insert into variant_summary (
    variant_code,
    item_code,
    variant_ref,
    item_name,
    brand_name,
    category_path,
    unit_price,
    color_name,
    size_label,
    stock_status,
    variant_rank_in_item,
    variants_for_item,
    summarized_at
)
select
    variant_code,
    item_code,
    variant_ref,
    item_name,
    brand_name,
    category_path,
    unit_price,
    color_name,
    size_label,
    stock_status,
    variant_rank_in_item,
    variants_for_item,
    current_timestamp
from current_variants;