with distinct_channels as (
    select distinct
        channel_group,
        source_medium
    from {{ ref('stg_ga4_daily_traffic') }}
)

select
    concat(lower(replace(channel_group, ' ', '_')), '__', lower(replace(replace(source_medium, ' ', ''), '/', '_'))) as channel_key,
    channel_group,
    source_medium,
    case
        when channel_group = 'Organic Search' then 'pSEO / Organic Search'
        when channel_group = 'Referral' then 'Viral Referral Loop'
        when channel_group = 'Organic Social' then 'Community & Social'
        else 'Direct & Bookmark'
    end as acquisition_type
from distinct_channels
