# Intervention Validation & Confirmation System

## Overview

The Intervention Validation & Confirmation System provides comprehensive validation of agricultural interventions against regulatory guidelines, best practices, and compliance requirements. It ensures data quality and regulatory compliance while providing interactive confirmation to farmers.

## 🎯 Key Features

### **Comprehensive Validation**
- **Regulatory Compliance**: Validates against EPHY database, AMM codes, and French agricultural regulations
- **Best Practices**: Checks weather conditions, timing, and application rates
- **Data Quality**: Ensures all required fields are present and valid
- **Real-time Validation**: Immediate feedback during voice recording

### **Interactive Confirmation**
- **Voice Playback**: Reads back extracted data for farmer confirmation
- **Visual Validation**: Shows validation results with color-coded severity levels
- **Interactive Questions**: Asks for clarification on missing or invalid data
- **Smart Suggestions**: Provides recommendations for corrections

### **Compliance Integration**
- **EPHY Database**: Validates phytosanitary products against official database
- **Weather Integration**: Checks weather conditions for treatment timing
- **Crop-specific Rules**: Applies validation rules based on crop type
- **Regulatory Limits**: Enforces dose limits and application windows

## 🏗️ Architecture

```
Voice Input → Data Extraction → Validation → Confirmation → Save/Reject
     ↓              ↓              ↓            ↓           ↓
  Whisper      AI Parser    Guidelines    Interactive   Database
  Transcription  (GPT-4)     Checker       Modal        Storage
```

## 📋 Validation Rules by Intervention Type

### **Traitement Phytosanitaire (Phytosanitary Treatment)**

#### **Required Fields**
- ✅ Parcelle (Field)
- ✅ Date d'intervention
- ✅ Surface travaillée
- ✅ Produit phytosanitaire avec code AMM
- ✅ Cible du traitement
- ✅ Conditions météo

#### **Validation Rules**
```python
# Wind speed validation
if wind_speed > 19:  # km/h
    validation_error("Traitement interdit par vent fort")

# Temperature validation  
if temperature < 5:  # °C
    validation_warning("Traitement déconseillé par température basse")

# AMM code validation
if not amm_code_valid:
    validation_error("Code AMM invalide ou inactif")

# Dose validation
if dose > max_authorized_dose:
    validation_critical("Dose dépasse les limites autorisées")
```

#### **Compliance Checks**
- **Code AMM**: Must be valid and active in EPHY database
- **Dose Limits**: Must not exceed authorized maximum dose
- **Target Validation**: Treatment target must be authorized for the product
- **Weather Conditions**: Wind < 19 km/h, no rain, temperature > 5°C
- **Pre-harvest Intervals**: Must respect minimum days before harvest

### **Fertilisation (Fertilization)**

#### **Required Fields**
- ✅ Parcelle
- ✅ Date d'intervention
- ✅ Surface travaillée
- ✅ Type et quantité de fertilisant
- ✅ Teneur en azote

#### **Validation Rules**
```python
# Nitrogen limits by crop
nitrogen_limits = {
    "blé": 200,      # kg N/ha/year
    "maïs": 250,
    "colza": 180
}

# Spreading periods
allowed_periods = {
    "autumn": "09-01 to 11-30",
    "spring": "02-01 to 07-31"
}
```

#### **Compliance Checks**
- **Nitrogen Limits**: Must not exceed crop-specific annual limits
- **Spreading Periods**: Must respect authorized spreading windows
- **Buffer Zones**: Must maintain distance from water courses
- **Soil Conditions**: Must check soil moisture and temperature

### **Semis (Planting)**

#### **Required Fields**
- ✅ Parcelle
- ✅ Date de semis
- ✅ Surface
- ✅ Culture
- ✅ Variété de semences

#### **Validation Rules**
```python
# Planting date validation
if planting_date < recommended_start or planting_date > recommended_end:
    validation_warning("Date de semis en dehors de la période recommandée")

# Seed variety validation
if variety not in authorized_varieties:
    validation_warning("Variété non recommandée pour cette région")
```

### **Récolte (Harvest)**

#### **Required Fields**
- ✅ Parcelle
- ✅ Date de récolte
- ✅ Surface récoltée
- ✅ Rendement
- ✅ Qualité (humidité, impuretés)

#### **Validation Rules**
```python
# Moisture content validation
if moisture > 25:  # %
    validation_warning("Humidité trop élevée pour stockage")

# Yield validation
if yield < expected_minimum:
    validation_info("Rendement inférieur aux attentes")
```

## 🔧 Implementation Details

### **Backend Services**

