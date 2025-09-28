# Agricultural Chatbot Prompts - Comprehensive Documentation

## 📋 **Overview**

This document provides comprehensive documentation for all prompts in the agricultural chatbot system. Each prompt is designed for specific agricultural scenarios with clear purposes, inputs, outputs, and usage guidelines.

## 🏗️ **Architecture**

### **Prompt Categories**
1. **Base Prompts** - Shared templates and context
2. **Agent-Specific Prompts** - Specialized prompts for each agent
3. **Semantic Routing Prompts** - Intent classification and routing
4. **Dynamic Examples** - Few-shot examples for enhanced precision

### **Prompt Structure**
Each prompt follows a consistent structure:
- **System Prompt**: Core behavior and responsibilities
- **Context Templates**: Structured input formatting
- **Response Format**: Expected output structure
- **Safety Guidelines**: Compliance and safety reminders
- **Few-Shot Examples**: Dynamic examples for precision

---

## 📚 **Base Prompts**

### **BASE_AGRICULTURAL_SYSTEM_PROMPT**
**Purpose**: Core system prompt for all agricultural agents
**Usage**: Base template for all specialized prompts
**Key Features**:
- French agricultural context
- Regulatory compliance (AMM, ZNT)
- Metric units (hectares, kg/ha, °C)
- Safety-first approach
- Expert knowledge base

**Template Variables**:
- `{siret}` - Farm identification
- `{region_code}` - Geographic region
- `{total_area_ha}` - Total farm area
- `{primary_crops}` - Main crops grown

### **FARM_CONTEXT_TEMPLATE**
**Purpose**: Standardized farm information injection
**Usage**: Provides consistent farm context across all prompts
**Variables**:
- `{siret}` - Farm SIRET number
- `{farm_name}` - Farm name
- `{region_code}` - Regional code
- `{total_area_ha}` - Total area in hectares
- `{primary_crops}` - Primary crops
- `{organic_certified}` - Organic certification status
- `{coordinates}` - GPS coordinates

### **WEATHER_CONTEXT_TEMPLATE**
**Purpose**: Current weather conditions injection
**Usage**: Provides real-time weather context
**Variables**:
- `{temperature}` - Current temperature (°C)
- `{humidity}` - Humidity percentage
- `{wind_speed}` - Wind speed (km/h)
- `{precipitation}` - Precipitation (mm)
- `{soil_moisture}` - Soil moisture percentage
- `{soil_temperature}` - Soil temperature (°C)

---

## 🚜 **Farm Data Agent Prompts**

### **FARM_DATA_CHAT_PROMPT**
**Purpose**: General farm data analysis and consultation
**Input**: Farm context, recent interventions, performance data
**Output**: Comprehensive farm analysis with recommendations
**Use Cases**:
- Overall farm performance analysis
- Data interpretation and insights
- General farm management advice

**Example Usage**:
```python
prompt = FARM_DATA_CHAT_PROMPT.format_messages(
    farm_context=farm_info,
    recent_interventions=interventions,
    performance_data=metrics,
    input=user_query
)
```

### **PARCEL_ANALYSIS_PROMPT**
**Purpose**: Detailed analysis of specific parcels
**Input**: Parcel ID, current crop, growth stage
**Output**: Parcel-specific analysis and recommendations
**Use Cases**:
- Individual parcel performance
- Crop-specific analysis
- Parcel optimization

### **PERFORMANCE_METRICS_PROMPT**
**Purpose**: Calculation and analysis of performance metrics
**Input**: Period, crops, specific metrics
**Output**: Calculated metrics with comparisons
**Use Cases**:
- Yield analysis
- Cost calculations
- Performance benchmarking

### **INTERVENTION_TRACKING_PROMPT**
**Purpose**: Tracking and analysis of farm interventions
**Input**: Intervention type, period, parcels
**Output**: Intervention history and effectiveness
**Use Cases**:
- Treatment tracking
- Compliance monitoring
- Intervention optimization

### **COST_ANALYSIS_PROMPT**
**Purpose**: Detailed cost analysis and optimization
**Input**: Period, crops, cost types
**Output**: Cost breakdown and optimization recommendations
**Use Cases**:
- Cost management
- Budget planning
- Cost optimization

### **TREND_ANALYSIS_PROMPT**
**Purpose**: Analysis of trends and patterns over time
**Input**: Analysis period, variables, granularity
**Output**: Trend analysis with projections
**Use Cases**:
- Historical analysis
- Trend identification
- Future projections

---

## ⚖️ **Regulatory Agent Prompts**

