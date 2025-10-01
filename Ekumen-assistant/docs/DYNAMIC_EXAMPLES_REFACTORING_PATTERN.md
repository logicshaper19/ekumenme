# Dynamic Examples Refactoring Pattern

## Overview

This document describes the **standard pattern** for refactoring inline few-shot examples from prompt files into the centralized `dynamic_examples.py` system.

## Why This Pattern?

The dynamic examples system provides:

1. **Centralized Management**: All examples in one place, easier to maintain and update
2. **Consistent Formatting**: Structured FewShotExample objects with metadata
3. **Flexible Selection**: Configure max examples, priority order, and filtering
4. **Reusability**: Same examples can be used across multiple prompts
5. **Metrics**: Track confidence, tags, and example types
6. **Easy Testing**: Examples can be tested independently

## The Refactoring Pattern

### Step 1: Extract Examples from Inline Prompts

**Before** (in `crop_health_prompts.py`):
```python
def get_crop_health_react_prompt(include_examples: bool = False):
    examples_section = ""
    if include_examples:
        examples_section = """
Exemple 1 - Diagnostic de maladie:
Question: J'observe des taches brunes sur les feuilles de mon blé
Thought: Je dois diagnostiquer la maladie...
Action: diagnose_disease
...
"""
```

### Step 2: Add Examples to `dynamic_examples.py`

Add to `_initialize_example_library()`:

```python
# ========================================
# 🌾 Crop Health ReAct Examples
# ========================================
self.examples["CROP_HEALTH_REACT_PROMPT"] = [
    FewShotExample(
        prompt_type="CROP_HEALTH_REACT_PROMPT",
        example_type=ExampleType.BASIC,
        user_query="J'observe des taches brunes sur les feuilles de mon blé",
        context="Blé tendre, stade montaison, région Centre",
        expected_response="""Question: J'observe des taches brunes sur les feuilles de mon blé
Thought: Je dois diagnostiquer la maladie en analysant les symptômes
Action: diagnose_disease
Action Input: {"crop": "blé", "symptoms": "taches brunes sur feuilles", "location": "feuilles"}
Observation: Septoriose du blé (Septoria tritici) - Maladie fongique, sévérité moyenne
Thought: J'ai identifié la maladie, je peux maintenant recommander un traitement
Final Answer: **Diagnostic: Septoriose du blé** (Septoria tritici)

**Symptômes:** Taches brunes sur feuilles - typique de cette maladie fongique

**Sévérité:** Moyenne - intervention recommandée

**Recommandations:**
- Traitement fongicide si >20% de surface foliaire atteinte
- Privilégier les triazoles ou strobilurines
- Intervenir avant montaison pour meilleure efficacité
- Surveiller l'évolution et conditions météo""",
        reasoning="Utilise diagnose_disease pour identifier la maladie, puis recommande traitement basé sur sévérité",
        confidence=0.94,
        tags=["diagnostic", "maladie", "tool_usage", "diagnose_disease", "septoriose"],
        created_at=datetime.now()
    ),
    # Add more examples...
]
```

### Step 3: Add Configuration

Add to `_initialize_configs()`:

```python
# Crop Health ReAct Config
self.configs["CROP_HEALTH_REACT_PROMPT"] = DynamicExampleConfig(
    prompt_type="CROP_HEALTH_REACT_PROMPT",
    max_examples=2,  # How many examples to inject
    example_types=[ExampleType.BASIC, ExampleType.COMPLEX],  # Which types to include
    priority_order=[ExampleType.BASIC, ExampleType.COMPLEX],  # Selection priority
    include_reasoning=True,  # Include reasoning field
    include_confidence=True  # Include confidence score
)
```

### Step 4: Update Prompt Function

**After** (in `crop_health_prompts.py`):

```python
from .dynamic_examples import get_dynamic_examples

def get_crop_health_react_prompt(include_examples: bool = True) -> ChatPromptTemplate:
    """
    Get ReAct-compatible ChatPromptTemplate for Crop Health Intelligence Agent.
    
    Args:
        include_examples: Whether to include few-shot examples from dynamic_examples.py (default True)
    """
    
    # Build examples section using dynamic examples system
    examples_section = ""
    if include_examples:
        dynamic_examples = get_dynamic_examples("CROP_HEALTH_REACT_PROMPT")
        if dynamic_examples:
            examples_section = f"""

EXEMPLES DE RAISONNEMENT RÉUSSI:

{dynamic_examples}"""
    
    # Rest of prompt construction...
    react_system_prompt = f"""{CROP_HEALTH_SYSTEM_PROMPT}
    
    ...
    {examples_section}
    
    IMPORTANT:
    - Suis EXACTEMENT le format ReAct ci-dessus"""
    
    return ChatPromptTemplate.from_messages([
        ("system", react_system_prompt),
        ("human", "{{context}}\n\nQuestion: {{input}}"),
        ("ai", "{agent_scratchpad}")
    ])
```

