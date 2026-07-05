"""Tests for Holiday Planner HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.crews.holiday_planner_report import HolidayPlannerReport
from epic_news.utils.html.template_manager import TemplateManager
from epic_news.utils.html.template_renderers.holiday_renderer import HolidayRenderer


@pytest.fixture
def sample_holiday_planner_data():
    """Provide a sample HolidayPlannerReport object for testing."""
    return HolidayPlannerReport(
        introduction="Test holiday plan for Paris.",
        itinerary=[
            {
                "day": 1,
                "date": "2024-07-15",
                "activities": [
                    {
                        "time": "10:00-12:00",
                        "description": "Visit Eiffel Tower - Test activity at iconic landmark",
                    }
                ],
            }
        ],
        accommodations=[
            {
                "name": "Test Hotel",
                "address": "123 Test Street, Paris",
                "price_range": "€120/night",
                "description": "Comfortable test hotel with excellent amenities",
            }
        ],
        dining={
            "restaurants": [
                {
                    "name": "Test Restaurant",
                    "location": "456 Test Avenue, Paris",
                    "cuisine": "French",
                    "price_range": "€€€",
                    "description": "Excellent French cuisine with local specialties",
                }
            ]
        },
        budget={
            "items": [
                {
                    "category": "Accommodation",
                    "item": "Hotel booking",
                    "cost": "480",
                    "currency": "EUR",
                    "notes": "4 nights at Test Hotel",
                }
            ],
            "total_estimated": "800",
            "currency": "EUR",
        },
    )


def test_holiday_planner_to_html(sample_holiday_planner_data, tmp_path):
    """Test that TemplateManager renders HOLIDAY_PLANNER and we can write it to a file."""
    html_file = tmp_path / "holiday_planner_report.html"
    tm = TemplateManager()
    html_content = tm.render_report("HOLIDAY_PLANNER", sample_holiday_planner_data)
    html_file.write_text(html_content, encoding="utf-8")

    assert html_file.exists()
    assert "Test holiday plan for Paris" in html_content
    assert "Visit Eiffel Tower" in html_content
    assert "Test Hotel" in html_content


def test_holiday_renderer(sample_holiday_planner_data):
    """Test the HolidayRenderer directly."""
    renderer = HolidayRenderer()
    html = renderer.render(sample_holiday_planner_data.to_template_data())
    soup = BeautifulSoup(html, "html.parser")

    # Test that key sections are present
    assert "Test holiday plan for Paris" in html
    assert "Visit Eiffel Tower" in html
    assert "Test Hotel" in html
    assert "Test Restaurant" in html

    # Test HTML structure
    assert soup.find("section", class_="introduction") is not None
    assert soup.find("section", class_="itinerary") is not None
    assert soup.find("section", class_="accommodations") is not None
    assert soup.find("section", class_="dining") is not None
    assert soup.find("section", class_="budget") is not None


def test_holiday_renderer_error_case():
    """When the data dict contains an 'error' key, only the error div is rendered."""
    renderer = HolidayRenderer()
    html = renderer.render({"error": "Destination not found"})
    soup = BeautifulSoup(html, "html.parser")

    assert "⚠️ Destination not found" in html
    error_div = soup.find("div", class_="error")
    assert error_div is not None
    # None of the normal sections should be present when short-circuited by the error branch.
    assert soup.find("section") is None


def test_holiday_renderer_full_data_all_sections():
    """Comprehensive dict exercising every optional branch of the renderer."""
    data = {
        "table_of_contents": ["Introduction", "Itinéraire", "Budget"],
        "introduction": "Bienvenue à Kyoto, ville des mille temples.",
        "itinerary": [
            {
                "day": 1,
                "date": "2024-09-01",
                "activities": [
                    {"time": "09:00-11:00", "description": "Visite du temple Kinkaku-ji"},
                    {"time": "14:00-16:00", "description": "Balade dans Gion"},
                ],
            },
            {
                "day": 2,
                "date": "2024-09-02",
                "activities": [
                    {"time": "10:00-12:00", "description": "Marché de Nishiki"},
                ],
            },
        ],
        "accommodations": [
            {
                "name": "Ryokan Sakura",
                "address": "12 Rue des Cerisiers, Kyoto",
                "price_range": "¥25000/night",
                "description": "Ryokan traditionnel avec onsen privé",
                "amenities": ["Onsen", "Petit-déjeuner inclus", "Wifi"],
                "contact_booking": "booking@ryokan-sakura.jp",
            }
        ],
        "dining": {
            "restaurants": [
                {
                    "name": "Kyoto Kaiseki House",
                    "location": "5 Rue de la Cascade, Kyoto",
                    "cuisine": "Kaiseki japonais",
                    "price_range": "¥¥¥¥",
                    "description": "Menu dégustation multi-services",
                    "dietary_options": ["Végétarien", "Sans gluten"],
                    "contact": "+81-75-000-0000",
                    "reservation_required": True,
                }
            ],
            "local_specialties": ["Yudofu", "Matcha warabimochi"],
        },
        "budget": {
            "items": [
                {
                    "category": "Hébergement",
                    "item": "Ryokan Sakura",
                    "cost": "500",
                    "currency": "USD",
                    "notes": "2 nuits",
                }
            ],
            "total_estimated": "1200",
            "currency": "USD",
            "notes": "Budget hors billets d'avion",
        },
        "practical_information": {
            "packing_checklist": {
                "vetements": ["Kimono léger", "Chaussures confortables"],
                "documents": ["Passeport", "Assurance voyage"],
                "toiletries": ["Brosse à dents"],
                "electronics": ["Adaptateur secteur"],
                "medical": ["Trousse de premiers secours"],
                "activities": ["Appareil photo"],
                "children": ["Jouets de voyage"],
            },
            "safety_tips": ["Respecter les files d'attente", "Éviter de parler fort dans les temples"],
            "emergency_contacts": [
                {"service": "Police", "number": "110", "notes": "Urgences uniquement"},
                {"service": "Ambulance", "number": "119"},
            ],
            "useful_phrases": [
                {"french": "Bonjour", "local": "Konnichiwa", "pronunciation": "kon-ni-chi-wa"},
                {"french": "Merci", "local": "Arigatou"},
            ],
        },
        "sources": [
            {"title": "Office du tourisme de Kyoto", "url": "https://kyoto-tourism.example"},
            {"title": "Guide sans lien"},
        ],
        "media": [
            {"url": "https://example.com/kinkakuji.jpg", "caption": "Le temple d'or", "type": "image"},
            {
                "url": "https://example.com/gion-tour.mp4",
                "caption": "Visite virtuelle de Gion",
                "type": "video",
            },
        ],
    }

    renderer = HolidayRenderer()
    html = renderer.render(data)
    soup = BeautifulSoup(html, "html.parser")

    # Introduction + TOC
    assert "Bienvenue à Kyoto" in html
    assert soup.find("section", class_="table-of-contents") is not None
    assert "Itinéraire" in html  # TOC item

    # Itinerary: two days, multiple activities
    day_divs = soup.find_all("div", class_="day-itinerary")
    assert len(day_divs) == 2
    assert "Jour 1 - 2024-09-01" in html
    assert "Jour 2 - 2024-09-02" in html
    assert "Visite du temple Kinkaku-ji" in html
    assert "Balade dans Gion" in html
    assert "Marché de Nishiki" in html

    # Accommodations: all optional fields
    assert "Ryokan Sakura" in html
    assert "12 Rue des Cerisiers, Kyoto" in html
    assert "¥25000/night" in html
    assert "Onsen, Petit-déjeuner inclus, Wifi" in html
    assert "booking@ryokan-sakura.jp" in html

    # Dining: restaurant details + local specialties
    assert "Kyoto Kaiseki House" in html
    assert "Cuisine: Kaiseki japonais" in html
    assert "Prix: ¥¥¥¥" in html
    assert "Végétarien, Sans gluten" in html
    assert "+81-75-000-0000" in html
    assert "Réservation recommandée" in html
    assert "Yudofu" in html
    assert "Matcha warabimochi" in html

    # Budget: table + total + notes
    assert soup.find("table", class_="budget-table") is not None
    assert "500 USD" in html
    assert "Total Estimé: 1200 USD" in html
    assert "Budget hors billets d'avion" in html

    # Practical information: packing categories, safety, emergency, phrases
    assert "Kimono léger" in html
    assert "Passeport" in html
    assert "Respecter les files d'attente" in html
    assert "Police: 110 (Urgences uniquement)" in html
    assert "Ambulance: 119" in html
    assert "Bonjour" in html and "Konnichiwa" in html and "[kon-ni-chi-wa]" in html
    assert "Merci" in html and "Arigatou" in html

    # Sources: with and without url
    sources_section = soup.find("div", class_="sources")
    assert sources_section is not None
    link = sources_section.find("a", href="https://kyoto-tourism.example")
    assert link is not None
    assert link.string == "Office du tourisme de Kyoto"
    assert "Guide sans lien" in html

    # Media: image tag for type=image, link for type=video
    media_section = soup.find("div", class_="media")
    assert media_section is not None
    img = media_section.find("img", src="https://example.com/kinkakuji.jpg")
    assert img is not None
    assert img.get("alt") == "Le temple d'or"
    video_link = media_section.find("a", href="https://example.com/gion-tour.mp4")
    assert video_link is not None
    assert video_link.string == "Visite virtuelle de Gion"

    assert html.strip().startswith("<div")


def test_holiday_renderer_minimal_data_via_template_manager():
    """Minimal data (only the required introduction) should not crash and produces a full page."""
    data = {"introduction": "Un court séjour."}
    html = TemplateManager().render_report("HOLIDAY_PLANNER", data)

    assert "<!DOCTYPE html>" in html
    assert "Un court séjour." in html

    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("section", class_="introduction") is not None
    # None of the optional sections should be rendered when absent.
    assert soup.find("section", class_="itinerary") is None
    assert soup.find("section", class_="accommodations") is None
    assert soup.find("section", class_="dining") is None
    assert soup.find("section", class_="budget") is None
    assert soup.find("section", class_="practical-information") is None
    assert soup.find("section", class_="sources-media") is None
    assert soup.find("section", class_="table-of-contents") is None


def test_holiday_renderer_empty_dict_produces_non_trivial_html():
    """A completely empty data dict must not raise and still yields a valid container."""
    renderer = HolidayRenderer()
    html = renderer.render({})
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("div", class_="holiday-planner") is not None
    assert soup.find("section") is None
    assert len(html) > 0


def test_holiday_renderer_day_without_activities_and_missing_fields():
    """A day with no activities and missing day/date falls back to default labels."""
    data = {
        "itinerary": [
            {"activities": []},
        ]
    }
    renderer = HolidayRenderer()
    html = renderer.render(data)

    assert "Jour N/A - Date non spécifiée" in html
    soup = BeautifulSoup(html, "html.parser")
    day_div = soup.find("div", class_="day-itinerary")
    assert day_div is not None
    assert day_div.find("div", class_="activities") is None


def test_holiday_renderer_activity_missing_time_and_description():
    """Activities missing time/description use the renderer's fallback text."""
    data = {
        "itinerary": [
            {"day": 1, "date": "2024-01-01", "activities": [{}]},
        ]
    }
    renderer = HolidayRenderer()
    html = renderer.render(data)

    assert "⏰ Heure non spécifiée" in html
    assert "Description non disponible" in html


