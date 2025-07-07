# Pydantic Implementation and Toolless Reporter Plan

This document outlines the plan to refactor five crews to use Pydantic models for structured output and implement the "Toolless Reporter" pattern to ensure clean, high-quality reports.

## 1. Core Principles

- **Structured Output**: All final tasks will use `output_pydantic` to enforce a strict, predictable data structure.
- **Toolless Reporter Pattern**: The final task of each crew will be executed by an agent with no tools assigned, preventing CrewAI from writing action traces into the final report.
- **Centralized Models**: All new Pydantic models will be defined in a new file: `src/epic_news/models/report_models.py`.
- **Configuration-Driven**: Agent and task configurations, including agent assignments, will be updated in their respective YAML files. Python code will not override these assignments.

## 2. Analysis of Existing Outputs (`/output/osint/`)

A review of the JSON files in the `/output/osint/` directory reveals the core issue this refactoring aims to solve: **output inconsistency**.

- **Actionable, Structured JSON**: Files like `Temenos Group_employee_sentiment_analysis.json` and `Temenos Group_hr_intelligence_report.json` contain well-formed, deeply nested JSON that is immediately machine-readable and useful. This is the desired state.
- **Unstructured Tool Calls**: Files like `Temenos Group_core_info.json` and `Temenos Group_history.json` contain raw tool calls (e.g., `Search the internet with Serper`). This is the primary problem caused by agents with tools writing their actions to the output file. The "Toolless Reporter" pattern will eliminate this entirely.
- **Mixed Content**: Some files contain a mix of thoughts from the agent and a final JSON object. While the JSON is present, the extraneous text makes direct parsing difficult.

This analysis confirms that enforcing a Pydantic model on a toolless final agent is the correct approach to guarantee clean, predictable, and purely data-driven outputs.

## 3. New Pydantic Models

The following Pydantic models will be created in `src/epic_news/models/report_models.py`. These models are designed based on the `expected_output` descriptions in the `tasks.yaml` files.

