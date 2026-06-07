# Project Roadmap & Task List

This document outlines the development roadmap, current tasks, and a history of completed work for the Epic News project.

## 🚀 Next Up (Priority)

*All priority tasks completed! See Changelog for details.*

## 📝 To-Do

### Deep Research System Implementation (Priority)

#### Phase 1: Infrastructure de Base (2-3 jours) ✅ TERMINÉ

- [x] **Modèles Pydantic DeepResearch:** ✅ Créé les modèles `ResearchSource`, `ResearchSection`, `QuantitativeAnalysis`, et `DeepResearchReport` dans `src/epic_news/models/crews/deep_research.py`
- [x] **Extension ContentState:** ✅ Confirmé que le champ `deep_research_report` existe déjà pour supporter DeepResearchReport
- [x] **DeepResearchExtractor:** ✅ Créé l'extracteur dans `src/epic_news/utils/content_extractors.py` et enregistré dans ContentExtractorFactory
- [x] **Template HTML:** ✅ Confirmé que DeepResearchRenderer existe et est intégré dans RendererFactory pour TemplateManager
- [x] **Flow Integration:** ✅ Modernisé `generate_deep_research()` dans main.py avec ContentExtractorFactory et TemplateManager

#### Phase 2: Agents et Configuration (3-4 jours) ✅ TERMINÉ

- [x] **Configuration YAML Complète:** ✅ Confirmé `agents.yaml` avec 4 agents spécialisés (primary_researcher, wikipedia_specialist, content_analyst, report_generator)
- [x] **Tâches Structurées:** ✅ Confirmé `tasks.yaml` avec `output_pydantic=DeepResearchReport` pour la tâche finale
- [x] **Outils Spécialisés:** ✅ Intégré ScrapeNinjaTool, SerperDevTool, WikipediaSearchTool, WikipediaArticleTool dans DeepResearchCrew
- [x] **Rôles Français:** ✅ Confirmé backstories, goals, et rôles professionnels en français pour chaque agent
- [x] **Sequential Process:** ✅ Configuré `Process.sequential` avec async_execution pour optimisation des performances
- [x] **Tests d'Intégration:** ✅ Validé avec script de test complet - 4 agents, 4 tâches, génération HTML (10,808 caractères)

#### Phase 3: REFONTE ACADÉMIQUE DEEP RESEARCH (5-7 jours) - CRITIQUE ⚠️ REFONTE COMPLÈTE

**ANALYSE YAML TERMINÉE:** Architecture 6-agents correcte MAIS écarts critiques identifiés vs spécifications académiques PhD

**ÉCARTS CRITIQUES IDENTIFIÉS:**

- ❌ **Code Interpreter manquant:** Agent data_analyst sans outils quantitatifs (OBLIGATOIRE pour analyse statistique)
- ❌ **Pas de CrewAI Flow:** Utilise crew séquentiel basique vs orchestration dynamique (@listen/@router)
- ❌ **Pas de modèles Pydantic:** Communication inter-agents par texte vs données structurées
- ❌ **Validation qualité insuffisante:** Pas de seuils quantitatifs ni re-planification adaptative
- ❌ **Rapports superficiels:** 5k caractères vs 20+ pages académiques requises

**PLAN DE REFONTE ACADÉMIQUE:**

##### Phase 3A: Infrastructure Critique (2-3 jours) ✅ TERMINÉ

- [x] **Analyse YAML Complète:** ✅ Confirmé architecture 6-agents mais écarts fonctionnels critiques
- [x] **Code Interpreter Integration:** ✅ Ajouté allow_code_execution=True à data_analyst (Docker installé, fonctionnel)
- [x] **Modèles Pydantic Académiques:** ✅ Créé ResearchPlan, CollectedData, QuantitativeAnalysis, QualityAssessment, ResearchState, AcademicReport dans `deep_research_academic.py`
- [x] **CrewAI Flow Dynamique:** ✅ Implémenté @start(), @listen(), @router() dans DeepResearchFlowAcademicFixed et DeepResearchFlowPhD

##### Phase 3B: Standards Académiques (3-4 jours) 🚀 EN COURS

- [ ] **Structure Rapport Académique:** Implémenter sections obligatoires complètes (résumé exécutif, revue littérature, méthodologie, analyse quantitative, conclusions)
- [ ] **Validation Qualité Rigoureuse:** Renforcer seuils quantitatifs (15k+ mots, 30+ sources, analyses statistiques avec Code Interpreter)
- [ ] **Boucles Itératives Avancées:** Améliorer re-planification automatique et validation multi-critères
- [ ] **Tests Académiques Approfondis:** Validation end-to-end avec sujets complexes et métriques PhD
- [ ] **Optimisation Longueur:** Atteindre consistamment 15,000+ mots vs 750 mots actuels
- [ ] **Analyse Quantitative Réelle:** Exploiter pleinement Code Interpreter pour calculs statistiques, visualisations, tests d'hypothèses

