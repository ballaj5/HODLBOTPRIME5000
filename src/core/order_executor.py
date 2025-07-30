# src/core/order_executor.py
import ccxt.async_support as ccxt
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.logger import logger

RETRYABLE_EXCEPTIONS = (
    ccxt.NetworkError,
    ccxt.ExchangeError,
    ccxt.RequestTimeout,
)

class OrderExecutor:
    def __init__(self, exchange_id: str, api_key: str, api_secret: str):
        """
        Initializes the OrderExecutor with explicit configuration.

        Args:
            exchange_id (str): The CCXT-compatible exchange ID (e.g., 'bybit').
            api_key (str): The API key for the exchange.
            api_secret (str): The API secret for the exchange.
        """
        # CORRECTED: The exchange ID is now passed in during initialization.
        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"Exchange '{exchange_id}' is not supported by ccxt.")

        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'spot'},
        })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=lambda retry_state: logger.warning(f"Retrying API call due to {retry_state.outcome.exception()}. Attempt #{retry_state.attempt_number}")
    )
    async def fetch_balance(self, currency='USDT'):
        logger.info(f"Fetching balance for {currency}...")
        balance = await self.exchange.fetch_balance()
        return balance.get(currency, {}).get('free', 0.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS)
    )
    async def create_order(self, symbol, order_type, side, amount):
        logger.info(f"Creating {side} {order_type} order for {amount} {symbol}...")
        try:
            order = await self.exchange.create_order(symbol, order_type, side, amount)
            logger.info(f"Successfully placed order: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise

    async def close_connection(self):
        if self.exchange:
            await self.exchange.close()
            logger.info("Exchange connection closed.")