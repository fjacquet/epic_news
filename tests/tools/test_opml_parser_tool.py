import os

import pytest

from src.epic_news.tools.opml_parser_tool import OpmlParserTool


@pytest.fixture
def tool():
    """Provides an instance of the OpmlParserTool."""
    return OpmlParserTool()


def test_successful_parsing(tool):
    """Test that the tool correctly parses a valid OPML file."""
    opml_file_path = os.path.abspath('data/feedly.opml')
    urls = tool._run(opml_file_path=opml_file_path)

    assert isinstance(urls, list)
    assert len(urls) > 0
    assert 'http://xkcd.com/rss.xml' in urls

def test_file_not_found(tool):
    """Test that the tool handles a non-existent file path gracefully."""
    result = tool._run(opml_file_path='non_existent_file.opml')
    assert 'Error: The file was not found' in result

@pytest.fixture
def malformed_opml_file(tmp_path):
    """Creates a temporary malformed OPML file for testing."""
    file_path = tmp_path / "malformed.opml"
    file_path.write_text('<opml><body</opml>')
    return str(file_path)

def test_malformed_xml(tool, malformed_opml_file):
    """Test that the tool handles a malformed XML file."""
    result = tool._run(opml_file_path=malformed_opml_file)
    assert 'Error parsing XML file' in result
