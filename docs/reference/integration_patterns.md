# CrewAI Integration Patterns & Technical Reference

## 📋 Overview

This document provides technical reference patterns and code examples derived from successful CrewAI integrations, particularly the menu designer workflow. These patterns serve as templates for future crew integrations and complex workflow implementations.

## 🔧 Data Structure Evolution Patterns

### Pattern: Backward Compatible Data Parsing

**Use Case:** When AI-generated data structures evolve, maintain compatibility with both old and new formats.

**Implementation:**

```python
def parse_flexible_menu_structure(self, menu_data: dict) -> List[Dict[str, str]]:
    """Parse menu structure supporting both old and new formats."""
    recipes = []
    
    for day, day_data in menu_data.items():
        if not isinstance(day_data, dict):
            continue
            
        for meal_name, meal_content in day_data.items():
            if not isinstance(meal_content, dict):
                continue
                
            # NEW FORMAT: dishes array
            if "dishes" in meal_content:
                dishes = meal_content.get("dishes", [])
                for dish_obj in dishes:
                    if isinstance(dish_obj, dict):
                        dish_name = dish_obj.get("name", "").strip()
                        dish_type = dish_obj.get("dish_type", "").strip()
                        if dish_name:
                            recipes.append({
                                "dish_name": dish_name,
                                "dish_type": dish_type,
                                "day": day,
                                "meal": meal_name
                            })
            
            # OLD FORMAT: direct dish keys (backward compatibility)
            else:
                legacy_keys = ["starter", "main_course", "dessert", "entrée", "plat_principal"]
                for key in legacy_keys:
                    if key in meal_content:
                        dish_name = meal_content[key]
                        if isinstance(dish_name, str) and dish_name.strip():
                            recipes.append({
                                "dish_name": dish_name.strip(),
                                "dish_type": key,
                                "day": day,
                                "meal": meal_name
                            })
    
    return recipes
```

**Key Benefits:**

- Handles data structure evolution gracefully
- Maintains backward compatibility
- Provides clear migration path
- Reduces integration breakage

## 🧠 Agent Memory Patterns

### Pattern: Persistent Memory with mem0

**Use Case:** Equip agents with long-term memory to enable personalized and context-aware interactions over multiple sessions.

**Implementation:**

To enable memory for a `crewAI` agent, simply set `memory=True` in the agent's configuration. This will allow the agent to leverage `mem0` to store and retrieve information.

```python
from crewai import Agent
from mem0 import MemoryClient

# Initialize the memory client
# Make sure to set the MEM0_API_KEY environment variable
client = MemoryClient()

# Create an agent with memory enabled
financial_analyst = Agent(
    role="Financial Analyst",
    goal="Provide insightful financial analysis",
    backstory="An expert financial analyst with a knack for spotting trends.",
    memory=True,
    verbose=True
)
```

**Key Benefits:**

- **Personalization:** Agents can remember user preferences, such as investment goals or dietary restrictions.
- **Context-Awareness:** Agents can maintain context across multiple conversations, leading to more natural and efficient interactions.
- **Improved Efficiency:** Agents can avoid asking for the same information repeatedly, saving time and reducing user frustration.

**Reference Implementation:**

- **`fin_daily` crew:** See `src/epic_news/crews/fin_daily/fin_daily.py` for an example of how to enable memory for agents in a crew.

## 🎯 CrewAI Template Variable Patterns

### Pattern: Complete Template Variable Provisioning

**Use Case:** Ensure all template variables referenced in CrewAI task configurations are provided.

**Implementation:**

```python
def generate_recipe_with_crew(self, recipe_spec: Dict[str, str]) -> Dict[str, Any]:
    """Generate recipe ensuring all template variables are provided."""
    
    # Prepare output file paths
    dish_slug = self._create_dish_slug(recipe_spec["dish_name"])
    json_file = self.output_dir / f"{dish_slug}.json"
    yaml_file = self.output_dir / f"{dish_slug}.yaml"
    
    # CRITICAL: Provide ALL template variables referenced in task configs
    recipe_inputs = {
        # Core recipe data
        "dish_name": recipe_spec["dish_name"],
        "dish_type": recipe_spec["dish_type"],
        "day": recipe_spec.get("day", ""),
        "meal": recipe_spec.get("meal", ""),
        
        # Template variables for file outputs (REQUIRED)
        "patrika_file": str(yaml_file),  # Referenced in task descriptions
        "output_file": str(json_file),   # Referenced in task descriptions
        
        # Additional context
        "cuisine_style": recipe_spec.get("cuisine_style", "French"),
        "dietary_restrictions": recipe_spec.get("dietary_restrictions", []),
    }
    
    try:
        # Execute crew with complete inputs
        result = self.cooking_crew.kickoff(inputs=recipe_inputs)
        return self._process_crew_result(result, json_file, yaml_file)
        
    except Exception as e:
        logger.error(f"Recipe generation failed for {recipe_spec['dish_name']}: {e}")
        return self._create_fallback_recipe(recipe_spec)
```

