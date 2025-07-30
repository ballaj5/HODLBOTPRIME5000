# src/llm/prepare_external_finetune_data.py
import os
import logging
import pandas as pd
import argparse
from datasets import load_dataset

# --- Local & Shared Imports ---
from src.utils.indicators import compute_indicators
# CORRECTED: Import shared logic from the new data_utils module
from src.llm.data_utils import generate_analysis_and_target, save_finetune_data

# --- Configuration ---
FINETUNE_OUTPUT_PATH = "/workspace/data/finetuning"
os.makedirs(FINETUNE_OUTPUT_PATH, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_dataset_from_hf(max_rows: int):
    """
    Downloads the sebdg/crypto_data dataset, processes it, and saves it as a JSONL file.

    Args:
        max_rows (int): The maximum number of rows to process from the dataset.
    """
    logging.info("🚀 Downloading 'sebdg/crypto_data' from Hugging Face Hub...")

    try:
        dataset = load_dataset("sebdg/crypto_data", split='train', streaming=True)
        dataset_sample = dataset.take(max_rows)
        df = pd.DataFrame(list(dataset_sample))
        logging.info(f"Successfully downloaded and sampled {len(df)} rows.")

    except Exception as e:
        logging.error(f"❌ Failed to download or process dataset from Hugging Face: {e}", exc_info=True)
        return

    finetune_data = []

    try:
        df_with_features = compute_indicators(df.copy())
        df_with_features['target'] = (df_with_features['close'].shift(-1) > df_with_features['close']).astype(int)
        df_with_features.dropna(inplace=True)

        logging.info(f"Processing {len(df_with_features)} records for the fine-tuning dataset...")

        for _, row in df_with_features.iterrows():
            instruction_input = (
                f"Analyze the following market data for {row.get('symbol', 'the asset')} and provide a rationale for the likely price movement:\n"
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
        logging.error(f"Failed during feature engineering: {e}", exc_info=True)
        return

    # Use the imported save function for a clean exit
    output_filename = "external_finetune_dataset.jsonl"
    output_filepath = os.path.join(FINETUNE_OUTPUT_PATH, output_filename)
    save_finetune_data(finetune_data, output_filepath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare external Hugging Face dataset for LLM fine-tuning.")
    parser.add_argument(
        "--max_rows",
        type=int,
        default=50000,
        help="The maximum number of rows to process from the dataset. Default is 50,000."
    )
    args = parser.parse_args()

    create_dataset_from_hf(args.max_rows)