#### Phase 4: CrewAI Code Interpreter (3-4 jours) - CRITIQUE URGENT

**MANQUE CRITIQUE:** Aucune analyse quantitative/statistique dans le rapport actuel (exigence PhD)

- [ ] **Configuration Docker:** Configurer environnement Docker pour exécution de code sécurisée
- [ ] **Intégration Analyste:** Ajouter Code Interpreter à l'agent Analyste de Données (OBLIGATOIRE pour deep research)
- [ ] **Dépendances Python:** Configurer pandas, numpy, scipy, matplotlib, seaborn dans l'environnement
- [ ] **Scripts d'Analyse:** Développer templates d'analyse statistique (corrélations, tendances, visualisations)
- [ ] **Sécurité:** Implémenter isolation et validation des inputs pour exécution de code
- [ ] **Tests Quantitatifs:** Valider capacités d'analyse statistique et génération de graphiques
- [ ] **Intégration Rapport:** Assurer que les analyses quantitatives sont intégrées dans le rapport final HTML

#### Phase 5: Validation Académique et Tests (3-4 jours) - STANDARDS PhD

**OBJECTIF:** Atteindre niveau académique PhD avec rapports de dizaines de pages

- [ ] **Tests End-to-End Académiques:** Valider génération de rapports de 20+ pages avec structure académique complète
- [ ] **Validation Méthodologique:** Tester planification → collecte → analyse → synthèse → validation
- [ ] **Standards Académiques:** Vérifier format PhD (résumé exécutif, méthodologie, analyse quantitative, conclusions, références)
- [ ] **Validation Française:** Tester qualité linguistique et standards académiques français
- [ ] **Tests Quantitatifs:** Valider analyses statistiques, graphiques, et interprétations
- [ ] **Tests de Performance:** Optimiser pour analyses quantitatives lourdes et rapports volumineux
- [ ] **Tests de Régression:** Vérifier compatibilité avec crews existants
- [ ] **Benchmarking Qualité:** Comparer avec standards de recherche académique réels
- [ ] **Documentation:** Mettre à jour guides utilisateur et documentation technique

#### Phase 6: Refonte Critique Deep Research (URGENT - 5-7 jours)

**STATUT ACTUEL:** ❌ ÉCHEC - Rapport généré = résumé simpliste (5k caractères) vs exigences PhD

**ACTIONS IMMÉDIATES:**

- [ ] **Audit Complet:** Analyser écarts entre implémentation actuelle et spécifications docs/99_deep_research.md
- [ ] **Refonte Architecture:** Remplacer flux v2 simpliste par architecture académique complète
- [ ] **Agents Spécialisés:** Implémenter les 6 agents selon spécification (Stratège, Collecteur, Wikipedia, Analyste+Code, Rédacteur, QA)
- [ ] **Orchestration Dynamique:** Créer flux CrewAI avec @listen/@router pour re-planification adaptative
- [ ] **Analyse Quantitative:** Intégrer Code Interpreter pour analyses statistiques obligatoires
- [ ] **Format Académique:** Développer templates HTML pour rapports de niveau PhD (20+ pages)
- [ ] **Validation Qualité:** Implémenter boucles de validation et amélioration continue
- [ ] **Test Réel:** Valider avec sujet complexe et mesurer qualité académique vs standards PhD

**CRITÈRES DE SUCCÈS:**

- ✅ Rapport de 20+ pages avec structure académique complète
- ✅ Analyse quantitative avec graphiques et statistiques
- ✅ Méthodologie rigoureuse multi-étapes documentée
- ✅ Re-planification dynamique et validation qualité
- ✅ Format HTML professionnel niveau publication académique

### Code Cleanup and Maintenance

- [ ] **Remove Unused and Deprecated Code:** Systematically review the `src/` directory to remove commented-out code blocks, unused imports, and other dead code to improve readability and maintainability.
  - **Example File:** `src/epic_news/crews/company_news/company_news_crew.py`

### Containerization

- [ ] **Verify CrewAI Execution in Docker:** Finalize and verify the setup for running CrewAI reliably within a containerized environment.

## 📋 Backlog (Future Tasks)

- [ ] **n8n Integration:**
  - [ ] Connect n8n to retrieve data initiated by CrewAI.
  - [ ] Connect n8n to initiate CrewAI workflows.
- [ ] **Technology Watch Agents:** Create new agents for monitoring and reporting on various technologies (Nutanix, Netbackup, Commvault, etc.).
- [ ] **Free API Integration:** Research, evaluate, and integrate valuable free APIs to expand the project's data-gathering capabilities.

