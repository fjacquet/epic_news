"""
Template Manager pour la génération de rapports HTML

Gère l'utilisation des templates HTML unifiés avec support du dark mode
et expérience utilisateur cohérente.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .templates import render_universal_report


class TemplateManager:
    """Gestionnaire de templates HTML avec support du dark mode et CSS unifié."""

    def __init__(self):
        """Initialise le gestionnaire de templates."""
        # Path from src/epic_news/utils/html/template_manager.py to templates/
        # Go up 5 levels: html -> utils -> epic_news -> src -> project_root -> templates
        self.templates_dir = Path(__file__).parent.parent.parent.parent.parent / "templates"
        self.universal_template_path = self.templates_dir / "universal_report_template.html"

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
            "LIBRARY": "📚 Analyse Littéraire",
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

    def generate_contextual_body(self, selected_crew: str, content_data: dict[str, Any]) -> str:
        """Génère le corps HTML contextualisé selon le type de crew."""

        if selected_crew == "POEM":
            return self._generate_poem_body(content_data)
        if selected_crew == "COOKING":
            return self._generate_cooking_body(content_data)
        if selected_crew == "NEWS":
            return self._generate_news_body(content_data)
        if selected_crew == "SHOPPING":
            return self._generate_shopping_body(content_data)
        if selected_crew == "HOLIDAY_PLANNER":
            return self._generate_holiday_body(content_data)
        if selected_crew == "LIBRARY":
            return self._generate_library_body(content_data)
        if selected_crew == "MEETING_PREP":
            return self._generate_meeting_body(content_data)
        if selected_crew == "SAINT":
            return self._generate_saint_body(content_data)
        if selected_crew == "MENU":
            return self._generate_menu_body(content_data)
        return self._generate_generic_body(content_data, selected_crew)

    def _generate_poem_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour un poème."""
        poem_content = data.get("poem_content", "")
        theme = data.get("theme", "")
        author = data.get("author", "Epic News AI")

        # Convert newlines to HTML breaks outside f-string
        formatted_poem = poem_content.replace("\n", "<br>")
        theme_html = f'<div class="poem-theme"><strong>Thème :</strong> {theme}</div>' if theme else ""

        return f"""
        <div class="poem-container">
            {theme_html}
            <div class="poem-content">
                {formatted_poem}
            </div>
            <div class="poem-author">
                <em>— {author}</em>
            </div>
        </div>

        <style>
        .poem-container {{
            max-width: 600px;
            margin: 2rem auto;
            padding: 2rem;
            background: var(--container-bg);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .poem-theme {{
            margin-bottom: 1.5rem;
            color: var(--heading-color);
            font-size: 1.1rem;
        }}
        .poem-content {{
            font-family: 'Georgia', serif;
            font-size: 1.2rem;
            line-height: 1.8;
            text-align: center;
            margin: 2rem 0;
            color: var(--text-color);
        }}
        .poem-author {{
            text-align: right;
            margin-top: 2rem;
            font-style: italic;
            color: var(--text-color);
        }}
        </style>
        """

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

    def _generate_news_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour les actualités."""
        articles = data.get("articles", [])
        summary = data.get("summary", "")

        articles_html = ""
        for article in articles:
            title = article.get("title", "")
            content = article.get("content", "")
            source = article.get("source", "")
            date = article.get("date", "")

            articles_html += f"""
            <article class="news-article">
                <h3>{title}</h3>
                <div class="article-meta">
                    {f'<span class="source">📰 {source}</span>' if source else ""}
                    {f'<span class="date">📅 {date}</span>' if date else ""}
                </div>
                <div class="article-content">{content}</div>
            </article>
            """

        return f"""
        <div class="news-container">
            {f'<div class="news-summary"><h3>📋 Résumé</h3><p>{summary}</p></div>' if summary else ""}
            <div class="news-articles">
                {articles_html}
            </div>
        </div>
        
        <style>
        .news-container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .news-summary {{
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border-left: 4px solid var(--heading-color);
        }}
        .news-article {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .news-article h3 {{
            color: var(--heading-color);
            margin-bottom: 1rem;
        }}
        .article-meta {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: var(--text-color);
            opacity: 0.8;
        }}
        .article-content {{
            line-height: 1.6;
        }}
        </style>
        """

    def _generate_generic_body(self, data: dict[str, Any], crew_type: str) -> str:
        """Génère un corps HTML générique pour les types de crew non spécialisés."""
        content = data.get("content", "")
        summary = data.get("summary", "")

        return f"""
        <div class="generic-report">
            <div class="report-type">
                <h2>📄 Rapport {crew_type}</h2>
            </div>

            {f'<div class="report-summary"><h3>📋 Résumé</h3><p>{summary}</p></div>' if summary else ""}

            <div class="report-content">
                <h3>📝 Contenu</h3>
                <div>{content}</div>
            </div>
        </div>

        <style>
        .generic-report {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .report-type h2 {{
            color: var(--heading-color);
            text-align: center;
            margin-bottom: 2rem;
        }}
        .report-summary, .report-content {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .report-summary h3, .report-content h3 {{
            color: var(--heading-color);
            margin-bottom: 1rem;
        }}
        </style>
        """

    def render_report(
        self,
        selected_crew: str,
        content_data: dict[str, Any],
        template_name: str = "universal_report_template.html",
    ) -> str:
        """Rend un rapport HTML complet en utilisant le template unifié."""

        # Générer le titre contextualisé
        report_title = self.generate_contextual_title(selected_crew, content_data)

        # Générer le corps contextualisé
        report_body = self.generate_contextual_body(selected_crew, content_data)

        # Date de génération
        generation_date = datetime.now().strftime("%d/%m/%Y à %H:%M")

        # Utiliser le système de rendu Jinja2 approprié
        return render_universal_report(
            title=report_title, content=report_body, generation_date=generation_date
        )

    # Méthodes pour les autres types de crew (à implémenter selon les besoins)
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

    def _generate_holiday_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour les vacances."""
        return self._generate_generic_body(data, "HOLIDAY_PLANNER")

    def _generate_library_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour la bibliothèque."""
        return self._generate_generic_body(data, "LIBRARY")

    def _generate_meeting_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour les réunions."""
        return self._generate_generic_body(data, "MEETING_PREP")

    def _generate_saint_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour le saint du jour."""
        saint_name = data.get("saint_name", "Saint du Jour")
        feast_date = data.get("feast_date", "")
        biography = data.get("biography", "")
        significance = data.get("significance", "")
        miracles = data.get("miracles", "")
        swiss_connection = data.get("swiss_connection", "")
        prayer_reflection = data.get("prayer_reflection", "")
        sources = data.get("sources", [])
        birth_year = data.get("birth_year", "")
        death_year = data.get("death_year", "")
        patron_of = data.get("patron_of", "")

        # Format dates for display
        date_info = ""
        if birth_year or death_year:
            date_info = f"<p><strong>📅 Dates :</strong> {birth_year} - {death_year}</p>"

        # Format feast date
        feast_info = f"<p><strong>🎉 Fête :</strong> {feast_date}</p>" if feast_date else ""

        # Format patron information
        patron_info = f"<p><strong>🙏 Patron de :</strong> {patron_of}</p>" if patron_of else ""

        # Format sources
        sources_html = ""
        if sources:
            sources_list = "\n".join(
                [f"<li><a href='{source}' target='_blank'>{source}</a></li>" for source in sources]
            )
            sources_html = f"""
            <div class="saint-sources">
                <h4>📚 Sources</h4>
                <ul>
                    {sources_list}
                </ul>
            </div>
            """

        return f"""
        <div class="saint-container">
            <div class="saint-header">
                <h2>⛪ {saint_name}</h2>
                {feast_info}
                {date_info}
                {patron_info}
            </div>
            
            <div class="saint-content">
                <div class="saint-section">
                    <h3>📖 Biographie</h3>
                    <p>{biography}</p>
                </div>
                
                <div class="saint-section">
                    <h3>✨ Signification</h3>
                    <p>{significance}</p>
                </div>
                
                <div class="saint-section">
                    <h3>🌟 Miracles</h3>
                    <p>{miracles}</p>
                </div>
                
                <div class="saint-section">
                    <h3>🇨🇭 Lien avec la Suisse</h3>
                    <p>{swiss_connection}</p>
                </div>
                
                <div class="saint-section prayer-section">
                    <h3>🙏 Prière et Réflexion</h3>
                    <div class="prayer-text">
                        <p><em>{prayer_reflection}</em></p>
                    </div>
                </div>
                
                {sources_html}
            </div>
        </div>
        
        <style>
        .saint-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .saint-header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .saint-header h2 {{
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 2rem;
        }}
        
        .saint-section {{
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .saint-section h3 {{
            color: var(--heading-color);
            margin-bottom: 1rem;
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5rem;
        }}
        
        .saint-section p {{
            line-height: 1.6;
            color: var(--text-color);
        }}
        
        .prayer-section {{
            background: linear-gradient(135deg, var(--container-bg) 0%, rgba(255,215,0,0.1) 100%);
            border-left: 4px solid var(--accent-color);
        }}
        
        .prayer-text {{
            font-style: italic;
            text-align: center;
            padding: 1rem;
        }}
        
        .saint-sources {{
            margin-top: 1rem;
        }}
        
        .saint-sources ul {{
            list-style-type: none;
            padding: 0;
        }}
        
        .saint-sources li {{
            margin-bottom: 0.5rem;
        }}
        
        .saint-sources a {{
            color: var(--accent-color);
            text-decoration: none;
        }}
        
        .saint-sources a:hover {{
            text-decoration: underline;
        }}
        </style>
        """

    def _generate_menu_body(self, data: dict[str, Any]) -> str:
        """Génère le corps HTML pour les menus."""
        return self._generate_generic_body(data, "MENU")

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