**Template Variable Audit Checklist:**

- [ ] Scan all task descriptions for `{variable}` patterns
- [ ] Verify all variables are provided in inputs dictionary
- [ ] Test with actual crew execution, not just validation
- [ ] Document required variables for future reference

## 🔄 Error Recovery Patterns

### Pattern: Layered Error Recovery

**Use Case:** Implement multiple fallback mechanisms for robust error handling.

**Implementation:**

```python
def robust_menu_processing(self, raw_menu_data: str) -> Dict[str, Any]:
    """Process menu data with layered error recovery."""
    
    # Layer 1: Direct processing (fastest path)
    try:
        menu_data = json.loads(raw_menu_data)
        validated_menu = self._validate_menu_structure(menu_data)
        return validated_menu
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed, attempting cleanup: {e}")
        
        # Layer 2: Data cleanup and retry
        try:
            cleaned_data = self._clean_json_string(raw_menu_data)
            menu_data = json.loads(cleaned_data)
            validated_menu = self._validate_menu_structure(menu_data)
            return validated_menu
            
        except Exception as e:
            logger.warning(f"Cleanup failed, using validator: {e}")
            
            # Layer 3: Validator-based recovery
            try:
                validator = MenuPlanValidator()
                validated_menu = validator.validate_and_fix(raw_menu_data)
                return validated_menu
                
            except Exception as e:
                logger.error(f"All recovery methods failed: {e}")
                
                # Layer 4: Minimal fallback
                return self._create_minimal_menu_fallback()

def _clean_json_string(self, raw_data: str) -> str:
    """Clean common JSON formatting issues."""
    # Remove markdown code blocks
    cleaned = re.sub(r'```json\s*|\s*```', '', raw_data)
    # Fix common quote issues
    cleaned = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', cleaned)
    # Remove trailing commas
    cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
    return cleaned.strip()
```

**Recovery Strategy Benefits:**

- Graceful degradation under failure conditions
- Multiple recovery paths increase success rate
- Detailed logging for debugging and monitoring
- Fallback options prevent complete workflow failure

## 🧪 Integration Testing Patterns

### Pattern: End-to-End Workflow Validation

**Use Case:** Verify complete workflows beyond unit testing.

**Implementation:**

```python
def test_complete_menu_to_recipe_workflow(self):
    """Test the complete menu designer to recipe generation workflow."""
    
    # Setup: Prepare test menu data
    test_menu = {
        "lundi": {
            "déjeuner": {
                "dishes": [
                    {"name": "Salade César", "dish_type": "entrée"},
                    {"name": "Saumon grillé", "dish_type": "plat principal"},
                    {"name": "Tarte aux pommes", "dish_type": "dessert"}
                ]
            }
        }
    }
    
    # Step 1: Menu validation
    validator = MenuPlanValidator()
    validated_menu = validator.validate(test_menu)
    assert validated_menu is not None
    assert "lundi" in validated_menu
    
    # Step 2: Recipe extraction
    generator = MenuGenerator()
    recipes = generator.parse_menu_structure(validated_menu)
    assert len(recipes) == 3
    assert all("dish_name" in recipe for recipe in recipes)
    
    # Step 3: Recipe generation
    recipe_outputs = []
    for recipe_spec in recipes:
        result = generator.generate_recipe(recipe_spec)
        recipe_outputs.append(result)
    
    # Step 4: File output verification
    expected_files = []
    for recipe in recipes:
        slug = generator._create_dish_slug(recipe["dish_name"])
        expected_files.extend([
            generator.output_dir / f"{slug}.json",
            generator.output_dir / f"{slug}.yaml"
        ])
    
    for file_path in expected_files:
        assert file_path.exists(), f"Expected output file not found: {file_path}"
        assert file_path.stat().st_size > 0, f"Output file is empty: {file_path}"
    
    # Step 5: report verification (assemble the DOCX and read it back)
    docx_path = assemble_menu_docx(validated_menu, inputs, "output/menu_designer/test.docx")
    report_text = extract_docx_text(docx_path)  # test helper

    # Verify actual dish names appear in the report (not placeholders)
    assert "Salade César" in report_text
    assert "Saumon grillé" in report_text
    assert "Tarte aux pommes" in report_text
    assert "Entrée du jour" not in report_text  # No placeholders
    
    # Step 6: Content quality verification
    for recipe_output in recipe_outputs:
        assert "ingredients" in recipe_output
        assert "instructions" in recipe_output
        assert len(recipe_output["ingredients"]) > 0
        assert len(recipe_output["instructions"]) > 0
```

**Integration Testing Benefits:**

