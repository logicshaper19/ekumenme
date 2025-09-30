"""
Enhanced Get Safety Guidelines Tool - DATABASE INTEGRATED

Provides comprehensive safety guidelines for agricultural products and practices
with REAL DATABASE INTEGRATION from EPHY (risk phrases, safety intervals, ZNT).

Features:
- Pydantic schemas for type safety
- Redis + memory caching (2h TTL)
- EPHY database integration for product safety data
- Risk phrases (H-phrases, P-phrases)
- Safety intervals (DAR, re-entry)
- ZNT requirements
- Emergency procedures
- Legal references
- Structured error handling
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import ValidationError
from langchain.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.cache import redis_cache
from app.core.database import AsyncSessionLocal
from app.services.configuration_service import ConfigurationService
from app.services.unified_regulatory_service import UnifiedRegulatoryService
from app.models.ephy import Produit, PhraseRisque, ProduitPhraseRisque, UsageProduit
from app.tools.schemas.safety_schemas import (
    SafetyGuidelinesInput,
    SafetyGuidelinesOutput,
    SafetyGuideline,
    SafetyEquipment,
    EmergencyProcedure,
    RiskPhrase,
    ProductSafetyInfo,
    SafetyLevel,
    SafetyPriority,
    ProductType,
    PracticeType
)

logger = logging.getLogger(__name__)


class EnhancedSafetyGuidelinesService:
    """Service for getting safety guidelines with DATABASE INTEGRATION"""
    
    def __init__(self):
        self.config_service = ConfigurationService()
        self.regulatory_service = UnifiedRegulatoryService()
    
    @redis_cache(ttl=7200, model_class=SafetyGuidelinesOutput, category="regulatory")
    async def get_safety_guidelines(
        self,
        product_type: Optional[str] = None,
        practice_type: Optional[str] = None,
        safety_level: str = "standard",
        amm_code: Optional[str] = None,
        product_name: Optional[str] = None,
        include_risk_phrases: bool = True,
        include_emergency_procedures: bool = True
    ) -> SafetyGuidelinesOutput:
        """
        Get comprehensive safety guidelines with database integration.
        
        Args:
            product_type: Type of agricultural product
            practice_type: Type of agricultural practice
            safety_level: Required safety level (basic, standard, high, critical)
            amm_code: AMM code for specific product lookup
            product_name: Product name for database search
            include_risk_phrases: Include risk phrases from EPHY database
            include_emergency_procedures: Include emergency procedures
            
        Returns:
            SafetyGuidelinesOutput with comprehensive safety information
        """
        try:
            # Validate input (Pydantic will handle enum conversion)
            input_data = SafetyGuidelinesInput(
                product_type=product_type,
                practice_type=practice_type,
                safety_level=safety_level,
                amm_code=amm_code,
                product_name=product_name,
                include_risk_phrases=include_risk_phrases,
                include_emergency_procedures=include_emergency_procedures
            )
            
            # Get configuration-based guidelines
            config_guidelines = self._get_config_guidelines(
                input_data.product_type,
                input_data.practice_type,
                input_data.safety_level
            )
            
            # Get database-based product safety info
            product_safety_info = None
            database_guidelines = []
            
            if (amm_code or product_name) and include_risk_phrases:
                async with AsyncSessionLocal() as db:
                    product_safety_info = await self._get_product_safety_from_db(
                        db, amm_code, product_name
                    )
                    
                    if product_safety_info:
                        # Create guideline from database data
                        db_guideline = self._create_guideline_from_product_safety(
                            product_safety_info,
                            input_data.safety_level
                        )
                        database_guidelines.append(db_guideline)
            
            # Combine guidelines
            all_guidelines = config_guidelines + database_guidelines
            
            # Calculate safety priority
            safety_priority = self._calculate_safety_priority(
                all_guidelines,
                product_safety_info
            )
            
            # Generate recommendations
            safety_recommendations = self._generate_safety_recommendations(
                all_guidelines,
                product_safety_info
            )
            
            # Generate critical warnings
            critical_warnings = self._generate_critical_warnings(
                all_guidelines,
                product_safety_info
            )
            
            # Get emergency contacts
            emergency_contacts = self._get_emergency_contacts()
            
            # Count total risk phrases
            total_risk_phrases = 0
            if product_safety_info:
                total_risk_phrases = len(product_safety_info.risk_phrases)
            
            # Determine data source
            data_source = "configuration"
            if product_safety_info and config_guidelines:
                data_source = "hybrid"
            elif product_safety_info:
                data_source = "ephy_database"
            
            return SafetyGuidelinesOutput(
                success=True,
                product_type=product_type,
                practice_type=practice_type,
                safety_level=safety_level,
                safety_guidelines=all_guidelines,
                product_safety_info=product_safety_info,
                safety_priority=safety_priority,
                total_guidelines=len(all_guidelines),
                total_risk_phrases=total_risk_phrases,
                safety_recommendations=safety_recommendations,
                critical_warnings=critical_warnings,
                emergency_contacts=emergency_contacts,
                data_source=data_source
            )
            
        except ValidationError as e:
            logger.error(f"Validation error in safety guidelines: {e}")
            return SafetyGuidelinesOutput(
                success=False,
                safety_level=safety_level,
                safety_priority=SafetyPriority.LOW,
                total_guidelines=0,
                error=f"Erreur de validation: {str(e)}",
                error_type="validation",
                data_source="none"
            )
        except Exception as e:
            logger.error(f"Error getting safety guidelines: {e}", exc_info=True)
            return SafetyGuidelinesOutput(
                success=False,
                safety_level=safety_level,
                safety_priority=SafetyPriority.LOW,
                total_guidelines=0,
                error=f"Erreur lors de la récupération des consignes de sécurité: {str(e)}",
                error_type="unknown",
                data_source="none"
            )
    
    async def _get_product_safety_from_db(
        self,
        db: AsyncSession,
        amm_code: Optional[str],
        product_name: Optional[str]
    ) -> Optional[ProductSafetyInfo]:
        """Get product safety information from EPHY database"""
        try:
            # Build query
            query = select(Produit)
            
            if amm_code:
                query = query.where(Produit.numero_amm == amm_code)
            elif product_name:
                query = query.where(Produit.nom_produit.ilike(f"%{product_name}%"))
            else:
                return None
            
            result = await db.execute(query)
            product = result.scalars().first()
            
            if not product:
                logger.info(f"Product not found: amm={amm_code}, name={product_name}")
                return None
            
            # Get risk phrases
            risk_phrases_query = select(PhraseRisque).join(
                ProduitPhraseRisque
            ).where(
                ProduitPhraseRisque.numero_amm == product.numero_amm
            )
            
            risk_phrases_result = await db.execute(risk_phrases_query)
            risk_phrases_db = risk_phrases_result.scalars().all()
            
            risk_phrases = [
                RiskPhrase(
                    code=phrase.code_phrase,
                    description=phrase.libelle_phrase,
                    category="hazard" if phrase.code_phrase.startswith("H") else "precautionary"
                )
                for phrase in risk_phrases_db
            ]
            
            # Get usage info for safety intervals and ZNT
            usage_query = select(UsageProduit).where(UsageProduit.numero_amm == product.numero_amm).limit(1)
            usage_result = await db.execute(usage_query)
            usage = usage_result.scalars().first()
            
            safety_interval_days = None
            znt_requirements = None
            
            if usage:
                safety_interval_days = usage.delai_avant_recolte_jour
                znt_requirements = {
                    "aquatic_m": float(usage.znt_aquatique_m) if usage.znt_aquatique_m else None,
                    "arthropods_m": float(usage.znt_arthropodes_non_cibles_m) if usage.znt_arthropodes_non_cibles_m else None,
                    "plants_m": float(usage.znt_plantes_non_cibles_m) if usage.znt_plantes_non_cibles_m else None
                }
            
            return ProductSafetyInfo(
                amm_code=product.numero_amm,
                product_name=product.nom_produit,
                risk_phrases=risk_phrases,
                safety_interval_days=safety_interval_days,
                znt_requirements=znt_requirements,
                authorized_mentions=product.mentions_autorisees,
                usage_restrictions=product.restrictions_usage_libelle
            )
            
        except Exception as e:
            logger.error(f"Error getting product safety from database: {e}")
            return None
    
    def _get_config_guidelines(
        self,
        product_type: Optional[str],  # Already a string from Pydantic
        practice_type: Optional[str],  # Already a string from Pydantic
        safety_level: str  # Already a string from Pydantic
    ) -> List[SafetyGuideline]:
        """Get safety guidelines from configuration"""
        guidelines = []

        # Get safety database from configuration
        safety_config = self._get_safety_config()

        # Get product-specific guidelines
        if product_type and product_type in safety_config:
            guideline_data = safety_config[product_type].get(safety_level)
            if guideline_data:
                guidelines.append(self._create_guideline_from_config(guideline_data))

        # Get practice-specific guidelines
        if practice_type and practice_type in safety_config:
            guideline_data = safety_config[practice_type].get(safety_level)
            if guideline_data:
                guidelines.append(self._create_guideline_from_config(guideline_data))

        return guidelines

    def _create_guideline_from_config(self, config_data: Dict[str, Any]) -> SafetyGuideline:
        """Create SafetyGuideline from configuration data"""
        # Convert equipment list to SafetyEquipment objects
        equipment = [
            SafetyEquipment(
                equipment_type=eq,
                is_mandatory=True,
                specification=None
            )
            for eq in config_data.get("required_equipment", [])
        ]

        # Convert emergency procedures to EmergencyProcedure objects
        emergency_procedures = [
            EmergencyProcedure(
                situation="Urgence générale",
                procedure=proc,
                priority=SafetyPriority.HIGH,
                contact_info=None
            )
            for proc in config_data.get("emergency_procedures", [])
        ]

        return SafetyGuideline(
            guideline_type=config_data.get("guideline_type", "general"),
            description=config_data.get("description", ""),
            safety_level=SafetyLevel(config_data.get("safety_level", "standard")),
            required_equipment=equipment,
            safety_measures=config_data.get("safety_measures", []),
            emergency_procedures=emergency_procedures,
            source="configuration"
        )

    def _create_guideline_from_product_safety(
        self,
        product_safety: ProductSafetyInfo,
        safety_level: str  # Already a string from Pydantic
    ) -> SafetyGuideline:
        """Create SafetyGuideline from product safety database info"""
        # Determine required equipment based on risk phrases
        equipment = self._determine_equipment_from_risk_phrases(product_safety.risk_phrases)

        # Generate safety measures from risk phrases
        safety_measures = self._generate_measures_from_risk_phrases(product_safety.risk_phrases)

        # Add ZNT-based measures
        if product_safety.znt_requirements:
            for znt_type, distance in product_safety.znt_requirements.items():
                if distance and distance > 0:
                    safety_measures.append(
                        f"Respecter ZNT {znt_type}: {distance}m"
                    )

        # Add safety interval measure
        if product_safety.safety_interval_days:
            safety_measures.append(
                f"Délai avant récolte (DAR): {product_safety.safety_interval_days} jours"
            )

        # Generate emergency procedures from P-phrases
        emergency_procedures = self._generate_emergency_procedures_from_risk_phrases(
            product_safety.risk_phrases
        )

        # Add legal references
        legal_references = [
            "Règlement (CE) n° 1272/2008 (CLP)",
            "Code du travail - Articles R4412-1 à R4412-160",
            "Arrêté du 4 mai 2017 relatif aux ZNT"
        ]

        return SafetyGuideline(
            guideline_type=f"product_{product_safety.amm_code}",
            description=f"Consignes de sécurité pour {product_safety.product_name}",
            safety_level=safety_level,
            required_equipment=equipment,
            safety_measures=safety_measures,
            emergency_procedures=emergency_procedures,
            risk_phrases=product_safety.risk_phrases,
            legal_references=legal_references,
            source="ephy_database"
        )

    def _determine_equipment_from_risk_phrases(
        self,
        risk_phrases: List[RiskPhrase]
    ) -> List[SafetyEquipment]:
        """Determine required equipment based on risk phrases"""
        equipment_set = set()

        for phrase in risk_phrases:
            code = phrase.code

            # Hazard phrases that require specific equipment
            if code in ["H301", "H302", "H304", "H311", "H312", "H314", "H315", "H317", "H318", "H319"]:
                equipment_set.add("gants")
                equipment_set.add("lunettes")

            if code in ["H330", "H331", "H332", "H334", "H335"]:
                equipment_set.add("masque_respiratoire")

            if code in ["H310", "H311", "H312", "H314"]:
                equipment_set.add("combinaison")
                equipment_set.add("bottes")

            # Precautionary phrases
            if code in ["P280", "P281"]:
                equipment_set.add("EPI_complet")

        # Convert to SafetyEquipment objects
        equipment = [
            SafetyEquipment(
                equipment_type=eq,
                is_mandatory=True,
                specification="Conforme aux normes EN"
            )
            for eq in sorted(equipment_set)
        ]

        return equipment if equipment else [
            SafetyEquipment(
                equipment_type="EPI_standard",
                is_mandatory=True,
                specification="Gants, lunettes, masque minimum"
            )
        ]

    def _generate_measures_from_risk_phrases(
        self,
        risk_phrases: List[RiskPhrase]
    ) -> List[str]:
        """Generate safety measures from risk phrases"""
        measures = set()

        for phrase in risk_phrases:
            # Add the precautionary statement directly
            if phrase.category == "precautionary":
                measures.add(phrase.description)

        return list(measures) if measures else ["Suivre les instructions de l'étiquette"]

    def _generate_emergency_procedures_from_risk_phrases(
        self,
        risk_phrases: List[RiskPhrase]
    ) -> List[EmergencyProcedure]:
        """Generate emergency procedures from risk phrases"""
        procedures = []

        # Map risk codes to emergency procedures
        emergency_map = {
            "H301": EmergencyProcedure(
                situation="Ingestion",
                procedure="Appeler immédiatement un centre antipoison. Ne PAS faire vomir.",
                priority=SafetyPriority.CRITICAL,
                contact_info="Centre Antipoison: 01 40 05 48 48"
            ),
            "H311": EmergencyProcedure(
                situation="Contact cutané",
                procedure="Rincer abondamment à l'eau pendant au moins 15 minutes. Retirer vêtements contaminés.",
                priority=SafetyPriority.HIGH,
                contact_info="SAMU: 15"
            ),
            "H314": EmergencyProcedure(
                situation="Contact avec les yeux",
                procedure="Rincer immédiatement et abondamment à l'eau pendant au moins 15 minutes. Consulter un médecin.",
                priority=SafetyPriority.CRITICAL,
                contact_info="SAMU: 15"
            ),
            "H330": EmergencyProcedure(
                situation="Inhalation",
                procedure="Transporter la personne à l'air frais. En cas de difficultés respiratoires, appeler le SAMU.",
                priority=SafetyPriority.CRITICAL,
                contact_info="SAMU: 15"
            )
        }

        for phrase in risk_phrases:
            if phrase.code in emergency_map:
                procedures.append(emergency_map[phrase.code])

        # Add default emergency procedure
        if not procedures:
            procedures.append(
                EmergencyProcedure(
                    situation="Urgence générale",
                    procedure="En cas d'accident, appeler le centre antipoison ou le SAMU",
                    priority=SafetyPriority.HIGH,
                    contact_info="Centre Antipoison: 01 40 05 48 48, SAMU: 15"
                )
            )

        return procedures

    def _calculate_safety_priority(
        self,
        guidelines: List[SafetyGuideline],
        product_safety: Optional[ProductSafetyInfo]
    ) -> SafetyPriority:
        """Calculate overall safety priority"""
        # Check for critical risk phrases
        if product_safety:
            for phrase in product_safety.risk_phrases:
                if phrase.code in ["H300", "H301", "H310", "H311", "H330", "H331", "H370", "H372"]:
                    return SafetyPriority.CRITICAL

        # Check safety levels in guidelines
        safety_levels = [g.safety_level for g in guidelines]

        if SafetyLevel.CRITICAL in safety_levels:
            return SafetyPriority.CRITICAL
        elif SafetyLevel.HIGH in safety_levels:
            return SafetyPriority.HIGH
        elif SafetyLevel.STANDARD in safety_levels:
            return SafetyPriority.MODERATE
        else:
            return SafetyPriority.LOW

    def _generate_safety_recommendations(
        self,
        guidelines: List[SafetyGuideline],
        product_safety: Optional[ProductSafetyInfo]
    ) -> List[str]:
        """Generate safety recommendations"""
        recommendations = []

        # Add equipment recommendations
        all_equipment = set()
        for guideline in guidelines:
            for eq in guideline.required_equipment:
                all_equipment.add(eq.equipment_type)

        if all_equipment:
            recommendations.append(
                f"Équipement de protection requis: {', '.join(sorted(all_equipment))}"
            )

        # Add product-specific recommendations
        if product_safety:
            if product_safety.safety_interval_days:
                recommendations.append(
                    f"Respecter le délai avant récolte de {product_safety.safety_interval_days} jours"
                )

            if product_safety.znt_requirements:
                max_znt = max(
                    [v for v in product_safety.znt_requirements.values() if v],
                    default=0
                )
                if max_znt > 0:
                    recommendations.append(
                        f"Respecter une zone non traitée (ZNT) d'au moins {max_znt}m"
                    )

            if product_safety.usage_restrictions:
                recommendations.append(
                    f"Restrictions d'usage: {product_safety.usage_restrictions}"
                )

        # Add general recommendations
        recommendations.extend([
            "Lire attentivement l'étiquette avant utilisation",
            "Respecter les doses prescrites",
            "Ne pas manger, boire ou fumer pendant l'utilisation",
            "Se laver soigneusement après manipulation"
        ])

        return recommendations

    def _generate_critical_warnings(
        self,
        guidelines: List[SafetyGuideline],
        product_safety: Optional[ProductSafetyInfo]
    ) -> List[str]:
        """Generate critical safety warnings"""
        warnings = []

        if product_safety:
            # Check for critical hazard phrases
            critical_phrases = {
                "H300": "MORTEL en cas d'ingestion",
                "H310": "MORTEL par contact cutané",
                "H330": "MORTEL par inhalation",
                "H370": "Risque avéré d'effets graves pour les organes",
                "H372": "Risque avéré d'effets graves pour les organes en cas d'exposition prolongée"
            }

            for phrase in product_safety.risk_phrases:
                if phrase.code in critical_phrases:
                    warnings.append(f"⚠️ DANGER: {critical_phrases[phrase.code]}")

        return warnings

    def _get_emergency_contacts(self) -> Dict[str, str]:
        """Get emergency contact information"""
        return {
            "centre_antipoison": "01 40 05 48 48 (Paris)",
            "samu": "15",
            "pompiers": "18",
            "numero_urgence_europeen": "112",
            "phyt_attitude": "0 800 887 887 (numéro vert)",
            "msa_sante_travail": "Contacter votre MSA locale"
        }

    def _get_safety_config(self) -> Dict[str, Any]:
        """Get safety configuration database"""
        return {
            "herbicide": {
                "basic": {
                    "guideline_type": "herbicide_basic",
                    "description": "Consignes de sécurité de base pour les herbicides",
                    "safety_level": "basic",
                    "required_equipment": ["gants", "lunettes", "masque"],
                    "safety_measures": [
                        "Lire l'étiquette avant utilisation",
                        "Respecter les doses prescrites",
                        "Éviter tout contact avec la peau et les yeux"
                    ],
                    "emergency_procedures": [
                        "Rincer abondamment à l'eau en cas de contact",
                        "Appeler le centre antipoison en cas d'ingestion"
                    ]
                },
                "standard": {
                    "guideline_type": "herbicide_standard",
                    "description": "Consignes de sécurité standard pour les herbicides",
                    "safety_level": "standard",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison"],
                    "safety_measures": [
                        "Lire l'étiquette avant utilisation",
                        "Respecter les doses prescrites",
                        "Éviter tout contact avec la peau et les yeux",
                        "Travailler dans un endroit bien ventilé"
                    ],
                    "emergency_procedures": [
                        "Rincer abondamment à l'eau en cas de contact",
                        "Appeler le centre antipoison en cas d'ingestion",
                        "Évacuer la zone en cas de déversement important"
                    ]
                },
                "high": {
                    "guideline_type": "herbicide_high",
                    "description": "Consignes de sécurité élevées pour les herbicides",
                    "safety_level": "high",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison", "bottes"],
                    "safety_measures": [
                        "Lire l'étiquette avant utilisation",
                        "Respecter strictement les doses prescrites",
                        "Éviter tout contact avec la peau et les yeux",
                        "Travailler dans un endroit bien ventilé",
                        "Isoler la zone de traitement"
                    ],
                    "emergency_procedures": [
                        "Rincer abondamment à l'eau en cas de contact",
                        "Appeler immédiatement le centre antipoison en cas d'ingestion",
                        "Évacuer la zone en cas de déversement",
                        "Alerter les secours si nécessaire"
                    ]
                }
            },
            "insecticide": {
                "basic": {
                    "guideline_type": "insecticide_basic",
                    "description": "Consignes de sécurité de base pour les insecticides",
                    "safety_level": "basic",
                    "required_equipment": ["gants", "lunettes", "masque"],
                    "safety_measures": [
                        "Lire l'étiquette avant utilisation",
                        "Respecter les doses prescrites",
                        "Éviter tout contact avec la peau et les yeux"
                    ],
                    "emergency_procedures": [
                        "Rincer abondamment à l'eau en cas de contact",
                        "Appeler le centre antipoison en cas d'ingestion"
                    ]
                },
                "standard": {
                    "guideline_type": "insecticide_standard",
                    "description": "Consignes de sécurité standard pour les insecticides",
                    "safety_level": "standard",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison"],
                    "safety_measures": [
                        "Lire l'étiquette avant utilisation",
                        "Respecter les doses prescrites",
                        "Éviter tout contact avec la peau et les yeux",
                        "Travailler dans un endroit bien ventilé"
                    ],
                    "emergency_procedures": [
                        "Rincer abondamment à l'eau en cas de contact",
                        "Appeler le centre antipoison en cas d'ingestion",
                        "Évacuer la zone en cas de déversement important"
                    ]
                },
                "high": {
                    "guideline_type": "insecticide_high",
                    "description": "Consignes de sécurité élevées pour les insecticides",
                    "safety_level": "high",
                    "required_equipment": ["gants", "lunettes", "masque", "combinaison", "bottes"],
                    "safety_measures": [
                        "Lire l'étiquette avant utilisation",
                        "Respecter strictement les doses prescrites",
                        "Éviter tout contact avec la peau et les yeux",
                        "Travailler dans un endroit bien ventilé",
                        "Isoler la zone de traitement"
                    ],
                    "emergency_procedures": [
                        "Rincer abondamment à l'eau en cas de contact",
                        "Appeler immédiatement le centre antipoison en cas d'ingestion",
                        "Évacuer la zone en cas de déversement",
                        "Alerter les secours si nécessaire"
                    ]
                }
            },
            "spraying": {
                "basic": {
                    "guideline_type": "spraying_basic",
                    "description": "Consignes de sécurité de base pour la pulvérisation",
                    "safety_level": "basic",
                    "required_equipment": ["pulvérisateur", "gants", "lunettes"],
                    "safety_measures": [
                        "Vérifier l'équipement avant utilisation",
                        "Respecter les doses prescrites",
                        "Éviter la dérive du produit"
                    ],
                    "emergency_procedures": [
                        "Arrêter la pulvérisation en cas de problème",
                        "Rincer l'équipement après utilisation"
                    ]
                },
                "standard": {
                    "guideline_type": "spraying_standard",
                    "description": "Consignes de sécurité standard pour la pulvérisation",
                    "safety_level": "standard",
                    "required_equipment": ["pulvérisateur", "gants", "lunettes", "masque", "combinaison"],
                    "safety_measures": [
                        "Vérifier l'équipement avant utilisation",
                        "Respecter les doses prescrites",
                        "Éviter la dérive du produit",
                        "Travailler dans de bonnes conditions météo"
                    ],
                    "emergency_procedures": [
                        "Arrêter la pulvérisation en cas de problème",
                        "Rincer l'équipement après utilisation",
                        "Évacuer la zone en cas de déversement"
                    ]
                }
            }
        }


# Initialize service
_safety_service = EnhancedSafetyGuidelinesService()


# Async wrapper function
async def get_safety_guidelines_async(
    product_type: Optional[str] = None,
    practice_type: Optional[str] = None,
    safety_level: str = "standard",
    amm_code: Optional[str] = None,
    product_name: Optional[str] = None,
    include_risk_phrases: bool = True,
    include_emergency_procedures: bool = True
) -> str:
    """
    Get comprehensive safety guidelines with DATABASE INTEGRATION.

    Args:
        product_type: Type of agricultural product (herbicide, insecticide, fongicide, etc.)
        practice_type: Type of agricultural practice (spraying, fertilization, etc.)
        safety_level: Required safety level (basic, standard, high, critical)
        amm_code: AMM code for specific product lookup in EPHY database
        product_name: Product name for database search
        include_risk_phrases: Include risk phrases (H-phrases, P-phrases) from EPHY database
        include_emergency_procedures: Include emergency procedures

    Returns:
        JSON string with comprehensive safety guidelines including:
        - Configuration-based guidelines
        - EPHY database product safety data
        - Risk phrases (H-phrases, P-phrases)
        - Safety intervals (DAR, re-entry)
        - ZNT requirements
        - Emergency procedures with contact info
        - Legal references
    """
    result = await _safety_service.get_safety_guidelines(
        product_type=product_type,
        practice_type=practice_type,
        safety_level=safety_level,
        amm_code=amm_code,
        product_name=product_name,
        include_risk_phrases=include_risk_phrases,
        include_emergency_procedures=include_emergency_procedures
    )
    return result.model_dump_json()


# Create LangChain tool
get_safety_guidelines_tool = StructuredTool.from_function(
    coroutine=get_safety_guidelines_async,
    name="get_safety_guidelines",
    description=(
        "Récupère les consignes de sécurité complètes pour les produits et pratiques agricoles "
        "avec INTÉGRATION BASE DE DONNÉES EPHY. "
        "Fournit les phrases de risque (H-phrases, P-phrases), les équipements de protection requis, "
        "les délais avant récolte (DAR), les zones non traitées (ZNT), les procédures d'urgence, "
        "et les références légales. "
        "Combine les données de configuration avec les informations réglementaires de la base EPHY. "
        "Inclut les contacts d'urgence (centre antipoison, SAMU, pompiers)."
    ),
    handle_validation_error=False
)

