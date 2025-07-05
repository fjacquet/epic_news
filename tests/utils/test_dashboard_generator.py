
from unittest.mock import mock_open
from faker import Faker
from epic_news.utils.dashboard_generator import DashboardGenerator, generate_all_dashboards

fake = Faker()

def test_dashboard_generator(mocker):
    # Test that the DashboardGenerator generates a dashboard
    mocker.patch('builtins.open', new_callable=mock_open, read_data='{"crews": {"test_crew": {"last_execution_time": 10}}}')
    mocker.patch('matplotlib.pyplot.show')
    generator = DashboardGenerator("test_dashboard")
    dashboard_file = generator.generate_dashboard()
    assert dashboard_file.endswith("test_dashboard.html")

def test_generate_all_dashboards(mocker):
    # Test that generate_all_dashboards generates dashboards for all available data
    mocker.patch('os.listdir', return_value=['test_dashboard.json'])
    mocker.patch('epic_news.utils.dashboard_generator.DashboardGenerator.generate_dashboard', return_value="test_dashboard.html")
    dashboard_files = generate_all_dashboards()
    assert len(dashboard_files) == 1
    assert dashboard_files[0] == "test_dashboard.html"