## ✅ Changelog (Completed Tasks)

### Q3 2025

- **DeepResearchCrew Integration (July 2025):**

- **Menu Designer Integration & Recipe Generation (July 2025):**
  - **End-to-End Workflow:** Successfully implemented complete menu planning to recipe generation integration with 30 recipes generated from weekly menu plans.
  - **Menu Parser Fix:** Updated `MenuGenerator.parse_menu_structure()` to handle new 'dishes' array format while maintaining backward compatibility with old starter/main_course/dessert structure.
  - **Recipe Generation:** Fixed CookingCrew template variable issues (patrika_file, output_file) enabling generation of both JSON and YAML recipe formats.
  - **HTML Rendering:** Fixed MenuRenderer to properly extract and display actual dish names from JSON menu structure instead of generic placeholders.
  - **Production Ready:** Complete integration now processes all dishes from validated weekly menu plans and generates individual recipes with proper file naming.

- **Comprehensive Test Quality Assurance (July 2025):**
  - **Test Suite Excellence:** Achieved 461 tests passing with only 5 skipped, zero failures across the entire project.
  - **Coverage & Quality:** Generated comprehensive test coverage reports and maintained high code quality standards.
  - **Bug Documentation:** Created detailed bug reports and systematic QA processes following project development principles.
  - **Test Infrastructure:** Enhanced test reliability with proper fixtures, mocking, and cross-platform compatibility.
  - **Lint & Format:** All code passes Ruff formatting and linting checks with zero issues.

- **Project Structure & Code Quality Improvements (Q3 2025):**
  - **ContentState Model Refactoring:** Replaced `Union[Any, None]` fields with specific Pydantic models for improved type safety and data clarity.
  - **Pydantic Standardization:** Consistently used `Optional[X]` instead of `Union[X, None]` across all models for better compatibility.
  - **Script Organization:** Relocated helper scripts from `src/epic_news/bin` to top-level `scripts/` directory for better separation of concerns.
  - **Logging Consistency:** Standardized `app.py` to use `loguru` for consistent logging across the entire application.

- **Complete HTML Rendering Integration (Q3 2025):**
  - **OSINT Crews Integration:** Successfully connected HTML rendering pipeline for all 9 OSINT and specialized crews.
  - **Crew Coverage:** Integrated `company_profiler`, `cross_reference_report_crew`, `geospatial_analysis`, `hr_intelligence`, `legal_analysis`, `menu_designer`, `sales_prospecting`, `tech_stack`, and `web_presence`.
  - **Unified Reporting:** All crews now generate consistent, professional HTML reports with proper styling and data presentation.

- **Pydantic Model & OSINT Crew Refactoring:**
  - **Structured Outputs:** Refactored 8 OSINT crews (`CompanyProfiler`, `CrossReferenceReport`, `GeospatialAnalysis`, `HRIntelligence`, `LegalAnalysis`, `WebPresence`, `TechStack`) to use Pydantic models for structured, reliable outputs.
  - **Centralized Models:** Relocated all crew-specific Pydantic models to a dedicated `src/epic_news/models/crews/` directory, improving project structure and modularity.
  - **Comprehensive Testing:** Created and validated unit tests for all new and relocated models to ensure data integrity.
  - **Project-Wide Updates:** Updated all import paths across the project to reflect the new model locations and fixed all resulting test failures.

- **HTML Reporting System:**
  - **Cross-Reference Report:** Implemented a complete HTML report generation pipeline for the Cross-Reference Crew, including an HTML factory, a Jinja2 template, and a dynamic regeneration script.
  - **Main Integration:** Integrated the HTML generation logic into the main application entry point.

- **Logging Modernization:**
  - **Loguru Integration:** Replaced the standard `logging` module with `loguru` across the core application for more powerful and configurable logging.
  - **Configuration:** Set up `loguru` sinks for both console and file-based logging.
  - **Documentation:** Updated the development guide to reflect the new logging standards.

- **Advanced Testing Libraries:**
  - **Dependencies:** Integrated `Faker` and `pytest-mock` to enhance the testing framework with realistic data generation and mocking.
  - **Standards:** Created sample tests and updated the development guide to establish new testing best practices.

- **Initial Dockerization Setup:**
  - **Dockerfiles:** Created `Dockerfile.api` and `Dockerfile.streamlit` to containerize the application components.
  - **Compose Files:** Set up `docker-compose.yml` files for orchestrating the development and production environments.

- **HTML Rendering for Core Crews:**
  - **Integrated 16 crews** with the HTML rendering pipeline, including `classify`, `company_news`, `cooking`, `fin_daily`, `holiday_planner`, and more.
