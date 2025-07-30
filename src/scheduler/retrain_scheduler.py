# src/scheduler/retrain_scheduler.py
import os
import logging
import time
import subprocess
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from src.telegram.send_alert import process_and_send_alerts

# --- Logging Setup ---
LOG_PATH = "/workspace/logs/scheduler.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
)
logger = logging.getLogger("Scheduler")

# --- Job Functions ---
def model_retrain_job():
    """Job to retrain the predictive models by running the script."""
    logger.info("🔁 Kicking off scheduled model retraining job...")
    try:
        result = subprocess.run(
            ["python", "-m", "scripts.train_model"],
            capture_output=True,
            text=True,
            check=True,
            cwd="/workspace"
        )
        logger.info("✅ Model retraining job completed successfully.")
        logger.debug("Training script output:\n%s", result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Model retraining job failed with exit code {e.returncode}.")
        logger.error("Error output:\n%s", e.stderr)
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred in the retraining job: {e}", exc_info=True)

def alert_sending_job():
    """Job to check for and send new alerts."""
    logger.info("📨 Kicking off scheduled alert sending job...")
    try:
        process_and_send_alerts()
        logger.info("✅ Alert sending job completed successfully.")
    except Exception as e:
        logger.error(f"❌ Alert sending job failed: {e}", exc_info=True)

# --- Main Scheduler Logic ---
def main():
    """Initializes and runs the scheduler for all background tasks."""
    scheduler = BackgroundScheduler(timezone="UTC")

    # CORRECTED: Read interval from environment variable, with a default
    retrain_minutes = int(os.getenv("RETRAIN_INTERVAL_MINUTES", 360)) # Default to 6 hours
    
    # Schedule jobs to run at regular intervals
    scheduler.add_job(model_retrain_job, 'interval', minutes=retrain_minutes, id='retrain_job')
    scheduler.add_job(alert_sending_job, 'interval', minutes=5, id='alert_job')

    try:
        scheduler.start()
        logger.info(f"✅ Scheduler started. Retraining every {retrain_minutes} minutes. Press Ctrl+C to exit.")
        
        logger.info("Triggering initial runs for all jobs...")
        scheduler.get_job('retrain_job').modify(next_run_time=datetime.now())
        scheduler.get_job('alert_job').modify(next_run_time=datetime.now())
        
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Shutdown signal received. Stopping scheduler...")
    finally:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler has been shut down.")

if __name__ == "__main__":
    main()