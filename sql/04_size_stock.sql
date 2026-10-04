-- ============================================================
-- part A: item-level size and stock summary
-- A product is considered a new arrival when at least one
-- current variant entered stock within the last 30 days.
-- ============================================================

drop table if exists item_size_stock_summary;

create table item_size_stock_summary as
select
    item_code,

    string_agg(
        distinct size_label,
        ', ' order by size_label
    ) filter (
        where size_label is not null
    ) as available_sizes,

    string_agg(
        distinct stock_status,
        ', ' order by stock_status
    ) filter (
        where stock_status is not null
    ) as stock_statuses,

    bool_or(
        new_in_stock_date >= current_date - interval '30 days'
    ) as is_new_arrival

from (
    select distinct on (variant_code)
        variant_code,
        item_code,
        size_label,
        stock_status,
        new_in_stock_date
    from stg_catalog_extract
    order by variant_code, loaded_at desc
) latest_variants

group by item_code;