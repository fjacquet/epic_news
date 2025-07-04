"""
Template Manager pour la génération de rapports HTML

Gère l'utilisation des templates HTML unifiés avec support du dark mode
et expérience utilisateur cohérente.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from epic_news.models.financial_report import FinancialReport
from epic_news.utils.html.template_renderers.renderer_factory import RendererFactory


class TemplateState(BaseModel):
    """Modèle de données pour l'état du template."""

    raw_text: str
    title: str = ""
    error_message: str = ""
    financial_report_model: FinancialReport | None = None


class TemplateManager:
    """Gestionnaire de templates HTML avec support du dark mode et CSS unifié."""

    def __init__(self):
        """Initialise le gestionnaire de templates."""
        # Path from src/epic_news/utils/html/template_manager.py to templates/
        # Go up 5 levels: html -> utils -> epic_news -> src -> project_root -> templates
        self.templates_dir = Path(__file__).parent.parent.parent.parent.parent / "templates"
        self.universal_template_path = self.templates_dir / "universal_report_template.html"
        self.state = TemplateState(raw_text="")

    def load_template(self, template_name: str = "universal_report_template.html") -> str:
        """Charge un template HTML depuis le répertoire templates."""
        template_path = self.templates_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found at {template_path}")

        with open(template_path, encoding="utf-8") as f:
            return f.read()

    def generate_contextual_title(self, selected_crew: str, content_data: dict[str, Any]) -> str:
        """Génère un titre contextualisé selon le type de crew."""
        crew_titles = {
            "POEM": "🌌 Création Poétique",
            "COOKING": "🍳 Recette Culinaire",
            "NEWS": "📰 Actualités du Jour",
            "SHOPPING": "🛒 Conseil d'Achat",
            "HOLIDAY_PLANNER": "🏖️ Planificateur de Vacances",
            "BOOK_SUMMARY": "📚 Analyse Littéraire",
            "MEETING_PREP": "📋 Préparation de Réunion",
            "SAINT": "⛪ Saint du Jour",
            "MENU": "🍽️ Menu de la Semaine",
            "FINDAILY": "💰 Analyse Financière Quotidienne",
            "NEWSDAILY": "📈 Revue de Presse Quotidienne",
            "RSS": "📡 Synthèse RSS Hebdomadaire",
            "MARKETING_WRITERS": "✍️ Contenu Marketing",
            "SALES_PROSPECTING": "💼 Prospection Commerciale",
            "OPEN_SOURCE_INTELLIGENCE": "🔍 Intelligence Open Source",
        }

        base_title = crew_titles.get(selected_crew, f"📄 Rapport {selected_crew}")

        # Ajouter des détails spécifiques si disponibles
        if selected_crew == "POEM" and content_data.get("poem_title"):
            return f"{base_title} - {content_data['poem_title']}"
        if selected_crew == "COOKING":
            # Chercher le titre de la recette dans différents champs possibles
            for field in ["recipe_title", "name", "title"]:
                if content_data.get(field):
                    return f"🍳 {content_data[field]}"
            return base_title
        if selected_crew == "NEWS" and content_data.get("main_topic"):
            return f"{base_title} - {content_data['main_topic']}"
        if selected_crew == "SHOPPING" and content_data.get("product_name"):
            return f"🛒 {content_data['product_name']} - Conseil d'Achat"

        return base_title

    def render_report(self, selected_crew: str, content_data: dict[str, Any]) -> str:
        """Main method to render a complete HTML report using the universal template."""
        try:
            # Load the universal template
            template_html = self.load_template("universal_report_template.html")

            # Generate contextual title and body
            title = self.generate_contextual_title(selected_crew, content_data)
            body_content = self.generate_contextual_body(content_data, selected_crew)

            # Replace placeholders in the template
            html_content = template_html.replace("{{ report_title }}", title)
            html_content = html_content.replace("{{ report_body|safe }}", body_content)
            html_content = html_content.replace(
                "{{ generation_date }}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # Clean up any remaining Jinja2 template syntax
            html_content = html_content.replace("{% if generation_date %}", "")
            html_content = html_content.replace("{% endif %}", "")

            return html_content  # noqa: RET504

        except Exception as e:
            print(f"❌ Error rendering report: {e}")
            # Return a basic HTML structure with error information
            return f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Erreur de Génération</title>
            </head>
            <body>
                <h1>Erreur lors de la génération du rapport</h1>
                <p>Une erreur s'est produite: {e}</p>
                <pre>{str(content_data)[:1000]}...</pre>
            </body>
            </html>
            """

    def generate_contextual_body(self, content_data: dict[str, Any], selected_crew: str) -> str:
        """Génère le corps HTML contextualisé selon le type de crew."""

        # Try to use modular renderer first
        if RendererFactory.has_specialized_renderer(selected_crew):
            try:
                renderer = RendererFactory.create_renderer(selected_crew)
                # Convert Pydantic models to dictionaries for renderer compatibility
                if hasattr(content_data, "model_dump"):
                    renderer_data = content_data.model_dump()
                elif hasattr(content_data, "dict"):
                    renderer_data = content_data.dict()
                else:
                    renderer_data = content_data
                return renderer.render(renderer_data)
            except Exception as e:
                print(f"❌ Error using modular renderer for {selected_crew}: {e}")
                # Fall back to legacy methods

        # Legacy handling for crews not yet migrated to modular renderers

        # Handle FINDAILY (Financial Reports) - Legacy fallback
        if selected_crew == "FINDAILY" or self.state.financial_report_model:
            # Check if we have a financial_report_model in content_data
            if not self.state.financial_report_model and isinstance(content_data, dict):
                # First try to get the model directly from content_data
                financial_model = content_data.get("financial_report_model")
                if financial_model and isinstance(financial_model, FinancialReport):
                    self.state.financial_report_model = financial_model
                    self.state.title = financial_model.title or "Financial Report"
                    print(f"✅ Using FinancialReport model: {financial_model.title}")
                else:
                    # Try to parse content_data as a FinancialReport
                    try:
                        self.state.financial_report_model = FinancialReport.model_validate(content_data)
                        self.state.title = self.state.financial_report_model.title or "Financial Report"
                        print(
                            f"✅ Parsed FinancialReport from content_data: {self.state.financial_report_model.title}"
                        )
                    except Exception as e:
                        print(f"❌ Error parsing financial report: {e}")

            if self.state.financial_report_model:
                # Use FinancialRenderer instead of legacy _generate_financial_report_body

                renderer = RendererFactory.create_renderer("FINANCIAL")
                data = self.state.financial_report_model.dict()
                return renderer.render(data)

        # NEWSDAILY now uses NewsDailyRenderer via RendererFactory

        # Handle SHOPPING_ADVICE (Shopping Advice Reports)
        # All crew types now use modular renderers via RendererFactory

        # Default to generic renderer
        try:
            renderer = RendererFactory.create_renderer(selected_crew)
            return renderer.render(content_data, selected_crew)
        except Exception as e:
            print(f"❌ Error using generic renderer: {e}")
            # Use GenericRenderer instead of legacy _generate_generic_body
            renderer = RendererFactory.create_renderer("GENERIC")
            return renderer.render(content_data, selected_crew)

    # The _generate_poem_body method has been removed and replaced by the PoemRenderer class
    # See src/epic_news/utils/html/template_renderers/poem_renderer.py

    # The _generate_cooking_body method has been removed and replaced by the CookingRenderer class
    # See src/epic_news/utils/html/template_renderers/cooking_renderer.py

    # The _generate_generic_body method has been removed and replaced by the GenericRenderer class
    # See src/epic_news/utils/html/template_renderers/generic_renderer.py

    # The _generate_shopping_body method has been removed and replaced by the ShoppingRenderer class
    # See src/epic_news/utils/html/template_renderers/shopping_renderer.py

    # The _generate_holiday_body method has been removed and replaced by the HolidayPlanRenderer class
    # See src/epic_news/utils/html/template_renderers/holiday_renderer.py

    # The _generate_library_body method has been removed and replaced by the BookSummaryRenderer class
    # See src/epic_news/utils/html/template_renderers/book_summary_renderer.py

    # The _generate_rss_weekly_body method has been removed and replaced by the RssWeeklyRenderer class
    # See src/epic_news/utils/html/template_renderers/rss_weekly_renderer.py

    # The _generate_meeting_body method has been removed and replaced by the MeetingPrepRenderer class
    # See src/epic_news/utils/html/template_renderers/meeting_prep_renderer.py

    # The _generate_saint_body method has been removed and replaced by the SaintRenderer class
    # See src/epic_news/utils/html/template_renderers/saint_renderer.py

    # The _generate_menu_body method has been removed and replaced by the MenuRenderer class
    # See src/epic_news/utils/html/template_renderers/menu_renderer.py

    # The _generate_financial_report_body method has been removed and replaced by the FinancialRenderer class
    # See src/epic_news/utils/html/template_renderers/financial_renderer.py

    # The _generate_cooking_body method has been removed and replaced by the CookingRenderer class
    # See src/epic_news/utils/html/template_renderers/cooking_renderer.py
