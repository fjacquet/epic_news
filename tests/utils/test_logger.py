import os

from epic_news.utils.logger import get_logger, setup_logging


def test_setup_logging(tmp_path, mocker):
    # Test that setup_logging configures the root logger correctly
    log_dir = tmp_path / "logs"
    setup_logging(log_to_file=True, log_dir=log_dir)
    logger = get_logger(__name__)
    # We can't directly check the level of a loguru logger, but we can check if it logs at the correct level
    mock_info = mocker.patch("loguru._logger.Logger.info")
    logger.info("test")
    mock_info.assert_called_once()


def test_log_to_file(tmp_path):
    # Test that logs are written to a file when log_to_file is True
    log_dir = tmp_path / "logs"
    log_file = log_dir / "epic_news.log"
    setup_logging(log_to_file=True, log_dir=log_dir)
    logger = get_logger(__name__)
    logger.info("This is a test log message.")
    # The logger is asynchronous, so we need to wait for the message to be written
    logger.complete()
    assert os.path.exists(log_file)
    with open(log_file) as f:
        assert "This is a test log message." in f.read()


def test_error_log_to_file(tmp_path):
    # Test that error logs are written to a separate file
    log_dir = tmp_path / "logs"
    error_log_file = log_dir / "epic_news_error.log"
    setup_logging(log_to_file=True, log_dir=log_dir)
    logger = get_logger(__name__)
    logger.error("This is a test error message.")
    # The logger is asynchronous, so we need to wait for the message to be written
    logger.complete()
    assert os.path.exists(error_log_file)
    with open(error_log_file) as f:
        assert "This is a test error message." in f.read()