```python
# src/epic_news/models/report_models.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Using legacy Union and Optional for CrewAI compatibility
from typing import Union

class CompanyCoreInfo(BaseModel):
    legal_name: str = Field(..., description="Full legal name of the company.")
    parent_company: Optional[str] = Field(None, description="Parent company, if any.")
    subsidiaries: List[str] = Field(default_factory=list, description="List of subsidiary companies.")
    year_founded: int = Field(..., description="Year the company was founded.")
    headquarters_location: str = Field(..., description="Headquarters location.")
    industry_classification: str = Field(..., description="Primary industry.")
    business_activities: List[str] = Field(..., description="List of primary business activities.")
    employee_count: Optional[int] = Field(None, description="Number of employees.")
    revenue: Optional[float] = Field(None, description="Annual revenue.")
    market_cap: Optional[float] = Field(None, description="Market capitalization if public.")
    corporate_structure: str = Field(..., description="Description of the corporate structure.")
    ownership_details: str = Field(..., description="Details about ownership.")
    mission_statement: Optional[str] = Field(None, description="Company's mission statement.")
    core_values: List[str] = Field(default_factory=list, description="List of core values.")

class CompanyHistory(BaseModel):
    key_milestones: List[str] = Field(..., description="Key historical milestones.")
    founding_story: str = Field(..., description="The story of the company's founding.")
    strategic_shifts: List[str] = Field(default_factory=list, description="Major strategic shifts or pivots.")
    acquisitions_and_mergers: List[Dict[str, Any]] = Field(default_factory=list, description="List of acquisitions and mergers.")
    leadership_changes: List[Dict[str, Any]] = Field(default_factory=list, description="Significant leadership changes.")
    major_product_launches: List[str] = Field(default_factory=list, description="Major product launches.")
    challenges_or_controversies: List[str] = Field(default_factory=list, description="Significant challenges or controversies.")

class Financials(BaseModel):
    revenue_and_profit_trends: List[Dict[str, Any]] = Field(..., description="Revenue and profit trends over 3-5 years.")
    key_financial_ratios: Dict[str, float] = Field(..., description="Key financial ratios.")
    funding_rounds: List[Dict[str, Any]] = Field(default_factory=list, description="Information on funding rounds.")
    major_investors: List[str] = Field(default_factory=list, description="List of major investors.")
    debt_structure: Optional[str] = Field(None, description="Description of the debt structure.")
    recent_financial_news: List[str] = Field(default_factory=list, description="Recent financial news.")

class MarketPosition(BaseModel):
    market_share: Optional[str] = Field(None, description="Estimated market share.")
    competitive_landscape: str = Field(..., description="Description of the competitive landscape.")
    key_competitors: List[str] = Field(..., description="List of key competitors.")
    comparative_advantages: List[str] = Field(..., description="List of comparative advantages.")
    industry_trends: List[str] = Field(..., description="Industry trends affecting the company.")
    growth_opportunities: List[str] = Field(..., description="Growth opportunities.")
    challenges: List[str] = Field(..., description="Market challenges.")

class ProductsAndServices(BaseModel):
    core_product_lines: List[str] = Field(..., description="Core product or service lines.")
    recent_launches: List[str] = Field(default_factory=list, description="Recent product launches.")
    discontinued_offerings: List[str] = Field(default_factory=list, description="Discontinued products.")
    pricing_strategy: Optional[str] = Field(None, description="Description of the pricing strategy.")
    customer_segments: List[str] = Field(..., description="Primary customer segments.")

class Management(BaseModel):
    key_executives: List[Dict[str, Any]] = Field(..., description="List of key executives and their backgrounds.")
    board_of_directors: List[str] = Field(..., description="List of board members.")
    management_style: Optional[str] = Field(None, description="Description of the management style.")
    corporate_culture: str = Field(..., description="Description of the corporate culture.")

class LegalCompliance(BaseModel):
    regulatory_framework: str = Field(..., description="Governing regulatory framework.")
    compliance_history: List[str] = Field(..., description="History of compliance and violations.")
    ongoing_litigation: List[str] = Field(default_factory=list, description="Ongoing or past litigation.")
    regulatory_filings: List[str] = Field(default_factory=list, description="Recent regulatory filings.")

class CompanyProfileReport(BaseModel):
    """Comprehensive company profile report."""
    company_name: str = Field(..., description="The name of the company being profiled.")
    core_info: CompanyCoreInfo
    history: CompanyHistory
    financials: Financials
    market_position: MarketPosition
    products_and_services: ProductsAndServices
    management: Management
    legal_compliance: LegalCompliance

class CrossReferenceReport(BaseModel):
    """Global intelligence report cross-referencing multiple data points."""
    target: str = Field(..., description="The target of the intelligence report.")
    executive_summary: str = Field(..., description="High-level summary of key findings.")
    detailed_findings: Dict[str, Any] = Field(..., description="A structured dictionary containing synthesized intelligence from all sources.")
    confidence_assessment: str = Field(..., description="Assessment of the confidence level in the findings.")
    information_gaps: List[str] = Field(default_factory=list, description="Identified information gaps.")

class GeospatialAnalysisReport(BaseModel):
    """Geospatial analysis report for a company."""
    company_name: str = Field(..., description="The name of the company.")
    physical_locations: List[Dict[str, Any]] = Field(..., description="Mapping of physical locations.")
    risk_assessment: List[Dict[str, Any]] = Field(..., description="Geospatial risk assessment.")
    supply_chain_map: List[Dict[str, Any]] = Field(..., description="Geospatial mapping of the supply chain.")
    mergers_and_acquisitions_insights: List[Dict[str, Any]] = Field(..., description="Geospatial intelligence for M&A.")

class HRIntelligenceReport(BaseModel):
    """Human Resources intelligence report."""
    company_name: str = Field(..., description="The name of the company.")
    leadership_assessment: Dict[str, Any] = Field(..., description="Assessment of the leadership team.")
    employee_sentiment: Dict[str, Any] = Field(..., description="Analysis of employee sentiment.")
    organizational_culture: Dict[str, Any] = Field(..., description="Assessment of the organizational culture.")
    talent_acquisition_strategy: Dict[str, Any] = Field(..., description="Analysis of talent acquisition strategy.")
    summary_and_recommendations: str = Field(..., description="Executive summary and recommendations.")

class LegalAnalysisReport(BaseModel):
    """Legal analysis report for a company."""
    company_name: str = Field(..., description="The name of the company.")
    compliance_assessment: Dict[str, Any] = Field(..., description="Assessment of legal compliance status.")
    ip_portfolio_analysis: Dict[str, Any] = Field(..., description="Analysis of the intellectual property portfolio.")
    regulatory_risk_assessment: Dict[str, Any] = Field(..., description="Assessment of regulatory risks.")
    litigation_history: List[Dict[str, Any]] = Field(..., description="Analysis of litigation history.")
    ma_due_diligence: Dict[str, Any] = Field(..., description="Legal due diligence for M&A activities.")
```

