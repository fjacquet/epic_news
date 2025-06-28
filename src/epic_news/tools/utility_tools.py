from .reporting_tool import ReportingTool


def get_reporting_tools(verbose: bool = False):
    """Factory function to get all reporting tools with verbosity control."""
    return [ReportingTool(verbose=verbose)]
