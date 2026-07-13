from epic_news.utils.docx_report.tables import md_table


def test_md_table_renders_header_separator_and_rows():
    rows = [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
    columns = [("A", "a"), ("B", "b")]
    out = md_table(rows, columns)
    lines = out.splitlines()
    assert lines[0] == "| A | B |"
    assert lines[1] == "| --- | --- |"
    assert lines[2] == "| 1 | 2 |"
    assert lines[3] == "| 3 | 4 |"


def test_md_table_escapes_pipe_in_cell():
    rows = [{"a": "left|right", "b": "ok"}]
    columns = [("A", "a"), ("B", "b")]
    out = md_table(rows, columns)
    # the pipe is escaped so it survives as literal text, not a column separator
    assert out.splitlines()[2] == "| left\\|right | ok |"


def test_md_table_empty_rows_returns_placeholder():
    assert md_table([], [("A", "a")]) == "_Aucune donnée._"
