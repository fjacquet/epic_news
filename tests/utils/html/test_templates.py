
from faker import Faker
from epic_news.utils.html.templates import get_template_environment, render_template, render_menu_report, render_shopping_list

fake = Faker()

def test_get_template_environment():
    # Test that get_template_environment returns a Jinja2 environment
    env = get_template_environment()
    assert env is not None

def test_render_template(mocker):
    # Test that render_template renders a template with the given context
    mocker.patch('jinja2.Environment.get_template').return_value.render.return_value = "<h1>Test</h1>"
    html = render_template("test.html", {})
    assert html == "<h1>Test</h1>"

def test_render_menu_report(mocker):
    # Test that render_menu_report renders the menu report using the template
    mocker.patch('epic_news.utils.html.templates.render_template', return_value="<h1>Test</h1>")
    html = render_menu_report("Test Title", "Test Subtitle", "Test Menu Structure", [], [])
    assert html == "<h1>Test</h1>"

def test_render_shopping_list(mocker):
    # Test that render_shopping_list renders the shopping list using the template
    mocker.patch('epic_news.utils.html.templates.render_template', return_value="<h1>Test</h1>")
    html = render_shopping_list("Test Title", [], 0)
    assert html == "<h1>Test</h1>"
