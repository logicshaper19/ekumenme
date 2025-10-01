# Routing Problem Analysis

## 🔴 **PROBLEM IDENTIFIED**

**User Query**: "Quelle est la météo à Dourdan ?"  
**Expected Response**: Simple weather forecast (3-5 sentences)  
**Actual Response**: Complex 6-section agricultural guide (2540 characters)

---

## 🔍 **Root Cause Analysis**

### **Problem 1: BASE_AGRICULTURAL_SYSTEM_PROMPT is TOO PRESCRIPTIVE**

**Location**: `app/prompts/base_prompts.py` (lines 12-65)

**Issue**: The base prompt **MANDATES** a 6-section structure for **ALL** responses:

```python
STRUCTURE DE RÉPONSE OBLIGATOIRE:
1. **Reconnaissance de la demande**
2. **La réalité technique**
3. **Solutions concrètes**
4. **Attentes réalistes**
5. **Alternatives viables**
6. **Encouragement personnalisé**
```

**Impact**: Even simple weather queries get this full treatment because:
- The synthesis node uses `BASE_AGRICULTURAL_SYSTEM_PROMPT` (line 464)
- The prompt says "OBLIGATOIRE" (mandatory)
- The LLM follows instructions literally

---

### **Problem 2: Synthesis Prompt Reinforces Complex Structure**

**Location**: `app/services/langgraph_workflow_service.py` (lines 463-526)

**Issue**: The synthesis prompt **explicitly templates** the 6-section structure:

```python
synthesis_prompt = f"""{BASE_AGRICULTURAL_SYSTEM_PROMPT}

INSTRUCTIONS DE RÉPONSE STRUCTURÉE:

Génère une réponse en suivant EXACTEMENT cette structure markdown:

## 🌱 [Titre engageant qui reconnaît la demande]
### ❄️ La Réalité Climatique
### 🏠 Solutions Concrètes
### ⏱️ Attentes Réalistes
### 🌳 Alternatives Viables pour {location}
### 💪 Mon Conseil
```

**Impact**: The LLM has no choice but to generate all 6 sections, even for "What's the weather?"

---

### **Problem 3: No Query Complexity Detection**

**Location**: Routing logic doesn't differentiate between:
- **Simple queries**: "Quelle est la météo ?" → Should be 3-5 sentences
- **Complex queries**: "Je veux planter du café" → Needs full 6-section analysis

**Current Behavior**:
- Semantic routing correctly identifies "weather" query ✅
- But synthesis node applies same template to ALL queries ❌

---

## 📊 **Query Classification**

### **Simple Queries** (Should be SHORT)
- "Quelle est la météo à Dourdan ?"
- "Quel temps fait-il ?"
- "Va-t-il pleuvoir demain ?"
- "Quelle est la température ?"

**Expected Response**: 3-5 sentences with:
- Current conditions
- 3-7 day forecast
- Key agricultural impacts (frost warning, rain alert)

---

### **Complex Queries** (Need FULL structure)
- "Je veux planter du café à Dourdan"
- "Comment cultiver des tomates en Normandie ?"
- "Quelle culture choisir pour mon exploitation ?"

**Expected Response**: Full 6-section guide with:
- Feasibility analysis
- Step-by-step instructions
- Alternatives
- Realistic expectations

---

## 🔧 **Solution Options**

### **Option 1: Query Complexity Detection** (RECOMMENDED)

Add complexity scoring to routing:

```python
def _classify_query_complexity(query: str) -> str:
    """Classify query as simple, medium, or complex"""
    
    # Simple queries (informational)
    simple_patterns = [
        r"quelle.*météo",
        r"quel.*temps",
        r"va.*pleuvoir",
        r"température",
        r"prévision"
    ]
    
    # Complex queries (planning/advice)
    complex_patterns = [
        r"(planter|cultiver|culture)",
        r"comment.*faire",
        r"recommand.*",
        r"conseil.*",
        r"choisir.*culture"
    ]
    
    if any(re.search(p, query.lower()) for p in simple_patterns):
        return "simple"
    elif any(re.search(p, query.lower()) for p in complex_patterns):
        return "complex"
    else:
        return "medium"
```

Then use different prompts:

```python
if complexity == "simple":
    # Use SHORT_RESPONSE_PROMPT (3-5 sentences)
elif complexity == "complex":
    # Use FULL_STRUCTURE_PROMPT (6 sections)
else:
    # Use MEDIUM_RESPONSE_PROMPT (3-4 sections)
```

---

### **Option 2: Conditional Synthesis Prompt**

Modify synthesis node to check query type:

```python
async def _synthesis_node(self, state):
    query_lower = state["query"].lower()
    
    # Detect simple weather query
    if any(word in query_lower for word in ["météo", "temps", "prévision"]) and \
       not any(word in query_lower for word in ["planter", "cultiver", "culture"]):
        # Use simple weather response template
        synthesis_prompt = SIMPLE_WEATHER_PROMPT
    else:
        # Use full agricultural guide template
        synthesis_prompt = FULL_AGRICULTURAL_PROMPT
```

---

### **Option 3: Separate Response Templates**

Create specialized prompts:

**File**: `app/prompts/response_templates.py`

