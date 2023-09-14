import os
import time
import datetime
import pandas as pd
from dotenv import load_dotenv


class EnvironmentVariables:
    def __init__(self):
        load_dotenv()

    def get_tickers(self):
        tickers = {
            "vanguard": os.getenv('vanguard_ticker'),
            "xtrackers_health": os.getenv('xtrackers_health'),
            "amundi_emerging_markets": os.getenv('amundi_emerging_markets'),
            "lyxor_dax_de": os.getenv('lyxor_dax_de')
        }
        return tickers


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
    def __init__(self, ticker, period1, period2, interval):
        BASE_URL = os.getenv('BASE_URL')
        print(f"BASE_URL retrieved: {BASE_URL}")  # To check the retrieved BASE_URL
        if not BASE_URL:
            raise ValueError("BASE_URL not found in environment variables.")
        self.query_string = f'{BASE_URL}{ticker}?period1={period1}&period2={period2}&interval={interval}&events=history&includeAdjustedClose=true'


class DataStorage:
    SAVE_PATH = "../data/"  # One level up from 'scripts'

    def __init__(self, dataframe, ticker):
        self.dataframe = dataframe
        self.filename = f"{ticker.replace('.', '_')}.csv"  # Replacing . with _

    def save_to_csv(self):
        save_location = os.path.join(self.SAVE_PATH, self.filename)
        if not os.path.exists(self.SAVE_PATH):
            os.makedirs(self.SAVE_PATH)
        self.dataframe.to_csv(save_location, index=False)
        print(f"Saved data to: {save_location}")


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
