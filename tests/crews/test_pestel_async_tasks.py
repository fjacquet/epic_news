from epic_news.crews.pestel import pestel_crew


def test_dimension_tasks_are_async_and_report_waits(monkeypatch):
    # Never spawn the Wikipedia MCP server in unit tests.
    monkeypatch.setattr(pestel_crew, "get_mcp_tools_or_empty", lambda crew: [])
    crew = pestel_crew.PestelCrew().crew()

    research = [t for t in crew.tasks if t.output_pydantic is None]
    report = crew.tasks[-1]

    assert len(research) == 6
    assert all(t.async_execution for t in research)
    assert report.async_execution is False
    assert {id(t) for t in report.context} == {id(t) for t in research}
    # One researcher per dimension: async tasks never share an Agent instance.
    assert len({id(t.agent) for t in research}) == 6
