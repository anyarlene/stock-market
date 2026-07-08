/*
  mart_entry_thresholds
  ---------------------
  Entry point prices at 5, 10, 15, 20, 25, 30 percent below the 52-week high per ETF.
  Used for the threshold bar chart and table in the dashboard.
  Unpivoted to long format so each row is one threshold level.
*/

with raw_thresholds as (
    select * from {{ source('raw', 'decrease_thresholds') }}
),

symbols as (
    select * from {{ source('raw', 'symbols') }}
),

latest_price as (
    select distinct on (ticker)
        ticker,
        close       as latest_close,
        close_eur   as latest_close_eur
    from {{ ref('mart_price_history') }}
    order by ticker, date desc
),

-- Most recent threshold row per symbol
latest_thresholds as (
    select distinct on (symbol_id)
        symbol_id,
        calculation_date,
        high_52week_price,
        decrease_5_price,
        decrease_10_price,
        decrease_15_price,
        decrease_20_price,
        decrease_25_price,
        decrease_30_price
    from raw_thresholds
    order by symbol_id, calculation_date desc
),

-- Unpivot threshold levels to long format
unpivoted as (
    select symbol_id, calculation_date, high_52week_price,  5 as pct_below, decrease_5_price  as threshold_price from latest_thresholds
    union all
    select symbol_id, calculation_date, high_52week_price, 10 as pct_below, decrease_10_price as threshold_price from latest_thresholds
    union all
    select symbol_id, calculation_date, high_52week_price, 15 as pct_below, decrease_15_price as threshold_price from latest_thresholds
    union all
    select symbol_id, calculation_date, high_52week_price, 20 as pct_below, decrease_20_price as threshold_price from latest_thresholds
    union all
    select symbol_id, calculation_date, high_52week_price, 25 as pct_below, decrease_25_price as threshold_price from latest_thresholds
    union all
    select symbol_id, calculation_date, high_52week_price, 30 as pct_below, decrease_30_price as threshold_price from latest_thresholds
),

final as (
    select
        s.ticker,
        s.name          as etf_name,
        s.exchange,
        s.currency      as native_currency,

        u.calculation_date,
        u.high_52week_price,
        u.pct_below,
        u.threshold_price,

        -- Is the current price at or below this threshold? (buying signal)
        case
            when p.latest_close <= u.threshold_price then true
            else false
        end as is_at_or_below_threshold,

        -- Gap between current price and this threshold
        round(p.latest_close - u.threshold_price, 2)                                            as gap_to_threshold,
        round((p.latest_close - u.threshold_price) / nullif(u.threshold_price, 0) * 100, 2)    as gap_to_threshold_pct,

        p.latest_close,
        p.latest_close_eur

    from unpivoted u
    inner join symbols s      on s.id     = u.symbol_id
    left  join latest_price p on p.ticker = s.ticker
    where s.is_active = true
)

select * from final
order by ticker, pct_below
