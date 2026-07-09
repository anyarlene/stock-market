/*
  mart_fx_rates
  -------------
  Historical FX rates to EUR (USD→EUR, GBP→EUR), exposed for the dashboard's
  currency conversion. The app uses EUR as a pivot to display values in EUR,
  USD, or GBP (triangulation, e.g. USD→GBP = (USD→EUR) / (GBP→EUR)).
*/

select
    from_currency,
    to_currency,
    rate_date,
    exchange_rate
from {{ ref('stg_currency_rates') }}
where to_currency = 'EUR'
