"""Tests for path utilities."""

import pathlib

import pytest

from epic_news.utils.path_utils import (
    get_project_root,
    get_template_dir,
    validate_output_path,
)


def test_get_project_root():
    """Test that get_project_root returns the correct project root directory."""
    project_root = get_project_root()
    assert isinstance(project_root, pathlib.Path)
    assert (project_root / "pyproject.toml").exists()
    assert "epic_news" in str(project_root)


def test_get_template_dir():
    """Test that get_template_dir returns the correct templates directory."""
    template_dir = get_template_dir()
    assert isinstance(template_dir, str)
    assert (pathlib.Path(template_dir) / "universal_report_template.html").exists()


def test_validate_output_path_valid():
    """Test that validate_output_path accepts valid paths."""
    project_root = get_project_root()
    valid_path = project_root / "output" / "test.txt"
    validate_output_path(str(valid_path))  # Should not raise


def test_validate_output_path_invalid_nested_users():
    """Test that validate_output_path raises ValueError for nested /Users/."""
    invalid_path = "/Users/test/Users/fjacquet/Projects/crews/epic_news/output/test.txt"
    with pytest.raises(ValueError, match="Invalid output path"):
        validate_output_path(invalid_path)


def test_validate_output_path_outside_project():
    """Test that validate_output_path raises ValueError for paths outside the project."""
    invalid_path = "/tmp/test.txt"
    with pytest.raises(ValueError, match="is outside the project directory"):
        validate_output_path(invalid_path)


def test_validate_output_path_empty():
    """Test that validate_output_path raises ValueError for empty paths."""
    with pytest.raises(ValueError, match="Output path cannot be empty"):
        validate_output_path("")
