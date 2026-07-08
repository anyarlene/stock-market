/*
  mart_price_history
  ------------------
  One row per ETF per trading day with both native-currency and EUR prices.
  This is the primary table the dashboard uses for price history charts and KPI cards.
*/

with base as (
    select * from {{ ref('int_etf_eur') }}
),

final as (
    select
        ticker,
        etf_name,
        isin,
        exchange,
        native_currency,
        date,
        open,
        high,
        low,
        close,
        volume,
        open_eur,
        high_eur,
        low_eur,
        close_eur,

        -- Derived daily metrics
        round(close - open, 2)                                          as daily_change,
        round((close - open) / nullif(open, 0) * 100, 2)               as daily_change_pct,
        round(close_eur - open_eur, 2)                                  as daily_change_eur,
        round((close_eur - open_eur) / nullif(open_eur, 0) * 100, 2)   as daily_change_eur_pct,

        -- Rolling 7-day average close (EUR) for smoothing
        round(
            avg(close_eur) over (
                partition by ticker
                order by date
                rows between 6 preceding and current row
            ),
            2
        ) as close_eur_7d_avg

    from base
)

select * from final
order by ticker, date
