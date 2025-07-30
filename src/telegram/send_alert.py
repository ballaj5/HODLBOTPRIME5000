# src/telegram/send_alert.py
import os
import requests
import json
import sys
from src.config import config
from src.logger import logger
from src.core.db_manager import DBManager
from src.llm.service import generate_commentary
from src.shared.constants import (
    FUTURES_PREDICTION_COINS,
    FUTURES_PREDICTION_TIMEFRAMES,
    FUTURES_PERPETUAL_COINS,
    FUTURES_PERPETUAL_TIMEFRAMES
)

# --- Configuration ---
API_URL = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
ALERT_FLAG_PATH = "/workspace/data/alerts_on.flag" # CORRECTED PATH

def _send_telegram_message(text: str):
    """Sends a formatted message to the configured Telegram chat."""
    payload = {'chat_id': config.TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(API_URL, data=payload, timeout=10)
        response.raise_for_status()
        logger.info("Successfully sent alert to Telegram.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")

def _format_alert(context: dict, alert_type: str, signal: str) -> str:
    """Formats the alert message with details from the prediction context."""
    price = context.get("price_at_prediction")
    price_str = f"${float(price):,.4f}" if price is not None else "N/A"
    llm_insight = context.get('llm_insight', 'Commentary not available.')

    return (
        f"🚨 *{alert_type.upper()} ALERT* 🚨\n\n"
        f"🪙 *Coin:* `{context.get('symbol')}/USDT`\n"
        f"⏳ *Timeframe:* `{context.get('timeframe')}`\n"
        f"💲 *Price at Alert:* `{price_str}`\n"
        f"📈 *Confidence:* `{float(context.get('confidence', 0)):.2f}%`\n"
        f"🎯 *RECOMMENDATION:* `{signal.upper()}`\n\n"
        f"🤖 *AI Rationale:* {llm_insight}"
    )

def send_test_alert():
    """Sends a predefined test alert to confirm connectivity."""
    logger.info("Sending a test alert...")
    test_context = {
        'symbol': 'BTC',
        'timeframe': '1h',
        'confidence': 99.99,
        'price_at_prediction': 65432.10
    }
    test_context['llm_insight'] = generate_commentary(test_context)
    message = _format_alert(test_context, alert_type="Futures Prediction", signal="UP")
    _send_telegram_message(message)
    logger.info("Test alert sent successfully.")

def process_and_send_alerts():
    """
    Main function to fetch unsent predictions from the DB, format,
    and send them as Telegram alerts.
    """
    if not os.path.exists(ALERT_FLAG_PATH):
        logger.info("Telegram alerts are toggled off. Skipping processing.")
        return

    # Connect to the central PostgreSQL database
    db = DBManager()
    try:
        # Fetch all predictions that haven't been sent yet
        unsent_predictions = db.execute_query(
            "SELECT * FROM predictions WHERE sent_to_telegram = FALSE", fetch='all'
        )

        if not unsent_predictions:
            logger.info("No new predictions to send.")
            return

        logger.info(f"Found {len(unsent_predictions)} new predictions to process.")

        for prediction_row in unsent_predictions:
            prediction_dict = dict(prediction_row)

            # Determine the type of alert and signal based on constants
            alert_to_send = None
            symbol = prediction_dict.get('symbol')
            timeframe = prediction_dict.get('timeframe')
            original_signal = prediction_dict.get('signal')

            if timeframe in FUTURES_PREDICTION_TIMEFRAMES and symbol in FUTURES_PREDICTION_COINS:
                alert_to_send = {"alert_type": "Futures Prediction", "signal": original_signal}
            elif timeframe in FUTURES_PERPETUAL_TIMEFRAMES and symbol in FUTURES_PERPETUAL_COINS:
                alert_to_send = {"alert_type": "Futures Perpetual", "signal": "Long" if original_signal == "UP" else "Short"}

            if alert_to_send:
                # Generate LLM commentary if confidence is high
                if prediction_dict.get('confidence', 0) > 70:
                    prediction_dict['llm_insight'] = generate_commentary(prediction_dict)

                # Format and send the message
                alert_message = _format_alert(
                    context=prediction_dict,
                    alert_type=alert_to_send['alert_type'],
                    signal=alert_to_send['signal']
                )
                _send_telegram_message(alert_message)

            # Mark the prediction as sent in the database
            db.execute_query(
                "UPDATE predictions SET sent_to_telegram = TRUE WHERE id = %s",
                (prediction_dict['id'],)
            )
            logger.info(f"Successfully processed and marked prediction ID {prediction_dict['id']} as sent.")

    except Exception as e:
        logger.error(f"Alert processing job failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == '__main__':
    # Allows running `python -m src.telegram.send_alert test`
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        send_test_alert()
    else:
        process_and_send_alerts()