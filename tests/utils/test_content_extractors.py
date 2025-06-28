import pytest

from epic_news.utils.content_extractors import (
    extract_code_from_markdown,
    extract_final_answer,
    extract_html_from_string,
    extract_json_from_markdown,
)


# Test cases for extract_json_from_markdown
@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "Here is some JSON: ```json\n{\"key\": \"value\"}```",
            '{\"key\": \"value\"}',
        ),
        ("No JSON here", None),
        ("```json\n{\"a\": 1}``` and ```json\n{\"b\": 2}```", '{\"a\": 1}'),  # First match
        ("Malformed: ```json\n{\"key\": \"value\"```", '{\"key\": \"value\"'), # Tolerates missing closing backticks
    ],
)
def test_extract_json_from_markdown(text, expected):
    assert extract_json_from_markdown(text) == expected


# Test cases for extract_html_from_string
@pytest.mark.parametrize(
    "text, expected",
    [
        (
            '<html><head></head><body><h1>Title</h1></body></html>',
            '<html><head></head><body><h1>Title</h1></body></html>',
        ),
        (
            'Some text before <html><body>Content</body></html> and after.',
            '<html><body>Content</body></html>',
        ),
        ("No HTML here", None),
        ("<html>mismatched tags</html>", "<html>mismatched tags</html>"),
    ],
)
def test_extract_html_from_string(text, expected):
    assert extract_html_from_string(text) == expected


# Test cases for extract_code_from_markdown
@pytest.mark.parametrize(
    "text, language, expected",
    [
        (
            "```python\nprint('hello')\n```",
            "python",
            "print('hello')",
        ),
        (
            "Some text and then ```javascript\nconsole.log('hi');\n```",
            "javascript",
            "console.log('hi');",
        ),
        ("No code block", "python", None),
        ("```\nraw block\n```", "", "raw block"),
    ],
)
def test_extract_code_from_markdown(text, language, expected):
    assert extract_code_from_markdown(text, language) == expected


# Test cases for extract_final_answer
@pytest.mark.parametrize(
    "text, expected",
    [
        (
            'Here is my thought process...\n\nFinal Answer: The answer is 42.',
            'The answer is 42.',
        ),
        (
            'Final Answer:This is it.',
            'This is it.',
        ),
        (
            'No final answer here.',
            None,
        ),
        (
            'FINAL ANSWER: Case-insensitive check.',
            'Case-insensitive check.',
        ),
        (
            'Another thought.\nFinal Answer:  With extra spaces.  ',
            'With extra spaces.',
        ),
    ],
)
def test_extract_final_answer(text, expected):
    assert extract_final_answer(text) == expected
