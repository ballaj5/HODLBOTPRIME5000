# src/llm/data_utils.py
import json
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def generate_analysis_and_target(row: pd.Series) -> (str, str):
    """
    Generates a human-like analysis based on indicator values and determines the target direction.
    This function is now centralized here to be used by any data preparation script.
    """
    analysis_parts = []

    # Analyze RSI
    if row['rsi'] > 70:
        analysis_parts.append(f"RSI is at {row['rsi']:.1f}, indicating the asset may be overbought.")
    elif row['rsi'] < 30:
        analysis_parts.append(f"RSI is at {row['rsi']:.1f}, indicating the asset may be oversold.")
    else:
        analysis_parts.append(f"RSI is neutral at {row['rsi']:.1f}.")

    # Analyze MACD
    if row['macd'] > 0:
        analysis_parts.append("The MACD is above the signal line, suggesting bullish momentum.")
    else:
        analysis_parts.append("The MACD is below the signal line, suggesting bearish momentum.")

    # Analyze Price vs. EMA
    if row['close'] > row['ema']:
        analysis_parts.append(f"The closing price of ${row['close']:.2f} is above its EMA of ${row['ema']:.2f}, which is a positive sign.")
    else:
        analysis_parts.append(f"The closing price of ${row['close']:.2f} is below its EMA of ${row['ema']:.2f}, which is a bearish sign.")

    target_direction = "UP" if row.get('target', 0) == 1 else "DOWN"
    full_analysis = " ".join(analysis_parts)
    full_analysis += f" Based on this combination of factors, the likely short-term price direction is {target_direction}."

    return full_analysis, target_direction

def save_finetune_data(finetune_data: list, output_filepath: str):
    """
    Saves a list of dictionaries to a JSONL file.
    """
    try:
        with open(output_filepath, 'w') as f:
            for entry in finetune_data:
                f.write(json.dumps(entry) + '\n')
        logger.info(f"✅ Successfully created dataset with {len(finetune_data)} entries.")
        logger.info(f"File saved to: {output_filepath}")
    except Exception as e:
        logger.error(f"❌ Failed to save dataset to {output_filepath}: {e}", exc_info=True)