def test_holiday_renderer_accommodation_minimal_fields():
    """An accommodation with only a name skips every optional detail div."""
    data = {"accommodations": [{"name": "Auberge Simple"}]}
    renderer = HolidayRenderer()
    html = renderer.render(data)
    soup = BeautifulSoup(html, "html.parser")

    assert "Auberge Simple" in html
    acc_div = soup.find("div", class_="accommodation")
    assert acc_div.find("div", class_="accommodation-address") is None
    assert acc_div.find("div", class_="accommodation-price") is None
    assert acc_div.find("div", class_="accommodation-description") is None
    assert acc_div.find("div", class_="accommodation-amenities") is None
    assert acc_div.find("div", class_="accommodation-contact") is None


def test_holiday_renderer_accommodation_missing_name_uses_fallback():
    """An accommodation dict without a name falls back to the default label."""
    data = {"accommodations": [{"address": "Somewhere"}]}
    renderer = HolidayRenderer()
    html = renderer.render(data)

    assert "Nom non spécifié" in html


def test_holiday_renderer_dining_only_local_specialties():
    """Dining with no restaurants but local specialties skips the restaurants block."""
    data = {"dining": {"local_specialties": ["Fondue", "Raclette"]}}
    renderer = HolidayRenderer()
    html = renderer.render(data)
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("div", class_="restaurants") is None
    assert soup.find("div", class_="local-specialties") is not None
    assert "Fondue" in html
    assert "Raclette" in html