## 4. Agent and Task Modifications

For each crew, a dedicated "reporter" agent will be used for the final task. This agent will be configured with `tools: []` in the `agents.yaml` file to ensure it is toolless. The final task of each crew will be assigned this agent and will have its `output_pydantic` field set in `tasks.yaml`.

---

### A. CompanyProfilerCrew

1.  **Define Reporter Agent (`agents.yaml`)**:
    ```yaml
    company_reporter:
      role: "Company Profile Report Writer"
      goal: "Compile all gathered intelligence into a comprehensive, well-structured company profile report."
      backstory: "An expert report writer specializing in synthesizing complex business intelligence into clear and concise reports."
      tools: [] # CRITICAL: This agent must be toolless
    ```

2.  **Update Final Task (`tasks.yaml`)**:
    ```yaml
    format_report_task:
      description: >
        Format the comprehensive company profile report for {company}.
        This task will take all the previously gathered information and format it into
        a single, comprehensive, and well-structured data object.
      expected_output: >
        A comprehensive data object containing all the information about {company}, conforming to the CompanyProfileReport Pydantic model.
      agent: company_reporter # Assign to the new toolless agent
      output_pydantic: CompanyProfileReport
    ```

---

### B. CrossReferenceReportCrew

1.  **Define Reporter Agent (`agents.yaml`)**:
    ```yaml
    osint_reporter:
      role: "Global Intelligence Report Integrator"
      goal: "Synthesize intelligence from multiple sources into a single, coherent, and comprehensive global report on {target}."
      backstory: "A master intelligence analyst skilled at seeing the big picture and integrating disparate pieces of information into a unified, actionable report."
      tools: [] # CRITICAL: Ensure this agent is toolless
    ```

2.  **Update Final Task (`tasks.yaml`)**:
    ```yaml
    global_reporting:
      description: >
        Create a comprehensive and extensive global intelligence report on {target} by
        aggregating all information from the context. This report must be extremely detailed and maintain the full depth of information.
      expected_output: >
        A comprehensive and extensive global intelligence report in a well-structured data format, conforming to the CrossReferenceReport Pydantic model.
      agent: osint_reporter # Assign to the toolless agent
      output_pydantic: CrossReferenceReport
      context: # Ensure it receives context from all previous tasks
        - intelligence_requirements_planning
        - intelligence_collection_coordination
        - intelligence_analysis_integration
        - intelligence_product_development
    ```

---

### C. GeospatialAnalysisCrew

1.  **Define Reporter Agent (`agents.yaml`)**:
    ```yaml
    geospatial_reporter:
      role: "Geospatial Intelligence Analyst"
      goal: "Analyze and report on the geospatial aspects of a company's operations, risks, and opportunities."
      backstory: "An expert in geographic information systems (GIS) and spatial analysis, capable of turning location data into strategic business insights."
      tools: [] # CRITICAL: Ensure this agent is toolless
    ```

