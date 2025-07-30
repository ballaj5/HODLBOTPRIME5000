# tests/test_pipeline.py
import os
import unittest
from unittest.mock import patch
import pandas as pd

# CORRECTED: Import the main function from the actual script to be tested
from src.data_fetch.fetch_futures_data import main as fetch_data_main 
from src.telegram.send_alert import send_test_alert
from src.shared.constants import SYMBOLS

class TestBotPipeline(unittest.TestCase):
    @patch('src.telegram.send_alert.requests.post')
    def test_telegram_alert(self, mock_post):
        """Test sending a Telegram alert."""
        mock_post.return_value.raise_for_status = lambda: None
        send_test_alert()
        self.assertTrue(mock_post.called)
        
    @patch('src.data_fetch.data_source.fetch_ohlcv_data')
    @patch('pandas.DataFrame.to_csv') # Mock the file writing
    def test_data_fetch_pipeline(self, mock_to_csv, mock_fetch_ohlcv):
        """Test the data fetching pipeline calls the CSV writing function correctly."""
        # Arrange: Mock the data fetching call to return some dummy data
        mock_fetch_ohlcv.return_value = pd.DataFrame({
            'timestamp': [1672531200000], 'open': [60000], 'high': [61000], 
            'low': [59000], 'close': [60500], 'volume': [100]
        })
        
        # Act: Run the main data fetching process
        fetch_data_main()
        
        # Assert: Verify that to_csv was called for the expected files
        self.assertGreater(mock_to_csv.call_count, 0)
        
        # Check if one of the calls was for a specific, expected file path
        first_call_path = mock_to_csv.call_args_list[0].args[0]
        self.assertIn("/workspace/data/history/", first_call_path) # CORRECTED PATH
        self.assertIn("BTCUSDT_1m.csv", first_call_path)


if __name__ == '__main__':
    unittest.main()