def test_holiday_renderer_restaurant_minimal_fields_uses_fallback_name():
    """A restaurant with no fields at all falls back to default name and skips optional divs."""
    data = {"dining": {"restaurants": [{}]}}
    renderer = HolidayRenderer()
    html = renderer.render(data)
    soup = BeautifulSoup(html, "html.parser")

    assert "Nom non spécifié" in html
    rest_div = soup.find("div", class_="restaurant")
    assert rest_div.find("div", class_="restaurant-location") is None
    assert rest_div.find("div", class_="restaurant-details") is None
    assert rest_div.find("div", class_="restaurant-description") is None
    assert rest_div.find("div", class_="restaurant-dietary") is None
    assert rest_div.find("div", class_="restaurant-contact") is None
    assert rest_div.find("div", class_="restaurant-reservation") is None


def test_holiday_renderer_budget_without_items_but_with_total_and_notes():
    """Budget with no line items still renders the total/notes, but skips the table."""
    data = {
        "budget": {
            "total_estimated": "999",
            "notes": "Estimation approximative",
        }
    }
    renderer = HolidayRenderer()
    html = renderer.render(data)
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("table", class_="budget-table") is None
    assert "Total Estimé: 999 CHF" in html  # default currency fallback
    assert "Estimation approximative" in html


