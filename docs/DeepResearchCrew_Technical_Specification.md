# DeepResearchCrew Integration - Technical Specification & Impact Analysis

## Executive Summary

This document outlines the technical specification and impact analysis for integrating DeepResearchCrew into the Epic News global flow. The integration will enable comprehensive internet research on user-provided topics, generating high-quality French language reports via HTML templating and email delivery.

## 1. Current State Analysis

### 1.1 Existing Implementation

- **Location**: `src/epic_news/crews/deep_research/deep_research.py`
- **Status**: Basic structure exists with 2 agents (researcher, reporting_analyst)
- **Current Limitations**:
  - No tools configured for agents
  - Generic agent configurations in `agents.yaml`
  - No Pydantic output model defined
  - Not integrated into main flow (`main.py`)
  - Missing from `ContentState` model
  - No HTML rendering capability

### 1.2 Available Tools for Research

Based on analysis of `src/epic_news/tools/`:

- **Web Search**: `SerperDevTool` (search & news modes)
- **Web Scraping**: `ScrapeNinjaTool`, `ScrapeWebsiteTool`
- **Wikipedia**: `WikipediaSearchTool`, `WikipediaArticleTool`
- **Specialized**: `YoutubeVideoSearchTool`, `WebsiteSearchTool`

## 2. Proposed Architecture

### 2.1 Agent Configuration

Following FinDailyCrew pattern:

- **Primary Researcher Agent**: Equipped with search and scraping tools
- **Wikipedia Specialist Agent**: Focused on Wikipedia research
- **Content Analyst Agent**: Synthesizes and analyzes gathered information
- **Report Generator Agent**: No tools, focuses on clean HTML report generation

### 2.2 Tool Selection Strategy

**Primary Tools** (based on docs/2_TOOLS_HANDBOOK.md):

- `SerperDevTool(n_results=25, search_type="search")` - General web search
- `SerperDevTool(n_results=15, search_type="news")` - Recent news
- `ScrapeNinjaTool()` - Primary web scraping
- `WikipediaSearchTool(limit=10)` - Wikipedia search
- `WikipediaArticleTool()` - Wikipedia content extraction

**Rationale**: Comprehensive coverage of web search, news, Wikipedia, and content extraction while maintaining tool efficiency.

### 2.3 Data Model Design

```python
class ResearchSource(BaseModel):
    """Individual research source information."""
    title: str = Field(..., description="Title of the source")
    url: Optional[str] = Field(None, description="URL of the source")
    source_type: str = Field(..., description="Type: web, wikipedia, news, etc.")
    summary: str = Field(..., description="Key information from this source")
    relevance_score: int = Field(..., description="Relevance score 1-10")

class ResearchSection(BaseModel):
    """Thematic section of research."""
    section_title: str = Field(..., description="Title of the research section")
    content: str = Field(..., description="Detailed content for this section")
    sources: List[ResearchSource] = Field(..., description="Sources supporting this section")

class DeepResearchReport(BaseModel):
    """Comprehensive research report model."""
    title: str = Field(..., description="Main title of the research report")
    topic: str = Field(..., description="Research topic")
    executive_summary: str = Field(..., description="High-level summary of findings")
    key_findings: List[str] = Field(..., description="List of key discoveries")
    research_sections: List[ResearchSection] = Field(..., description="Detailed research sections")
    methodology: str = Field(..., description="Research methodology used")
    sources_count: int = Field(..., description="Total number of sources consulted")
    report_date: Optional[str] = Field(None, description="Report generation date")
    confidence_level: str = Field(..., description="Overall confidence in findings")
```

## 3. Implementation Plan

### 3.1 Phase 1: Core Model & Configuration

1. **Create DeepResearchReport Model**
   - File: `src/epic_news/models/crews/deep_research_report.py`
   - Follow FinancialReport pattern with French language focus

2. **Update ContentState Model**
   - Add `deep_research_report: Optional[DeepResearchReport] = None`
   - Import new model in `content_state.py`

3. **Update Agent Configuration**
   - Enhance `agents.yaml` with specific roles and tools
   - Configure `async_execution: true` for research tasks
   - Add French language instructions

### 3.2 Phase 2: Crew Enhancement

1. **Update DeepResearchCrew Class**
   - Add tool configurations to agents
   - Configure 4 agents with specific responsibilities
   - Set up task dependencies and context flow
   - Configure final task with `output_pydantic=DeepResearchReport`

2. **Create Task Configuration**
   - Update `tasks.yaml` with comprehensive research tasks
   - Ensure French language output requirements
   - Set appropriate async execution flags

### 3.3 Phase 3: Main Flow Integration

1. **Update Classification Logic**
   - Add `DEEPRESEARCH` to `CrewCategories` class
   - Update classification prompts to recognize deep research requests

2. **Add Flow Handler Method**
   - Create `generate_deep_research()` method in `main.py`
   - Follow FinDailyCrew pattern for execution and state management
   - Integrate with existing error handling and logging

