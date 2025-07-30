# src/core/db_manager.py
import psycopg2
from psycopg2.extras import RealDictCursor
from tenacity import retry, stop_after_attempt, wait_exponential
from src.logger import setup_logger

logger = setup_logger("DBManager")

class DBManager:
    """Manages the connection and queries to the PostgreSQL database."""

    def __init__(self, db_name, db_user, db_pass, db_host, db_port):
        """
        Initializes the DBManager with an explicit database connection string.

        Args:
            db_name (str): Database name.
            db_user (str): Database user.
            db_pass (str): Database password.
            db_host (str): Database host.
            db_port (str): Database port.
        """
        # CORRECTED: The DSN is now built from arguments passed to the constructor.
        self.dsn = f"dbname='{db_name}' user='{db_user}' password='{db_pass}' host='{db_host}' port='{db_port}'"
        self.conn = None
        # The connection is still attempted on initialization.
        self.connect()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
    def connect(self):
        """Establishes a connection to the database."""
        try:
            # If there's an existing connection, close it first.
            if self.conn and not self.conn.closed:
                self.conn.close()

            self.conn = psycopg2.connect(self.dsn)
            logger.info("✅ Connected to PostgreSQL database.")
        except psycopg2.OperationalError as e:
            logger.error(f"❌ Failed to connect to PostgreSQL. Retrying... Error: {e}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("🔌 PostgreSQL connection closed.")

    def execute_query(self, query, params=(), fetch=None):
        """
        Executes a query and returns the result.
        """
        try:
            # Ensure connection is alive before executing.
            if self.conn is None or self.conn.closed:
                logger.warning("Connection was closed. Reconnecting...")
                self.connect()

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                if fetch == 'one':
                    return cursor.fetchone()
                if fetch == 'all':
                    return cursor.fetchall()
        except (psycopg2.DatabaseError, psycopg2.OperationalError) as e:
            logger.error(f"Query failed: {query} | Error: {e}")
            self.conn.rollback()
            # If connection is lost, psycopg2 will close it.
            if isinstance(e, psycopg2.OperationalError):
                logger.warning("Connection may have been lost. It will be re-established on next query.")
            raise

    def ensure_tables_exist(self):
        """Creates all necessary tables if they don't exist."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                symbol TEXT NOT NULL,
                type TEXT NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                status TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                signal TEXT NOT NULL,
                confidence DOUBLE PRECISION NOT NULL,
                sent_to_telegram BOOLEAN DEFAULT FALSE
            );
            """
        ]
        for query in queries:
            self.execute_query(query)
        logger.info("📦 Ensured all required tables exist.")

    def log_trade(self, symbol, trade_type, price, amount, status):
        """Logs a trade into the database."""
        query = """
        INSERT INTO trades (symbol, type, price, amount, status)
        VALUES (%s, %s, %s, %s, %s);
        """
        params = (symbol, trade_type, price, amount, status)
        self.execute_query(query, params)
        logger.info(f"📝 Logged trade: {symbol} {trade_type} {amount} at {price}")

    def log_prediction(self, context):
        """Logs a prediction signal."""
        query = """
        INSERT INTO predictions (symbol, timeframe, signal, confidence)
        VALUES (%s, %s, %s, %s);
        """
        params = (context['symbol'], context['timeframe'], context['signal'], context.get('confidence', 0))
        self.execute_query(query, params)
        logger.info(f"🔮 Logged prediction for {context['symbol']} with {context.get('confidence', 0):.2f}% confidence.")