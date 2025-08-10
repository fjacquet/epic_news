"""JSON utilities for tool output standardization.

All tools should return a JSON string. Use `ensure_json_str` to
convert dicts, lists, pydantic models, or arbitrary objects into
UTF-8 JSON strings.
"""

from __future__ import annotations

import json
from typing import Any


def _looks_like_json_string(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    return (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]"))


def ensure_json_str(obj: Any) -> str:
    """Return a JSON string for any input.

    - If `obj` is already a JSON-looking string, return as-is.
    - If `obj` is a string but not JSON-looking, wrap it in {"result": str}.
    - Otherwise json.dumps with ensure_ascii=False and default=str.
    - On failure, return a minimal JSON string with a stringified representation.
    """
    try:
        if isinstance(obj, str):
            return obj if _looks_like_json_string(obj) else json.dumps({"result": obj}, ensure_ascii=False)
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:  # pragma: no cover - absolute fallback
        try:
            return json.dumps({"result": str(obj)}, ensure_ascii=False)
        except Exception:
            return '{"result": "<unserializable>"}'
