# Environmental Regulations Tool - Comprehensive Improvement Plan

## Current Status: 7/10 → Target: 9.5/10

### ✅ Completed (Phase 1)
1. **Enhanced Pydantic Schemas**
   - `ProductEnvironmentalData` - Environmental fate and ecotoxicology
   - `CumulativeImpactAssessment` - Multi-application tracking
   - `GroundwaterRiskAssessment` - Vulnerability assessment
   - `WaterBodyClassification` - Water body type-specific rules
   - `EnvironmentalImpactData` - Enhanced with 20+ new fields
   - New enums: `WaterBodyType`, `EquipmentDriftClass`, `GroundwaterVulnerability`

2. **Schema Enhancements**
   - Water body type classification (drinking water, permanent stream, etc.)
   - Equipment drift class (1-star, 3-star, 5-star)
   - Weather data (humidity, rain forecast, temperature inversion)
   - Soil data (moisture, depth to groundwater)
   - Neighbor considerations (organic farms, beehives, habitations)
   - BBCH growth stage integration
   - Natura 2000 site code tracking

---

## 🚀 HIGH PRIORITY IMPLEMENTATIONS (Phase 2)

### 1. Product Environmental Fate Data from EPHY ⭐⭐⭐
**Status**: Schemas ready, implementation needed

**Implementation**:
```python
async def _get_product_environmental_data(
    self, db: AsyncSession, amm_code: str
) -> Optional[ProductEnvironmentalData]:
    """Get comprehensive environmental data from EPHY"""
    
    # Get product and substances
    product_query = select(Produit).where(Produit.numero_amm == amm_code)
    product = await db.execute(product_query)
    
    # Get active substances
    substances_query = select(SubstanceActive).join(
        ProduitSubstance
    ).where(ProduitSubstance.numero_amm == amm_code)
    substances = await db.execute(substances_query)
    
    # Get risk phrases for CMR/PBT classification
    risk_phrases_query = select(PhraseRisque).join(
        ProduitPhraseRisque
    ).where(ProduitPhraseRisque.numero_amm == amm_code)
    risk_phrases = await db.execute(risk_phrases_query)
    
    # Classify based on risk phrases
    is_cmr = any(p.code in ["H340", "H341", "H350", "H351", "H360", "H361"] 
                 for p in risk_phrases)
    
    # Determine aquatic toxicity from H-phrases
    aquatic_toxicity = "very_high" if any(p.code == "H400" for p in risk_phrases) else "moderate"
    
    # Determine bee toxicity from specific phrases
    bee_toxicity = "highly_toxic" if any(p.code in ["H410", "H411"] for p in risk_phrases) else "not_toxic"
    
    return ProductEnvironmentalData(
        amm_code=amm_code,
        product_name=product.nom_produit,
        active_substances=[s.nom_substance for s in substances],
        is_cmr=is_cmr,
        aquatic_toxicity_level=aquatic_toxicity,
        bee_toxicity=bee_toxicity
    )
```

**Files to modify**:
- `check_environmental_regulations_tool_enhanced.py` - Add method
- Call from `check_environmental_regulations()` when `amm_codes` provided

---

### 2. Enhanced ZNT Reduction Logic ⭐⭐⭐
**Status**: Schemas ready, implementation needed

**Implementation**:
```python
def _calculate_znt_reduction(
    self,
    base_znt_m: float,
    equipment_class: EquipmentDriftClass,
    has_vegetation_buffer: bool,
    water_body_type: WaterBodyType
) -> ZNTCompliance:
    """Calculate ZNT with proper reduction rules"""
    
    # Drinking water sources: NO reduction allowed
    if water_body_type == WaterBodyType.DRINKING_WATER_SOURCE:
        return ZNTCompliance(
            required_znt_m=max(base_znt_m, 200),
            reduction_possible=False,
            minimum_absolute_znt_m=200,
            water_body_type=water_body_type
        )
    
    # Equipment-based reduction
    reduction_rates = {
        EquipmentDriftClass.NO_EQUIPMENT: 0.0,
        EquipmentDriftClass.ONE_STAR: 0.25,
        EquipmentDriftClass.THREE_STAR: 0.33,
        EquipmentDriftClass.FIVE_STAR: 0.50
    }
    
    base_reduction = reduction_rates.get(equipment_class, 0.0)
    
    # Additional reduction with vegetation buffer
    if has_vegetation_buffer:
        base_reduction += 0.20
    
    # Cap total reduction at 66% (cannot reduce more than 2/3)
    total_reduction = min(base_reduction, 0.66)
    
    # Calculate reduced ZNT
    reduced_znt = base_znt_m * (1 - total_reduction)
    
    # Minimum absolute ZNT (cannot go below 5m for permanent streams)
    min_znt = 5.0 if water_body_type == WaterBodyType.PERMANENT_STREAM else 1.0
    final_znt = max(reduced_znt, min_znt)
    
    return ZNTCompliance(
        required_znt_m=base_znt_m,
        reduced_znt_m=final_znt,
        reduction_possible=True,
        equipment_class_required=EquipmentDriftClass.THREE_STAR,
        max_reduction_percent=total_reduction * 100,
        minimum_absolute_znt_m=min_znt,
        water_body_type=water_body_type
    )
```

