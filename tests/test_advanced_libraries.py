def test_mocking_with_pytest_mock(mocker):
    """
    This test demonstrates the use of pytest-mock.
    """
    # Create a mock object
    mock_object = mocker.Mock()

    # Configure the mock to return a specific value when a method is called
    mock_object.get_name.return_value = "Test Name"

    # Call the method on the mock object
    result = mock_object.get_name()

    # Assert that the method was called and returned the expected value
    mock_object.get_name.assert_called_once()
    assert result == "Test Name"
