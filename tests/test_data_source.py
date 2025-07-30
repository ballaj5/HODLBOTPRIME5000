# tests/test_data_source.py
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
# CORRECTED: Standardized import path to include 'src'
from src.data_fetch.data_source import fetch_ohlcv_data
from datetime import datetime

@patch('src.data_fetch.data_source.ccxt.bybit')
def test_fetch_ohlcv_data_success(mock_bybit):
    """
    Tests successful data fetching by mocking the ccxt exchange object.
    """
    # Arrange
    mock_data = [
        [1672531200000, 16500, 16600, 16400, 16550, 100],
        [1672534800000, 16550, 16700, 16500, 16650, 120],
    ]
    mock_exchange_instance = MagicMock()
    mock_exchange_instance.fetch_ohlcv.return_value = mock_data
    mock_exchange_instance.timeframes = ['1h']
    mock_bybit.return_value = mock_exchange_instance

    # Act
    df = fetch_ohlcv_data(symbol="BTC", timeframe="1h", since=datetime.utcnow())

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'close' in df.columns
    mock_exchange_instance.fetch_ohlcv.assert_called_once()