from epic_news.crews.news_daily.news_daily import NewsDailyCrew

REGION_TASKS = 7


def test_region_tasks_parallel_with_distinct_agents():
    crew = NewsDailyCrew().crew()
    regions = crew.tasks[:REGION_TASKS]
    curation, final = crew.tasks[REGION_TASKS], crew.tasks[REGION_TASKS + 1]

    assert all(t.async_execution for t in regions)
    assert curation.async_execution is False and final.async_execution is False
    assert len({id(t.agent) for t in regions}) == REGION_TASKS
    assert {id(t) for t in curation.context} == {id(t) for t in regions}


def test_every_task_agent_is_registered_in_the_crew():
    crew = NewsDailyCrew().crew()
    registered = {id(a) for a in crew.agents}
    assert all(id(t.agent) in registered for t in crew.tasks if t.agent is not None)


def test_region_researchers_keep_llm_timeout():
    crew = NewsDailyCrew().crew()
    assert all(t.agent.llm.timeout is not None for t in crew.tasks[:REGION_TASKS])
