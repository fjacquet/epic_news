"""
CoinMarketCap API tool for cryptocurrency news.
"""

import json
import os

import requests
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel

from epic_news.models.coinmarketcap_models import CryptocurrencyNewsInput

CMC_PRO_API_BASE_URL = "https://pro-api.coinmarketcap.com"


class CoinMarketCapNewsTool(BaseTool):
    name: str = "CoinMarketCap Cryptocurrency News"
    description: str = (
        "Get the latest cryptocurrency news articles. "
        "Optionally provide a cryptocurrency symbol or slug (e.g., BTC, bitcoin) to filter news."
    )
    args_schema: type[BaseModel] = CryptocurrencyNewsInput

    def _run(self, symbol: str | None = None, limit: int = 10) -> str:
        logger.info(
            f"Retrieving {limit} news articles for {symbol if symbol else 'general cryptocurrencies'}"
        )

        if limit > 50:
            limit = 50
            logger.warning("News articles limit capped at 50")

        try:
            headers = {
                "X-CMC_PRO_API_KEY": os.environ.get("X-CMC_PRO_API_KEY", ""),
                "Accept": "application/json",
            }

            api_endpoint = f"{CMC_PRO_API_BASE_URL}/v2/news/latest"
            params = {"limit": limit, "sort_by": "published_at"}

            if symbol:
                if symbol.islower() and "-" in symbol or (symbol.islower() and not symbol.isupper()):
                    params["slug"] = symbol
                else:
                    params["symbol"] = symbol.upper()

            response = requests.get(api_endpoint, headers=headers, params=params)

            if response.status_code != 200:
                error_msg = f"CoinMarketCap API error (News): {response.status_code} - {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            data = response.json()

            if "data" not in data or not isinstance(data.get("data"), list) or not data["data"]:
                logger.info(
                    f"No news articles found for {symbol if symbol else 'general'} or empty list returned."
                )
                return json.dumps(
                    {"query_filter": symbol if symbol else "general", "count": 0, "articles": []}
                )

            news_items = data["data"]
            articles_list = []
            for item in news_items:
                source_name = None  # Initialize
                article_source_value = item.get("source")
                if isinstance(article_source_value, dict):
                    source_name = article_source_value.get("name")
                if (
                    not source_name
                ):  # If source was not a dict, or name was not in it, or source key was missing
                    source_name = item.get("source_name")  # Try direct source_name key

                article = {
                    "title": item.get("title"),
                    "source": source_name,
                    "url": item.get("url"),
                    "published_at": item.get("publishedAt")
                    or item.get("published_at")
                    or item.get("timestamp"),
                    "description": item.get("description") or item.get("subtitle"),
                    "cover_image_url": item.get("cover"),
                }
                articles_list.append(article)

            output_data = {
                "query_filter": symbol if symbol else "general",
                "count": len(articles_list),
                "articles": articles_list,
            }
            logger.info(
                f"Successfully retrieved {len(articles_list)} news articles for {symbol if symbol else 'general'}"
            )
            return json.dumps(output_data)

        except requests.exceptions.RequestException as e:
            error_msg = f"API Request failed for news: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
        except Exception as e:
            error_msg = f"Error processing cryptocurrency news: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg})
