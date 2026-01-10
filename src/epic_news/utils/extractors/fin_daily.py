"""Financial extractor module for FIN_DAILY crew content.

This module provides the extractor for FinDailyCrew output to parse it into
a structured FinancialReport model.
"""

import json
from typing import Any

from loguru import logger

from epic_news.models.crews.financial_report import FinancialReport
from epic_news.utils.extractors.base_extractor import ContentExtractor


class FinancialExtractor(ContentExtractor):
    """Extractor for FIN_DAILY crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract financial report data using FinancialReport Pydantic model."""
        logger.debug("🔍 DEBUG FINANCIAL extraction:")

        # Check for financial_report_model in state_data
        financial_report = state_data.get("financial_report_model")
        logger.debug(f"  financial_report type: {type(financial_report)}")

        if financial_report is None:
            # Try to find financial report in raw data
            fin_daily_data = state_data.get("fin_daily_report", {})
            fin_raw = fin_daily_data.get("raw", "{}")
            logger.debug(f"  fin_raw (first 200 chars): {str(fin_raw)[:200]}...")

            try:
                # Try to parse as JSON
                fin_data = json.loads(fin_raw) if isinstance(fin_raw, str) else fin_raw

                # Try to create FinancialReport from the data
                financial_report = FinancialReport.model_validate(fin_data)
                logger.debug(f"  ✅ FinancialReport parsed from raw data: {financial_report.title}")
            except Exception as e:
                logger.error(f"  ❌ Failed to parse FinancialReport from raw data: {e}")
                return {"error": f"Failed to parse financial report data: {e}"}
        elif isinstance(financial_report, dict):
            # Handle case where financial_report is a dict (due to serialization)
            try:
                financial_report = FinancialReport.model_validate(financial_report)
                logger.debug(f"  ✅ FinancialReport reconstructed from dict: {financial_report.title}")
            except Exception as e:
                logger.error(f"  ❌ Failed to reconstruct FinancialReport: {e}")
                logger.debug("  🔧 Creating fallback FinancialReport with available data...")

                # Create a fallback FinancialReport with available data
                fr_dict = financial_report  # Keep dict reference before reassignment
                financial_report = FinancialReport(  # type: ignore[call-arg]
                    title=fr_dict.get("title", "Daily Financial Report"),  # type: ignore[union-attr]
                    executive_summary=fr_dict.get(  # type: ignore[union-attr]
                        "executive_summary",
                        fr_dict.get("summary", "Financial analysis summary not available"),  # type: ignore[union-attr]
                    )
                    or "Financial analysis summary not available",
                    analyses=[],  # Empty list for now - can be enhanced later
                    suggestions=[],  # Empty list for now - can be enhanced later
                )
                logger.debug(f"  ✅ Fallback FinancialReport created: {financial_report.title}")

        # Return the financial report model object directly for TemplateManager
        # TemplateManager expects the actual model object, not a dictionary
        return {"financial_report_model": financial_report}
