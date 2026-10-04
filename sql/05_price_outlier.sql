-- ============================================================
-- part A: category-level price outlier detection
--
-- A variant is an outlier when its price is more than
-- 2 population standard deviations from its category mean.
--
-- null prices are excluded from the statistics.
-- categories with zero standard deviation are not flagged.
-- ============================================================

drop table if exists price_outliers;

create table price_outliers as

with category_stats as (
    select
        variant_code,
        item_code,
        category_path,
        unit_price,

        avg(unit_price) over (
            partition by category_path
        ) as category_mean_price,

        stddev_pop(unit_price) over (
            partition by category_path
        ) as category_stddev_price

    from variant_summary
    where unit_price is not null
)

select
    variant_code,
    item_code,
    category_path,
    unit_price,
    category_mean_price,
    category_stddev_price,

    case
        when category_stddev_price is null
             or category_stddev_price = 0
            then false

        when abs(unit_price - category_mean_price)
             > 2 * category_stddev_price
            then true

        else false
    end as is_price_outlier

from category_stats;