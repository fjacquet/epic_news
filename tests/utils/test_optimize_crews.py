
from unittest.mock import patch, MagicMock
from epic_news.utils.optimize_crews import discover_crews, analyze_all_crews, analyze_crew_module, display_results

@patch('os.listdir', return_value=['test_crew'])
@patch('os.path.isdir', return_value=True)
@patch('os.path.exists', return_value=True)
def test_discover_crews(mock_exists, mock_isdir, mock_listdir):
    # Test that discover_crews discovers all crew modules in the project
    crews = discover_crews()
    assert len(crews) == 1
    assert crews[0] == "epic_news.crews.test_crew.test_crew_crew"

@patch('epic_news.utils.optimize_crews.discover_crews', return_value=['epic_news.crews.test_crew.test_crew_crew'])
@patch('epic_news.utils.optimize_crews.analyze_crew_module', return_value={'TestCrew': {'current_process': 'Sequential', 'optimal_process': 'Hierarchical', 'task_count': 2, 'async_tasks': 2}})
def test_analyze_all_crews(mock_analyze_crew_module, mock_discover_crews):
    # Test that analyze_all_crews analyzes all crews in the project
    results = analyze_all_crews()
    assert len(results) == 1
    assert "epic_news.crews.test_crew.test_crew_crew" in results

@patch('importlib.import_module')
def test_analyze_crew_module(mock_import_module, mocker):
    # Test that analyze_crew_module analyzes a crew module
    mock_crew_class = MagicMock()
    mock_crew_class.return_value.crew.return_value.process = "Sequential"
    mock_module = MagicMock()
    mocker.patch('epic_news.utils.optimize_crews.inspect.getmembers', return_value=[('TestCrew', mock_crew_class)])
    mocker.patch('epic_news.utils.optimize_crews.inspect.isclass', return_value=True)
    mocker.patch('epic_news.utils.optimize_crews.callable', return_value=True)
    mock_import_module.return_value = mock_module
    results = analyze_crew_module("epic_news.crews.test_crew.test_crew_crew")
    assert "TestCrew" in results

def test_display_results(capsys):
    # Test that display_results displays the analysis results in a tabular format
    results = {"epic_news.crews.test_crew.test_crew_crew": {"TestCrew": {"current_process": "Sequential", "optimal_process": "Hierarchical", "task_count": 2, "async_tasks": 2}}}
    display_results(results)
    captured = capsys.readouterr()
    assert "Crew Orchestration Analysis" in captured.out
