"""
Enhanced Check Environmental Regulations Tool - DATABASE INTEGRATED

Provides comprehensive environmental compliance checking for agricultural practices
with REAL DATABASE INTEGRATION from EPHY (ZNT requirements, environmental restrictions).

Features:
- Pydantic schemas for type safety
- Redis + memory caching (2h TTL)
- EPHY database integration for ZNT requirements
- Water protection regulations
- Biodiversity protection (Natura 2000, pollinators)
- Air quality regulations
- Nitrate directive compliance
- Seasonal restrictions
- Legal references
- Structured error handling
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import ValidationError
from langchain.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.cache import redis_cache
from app.core.database import AsyncSessionLocal
from app.services.configuration_service import ConfigurationService
from app.services.unified_regulatory_service import UnifiedRegulatoryService
from app.models.ephy import Produit, UsageProduit, SubstanceActive, ProduitSubstance, PhraseRisque, ProduitPhraseRisque
from app.tools.schemas.environmental_schemas import (
    EnvironmentalRegulationsInput,
    EnvironmentalRegulationsOutput,
    EnvironmentalRegulation,
    EnvironmentalRisk,
    ZNTCompliance,
    EnvironmentalImpactData,
    EnvironmentalImpactLevel,
    ComplianceStatus,
    RiskLevel,
    RegulationType,
    PracticeType,
    ProductEnvironmentalData,
    WaterBodyClassification,
    WaterBodyType,
    EquipmentDriftClass
)

logger = logging.getLogger(__name__)


class EnhancedEnvironmentalRegulationsService:
    """Service for checking environmental regulations with DATABASE INTEGRATION"""
    
    def __init__(self):
        self.config_service = ConfigurationService()
        self.regulatory_service = UnifiedRegulatoryService()
    
    @redis_cache(ttl=7200, model_class=EnvironmentalRegulationsOutput, category="regulatory")
    async def check_environmental_regulations(
        self,
        practice_type: str,
        location: Optional[str] = None,
        environmental_impact: Optional[Dict[str, Any]] = None,
        amm_codes: Optional[List[str]] = None,
        crop_eppo_code: Optional[str] = None,
        field_size_ha: Optional[float] = None,
        application_date: Optional[date] = None
    ) -> EnvironmentalRegulationsOutput:
        """
        Check environmental regulations with database integration.
        
        Args:
            practice_type: Type of agricultural practice
            location: Location (department, region)
            environmental_impact: Environmental impact assessment data
            amm_codes: AMM codes of products to check
            crop_eppo_code: EPPO code of the crop
            field_size_ha: Field size in hectares
            application_date: Planned application date
            
        Returns:
            EnvironmentalRegulationsOutput with comprehensive environmental compliance
        """
        try:
            # Parse environmental impact data
            impact_data = None
            if environmental_impact:
                impact_data = EnvironmentalImpactData(**environmental_impact)
            
            # Validate input
            input_data = EnvironmentalRegulationsInput(
                practice_type=practice_type,
                location=location,
                environmental_impact=impact_data,
                amm_codes=amm_codes,
                crop_eppo_code=crop_eppo_code,
                field_size_ha=field_size_ha,
                application_date=application_date
            )
            
            # Get configuration-based regulations
            config_regulations = self._get_config_regulations(
                input_data.practice_type,
                impact_data
            )
            
            # Get database-based ZNT compliance and product environmental data
            znt_compliance = None
            database_regulations = []
            product_environmental_data = None
            water_body_classification = None

            if amm_codes:
                async with AsyncSessionLocal() as db:
                    # Get ZNT compliance with enhanced reduction logic
                    znt_compliance = await self._get_znt_compliance_from_db(
                        db, amm_codes, impact_data
                    )

                    if znt_compliance:
                        # Create regulation from ZNT data
                        znt_regulation = self._create_znt_regulation(znt_compliance)
                        database_regulations.append(znt_regulation)

                    # Get product environmental data (HIGH PRIORITY #1)
                    product_environmental_data = await self._get_product_environmental_data(
                        db, amm_codes
                    )

            # Classify water body (HIGH PRIORITY #3)
            if impact_data and impact_data.water_proximity_m is not None:
                water_body_classification = self._classify_water_body(
                    impact_data.water_proximity_m,
                    impact_data.water_body_type,
                    impact_data.water_body_width_m
                )
            
            # Combine regulations
            all_regulations = config_regulations + database_regulations
            
            # Calculate environmental risk
            environmental_risk = self._calculate_environmental_risk(
                all_regulations,
                impact_data
            )
            
            # Generate recommendations
            environmental_recommendations = self._generate_environmental_recommendations(
                all_regulations,
                znt_compliance,
                impact_data
            )
            
            # Generate critical warnings
            critical_warnings = self._generate_critical_warnings(
                all_regulations,
                environmental_risk,
                impact_data
            )
            
            # Get seasonal restrictions
            seasonal_restrictions = self._get_seasonal_restrictions(
                input_data.practice_type,
                application_date,
                impact_data
            )
            
            # Count compliance
            compliant_count = sum(
                1 for r in all_regulations if r.compliance_status == ComplianceStatus.COMPLIANT
            )
            non_compliant_count = sum(
                1 for r in all_regulations if r.compliance_status == ComplianceStatus.NON_COMPLIANT
            )
            
            # Determine data source
            data_source = "configuration"
            if znt_compliance and config_regulations:
                data_source = "hybrid"
            elif znt_compliance:
                data_source = "ephy_database"
            
            return EnvironmentalRegulationsOutput(
                success=True,
                practice_type=practice_type,
                location=location,
                environmental_regulations=all_regulations,
                environmental_risk=environmental_risk,
                znt_compliance=znt_compliance,
                product_environmental_data=product_environmental_data,
                water_body_classification=water_body_classification,
                environmental_recommendations=environmental_recommendations,
                critical_warnings=critical_warnings,
                total_regulations=len(all_regulations),
                compliant_count=compliant_count,
                non_compliant_count=non_compliant_count,
                seasonal_restrictions=seasonal_restrictions,
                data_source=data_source
            )
            
        except ValidationError as e:
            logger.error(f"Validation error in environmental regulations: {e}")
            return EnvironmentalRegulationsOutput(
                success=False,
                practice_type=practice_type,
                environmental_risk=EnvironmentalRisk(
                    risk_level=RiskLevel.LOW,
                    risk_score=0.0
                ),
                total_regulations=0,
                error=f"Erreur de validation: {str(e)}",
                error_type="validation",
                data_source="none"
            )
        except Exception as e:
            logger.error(f"Error checking environmental regulations: {e}", exc_info=True)
            return EnvironmentalRegulationsOutput(
                success=False,
                practice_type=practice_type,
                environmental_risk=EnvironmentalRisk(
                    risk_level=RiskLevel.LOW,
                    risk_score=0.0
                ),
                total_regulations=0,
                error=f"Erreur lors de la vérification des réglementations environnementales: {str(e)}",
                error_type="unknown",
                data_source="none"
            )
    
    async def _get_znt_compliance_from_db(
        self,
        db: AsyncSession,
        amm_codes: List[str],
        impact_data: Optional[EnvironmentalImpactData]
    ) -> Optional[List[ZNTCompliance]]:
        """Get ZNT compliance from EPHY database"""
        try:
            znt_compliance_list = []
            
            for amm_code in amm_codes:
                # Get product usage data
                usage_query = select(UsageProduit).where(
                    UsageProduit.numero_amm == amm_code
                ).limit(1)
                
                usage_result = await db.execute(usage_query)
                usage = usage_result.scalars().first()
                
                if not usage:
                    logger.info(f"No usage data found for AMM: {amm_code}")
                    continue
                
                # Check each ZNT type
                znt_types = {
                    "aquatic": usage.znt_aquatique_m,
                    "arthropods": usage.znt_arthropodes_non_cibles_m,
                    "plants": usage.znt_plantes_non_cibles_m
                }
                
                for znt_type, znt_value in znt_types.items():
                    if znt_value and float(znt_value) > 0:
                        required_znt = float(znt_value)
                        actual_distance = impact_data.water_proximity_m if impact_data else None

                        # HIGH PRIORITY #2: Enhanced ZNT reduction logic
                        water_body_type = impact_data.water_body_type if impact_data else WaterBodyType.UNKNOWN
                        equipment_class = impact_data.drift_reduction_equipment if impact_data else EquipmentDriftClass.NO_EQUIPMENT
                        has_vegetation_buffer = impact_data.has_vegetation_buffer if impact_data else False

                        # Calculate ZNT with reduction
                        znt_with_reduction = self._calculate_znt_reduction(
                            required_znt,
                            equipment_class,
                            has_vegetation_buffer,
                            water_body_type
                        )

                        # Check compliance against reduced ZNT
                        is_compliant = True
                        if actual_distance is not None:
                            effective_znt = znt_with_reduction.reduced_znt_m if znt_with_reduction.reduced_znt_m else required_znt
                            is_compliant = actual_distance >= effective_znt

                        znt_compliance_list.append(
                            ZNTCompliance(
                                required_znt_m=required_znt,
                                actual_distance_m=actual_distance,
                                is_compliant=is_compliant,
                                znt_type=znt_type,
                                reduction_possible=znt_with_reduction.reduction_possible,
                                reduction_conditions=znt_with_reduction.reduction_conditions,
                                equipment_class_required=znt_with_reduction.equipment_class_required,
                                max_reduction_percent=znt_with_reduction.max_reduction_percent,
                                minimum_absolute_znt_m=znt_with_reduction.minimum_absolute_znt_m,
                                reduced_znt_m=znt_with_reduction.reduced_znt_m,
                                water_body_type=water_body_type
                            )
                        )
            
            return znt_compliance_list if znt_compliance_list else None
            
        except Exception as e:
            logger.error(f"Error getting ZNT compliance from database: {e}")
            return None

    async def _get_product_environmental_data(
        self,
        db: AsyncSession,
        amm_codes: List[str]
    ) -> Optional[List[ProductEnvironmentalData]]:
        """
        HIGH PRIORITY #1: Get product environmental fate and ecotoxicology data from EPHY
        """
        try:
            product_env_data_list = []

            for amm_code in amm_codes:
                # Get product
                product_query = select(Produit).where(Produit.numero_amm == amm_code)
                product_result = await db.execute(product_query)
                product = product_result.scalars().first()

                if not product:
                    logger.info(f"No product found for AMM: {amm_code}")
                    continue

                # Get active substances
                substances_query = select(SubstanceActive).join(
                    ProduitSubstance
                ).where(ProduitSubstance.numero_amm == amm_code)
                substances_result = await db.execute(substances_query)
                substances = substances_result.scalars().all()

                # Get risk phrases for classification
                risk_phrases_query = select(PhraseRisque).join(
                    ProduitPhraseRisque
                ).where(ProduitPhraseRisque.numero_amm == amm_code)
                risk_phrases_result = await db.execute(risk_phrases_query)
                risk_phrases = risk_phrases_result.scalars().all()

                # Classify based on risk phrases
                is_cmr = any(
                    p.code_phrase in ["H340", "H341", "H350", "H351", "H360", "H361"]
                    for p in risk_phrases
                )

                # Determine aquatic toxicity from H-phrases
                aquatic_toxicity = "low"
                if any(p.code_phrase == "H400" for p in risk_phrases):
                    aquatic_toxicity = "very_high"
                elif any(p.code_phrase == "H410" for p in risk_phrases):
                    aquatic_toxicity = "very_high"
                elif any(p.code_phrase == "H411" for p in risk_phrases):
                    aquatic_toxicity = "high"
                elif any(p.code_phrase in ["H412", "H413"] for p in risk_phrases):
                    aquatic_toxicity = "moderate"

                # Determine bee toxicity
                bee_toxicity = "not_toxic"
                if any(p.code_phrase in ["H410", "H411"] for p in risk_phrases):
                    bee_toxicity = "highly_toxic"
                elif any(p.code_phrase in ["H412"] for p in risk_phrases):
                    bee_toxicity = "toxic"

                # Check for PBT/vPvB (would need additional data, using CMR as proxy)
                is_pbt = False  # Would need specific data
                is_vpvb = False  # Would need specific data

                product_env_data_list.append(
                    ProductEnvironmentalData(
                        amm_code=amm_code,
                        product_name=product.nom_produit,
                        active_substances=[s.nom_substance for s in substances],
                        is_cmr=is_cmr,
                        aquatic_toxicity_level=aquatic_toxicity,
                        bee_toxicity=bee_toxicity,
                        is_pbt=is_pbt,
                        is_vpvb=is_vpvb
                    )
                )

            return product_env_data_list if product_env_data_list else None

        except Exception as e:
            logger.error(f"Error getting product environmental data: {e}")
            return None

    def _calculate_znt_reduction(
        self,
        base_znt_m: float,
        equipment_class: EquipmentDriftClass,
        has_vegetation_buffer: bool,
        water_body_type: WaterBodyType
    ) -> ZNTCompliance:
        """
        HIGH PRIORITY #2: Calculate ZNT with proper reduction rules

        Equipment-based reduction:
        - 1-star: 25% reduction
        - 3-star: 33% reduction
        - 5-star: 50% reduction

        Vegetation buffer: +20% additional reduction
        Maximum total reduction: 66% (cannot exceed 2/3)
        """
        # Drinking water sources: NO reduction allowed
        # Note: is_compliant will be properly set by caller based on actual_distance
        if water_body_type == WaterBodyType.DRINKING_WATER_SOURCE:
            return ZNTCompliance(
                required_znt_m=max(base_znt_m, 200),
                reduction_possible=False,
                minimum_absolute_znt_m=200,
                water_body_type=water_body_type,
                is_compliant=True,  # Placeholder - caller will override with actual check
                znt_type="drinking_water"
            )

        # Equipment-based reduction rates
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

        # Minimum absolute ZNT (cannot go below these values)
        min_znt_by_type = {
            WaterBodyType.PERMANENT_STREAM: 5.0,
            WaterBodyType.INTERMITTENT_STREAM: 5.0,
            WaterBodyType.LAKE_POND: 5.0,
            WaterBodyType.WETLAND: 5.0,
            WaterBodyType.DRAINAGE_DITCH: 1.0,
            WaterBodyType.UNKNOWN: 5.0
        }

        min_znt = min_znt_by_type.get(water_body_type, 5.0)

        # Apply minimum cap with explicit logging
        if reduced_znt < min_znt:
            logger.debug(
                f"ZNT reduction capped: {reduced_znt:.1f}m → {min_znt}m (minimum for {water_body_type.value})"
            )
        final_znt = max(reduced_znt, min_znt)

        # Build reduction conditions
        reduction_conditions = []
        if total_reduction > 0:
            if equipment_class != EquipmentDriftClass.NO_EQUIPMENT:
                reduction_conditions.append(
                    f"Buses anti-dérive {equipment_class.value} homologuées"
                )
            if has_vegetation_buffer:
                reduction_conditions.append(
                    "Bande enherbée ou végétalisée (largeur ≥ 5m)"
                )
            reduction_conditions.append(
                "Conditions météo favorables (vent < 19 km/h)"
            )
            reduction_conditions.append(
                f"ZNT minimale absolue: {min_znt}m"
            )

        # Determine required equipment class for reduction
        equipment_required = None
        if base_znt_m > 5:
            equipment_required = EquipmentDriftClass.THREE_STAR

        return ZNTCompliance(
            required_znt_m=base_znt_m,
            reduced_znt_m=final_znt if total_reduction > 0 else None,
            reduction_possible=total_reduction > 0,
            equipment_class_required=equipment_required,
            max_reduction_percent=total_reduction * 100 if total_reduction > 0 else None,
            minimum_absolute_znt_m=min_znt,
            water_body_type=water_body_type,
            reduction_conditions=reduction_conditions if reduction_conditions else None,
            is_compliant=False,  # Will be updated by caller
            znt_type="calculated"
        )

    def _classify_water_body(
        self,
        water_proximity_m: float,
        water_body_type: WaterBodyType,
        water_body_width_m: Optional[float]
    ) -> WaterBodyClassification:
        """
        HIGH PRIORITY #3: Classify water body and determine protection requirements

        Note: water_body_width_m can affect ZNT categories in some regions.
        Large rivers (>7.5m) may have different requirements than small streams.
        Currently using type-based rules; width-based adjustments can be added later.
        """
        # Water body type-specific rules
        water_body_rules = {
            WaterBodyType.DRINKING_WATER_SOURCE: {
                "base_znt_m": 200.0,
                "reduction_allowed": False,
                "special_protections": [
                    "Périmètre de protection rapprochée (PPR)",
                    "Interdiction totale de produits phytosanitaires",
                    "Autorisation préfectorale requise pour toute intervention",
                    "Sanctions pénales en cas de pollution"
                ],
                "is_drinking_water_source": True,
                "is_fish_bearing": False
            },
            WaterBodyType.PERMANENT_STREAM: {
                "base_znt_m": 5.0,
                "reduction_allowed": True,
                "special_protections": [
                    "Protection contre le ruissellement",
                    "Bande enherbée recommandée (5-10m)",
                    "Interdiction de rinçage du matériel",
                    "Respect des ZNT aquatiques, arthropodes, plantes"
                ],
                "is_drinking_water_source": False,
                "is_fish_bearing": True
            },
            WaterBodyType.INTERMITTENT_STREAM: {
                "base_znt_m": 5.0,
                "reduction_allowed": True,
                "special_protections": [
                    "Vérifier l'état (sec ou en eau) avant traitement",
                    "Protection renforcée en période d'écoulement",
                    "Attention aux connexions avec cours d'eau permanents",
                    "Bande enherbée recommandée"
                ],
                "is_drinking_water_source": False,
                "is_fish_bearing": False
            },
            WaterBodyType.DRAINAGE_DITCH: {
                "base_znt_m": 1.0,
                "reduction_allowed": False,
                "special_protections": [
                    "Éviter le ruissellement direct",
                    "Attention aux connexions avec cours d'eau",
                    "Pas de rinçage du matériel à proximité",
                    "Vérifier l'exutoire du fossé"
                ],
                "is_drinking_water_source": False,
                "is_fish_bearing": False
            },
            WaterBodyType.LAKE_POND: {
                "base_znt_m": 5.0,
                "reduction_allowed": True,
                "special_protections": [
                    "Protection contre le ruissellement",
                    "Attention aux zones de baignade",
                    "Respect des ZNT aquatiques",
                    "Bande enherbée recommandée"
                ],
                "is_drinking_water_source": False,
                "is_fish_bearing": True
            },
            WaterBodyType.WETLAND: {
                "base_znt_m": 10.0,
                "reduction_allowed": False,
                "special_protections": [
                    "Zone humide protégée (Code de l'environnement)",
                    "Biodiversité sensible (amphibiens, oiseaux)",
                    "Interdiction stricte de traitement dans la zone",
                    "Possible classement Natura 2000"
                ],
                "is_drinking_water_source": False,
                "is_fish_bearing": True
            }
        }

        # Get rules for water body type
        rules = water_body_rules.get(water_body_type, {
            "base_znt_m": 5.0,
            "reduction_allowed": True,
            "special_protections": [
                "Respecter les ZNT réglementaires",
                "Éviter le ruissellement"
            ],
            "is_drinking_water_source": False,
            "is_fish_bearing": False
        })

        return WaterBodyClassification(
            water_body_type=water_body_type,
            base_znt_m=rules["base_znt_m"],
            reduction_allowed=rules["reduction_allowed"],
            special_protections=rules["special_protections"],
            is_drinking_water_source=rules["is_drinking_water_source"],
            is_fish_bearing=rules["is_fish_bearing"]
        )

    def _create_znt_regulation(self, znt_compliance: List[ZNTCompliance]) -> EnvironmentalRegulation:
        """Create environmental regulation from ZNT compliance data"""
        # Aggregate ZNT requirements
        required_measures = []
        restrictions = []
        penalties = []
        znt_requirements = {}

        non_compliant = any(not z.is_compliant for z in znt_compliance)

        for znt in znt_compliance:
            znt_requirements[f"{znt.znt_type}_m"] = znt.required_znt_m
            required_measures.append(
                f"Respecter ZNT de {znt.required_znt_m}m pour {znt.znt_type}"
            )

            if znt.reduction_possible and znt.reduction_conditions:
                required_measures.append(
                    f"Réduction ZNT possible: {', '.join(znt.reduction_conditions)}"
                )

        restrictions = [
            "Interdiction de traiter à moins de la ZNT",
            "Interdiction de traiter par vent fort (> 19 km/h)",
            "Interdiction de traiter en cas de pluie imminente"
        ]

        penalties = [
            "Amende: 3000€ à 30000€ (Article L253-17 du Code rural)",
            "Suspension de l'autorisation de traitement",
            "Retrait des aides PAC en cas de non-conformité répétée"
        ]

        legal_references = [
            "Arrêté du 4 mai 2017 relatif aux ZNT",
            "Code rural et de la pêche maritime - Article L253-7",
            "Code de l'environnement - Article L216-6"
        ]

        compliance_status = ComplianceStatus.NON_COMPLIANT if non_compliant else ComplianceStatus.COMPLIANT

        return EnvironmentalRegulation(
            regulation_type=RegulationType.ZNT_COMPLIANCE,
            regulation_name="Zones Non Traitées (ZNT) - Base de données EPHY",
            compliance_status=compliance_status,
            environmental_impact=EnvironmentalImpactLevel.HIGH,
            required_measures=required_measures,
            restrictions=restrictions,
            penalties=penalties,
            legal_references=legal_references,
            znt_requirements=znt_requirements,
            source="ephy_database"
        )

    def _get_config_regulations(
        self,
        practice_type: str,
        impact_data: Optional[EnvironmentalImpactData]
    ) -> List[EnvironmentalRegulation]:
        """Get configuration-based environmental regulations"""
        regulations = []

        # Configuration database
        environmental_database = {
            "spraying": {
                "water_protection": {
                    "regulation_name": "Protection des eaux",
                    "environmental_impact": EnvironmentalImpactLevel.HIGH,
                    "required_measures": [
                        "Respecter les ZNT (zones non traitées)",
                        "Éviter le ruissellement vers les cours d'eau",
                        "Respecter les doses homologuées",
                        "Utiliser des buses anti-dérive"
                    ],
                    "restrictions": [
                        "Interdiction de traiter à proximité immédiate des cours d'eau",
                        "Interdiction de traiter en cas de pluie imminente",
                        "Interdiction de rincer le matériel près des points d'eau"
                    ],
                    "penalties": [
                        "Amende: 3000€ à 30000€",
                        "Suspension de l'autorisation de traitement",
                        "Responsabilité civile en cas de pollution"
                    ],
                    "legal_references": [
                        "Code de l'environnement - Article L216-6",
                        "Arrêté du 4 mai 2017 relatif aux ZNT",
                        "Directive cadre sur l'eau 2000/60/CE"
                    ]
                },
                "biodiversity_protection": {
                    "regulation_name": "Protection de la biodiversité",
                    "environmental_impact": EnvironmentalImpactLevel.MODERATE,
                    "required_measures": [
                        "Éviter les périodes de floraison pour protéger les abeilles",
                        "Respecter les cycles de reproduction de la faune",
                        "Privilégier les alternatives biologiques",
                        "Maintenir des zones de biodiversité (haies, bandes enherbées)"
                    ],
                    "restrictions": [
                        "Interdiction de traiter pendant la floraison (abeilles)",
                        "Interdiction de traiter pendant la nidification (oiseaux)",
                        "Restrictions en zones Natura 2000"
                    ],
                    "penalties": [
                        "Amende: 2000€ à 15000€",
                        "Compensation écologique obligatoire",
                        "Suspension des aides environnementales"
                    ],
                    "legal_references": [
                        "Code de l'environnement - Article L411-1",
                        "Directive Habitats 92/43/CEE",
                        "Arrêté du 28 novembre 2003 (protection des abeilles)"
                    ]
                },
                "air_quality": {
                    "regulation_name": "Qualité de l'air",
                    "environmental_impact": EnvironmentalImpactLevel.MODERATE,
                    "required_measures": [
                        "Éviter la dérive de pulvérisation",
                        "Traiter par vent favorable (< 19 km/h)",
                        "Utiliser du matériel contrôlé et homologué",
                        "Respecter les distances par rapport aux habitations"
                    ],
                    "restrictions": [
                        "Interdiction de traiter par vent fort (> 19 km/h)",
                        "Interdiction de traiter à proximité des habitations (50m minimum)",
                        "Interdiction de traiter en période de forte chaleur"
                    ],
                    "penalties": [
                        "Amende: 1500€ à 10000€",
                        "Suspension de l'activité de traitement",
                        "Responsabilité civile en cas de dommages"
                    ],
                    "legal_references": [
                        "Code de l'environnement - Article L220-1",
                        "Arrêté du 27 juin 2016 (distances habitations)",
                        "Directive 2008/50/CE (qualité de l'air)"
                    ]
                }
            },
            "fertilization": {
                "nitrate_directive": {
                    "regulation_name": "Directive Nitrates",
                    "environmental_impact": EnvironmentalImpactLevel.HIGH,
                    "required_measures": [
                        "Respecter le plafond d'azote (170 kg N/ha/an)",
                        "Établir un plan d'épandage",
                        "Tenir un cahier d'enregistrement",
                        "Respecter les périodes d'interdiction d'épandage"
                    ],
                    "restrictions": [
                        "Interdiction d'épandage en hiver (15 nov - 15 janv)",
                        "Interdiction d'épandage à proximité des cours d'eau",
                        "Interdiction d'épandage sur sol gelé ou enneigé"
                    ],
                    "penalties": [
                        "Amende: 5000€ à 30000€",
                        "Suspension des aides PAC",
                        "Mise en demeure de régularisation"
                    ],
                    "legal_references": [
                        "Directive 91/676/CEE (Directive Nitrates)",
                        "Code de l'environnement - Article R211-80",
                        "Arrêté du 19 décembre 2011 (programme d'actions)"
                    ]
                },
                "phosphorus_management": {
                    "regulation_name": "Gestion du phosphore",
                    "environmental_impact": EnvironmentalImpactLevel.MODERATE,
                    "required_measures": [
                        "Respecter le plafond de phosphore",
                        "Réaliser des analyses de sol régulières",
                        "Pratiquer la rotation des cultures",
                        "Éviter les apports excessifs"
                    ],
                    "restrictions": [
                        "Interdiction d'apport en cas de surplus avéré",
                        "Interdiction d'épandage à proximité des cours d'eau",
                        "Restrictions en zones sensibles"
                    ],
                    "penalties": [
                        "Amende: 3000€ à 15000€",
                        "Suspension des aides environnementales",
                        "Obligation de remédiation"
                    ],
                    "legal_references": [
                        "Code de l'environnement - Article L216-6",
                        "Directive cadre sur l'eau 2000/60/CE"
                    ]
                }
            },
            "irrigation": {
                "water_usage": {
                    "regulation_name": "Usage de l'eau",
                    "environmental_impact": EnvironmentalImpactLevel.HIGH,
                    "required_measures": [
                        "Installer un compteur d'eau",
                        "Respecter le plafond d'usage autorisé",
                        "Optimiser l'efficacité de l'irrigation",
                        "Déclarer les prélèvements"
                    ],
                    "restrictions": [
                        "Interdiction d'irrigation en période de sécheresse",
                        "Restrictions horaires en été (irrigation nocturne)",
                        "Interdiction de prélèvement sans autorisation"
                    ],
                    "penalties": [
                        "Amende: 4000€ à 30000€",
                        "Suspension du droit de prélèvement",
                        "Responsabilité pénale en cas de prélèvement illégal"
                    ],
                    "legal_references": [
                        "Code de l'environnement - Article L214-1",
                        "Loi sur l'eau et les milieux aquatiques (2006)",
                        "Arrêtés préfectoraux sécheresse"
                    ]
                },
                "groundwater_protection": {
                    "regulation_name": "Protection des eaux souterraines",
                    "environmental_impact": EnvironmentalImpactLevel.HIGH,
                    "required_measures": [
                        "Éviter la contamination des nappes phréatiques",
                        "Surveiller la qualité de l'eau",
                        "Respecter les zones de protection des captages",
                        "Limiter les intrants en zones vulnérables"
                    ],
                    "restrictions": [
                        "Interdiction de traiter à proximité des captages d'eau potable",
                        "Interdiction de produits dangereux en zones de protection",
                        "Restrictions d'usage en périmètres de protection"
                    ],
                    "penalties": [
                        "Amende: 5000€ à 50000€",
                        "Suspension de l'activité agricole",
                        "Responsabilité civile et pénale en cas de pollution"
                    ],
                    "legal_references": [
                        "Code de la santé publique - Article L1321-2",
                        "Code de l'environnement - Article L211-3",
                        "Directive 2006/118/CE (eaux souterraines)"
                    ]
                }
            }
        }

        # Get regulations for practice type
        if practice_type not in environmental_database:
            return regulations

        practice_regulations = environmental_database[practice_type]

        for reg_type, reg_data in practice_regulations.items():
            # Assess compliance
            compliance_status = self._assess_compliance(reg_data, impact_data)

            regulation = EnvironmentalRegulation(
                regulation_type=RegulationType(reg_type),
                regulation_name=reg_data["regulation_name"],
                compliance_status=compliance_status,
                environmental_impact=reg_data["environmental_impact"],
                required_measures=reg_data["required_measures"],
                restrictions=reg_data["restrictions"],
                penalties=reg_data["penalties"],
                legal_references=reg_data.get("legal_references"),
                source="configuration"
            )
            regulations.append(regulation)

        return regulations

    def _assess_compliance(
        self,
        regulation_data: Dict[str, Any],
        impact_data: Optional[EnvironmentalImpactData]
    ) -> ComplianceStatus:
        """Assess compliance status based on environmental impact"""
        if not impact_data:
            return ComplianceStatus.UNKNOWN

        # Check water proximity for water-related regulations
        if "water" in regulation_data["regulation_name"].lower():
            if impact_data.water_proximity_m is not None:
                if impact_data.water_proximity_m < 5:
                    return ComplianceStatus.NON_COMPLIANT
                elif impact_data.water_proximity_m < 20:
                    return ComplianceStatus.PARTIALLY_COMPLIANT

        # Check flowering period for biodiversity
        if "biodiversité" in regulation_data["regulation_name"].lower():
            if impact_data.flowering_period:
                return ComplianceStatus.NON_COMPLIANT

        # Check wind speed for air quality
        if "air" in regulation_data["regulation_name"].lower():
            if impact_data.wind_speed_kmh is not None:
                if impact_data.wind_speed_kmh > 19:
                    return ComplianceStatus.NON_COMPLIANT
                elif impact_data.wind_speed_kmh > 15:
                    return ComplianceStatus.PARTIALLY_COMPLIANT

        # Check sensitive areas
        if impact_data.sensitive_area:
            return ComplianceStatus.PARTIALLY_COMPLIANT

        # Check overall impact level
        if impact_data.impact_level == EnvironmentalImpactLevel.LOW:
            return ComplianceStatus.COMPLIANT
        elif impact_data.impact_level == EnvironmentalImpactLevel.MODERATE:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        elif impact_data.impact_level in [EnvironmentalImpactLevel.HIGH, EnvironmentalImpactLevel.CRITICAL]:
            return ComplianceStatus.NON_COMPLIANT

        return ComplianceStatus.UNKNOWN

    def _calculate_environmental_risk(
        self,
        regulations: List[EnvironmentalRegulation],
        impact_data: Optional[EnvironmentalImpactData]
    ) -> EnvironmentalRisk:
        """Calculate environmental risk based on regulations and impact"""
        if not regulations:
            return EnvironmentalRisk(
                risk_level=RiskLevel.LOW,
                risk_score=0.0
            )

        risk_score = 0.0
        high_impact_count = 0
        non_compliant_count = 0
        critical_issues = []

        for regulation in regulations:
            # Count high impact regulations
            if regulation.environmental_impact in [EnvironmentalImpactLevel.HIGH, EnvironmentalImpactLevel.CRITICAL]:
                high_impact_count += 1

            # Count non-compliant
            if regulation.compliance_status == ComplianceStatus.NON_COMPLIANT:
                non_compliant_count += 1
                critical_issues.append(f"Non-conformité: {regulation.regulation_name}")

            # Calculate risk contribution
            impact_weight = {
                EnvironmentalImpactLevel.LOW: 0.1,
                EnvironmentalImpactLevel.MODERATE: 0.3,
                EnvironmentalImpactLevel.HIGH: 0.6,
                EnvironmentalImpactLevel.CRITICAL: 1.0
            }.get(regulation.environmental_impact, 0.3)

            compliance_weight = {
                ComplianceStatus.COMPLIANT: 0.1,
                ComplianceStatus.PARTIALLY_COMPLIANT: 0.5,
                ComplianceStatus.NON_COMPLIANT: 1.0,
                ComplianceStatus.UNKNOWN: 0.3
            }.get(regulation.compliance_status, 0.3)

            risk_score += impact_weight * compliance_weight

        # Normalize risk score
        if len(regulations) > 0:
            risk_score = risk_score / len(regulations)

        # Boost risk if in sensitive area
        if impact_data and impact_data.sensitive_area:
            risk_score = min(1.0, risk_score * 1.3)
            critical_issues.append("Zone sensible (Natura 2000 ou équivalent)")

        # Determine risk level
        if risk_score > 0.7 or non_compliant_count >= 2:
            risk_level = RiskLevel.CRITICAL
        elif risk_score > 0.5 or non_compliant_count >= 1:
            risk_level = RiskLevel.HIGH
        elif risk_score > 0.3:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW

        return EnvironmentalRisk(
            risk_level=risk_level,
            risk_score=round(risk_score, 2),
            high_impact_count=high_impact_count,
            non_compliant_count=non_compliant_count,
            critical_issues=critical_issues
        )

    def _generate_environmental_recommendations(
        self,
        regulations: List[EnvironmentalRegulation],
        znt_compliance: Optional[List[ZNTCompliance]],
        impact_data: Optional[EnvironmentalImpactData]
    ) -> List[str]:
        """Generate environmental recommendations"""
        recommendations = []

        # ZNT-specific recommendations
        if znt_compliance:
            for znt in znt_compliance:
                if not znt.is_compliant:
                    recommendations.append(
                        f"⚠️ ZNT NON RESPECTÉE: Distance actuelle {znt.actual_distance_m}m < "
                        f"ZNT requise {znt.required_znt_m}m ({znt.znt_type})"
                    )
                    if znt.reduction_possible:
                        recommendations.append(
                            f"💡 Réduction ZNT possible avec: {', '.join(znt.reduction_conditions)}"
                        )
                else:
                    recommendations.append(
                        f"✅ ZNT respectée: {znt.required_znt_m}m pour {znt.znt_type}"
                    )

        # Regulation-specific recommendations
        for regulation in regulations:
            if regulation.compliance_status == ComplianceStatus.NON_COMPLIANT:
                recommendations.append(f"⚠️ Non-conformité: {regulation.regulation_name}")
                recommendations.extend([f"  • {measure}" for measure in regulation.required_measures[:2]])
            elif regulation.compliance_status == ComplianceStatus.PARTIALLY_COMPLIANT:
                recommendations.append(f"⚠️ Conformité partielle: {regulation.regulation_name}")
                recommendations.extend([f"  • {measure}" for measure in regulation.required_measures[:1]])

        # Impact-based recommendations
        if impact_data:
            if impact_data.water_proximity_m is not None and impact_data.water_proximity_m < 20:
                recommendations.append(
                    "💧 Proximité d'eau détectée: Utiliser des buses anti-dérive et éviter les traitements par vent fort"
                )

            if impact_data.flowering_period:
                recommendations.append(
                    "🐝 Période de floraison: Reporter le traitement ou utiliser des produits non toxiques pour les abeilles"
                )

            # Weather recommendations (ENHANCED)
            if impact_data.wind_speed_kmh and impact_data.wind_speed_kmh > 15:
                recommendations.append(
                    f"💨 Vent trop fort ({impact_data.wind_speed_kmh} km/h): Reporter le traitement (max 19 km/h)"
                )

            if impact_data.temperature_c is not None and impact_data.temperature_c > 25:
                recommendations.append(
                    f"🌡️ Température élevée ({impact_data.temperature_c}°C): Traiter tôt le matin ou en soirée"
                )

            if impact_data.humidity_percent is not None and impact_data.humidity_percent < 50:
                recommendations.append(
                    f"💧 Humidité faible ({impact_data.humidity_percent}%): Augmenter le volume de bouillie pour limiter la dérive"
                )

            if impact_data.rain_forecast_48h:
                recommendations.append(
                    "🌧️ Pluie prévue: Attendre une fenêtre météo stable (48-72h sans pluie)"
                )

            if impact_data.sensitive_area:
                recommendations.append(
                    "🌿 Zone sensible: Respecter strictement toutes les réglementations environnementales"
                )

        if not recommendations:
            recommendations.append("✅ Toutes les réglementations environnementales sont respectées")

        return recommendations

    def _generate_critical_warnings(
        self,
        regulations: List[EnvironmentalRegulation],
        environmental_risk: EnvironmentalRisk,
        impact_data: Optional[EnvironmentalImpactData]
    ) -> List[str]:
        """Generate critical environmental warnings"""
        warnings = []

        # Critical risk level
        if environmental_risk.risk_level == RiskLevel.CRITICAL:
            warnings.append(
                "🚨 RISQUE ENVIRONNEMENTAL CRITIQUE: Intervention fortement déconseillée dans ces conditions"
            )

        # Multiple non-compliances
        if environmental_risk.non_compliant_count >= 2:
            warnings.append(
                f"⚠️ ATTENTION: {environmental_risk.non_compliant_count} réglementations non respectées - "
                "Risque de sanctions importantes"
            )

        # Specific critical conditions
        if impact_data:
            if impact_data.water_proximity_m is not None and impact_data.water_proximity_m < 5:
                warnings.append(
                    "🚫 INTERDICTION: Distance au cours d'eau < 5m - Traitement INTERDIT"
                )

            # Weather-based restrictions (ENHANCED)
            if impact_data.wind_speed_kmh and impact_data.wind_speed_kmh > 19:
                warnings.append(
                    "🚫 INTERDICTION: Vent > 19 km/h - Traitement INTERDIT (risque de dérive)"
                )

            if impact_data.temperature_c is not None:
                if impact_data.temperature_c > 25:
                    warnings.append(
                        f"⚠️ TEMPÉRATURE ÉLEVÉE: {impact_data.temperature_c}°C - Risque d'évaporation et efficacité réduite"
                    )
                elif impact_data.temperature_c < 10:
                    warnings.append(
                        f"⚠️ TEMPÉRATURE BASSE: {impact_data.temperature_c}°C - Efficacité réduite (vérifier étiquette produit)"
                    )

            if impact_data.humidity_percent is not None and impact_data.humidity_percent < 30:
                warnings.append(
                    f"⚠️ HUMIDITÉ FAIBLE: {impact_data.humidity_percent}% - Risque de dérive accru"
                )

            if impact_data.rain_forecast_48h:
                warnings.append(
                    "⚠️ PLUIE PRÉVUE (48h): Risque de ruissellement - Reporter le traitement"
                )

            if impact_data.temperature_inversion:
                warnings.append(
                    "🚫 INTERDICTION: Inversion de température - Risque de dérive MAJEUR - Traitement INTERDIT"
                )

            if impact_data.sensitive_area and environmental_risk.non_compliant_count > 0:
                warnings.append(
                    "⚠️ ZONE SENSIBLE: Non-conformité en zone protégée - Sanctions renforcées"
                )

        # Add critical issues from risk assessment
        for issue in environmental_risk.critical_issues:
            if issue not in warnings:
                warnings.append(f"⚠️ {issue}")

        return warnings

    def _get_seasonal_restrictions(
        self,
        practice_type: str,
        application_date: Optional[date],
        impact_data: Optional[EnvironmentalImpactData]
    ) -> Optional[List[str]]:
        """Get seasonal restrictions based on application date"""
        if not application_date:
            return None

        restrictions = []
        month = application_date.month

        # Fertilization restrictions (winter)
        if practice_type == PracticeType.FERTILIZATION:
            if month in [11, 12, 1]:
                restrictions.append(
                    "❄️ Période d'interdiction d'épandage (15 nov - 15 janv) - Directive Nitrates"
                )

        # Spraying restrictions (flowering)
        if practice_type == PracticeType.SPRAYING:
            if month in [4, 5, 6, 7]:
                restrictions.append(
                    "🌸 Période de floraison: Vérifier l'absence de floraison avant traitement (protection des abeilles)"
                )

            if impact_data and impact_data.flowering_period:
                restrictions.append(
                    "🐝 INTERDICTION: Traitement pendant la floraison (Arrêté du 28 novembre 2003)"
                )

        # Irrigation restrictions (summer drought)
        if practice_type == PracticeType.IRRIGATION:
            if month in [7, 8, 9]:
                restrictions.append(
                    "☀️ Période de sécheresse potentielle: Vérifier les arrêtés préfectoraux en vigueur"
                )

        return restrictions if restrictions else None


# ============================================================================
# ASYNC WRAPPER FUNCTION
# ============================================================================

async def check_environmental_regulations_async(
    practice_type: str,
    location: Optional[str] = None,
    environmental_impact: Optional[Dict[str, Any]] = None,
    amm_codes: Optional[List[str]] = None,
    crop_eppo_code: Optional[str] = None,
    field_size_ha: Optional[float] = None,
    application_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async wrapper for environmental regulations check.

    Args:
        practice_type: Type of agricultural practice
        location: Location (department, region)
        environmental_impact: Environmental impact assessment data
        amm_codes: AMM codes of products to check
        crop_eppo_code: EPPO code of the crop
        field_size_ha: Field size in hectares
        application_date: Planned application date (YYYY-MM-DD)

    Returns:
        Dict with environmental compliance data
    """
    service = EnhancedEnvironmentalRegulationsService()

    # Parse application date
    parsed_date = None
    if application_date:
        try:
            parsed_date = datetime.strptime(application_date, "%Y-%m-%d").date()
        except ValueError:
            logger.warning(f"Invalid date format: {application_date}")

    result = await service.check_environmental_regulations(
        practice_type=practice_type,
        location=location,
        environmental_impact=environmental_impact,
        amm_codes=amm_codes,
        crop_eppo_code=crop_eppo_code,
        field_size_ha=field_size_ha,
        application_date=parsed_date
    )

    return result.model_dump()


# ============================================================================
# LANGCHAIN TOOL
# ============================================================================

check_environmental_regulations_tool_enhanced = StructuredTool.from_function(
    coroutine=check_environmental_regulations_async,
    name="check_environmental_regulations_enhanced",
    description="""Vérifie la conformité aux réglementations environnementales pour les pratiques agricoles.

    Intégration base de données EPHY pour:
    - ZNT (Zones Non Traitées) aquatiques, arthropodes, plantes
    - Protection des eaux (cours d'eau, nappes phréatiques)
    - Protection de la biodiversité (abeilles, Natura 2000)
    - Qualité de l'air (dérive, distances habitations)
    - Directive Nitrates (fertilisation)
    - Restrictions saisonnières

    Retourne: Conformité environnementale, risques, recommandations, avertissements critiques.""",
    handle_validation_error=False
)

