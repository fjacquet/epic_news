import warnings

from epic_news.tools.report_tools import get_report_tools as _get_report_tools


def get_reporting_tools(verbose: bool = False):
    """Deprecated shim. Use `epic_news.tools.report_tools.get_report_tools()` instead.

    Args:
        verbose: Ignored. Kept for backward compatibility.

    Returns:
        list: Tools from `report_tools.get_report_tools()` (RenderReportTool, optionally HtmlToPdfTool).
    """
    warnings.warn(
        "get_reporting_tools() is deprecated. Import from epic_news.tools.report_tools.get_report_tools instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_report_tools()
