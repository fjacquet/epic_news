import os
from typing import Optional

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

from epic_news.models.finance_models import ExchangeRateToolInput


class ExchangeRateTool(BaseTool):
    name: str = "Exchange Rate Tool"
    description: str = (
        "Fetches the latest exchange rates for specified currencies using the OpenExchangeRates API. "
        "Requires an OPENEXCHANGERATES_API_KEY environment variable."
    )
    args_schema: type[BaseModel] = ExchangeRateToolInput
    api_key: Optional[str] = None
    base_url: str = "https://openexchangerates.org/api/latest.json"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.getenv("OPENEXCHANGERATES_API_KEY")

    def _run(self, base_currency: str = "USD", target_currencies: Optional[list[str]] = None) -> str:
        if not self.api_key:
            return "Error: OPENEXCHANGERATES_API_KEY environment variable not set. Please get an API key from openexchangerates.org."

        params = {"app_id": self.api_key, "base": base_currency}

        if target_currencies:
            params["symbols"] = ",".join(target_currencies)

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            data = response.json()

            if "error" in data:
                return f"API Error: {data.get('description', 'Unknown error from OpenExchangeRates API.')}"

            rates = data.get("rates")
            if not rates:
                return "Error: Could not retrieve exchange rates from the API response."

            # If specific target_currencies were requested, filter the results
            # (though the 'symbols' param should already do this on the API side)
            if target_currencies:
                output_rates = {curr: rates.get(curr) for curr in target_currencies if curr in rates}
            else:
                output_rates = rates

            if not output_rates:
                return f"Error: No rates found for the specified target currencies: {target_currencies} with base {base_currency}"

            return f"Exchange rates based on {data.get('base', base_currency)} at timestamp {data.get('timestamp', 'N/A')}: {output_rates}"

        except requests.exceptions.HTTPError as http_err:
            return f"HTTP error occurred: {http_err} - Response: {response.text}"
        except requests.exceptions.RequestException as req_err:
            return f"Request error occurred: {req_err}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"
