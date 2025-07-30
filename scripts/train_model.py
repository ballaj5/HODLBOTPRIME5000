# scripts/train_model.py
import os
import logging
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
from ta import add_all_ta_features

# Add project root to path to allow absolute imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Configuration ---
DATA_DIR = "/workspace/data/history"
OUTPUT_DIR = "/workspace/models_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adds technical analysis features and a target column to the dataframe."""
    df = add_all_ta_features(
        df, open="open", high="high", low="low", close="close", volume="volume", fillna=True
    )
    # Target: 1 if next candle's close is higher, -1 if lower/same
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int).replace(0, -1)
    df.dropna(inplace=True)
    return df

def simulate_10m_from_1m(symbol: str) -> pd.DataFrame | None:
    """Generates a 10m dataframe from 1m data if available."""
    try:
        path_1m = os.path.join(DATA_DIR, f"{symbol}USDT_1m.csv")
        if not os.path.exists(path_1m):
            logging.warning(f"1m data for {symbol} not found, cannot simulate 10m.")
            return None

        df_1m = pd.read_csv(path_1m)
        df_1m['timestamp'] = pd.to_datetime(df_1m['timestamp'])
        df_1m.set_index('timestamp', inplace=True)

        df_10m = df_1m.resample('10T').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
        }).dropna().reset_index()

        logging.info(f"Successfully simulated 10m timeframe for {symbol}.")
        return df_10m
    except Exception as e:
        logging.warning(f"10m simulation failed for {symbol}: {e}")
        return None

def train_model(symbol: str, tf: str, df: pd.DataFrame):
    """Trains and saves a single XGBoost model."""
    try:
        features = [c for c in df.columns if c not in ['timestamp', 'target']]
        X = df[features]
        y = df['target']

        if len(df) < 100 or len(y.unique()) < 2:
            logging.warning(f"Skipping {symbol}-{tf} (not enough data or only one class in target).")
            return

        # XGBoost requires target labels to be 0 or 1
        y_train_xgb = y.replace({-1: 0})

        X_train, X_test, y_train, y_test = train_test_split(
            X, y_train_xgb, test_size=0.2, stratify=y_train_xgb, random_state=42
        )

        model = xgb.XGBClassifier(
            objective='binary:logistic',
            use_label_encoder=False,
            eval_metric='logloss',
            tree_method='gpu_hist' # Assumes GPU is available
        )

        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)

        model_path = os.path.join(OUTPUT_DIR, f"{symbol}USDT_{tf}_model.pkl")
        joblib.dump(model, model_path)

        logging.info(f"✅ {symbol}-{tf} model trained and saved. Accuracy: {acc:.4f}")
    except Exception as e:
        logging.error(f"❌ Failed to train {symbol}-{tf}: {e}", exc_info=True)

def train_all():
    """
    Main function to execute a consolidated and efficient training plan.
    """
    logging.info("🚀 Starting consolidated model training cycle...")

    # CORRECTED: A single, non-redundant training plan.
    # Defines exactly which symbol/timeframe pairs to train.
    training_plan = {
        # High-frequency models for all perpetual symbols
        "BTC": ["1m", "5m", "10m", "15m", "30m", "1h", "1d"],
        "ETH": ["1m", "5m", "10m", "15m", "30m", "1h", "1d"],
        "SOL": ["1m", "5m", "10m", "15m", "30m", "1h", "1d"],
        # Other perpetuals with fewer models
        "DOGE": ["5m", "15m", "1h"],
        "XRP": ["5m", "15m", "1h"],
        "ADA": ["5m", "15m", "1h"],
        "WIF": ["1m", "5m", "15m"],
        "1000PEPE": ["1m", "5m", "15m"],
    }

    for symbol, timeframes in training_plan.items():
        logging.info(f"--- Processing symbol: {symbol} ---")
        for tf in timeframes:
            df = None
            # Handle the simulated 10m timeframe differently
            if tf == '10m':
                df = simulate_10m_from_1m(symbol)
            else:
                # Load data from CSV for all other timeframes
                csv_path = os.path.join(DATA_DIR, f"{symbol}USDT_{tf}.csv")
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                else:
                    logging.warning(f"⛔ Data file missing, cannot train model: {csv_path}")

            if df is not None and not df.empty:
                df_features = compute_indicators(df)
                train_model(symbol, tf, df_features)

    logging.info("🏁 Model training cycle finished.")

if __name__ == "__main__":
    train_all()