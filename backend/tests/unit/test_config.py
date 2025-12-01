"""Unit tests for configuration."""
import os
from pathlib import Path
from src.core.config import (
    PROJECT_ROOT,
    REPO_ROOT,
    MODEL_CHAT,
    MODEL_EMBED,
    TOP_K,
    MAX_RESUME_CTX,
    MAX_USER_CTX,
    DATASET_PATH,
    CHROMA_DIR,
    validate_paths,
)


def test_project_root_exists():
    """Test that PROJECT_ROOT is a valid path."""
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists() or PROJECT_ROOT.parent.exists()


def test_repo_root_exists():
    """Test that REPO_ROOT is a valid path."""
    assert isinstance(REPO_ROOT, Path)
    # REPO_ROOT should be one level up from PROJECT_ROOT
    assert REPO_ROOT == PROJECT_ROOT.parent


def test_model_configs():
    """Test that model configurations are set."""
    assert isinstance(MODEL_CHAT, str)
    assert len(MODEL_CHAT) > 0
    assert isinstance(MODEL_EMBED, str)
    assert len(MODEL_EMBED) > 0


def test_retrieval_configs():
    """Test that retrieval configurations are valid."""
    assert isinstance(TOP_K, int)
    assert TOP_K > 0
    assert isinstance(MAX_RESUME_CTX, int)
    assert MAX_RESUME_CTX > 0
    assert isinstance(MAX_USER_CTX, int)
    assert MAX_USER_CTX > 0


def test_path_configs():
    """Test that path configurations are valid."""
    assert isinstance(DATASET_PATH, Path)
    assert isinstance(CHROMA_DIR, Path)


def test_validate_paths():
    """Test the validate_paths utility function."""
    paths = validate_paths()
    assert isinstance(paths, dict)
    assert "ENV_PATH_exists" in paths
    assert "DATASET_PATH_exists" in paths
    assert "CHROMA_DIR_exists" in paths
    assert "LOG_FILE_parent_exists" in paths
    # All should be boolean values
    for value in paths.values():
        assert isinstance(value, bool)