**Files to modify**:
- `check_environmental_regulations_tool_enhanced.py` - Replace `_get_znt_compliance_from_db()`

---

### 3. Water Body Classification ⭐⭐⭐
**Status**: Schemas ready, implementation needed

**Implementation**:
```python
def _classify_water_body(
    self,
    water_proximity_m: Optional[float],
    water_body_type: WaterBodyType,
    water_body_width_m: Optional[float]
) -> Optional[WaterBodyClassification]:
    """Classify water body and determine protection requirements"""
    
    if not water_proximity_m:
        return None
    
    # Water body type-specific rules
    water_body_rules = {
        WaterBodyType.DRINKING_WATER_SOURCE: {
            "base_znt_m": 200.0,
            "reduction_allowed": False,
            "special_protections": [
                "Périmètre de protection rapprochée",
                "Interdiction totale de produits phytosanitaires",
                "Autorisation préfectorale requise"
            ],
            "is_drinking_water_source": True
        },
        WaterBodyType.PERMANENT_STREAM: {
            "base_znt_m": 5.0,
            "reduction_allowed": True,
            "special_protections": [
                "Protection contre le ruissellement",
                "Bande enherbée recommandée"
            ],
            "is_fish_bearing": True  # Assume yes for permanent streams
        },
        WaterBodyType.INTERMITTENT_STREAM: {
            "base_znt_m": 5.0,
            "reduction_allowed": True,
            "special_protections": [
                "Vérifier l'état (sec ou en eau)",
                "Protection renforcée en période d'écoulement"
            ]
        },
        WaterBodyType.DRAINAGE_DITCH: {
            "base_znt_m": 1.0,
            "reduction_allowed": False,
            "special_protections": [
                "Éviter le ruissellement direct",
                "Attention aux connexions avec cours d'eau"
            ]
        }
    }
    
    rules = water_body_rules.get(water_body_type, {
        "base_znt_m": 5.0,
        "reduction_allowed": True,
        "special_protections": []
    })
    
    return WaterBodyClassification(**rules, water_body_type=water_body_type)
```

**Files to modify**:
- `check_environmental_regulations_tool_enhanced.py` - Add method
- Call from `check_environmental_regulations()` when water proximity data available

---

### 4. Weather Integration ⭐⭐⭐
**Status**: Schemas ready, implementation needed

**Implementation**:
```python
def _assess_weather_restrictions(
    self,
    impact_data: EnvironmentalImpactData
) -> List[str]:
    """Assess weather-based restrictions"""
    restrictions = []
    
    # Wind speed (CRITICAL)
    if impact_data.wind_speed_kmh:
        if impact_data.wind_speed_kmh > 19:
            restrictions.append(
                "🚫 INTERDICTION: Vent > 19 km/h - Risque de dérive inacceptable"
            )
        elif impact_data.wind_speed_kmh > 15:
            restrictions.append(
                "⚠️ ATTENTION: Vent 15-19 km/h - Conditions limites, utiliser buses anti-dérive"
            )
    
    # Temperature
    if impact_data.temperature_c:
        if impact_data.temperature_c > 25:
            restrictions.append(
                "⚠️ ATTENTION: Température > 25°C - Risque d'évaporation accrue"
            )
        if impact_data.temperature_c < 5:
            restrictions.append(
                "⚠️ ATTENTION: Température < 5°C - Efficacité réduite, risque de gel"
            )
    
    # Humidity
    if impact_data.humidity_percent:
        if impact_data.humidity_percent < 30:
            restrictions.append(
                "⚠️ ATTENTION: Humidité < 30% - Risque d'évaporation et dérive accrus"
            )
    
    # Rain forecast
    if impact_data.rain_forecast_48h:
        restrictions.append(
            "⚠️ ATTENTION: Pluie prévue sous 48h - Risque de lessivage et ruissellement"
        )
    
    # Temperature inversion
    if impact_data.temperature_inversion:
        restrictions.append(
            "🚫 INTERDICTION: Inversion de température - Risque de dérive prolongée"
        )
    
    return restrictions
```

