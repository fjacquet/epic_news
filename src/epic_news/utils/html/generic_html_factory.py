from pydantic import BaseModel

from epic_news.utils.html.template_manager import TemplateManager


def generic_html_factory(report_model: BaseModel, html_file: str, title: str) -> None:
    """
    Converts a Pydantic model to a visually appealing HTML file.

    Args:
        report_model: The Pydantic model containing the report data.
        html_file: The path to the output HTML file.
        title: The title of the report.
    """
    template_manager = TemplateManager()
    soup = template_manager.get_template()
    body = soup.body

    if not body:
        raise ValueError("Template is missing a body tag.")

    # Add a title to the report
    title_tag = soup.new_tag("h1", attrs={"class": "title"})
    title_tag.string = title
    body.append(title_tag)

    # Create a container for the report sections
    container = soup.new_tag("div", attrs={"class": "container"})
    body.append(container)

    for field_name, field_value in report_model:
        section = soup.new_tag("div", attrs={"class": "section"})
        container.append(section)
        section_title = soup.new_tag("h2")
        section_title.string = field_name.replace("_", " ").title()
        section.append(section_title)

        if isinstance(field_value, BaseModel):
            content = soup.new_tag("pre")
            content.string = field_value.model_dump_json(indent=2)
        elif isinstance(field_value, list):
            list_tag = soup.new_tag("ul")
            for item in field_value:
                list_item = soup.new_tag("li")
                list_item.string = str(item)
                list_tag.append(list_item)
            content = list_tag
        else:
            content = soup.new_tag("p")
            content.string = str(field_value)

        section.append(content)

    # Write the generated HTML to the specified file
    template_manager.write_template(soup, html_file)
