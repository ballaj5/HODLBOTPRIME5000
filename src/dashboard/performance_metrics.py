# src/dashboard/performance_metrics.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging

# It's good practice to have a logger in every file
logger = logging.getLogger(__name__)

def load_performance_data():
    """
    Loads evaluated prediction data for performance tracking.

    This function is a placeholder for fetching real, evaluated prediction outcomes
    from a persistent data store like a database. For a real system, you would:
    1. Log every prediction to a database table.
    2. Have a separate process that evaluates if the prediction was correct after
       a certain time period (e.g., did the price move up as predicted?).
    3. Store the outcome (e.g., True/False) in the table.
    4. This function would then query that table to get the data.
    """
    try:
        # For this example, we still read from a log, but now we require
        # the 'is_correct' column to be present from a real evaluation process.
        df = pd.read_json("logs/alerts_log.jsonl", lines=True)
        if df.empty:
            return pd.DataFrame(columns=['timestamp', 'is_correct'])

        # --- THIS IS THE CRITICAL CHANGE ---
        # We no longer generate random data. We check if the evaluation data exists.
        if 'is_correct' not in df.columns:
            logger.warning("Performance data is missing the 'is_correct' column. "
                           "Displaying 0% accuracy. Please run a backtest or evaluation script.")
            # Return an empty frame so the dashboard shows 0 instead of crashing.
            return pd.DataFrame(columns=['timestamp', 'is_correct'])

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df[['timestamp', 'is_correct']]

    except (FileNotFoundError, ValueError):
        # This occurs if the log file doesn't exist or is empty/malformed.
        logger.warning("alerts_log.jsonl not found or is empty. Cannot calculate performance.")
        return pd.DataFrame(columns=['timestamp', 'is_correct'])

def calculate_accuracy_metrics(df: pd.DataFrame):
    """Calculates accuracy for 24-hour, 7-day, and 30-day periods."""
    now = datetime.utcnow()
    periods = {
        "24h": now - timedelta(days=1),
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30)
    }
    metrics = {"24h": 0.0, "7d": 0.0, "30d": 0.0}

    # If the dataframe is empty (either no log or no 'is_correct' column),
    # this will correctly result in all metrics being 0.
    if df.empty:
        return metrics

    for key, start_date in periods.items():
        period_df = df[df['timestamp'] >= start_date]
        if not period_df.empty:
            # Ensure the column is boolean or 0/1 for proper mean calculation
            metrics[key] = period_df['is_correct'].astype(bool).mean() * 100
    return metrics

def render_performance_metrics():
    """Renders the full performance metrics section in Streamlit."""
    st.header("Prediction Accuracy")
    st.caption("Performance of evaluated historical signals")

    df = load_performance_data()
    metrics = calculate_accuracy_metrics(df)

    if df.empty:
        st.warning("No evaluated performance data available.", icon="⚠️")

    # Display metric cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Last 24 Hours", value=f"{metrics['24h']:.1f}%")
    with col2:
        st.metric(label="Last 7 Days", value=f"{metrics['7d']:.1f}%")
    with col3:
        st.metric(label="Last 30 Days", value=f"{metrics['30d']:.1f}%")

    # Display bar chart
    chart_data = pd.DataFrame.from_dict(metrics, orient='index', columns=['Accuracy'])
    st.bar_chart(chart_data, height=300)