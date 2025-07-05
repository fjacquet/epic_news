
from epic_news.utils.html.template_renderers.book_summary_renderer import BookSummaryRenderer
from epic_news.utils.html.template_renderers.generic_renderer import GenericRenderer
from epic_news.utils.html.template_renderers.renderer_factory import RendererFactory


def test_create_renderer():
    # Test that the factory creates the correct renderer for a given crew type
    renderer = RendererFactory.create_renderer("BOOK_SUMMARY")
    assert isinstance(renderer, BookSummaryRenderer)
    renderer = RendererFactory.create_renderer("UNKNOWN")
    assert isinstance(renderer, GenericRenderer)

def test_get_supported_crew_types():
    # Test that get_supported_crew_types returns a list of supported crew types
    supported_types = RendererFactory.get_supported_crew_types()
    assert "BOOK_SUMMARY" in supported_types
    assert "GENERIC" in supported_types

def test_register_renderer():
    # Test that a new renderer can be registered
    class TestRenderer(GenericRenderer):
        def __init__(self):
            pass
    RendererFactory.register_renderer("TEST", TestRenderer)
    renderer = RendererFactory.create_renderer("TEST")
    assert isinstance(renderer, TestRenderer)

def test_has_specialized_renderer():
    # Test that has_specialized_renderer returns the correct value
    assert RendererFactory.has_specialized_renderer("BOOK_SUMMARY")
    assert not RendererFactory.has_specialized_renderer("UNKNOWN")
