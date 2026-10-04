select
    parse_date('%y%m%d', event_date) as session_date,

    coalesce(
        (
            select ep.value.string_value
            from unnest(event_params) as ep
            where ep.key = 'source'
        ),
        '(direct)'
    ) as source,

    coalesce(
        (
            select ep.value.string_value
            from unnest(event_params) as ep
            where ep.key = 'medium'
        ),
        '(none)'
    ) as medium,

    count(*) as session_starts

from `project_id.analytics_dataset.events_*`

where event_name = 'session_start'

group by
    session_date,
    source,
    medium

order by
    session_date,
    session_starts desc;