### **REGULATORY_CHAT_PROMPT**
**Purpose**: General regulatory consultation and compliance
**Input**: Regulatory context, farm context
**Output**: Regulatory guidance and compliance advice
**Use Cases**:
- General regulatory questions
- Compliance guidance
- Regulatory updates

### **AMM_LOOKUP_PROMPT**
**Purpose**: Verification of product authorizations (AMM)
**Input**: Product name, AMM number, crop, usage
**Output**: Authorization status and conditions
**Use Cases**:
- Product authorization verification
- AMM status checking
- Usage validation

**Example Usage**:
```python
prompt = AMM_LOOKUP_PROMPT.format_messages(
    product_name="Roundup",
    amm_number="2000233",
    crop="blé",
    usage="désherbage",
    regulatory_context=context
)
```

### **USAGE_CONDITIONS_PROMPT**
**Purpose**: Detailed usage conditions for products
**Input**: Product name, crop, target pest/disease
**Output**: Complete usage conditions and restrictions
**Use Cases**:
- Usage condition verification
- Application guidelines
- Restriction checking

### **SAFETY_CLASSIFICATIONS_PROMPT**
**Purpose**: Safety classifications and hazard information
**Input**: Product name, active substance
**Output**: Safety classifications and precautions
**Use Cases**:
- Safety information
- Hazard assessment
- Precaution guidelines

### **PRODUCT_SUBSTITUTION_PROMPT**
**Purpose**: Finding alternatives and substitutions
**Input**: Current product, crop, target, reason
**Output**: Alternative products and recommendations
**Use Cases**:
- Product alternatives
- Substitution options
- Biocontrol recommendations

### **COMPLIANCE_CHECK_PROMPT**
**Purpose**: Compliance verification and checking
**Input**: Intervention details, product, date, parcel
**Output**: Compliance status and recommendations
**Use Cases**:
- Compliance verification
- Audit preparation
- Regulatory checking

### **ENVIRONMENTAL_REGULATIONS_PROMPT**
**Purpose**: Environmental regulation compliance
**Input**: Environmental context, zone, season
**Output**: Environmental compliance guidance
**Use Cases**:
- Environmental compliance
- ZNT verification
- Environmental protection

---

## 🌤️ **Weather Agent Prompts**

### **WEATHER_CHAT_PROMPT**
**Purpose**: General weather consultation and advice
**Input**: Weather data, farm context, planned intervention
**Output**: Weather-based recommendations
**Use Cases**:
- General weather advice
- Weather consultation
- Weather-based planning

### **WEATHER_FORECAST_PROMPT**
**Purpose**: Detailed weather forecasts and planning
**Input**: Forecast period, location, intervention type
**Output**: Detailed forecasts with recommendations
**Use Cases**:
- Weather forecasting
- Forecast interpretation
- Weather-based planning

### **INTERVENTION_WINDOW_PROMPT**
**Purpose**: Optimal intervention window identification
**Input**: Intervention type, crop, growth stage, urgency
**Output**: Optimal timing recommendations
**Use Cases**:
- Treatment timing
- Intervention windows
- Optimal conditions

### **WEATHER_RISK_ANALYSIS_PROMPT**
**Purpose**: Weather risk assessment and mitigation
**Input**: Risk type, period, crops
**Output**: Risk analysis and mitigation strategies
**Use Cases**:
- Risk assessment
- Weather hazards
- Mitigation planning

### **IRRIGATION_PLANNING_PROMPT**
**Purpose**: Irrigation planning and optimization
**Input**: Crops, irrigation system, water resources
**Output**: Irrigation schedule and recommendations
**Use Cases**:
- Irrigation planning
- Water management
- Irrigation optimization

### **EVAPOTRANSPIRATION_PROMPT**
**Purpose**: Evapotranspiration calculations
**Input**: Crops, growth stages, period
**Output**: ETR calculations and water needs
**Use Cases**:
- ETR calculations
- Water needs assessment
- Irrigation planning

### **CLIMATE_ADAPTATION_PROMPT**
**Purpose**: Climate change adaptation strategies
**Input**: Climate context, crops, objectives
**Output**: Adaptation strategies and recommendations
**Use Cases**:
- Climate adaptation
- Resilience planning
- Climate change response

---

## 🌱 **Crop Health Agent Prompts**

### **CROP_HEALTH_CHAT_PROMPT**
**Purpose**: General crop health consultation
**Input**: Diagnostic context, farm context
**Output**: Crop health advice and recommendations
**Use Cases**:
- General crop health
- Health consultation
- Preventive advice

