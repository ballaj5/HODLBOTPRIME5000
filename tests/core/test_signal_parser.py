# tests/core/test_signal_parser.py
import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.core.signal_parser import SignalParser

@pytest.fixture
def mock_model():
    """Fixture to create a mock prediction model."""
    model = MagicMock()
    # Configure the mock's predict method
    model.predict.return_value = [1] # Default to predicting 'buy'
    return model

@pytest.fixture
def sample_market_data():
    """Fixture to create a sample pandas DataFrame of market data."""
    data = {
        'timestamp': [1672531200000, 1672534800000],
        'open': [16500, 16550],
        'high': [16600, 16700],
        'low': [16400, 16500],
        'close': [16550, 16650],
        'volume': [100, 120],
        'close_time': [1672534799999, 1672538399999] # Example feature to be dropped
    }
    return pd.DataFrame(data)

def test_generate_buy_signal(mock_model, sample_market_data):
    """Tests that a 'buy' signal is generated when model predicts 1."""
    # Arrange
    mock_model.predict.return_value = [1]
    parser = SignalParser(model=mock_model)
    
    # Act
    signal = parser.generate_signal(sample_market_data)
    
    # Assert
    assert signal == 'buy'
    mock_model.predict.assert_called_once()

def test_generate_sell_signal(mock_model, sample_market_data):
    """Tests that a 'sell' signal is generated when model predicts -1."""
    # Arrange
    mock_model.predict.return_value = [-1]
    parser = SignalParser(model=mock_model)
    
    # Act
    signal = parser.generate_signal(sample_market_data)
    
    # Assert
    assert signal == 'sell'
    mock_model.predict.assert_called_once()

def test_generate_hold_signal(mock_model, sample_market_data):
    """Tests that a 'hold' signal is generated when model predicts 0."""
    # Arrange
    mock_model.predict.return_value = [0]
    parser = SignalParser(model=mock_model)
    
    # Act
    signal = parser.generate_signal(sample_market_data)
    
    # Assert
    assert signal == 'hold'
    mock_model.predict.assert_called_once()

def test_hold_signal_on_empty_data(mock_model):
    """Tests that 'hold' is returned if the market data is empty."""
    # Arrange
    parser = SignalParser(model=mock_model)
    empty_df = pd.DataFrame()
    
    # Act
    signal = parser.generate_signal(empty_df)
    
    # Assert
    assert signal == 'hold'
    # Ensure the model was not called with empty data
    mock_model.predict.assert_not_called()

def test_hold_signal_on_prediction_error(mock_model, sample_market_data):
    """Tests that 'hold' is returned if the model's predict method raises an error."""
    # Arrange
    mock_model.predict.side_effect = Exception("Prediction failed")
    parser = SignalParser(model=mock_model)
    
    # Act
    signal = parser.generate_signal(sample_market_data)
    
    # Assert
    assert signal == 'hold'