**Files to modify**:
- `check_environmental_regulations_tool_enhanced.py` - Add method
- Call from `check_environmental_regulations()` and add to output

---

### 5. Cumulative Impact Assessment ⭐⭐
**Status**: Schemas ready, implementation needed (requires application history)

**Implementation**:
```python
async def _assess_cumulative_impact(
    self,
    db: AsyncSession,
    amm_codes: List[str],
    field_size_ha: float,
    soil_type: Optional[str]
) -> Optional[CumulativeImpactAssessment]:
    """Assess cumulative environmental impact"""
    
    # NOTE: Requires application history from database
    # For now, provide basic assessment based on product properties
    
    total_active_substance = 0.0
    high_persistence_products = []
    
    for amm_code in amm_codes:
        # Get product environmental data
        env_data = await self._get_product_environmental_data(db, amm_code)
        
        if env_data:
            # Check for persistent substances
            if env_data.soil_half_life_days and env_data.soil_half_life_days > 60:
                high_persistence_products.append(env_data.product_name)
    
    # Assess soil residue risk
    soil_residue_risk = RiskLevel.HIGH if high_persistence_products else RiskLevel.LOW
    
    # Assess water contamination risk
    water_risk = RiskLevel.MODERATE  # Default
    
    warnings = []
    if high_persistence_products:
        warnings.append(
            f"⚠️ Produits persistants détectés: {', '.join(high_persistence_products)}"
        )
        warnings.append(
            "Recommandation: Attendre au moins 90 jours avant nouvelle application"
        )
    
    return CumulativeImpactAssessment(
        total_applications_30days=0,  # Would need history
        total_active_substance_kg=total_active_substance,
        soil_residue_risk=soil_residue_risk,
        water_contamination_risk=water_risk,
        cumulative_warnings=warnings,
        recommended_waiting_period_days=90 if high_persistence_products else None
    )
```

**Files to modify**:
- `check_environmental_regulations_tool_enhanced.py` - Add method
- Call from `check_environmental_regulations()` when `amm_codes` provided

---

## 📊 MEDIUM PRIORITY (Phase 3)

### 6. Groundwater Vulnerability Assessment ⭐⭐
**Implementation**: Calculate GUS index, assess recharge zones

### 7. Natura 2000 Specific Checks ⭐⭐
**Implementation**: Site-specific management plans, protected species

### 8. Neighbor Considerations ⭐
**Implementation**: Organic farm buffers, beehive distances

### 9. Seasonal Phenology Integration ⭐
**Implementation**: BBCH-based flowering detection

---

## 📝 IMPLEMENTATION SEQUENCE

**Week 1**: High Priority Items 1-3
- Product environmental data
- Enhanced ZNT reduction
- Water body classification

**Week 2**: High Priority Items 4-5
- Weather integration
- Cumulative impact (basic)

**Week 3**: Medium Priority Items
- Groundwater assessment
- Neighbor considerations

**Week 4**: Testing & Refinement
- Comprehensive test suite
- Real-world validation
- Performance optimization

---

## 🎯 SUCCESS METRICS

- **Score**: 7/10 → 9.5/10
- **Database Integration**: 30% → 80%
- **Environmental Science Accuracy**: 60% → 95%
- **Actionable Recommendations**: 70% → 95%
- **Test Coverage**: 6 tests → 15+ tests

---

## 📚 NEXT STEPS

1. Implement high-priority items 1-3 (this session if time permits)
2. Create comprehensive test suite with real EPHY data
3. Validate with agricultural compliance experts
4. Document all environmental science assumptions
5. Add integration with weather services (future)