3. **HTML Rendering Integration**
   - Create HTML factory function for DeepResearchReport
   - Add template to existing templating system
   - Ensure French language rendering with emojis and professional styling

### 3.4 Phase 4: Email Integration

1. **PostCrew Integration**
   - Ensure DeepResearchReport is included in email generation
   - Test email delivery with HTML content
   - Validate French language email formatting

## 4. Technical Specifications

### 4.1 Configuration Files

**agents.yaml Structure**:

```yaml
primary_researcher:
  role: "Chercheur Principal en {topic}"
  goal: "Effectuer une recherche approfondie sur {topic} en utilisant diverses sources web"
  backstory: "Expert en recherche avec accès aux outils web les plus avancés"
  tools: ["SerperDevTool", "ScrapeNinjaTool"]
  async_execution: true

wikipedia_specialist:
  role: "Spécialiste Wikipedia en {topic}"
  goal: "Extraire des informations détaillées de Wikipedia sur {topic}"
  backstory: "Spécialiste de l'extraction d'informations encyclopédiques"
  tools: ["WikipediaSearchTool", "WikipediaArticleTool"]
  async_execution: true

content_analyst:
  role: "Analyste de Contenu {topic}"
  goal: "Analyser et synthétiser les informations collectées sur {topic}"
  backstory: "Expert en analyse de contenu et synthèse d'informations"
  tools: ["SerperDevTool"]
  async_execution: true

report_generator:
  role: "Générateur de Rapport {topic}"
  goal: "Créer un rapport HTML professionnel en français sur {topic}"
  backstory: "Spécialiste de la rédaction de rapports professionnels"
  async_execution: false
```

### 4.2 Integration Points

**main.py Changes**:

- Add `DEEPRESEARCH` case in classification logic
- Create `generate_deep_research()` method
- Update HTML rendering to include DeepResearchReport
- Ensure email integration includes new report type

**ContentState Updates**:

- Add import for DeepResearchReport
- Add field: `deep_research_report: Optional[DeepResearchReport] = None`

## 5. Impact Analysis

### 5.1 Positive Impacts

- **Enhanced Research Capabilities**: Comprehensive internet research on any topic
- **Professional Output**: High-quality French reports with proper HTML formatting
- **Scalable Architecture**: Follows established patterns for easy maintenance
- **Tool Efficiency**: Optimal selection of research tools for comprehensive coverage

### 5.2 System Integration Benefits

- **Consistent Flow**: Seamless integration with existing crew orchestration
- **State Management**: Proper integration with ContentState model
- **Email Delivery**: Automatic integration with PostCrew for report distribution
- **Error Handling**: Inherits robust error handling from main flow

### 5.3 Resource Considerations

- **API Usage**: Increased usage of SerperDev and other web tools
- **Processing Time**: Research tasks may take longer due to comprehensive nature
- **Storage**: Additional state storage for research reports

## 6. Risk Assessment & Mitigation

### 6.1 Technical Risks

**Risk**: Tool API rate limits or failures
**Mitigation**: Implement proper error handling and fallback mechanisms

**Risk**: Large research reports affecting performance
**Mitigation**: Implement content size limits and pagination if needed

**Risk**: French language quality in reports
**Mitigation**: Specific French language instructions in agent configurations

### 6.2 Integration Risks

**Risk**: Breaking existing crew functionality
**Mitigation**: Follow established patterns exactly, comprehensive testing

**Risk**: ContentState model conflicts
**Mitigation**: Use Optional fields and proper imports

## 7. Testing Strategy

### 7.1 Unit Testing

- Test DeepResearchReport model validation
- Test individual agent configurations
- Test tool integrations

### 7.2 Integration Testing

- Test full crew execution with sample topics
- Test main flow integration
- Test HTML rendering and email delivery
- Test French language output quality

### 7.3 Performance Testing

- Test with various topic complexities
- Monitor API usage and response times
- Validate memory usage with large reports

## 8. Success Criteria

1. **Functional Requirements**:
   - ✅ Crew executes successfully with DEEPRESEARCH action
   - ✅ Generates comprehensive French language reports
   - ✅ Integrates seamlessly with existing email flow
   - ✅ Follows all architectural patterns

2. **Quality Requirements**:
   - ✅ Professional HTML output with proper formatting
   - ✅ Comprehensive research using multiple sources
   - ✅ Proper error handling and logging
   - ✅ Maintains system performance standards

3. **Maintainability Requirements**:
   - ✅ Follows established code patterns
   - ✅ Proper documentation and comments
   - ✅ Configurable via YAML files
   - ✅ Testable and debuggable

## 9. Next Steps

1. **User Review & Approval**: Review this specification for completeness
2. **Implementation Phase 1**: Create models and basic configuration
3. **Implementation Phase 2**: Enhance crew with tools and tasks
4. **Implementation Phase 3**: Integrate with main flow
5. **Testing & Validation**: Comprehensive testing of all components
6. **Documentation Update**: Update TODO.md and other relevant docs

---

**Document Version**: 1.0  
**Date**: 2025-07-15  
**Author**: Cascade AI Assistant  
**Status**: Ready for Review
