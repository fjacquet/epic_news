import json

from epic_news.tools._json_utils import ensure_json_str


def test_ensure_json_str_from_dict():
    s = ensure_json_str({"a": 1})
    assert isinstance(s, str)
    obj = json.loads(s)
    assert obj == {"a": 1}


def test_ensure_json_str_from_text():
    s = ensure_json_str("hello")
    assert isinstance(s, str)
    obj = json.loads(s)
    assert obj == {"result": "hello"}