2.  **Update Final Task (`tasks.yaml`)**:
    ```yaml
    geospatial_intelligence_for_mergers_acquisitions:
      description: >
        Provide geospatial intelligence for {company}'s mergers and acquisitions, and consolidate all findings into a final report.
      expected_output: >
        A comprehensive data object providing geospatial intelligence for {company}'s M&A activities and overall operations, conforming to the GeospatialAnalysisReport Pydantic model.
      agent: geospatial_reporter # Assign to the toolless agent
      output_pydantic: GeospatialAnalysisReport
      context:
        - physical_location_mapping
        - geospatial_risk_assessment
        - supply_chain_mapping
    ```

---

### D. HRIntelligenceCrew

1.  **Define Reporter Agent (`agents.yaml`)**:
    ```yaml
    hr_reporter:
      role: "HR Intelligence Report Specialist"
      goal: "Consolidate all HR intelligence findings about {company} into a comprehensive report."
      backstory: "A specialist in human capital analytics, skilled at interpreting HR data to provide strategic insights."
      tools: [] # CRITICAL: Ensure this agent is toolless
    ```

2.  **Update Final Task (`tasks.yaml`)**:
    ```yaml
    format_hr_intelligence_report:
      description: >
        Consolidate all HR intelligence findings about {company} into a comprehensive data object.
      expected_output: >
        A comprehensive data object consolidating all HR intelligence findings about {company}, conforming to the HRIntelligenceReport Pydantic model.
      agent: hr_reporter # Assign to the toolless agent
      output_pydantic: HRIntelligenceReport
      context:
        - leadership_team_assessment
        - employee_sentiment_analysis
        - organizational_culture_assessment
        - talent_acquisition_strategy
    ```

---

### E. LegalAnalysisCrew

1.  **Define Reporter Agent (`agents.yaml`)**:
    ```yaml
    legal_reporter:
      role: "Legal Analysis Report Coordinator"
      goal: "Synthesize all legal analysis into a final, comprehensive due diligence report for {company}."
      backstory: "A meticulous legal analyst with expertise in summarizing complex legal and regulatory information for executive review."
      tools: [] # CRITICAL: Ensure this agent is toolless
    ```

2.  **Update Final Task (`tasks.yaml`)**:
    ```yaml
    mergers_and_acquisitions_due_diligence:
      description: >
        Conduct legal due diligence for {company}'s mergers and acquisitions and consolidate all legal findings into a final report.
      expected_output: >
        A comprehensive data object analyzing {company}'s M&A due diligence and overall legal standing, conforming to the LegalAnalysisReport Pydantic model.
      agent: legal_reporter # Assign to the toolless agent
      output_pydantic: LegalAnalysisReport
      context:
        - legal_compliance_assessment
        - intellectual_property_analysis
        - regulatory_risk_assessment
        - litigation_history_analysis
    ```

## 5. Impact Analysis

- **Positive Impacts**:
    - **Reliability**: Outputs will be predictable and consistently structured, eliminating parsing errors downstream.
    - **Data Quality**: Pydantic models enforce data validation, improving the accuracy and completeness of reports.
    - **Maintainability**: Separating data structure (Pydantic) from logic (agents/tasks) makes the codebase easier to understand and modify.
    - **Developer Experience**: Clear data contracts between tasks simplify development and debugging.
    - **Clean Outputs**: The "Toolless Reporter" pattern guarantees that no extraneous agent thoughts or tool calls will contaminate the final output.

