# tests/core/test_order_executor.py
import pytest
from unittest.mock import AsyncMock, patch
from src.core.order_executor import OrderExecutor
import ccxt.async_support as ccxt

# Define dummy credentials to pass to the constructor
TEST_EXCHANGE_ID = "bybit"
TEST_API_KEY = "test_key"
TEST_API_SECRET = "test_secret"

@pytest.fixture
def mock_exchange():
    """Fixture to create a mock CCXT exchange object."""
    mock_ex = AsyncMock(spec=ccxt.bybit) # Using bybit as the spec
    mock_ex.fetch_balance.return_value = {
        'USDT': {'free': 1000.0, 'used': 0.0, 'total': 1000.0}
    }
    mock_ex.create_order.return_value = {
        'id': '12345', 'price': 51000.0, 'amount': 0.01
    }
    return mock_ex

@pytest.mark.asyncio
# CORRECTED: Patch the correct exchange that will be dynamically loaded
@patch('src.core.order_executor.ccxt.bybit')
async def test_fetch_balance_success(mock_bybit, mock_exchange):
    """Tests successful balance fetching."""
    # Arrange
    mock_bybit.return_value = mock_exchange
    # CORRECTED: Pass exchange_id to constructor
    executor = OrderExecutor(exchange_id=TEST_EXCHANGE_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET)
    
    # Act
    balance = await executor.fetch_balance('USDT')
    
    # Assert
    assert balance == 1000.0
    mock_exchange.fetch_balance.assert_called_once()

@pytest.mark.asyncio
@patch('src.core.order_executor.ccxt.bybit')
async def test_create_order_success(mock_bybit, mock_exchange):
    """Tests successful order creation."""
    # Arrange
    mock_bybit.return_value = mock_exchange
    # CORRECTED: Pass exchange_id to constructor
    executor = OrderExecutor(exchange_id=TEST_EXCHANGE_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET)
    
    # Act
    order = await executor.create_order(symbol="BTC/USDT", order_type="market", side="buy", amount=0.01)
    
    # Assert
    assert order['id'] == '12345'
    mock_exchange.create_order.assert_called_once_with("BTC/USDT", "market", "buy", 0.01)

@pytest.mark.asyncio
@patch('src.core.order_executor.ccxt.bybit')
async def test_create_order_network_error_retry(mock_bybit, mock_exchange):
    """Tests that the retry mechanism is triggered on a network error."""
    # Arrange
    mock_exchange.create_order.side_effect = [
        ccxt.NetworkError("Connection failed"), 
        {'id': '12345', 'price': 51000.0, 'amount': 0.01}
    ]
    mock_bybit.return_value = mock_exchange
    # CORRECTED: Pass exchange_id to constructor
    executor = OrderExecutor(exchange_id=TEST_EXCHANGE_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET)

    # Act
    order = await executor.create_order("BTC/USDT", "market", "buy", 0.01)

    # Assert
    assert order is not None
    assert mock_exchange.create_order.call_count == 2