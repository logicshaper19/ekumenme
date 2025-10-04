"""
Environmental Regulations Service
Extracted from check_environmental_regulations_tool.py for better maintainability
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import ValidationError
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
from app.config.environmental_regulations_config import (
    ENVIRONMENTAL_DATABASE,
    ZNT_REDUCTION_RATES,
    MIN_ZNT_BY_WATER_BODY_TYPE,
    WATER_BODY_RULES,
    RISK_WEIGHTS
)

logger = logging.getLogger(__name__)


class EnvironmentalRegulationsService:
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
            config_regulations = self.get_config_regulations(
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
                    znt_compliance = await self.get_znt_compliance_from_db(
                        db, amm_codes, impact_data
                    )

                    if znt_compliance:
                        # Create regulation from ZNT data
                        znt_regulation = self.create_znt_regulation(znt_compliance)
                        database_regulations.append(znt_regulation)

                    # Get product environmental data (HIGH PRIORITY #1)
                    product_environmental_data = await self.get_product_environmental_data(
                        db, amm_codes
                    )

            # Classify water body (HIGH PRIORITY #3)
            if impact_data and impact_data.water_proximity_m is not None:
                water_body_classification = self.classify_water_body(
                    impact_data.water_proximity_m,
                    impact_data.water_body_type if impact_data.water_body_type else WaterBodyType.UNKNOWN,
                    impact_data.water_body_width_m
                )

            # Combine all regulations
            all_regulations = config_regulations + database_regulations

            # Assess overall compliance
            overall_compliance = self.assess_compliance(all_regulations, impact_data)

            # Calculate environmental risk
            environmental_risk = self.calculate_environmental_risk(all_regulations)

            # Generate recommendations
            recommendations = self.generate_environmental_recommendations(
                all_regulations, znt_compliance, product_environmental_data, water_body_classification
            )

            # Generate critical warnings
            critical_warnings = self.generate_critical_warnings(
                all_regulations, znt_compliance, product_environmental_data
            )

            # Get seasonal restrictions
            seasonal_restrictions = self.get_seasonal_restrictions(
                practice_type, application_date, location
            )

            return EnvironmentalRegulationsOutput(
                practice_type=practice_type,
                location=location,
                regulations=all_regulations,
                znt_compliance=znt_compliance,
                product_environmental_data=product_environmental_data,
                water_body_classification=water_body_classification,
                overall_compliance=overall_compliance,
                environmental_risk=environmental_risk,
                recommendations=recommendations,
                critical_warnings=critical_warnings,
                seasonal_restrictions=seasonal_restrictions,
                generated_at=datetime.utcnow()
            )

        except ValidationError as e:
            logger.error(f"Validation error in environmental regulations check: {e}")
            raise ValueError(f"Invalid input data: {e}")
        except Exception as e:
            logger.error(f"Error checking environmental regulations: {e}")
            raise Exception(f"Failed to check environmental regulations: {str(e)}")

    async def get_znt_compliance_from_db(
        self,
        db: AsyncSession,
        amm_codes: List[str],
        impact_data: Optional[EnvironmentalImpactData]
    ) -> Optional[List[ZNTCompliance]]:
        """
        Get ZNT compliance from EPHY database

        PERFORMANCE OPTIMIZATION: Batch query for multiple products
        """
        try:
            znt_compliance_list = []

            # PERFORMANCE FIX: Batch query instead of N queries
            try:
                usage_query = select(UsageProduit).where(
                    UsageProduit.numero_amm.in_(amm_codes)
                )
                usage_result = await db.execute(usage_query)
                usages = usage_result.scalars().all()
            except Exception as e:
                logger.error(f"Database error fetching ZNT data: {e}")
                return None

            if not usages:
                logger.info(f"No usage data found for AMM codes: {amm_codes}")
                return None

            # Validate data quality before processing
            valid_usages = []
            for usage in usages:
                # Check if at least one ZNT value is valid
                has_valid_znt = False
                for znt_value in [usage.znt_aquatique_m, usage.znt_arthropodes_non_cibles_m, usage.znt_plantes_non_cibles_m]:
                    try:
                        if znt_value and float(znt_value) > 0:
                            has_valid_znt = True
                            break
                    except (ValueError, TypeError):
                        continue
                
                if has_valid_znt:
                    valid_usages.append(usage)
                else:
                    logger.warning(f"Skipping usage {usage.numero_amm}: No valid ZNT values")

            if not valid_usages:
                logger.warning(f"No valid ZNT data for any products: {amm_codes}")
                return None

            # Process valid usages only
            for usage in valid_usages:
                
                # Check each ZNT type
                znt_types = {
                    "aquatic": usage.znt_aquatique_m,
                    "arthropods": usage.znt_arthropodes_non_cibles_m,
                    "plants": usage.znt_plantes_non_cibles_m
                }
                
                for znt_type, znt_value in znt_types.items():
                    # EDGE CASE FIX: Validate ZNT value is a valid number
                    try:
                        if znt_value and float(znt_value) > 0:
                            required_znt = float(znt_value)
                        else:
                            continue
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid ZNT value for {znt_type}: {znt_value} - {e}")
                        continue

                    actual_distance = impact_data.water_proximity_m if impact_data else None

                    # HIGH PRIORITY #2: Enhanced ZNT reduction logic
                    water_body_type = impact_data.water_body_type if impact_data else WaterBodyType.UNKNOWN
                    equipment_class = impact_data.drift_reduction_equipment if impact_data else EquipmentDriftClass.NO_EQUIPMENT
                    has_vegetation_buffer = impact_data.has_vegetation_buffer if impact_data else False

                    # Calculate ZNT with reduction
                    znt_with_reduction = self.calculate_znt_reduction(
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
            
            # EDGE CASE FIX: When multiple products, consolidate by ZNT type (use most restrictive)
            if len(znt_compliance_list) > 1:
                znt_by_type = {}
                for znt in znt_compliance_list:
                    znt_type = znt.znt_type
                    if znt_type not in znt_by_type or znt.required_znt_m > znt_by_type[znt_type].required_znt_m:
                        znt_by_type[znt_type] = znt

                znt_compliance_list = list(znt_by_type.values())
                logger.info(f"Consolidated {len(znt_by_type)} ZNT types from multiple products (using most restrictive)")

            return znt_compliance_list if znt_compliance_list else None

        except Exception as e:
            logger.error(f"Error getting ZNT compliance from database: {e}")
            return None

    @redis_cache(ttl=86400, category="product_env")  # 24h cache for expensive product data
    async def get_product_environmental_data(
        self,
        db: AsyncSession,
        amm_codes: List[str]
    ) -> Optional[List[ProductEnvironmentalData]]:
        """
        HIGH PRIORITY #1: Get product environmental fate and ecotoxicology data from EPHY
        PERFORMANCE FIX: Batch queries instead of N+1 pattern
        """
        try:
            if not amm_codes:
                return None

            # BATCH QUERY: Get all products at once
            try:
                products_query = select(Produit).where(Produit.numero_amm.in_(amm_codes))
                products_result = await db.execute(products_query)
                products = products_result.scalars().all()
            except Exception as e:
                logger.error(f"Database error fetching products: {e}")
                return None
            
            if not products:
                logger.info(f"No products found for AMM codes: {amm_codes}")
                return None

            # BATCH QUERY: Get all substances for all products
            try:
                substances_query = (
                    select(SubstanceActive, ProduitSubstance.numero_amm)
                    .join(ProduitSubstance)
                    .where(ProduitSubstance.numero_amm.in_(amm_codes))
                )
                substances_result = await db.execute(substances_query)
            except Exception as e:
                logger.error(f"Database error fetching substances: {e}")
                return None
            
            # Group substances by AMM code
            substances_by_amm = {}
            for substance, amm in substances_result:
                if amm not in substances_by_amm:
                    substances_by_amm[amm] = []
                substances_by_amm[amm].append(substance)

            # BATCH QUERY: Get all risk phrases for all products
            try:
                risk_phrases_query = (
                    select(PhraseRisque, ProduitPhraseRisque.numero_amm)
                    .join(ProduitPhraseRisque)
                    .where(ProduitPhraseRisque.numero_amm.in_(amm_codes))
                )
                risk_phrases_result = await db.execute(risk_phrases_query)
            except Exception as e:
                logger.error(f"Database error fetching risk phrases: {e}")
                return None
            
            # Group risk phrases by AMM code
            risk_phrases_by_amm = {}
            for phrase, amm in risk_phrases_result:
                if amm not in risk_phrases_by_amm:
                    risk_phrases_by_amm[amm] = []
                risk_phrases_by_amm[amm].append(phrase)

            # Process each product with pre-fetched data
            product_env_data_list = []
            for product in products:
                amm = product.numero_amm
                substances = substances_by_amm.get(amm, [])
                risk_phrases = risk_phrases_by_amm.get(amm, [])
                
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
                        amm_code=amm,
                        product_name=product.nom_produit,
                        active_substances=[s.nom_substance for s in substances],
                        is_cmr=is_cmr,
                        aquatic_toxicity_level=aquatic_toxicity,
                        bee_toxicity=bee_toxicity,
                        is_pbt=is_pbt,
                        is_vpvb=is_vpvb
                    )
                )

            logger.info(f"Processed {len(product_env_data_list)} products with batch queries (reduced from {len(amm_codes) * 3} to 3 queries)")
            return product_env_data_list if product_env_data_list else None

        except Exception as e:
            logger.error(f"Error getting product environmental data: {e}")
            return None

    def calculate_znt_reduction(
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
        # Special case: Drinking water sources have no reduction
        if water_body_type == WaterBodyType.DRINKING_WATER_SOURCE:
            return ZNTCompliance(
                required_znt_m=base_znt_m,
                actual_distance_m=None,
                is_compliant=True,  # Placeholder - caller will override with actual check
                znt_type="drinking_water"
            )

        # Equipment-based reduction rates
        reduction_rates = ZNT_REDUCTION_RATES

        base_reduction = reduction_rates.get(equipment_class, 0.0)

        # Additional reduction with vegetation buffer
        if has_vegetation_buffer:
            additional_reduction = 0.20  # 20% additional reduction
        else:
            additional_reduction = 0.0

        # Calculate total reduction (capped at 66%)
        total_reduction = min(base_reduction + additional_reduction, 0.66)

        # Calculate reduced ZNT
        reduced_znt = base_znt_m * (1 - total_reduction)

        # Minimum absolute ZNT (cannot go below these values)
        min_znt_by_type = MIN_ZNT_BY_WATER_BODY_TYPE

        min_znt = min_znt_by_type.get(water_body_type, 5.0)

        # Apply minimum cap with explicit logging
        if reduced_znt < min_znt:
            logger.info(f"ZNT reduction capped at minimum {min_znt}m for {water_body_type} (was {reduced_znt:.1f}m)")
            reduced_znt = min_znt

        # Determine reduction conditions
        reduction_conditions = []
        if base_reduction > 0:
            reduction_conditions.append(f"Équipement {equipment_class.value} (-{base_reduction*100:.0f}%)")
        if additional_reduction > 0:
            reduction_conditions.append(f"Zone tampon végétalisée (-{additional_reduction*100:.0f}%)")

        return ZNTCompliance(
            required_znt_m=base_znt_m,
            actual_distance_m=None,
            is_compliant=True,  # Placeholder - caller will override with actual check
            znt_type="calculated",
            reduction_possible=total_reduction > 0,
            reduction_conditions=reduction_conditions,
            equipment_class_required=equipment_class,
            max_reduction_percent=total_reduction * 100,
            minimum_absolute_znt_m=min_znt,
            reduced_znt_m=reduced_znt,
            water_body_type=water_body_type
        )

    def classify_water_body(
        self,
        distance_m: float,
        water_body_type: WaterBodyType,
        width_m: Optional[float] = None
    ) -> WaterBodyClassification:
        """
        HIGH PRIORITY #3: Classify water body and determine ZNT requirements

        Note: water_body_width_m can affect ZNT categories in some regions.
        Large rivers (>7.5m) may have different requirements than small streams.
        Currently using type-based rules; width-based adjustments can be added later.
        """
        # Use imported water body rules
        water_body_rules = WATER_BODY_RULES

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

    def create_znt_regulation(self, znt_compliance: List[ZNTCompliance]) -> EnvironmentalRegulation:
        """Create environmental regulation from ZNT compliance data"""
        required_measures = []
        znt_requirements = {}

        non_compliant = any(not z.is_compliant for z in znt_compliance)

        for znt in znt_compliance:
            znt_requirements[f"{znt.znt_type}_m"] = znt.required_znt_m
            required_measures.append(
                f"Respecter ZNT de {znt.required_znt_m}m pour {znt.znt_type}"
            )

            if znt.reduction_possible and znt.reduction_conditions:
                required_measures.extend([
                    f"Utiliser {', '.join(znt.reduction_conditions)} pour réduire ZNT",
                    f"ZNT minimum absolu: {znt.minimum_absolute_znt_m}m"
                ])

        return EnvironmentalRegulation(
            regulation_name="Zones de Non-Traitement (ZNT)",
            regulation_type=RegulationType.ZNT,
            environmental_impact=EnvironmentalImpactLevel.HIGH,
            compliance_status=ComplianceStatus.COMPLIANT if not non_compliant else ComplianceStatus.NON_COMPLIANT,
            required_measures=required_measures,
            restrictions=[
                "Interdiction de traitement dans la ZNT",
                "Respecter les distances minimales obligatoires"
            ],
            penalties=[
                "Amende: 1500€ à 15000€",
                "Suspension de l'autorisation de traitement",
                "Responsabilité civile en cas de pollution"
            ],
            legal_references=[
                "Arrêté du 4 mai 2017 relatif aux ZNT",
                "Code de l'environnement - Article L216-6"
            ],
            metadata=znt_requirements
        )

    def get_config_regulations(
        self,
        practice_type: str,
        impact_data: Optional[EnvironmentalImpactData]
    ) -> List[EnvironmentalRegulation]:
        """Get configuration-based environmental regulations"""
        regulations = []

        # Use imported configuration database
        environmental_database = ENVIRONMENTAL_DATABASE

        # Get regulations for practice type
        if practice_type not in environmental_database:
            return regulations

        practice_regulations = environmental_database[practice_type]

        for reg_type, reg_data in practice_regulations.items():
            # Assess compliance
            compliance_status = self.assess_compliance(reg_data, impact_data)

            regulation = EnvironmentalRegulation(
                regulation_name=reg_data["regulation_name"],
                regulation_type=RegulationType(reg_type.upper()),
                environmental_impact=reg_data["environmental_impact"],
                compliance_status=compliance_status,
                required_measures=reg_data["required_measures"],
                restrictions=reg_data["restrictions"],
                penalties=reg_data["penalties"],
                legal_references=reg_data["legal_references"]
            )

            regulations.append(regulation)

        return regulations

    def assess_compliance(
        self,
        regulation_data: Dict[str, Any],
        impact_data: Optional[EnvironmentalImpactData]
    ) -> ComplianceStatus:
        """Assess compliance status for a regulation"""
        # This is a simplified compliance assessment
        # In a real implementation, this would check against actual conditions
        
        if not impact_data:
            return ComplianceStatus.UNKNOWN

        # Check if any restrictions are violated
        restrictions = regulation_data.get("restrictions", [])
        
        # Simple compliance check based on environmental impact
        if impact_data.water_proximity_m and impact_data.water_proximity_m < 5:
            return ComplianceStatus.NON_COMPLIANT
        
        return ComplianceStatus.COMPLIANT

    def calculate_environmental_risk(
        self,
        regulations: List[EnvironmentalRegulation]
    ) -> EnvironmentalRisk:
        """Calculate overall environmental risk score"""
        if not regulations:
            return EnvironmentalRisk(
                risk_level=RiskLevel.LOW,
                risk_score=0.0,
                risk_factors=[]
            )

        risk_score = 0.0
        risk_factors = []
        non_compliant_count = 0
        critical_issues = []

        for regulation in regulations:
            # Count non-compliant
            if regulation.compliance_status == ComplianceStatus.NON_COMPLIANT:
                non_compliant_count += 1
                critical_issues.append(f"Non-conformité: {regulation.regulation_name}")

            # Calculate risk contribution using imported weights
            impact_weight = RISK_WEIGHTS["impact_weight"].get(regulation.environmental_impact, 0.3)
            compliance_weight = RISK_WEIGHTS["compliance_weight"].get(regulation.compliance_status, 0.3)

            risk_score += impact_weight * compliance_weight

        # Normalize risk score
        if len(regulations) > 0:
            risk_score = risk_score / len(regulations)

        # Determine risk level
        if risk_score >= 0.8 or non_compliant_count > 2:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.6 or non_compliant_count > 0:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.4:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW

        # Add critical issues to risk factors
        risk_factors.extend(critical_issues)

        return EnvironmentalRisk(
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors
        )

    def generate_environmental_recommendations(
        self,
        regulations: List[EnvironmentalRegulation],
        znt_compliance: Optional[List[ZNTCompliance]],
        product_environmental_data: Optional[List[ProductEnvironmentalData]],
        water_body_classification: Optional[WaterBodyClassification]
    ) -> List[str]:
        """Generate environmental recommendations based on analysis"""
        recommendations = []

        # ZNT recommendations
        if znt_compliance:
            for znt in znt_compliance:
                if not znt.is_compliant:
                    recommendations.append(
                        f"URGENT: Respecter la ZNT de {znt.required_znt_m}m pour {znt.znt_type}"
                    )
                elif znt.reduction_possible:
                    recommendations.append(
                        f"Optimiser: Utiliser {', '.join(znt.reduction_conditions)} pour réduire la ZNT"
                    )

        # Product environmental recommendations
        if product_environmental_data:
            for product in product_environmental_data:
                if product.is_cmr:
                    recommendations.append(
                        f"Attention: {product.product_name} contient des substances CMR"
                    )
                if product.aquatic_toxicity_level in ["high", "very_high"]:
                    recommendations.append(
                        f"Précaution: {product.product_name} très toxique pour les organismes aquatiques"
                    )
                if product.bee_toxicity in ["toxic", "highly_toxic"]:
                    recommendations.append(
                        f"Protection: {product.product_name} toxique pour les abeilles - éviter la floraison"
                    )

        # Water body recommendations
        if water_body_classification:
            if water_body_classification.is_drinking_water_source:
                recommendations.append(
                    "CRITIQUE: Zone de captage d'eau potable - interdiction totale de traitement"
                )
            if water_body_classification.is_fish_bearing:
                recommendations.append(
                    "Protection: Cours d'eau à poissons - respecter strictement les ZNT"
                )

        # General recommendations
        recommendations.extend([
            "Vérifier les conditions météorologiques avant traitement",
            "Utiliser du matériel homologué et bien entretenu",
            "Tenir un registre des traitements effectués"
        ])

        return recommendations

    def generate_critical_warnings(
        self,
        regulations: List[EnvironmentalRegulation],
        znt_compliance: Optional[List[ZNTCompliance]],
        product_environmental_data: Optional[List[ProductEnvironmentalData]]
    ) -> List[str]:
        """Generate critical warnings for immediate attention"""
        warnings = []

        # ZNT warnings
        if znt_compliance:
            for znt in znt_compliance:
                if not znt.is_compliant:
                    warnings.append(
                        f"⚠️ NON-CONFORMITÉ ZNT: Distance insuffisante ({znt.actual_distance_m}m < {znt.required_znt_m}m requis)"
                    )

        # Product warnings
        if product_environmental_data:
            for product in product_environmental_data:
                if product.is_cmr:
                    warnings.append(
                        f"⚠️ SUBSTANCE CMR: {product.product_name} - risque cancérogène, mutagène ou toxique"
                    )
                if product.aquatic_toxicity_level == "very_high":
                    warnings.append(
                        f"⚠️ TOXICITÉ AQUATIQUE: {product.product_name} - très toxique pour les organismes aquatiques"
                    )

        # Regulation warnings
        for regulation in regulations:
            if regulation.compliance_status == ComplianceStatus.NON_COMPLIANT:
                warnings.append(
                    f"⚠️ NON-CONFORMITÉ: {regulation.regulation_name}"
                )

        return warnings

    def get_seasonal_restrictions(
        self,
        practice_type: str,
        application_date: Optional[date],
        location: Optional[str]
    ) -> List[str]:
        """Get seasonal restrictions for the practice"""
        restrictions = []

        if not application_date:
            return restrictions

        # General seasonal restrictions
        month = application_date.month

        if practice_type == "spraying":
            if month in [12, 1, 2]:  # Winter
                restrictions.append("Période hivernale - éviter les traitements par temps froid")
            elif month in [6, 7, 8]:  # Summer
                restrictions.append("Période estivale - éviter les traitements par forte chaleur")

        elif practice_type == "fertilization":
            if month in [11, 12, 1, 2]:  # Winter period
                restrictions.append("Période d'interdiction d'épandage (15 nov - 15 janv)")

        return restrictions
