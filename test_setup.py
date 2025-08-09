from src.stock_data_model import EnvironmentVariables
from pyspark.sql import SparkSession

def test_env_variables():
    env = EnvironmentVariables()
    tickers = env.get_tickers()
    print("Environment variables loaded successfully:")
    for key, value in tickers.items():
        print(f"{key}: {value}")

def test_spark_session():
    print("\nTesting Spark setup...")
    try:
        spark = SparkSession.builder.appName("TestSetup").getOrCreate()
        print("Spark session created successfully!")
        spark.stop()
    except Exception as e:
        print(f"Error creating Spark session: {e}")

if __name__ == "__main__":
    print("Testing project setup...")
    test_env_variables()
    test_spark_session()
    print("\nSetup test complete!")