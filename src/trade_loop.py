# src/trade_loop.py
import asyncio
import pandas as pd
from datetime import datetime, timedelta, timezone
from src.logger import logger
from src.config import config
from src.core.db_manager import DBManager
from src.core.model_validator import load_model
from src.core.order_executor import OrderExecutor
from src.core.signal_parser import SignalParser
from src.data_fetch.data_source import fetch_ohlcv_data

class TradeLoop:
    def __init__(self):
        self.is_running = False
        self.model = load_model(config.MODEL_PATH, config.BACKUP_MODEL_PATH)
        self.db_manager = DBManager(
            host=config.DB_HOST,
            port=config.DB_PORT,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
        self.db_manager.ensure_tables_exist()
        self.order_executor = OrderExecutor(config.BYBIT_API_KEY, config.BYBIT_API_SECRET)
        self.signal_parser = SignalParser(self.model)
        # This will be set by _synchronize_position_state
        self.in_position = False

    def _synchronize_position_state(self):
        """
        RECOMMENDATION: Check the exchange for any open positions upon starting.
        This prevents state desynchronization if the bot restarts.
        """
        try:
            logger.info(f"Synchronizing position state for {config.SYMBOL}...")
            # In a real implementation, you would:
            # 1. Fetch open positions from the exchange via self.order_executor
            #    positions = self.order_executor.get_positions()
            # 2. Check if a position for config.SYMBOL exists.
            #    open_position = next((p for p in positions if p['symbol'] == config.SYMBOL), None)
            # 3. If it exists and its size is > 0, set self.in_position to True.
            #    if open_position and float(open_position['size']) > 0:
            #        self.in_position = True
            #        logger.info(f"Found existing position for {config.SYMBOL}. State set to IN_POSITION.")
            #    else:
            #        self.in_position = False
            # For now, we assume we start with no position.
            self.in_position = False
            logger.info("Starting with no assumed position.")
        except Exception as e:
            logger.error(f"Failed to synchronize position state: {e}. Defaulting to no position.")
            self.in_position = False

    async def wait_for_next_candle(self):
        """
        CORRECTED: Calculates the time until the next candle closes and sleeps.
        This ensures the bot runs in sync with the market's timeframe.
        """
        now = datetime.now(timezone.utc)
        # For '1h' timeframe
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        wait_seconds = (next_hour - now).total_seconds()
        logger.info(f"Next check in {wait_seconds / 60:.2f} minutes at {next_hour.isoformat()}")
        await asyncio.sleep(wait_seconds)

    async def run(self):
        self.is_running = True
        self._synchronize_position_state() # Check for existing positions on startup
        logger.info("Trading bot started. Press Ctrl+C to stop.")

        while self.is_running:
            try:
                logger.info(f"Fetching market data for {config.SYMBOL}...")
                market_data = fetch_ohlcv_data(
                    symbol=config.SYMBOL.split('/')[0],
                    timeframe=config.TIMEFRAME,
                    since=datetime.utcnow() - timedelta(days=5)
                )

                if market_data is None or market_data.empty:
                    logger.warning("Could not fetch market data. Retrying in 60 seconds.")
                    await asyncio.sleep(60)
                    continue

                signal = self.signal_parser.generate_signal(market_data)

                if signal == 'buy' and not self.in_position:
                    logger.info("Buy signal received. Executing trade.")
                    order = await self.order_executor.create_order(
                        config.SYMBOL, 'market', 'buy', config.TRADE_AMOUNT
                    )
                    self.db_manager.log_trade(config.SYMBOL, 'buy', order['price'], config.TRADE_AMOUNT, 'filled')
                    self.in_position = True
                elif signal == 'sell' and self.in_position:
                    logger.info("Sell signal received. Executing trade.")
                    order = await self.order_executor.create_order(
                        config.SYMBOL, 'market', 'sell', config.TRADE_AMOUNT
                    )
                    self.db_manager.log_trade(config.SYMBOL, 'sell', order['price'], config.TRADE_AMOUNT, 'filled')
                    self.in_position = False
                else:
                    logger.info(f"Hold signal received for {config.SYMBOL}. No action taken.")

                await self.wait_for_next_candle() # Use the synchronized wait

            except asyncio.CancelledError:
                self.is_running = False
                logger.info("Trade loop cancelled.")
            except Exception as e:
                logger.error(f"An error occurred in the trade loop: {e}", exc_info=True)
                await asyncio.sleep(60)

        await self.stop()

    async def stop(self):
        logger.info("Stopping trade loop and closing connections...")
        await self.order_executor.close_connection()
        self.db_manager.close()
        logger.info("Bot has been shut down gracefully.")


async def main():
    trade_loop = TradeLoop()
    try:
        await trade_loop.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping bot...")
    finally:
        if trade_loop.is_running:
            await trade_loop.stop()

if __name__ == "__main__":
    asyncio.run(main())