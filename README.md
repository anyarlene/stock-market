# stock-market

Processing and Analytics on Stock Market data


`stock_data_model.py`
This script defines the primary classes and methods used to fetch and store stock market data:

#### EnvironmentVariables: 
Loads environment variables and retrieves the ticker symbols.
#### TimePeriod: 
Defines a specific time period for which to retrieve stock data.
#### YahooFinanceURL: 
Generates the Yahoo Finance URL based on a given ticker and time period.
#### DataFetcher: 
Fetches the stock data based on a given Yahoo Finance URL.
#### DataStorage: 
Saves the retrieved stock data to a CSV file.