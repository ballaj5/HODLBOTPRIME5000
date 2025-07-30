# src/core/signal_parser.py
import pandas as pd
from src.logger import logger

class SignalParser:
    def __init__(self, model):
        if model is None:
            raise ValueError("SignalParser cannot be initialized with a None model.")
        self.model = model

    def generate_signal(self, market_data: pd.DataFrame):
        logger.debug("Generating trading signal...")
        if market_data.empty:
            logger.warning("Market data is empty, cannot generate signal.")
            return 'hold'

        try:
            features = market_data.drop(columns=['timestamp'], errors='ignore').iloc[-1:]
            prediction = self.model.predict(features)[0]

            if prediction == 1:
                logger.info("Signal: BUY")
                return 'buy'
            # CORRECTED: The model predicts -1 for down/sell.
            elif prediction == -1: 
                logger.info("Signal: SELL")
                return 'sell'
            else:
                logger.info("Signal: HOLD")
                return 'hold'
        except Exception as e:
            logger.error(f"Error during model prediction: {e}")
            return 'hold'