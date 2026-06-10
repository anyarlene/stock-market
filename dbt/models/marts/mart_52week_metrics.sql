/*
  mart_52week_metrics
  -------------------
  Latest 52-week high/low metrics per ETF, joined with the most recent price.
  Used for KPI cards and summary table in Metabase.
*/

with metrics as (
    select * from {{ source('raw', 'fifty_two_week_metrics') }}
),

symbols as (
    select * from {{ source('raw', 'symbols') }}
),

price_history as (
    select * from {{ ref('mart_price_history') }}
),

-- Most recent calculation per symbol
latest_metrics as (
    select distinct on (symbol_id)
        symbol_id,
        calculation_date,
        high_52week,
        low_52week,
        high_date,
        low_date
    from metrics
    order by symbol_id, calculation_date desc
),

-- Most recent price per ticker
latest_price as (
    select distinct on (ticker)
        ticker,
        date        as latest_price_date,
        close       as latest_close,
        close_eur   as latest_close_eur,
        daily_change_eur_pct
    from price_history
    order by ticker, date desc
),

final as (
    select
        s.ticker,
        s.name          as etf_name,
        s.isin,
        s.exchange,
        s.currency      as native_currency,

        -- 52-week metrics (native currency)
        m.high_52week,
        m.low_52week,
        m.high_date,
        m.low_date,
        m.calculation_date,

        -- Range spread
        round(m.high_52week - m.low_52week, 2)                                              as range_52week,
        round((m.high_52week - m.low_52week) / nullif(m.low_52week, 0) * 100, 2)            as range_52week_pct,

        -- Latest price
        p.latest_price_date,
        p.latest_close,
        p.latest_close_eur,
        p.daily_change_eur_pct,

        -- Distance from 52-week high
        round(m.high_52week - p.latest_close, 2)                                            as distance_from_high,
        round((m.high_52week - p.latest_close) / nullif(m.high_52week, 0) * 100, 2)        as pct_below_52w_high,

        -- Distance from 52-week low
        round(p.latest_close - m.low_52week, 2)                                             as distance_from_low,
        round((p.latest_close - m.low_52week) / nullif(m.low_52week, 0) * 100, 2)          as pct_above_52w_low

    from latest_metrics m
    inner join symbols s       on s.id     = m.symbol_id
    left  join latest_price p  on p.ticker = s.ticker
    where s.is_active = true
)

select * from final
order by ticker
