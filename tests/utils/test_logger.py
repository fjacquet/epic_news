import logging
import unittest

from epic_news.utils.logger import get_logger, setup_logging


class TestLogger(unittest.TestCase):
    def test_setup_logging(self):
        """Test that logging is set up correctly."""
        # Reset logging to a known state before testing
        logging.getLogger().handlers = []
        setup_logging(log_level=logging.INFO)
        logger = get_logger("test_logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.getEffectiveLevel(), logging.INFO)

    def test_get_logger(self):
        """Test that get_logger returns a logger with the correct name."""
        logger = get_logger("my_test_logger")
        self.assertEqual(logger.name, "my_test_logger")


if __name__ == "__main__":
    unittest.main()
