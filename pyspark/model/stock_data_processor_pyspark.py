from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os
from dotenv import load_dotenv
import time
import datetime

# Initialize Spark Session
spark = SparkSession.builder.appName("FinanceDataProcessing").getOrCreate()

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

# Note: TimePeriod class remains the same as the original Python code
# as there is no direct equivalent in PySpark

class YahooFinanceURL:
    def __init__(self, ticker, period1, period2, interval):
        BASE_URL = os.getenv('BASE_URL')
        if not BASE_URL:
            raise ValueError("BASE_URL not found in environment variables.")
        self.query_string = f'{BASE_URL}{ticker}?period1={period1}&period2={period2}&interval={interval}&events=history&includeAdjustedClose=true'

# DataStorage class is not directly applicable in PySpark as it deals with local file systems.
# Instead, we can save data using Spark's DataFrame write API. This is a basic example:
class DataStorage:
    SAVE_PATH = "data/"  # Path in HDFS or other supported file system

    def __init__(self, dataframe, ticker):
        self.dataframe = dataframe
        self.filename = f"{ticker.replace('.', '_')}.csv"  # Replacing . with _

    def save_to_csv(self):
        save_location = os.path.join(self.SAVE_PATH, self.filename)
        self.dataframe.write.csv(save_location, mode="overwrite", header=True)

# The DataFetcher class will need significant modifications as Spark does not 
# natively support downloading data from URLs. This functionality would typically 
# be handled outside of Spark, and the resulting data would be loaded into a DataFrame.

# However, if the data is already available in a format that Spark can read (e.g., 
# a CSV file in HDFS or a cloud storage bucket), you can use Spark to load the data:
class DataFetcher:
    def __init__(self, filepath):
        self.filepath = filepath

    def fetch_data(self):
        try:
            df = spark.read.csv(self.filepath, header=True, inferSchema=True)
            if df.count() == 0:
                print("Downloaded data is empty.")
                return None
            else:
                print("Download successful!")
                return df
        except Exception as e:
            print(f"Download failed. Error: {e}")
            return None
