"""
Modèles Pydantic pour le système Deep Research Académique
Structures de données pour communication inter-agents et validation qualité
"""

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field, validator


class ResearchPlan(BaseModel):
    """Plan de recherche stratégique avec méthodologie et critères qualité"""

    topic: str = Field(..., description="Sujet de recherche principal")
    scope: str = Field(..., description="Portée et limites de la recherche")
    objectives: list[str] = Field(..., description="Objectifs de recherche principaux")
    research_questions: list[str] = Field(..., description="Questions de recherche clés")
    methodology: str = Field(..., description="Méthodologie de recherche détaillée")
    data_sources: list[str] = Field(..., description="Sources de données à explorer")
    quality_criteria: dict[str, float] = Field(..., description="Critères de qualité quantitatifs")
    timeline: dict[str, str] = Field(..., description="Calendrier et priorités")
    expected_depth: str = Field(default="PhD", description="Niveau de profondeur attendu")

    @validator("quality_criteria")
    def validate_quality_criteria(cls, v):
        required_criteria = ["min_word_count", "min_sources", "min_statistical_tests"]
        for criterion in required_criteria:
            if criterion not in v:
                raise ValueError(f"Critère qualité manquant: {criterion}")
        return v


class CollectedData(BaseModel):
    """Données collectées avec métadonnées de qualité"""

    source_url: str = Field(..., description="URL de la source")
    source_type: str = Field(..., description="Type de source (web, academic, wikipedia, etc.)")
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="Score de crédibilité (0-1)")
    content: str = Field(..., description="Contenu extrait")
    extraction_date: datetime = Field(default_factory=datetime.now)
    key_findings: list[str] = Field(..., description="Découvertes clés extraites")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Score de pertinence")
    data_quality: str = Field(..., description="Évaluation qualitative des données")

    @validator("credibility_score", "relevance_score")
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Les scores doivent être entre 0.0 et 1.0")
        return v


class QuantitativeAnalysis(BaseModel):
    """Analyse quantitative avec métriques statistiques"""

    analysis_type: str = Field(..., description="Type d'analyse (descriptive, corrélation, etc.)")
    metrics: dict[str, Union[float, int]] = Field(..., description="Métriques calculées")
    statistical_tests: list[str] = Field(..., description="Tests statistiques effectués")
    p_values: dict[str, float] = Field(default_factory=dict, description="Valeurs p des tests")
    confidence_intervals: dict[str, list[float]] = Field(
        default_factory=dict, description="Intervalles de confiance"
    )
    effect_sizes: dict[str, float] = Field(default_factory=dict, description="Tailles d'effet")
    visualizations: list[str] = Field(..., description="Graphiques et visualisations générés")
    code_executed: str = Field(..., description="Code Python exécuté pour l'analyse")
    interpretation: str = Field(..., description="Interprétation des résultats statistiques")
    limitations: list[str] = Field(..., description="Limitations de l'analyse")

    @validator("p_values")
    def validate_p_values(cls, v):
        for test, p_val in v.items():
            if not 0.0 <= p_val <= 1.0:
                raise ValueError(f"Valeur p invalide pour {test}: {p_val}")
        return v


class QualityAssessment(BaseModel):
    """Évaluation qualité avec seuils et recommandations"""

    overall_score: float = Field(..., ge=0.0, le=1.0, description="Score qualité global")
    word_count: int = Field(..., description="Nombre de mots du rapport")
    source_count: int = Field(..., description="Nombre de sources utilisées")
    credible_source_ratio: float = Field(..., ge=0.0, le=1.0, description="Ratio sources crédibles")
    statistical_analysis_present: bool = Field(..., description="Présence d'analyse statistique")
    academic_structure_score: float = Field(..., ge=0.0, le=1.0, description="Score structure académique")
    factual_accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Score précision factuelle")
    coherence_score: float = Field(..., ge=0.0, le=1.0, description="Score cohérence logique")

    # Seuils qualité PhD
    quality_thresholds: dict[str, Union[int, float]] = Field(
        default={
            "min_word_count": 15000,
            "min_sources": 25,
            "min_credible_ratio": 0.8,
            "min_overall_score": 0.85,
            "min_academic_structure": 0.9,
        }
    )

    meets_phd_standards: bool = Field(default=False, description="Respecte les standards PhD")
    improvement_recommendations: list[str] = Field(..., description="Recommandations d'amélioration")
    requires_replanning: bool = Field(default=False, description="Nécessite re-planification")

    def __init__(self, **data):
        super().__init__(**data)
        self.meets_phd_standards = self._assess_phd_standards()
        self.requires_replanning = not self.meets_phd_standards

    def _assess_phd_standards(self) -> bool:
        """Évalue si le rapport respecte les standards PhD"""
        thresholds = self.quality_thresholds

        checks = [
            self.word_count >= thresholds["min_word_count"],
            self.source_count >= thresholds["min_sources"],
            self.credible_source_ratio >= thresholds["min_credible_ratio"],
            self.overall_score >= thresholds["min_overall_score"],
            self.academic_structure_score >= thresholds["min_academic_structure"],
            self.statistical_analysis_present,
        ]

        return all(checks)


