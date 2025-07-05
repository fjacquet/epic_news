
from epic_news.utils.crewai_retry_patch import patch_crewai_llm_initialization, initialize_retry_mechanism

def test_patch_crewai_llm_initialization(mocker):
    # Test that patch_crewai_llm_initialization patches the CrewAI LLM initialization
    mocker.patch('epic_news.utils.crewai_retry_patch.get_llm_with_retries')
    mock_agent = mocker.patch('crewai.agent.Agent')
    patch_crewai_llm_initialization()
    assert mock_agent._get_llm is not None

def test_initialize_retry_mechanism(mocker):
    # Test that initialize_retry_mechanism initializes the LLM retry mechanism
    mock_patch_crewai_llm_initialization = mocker.patch('epic_news.utils.crewai_retry_patch.patch_crewai_llm_initialization')
    initialize_retry_mechanism()
    mock_patch_crewai_llm_initialization.assert_called_once()