### **DISEASE_DIAGNOSIS_PROMPT**
**Purpose**: Disease identification and diagnosis
**Input**: Crop, growth stage, symptoms, location
**Output**: Disease diagnosis and treatment
**Use Cases**:
- Disease identification
- Symptom analysis
- Treatment recommendations

### **PEST_IDENTIFICATION_PROMPT**
**Purpose**: Pest identification and management
**Input**: Crop, growth stage, damage, insect presence
**Output**: Pest identification and control
**Use Cases**:
- Pest identification
- Damage assessment
- Control strategies

### **NUTRIENT_DEFICIENCY_PROMPT**
**Purpose**: Nutrient deficiency analysis
**Input**: Crop, growth stage, symptoms, soil analysis
**Output**: Deficiency diagnosis and correction
**Use Cases**:
- Deficiency diagnosis
- Nutrient analysis
- Fertilization recommendations

### **TREATMENT_PLAN_PROMPT**
**Purpose**: Comprehensive treatment planning
**Input**: Identified problem, crop, growth stage, infestation level
**Output**: Treatment plan and recommendations
**Use Cases**:
- Treatment planning
- Strategy development
- Implementation guidance

### **RESISTANCE_MANAGEMENT_PROMPT**
**Purpose**: Resistance management strategies
**Input**: Problem, products used, efficacy
**Output**: Resistance management plan
**Use Cases**:
- Resistance prevention
- Management strategies
- Product rotation

### **BIOLOGICAL_CONTROL_PROMPT**
**Purpose**: Biological control recommendations
**Input**: Pest/disease, crop, context
**Output**: Biological control strategies
**Use Cases**:
- Biocontrol options
- Natural enemies
- Biological products

### **THRESHOLD_MANAGEMENT_PROMPT**
**Purpose**: Intervention threshold management
**Input**: Pest, crop, growth stage, observations
**Output**: Threshold analysis and recommendations
**Use Cases**:
- Threshold monitoring
- Intervention decisions
- Monitoring strategies

---

## 📅 **Planning Agent Prompts**

### **PLANNING_CHAT_PROMPT**
**Purpose**: General planning consultation
**Input**: Planning context, farm context
**Output**: Planning advice and recommendations
**Use Cases**:
- General planning
- Planning consultation
- Strategy development

### **TASK_PLANNING_PROMPT**
**Purpose**: Detailed task planning and scheduling
**Input**: Period, interventions, resources, constraints
**Output**: Detailed task schedule
**Use Cases**:
- Task scheduling
- Work planning
- Resource allocation

### **RESOURCE_OPTIMIZATION_PROMPT**
**Purpose**: Resource optimization and allocation
**Input**: Available resources, interventions, objectives
**Output**: Optimized resource allocation
**Use Cases**:
- Resource optimization
- Efficiency improvement
- Cost reduction

### **SEASONAL_PLANNING_PROMPT**
**Purpose**: Seasonal planning and management
**Input**: Season, crops, objectives
**Output**: Seasonal plan and recommendations
**Use Cases**:
- Seasonal planning
- Annual planning
- Seasonal management

### **WEATHER_DEPENDENT_PLANNING_PROMPT**
**Purpose**: Weather-dependent planning
**Input**: Weather forecast, interventions, constraints
**Output**: Weather-adapted plan
**Use Cases**:
- Weather adaptation
- Flexible planning
- Contingency planning

### **COST_OPTIMIZATION_PROMPT**
**Purpose**: Cost optimization and management
**Input**: Budget, interventions, constraints
**Output**: Cost-optimized plan
**Use Cases**:
- Cost optimization
- Budget management
- Cost reduction

### **EMERGENCY_PLANNING_PROMPT**
**Purpose**: Emergency planning and response
**Input**: Emergency situation, urgency, resources
**Output**: Emergency response plan
**Use Cases**:
- Emergency response
- Crisis management
- Rapid reorganization

### **WORKFLOW_OPTIMIZATION_PROMPT**
**Purpose**: Workflow optimization and improvement
**Input**: Processes, objectives, constraints
**Output**: Optimized workflow
**Use Cases**:
- Process improvement
- Workflow optimization
- Efficiency enhancement

---

## 🌍 **Sustainability Agent Prompts**

### **SUSTAINABILITY_CHAT_PROMPT**
**Purpose**: General sustainability consultation
**Input**: Sustainability context, farm context
**Output**: Sustainability advice and recommendations
**Use Cases**:
- General sustainability
- Environmental advice
- Sustainability planning

### **CARBON_FOOTPRINT_PROMPT**
**Purpose**: Carbon footprint calculation and analysis
**Input**: Period, crops, carbon data
**Output**: Carbon footprint analysis
**Use Cases**:
- Carbon calculation
- Emission analysis
- Carbon reduction