#### **InterventionGuidelines** (`/app/services/validation/intervention_guidelines.py`)
```python
class InterventionGuidelines:
    def validate_intervention(self, intervention_data: Dict[str, Any]) -> List[ValidationResult]
    def generate_confirmation_summary(self, data: Dict, results: List[ValidationResult]) -> Dict
    def get_intervention_guidelines(self, intervention_type: str) -> Dict[str, Any]
```

#### **InterventionChecker** (`/app/services/validation/intervention_checker.py`)
```python
class InterventionChecker:
    async def validate_and_confirm_intervention(self, data: Dict, context: Dict) -> Dict
    async def _enhanced_validation(self, data: Dict, context: Dict) -> List[ValidationResult]
    async def _validate_phytosanitary_products(self, data: Dict) -> List[ValidationResult]
    async def _validate_weather_conditions(self, data: Dict, context: Dict) -> List[ValidationResult]
```

### **Frontend Components**

#### **InterventionConfirmationModal** (`/src/components/InterventionConfirmationModal.tsx`)
- **Visual Validation Display**: Shows validation results with icons and colors
- **Interactive Questions**: Handles confirmation, clarification, and acknowledgment
- **Voice Playback**: Integrates with TTS for audio confirmation
- **Progressive Confirmation**: Guides farmer through validation issues

#### **StreamingVoiceAssistant** (Enhanced)
- **Real-time Validation**: Shows validation results during voice input
- **Confirmation Integration**: Opens modal when validation issues are found
- **Voice Feedback**: Plays back extracted data for confirmation

## 📊 Validation Result Types

### **Validation Levels**
```typescript
enum ValidationLevel {
  INFO = "info",           // Informational message
  WARNING = "warning",     // Non-blocking issue
  ERROR = "error",         // Blocking issue, requires correction
  CRITICAL = "critical"    // Regulatory violation, requires explicit confirmation
}
```

### **Validation Result Structure**
```typescript
interface ValidationResult {
  is_valid: boolean
  level: ValidationLevel
  message: string
  field: string
  suggested_value?: any
  compliance_issues?: string[]
}
```

## 🎤 Voice Confirmation Flow

### **1. Data Extraction**
```
Farmer: "J'ai appliqué du fongicide sur la parcelle Nord ce matin"
↓
AI: Extracts structured data
↓
{
  "parcelle": "Parcelle Nord",
  "type_intervention": "traitement_phytosanitaire",
  "date_intervention": "2025-01-15",
  "intrants": [...]
}
```

### **2. Validation**
```
Validation Engine: Checks against guidelines
↓
Results: [
  { level: "error", message: "Code AMM requis", field: "intrants" },
  { level: "warning", message: "Conditions météo non spécifiées", field: "conditions_meteo" }
]
```

### **3. Voice Confirmation**
```
AI Voice: "J'ai enregistré votre traitement phytosanitaire sur la parcelle Nord 
le 15 janvier. Attention: code AMM requis pour les produits phytosanitaires. 
Confirmez-vous ces informations?"
```

### **4. Interactive Confirmation**
```
Modal: Shows validation results and asks:
- "Pouvez-vous préciser le code AMM du produit utilisé?"
- "Quelles étaient les conditions météo?"
- "Confirmez-vous malgré les avertissements?"
```

## 🔄 Confirmation Question Types

### **1. Confirmation Questions**
```typescript
{
  type: "confirmation",
  question: "Confirmez-vous cette intervention malgré: [issue]?",
  requires_explicit_confirmation: true
}
```

### **2. Clarification Questions**
```typescript
{
  type: "clarification", 
  question: "Pouvez-vous préciser: [missing_field]?",
  suggested_prompt: "Quel est le code AMM du produit?"
}
```

### **3. Acknowledgment Questions**
```typescript
{
  type: "acknowledgment",
  question: "Attention: 2 avertissement(s) détecté(s). Voulez-vous continuer?",
  details: [{ field: "conditions_meteo", message: "Conditions non spécifiées" }]
}
```

## 🚨 Compliance Integration

### **EPHY Database Integration**
```python
async def _validate_phytosanitary_products(self, intervention_data):
    for intrant in intervention_data.get("intrants", []):
        if intrant.get("type_intrant") == "Phytosanitaire":
            amm_code = intrant.get("code_amm")
            product_info = await self.ephy_service.get_product_by_amm(amm_code)
            
            # Validate AMM code
            if not product_info:
                return ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Code AMM {amm_code} non trouvé"
                )
            
            # Check if still authorized
            if not product_info.get("is_active"):
                return ValidationResult(
                    level=ValidationLevel.ERROR,
                    message="Produit n'est plus autorisé"
                )
```

