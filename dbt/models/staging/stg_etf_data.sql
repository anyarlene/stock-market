with source as (
    select * from {{ source('raw', 'etf_data') }}
),

symbols as (
    select * from {{ source('raw', 'symbols') }}
),

staged as (
    select
        e.id,
        e.symbol_id,
        s.ticker,
        s.name                                  as etf_name,
        s.isin,
        s.exchange,
        s.currency                              as native_currency,
        e.date,
        e.open,
        e.high,
        e.low,
        e.close,
        e.volume,
        e.open_eur,
        e.high_eur,
        e.low_eur,
        e.close_eur,
        e.created_at
    from source e
    inner join symbols s on e.symbol_id = s.id
    where s.is_active = true
)

select * from staged
