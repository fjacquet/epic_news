
from unittest.mock import mock_open
from faker import Faker
from epic_news.utils.html.extractor import extract_html_from_json_output, extract_html_from_directory

fake = Faker()

def test_extract_html_from_json_output(mocker):
    # Test that extract_html_from_json_output extracts HTML from a JSON file
    mocker.patch('builtins.open', mock_open(read_data='{"html": "<h1>Test</h1>"}'))
    mocker.patch('pathlib.Path.exists', return_value=True)
    mocker.patch('pathlib.Path.read_text', return_value='{"html": "<h1>Test</h1>"}')
    mocker.patch('pathlib.Path.write_text')
    assert extract_html_from_json_output("test.json")

def test_extract_html_from_directory(mocker):
    # Test that extract_html_from_directory extracts HTML from all JSON files in a directory
    mocker.patch('pathlib.Path.exists', return_value=True)
    mocker.patch('pathlib.Path.glob', return_value=["test.json"])
    mocker.patch('epic_news.utils.html.extractor.extract_html_from_json_output', return_value=True)
    assert extract_html_from_directory(".", "*.json") == 1
