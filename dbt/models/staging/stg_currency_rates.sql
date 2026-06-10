with source as (
    select * from {{ source('raw', 'currency_rates') }}
),

staged as (
    select
        id,
        from_currency,
        to_currency,
        rate_date,
        exchange_rate,
        created_at
    from source
    where exchange_rate > 0
)

select * from staged
