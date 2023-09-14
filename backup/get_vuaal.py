import time
import datetime
import pandas as pd
import os
from dotenv import load_dotenv

# Load credentials from the .env file
load_dotenv()

vanguard_ticker = os.getenv('vanguard_ticker')
period1 = int(time.mktime(datetime.datetime(2019, 5, 14, 23, 59).timetuple()))
period2 = int(time.mktime(datetime.datetime(2023, 8, 25, 23, 59).timetuple()))
interval = '1d'  # 1d, 1m, 1wk

query_string = f'https://query1.finance.yahoo.com/v7/finance/download/{vanguard_ticker}?period1={period1}&period2={period2}&interval={interval}&events=history&includeAdjustedClose=true'

print(query_string)
try:
    df = pd.read_csv(query_string)
    
    # Check if the dataframe is not empty
    if df.empty:
        print("Downloaded data is empty.")
    else:
        #print(df.head())  # Print the first few rows for an overview
        print("Download successful!")
        
        # Ensure the 'data' directory exists; if not, create it
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # Save the DataFrame to a CSV file inside the 'data' directory
        df.to_csv('data/VUAAL.csv', index=False)
except Exception as e:
    print(f"Download failed. Error: {e}")
