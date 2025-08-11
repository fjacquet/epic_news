#!/usr/bin/env python3
"""
Script to regenerate deep research HTML from JSON data using the new modular extractor structure.

This script demonstrates using the DeepResearchExtractor for processing JSON data into
a proper DeepResearchReport model, then generating HTML output.
"""

import json
import os
from datetime import datetime

from epic_news.utils.extractors.deep_research import DeepResearchExtractor
from epic_news.utils.html.template_manager import TemplateManager

# Ensure output directory exists
os.makedirs("output/deep_research", exist_ok=True)

# Load JSON data
try:
    with open("output/deep_research/report.json", encoding="utf-8") as f:
        raw_data = f.read()
    print("✅ Loaded JSON from output/deep_research/report.json")
except FileNotFoundError:
    print("⚠️ No report.json found, creating sample data instead")
    # Create sample data if no file exists
    raw_data = json.dumps(
        {
            "title": "Recherche approfondie: Exemple de sujet",
            "topic": "Exemple de sujet",
            "executive_summary": "Voici un résumé exécutif d'exemple.",
            "key_findings": ["Point clé 1", "Point clé 2"],
            "methodology": "Méthodologie de recherche rigoureuse",
            "sources_count": 2,
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "confidence_level": "High",
            "conclusions": "Conclusions basées sur les recherches.",
            "research_sections": [
                {
                    "title": "Section 1",
                    "content": "Contenu détaillé de la section 1.",
                    "conclusions": "Conclusions de la section 1.",
                    "sources": [
                        {
                            "title": "Source 1",
                            "url": "https://example.com/1",
                            "source_type": "web",
                            "summary": "Résumé de la source 1",
                            "relevance_score": 8,
                            "credibility_score": 7,
                            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
                        }
                    ],
                }
            ],
        }
    )

# Create state data structure as expected by the extractor
state_data = {
    "raw_output": raw_data,
    "crew_type": "DEEPRESEARCH",
    "topic": "Exemple de sujet",  # Fallback topic
    "current_date": datetime.now().strftime("%Y-%m-%d"),
}

# Use the extractor to parse the data
extractor = DeepResearchExtractor()
result = extractor.extract(state_data)

# Get the model from the extraction result
report_model = result["deep_research_model"]

# Generate HTML using TemplateManager
tm = TemplateManager()
html_output_path = "output/deep_research/regenerated_report.html"
html = tm.render_report("DEEPRESEARCH", report_model)
with open(html_output_path, "w", encoding="utf-8") as f:
    f.write(html)
print("✅ Deep research report HTML regenerated successfully")

# Save the model as JSON for reference
with open("output/deep_research/validated_report.json", "w", encoding="utf-8") as f:
    f.write(report_model.model_dump_json(indent=2))
print("✅ Validated model saved to output/deep_research/validated_report.json")