class ResearchState(BaseModel):
    """État global de la recherche pour orchestration dynamique"""

    research_id: str = Field(..., description="Identifiant unique de la recherche")
    topic: str = Field(..., description="Sujet de recherche")
    current_phase: str = Field(default="planning", description="Phase actuelle")

    # Données des phases
    research_plan: Optional[ResearchPlan] = None
    collected_data: list[CollectedData] = Field(default_factory=list)
    quantitative_analysis: Optional[QuantitativeAnalysis] = None
    quality_assessment: Optional[QualityAssessment] = None

    # Métadonnées d'orchestration
    iteration_count: int = Field(default=1, description="Nombre d'itérations")
    max_iterations: int = Field(default=3, description="Maximum d'itérations autorisées")
    phase_history: list[str] = Field(default_factory=list, description="Historique des phases")

    # Statut et contrôle qualité
    is_complete: bool = Field(default=False, description="Recherche terminée")
    needs_replanning: bool = Field(default=False, description="Nécessite re-planification")
    error_messages: list[str] = Field(default_factory=list, description="Messages d'erreur")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def advance_phase(self, next_phase: str):
        """Avance vers la phase suivante"""
        self.phase_history.append(self.current_phase)
        self.current_phase = next_phase
        self.updated_at = datetime.now()

    def trigger_replanning(self, reason: str):
        """Déclenche une re-planification"""
        self.needs_replanning = True
        self.iteration_count += 1
        self.error_messages.append(f"Re-planification requise: {reason}")
        self.current_phase = "planning"
        self.updated_at = datetime.now()

    def can_continue_iteration(self) -> bool:
        """Vérifie si une nouvelle itération est possible"""
        return self.iteration_count < self.max_iterations

    def get_completion_status(self) -> dict[str, Union[bool, str, int]]:
        """Retourne le statut de completion"""
        return {
            "is_complete": self.is_complete,
            "current_phase": self.current_phase,
            "iteration": self.iteration_count,
            "meets_standards": self.quality_assessment.meets_phd_standards
            if self.quality_assessment
            else False,
            "word_count": self.quality_assessment.word_count if self.quality_assessment else 0,
            "source_count": len(self.collected_data),
        }


class AcademicReport(BaseModel):
    """Rapport académique final avec structure PhD"""

    title: str = Field(..., description="Titre du rapport")
    topic: str = Field(..., description="Sujet de recherche")

    # Structure académique
    executive_summary: str = Field(..., description="Résumé exécutif (2-3 pages)")
    introduction: str = Field(..., description="Introduction et contexte")
    literature_review: str = Field(..., description="Revue de littérature (5-8 pages)")
    methodology: str = Field(..., description="Méthodologie (2-3 pages)")
    quantitative_analysis: str = Field(..., description="Analyse quantitative (5-10 pages)")
    discussion: str = Field(..., description="Discussion des résultats")
    conclusions: str = Field(..., description="Conclusions et recommandations")
    references: list[str] = Field(..., description="Références bibliographiques")
    appendices: str = Field(default="", description="Annexes")

    # Métadonnées qualité
    word_count: int = Field(..., description="Nombre total de mots")
    source_count: int = Field(..., description="Nombre de sources")
    statistical_tests_count: int = Field(..., description="Nombre de tests statistiques")
    visualization_count: int = Field(..., description="Nombre de visualisations")

    # Validation académique
    academic_level: str = Field(default="PhD", description="Niveau académique")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Score qualité global")

    created_at: datetime = Field(default_factory=datetime.now)

    @validator("word_count")
    def validate_word_count(cls, v):
        if v < 15000:  # Minimum PhD standard
            raise ValueError(f"Rapport trop court: {v} mots (minimum 15,000)")
        return v

    def to_html(self) -> str:
        """Génère le rapport en format HTML académique"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.title}</title>
            <style>
                body {{ font-family: 'Times New Roman', serif; line-height: 1.6; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .section {{ margin: 30px 0; }}
                .section h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .references {{ font-size: 0.9em; }}
                .metadata {{ background: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 {self.title}</h1>
                <p><strong>Recherche Académique Approfondie</strong></p>
                <p>Généré le {self.created_at.strftime("%d/%m/%Y")}</p>
            </div>
            
            <div class="metadata">
                <h3>🎯 Métadonnées de Qualité</h3>
                <ul>
                    <li><strong>Nombre de mots:</strong> {self.word_count:,}</li>
                    <li><strong>Sources utilisées:</strong> {self.source_count}</li>
                    <li><strong>Tests statistiques:</strong> {self.statistical_tests_count}</li>
                    <li><strong>Visualisations:</strong> {self.visualization_count}</li>
                    <li><strong>Score qualité:</strong> {self.quality_score:.2%}</li>
                    <li><strong>Niveau académique:</strong> {self.academic_level}</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>📋 Résumé Exécutif</h2>
                {self.executive_summary}
            </div>
            
            <div class="section">
                <h2>🎯 Introduction</h2>
                {self.introduction}
            </div>
            
            <div class="section">
                <h2>📚 Revue de Littérature</h2>
                {self.literature_review}
            </div>
            
            <div class="section">
                <h2>🔬 Méthodologie</h2>
                {self.methodology}
            </div>
            
            <div class="section">
                <h2>📊 Analyse Quantitative</h2>
                {self.quantitative_analysis}
            </div>
            
            <div class="section">
                <h2>💭 Discussion</h2>
                {self.discussion}
            </div>
            
            <div class="section">
                <h2>🎯 Conclusions</h2>
                {self.conclusions}
            </div>
            
            <div class="section references">
                <h2>📖 Références</h2>
                <ol>
                    {"".join(f"<li>{ref}</li>" for ref in self.references)}
                </ol>
            </div>
            
            {f'<div class="section"><h2>📎 Annexes</h2>{self.appendices}</div>' if self.appendices else ""}
        </body>
        </html>
        """
        return html_content
