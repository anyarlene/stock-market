import sys
import unittest
from unittest.mock import patch
import pandas as pd
from stock_data_model import EnvironmentVariables, TimePeriod, YahooFinanceURL, DataStorage, DataFetcher

# Test class for EnvironmentVariables
class TestEnvironmentVariables(unittest.TestCase):

    @patch('stock_data_model.os.getenv')
    def test_environment_variables_loaded(self, mock_getenv):
        """ Ensure environment variables are loaded correctly 
            and verify that the get_tickers method returns the correct dictionary structure with expected tickers """
        
        mock_getenv.side_effect = ['VANGUARD_TICKER', 'XTRACKERS_HEALTH', 'AMUNDI_EM', 'LYXOR_DAX']
        env = EnvironmentVariables()
        tickers = env.get_tickers()
        self.assertEqual(tickers, {
            "vanguard": 'VANGUARD_TICKER',
            "xtrackers_health": 'XTRACKERS_HEALTH',
            "amundi_emerging_markets": 'AMUNDI_EM',
            "lyxor_dax_de": 'LYXOR_DAX'
        })

# Test class for TimePeriod
class TestTimePeriod(unittest.TestCase):

    def test_correct_timestamp_generation(self):
        """ Validate that the correct timestamp is generated for the given start and end dates."""
        time_period = TimePeriod(2020, 1, 1, 2021, 1, 1)
        self.assertEqual(time_period.period1, 1577836800)
        self.assertEqual(time_period.period2, 1609459199)

# Test class for YahooFinanceURL
class TestYahooFinanceURL(unittest.TestCase):

    @patch('your_module.os.getenv')
    def test_base_url_retrieval(self, mock_getenv):

        """ Ensure the BASE_URL is correctly retrieved from the environment variables """

        # Adjusting the return value to the actual BASE_URL
        mock_getenv.return_value = 'https://query1.finance.yahoo.com/v7/finance/download/'
        yf_url = YahooFinanceURL('TICKER', 1577836800, 1609459199, '1d')
        self.assertIn('https://query1.finance.yahoo.com/v7/finance/download/', yf_url.query_string)


# Test class for DataStorage
class TestDataStorage(unittest.TestCase):

    @patch('your_module.os.path.exists')
    @patch('your_module.os.makedirs')
    @patch('your_module.pd.DataFrame.to_csv')
    def test_correct_file_path(self, mock_to_csv, mock_makedirs, mock_exists):

        """ Verify the correct file path and filename are generated for CSV storage """

        mock_exists.return_value = False
        df = pd.DataFrame()
        storage = DataStorage(df, 'test.csv')
        storage.save_to_csv()
        mock_makedirs.assert_called_with('data/')
        mock_to_csv.assert_called_with('data/test.csv', index=False)

# Test class for DataFetcher
class TestDataFetcher(unittest.TestCase):

    @patch('your_module.pd.read_csv')
    def test_fetch_data_success(self, mock_read_csv):

        """ Test fetch_data method with a valid URL to ensure data is fetched and returned as a DataFrame """

        mock_read_csv.return_value = pd.DataFrame({'test': [1, 2, 3]})
        fetcher = DataFetcher(YahooFinanceURL('TICKER', 1577836800, 1609459199, '1d'))
        result = fetcher.fetch_data()
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

# Running the test suite
if __name__ == '__main__':
    unittest.main()
