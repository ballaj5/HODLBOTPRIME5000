# tests/core/test_model_validator.py
import pytest
import pickle
from pathlib import Path
from src.core.model_validator import load_model

@pytest.fixture
def dummy_models(tmp_path: Path):
    """
    Fixture to create dummy model files in a temporary directory.
    - A valid primary model.
    - A valid backup model.
    - A corrupted model file.
    """
    primary_path = tmp_path / "model.pkl"
    backup_path = tmp_path / "backup_model.pkl"
    corrupt_path = tmp_path / "corrupt.pkl"
    
    # Create a simple dummy model object (e.g., a dictionary)
    valid_model_data = {"type": "valid"}
    
    # Write the valid primary and backup models
    with open(primary_path, "wb") as f:
        pickle.dump(valid_model_data, f)
    with open(backup_path, "wb") as f:
        pickle.dump({"type": "backup"}, f)
    
    # Write a corrupted file (e.g., just text)
    with open(corrupt_path, "w") as f:
        f.write("this is not a pickle file")
        
    return {"primary": primary_path, "backup": backup_path, "corrupt": corrupt_path}

def test_load_primary_model_success(dummy_models):
    """Tests loading a valid primary model."""
    model = load_model(dummy_models["primary"], dummy_models["backup"])
    assert model is not None
    assert model["type"] == "valid"

def test_fallback_to_backup_model_when_primary_is_missing(dummy_models):
    """Tests that the system falls back to the backup if the primary is not found."""
    non_existent_path = Path("non_existent_model.pkl")
    model = load_model(non_existent_path, dummy_models["backup"])
    assert model is not None
    assert model["type"] == "backup"

def test_load_model_fails_if_no_models_exist(dummy_models):
    """Tests that a FileNotFoundError is raised if no models are found."""
    with pytest.raises(FileNotFoundError, match="Critical: No model could be loaded"):
        load_model("non_existent.pkl", "also_non_existent.pkl")

def test_load_model_fails_on_corrupt_primary_and_no_backup(dummy_models):
    """Tests that a FileNotFoundError is raised if the primary is corrupt and no backup exists."""
    with pytest.raises(FileNotFoundError): # Will bubble up after logging the pickle error
        load_model(dummy_models["corrupt"])