### **BIODIVERSITY_ASSESSMENT_PROMPT**
**Purpose**: Biodiversity assessment and improvement
**Input**: Biodiversity context, practices, objectives
**Output**: Biodiversity assessment and recommendations
**Use Cases**:
- Biodiversity evaluation
- Habitat assessment
- Biodiversity improvement

### **SOIL_HEALTH_PROMPT**
**Purpose**: Soil health analysis and improvement
**Input**: Soil analysis, practices, issues
**Output**: Soil health assessment and recommendations
**Use Cases**:
- Soil health evaluation
- Soil improvement
- Soil management

### **WATER_MANAGEMENT_PROMPT**
**Purpose**: Water management and conservation
**Input**: Water resources, irrigation systems, constraints
**Output**: Water management recommendations
**Use Cases**:
- Water conservation
- Irrigation optimization
- Water management

### **ENERGY_EFFICIENCY_PROMPT**
**Purpose**: Energy efficiency and optimization
**Input**: Current consumption, equipment, objectives
**Output**: Energy efficiency recommendations
**Use Cases**:
- Energy optimization
- Efficiency improvement
- Renewable energy

### **CERTIFICATION_SUPPORT_PROMPT**
**Purpose**: Certification support and preparation
**Input**: Certification type, current level, objectives
**Output**: Certification support and recommendations
**Use Cases**:
- Certification preparation
- Compliance support
- Certification maintenance

### **CIRCULAR_ECONOMY_PROMPT**
**Purpose**: Circular economy implementation
**Input**: Current waste, resources, objectives
**Output**: Circular economy recommendations
**Use Cases**:
- Waste reduction
- Resource optimization
- Circular practices

### **CLIMATE_ADAPTATION_PROMPT**
**Purpose**: Climate adaptation strategies
**Input**: Observed changes, risks, objectives
**Output**: Climate adaptation recommendations
**Use Cases**:
- Climate adaptation
- Resilience building
- Climate response

---

## 🎯 **Semantic Routing Prompts**

### **SEMANTIC_ORCHESTRATOR_SYSTEM_PROMPT**
**Purpose**: Master orchestrator with semantic routing capabilities
**Input**: User query, farm context, weather context
**Output**: Agent selection and coordination
**Use Cases**:
- Multi-agent coordination
- Semantic routing
- Response synthesis

### **SEMANTIC_INTENT_CLASSIFICATION_PROMPT**
**Purpose**: Intent classification and prompt selection
**Input**: User query, context, chat history
**Output**: Intent classification and prompt selection
**Use Cases**:
- Intent understanding
- Prompt routing
- Classification

### **SEMANTIC_AGENT_SELECTION_PROMPT**
**Purpose**: Intelligent agent selection
**Input**: Query, intent, context, complexity
**Output**: Agent selection and reasoning
**Use Cases**:
- Agent routing
- Selection optimization
- Multi-agent coordination

### **SEMANTIC_RESPONSE_SYNTHESIS_PROMPT**
**Purpose**: Response synthesis and coordination
**Input**: Original intent, agent responses, context
**Output**: Synthesized response
**Use Cases**:
- Response coordination
- Synthesis
- Coherence

### **SEMANTIC_CONFLICT_RESOLUTION_PROMPT**
**Purpose**: Conflict resolution and decision making
**Input**: Conflict, context, sources, user intent
**Output**: Resolved conflict and reasoning
**Use Cases**:
- Conflict resolution
- Decision making
- Consensus building

### **SEMANTIC_QUALITY_ASSURANCE_PROMPT**
**Purpose**: Quality assurance and validation
**Input**: Response, original intent, context, criteria
**Output**: Quality validation and recommendations
**Use Cases**:
- Quality control
- Validation
- Assurance

### **SEMANTIC_PERFORMANCE_MONITORING_PROMPT**
**Purpose**: Performance monitoring and optimization
**Input**: Period, metrics, objectives, intent types
**Output**: Performance analysis and recommendations
**Use Cases**:
- Performance monitoring
- Optimization
- Analytics

---

## 🔄 **Dynamic Examples System**

### **Dynamic Few-Shot Examples**
**Purpose**: Provide relevant examples for each prompt type
**Features**:
- **Dynamic Selection**: Examples selected based on context
- **Multiple Types**: Basic, complex, edge cases, error handling
- **Priority Ordering**: Examples ordered by relevance
- **Confidence Scoring**: Each example has confidence metrics

### **Example Types**
1. **BASIC**: Standard use cases
2. **COMPLEX**: Advanced scenarios
3. **EDGE_CASE**: Unusual situations
4. **ERROR_HANDLING**: Error scenarios
5. **REGULATORY**: Compliance examples
6. **SAFETY**: Safety-critical examples

