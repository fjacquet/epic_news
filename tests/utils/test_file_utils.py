import os

import pytest

from epic_news.utils.file_utils import read_file_content


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with some content."""
    file_path = tmp_path / "test_file.txt"
    content = "Hello, this is a test file for epic_news! 🚀"
    file_path.write_text(content, encoding="utf-8")
    return file_path, content


def test_read_file_content_absolute_path(temp_file):
    """Test reading a file using its absolute path."""
    file_path, expected_content = temp_file
    assert read_file_content(str(file_path)) == expected_content


def test_read_file_content_relative_path(temp_file, tmp_path):
    """Test reading a file using its relative path."""
    _, expected_content = temp_file
    # Change CWD to the temp directory to test relative paths
    os.chdir(tmp_path)
    assert read_file_content("test_file.txt") == expected_content


def test_read_file_content_file_not_found():
    """Test that an empty string is returned for a non-existent file."""
    assert read_file_content("non_existent_file.txt") == ""


import logging
from unittest.mock import mock_open
from faker import Faker
from epic_news.utils.file_utils import read_file_content, save_json_file

fake = Faker()

def test_read_file_content(mocker):
    # Test that read_file_content reads the content of a file
    mocker.patch("builtins.open", mock_open(read_data="Test Content"))
    content = read_file_content("test.txt")
    assert content == "Test Content"

def test_save_json_file(mocker):
    # Test that save_json_file saves a dictionary to a JSON file
    mock_file = mock_open()
    mocker.patch("builtins.open", mock_file)
    mocker.patch("pathlib.Path.mkdir")
    save_json_file("test.json", {"test_key": "test_value"})
    mock_file.assert_called_once_with(mocker.ANY, "w", encoding="utf-8")

def test_read_file_content_file_not_found_prints_error(caplog):
    """Test that an error message is printed for a non-existent file."""
    file_path = "another_non_existent_file.txt"
    with caplog.at_level(logging.ERROR):
        read_file_content(file_path)
    assert "Error: File not found at path:" in caplog.text
