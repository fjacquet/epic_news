"""
Meeting Preparation Renderer

Renders meeting preparation data to structured HTML using BeautifulSoup.
Handles company profile, participants, industry overview, talking points,
strategic recommendations, and additional resources.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class MeetingPrepRenderer(BaseRenderer):
    """Renders meeting preparation content with structured formatting."""

    def render(self, data: dict[str, Any]) -> str:
        """
        Render meeting preparation data to HTML.

        Args:
            data: Dictionary containing meeting preparation data

        Returns:
            HTML string for meeting preparation content
        """
        # Handle different input types
        if hasattr(data, "to_template_data") and callable(data.to_template_data):
            data = data.to_template_data()
        elif hasattr(data, "model_dump") and callable(data.model_dump):
            data = data.model_dump()
        elif hasattr(data, "dict") and callable(data.dict):
            data = data.dict()

        # Create main container
        soup = BeautifulSoup('<div class="meeting-prep-container"></div>', "html.parser")
        container = soup.find("div")

        # Add title if available
        if "title" in data:
            title_h2 = soup.new_tag("h2")
            title_h2.attrs["class"] = ["meeting-title"]
            title_h2.string = data["title"]
            container.append(title_h2)

        # Add summary
        self._add_summary(soup, container, data)

        # Add company profile
        self._add_company_profile(soup, container, data)

        # Add participants
        self._add_participants(soup, container, data)

        # Add industry overview
        self._add_industry_overview(soup, container, data)

        # Add talking points
        self._add_talking_points(soup, container, data)

        # Add strategic recommendations
        self._add_strategic_recommendations(soup, container, data)

        # Add additional resources
        self._add_additional_resources(soup, container, data)

        # Add styles
        self._add_styles(soup)

        # Now that we're using attrs["class"] instead of class_, we don't need to replace class_ with class
        return str(soup)

    def _add_summary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add meeting summary."""
        summary = data.get("summary")
        if not summary:
            return

        summary_div = soup.new_tag("div")
        summary_div.attrs["class"] = ["meeting-summary"]

        summary_p = soup.new_tag("p")
        summary_p.string = summary
        summary_div.append(summary_p)

        container.append(summary_div)

    def _add_company_profile(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add company profile section."""
        company_profile = data.get("company_profile", {})
        if not company_profile:
            return

        section = soup.new_tag("div")
        section.attrs["class"] = ["meeting-section"]

        # Section heading
        heading = soup.new_tag("h3")
        heading.string = "🏢 Profil de l'Entreprise"
        section.append(heading)

        profile_div = soup.new_tag("div")
        profile_div.attrs["class"] = ["company-profile"]

        # Company name
        company_name = company_profile.get("name")
        if company_name:
            name_p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = "Nom:"
            name_p.append(strong)
            name_p.append(f" {company_name}")
            profile_div.append(name_p)

        # Industry
        industry = company_profile.get("industry")
        if industry:
            industry_p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = "Secteur:"
            industry_p.append(strong)
            industry_p.append(f" {industry}")
            profile_div.append(industry_p)

        # Key products
        key_products = company_profile.get("key_products", [])
        if key_products:
            products_p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = "Produits clés:"
            products_p.append(strong)
            products_p.append(" ")

            products_list = soup.new_tag("span")
            products_list.string = ", ".join(key_products)
            products_p.append(products_list)
            profile_div.append(products_p)

        # Market position
        market_position = company_profile.get("market_position")
        if market_position:
            position_p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = "Position sur le marché:"
            position_p.append(strong)
            position_p.append(f" {market_position}")
            profile_div.append(position_p)

        section.append(profile_div)
        container.append(section)

    def _add_participants(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add participants section."""
        participants = data.get("participants", [])
        if not participants:
            return

        section = soup.new_tag("div")
        section.attrs["class"] = ["meeting-section"]

        # Section heading
        heading = soup.new_tag("h3")
        heading.string = "👥 Participants"
        section.append(heading)

        participants_div = soup.new_tag("div")
        participants_div.attrs["class"] = ["participants-list"]

        for participant in participants:
            participant_div = soup.new_tag("div")
            participant_div.attrs["class"] = ["participant"]

            # Name
            name = participant.get("name")
            if name:
                name_h4 = soup.new_tag("h4")
                name_h4.string = name
                participant_div.append(name_h4)

            # Role
            role = participant.get("role")
            if role:
                role_p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.string = "Rôle:"
                role_p.append(strong)
                role_p.append(f" {role}")
                participant_div.append(role_p)

            # Background
            background = participant.get("background")
            if background:
                background_p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.string = "Profil:"
                background_p.append(strong)
                background_p.append(f" {background}")
                participant_div.append(background_p)

            participants_div.append(participant_div)

        section.append(participants_div)
        container.append(section)

    def _add_industry_overview(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add industry overview section."""
        industry_overview = data.get("industry_overview")
        if not industry_overview:
            return

        section = soup.new_tag("div")
        section.attrs["class"] = ["meeting-section"]

        # Section heading
        heading = soup.new_tag("h3")
        heading.string = "🌐 Aperçu du Secteur"
        section.append(heading)

        overview_div = soup.new_tag("div")
        overview_div.attrs["class"] = ["industry-overview"]

        overview_p = soup.new_tag("p")
        overview_p.string = industry_overview
        overview_div.append(overview_p)

        section.append(overview_div)
        container.append(section)

    def _add_talking_points(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add talking points section."""
        talking_points = data.get("talking_points", [])
        if not talking_points:
            return

        section = soup.new_tag("div")
        section.attrs["class"] = ["meeting-section"]

        # Section heading
        heading = soup.new_tag("h3")
        heading.string = "💬 Points de Discussion"
        section.append(heading)

        points_div = soup.new_tag("div")
        points_div.attrs["class"] = ["talking-points-list"]

        for i, point in enumerate(talking_points):
            point_div = soup.new_tag("div")
            point_div.attrs["class"] = ["talking-point"]

            # Topic as heading
            topic = point.get("topic", "")
            point_h4 = soup.new_tag("h4")
            point_h4.string = f"{topic}"
            point_div.append(point_h4)

            # Key points as bullet list
            key_points = point.get("key_points", [])
            if key_points:
                key_points_div = soup.new_tag("div")
                key_points_div.attrs["class"] = ["key-points"]

                key_points_h5 = soup.new_tag("h5")
                key_points_h5.string = "Points clés:"
                key_points_div.append(key_points_h5)

                key_points_ul = soup.new_tag("ul")
                key_points_ul.attrs["class"] = ["key-points-list"]

                for key_point in key_points:
                    key_point_li = soup.new_tag("li")
                    key_point_li.string = key_point
                    key_points_ul.append(key_point_li)

                key_points_div.append(key_points_ul)
                point_div.append(key_points_div)

            # Questions
            questions = point.get("questions", [])
            if questions:
                questions_div = soup.new_tag("div")
                questions_div.attrs["class"] = ["questions"]

                questions_h5 = soup.new_tag("h5")
                questions_h5.string = "Questions à poser:"
                questions_div.append(questions_h5)

                questions_ul = soup.new_tag("ul")
                questions_ul.attrs["class"] = ["questions-list"]

                for question in questions:
                    question_li = soup.new_tag("li")
                    question_li.string = question
                    questions_ul.append(question_li)

                questions_div.append(questions_ul)
                point_div.append(questions_div)

            points_div.append(point_div)

        section.append(points_div)
        container.append(section)

    def _add_strategic_recommendations(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add strategic recommendations section."""
        recommendations = data.get("strategic_recommendations", [])
        if not recommendations:
            return

        section = soup.new_tag("div")
        section.attrs["class"] = ["meeting-section", "recommendation-section"]

        # Section heading
        heading = soup.new_tag("h3")
        heading.string = "🎯 Recommandations Stratégiques"
        section.append(heading)

        recommendations_div = soup.new_tag("div")
        recommendations_div.attrs["class"] = ["recommendations-list"]

        for i, reco in enumerate(recommendations):
            reco_div = soup.new_tag("div")
            reco_div.attrs["class"] = ["recommendation-item"]

            # Area as heading
            area = reco.get("area", "")
            reco_h4 = soup.new_tag("h4")
            reco_h4.string = f"{i + 1}. {area}"
            reco_div.append(reco_h4)

            # Suggestion
            suggestion = reco.get("suggestion", "")
            if suggestion:
                suggestion_div = soup.new_tag("div")
                suggestion_div.attrs["class"] = ["recommendation-suggestion"]

                suggestion_p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.string = "Suggestion:"
                suggestion_p.append(strong)
                suggestion_p.append(f" {suggestion}")
                suggestion_div.append(suggestion_p)

                reco_div.append(suggestion_div)

            # Expected outcome
            expected_outcome = reco.get("expected_outcome", "")
            if expected_outcome:
                outcome_div = soup.new_tag("div")
                outcome_div.attrs["class"] = ["recommendation-outcome"]

                outcome_p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.string = "Résultat attendu:"
                outcome_p.append(strong)
                outcome_p.append(f" {expected_outcome}")
                outcome_div.append(outcome_p)

                reco_div.append(outcome_div)

            recommendations_div.append(reco_div)

        section.append(recommendations_div)
        container.append(section)

    def _add_additional_resources(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add additional resources section."""
        resources = data.get("additional_resources", [])
        if not resources:
            return

        section = soup.new_tag("div")
        section.attrs["class"] = ["meeting-section"]

        # Section heading
        heading = soup.new_tag("h3")
        heading.string = "📚 Ressources Additionnelles"
        section.append(heading)

        resources_div = soup.new_tag("div")
        resources_div.attrs["class"] = ["resources-list"]

        for resource in resources:
            resource_div = soup.new_tag("div")
            resource_div.attrs["class"] = ["resource-item"]

            # Title with link if URL is available
            title = resource.get("title", "")
            url = resource.get("link", "")  # Note: JSON uses 'link' not 'url'

            resource_h4 = soup.new_tag("h4")
            if url:
                # Create clickable title
                title_a = soup.new_tag("a", href=url, target="_blank")
                title_a.string = title
                resource_h4.append(title_a)
            else:
                resource_h4.string = title
            resource_div.append(resource_h4)

            # Description
            description = resource.get("description", "")
            if description:
                desc_p = soup.new_tag("p")
                desc_p.string = description
                resource_div.append(desc_p)

            # Display URL separately if available
            if url:
                url_p = soup.new_tag("p")
                url_p.attrs["class"] = ["resource-link"]
                url_a = soup.new_tag("a", href=url, target="_blank")
                url_a.string = url
                url_p.append(url_a)
                resource_div.append(url_p)

            resources_div.append(resource_div)

        section.append(resources_div)
        container.append(section)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles for meeting preparation."""
        style = soup.new_tag("style")
        style.string = """
        .meeting-prep-container {
            max-width: 800px;
            margin: 0 auto;
        }
        .meeting-summary {
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--highlight-bg);
            border-left: 4px solid var(--heading-color);
            border-radius: 4px;
            font-size: 1.1em;
        }
        .meeting-section {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: 0 2px 4px var(--shadow-color);
        }
        .meeting-section h3 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }
        .participant {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--highlight-bg);
            border-radius: 4px;
        }
        .participant h4 {
            margin: 0 0 0.5rem 0;
            color: var(--h3-color);
        }
        .talking-point {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--highlight-bg);
            border-left: 4px solid #007bff;
            border-radius: 4px;
        }
        .questions-list {
            margin-top: 0.5rem;
            padding-left: 1.5rem;
        }
        .questions-list li {
            margin-bottom: 0.5rem;
        }
        .recommendation-section {
            background: linear-gradient(to right, var(--container-bg), rgba(40, 167, 69, 0.1));
            border-left: 4px solid #28a745;
        }
        .recommendation-item {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--container-bg);
            border-radius: 4px;
        }
        .resource-item {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--highlight-bg);
            border-radius: 4px;
        }
        """
        soup.append(style)
