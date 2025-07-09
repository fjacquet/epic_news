import re

from unidecode import unidecode


def create_topic_slug(topic: str) -> str:
    """Create a URL-safe slug from a topic string.

    Converts a topic like "Tarte aux pommes" to "tarte-aux-pommes"
    for use in file names and URLs.

    Args:
        topic: The original topic string

    Returns:
        A URL-safe slug version of the topic
    """
    # Convert to ASCII
    slug = unidecode(topic)
    # Convert to lowercase
    slug = slug.lower()
    # Replace spaces and special characters with hyphens
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    # Remove leading/trailing hyphens
    return slug.strip("-")
