import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location("eval_routing", Path("scripts/eval_routing.py"))
eval_routing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_routing)


def test_score_counts_exact_matches():
    assert eval_routing.score([("POEM", "POEM"), ("MENU", "COOKING"), ("PESTEL", "PESTEL")]) == (2, 3)


def test_dataset_covers_every_category():
    from epic_news.models.content_state import CrewCategories

    data = json.loads(Path("scripts/routing_eval_requests.json").read_text(encoding="utf-8"))
    expected = {row["expected"] for row in data}
    categories = set(CrewCategories.to_dict()) - {"UNKNOWN"}
    assert categories <= expected
    assert len(data) >= 25
