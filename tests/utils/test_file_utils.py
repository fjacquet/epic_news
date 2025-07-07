from faker import Faker
from loguru import logger

from epic_news.utils.file_utils import read_file_content, save_json_file

fake = Faker()


def test_read_file_content(mocker):
    # Test that read_file_content reads the content of a file
    mocker.patch("builtins.open", mocker.mock_open(read_data="Test Content"))
    content = read_file_content("test.txt")
    assert content == "Test Content"


def test_save_json_file(mocker):
    # Test that save_json_file saves a dictionary to a JSON file
    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)
    mocker.patch("pathlib.Path.mkdir")
    save_json_file("test.json", {"test_key": "test_value"})
    mock_file.assert_called_once_with(mocker.ANY, "w", encoding="utf-8")


def test_read_file_content_file_not_found_prints_error(caplog):
    """Test that an error message is printed for a non-existent file."""
    logger.add(caplog.handler, format="{message}")
    file_path = "another_non_existent_file.txt"
    read_file_content(file_path)
    assert "Error: File not found at path:" in caplog.text
