# tests/core/test_db_manager.py
import pytest
from unittest.mock import patch, MagicMock
from src.core.db_manager import DBManager
import psycopg2 # Import for mocking its exceptions

@pytest.fixture
def db_creds():
    """Provides standard dummy credentials for the DBManager constructor."""
    return ("test_db", "test_user", "test_pass", "localhost", "5432")

@pytest.fixture
def mock_psycopg2_connect():
    """Mocks the psycopg2.connect call to avoid real network connections."""
    with patch('src.core.db_manager.psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_connect, mock_cursor

def test_db_manager_connect_success(mock_psycopg2_connect, db_creds):
    """Tests that the DBManager initializes and calls connect."""
    # Act - CORRECTED: Pass credentials to the constructor
    db_manager = DBManager(*db_creds)
    
    # Assert
    mock_psycopg2_connect[0].assert_called_once()
    assert db_manager.conn is not None

@patch('src.core.db_manager.config') # Mock the config object to avoid dependency
def test_ensure_tables_exist(mock_config, mock_psycopg2_connect, db_creds):
    """Tests that the queries to create tables are executed."""
    # Arrange - CORRECTED: Pass credentials
    db_manager = DBManager(*db_creds)
    mock_cursor = mock_psycopg2_connect[1]

    # Act
    db_manager.ensure_tables_exist()

    # Assert
    assert mock_cursor.execute.call_count == 2
    first_call_args = mock_cursor.execute.call_args_list[0].args[0]
    assert "CREATE TABLE IF NOT EXISTS trades" in first_call_args

def test_log_trade(mock_psycopg2_connect, db_creds):
    """Tests that a trade is logged with the correct SQL and parameters."""
    # Arrange - CORRECTED: Pass credentials
    db_manager = DBManager(*db_creds)
    mock_cursor = mock_psycopg2_connect[1]

    # Act
    db_manager.log_trade("BTC/USDT", "buy", 50000.0, 0.01, "filled")

    # Assert
    mock_cursor.execute.assert_called_once()
    assert "INSERT INTO trades" in mock_cursor.execute.call_args.args[0]
    assert mock_cursor.execute.call_args.args[1] == ("BTC/USDT", "buy", 50000.0, 0.01, "filled")

def test_connection_failure_raises_exception(db_creds):
    """Tests that a connection error during initialization raises an exception."""
    # Arrange
    with patch('src.core.db_manager.psycopg2.connect') as mock_connect:
        mock_connect.side_effect = psycopg2.OperationalError("Test connection error")
        
        # Act & Assert
        with pytest.raises(psycopg2.OperationalError):
            # CORRECTED: Pass credentials
            DBManager(*db_creds)