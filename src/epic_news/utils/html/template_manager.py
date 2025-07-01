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
from epic_news.utils.html.renderer_factory import RendererFactory


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

            return html_content

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
        if selected_crew == "SHOPPING_ADVICE":
            return self._generate_shopping_body(content_data)

        # Handle RSS_WEEKLY (RSS Weekly Digest Reports)
        if selected_crew == "RSS_WEEKLY":
            return self._generate_rss_weekly_body(content_data)

        # Handle other crew types with legacy methods
        if selected_crew == "COOKING":
            return self._generate_cooking_body(content_data)
        # HOLIDAY_PLANNER now uses HolidayPlanRenderer via RendererFactory
        if selected_crew == "MENU":
            return self._generate_menu_body(content_data)

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

    def _generate_cooking_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour une recette."""
        recipe_title = data.get("recipe_title", "Recette")
        description = data.get("description", "")
        ingredients = data.get("ingredients", [])
        instructions = data.get("instructions", [])
        prep_time = data.get("prep_time", "")
        cook_time = data.get("cook_time", "")
        servings = data.get("servings", "")
        chef_notes = data.get("chef_notes", "")
        difficulty = data.get("difficulty", "")
        category = data.get("category", "")

        # Build ingredients HTML
        ingredients_html = ""
        if ingredients:
            ingredients_html = (
                "<ul class='ingredients-list'>"
                + "".join([f"<li>🥄 {ing}</li>" for ing in ingredients])
                + "</ul>"
            )

        # Build instructions HTML
        instructions_html = ""
        if instructions:
            instructions_html = (
                "<ol class='instructions-list'>"
                + "".join([f"<li>{step}</li>" for step in instructions])
                + "</ol>"
            )

        return f"""
        <div class="recipe-container">
            {f'<div class="recipe-description">{description}</div>' if description else ""}

            <div class="recipe-meta">
                {f'<span class="prep-time">⏲️ Préparation: {prep_time}</span>' if prep_time else ""}
                {f'<span class="cook-time">🔥 Cuisson: {cook_time}</span>' if cook_time else ""}
                {f'<span class="servings">👥 Portions: {servings}</span>' if servings else ""}
                {f'<span class="difficulty">📊 Difficulté: {difficulty}</span>' if difficulty else ""}
                {f'<span class="category">🏷️ Catégorie: {category}</span>' if category else ""}
            </div>

            {f'<div class="recipe-section"><h3>🥘 Ingrédients</h3>{ingredients_html}</div>' if ingredients else ""}
            {f'<div class="recipe-section"><h3>👨‍🍳 Instructions</h3>{instructions_html}</div>' if instructions else ""}
            {f'<div class="recipe-section"><h3>📝 Notes du Chef</h3><p>{chef_notes}</p></div>' if chef_notes else ""}
        </div>

        <style>
        .recipe-container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .recipe-meta {{
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .recipe-section {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .recipe-section h3 {{
            color: var(--heading-color);
            margin-bottom: 1rem;
        }}
        .recipe-section ul, .recipe-section ol {{
            margin: 0;
            padding-left: 1.5rem;
        }}
        .recipe-section li {{
            margin: 0.5rem 0;
            line-height: 1.6;
        }}
        </style>
        """

    # The _generate_generic_body method has been removed and replaced by the GenericRenderer class
    # See src/epic_news/utils/html/template_renderers/generic_renderer.py

    def _generate_shopping_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour le shopping avec données structurées."""
        if "error" in data:
            return f"<div class='error'>⚠️ {data['error']}</div>"

        # Build structured shopping advice HTML
        sections = []

        # Product Overview Section
        if data.get("product_name") and data.get("product_overview"):
            sections.append(f"""
            <section class="product-overview">
                <h2>🛍️ {data["product_name"]}</h2>
                <div class="overview">
                    <p>{data["product_overview"]}</p>
                </div>
            </section>
            """)

        # Product Details Section
        if data.get("product_specifications") or data.get("product_pros") or data.get("product_cons"):
            details_html = "<section class='product-details'><h3>📋 Détails du Produit</h3>"

            if data.get("product_specifications"):
                specs = data["product_specifications"]
                if isinstance(specs, list):
                    specs_html = "<ul>" + "".join([f"<li>{spec}</li>" for spec in specs]) + "</ul>"
                else:
                    specs_html = f"<p>{specs}</p>"
                details_html += f"<div class='specifications'><h4>🔧 Spécifications</h4>{specs_html}</div>"

            if data.get("product_pros"):
                pros = data["product_pros"]
                if isinstance(pros, list):
                    pros_html = "<ul>" + "".join([f"<li>✅ {pro}</li>" for pro in pros]) + "</ul>"
                else:
                    pros_html = f"<p>✅ {pros}</p>"
                details_html += f"<div class='pros'><h4>👍 Avantages</h4>{pros_html}</div>"

            if data.get("product_cons"):
                cons = data["product_cons"]
                if isinstance(cons, list):
                    cons_html = "<ul>" + "".join([f"<li>❌ {con}</li>" for con in cons]) + "</ul>"
                else:
                    cons_html = f"<p>❌ {cons}</p>"
                details_html += f"<div class='cons'><h4>👎 Inconvénients</h4>{cons_html}</div>"

            details_html += "</section>"
            sections.append(details_html)

        # Pricing Section
        if data.get("switzerland_prices") or data.get("france_prices"):
            pricing_html = "<section class='pricing'><h3>💰 Comparaison des Prix</h3>"

            if data.get("switzerland_prices"):
                pricing_html += "<div class='country-prices'><h4>🇨🇭 Suisse</h4><div class='price-grid'>"
                for price in data["switzerland_prices"]:
                    pricing_html += f"""
                    <div class="price-card">
                        <h5>{price.get("retailer", "N/A")}</h5>
                        <p class="price">{price.get("price", "N/A")}</p>
                        <p class="total">Total: {price.get("total_cost", "N/A")}</p>
                        {f'<p class="shipping">Livraison: {price["shipping_cost"]}</p>' if price.get("shipping_cost") else ""}
                        {f'<a href="{price["url"]}" target="_blank" class="buy-link">Acheter</a>' if price.get("url") else ""}
                        {f'<p class="notes">{price["notes"]}</p>' if price.get("notes") else ""}
                    </div>
                    """
                pricing_html += "</div></div>"

            if data.get("france_prices"):
                pricing_html += "<div class='country-prices'><h4>🇫🇷 France</h4><div class='price-grid'>"
                for price in data["france_prices"]:
                    pricing_html += f"""
                    <div class="price-card">
                        <h5>{price.get("retailer", "N/A")}</h5>
                        <p class="price">{price.get("price", "N/A")}</p>
                        <p class="total">Total: {price.get("total_cost", "N/A")}</p>
                        {f'<p class="shipping">Livraison: {price["shipping_cost"]}</p>' if price.get("shipping_cost") else ""}
                        {f'<a href="{price["url"]}" target="_blank" class="buy-link">Acheter</a>' if price.get("url") else ""}
                        {f'<p class="notes">{price["notes"]}</p>' if price.get("notes") else ""}
                    </div>
                    """
                pricing_html += "</div></div>"

            pricing_html += "</section>"
            sections.append(pricing_html)

        # Competitors Section
        if data.get("competitors"):
            comp_html = "<section class='competitors'><h3>🏆 Concurrence</h3><div class='competitor-grid'>"
            for comp in data["competitors"]:
                comp_html += f"""
                <div class="competitor-card">
                    <h4>{comp.get("name", "N/A")}</h4>
                    <p class="price-range">Prix: {comp.get("price_range", "N/A")}</p>
                    {f'<div class="features"><strong>Caractéristiques:</strong> {comp["key_features"]}</div>' if comp.get("key_features") else ""}
                    {f'<div class="pros"><strong>Avantages:</strong> {comp["pros"]}</div>' if comp.get("pros") else ""}
                    {f'<div class="cons"><strong>Inconvénients:</strong> {comp["cons"]}</div>' if comp.get("cons") else ""}
                </div>
                """
            comp_html += "</div></section>"
            sections.append(comp_html)

        # Executive Summary
        if data.get("executive_summary"):
            sections.append(f"""
            <section class="executive-summary">
                <h3>📊 Résumé Exécutif</h3>
                <div class="summary-content">
                    <p>{data["executive_summary"]}</p>
                </div>
            </section>
            """)

        # Final Recommendations
        if data.get("final_recommendations"):
            sections.append(f"""
            <section class="recommendations">
                <h3>🎯 Recommandations Finales</h3>
                <div class="recommendations-content">
                    <p>{data["final_recommendations"]}</p>
                </div>
            </section>
            """)

        # Best Deals
        if data.get("best_deals"):
            deals = data["best_deals"]
            if isinstance(deals, list):
                deals_html = "<ul>" + "".join([f"<li>🔥 {deal}</li>" for deal in deals]) + "</ul>"
            else:
                deals_html = f"<p>{deals}</p>"
            sections.append(f"""
            <section class="best-deals">
                <h3>🔥 Meilleures Offres</h3>
                <div class="deals-content">
                    {deals_html}
                </div>
            </section>
            """)

        return "\n".join(sections)

    # The _generate_holiday_body method has been removed and replaced by the HolidayPlanRenderer class
    # See src/epic_news/utils/html/template_renderers/holiday_plan_renderer.py

    # The _generate_library_body method has been removed and replaced by the BookSummaryRenderer class
    # See src/epic_news/utils/html/template_renderers/book_summary_renderer.py

    def _generate_rss_weekly_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour le digest RSS hebdomadaire."""
        if "error" in data:
            return f"<div class='error'>⚠️ {data['error']}</div>"

        sections = []

        # Executive Summary
        if data.get("executive_summary"):
            sections.append(f"""
            <section class="executive-summary">
                <h2>📊 Résumé Exécutif</h2>
                <div class="summary-content">
                    <p>{data["executive_summary"]}</p>
                </div>
            </section>
            """)

        # Statistics Overview
        total_feeds = data.get("total_feeds", 0)
        total_articles = data.get("total_articles", 0)
        if total_feeds > 0 or total_articles > 0:
            sections.append(f"""
            <section class="statistics">
                <h2>📈 Statistiques</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>📡 Flux RSS</h3>
                        <p class="stat-number">{total_feeds}</p>
                    </div>
                    <div class="stat-card">
                        <h3>📰 Articles</h3>
                        <p class="stat-number">{total_articles}</p>
                    </div>
                </div>
            </section>
            """)

        # Feed Digests
        if data.get("feeds"):
            sections.append("<section class='feed-digests'><h2>📡 Digest par Source</h2>")

            for feed in data["feeds"]:
                feed_name = feed.get("feed_name", "Source inconnue")
                feed_url = feed.get("feed_url", "")
                articles = feed.get("articles", [])

                sections.append(f"""
                <div class="feed-digest">
                    <h3>🌐 {feed_name}</h3>
                    {f'<p class="feed-url"><a href="{feed_url}" target="_blank">{feed_url}</a></p>' if feed_url else ""}
                    <div class="articles-count">📊 {len(articles)} article(s)</div>
                """)

                if articles:
                    sections.append("<div class='articles-list'>")
                    for article in articles:
                        title = article.get("title", "Titre non disponible")
                        link = article.get("link", "")
                        published = article.get("published", "")
                        summary = article.get("summary", "")

                        sections.append(f"""
                        <article class="article-summary">
                            <h4>{'<a href="' + link + '" target="_blank">' + title + "</a>" if link else title}</h4>
                            {f'<p class="published-date">📅 {published}</p>' if published else ""}
                            {f'<div class="summary"><p>{summary}</p></div>' if summary else ""}
                        </article>
                        """)
                    sections.append("</div>")

                sections.append("</div>")

            sections.append("</section>")

        return "\n".join(sections)

    # The _generate_meeting_body method has been removed and replaced by the MeetingPrepRenderer class
    # See src/epic_news/utils/html/template_renderers/meeting_prep_renderer.py

    # The _generate_saint_body method has been removed and replaced by the SaintRenderer class
    # See src/epic_news/utils/html/template_renderers/saint_renderer.py

    def _generate_menu_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour les menus."""
        # Use GenericRenderer instead of legacy _generate_generic_body
        renderer = RendererFactory.create_renderer("GENERIC")
        return renderer.render(data, "MENU")

    # The _generate_financial_report_body method has been removed and replaced by the FinancialRenderer class
    # See src/epic_news/utils/html/template_renderers/financial_renderer.py

    def _generate_cooking_body(self, data: dict[str, Any]) -> str:
        """Generate rich HTML content for cooking recipes with structured formatting."""
        recipe_title = data.get("recipe_title", "Recette")
        ingredients = data.get("ingredients", [])
        instructions = data.get("instructions", [])
        prep_time = data.get("prep_time", "")
        cook_time = data.get("cook_time", "")
        servings = data.get("servings", "")
        difficulty = data.get("difficulty", "")
        rating = data.get("rating", "")
        categories = data.get("categories", [])
        notes = data.get("notes", "")
        source = data.get("source", "")
        source_url = data.get("source_url", "")
        nutritional_info = data.get("nutritional_info", "")

        # Build category display
        category_display = ", ".join(categories) if categories else ""

        # Build rating display
        rating_stars = ""
        if rating and str(rating).isdigit():
            rating_num = int(rating)
            rating_stars = "⭐" * min(rating_num, 5)

        # Build difficulty display
        difficulty_emoji = {
            "facile": "🟢 Facile",
            "moyen": "🟡 Moyen",
            "difficile": "🔴 Difficile",
            "easy": "🟢 Facile",
            "medium": "🟡 Moyen",
            "hard": "🔴 Difficile",
        }.get(difficulty.lower(), difficulty)

        body_content = f"""
        <div class="recipe-container">
            <header class="recipe-header">
                <h1 class="recipe-title">🍽️ {recipe_title}</h1>
                <div class="recipe-meta">
                    {f'<div class="meta-item"><strong>⏱️ Préparation:</strong> {prep_time}</div>' if prep_time else ""}
                    {f'<div class="meta-item"><strong>🔥 Cuisson:</strong> {cook_time}</div>' if cook_time else ""}
                    {f'<div class="meta-item"><strong>👥 Portions:</strong> {servings}</div>' if servings else ""}
                    {f'<div class="meta-item"><strong>📊 Difficulté:</strong> {difficulty_emoji}</div>' if difficulty else ""}
                    {f'<div class="meta-item"><strong>⭐ Note:</strong> {rating_stars}</div>' if rating_stars else ""}
                    {f'<div class="meta-item"><strong>🏷️ Catégorie:</strong> {category_display}</div>' if category_display else ""}
                </div>
            </header>

            <main class="recipe-content">
                <section class="ingredients-section">
                    <h2>🛒 Ingrédients</h2>
                    <ul class="ingredients-list">
        """

        # Add ingredients
        for ingredient in ingredients:
            if ingredient.strip():
                body_content += f"                        <li>{ingredient.strip()}</li>\n"

        body_content += """
                    </ul>
                </section>

                <section class="instructions-section">
                    <h2>👩‍🍳 Instructions</h2>
                    <ol class="instructions-list">
        """

        # Add instructions
        for i, instruction in enumerate(instructions, 1):
            if instruction.strip():
                body_content += (
                    f"                        <li><strong>Étape {i}:</strong> {instruction.strip()}</li>\n"
                )

        body_content += "                    </ol>\n                </section>\n"

        # Add optional sections
        if notes:
            body_content += f"""
                <section class="notes-section">
                    <h2>📝 Notes du Chef</h2>
                    <div class="notes-content">
                        <p>{notes}</p>
                    </div>
                </section>
            """

        if nutritional_info:
            body_content += f"""
                <section class="nutrition-section">
                    <h2>🥗 Informations Nutritionnelles</h2>
                    <div class="nutrition-content">
                        <p>{nutritional_info}</p>
                    </div>
                </section>
            """

        if source or source_url:
            body_content += """
                <section class="source-section">
                    <h2>📚 Source</h2>
                    <div class="source-content">
            """
            if source_url:
                body_content += f'                        <p><a href="{source_url}" target="_blank" rel="noopener">🔗 {source or "Voir la recette originale"}</a></p>\n'
            elif source:
                body_content += f"                        <p>{source}</p>\n"
            body_content += "                    </div>\n                </section>\n"

        body_content += """
            </main>

            <footer class="recipe-footer">
                <p class="generated-by">✨ Recette générée par <strong>Epic News AI</strong></p>
                <p class="generation-date">📅 Générée le {current_date}</p>
            </footer>
        </div>

        <style>
        .recipe-container {
            max-width: 800px;
            margin: 0 auto;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }

        .recipe-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .recipe-title {
            font-size: 2.5rem;
            margin: 0 0 1rem 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .recipe-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .meta-item {
            background: rgba(255,255,255,0.2);
            padding: 0.5rem;
            border-radius: 6px;
            font-size: 0.9rem;
        }

        .recipe-content {
            display: grid;
            gap: 2rem;
        }

        .ingredients-section, .instructions-section, .notes-section, .nutrition-section, .source-section {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        .ingredients-section h2, .instructions-section h2, .notes-section h2, .nutrition-section h2, .source-section h2 {
            color: #667eea;
            margin-top: 0;
            font-size: 1.5rem;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 0.5rem;
        }

        .ingredients-list, .instructions-list {
            margin: 1rem 0;
            padding-left: 1.5rem;
        }

        .ingredients-list li, .instructions-list li {
            margin: 0.5rem 0;
            padding: 0.3rem 0;
        }

        .instructions-list li {
            margin: 1rem 0;
            padding: 0.8rem;
            background: white;
            border-radius: 8px;
            border-left: 3px solid #28a745;
        }

        .notes-content, .nutrition-content, .source-content {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
        }

        .recipe-footer {
            text-align: center;
            margin-top: 2rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
            color: #6c757d;
            font-size: 0.9rem;
        }

        .recipe-footer p {
            margin: 0.25rem 0;
        }

        @media (max-width: 768px) {
            .recipe-container {
                margin: 0 1rem;
            }

            .recipe-title {
                font-size: 2rem;
            }

            .recipe-meta {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """.replace("{current_date}", datetime.now().strftime("%d/%m/%Y"))

        return body_content