```python
SIMPLE_WEATHER_RESPONSE = """
Réponds de manière concise (3-5 phrases) avec:

1. Conditions actuelles (température, conditions)
2. Prévisions 3-7 jours (min/max, précipitations)
3. Impact agricole principal (gel, pluie, vent fort)

Format:
🌤️ **Météo à {location}**
[Conditions actuelles]
[Prévisions courtes]
[⚠️ Alerte si nécessaire]
"""

FULL_AGRICULTURAL_GUIDE = """
[Current 6-section structure]
"""
```

---

## 🎯 **Recommended Implementation**

### **Step 1: Add Query Complexity Classifier**

**File**: `app/services/query_classifier.py` (NEW)

```python
class QueryComplexityClassifier:
    """Classify query complexity for appropriate response length"""
    
    SIMPLE_PATTERNS = {
        "weather_info": [r"quelle.*météo", r"quel.*temps", r"prévision"],
        "temperature": [r"température", r"combien.*degré"],
        "precipitation": [r"va.*pleuvoir", r"pluie"],
        "general_info": [r"c'est quoi", r"qu'est-ce que"]
    }
    
    COMPLEX_PATTERNS = {
        "cultivation": [r"planter", r"cultiver", r"culture de"],
        "planning": [r"comment.*faire", r"étapes", r"planifier"],
        "advice": [r"recommand", r"conseil", r"suggère"],
        "comparison": [r"choisir", r"meilleur", r"comparer"]
    }
    
    def classify(self, query: str) -> Dict[str, Any]:
        """Returns: {complexity: 'simple'|'medium'|'complex', confidence: float}"""
        # Implementation...
```

---

### **Step 2: Modify Synthesis Node**

**File**: `app/services/langgraph_workflow_service.py`

```python
async def _synthesis_node(self, state):
    # Classify query complexity
    from app.services.query_classifier import QueryComplexityClassifier
    classifier = QueryComplexityClassifier()
    complexity = classifier.classify(state["query"])
    
    if complexity["complexity"] == "simple":
        # Use concise response template
        synthesis_prompt = self._create_simple_response_prompt(state)
    else:
        # Use full 6-section structure
        synthesis_prompt = self._create_full_response_prompt(state)
    
    # Generate response...
```

---

### **Step 3: Create Simple Response Template**

```python
def _create_simple_response_prompt(self, state):
    """Create prompt for simple informational queries"""
    
    weather_summary = self._format_weather_data(state.get("weather_data"))
    location = self._extract_location_from_query(state["query"])
    
    return f"""Tu es un conseiller agricole. Réponds de manière CONCISE (3-5 phrases maximum).

QUESTION: {state["query"]}

DONNÉES MÉTÉO:
{weather_summary}

INSTRUCTIONS:
- Réponds directement à la question posée
- Utilise les données météo réelles
- Format: 3-5 phrases maximum
- Inclus un emoji pertinent
- Mentionne l'impact agricole principal si pertinent

EXEMPLE DE RÉPONSE:
🌤️ **Météo à {location}**
Actuellement 16°C avec ciel nuageux. Les prévisions pour les 7 prochains jours montrent des températures entre 11°C et 20°C, avec du soleil prévu pour les prochains jours. ⚠️ Attention aux températures fraîches le matin (11-12°C) qui peuvent affecter les cultures sensibles au froid.
"""
```

---

## 📈 **Expected Improvements**

### **Before** (Current)
```
Query: "Quelle est la météo à Dourdan ?"
Response: 2540 characters, 6 sections, full agricultural guide
Time: ~5 seconds
User Experience: ❌ Overwhelming, too much info
```

### **After** (With Fix)
```
Query: "Quelle est la météo à Dourdan ?"
Response: ~300 characters, 3-5 sentences, direct answer
Time: ~2 seconds
User Experience: ✅ Clear, concise, helpful
```

---

## 🧪 **Test Cases**

### **Simple Queries** (Should be SHORT)
1. "Quelle est la météo à Dourdan ?"
2. "Quel temps fait-il à Paris ?"
3. "Va-t-il pleuvoir demain ?"
4. "Quelle est la température actuelle ?"

**Expected**: 3-5 sentences, weather data only

---

### **Complex Queries** (Should be FULL)
1. "Je veux planter du café à Dourdan"
2. "Comment cultiver des tomates en Normandie ?"
3. "Quelle culture choisir pour mon exploitation ?"
4. "Recommandations pour améliorer mon rendement"

**Expected**: Full 6-section guide with analysis

---

## 🎯 **Priority**

**HIGH** - This affects user experience significantly

**Impact**:
- Simple queries get overwhelming responses
- Users may abandon the system
- Response time is unnecessarily long
- LLM costs are higher than needed

**Effort**: Medium (2-3 hours)
- Create query classifier
- Add conditional logic to synthesis
- Create simple response template
- Test with various queries

---

## 📝 **Summary**

**Root Cause**: `BASE_AGRICULTURAL_SYSTEM_PROMPT` mandates 6-section structure for ALL queries

**Solution**: Add query complexity detection and use appropriate response templates

**Files to Modify**:
1. `app/services/query_classifier.py` (NEW)
2. `app/services/langgraph_workflow_service.py` (modify synthesis node)
3. `app/prompts/response_templates.py` (NEW - simple templates)

**Expected Result**: Simple queries get concise answers, complex queries get full guides

---

**Status**: 🔴 **NEEDS FIX**  
**Priority**: **HIGH**  
**Estimated Effort**: 2-3 hours

