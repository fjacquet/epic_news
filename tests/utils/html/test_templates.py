from epic_news.utils.html.templates import get_template_environment, render_template


def test_get_template_environment():
    # Test that get_template_environment returns a Jinja2 environment
    env = get_template_environment()
    assert env is not None


def test_render_template(mocker):
    # Test that render_template renders a template with the given context
    mocker.patch("jinja2.Environment.get_template").return_value.render.return_value = "<h1>Test</h1>"
    html = render_template("test.html", {})
    assert html == "<h1>Test</h1>"


def test_render_template_calls_jinja(mocker):
    # Ensure render_template delegates to Jinja2 Environment.get_template().render()
    mock_env = mocker.patch("epic_news.utils.html.templates.get_template_environment")
    mock_template = mocker.MagicMock()
    mock_template.render.return_value = "<h1>OK</h1>"
    mock_env.return_value.get_template.return_value = mock_template
    html = render_template("any.html", {"x": 1})
    assert html == "<h1>OK</h1>"
    mock_env.return_value.get_template.assert_called_with("any.html")
    mock_template.render.assert_called_with(x=1)
