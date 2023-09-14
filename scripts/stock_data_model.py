import os
import time
import datetime
import pandas as pd
from dotenv import load_dotenv


class EnvironmentVariables:
    def __init__(self):
        load_dotenv()
        self.vanguard_ticker = os.getenv('vanguard_ticker')

    def get_ticker(self):
        return self.vanguard_ticker


class TimePeriod:
    def __init__(self, start_year, start_month, start_day, end_year, end_month, end_day):
        self.period1 = int(time.mktime(datetime.datetime(start_year, start_month, start_day, 23, 59).timetuple()))
        self.period2 = int(time.mktime(datetime.datetime(end_year, end_month, end_day, 23, 59).timetuple()))
        self.interval = '1d'  # Default to daily. Can be modified as needed.

    def set_interval(self, interval):
        if interval in ['1d', '1m', '1wk']:
            self.interval = interval
        else:
            raise ValueError("Invalid interval provided. Acceptable values are '1d', '1m', or '1wk'.")


class YahooFinanceURL:
    BASE_URL = 'https://query1.finance.yahoo.com/v7/finance/download/'

    def __init__(self, ticker, period1, period2, interval):
        self.query_string = f'{self.BASE_URL}{ticker}?period1={period1}&period2={period2}&interval={interval}&events=history&includeAdjustedClose=true'


class DataStorage:
    def __init__(self, dataframe, filename="VUAAL.csv"):
        self.dataframe = dataframe
        self.filename = filename

    def save_to_csv(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        self.dataframe.to_csv(f'data/{self.filename}', index=False)


class DataFetcher:
    def __init__(self, url):
        self.url = url

    def fetch_data(self):
        try:
            df = pd.read_csv(self.url.query_string)
            if df.empty:
                print("Downloaded data is empty.")
                return None
            else:
                print("Download successful!")
                return df
        except Exception as e:
            print(f"Download failed. Error: {e}")
            return None

if __name__ == "__main__":
    time_period = TimePeriod(2019, 5, 14, 2023, 8, 25)  # Creating the time_period object
    url = YahooFinanceURL("VUAA.L", time_period.period1, time_period.period2, time_period.interval)
    print(url.query_string)



