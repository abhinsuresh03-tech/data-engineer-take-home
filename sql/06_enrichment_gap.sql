-- ============================================================
-- part A: enrichment gap analysis
--
-- never_attempted:
--   no enrichment attempt exists for the variant.
--
-- always_failed:
--   attempts exist, but none succeeded.
--
-- enriched:
--   at least one successful attempt exists.
-- ============================================================

drop table if exists enrichment_gap;

create table enrichment_gap as

select
    vs.variant_code,

    case
        when count(ve.variant_code) = 0
            then 'never_attempted'

        when count(ve.variant_code) filter (
            where ve.status = 'success'
        ) = 0
            then 'always_failed'

        else 'enriched'
    end as enrichment_status

from variant_summary vs

left join variant_enrichment ve
    on vs.variant_code = ve.variant_code

group by
    vs.variant_code;