# src/core/model_validator.py
import pickle
import os
import hashlib
from src.logger import logger

def get_file_checksum(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def load_model(model_path, backup_model_path=None):
    path_to_load = None

    if os.path.exists(model_path):
        logger.info(f"Primary model found at {model_path}.")
        path_to_load = model_path
    else:
        logger.warning(f"Primary model not found at {model_path}.")
        if backup_model_path and os.path.exists(backup_model_path):
            logger.info(f"Falling back to backup model at {backup_model_path}.")
            path_to_load = backup_model_path

    if path_to_load:
        try:
            with open(path_to_load, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Model successfully loaded from {path_to_load}.")
            return model
        except (pickle.UnpicklingError, EOFError) as e:
            logger.error(f"Failed to unpickle model from {path_to_load}: {e}")

    raise FileNotFoundError("Critical: No valid model could be loaded. Bot cannot proceed.")