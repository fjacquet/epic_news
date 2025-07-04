# epic_news Output Formatting Guide

This document establishes the definitive standards for all reports generated by epic_news agents. All agents must adhere to these guidelines to ensure consistent and high-quality results.

## General Principles

The primary output of each epic_news crew is a comprehensive HTML report. This report should be well-structured, easy to read, and contain all the necessary information for a human to make an informed decision.

### ⚠️ Critical Reminders

* **DO NOT** return raw API responses as your task result.
* **DO NOT** include placeholder text like 'TODO' in the final report.
* **ALWAYS** ensure your final output is a single, complete, and well-formed HTML document.

## HTML Report Standards

### HTML Structure & Formatting

* Use proper HTML5 document structure (`<!DOCTYPE html>`).
* Use UTF-8 encoding (`<meta charset="UTF-8">`) for emoji support.
* Structure content with appropriate heading levels (h1-h6) and semantic elements (sections, tables, lists).
* Include a clear title and publication date.
* Use tables for comparative data and lists for sequential information.
* Use emphasis (bold/italic) for important points.

### HTML Content Requirements

* Present information in logical sections with clear headings.
* Include data sources and methodology where applicable.
* Provide actionable conclusions and recommendations.
* Include real, verifiable ticker symbols for all financial instruments.

### HTML Prohibited Elements

* No raw JSON data, API responses, or debugging information.
* No placeholder text or TODOs.
* No unclosed or malformed HTML tags.

### Emoji Usage Guidelines

Use emojis strategically to highlight key points:

* 📈 Growth trends, positive performance
* 📉 Decline trends, negative performance
* 🔍 Analysis insights, detailed examination
* 🌐 Global factors, market-wide considerations
* 🚀 High-growth potential, emerging opportunities
* ⚠️ Risk indicators, warnings
* 💰 Financial metrics, monetary values
* ⏱️ Time horizons, temporal considerations
* 📊 Data visualization, statistics
* 🛡️ Defensive strategies, capital preservation
* 👨‍💼 Management quality, governance
* 💡 Innovation, competitive advantage

## Implementation Example & Quality Checklist

### ✅ Best-Practice Implementation

The final agent in a crew is typically responsible for consolidating all prior information into a single, comprehensive HTML report. Preceding agents should pass their findings through the task context. The final agent then retrieves this information from the context, synthesizes it, and formats the final HTML report. This is returned as a string that is then saved to a file by the crew's configuration.

```python
# Example of a final agent's action

# Consolidate findings from previous tasks (context)
consolidated_findings = context.get("consolidated_analysis", "No analysis found.")

# Structure the final HTML report
final_report_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Comprehensive Financial Report</title>
</head>
<body>
    <h1>📊 epic_news Integrated Report</h1>
    <p><strong>Date:</strong> {current_date}</p>
    <section>
        <h2>Executive Summary</h2>
        <p>This report integrates findings from our specialized crews...</p>
    </section>
    <section>
        <h2>Detailed Analysis</h2>
        <div>{consolidated_findings}</div>
    </section>
</body>
</html>
"""

return final_report_html # The crew will handle saving this to a file.
```

### Quality Checklist

1. **Validate HTML:** Ensure the final output is well-formed HTML with correct structure and UTF-8 encoding.
2. **Completeness:** Confirm all required sections and data points from the analysis are present.
3. **Accuracy:** Verify that all data, especially ticker symbols and financial figures, are correct.
4. **Clarity:** Ensure the content is readable, actionable, and free of jargon.
5. **No Raw Data:** Confirm that no raw API responses or debugging information is included in the final report.
