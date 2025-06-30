import asyncio

from epic_news.tools.unified_rss_tool import UnifiedRssTool


async def fetch_articles_from_opml(
    opml_file_path: str,
    output_file_path: str,
    days: int = 7,
) -> None:
    """
    Uses UnifiedRssTool to parse an OPML file, fetch recent articles,
    and save them to a JSON file.

    Args:
        opml_file_path: The path to the OPML file.
        output_file_path: The path to save the output JSON file.
        days: The number of days back to fetch articles from.
    """
    print(f"🚀 Starting article fetching from {opml_file_path} using UnifiedRssTool...")

    rss_tool = UnifiedRssTool()

    # The UnifiedRssTool._run method is synchronous, so we run it in a separate thread
    # to avoid blocking the asyncio event loop.
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,  # Use the default thread pool executor
        rss_tool._run,
        opml_file_path,
        days,
        output_file_path,
    )

    print(f"✅ UnifiedRssTool execution finished. Result: {result}")


if __name__ == "__main__":
    # Define paths
    opml_path = os.path.abspath("data/feedly.opml")
    output_path = os.path.abspath("output/rss_weekly/report.json")

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Run the async function
    asyncio.run(fetch_articles_from_opml(opml_path, output_path))
