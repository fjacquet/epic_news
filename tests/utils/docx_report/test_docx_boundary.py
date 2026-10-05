import os

import pytest

from epic_news.utils.docx_report.docx_builder import build_docx


def test_build_docx_refuses_paths_outside_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="output/"):
        build_docx([("Intro", "text")], {"title": "T"}, "../evil.docx")


def test_build_docx_refuses_an_absolute_path_outside_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "elsewhere" / "evil.docx"
    with pytest.raises(ValueError, match="output/"):
        build_docx([("Intro", "text")], {"title": "T"}, str(target))
    assert not target.exists()


def test_build_docx_refuses_a_sibling_directory_sharing_the_prefix(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="output/"):
        build_docx([("Intro", "text")], {"title": "T"}, "output_evil/x.docx")
    assert not (tmp_path / "output_evil").exists()


def test_build_docx_refuses_a_symlink_in_output_pointing_outside(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        os.symlink(outside, tmp_path / "output" / "link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    with pytest.raises(ValueError, match="output/"):
        build_docx([("Intro", "text")], {"title": "T"}, "output/link/x.docx")
    assert not (outside / "x.docx").exists()
