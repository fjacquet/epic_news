"""
Modèles Pydantic pour le système de recherche approfondie CrewAI.

Ce module définit les structures de données pour l'échange d'informations
entre les agents du système de recherche approfondie et la génération
de rapports structurés en français.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    """Source de recherche avec métadonnées de crédibilité."""

    url: str = Field(description="URL de la source")
    title: str = Field(description="Titre de la source")
    credibility_score: float = Field(description="Score de crédibilité (0.0-1.0)", ge=0.0, le=1.0)
    extraction_date: str = Field(description="Date d'extraction (ISO format)")
    summary: str | None = Field(default=None, description="Résumé du contenu de la source")


class ResearchSection(BaseModel):
    """Section de recherche avec contenu structuré."""

    title: str = Field(description="Titre de la section")
    content: str = Field(description="Contenu détaillé de la section")
    sources: list[ResearchSource] = Field(
        default_factory=list, description="Sources utilisées pour cette section"
    )
    key_findings: list[str] = Field(default_factory=list, description="Découvertes clés de cette section")
    confidence_level: float | None = Field(
        default=None, description="Niveau de confiance dans les informations (0.0-1.0)", ge=0.0, le=1.0
    )


class QuantitativeAnalysis(BaseModel):
    """Résultats d'analyse quantitative avec métriques."""

    methodology: str = Field(description="Méthodologie d'analyse utilisée")
    key_metrics: dict = Field(default_factory=dict, description="Métriques clés calculées")
    statistical_summary: str = Field(description="Résumé statistique")
    visualizations: list[str] = Field(
        default_factory=list, description="Chemins vers les visualisations générées"
    )
    code_executed: str | None = Field(default=None, description="Code Python exécuté pour l'analyse")


class DeepResearchReport(BaseModel):
    """Rapport de recherche approfondie complet."""

    title: str = Field(description="Titre du rapport de recherche")
    executive_summary: str = Field(description="Résumé exécutif")
    methodology: str = Field(description="Méthodologie de recherche utilisée")

    research_sections: list[ResearchSection] = Field(
        default_factory=list, description="Sections de recherche détaillées"
    )

    quantitative_analysis: QuantitativeAnalysis | None = Field(
        default=None, description="Analyse quantitative si applicable"
    )

    key_findings: list[str] = Field(
        default_factory=list, description="Découvertes principales de la recherche"
    )

    conclusions: str = Field(description="Conclusions de la recherche")

    recommendations: list[str] = Field(
        default_factory=list, description="Recommandations basées sur la recherche"
    )

    limitations: list[str] = Field(default_factory=list, description="Limitations de la recherche")

    sources: list[ResearchSource] = Field(default_factory=list, description="Toutes les sources utilisées")

    generation_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="Date de génération du rapport"
    )

    research_duration: str | None = Field(default=None, description="Durée de la recherche")

    quality_score: float | None = Field(
        default=None, description="Score de qualité global (0.0-1.0)", ge=0.0, le=1.0
    )

    class Config:
        """Configuration Pydantic."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "title": "État de l'Art d'Apache Tomcat : Analyse Approfondie",
                "executive_summary": "Cette recherche examine l'état actuel d'Apache Tomcat...",
                "methodology": "Recherche documentaire combinée à une analyse quantitative...",
                "research_sections": [
                    {
                        "title": "Architecture et Performance",
                        "content": "Apache Tomcat présente une architecture modulaire...",
                        "key_findings": ["Performance améliorée de 15% en version 10.x"],
                        "sources": [],
                    }
                ],
                "key_findings": [
                    "Tomcat 10.x offre des performances significativement améliorées",
                    "Migration vers Jakarta EE nécessite une planification",
                ],
                "conclusions": "Apache Tomcat reste une solution robuste...",
                "recommendations": [
                    "Migrer vers Tomcat 10.x pour les nouvelles applications",
                    "Planifier la migration Jakarta EE pour les applications existantes",
                ],
            }
        }
