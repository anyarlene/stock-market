/*
  Ensures every price row has EUR-converted columns.
  If the ETL has already populated open_eur/close_eur (the common path), those values are
  kept as-is. For any remaining nulls the most-recent available exchange rate is used as
  a fallback so downstream marts always have EUR figures.
*/

with etf as (
    select * from {{ ref('stg_etf_data') }}
),

rates as (
    select * from {{ ref('stg_currency_rates') }}
),

-- Latest available rate per currency pair (fallback only)
latest_rates as (
    select distinct on (from_currency, to_currency)
        from_currency,
        to_currency,
        exchange_rate
    from rates
    order by from_currency, to_currency, rate_date desc
),

enriched as (
    select
        e.id,
        e.symbol_id,
        e.ticker,
        e.etf_name,
        e.isin,
        e.exchange,
        e.native_currency,
        e.date,
        e.open,
        e.high,
        e.low,
        e.close,
        e.volume,

        -- EUR values: use ETL-populated value; fall back to same-day rate; then latest rate
        coalesce(
            e.open_eur,
            case when e.native_currency != 'EUR'
                 then round(e.open * r_day.exchange_rate, 2) end,
            case when e.native_currency != 'EUR'
                 then round(e.open * r_latest.exchange_rate, 2) end,
            e.open
        ) as open_eur,

        coalesce(
            e.high_eur,
            case when e.native_currency != 'EUR'
                 then round(e.high * r_day.exchange_rate, 2) end,
            case when e.native_currency != 'EUR'
                 then round(e.high * r_latest.exchange_rate, 2) end,
            e.high
        ) as high_eur,

        coalesce(
            e.low_eur,
            case when e.native_currency != 'EUR'
                 then round(e.low * r_day.exchange_rate, 2) end,
            case when e.native_currency != 'EUR'
                 then round(e.low * r_latest.exchange_rate, 2) end,
            e.low
        ) as low_eur,

        coalesce(
            e.close_eur,
            case when e.native_currency != 'EUR'
                 then round(e.close * r_day.exchange_rate, 2) end,
            case when e.native_currency != 'EUR'
                 then round(e.close * r_latest.exchange_rate, 2) end,
            e.close
        ) as close_eur

    from etf e
    -- Same-day rate (exact match)
    left join rates r_day
        on r_day.from_currency = e.native_currency
       and r_day.to_currency   = 'EUR'
       and r_day.rate_date     = e.date
    -- Latest available rate (fallback)
    left join latest_rates r_latest
        on r_latest.from_currency = e.native_currency
       and r_latest.to_currency   = 'EUR'
)

select * from enriched