def test_holiday_renderer_practical_information_partial_sections():
    """Practical information with only safety tips renders that block and skips the rest."""
    data = {
        "practical_information": {
            "safety_tips": ["Ne pas boire l'eau du robinet"],
        }
    }
    renderer = HolidayRenderer()
    html = renderer.render(data)
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("div", class_="safety-tips") is not None
    assert "Ne pas boire l'eau du robinet" in html
    assert soup.find("div", class_="packing-checklist") is None
    assert soup.find("div", class_="emergency-contacts") is None
    assert soup.find("div", class_="useful-phrases") is None


def test_holiday_renderer_sources_without_url_and_missing_title():
    """A source without a url renders plain text; without a title falls back to default text."""
    data = {"sources": [{"title": "Blog de voyage"}, {}]}
    renderer = HolidayRenderer()
    html = renderer.render(data)

    assert "Blog de voyage" in html
    assert "Source sans titre" in html
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("div", class_="sources") is not None
    assert soup.find("a") is None  # no url means no <a> link rendered


def test_holiday_renderer_media_item_without_type_defaults_to_image():
    """A media item with no explicit type is treated as an image and skips caption when absent."""
    data = {"media": [{"url": "https://example.com/photo.png"}]}
    renderer = HolidayRenderer()
    html = renderer.render(data)
    soup = BeautifulSoup(html, "html.parser")

    img = soup.find("img", src="https://example.com/photo.png")
    assert img is not None
    media_item = soup.find("div", class_="media-item")
    assert media_item.find("div", class_="media-caption") is None
