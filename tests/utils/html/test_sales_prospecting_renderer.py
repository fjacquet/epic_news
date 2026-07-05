"""Tests for the Sales Prospecting HTML renderer.

Covers both the end-to-end path (``TemplateManager.render_report`` with the
``SALES_PROSPECTING`` crew identifier registered in ``renderer_factory.py``)
and direct ``SalesProspectingRenderer.render`` calls used to exercise
defensive branches (missing optional contact fields, falsy/empty sections)
that the strict ``SalesProspectingReport`` Pydantic model can't produce.
"""

from bs4 import BeautifulSoup

from epic_news.models.crews.sales_prospecting_report import KeyContact, SalesProspectingReport
from epic_news.utils.html.template_manager import TemplateManager
from epic_news.utils.html.template_renderers.sales_prospecting_renderer import SalesProspectingRenderer

CREW_IDENTIFIER = "SALES_PROSPECTING"


def _full_report() -> SalesProspectingReport:
    return SalesProspectingReport(
        company_overview="Acme Corp is a leading widget manufacturer with 500 employees.",
        key_contacts=[
            KeyContact(
                name="Jane Doe",
                role="VP of Engineering",
                department="Engineering",
                contact_info="jane.doe@acme.example",
            ),
            KeyContact(
                name="John Smith",
                role="CFO",
                department="Finance",
                contact_info="john.smith@acme.example",
            ),
        ],
        approach_strategy="Lead with an ROI-focused pitch targeting the engineering budget cycle.",
        remaining_information="Acme recently raised a Series C round and is expanding into Europe.",
    )


def test_full_report_renders_all_sections_via_template_manager():
    """Full data through the real pipeline: TemplateManager -> RendererFactory -> renderer."""
    data = _full_report().model_dump()

    html = TemplateManager().render_report(CREW_IDENTIFIER, data)

    assert "<!DOCTYPE html>" in html

    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("div.sales-prospecting-report")
    assert root is not None, "renderer root container missing from rendered document"

    # Header always present.
    header = root.select_one("div.report-header")
    assert header is not None
    assert header.h1.get_text() == "Sales Prospecting Report"

    # Exactly 4 sections carry the shared "report-section" class: overview,
    # key contacts, approach strategy, remaining information (in that order).
    sections = root.select("section.report-section")
    assert len(sections) == 4
    heading_texts = [section.h2.get_text() for section in sections]
    assert heading_texts == [
        "Company Overview",
        "Key Contacts",
        "Approach Strategy",
        "Remaining Information",
    ]

    # Company overview content.
    assert sections[0].p.get_text() == ("Acme Corp is a leading widget manufacturer with 500 employees.")

    # Key contacts: two cards, in insertion order, all four fields present.
    cards = sections[1].select("div.contact-card")
    assert len(cards) == 2

    first_card_texts = [tag.get_text() for tag in cards[0].find_all(["h3", "p"])]
    assert first_card_texts == [
        "Jane Doe",
        "VP of Engineering",
        "Engineering",
        "jane.doe@acme.example",
    ]

    second_card_texts = [tag.get_text() for tag in cards[1].find_all(["h3", "p"])]
    assert second_card_texts == [
        "John Smith",
        "CFO",
        "Finance",
        "john.smith@acme.example",
    ]

    # Contacts are wrapped in the contacts-grid container.
    assert sections[1].select_one("div.contacts-grid") is not None

    # Approach strategy content.
    assert sections[2].p.get_text() == (
        "Lead with an ROI-focused pitch targeting the engineering budget cycle."
    )

    # Remaining information content.
    assert sections[3].p.get_text() == ("Acme recently raised a Series C round and is expanding into Europe.")

    # Raw data debug section is always rendered, with the fed-in data serialized.
    raw = root.select_one("details.raw-data")
    assert raw is not None
    assert raw.summary.get_text() == "View Raw Data"
    assert "Acme Corp is a leading widget manufacturer" in raw.code.get_text()
    assert "Jane Doe" in raw.code.get_text()


def test_empty_data_renders_without_crashing_and_skips_optional_sections():
    """Minimal/empty data: no crash, header + raw-data survive, optional sections vanish."""
    html = TemplateManager().render_report(CREW_IDENTIFIER, {})

    assert "<!DOCTYPE html>" in html

    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("div.sales-prospecting-report")
    assert root is not None

    header = root.select_one("div.report-header")
    assert header is not None
    assert header.h1.get_text() == "Sales Prospecting Report"

    # None of the optional sections should be present for empty data.
    assert root.select("section.report-section") == []
    assert root.select_one("div.contacts-grid") is None

    # Raw data section still renders, with the empty dict serialized.
    raw = root.select_one("details.raw-data")
    assert raw is not None
    assert raw.code.get_text() == "{}"


def test_direct_render_skips_falsy_optional_fields():
    """Falsy (empty string / None / empty list) values must skip their section entirely."""
    data = {
        "company_overview": "",
        "key_contacts": [],
        "approach_strategy": None,
        "remaining_information": None,
    }

    html = SalesProspectingRenderer().render(data)
    soup = BeautifulSoup(html, "html.parser")

    assert soup.select("section.report-section") == []
    assert "Company Overview" not in html
    assert "Key Contacts" not in html
    assert "Approach Strategy" not in html
    assert "Remaining Information" not in html

    # Header and raw-data debug block are unconditional.
    assert soup.select_one("div.report-header") is not None
    assert soup.select_one("details.raw-data") is not None


def test_direct_render_contact_missing_optional_keys_falls_back_to_na():
    """A contact dict missing role/department/contact_info exercises the "N/A" fallback branch.

    ``KeyContact`` marks these fields as required, so this defensive branch can
    only be reached by feeding the renderer a raw dict that skips Pydantic
    validation (e.g. schema drift from an upstream crew) -- exactly what this
    test does.
    """
    data = {
        "key_contacts": [{"name": "Solo Contact"}],
    }

    html = SalesProspectingRenderer().render(data)
    soup = BeautifulSoup(html, "html.parser")

    card = soup.select_one("div.contact-card")
    assert card is not None
    texts = [tag.get_text() for tag in card.find_all(["h3", "p"])]
    assert texts == ["Solo Contact", "N/A", "N/A", "N/A"]


def test_direct_render_contact_missing_name_falls_back_to_na():
    """A contact dict missing "name" exercises the h3 fallback branch too."""
    data = {
        "key_contacts": [{"role": "Analyst", "department": "Finance", "contact_info": "x@example.com"}],
    }

    html = SalesProspectingRenderer().render(data)
    soup = BeautifulSoup(html, "html.parser")

    card = soup.select_one("div.contact-card")
    assert card is not None
    assert card.h3.get_text() == "N/A"
    paragraphs = [p.get_text() for p in card.find_all("p")]
    assert paragraphs == ["Analyst", "Finance", "x@example.com"]


def test_direct_render_raw_data_preserves_unicode_without_escaping():
    """``_add_raw_data`` dumps with ensure_ascii=False; accented text stays literal."""
    data = {"company_overview": "Société basée à Genève, café compris."}

    html = SalesProspectingRenderer().render(data)
    soup = BeautifulSoup(html, "html.parser")

    code_text = soup.select_one("details.raw-data code").get_text()
    assert "Société basée à Genève, café compris." in code_text
    assert "\\u00e9" not in code_text
