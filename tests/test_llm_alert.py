# tests/test_llm_alert.py
import pytest
import os
from unittest.mock import patch, MagicMock

# The function to be tested
from src.telegram.send_alert import process_and_send_alerts

@patch('src.telegram.send_alert.DBManager')
@patch('src.telegram.send_alert._send_telegram_message')
@patch('src.telegram.send_alert.generate_commentary')
def test_sends_alert_for_unsent_prediction(mock_llm, mock_telegram, mock_db_manager):
    """
    Tests that a Telegram message is sent for a new, high-confidence prediction from the DB.
    """
    # --- Arrange ---
    # 1. Mock the return value of the LLM commentary
    mock_llm.return_value = "This is a test commentary."

    # 2. Mock the DBManager to simulate fetching one unsent prediction
    mock_db_instance = MagicMock()
    mock_db_instance.execute_query.side_effect = [
        # First call to execute_query fetches the prediction
        [{'id': 1, 'symbol': 'BTC', 'timeframe': '1h', 'signal': 'UP', 'confidence': 95.0, 'sent_to_telegram': False}],
        # Second call to execute_query updates the row (no return value needed)
        None
    ]
    mock_db_manager.return_value = mock_db_instance

    # 3. Ensure the alert flag file exists so the function doesn't skip
    with patch('os.path.exists', return_value=True):
        # --- Act ---
        process_and_send_alerts()

    # --- Assert ---
    # Check that the DB was queried to fetch unsent predictions
    fetch_query_call = mock_db_instance.execute_query.call_args_list[0]
    assert "SELECT * FROM predictions WHERE sent_to_telegram = FALSE" in fetch_query_call[0][0]

    # Check that the LLM was called because confidence was high
    mock_llm.assert_called_once()

    # Check that the Telegram message was sent
    mock_telegram.assert_called_once()
    sent_text = mock_telegram.call_args[0][0]
    assert "Futures Prediction" in sent_text
    assert "BTC" in sent_text
    assert "95.00%" in sent_text
    assert "test commentary" in sent_text

    # Check that the DB was updated to mark the prediction as sent
    update_query_call = mock_db_instance.execute_query.call_args_list[1]
    assert "UPDATE predictions SET sent_to_telegram = TRUE WHERE id = %s" in update_query_call[0][0]
    assert update_query_call[0][1] == (1,) # Check that the correct ID was updated

@patch('src.telegram.send_alert.DBManager')
@patch('src.telegram.send_alert._send_telegram_message')
def test_does_not_send_when_no_new_predictions(mock_telegram, mock_db_manager):
    """
    Tests that no message is sent if the database returns no new predictions.
    """
    # --- Arrange ---
    # Mock the DBManager to return an empty list
    mock_db_instance = MagicMock()
    mock_db_instance.execute_query.return_value = [] # No unsent predictions
    mock_db_manager.return_value = mock_db_instance

    # Ensure the alert flag file exists
    with patch('os.path.exists', return_value=True):
        # --- Act ---
        process_and_send_alerts()

    # --- Assert ---
    # Check that the Telegram function was NEVER called
    mock_telegram.assert_not_called()