### **Usage**
```python
# Get prompt with dynamic examples
prompt_with_examples = get_prompt_with_examples(
    prompt_type="AMM_LOOKUP_PROMPT",
    query="Vérifier l'autorisation AMM du Roundup",
    context="Produit phytosanitaire"
)

# Add new example
add_dynamic_example(
    prompt_type="AMM_LOOKUP_PROMPT",
    example_type="REGULATORY",
    user_query="Est-ce que le glyphosate est autorisé?",
    context="Vérification réglementaire",
    expected_response="...",
    reasoning="Vérification complète AMM",
    confidence=0.95,
    tags=["amm", "autorisation"]
)
```

---

## 📊 **Usage Guidelines**

### **Prompt Selection**
1. **Identify Intent**: Use semantic routing to identify user intent
2. **Select Prompt**: Choose appropriate specialized prompt
3. **Inject Context**: Add relevant context and examples
4. **Execute**: Run prompt with LLM
5. **Validate**: Ensure response quality and compliance

### **Context Injection**
- Always provide relevant farm context
- Include current weather conditions when applicable
- Add regulatory context for compliance prompts
- Include diagnostic context for health prompts

### **Response Validation**
- Check regulatory compliance
- Verify safety guidelines
- Ensure technical accuracy
- Validate response format

### **Performance Monitoring**
- Track prompt performance
- Monitor user satisfaction
- Analyze confidence scores
- Optimize based on metrics

---

## 🧪 **Testing Guidelines**

### **Unit Testing**
Each prompt should have unit tests covering:
- **Input Validation**: Test with various input formats
- **Output Format**: Verify response structure
- **Edge Cases**: Test unusual scenarios
- **Error Handling**: Test error conditions
- **Compliance**: Verify regulatory compliance

### **Integration Testing**
- **End-to-End**: Test complete workflows
- **Multi-Agent**: Test agent coordination
- **Semantic Routing**: Test intent classification
- **Dynamic Examples**: Test example injection

### **Performance Testing**
- **Response Time**: Measure prompt execution time
- **Accuracy**: Test response accuracy
- **Consistency**: Test response consistency
- **Scalability**: Test under load

---

## 🔧 **Maintenance**

### **Regular Updates**
- **Regulatory Changes**: Update compliance prompts
- **New Examples**: Add new few-shot examples
- **Performance Optimization**: Improve based on metrics
- **User Feedback**: Incorporate user feedback

### **Version Control**
- **Prompt Versions**: Track prompt changes
- **A/B Testing**: Test prompt improvements
- **Rollback**: Ability to rollback changes
- **Documentation**: Keep documentation updated

### **Monitoring**
- **Performance Metrics**: Track key metrics
- **Error Rates**: Monitor error rates
- **User Satisfaction**: Track user feedback
- **Compliance**: Monitor regulatory compliance

---

## 📈 **Best Practices**

### **Prompt Design**
1. **Clear Purpose**: Each prompt has a clear, specific purpose
2. **Structured Input**: Use consistent input formats
3. **Structured Output**: Define clear output formats
4. **Safety First**: Always include safety guidelines
5. **Context Aware**: Include relevant context

### **Example Management**
1. **Relevant Examples**: Use contextually relevant examples
2. **Quality Examples**: Ensure high-quality examples
3. **Diverse Examples**: Include various scenarios
4. **Regular Updates**: Keep examples current
5. **Performance Tracking**: Monitor example effectiveness

### **Semantic Routing**
1. **Intent Clarity**: Clear intent classification
2. **Fallback Options**: Multiple routing methods
3. **Confidence Scoring**: Include confidence metrics
4. **Performance Monitoring**: Track routing accuracy
5. **Continuous Improvement**: Regular optimization

---

## 🚀 **Future Enhancements**

### **Planned Features**
- **Multi-Language Support**: Support for multiple languages
- **Advanced Analytics**: Enhanced performance analytics
- **Machine Learning**: ML-based prompt optimization
- **Real-Time Updates**: Dynamic prompt updates
- **User Personalization**: Personalized prompts

### **Integration Opportunities**
- **External APIs**: Integration with external services
- **IoT Data**: Integration with IoT sensors
- **Weather Services**: Real-time weather integration
- **Regulatory Databases**: Live regulatory data
- **Market Data**: Market price integration

---

This documentation provides a comprehensive guide to all prompts in the agricultural chatbot system. Each prompt is designed for specific use cases with clear inputs, outputs, and guidelines for optimal usage.
