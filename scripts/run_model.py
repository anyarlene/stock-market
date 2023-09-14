from stock_data_model import EnvironmentVariables, TimePeriod, YahooFinanceURL, DataFetcher, DataStorage

if __name__ == "__main__":
    # Load environment variables and get ticker
    env_vars = EnvironmentVariables()
    ticker = env_vars.get_ticker()
    print("Ticker:", ticker)



    # Define the time period
    time_period = TimePeriod(2019, 5, 14, 2023, 8, 25)
    time_period.set_interval('1d')

    # Create the Yahoo Finance URL
    url = YahooFinanceURL(ticker, time_period.period1, time_period.period2, time_period.interval)
    print("Generated URL:", url.query_string)
    # Fetch the data
    fetcher = DataFetcher(url)
    df = fetcher.fetch_data()

    # If data is fetched successfully, save it
    if df is not None:
        storage = DataStorage(df)
        storage.save_to_csv()
