from stock_data_model import EnvironmentVariables, TimePeriod, YahooFinanceURL, DataFetcher, DataStorage

if __name__ == "__main__":
    # Load environment variables and get tickers
    env_vars = EnvironmentVariables()
    tickers = env_vars.get_tickers()

    # Define the time period
    time_period = TimePeriod(2019, 5, 14, 2023, 8, 25)
    time_period.set_interval('1d')

    for ticker_name, ticker in tickers.items():
        print("Ticker:", ticker)

        # Create the Yahoo Finance URL
        url = YahooFinanceURL(ticker, time_period.period1, time_period.period2, time_period.interval)
        print(f"Generated URL for {ticker_name}:", url.query_string)

        # Fetch the data
        fetcher = DataFetcher(url)
        df = fetcher.fetch_data()

        # If data is fetched successfully, save it
        if df is not None:
            storage = DataStorage(df, ticker)
            storage.save_to_csv()