## Example Types

Use appropriate `ExampleType` for each example:

- `BASIC`: Simple, straightforward examples showing basic tool usage
- `COMPLEX`: Multi-step reasoning with multiple tool calls
- `EDGE_CASE`: Unusual scenarios, error conditions, alerts
- `ERROR_HANDLING`: How to handle missing data or errors
- `REGULATORY`: Compliance and safety-critical examples
- `SAFETY`: Safety-first examples with warnings

## Naming Conventions

### Prompt Type Keys

Use descriptive, uppercase keys with `_REACT_PROMPT` suffix for ReAct agents:

- `WEATHER_REACT_PROMPT`
- `CROP_HEALTH_REACT_PROMPT`
- `FARM_DATA_REACT_PROMPT`
- `REGULATORY_REACT_PROMPT`

### Tags

Use lowercase, descriptive tags:

- Tool usage: `"tool_usage"`, `"diagnose_disease"`, `"get_weather_data"`
- Domain: `"diagnostic"`, `"maladie"`, `"ravageur"`, `"irrigation"`
- Type: `"alerte"`, `"protection"`, `"traitement"`

## Configuration Guidelines

### max_examples

- **1 example**: Simple agents, token optimization
- **2 examples**: Standard (1 basic + 1 complex)
- **3+ examples**: Complex agents with many edge cases

### priority_order

Order examples by importance:

```python
# Safety-first
priority_order=[ExampleType.SAFETY, ExampleType.REGULATORY, ExampleType.BASIC]

# Learning-first
priority_order=[ExampleType.BASIC, ExampleType.COMPLEX, ExampleType.EDGE_CASE]
```

## Testing Your Refactoring

Create a test script:

```python
from app.prompts.dynamic_examples import get_dynamic_examples, get_example_stats
from app.prompts.your_prompts import get_your_react_prompt

# Test examples are available
examples = get_dynamic_examples("YOUR_REACT_PROMPT")
assert examples, "No examples found!"

# Test prompt integration
prompt_with = get_your_react_prompt(include_examples=True)
prompt_without = get_your_react_prompt(include_examples=False)

system_with = str(prompt_with.messages[0].prompt.template)
system_without = str(prompt_without.messages[0].prompt.template)

assert len(system_with) > len(system_without), "Examples not injected!"
assert "EXEMPLES" in system_with, "Examples section missing!"

# Test stats
stats = get_example_stats()
assert "YOUR_REACT_PROMPT" in stats, "Prompt type not in stats!"
```

## Completed Refactorings

✅ **Weather Agent** (`WEATHER_REACT_PROMPT`)
- 4 examples (basic, complex, edge_case)
- Tools: get_weather_data, identify_intervention_windows, analyze_weather_risks, calculate_evapotranspiration
- Avg confidence: 0.94

✅ **Crop Health Agent** (`CROP_HEALTH_REACT_PROMPT`)
- 2 examples (basic, complex)
- Tools: diagnose_disease, identify_pest
- Avg confidence: 0.93

## Next Agents to Refactor

Following the same pattern:

1. **Farm Data Agent** - Extract examples from farm_data_prompts.py
2. **Regulatory Agent** - Extract AMM lookup examples
3. **Planning Agent** - Extract task planning examples
4. **Sustainability Agent** - Extract carbon footprint examples

## Benefits Demonstrated

From test results:

- **Weather ReAct**: 3,651 characters of examples (4 examples)
- **Crop Health ReAct**: 2,405 characters of examples (2 examples)
- **Prompt size difference**: ~2,400 characters when examples included
- **Flexibility**: Can toggle examples on/off per request
- **Consistency**: All examples follow same ReAct format

## Token Optimization

Control token usage by:

1. **Toggle examples**: `include_examples=False` for simple queries
2. **Reduce max_examples**: Set to 1 for token-sensitive scenarios
3. **Filter by relevance**: Use context/user_query for smart selection (future enhancement)
4. **Measure impact**: Track token usage and response quality

## Maintenance

When updating examples:

1. Edit in `dynamic_examples.py` only (single source of truth)
2. Update confidence scores based on real performance
3. Add new tags as needed
4. Adjust priority_order based on user feedback
5. Run tests to verify changes

## Summary

This refactoring pattern provides:

- ✅ Centralized example management
- ✅ Consistent structure and metadata
- ✅ Flexible configuration per agent
- ✅ Easy testing and validation
- ✅ Token usage control
- ✅ Reusability across prompts

Follow this pattern for all future agent prompt refactorings.