- Catches issues that unit tests miss
- Verifies data flow through complete workflows
- Validates file outputs and their contents
- Ensures end-user experience quality

## 📊 Quality Assurance Patterns

### Pattern: Comprehensive Test Suite Management

**Use Case:** Maintain high-quality test suites with systematic approaches.

**Implementation:**

```python
# conftest.py - Shared test fixtures
@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test to prevent interference."""
    # Clear application caches
    if hasattr(cache_manager, 'clear'):
        cache_manager.clear()
    
    # Clear test-specific caches
    import functools
    functools.lru_cache.cache_clear = lambda: None
    
    yield
    
    # Cleanup after test
    if hasattr(cache_manager, 'clear'):
        cache_manager.clear()

@pytest.fixture
def mock_environment():
    """Provide consistent environment for tests."""
    with patch.dict(os.environ, {
        'ALPHA_VANTAGE_API_KEY': 'test_key',
        'OPENAI_API_KEY': 'test_openai_key',
        'LOG_LEVEL': 'DEBUG'
    }):
        yield

# Test implementation with realistic data
def test_menu_parsing_with_realistic_data(self, mock_environment):
    """Test menu parsing with realistic, dynamic data."""
    from faker import Faker
    fake = Faker('fr_FR')  # French locale for realistic dish names
    
    # Generate realistic test data
    realistic_menu = {
        fake.day_name().lower(): {
            "déjeuner": {
                "dishes": [
                    {
                        "name": f"{fake.word().title()} {fake.word()}",
                        "dish_type": "entrée"
                    },
                    {
                        "name": f"{fake.word().title()} aux {fake.word()}",
                        "dish_type": "plat principal"
                    }
                ]
            }
        }
    }
    
    # Test with realistic data
    generator = MenuGenerator()
    recipes = generator.parse_menu_structure(realistic_menu)
    
    # Verify parsing works with dynamic data
    assert len(recipes) == 2
    assert all(recipe["dish_name"] for recipe in recipes)
    assert all(recipe["dish_type"] in ["entrée", "plat principal"] for recipe in recipes)
```

**QA Pattern Benefits:**

- Prevents cache interference between tests
- Uses realistic data for better test coverage
- Provides consistent test environments
- Scales well with large test suites

## 🚀 Production Deployment Patterns

### Pattern: Production Readiness Validation

**Use Case:** Ensure systems are production-ready before deployment.

**Validation Checklist:**

```python
def validate_production_readiness(self) -> Dict[str, bool]:
    """Comprehensive production readiness validation."""
    
    checks = {}
    
    # 1. Integration completeness
    checks["end_to_end_workflow"] = self._test_complete_workflow()
    checks["error_recovery"] = self._test_error_scenarios()
    checks["data_format_compatibility"] = self._test_data_formats()
    
    # 2. Performance benchmarks
    checks["response_time"] = self._benchmark_response_times()
    checks["memory_usage"] = self._check_memory_consumption()
    checks["concurrent_processing"] = self._test_concurrency()
    
    # 3. Quality gates
    checks["test_coverage"] = self._verify_test_coverage()
    checks["code_quality"] = self._run_quality_checks()
    checks["documentation"] = self._verify_documentation()
    
    # 4. Operational readiness
    checks["logging_configuration"] = self._verify_logging()
    checks["monitoring_setup"] = self._verify_monitoring()
    checks["error_handling"] = self._verify_error_handling()
    
    return checks

def _test_complete_workflow(self) -> bool:
    """Test the complete workflow end-to-end."""
    try:
        # Run actual workflow with test data
        result = self.run_menu_designer_workflow(test_data=True)
        return (
            result["recipes_generated"] > 0 and
            result["docx_generated"] and
            result["files_created"] > 0
        )
    except Exception:
        return False
```

## 📚 Reference Implementation

### Complete Integration Example

For a complete reference implementation, see:

- **Menu Generator:** `src/epic_news/utils/menu_generator.py`
- **DOCX Assembler:** `src/epic_news/utils/docx_report/crews/menu.py`
- **Main Integration:** `src/epic_news/main.py` (lines 720-730)
- **Test Examples:** `tests/utils/test_menu_generator.py`

### Key Files Modified

- `MenuGenerator.parse_menu_structure(plan)` - walks the typed `WeeklyMenuPlan` (one recipe spec per dish)
- `main.py` - Template variable provisioning
- `assemble_menu_docx()` - handles both menu data formats

## 🎯 Success Metrics

**Integration Success Indicators:**

- ✅ Zero data loss during format transitions
- ✅ All template variables resolved successfully
- ✅ DOCX output shows actual data, not placeholders
- ✅ Complete workflow executes without errors
- ✅ All tests pass with realistic data
- ✅ Production deployment succeeds

---

*This reference guide provides proven patterns for successful CrewAI integrations. Use these patterns as templates for future development and adapt them to specific use cases.*
