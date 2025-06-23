import os

from epic_news.utils.directory_utils import ensure_output_directories


def test_ensure_output_directories(tmp_path):
    """Test that all required output directories are created."""
    # Change to the temporary directory to run the test
    os.chdir(tmp_path)

    # Run the function to create directories
    ensure_output_directories()

    # List of all directories that should be created
    expected_dirs = [
        "checkpoints",
        "output",
        "output/meeting",
        "output/lead_scoring",
        "output/contact_finder",
        "output/cooking",
        "output/library",
        "output/poem",
        "output/email",
        "output/holiday",
        "output/marketing",
    ]

    # Check that each directory was created
    for subdir in expected_dirs:
        assert os.path.isdir(subdir), f"Directory '{subdir}' was not created."
