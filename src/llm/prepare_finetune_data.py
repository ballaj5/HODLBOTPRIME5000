# src/llm/prepare_finetune_data.py
import os
import logging
import pandas as pd
from datetime import datetime, timedelta
import argparse

# --- Local & Shared Imports ---
from src.shared.constants import SYMBOLS, ALL_TIMEFRAMES
from src.utils.indicators import compute_indicators
# CORRECTED: Import shared logic from the new data_utils module
from src.llm.data_utils import generate_analysis_and_target, save_finetune_data

# --- Configuration ---
HISTORY_DATA_PATH = "/workspace/data/history"
FINETUNE_OUTPUT_PATH = "/workspace/data/finetuning"
os.makedirs(FINETUNE_OUTPUT_PATH, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_finetune_dataset(days: int):
    """
    Processes local historical data to create a JSONL dataset for fine-tuning an LLM.
    """
    logging.info(f"🚀 Starting dataset creation for the last {days} days of data.")

    finetune_data = []
    start_date = datetime.utcnow() - timedelta(days=days)

    for symbol in SYMBOLS:
        for tf in ALL_TIMEFRAMES:
            path = os.path.join(HISTORY_DATA_PATH, f"{symbol}USDT_{tf}.csv") # Use os.path.join for safety
            if not os.path.exists(path):
                logging.warning(f"File not found, skipping: {path}")
                continue

            try:
                df = pd.read_csv(path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                df_filtered = df[df['timestamp'] >= start_date].copy()

                if len(df_filtered) < 50:
                    logging.warning(f"Insufficient data for {symbol}-{tf} in the last {days} days. Skipping.")
                    continue

                df_with_features = compute_indicators(df_filtered)
                df_with_features['target'] = (df_with_features['close'].shift(-1) > df_with_features['close']).astype(int)
                df_with_features.dropna(inplace=True)

                logging.info(f"Processing {len(df_with_features)} records for {symbol}-{tf}...")

                for _, row in df_with_features.iterrows():
                    instruction_input = (
                        f"Analyze the following market data for {symbol}/USDT on the {tf} timeframe and provide a rationale for the likely price movement:\n"
                        f"- RSI: {row['rsi']:.2f}\n"
                        f"- MACD: {row['macd']:.6f}\n"
                        f"- EMA: {row['ema']:.4f}\n"
                        f"- Current Close Price: {row['close']:.4f}"
                    )

                    # Use the imported function
                    expert_analysis, _ = generate_analysis_and_target(row)

                    finetune_data.append({
                        "instruction": "You are a crypto trading analyst. Your task is to analyze technical indicators and provide a brief, reasoned outlook on the asset's next likely price movement.",
                        "input": instruction_input,
                        "output": expert_analysis
                    })

            except Exception as e:
                logging.error(f"Failed to process {symbol}-{tf}: {e}", exc_info=True)

    # Use the imported save function for a clean exit
    output_filename = f"trading_finetune_dataset_{days}d.jsonl"
    output_filepath = os.path.join(FINETUNE_OUTPUT_PATH, output_filename)
    save_finetune_data(finetune_data, output_filepath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare historical trading data for LLM fine-tuning.")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="The number of past days of data to process for the dataset. Default is 30."
    )
    args = parser.parse_args()

    create_finetune_dataset(args.days)