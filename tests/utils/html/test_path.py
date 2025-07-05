
from faker import Faker
from epic_news.utils.html.path import extract_recipe_title_from_state, generate_cooking_output_path, determine_output_path

fake = Faker()

def test_extract_recipe_title_from_state():
    # Test that extract_recipe_title_from_state extracts the recipe title from the state data
    state_data = {"recipe": {"raw": '{"name": "Test Recipe"}'}}
    assert extract_recipe_title_from_state(state_data) == "Test Recipe"

def test_generate_cooking_output_path():
    # Test that generate_cooking_output_path generates the output path for a cooking recipe
    state_data = {"recipe": {"raw": '{"name": "Test Recipe"}'}}
    assert generate_cooking_output_path(state_data) == "output/cooking/test-recipe.html"

def test_determine_output_path():
    # Test that determine_output_path determines the appropriate output path
    state_data = {"output_file": "test.yaml"}
    assert determine_output_path("COOKING", state_data) == "test.html"
    state_data = {"recipe": {"raw": '{"name": "Test Recipe"}'}}
    assert determine_output_path("COOKING", state_data) == "output/cooking/test-recipe.html"
    assert determine_output_path("POEM") == "output/poem/poem.html"