- **Potential Risks & Mitigation**:
    - **Initial Implementation Effort**: The initial setup requires creating a new file, modifying several YAML configurations, and updating Python crew definitions. **Mitigation**: This plan provides a clear, step-by-step guide to minimize effort and ensure consistency.
    - **Pydantic Model Rigidity**: If the LLM fails to generate output that perfectly matches the Pydantic schema, the task will fail. **Mitigation**: The prompts for the reporter agents must be very clear, instructing them to generate output that strictly adheres to the provided model. The `expected_output` in `tasks.yaml` should explicitly reference the Pydantic model.
    - **Increased Complexity**: Adding a new file and new classes introduces a small amount of complexity. **Mitigation**: This is a necessary trade-off for the significant gains in reliability and data quality. Centralizing models in `report_models.py` contains this complexity.

## 6. Implementation Checklist (To-Do)

-   [ ] **1. Create Pydantic Models File**:
    -   [ ] Create the new file: `src/epic_news/models/report_models.py`.
    -   [ ] Add all Pydantic class definitions as specified in section 3.

-   [ ] **2. Refactor `CompanyProfilerCrew`**:
    -   [ ] Modify `src/epic_news/crews/company_profiler/config/agents.yaml` to add the `company_reporter` agent with `tools: []`.
    -   [ ] Modify `src/epic_news/crews/company_profiler/config/tasks.yaml` to update the `format_report_task` as specified.
    -   [ ] Modify `src/epic_news/crews/company_profiler/company_profiler_crew.py` to import `CompanyProfileReport` and ensure the task loader correctly maps the string to the class.

-   [ ] **3. Refactor `CrossReferenceReportCrew`**:
    -   [ ] Modify `src/epic_news/crews/cross_reference_report_crew/config/agents.yaml` to ensure the `osint_reporter` has `tools: []`.
    -   [ ] Modify `src/epic_news/crews/cross_reference_report_crew/config/tasks.yaml` to update the `global_reporting` task.
    -   [ ] Modify `src/epic_news/crews/cross_reference_report_crew/cross_reference_report_crew.py` to import `CrossReferenceReport` and ensure the task loader correctly maps the string to the class.

-   [ ] **4. Refactor `GeospatialAnalysisCrew`**:
    -   [ ] Modify `src/epic_news/crews/geospatial_analysis/config/agents.yaml` to ensure the `geospatial_reporter` has `tools: []`.
    -   [ ] Modify `src/epic_news/crews/geospatial_analysis/config/tasks.yaml` to update the final task.
    -   [ ] Modify `src/epic_news/crews/geospatial_analysis/geospatial_analysis_crew.py` to import `GeospatialAnalysisReport` and ensure the task loader correctly maps the string to the class.

-   [ ] **5. Refactor `HRIntelligenceCrew`**:
    -   [ ] Modify `src/epic_news/crews/hr_intelligence/config/agents.yaml` to ensure the `hr_reporter` has `tools: []`.
    -   [ ] Modify `src/epic_news/crews/hr_intelligence/config/tasks.yaml` to update the `format_hr_intelligence_report` task.
    -   [ ] Modify `src/epic_news/crews/hr_intelligence/hr_intelligence_crew.py` to import `HRIntelligenceReport` and ensure the task loader correctly maps the string to the class.

-   [ ] **6. Refactor `LegalAnalysisCrew`**:
    -   [ ] Modify `src/epic_news/crews/legal_analysis/config/agents.yaml` to ensure the `legal_reporter` has `tools: []`.
    -   [ ] Modify `src/epic_news/crews/legal_analysis/config/tasks.yaml` to update the final task.
    -   [ ] Modify `src/epic_news/crews/legal_analysis/legal_analysis_crew.py` to import `LegalAnalysisReport` and ensure the task loader correctly maps the string to the class.

-   [ ] **7. Verification**:
    -   [ ] Run each of the five refactored crews with a sample input (e.g., a company name).
    -   [ ] Verify that the final output of each crew is a clean JSON object that validates against the corresponding Pydantic model.
    -   [ ] Confirm that no tool calls or agent thoughts are present in the final output files.
    -   [ ] Run the full test suite (`uv run pytest`) to ensure no regressions were introduced.