### **Weather Service Integration**
```python
async def _validate_weather_conditions(self, intervention_data, user_context):
    weather_data = await self.weather_service.get_weather_for_date(
        date=intervention_data.get("date_intervention"),
        location=user_context.get("location")
    )
    
    # Check wind speed for phytosanitary treatments
    if intervention_data.get("type_intervention") == "traitement_phytosanitaire":
        wind_speed = weather_data.get("wind_speed_kmh", 0)
        if wind_speed > 19:
            return ValidationResult(
                level=ValidationLevel.CRITICAL,
                message=f"Traitement interdit: vent trop fort ({wind_speed} km/h)"
            )
```

## 📱 User Experience Flow

### **1. Voice Recording**
- Farmer records intervention description
- Real-time transcription with visual feedback
- Audio level visualization

### **2. Data Extraction**
- AI extracts structured data from transcript
- Shows extracted information in real-time
- Highlights any missing required fields

### **3. Validation & Confirmation**
- Validation results displayed with color coding
- Voice confirmation plays back extracted data
- Interactive modal opens if issues found

### **4. Resolution**
- Farmer answers clarification questions
- System re-validates with updated data
- Final confirmation before saving

### **5. Save or Reject**
- Intervention saved if all validations pass
- Rejected if critical issues remain unresolved
- Audit trail maintained for compliance

## 🛡️ Security & Compliance

### **Data Validation**
- All inputs validated against type and range constraints
- SQL injection prevention through parameterized queries
- XSS protection in frontend components

### **Audit Trail**
- All validation results logged with timestamps
- User confirmations recorded for compliance
- Change history maintained for regulatory audits

### **Privacy Protection**
- Voice data not stored permanently
- Personal information encrypted in transit
- GDPR compliance for EU users

## 🚀 Future Enhancements

### **Planned Features**
1. **Machine Learning Validation**: Learn from farmer corrections to improve validation rules
2. **Predictive Compliance**: Warn about potential future compliance issues
3. **Multi-language Support**: Support for multiple languages and regional regulations
4. **Integration APIs**: Connect with farm management systems and weather services
5. **Mobile App**: Native mobile app for field recording

### **Advanced Validation**
1. **Satellite Integration**: Use satellite data for crop stage validation
2. **IoT Integration**: Connect with soil sensors and weather stations
3. **Blockchain Records**: Immutable intervention records for premium markets
4. **AI Recommendations**: Suggest optimal intervention timing and products

## 📚 Usage Examples

### **Example 1: Valid Phytosanitary Treatment**
```json
{
  "parcelle": "Parcelle Nord",
  "type_intervention": "traitement_phytosanitaire",
  "date_intervention": "2025-01-15",
  "surface_travaillee_ha": 12.5,
  "culture": "blé",
  "intrants": [
    {
      "libelle": "Saracen Delta",
      "code_amm": "2190312",
      "quantite_totale": 1.25,
      "unite_intrant_intervention": "L",
      "cible": "mauvaises herbes"
    }
  ],
  "conditions_meteo": "Ensoleillé, 18°C, vent faible"
}
```

**Validation Result**: ✅ Valid - All requirements met

### **Example 2: Missing AMM Code**
```json
{
  "parcelle": "Parcelle Sud",
  "type_intervention": "traitement_phytosanitaire",
  "intrants": [
    {
      "libelle": "Produit fongicide",
      "quantite_totale": 2.0,
      "unite_intrant_intervention": "L"
      // Missing code_amm
    }
  ]
}
```

**Validation Result**: ❌ Error - "Code AMM requis pour les produits phytosanitaires"

**Confirmation Question**: "Pouvez-vous préciser le code AMM du produit fongicide utilisé?"

### **Example 3: Weather Warning**
```json
{
  "type_intervention": "traitement_phytosanitaire",
  "conditions_meteo": "Vent fort, 25 km/h"
}
```

**Validation Result**: ⚠️ Critical - "Traitement interdit par vent fort (>19 km/h)"

**Confirmation Question**: "Confirmez-vous cette intervention malgré le vent fort? (Réglementairement interdit)"

## 🔧 Configuration

### **Environment Variables**
```bash
# EPHY Database
EPHY_API_URL=https://ephy.anses.fr/api
EPHY_API_KEY=your_api_key

# Weather Service
WEATHER_API_KEY=your_weather_api_key
WEATHER_SERVICE_URL=https://api.weather.com

# Validation Settings
MAX_WIND_SPEED_KMH=19
MIN_TEMPERATURE_C=5
MAX_TEMPERATURE_C=30
```

### **Validation Rules Configuration**
```python
# Custom validation rules can be added in intervention_guidelines.py
CUSTOM_RULES = {
    "fertilization": {
        "nitrogen_limits": {
            "custom_crop": 150  # kg N/ha/year
        }
    }
}
```

This comprehensive validation and confirmation system ensures that all agricultural interventions are properly validated against regulatory requirements while providing an intuitive, voice-driven interface for farmers to confirm and correct their data.
