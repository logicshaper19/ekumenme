"""
Journal service for agricultural chatbot
Handles voice journal entries and intervention validation
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime

from app.models.intervention import VoiceJournalEntry, ValidationStatus, InterventionType
from app.models.user import User
from app.schemas.journal import JournalEntryCreate, ValidationResult


class JournalService:
    """Service for managing voice journal entries and validation"""
    
    async def create_entry(
        self,
        db: AsyncSession,
        user_id: str,
        entry_data: JournalEntryCreate
    ) -> VoiceJournalEntry:
        """Create a new journal entry"""
        entry = VoiceJournalEntry(
            user_id=user_id,
            farm_siret=entry_data.farm_siret,
            parcel_id=entry_data.parcel_id,
            content=entry_data.content,
            intervention_type=entry_data.intervention_type,
            products_used=entry_data.products_used,
            weather_conditions=entry_data.weather_conditions,
            temperature_celsius=entry_data.temperature_celsius,
            humidity_percent=entry_data.humidity_percent,
            wind_speed_kmh=entry_data.wind_speed_kmh,
            notes=entry_data.notes,
            validation_status=ValidationStatus.PENDING
        )
        
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        
        return entry
    
    async def get_entry(
        self,
        db: AsyncSession,
        entry_id: str,
        user_id: str
    ) -> Optional[VoiceJournalEntry]:
        """Get a journal entry by ID"""
        result = await db.execute(
            select(VoiceJournalEntry)
            .where(
                and_(
                    VoiceJournalEntry.id == entry_id,
                    VoiceJournalEntry.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_entries(
        self,
        db: AsyncSession,
        user_id: str,
        farm_siret: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[VoiceJournalEntry]:
        """Get user's journal entries"""
        query = select(VoiceJournalEntry).where(VoiceJournalEntry.user_id == user_id)
        
        if farm_siret:
            query = query.where(VoiceJournalEntry.farm_siret == farm_siret)
        
        query = query.order_by(desc(VoiceJournalEntry.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def validate_entry(
        self,
        db: AsyncSession,
        entry_data: JournalEntryCreate,
        user: User
    ) -> ValidationResult:
        """Validate a journal entry"""
        warnings = []
        compliance_issues = []
        safety_alerts = []
        recommendations = []
        
        # Basic validation
        if not entry_data.content.strip():
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.ERROR,
                error_message="Le contenu de l'entrée ne peut pas être vide"
            )
        
        # Validate intervention type
        if not entry_data.intervention_type:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.ERROR,
                error_message="Le type d'intervention est requis"
            )
        
        # Validate products if provided
        if entry_data.products_used:
            for product in entry_data.products_used:
                if not product.get("product_name"):
                    compliance_issues.append("Nom du produit manquant")
                if not product.get("quantity_used"):
                    compliance_issues.append("Quantité utilisée manquante")
                if not product.get("unit"):
                    compliance_issues.append("Unité de mesure manquante")
        
        # Weather validation
        if entry_data.weather_conditions:
            if entry_data.weather_conditions == "rainy" and entry_data.intervention_type in [
                InterventionType.PEST_CONTROL,
                InterventionType.DISEASE_CONTROL,
                InterventionType.WEED_CONTROL
            ]:
                warnings.append("Traitement par temps pluvieux - vérifiez les conditions d'application")
        
        # Temperature validation
        if entry_data.temperature_celsius:
            if entry_data.temperature_celsius < 5:
                warnings.append("Température très basse - vérifiez l'efficacité des traitements")
            elif entry_data.temperature_celsius > 30:
                warnings.append("Température élevée - risque de volatilisation")
        
        # Wind speed validation
        if entry_data.wind_speed_kmh:
            if entry_data.wind_speed_kmh > 19:  # 19 km/h = 5.3 m/s
                safety_alerts.append("Vent fort détecté - risque de dérive, évitez les traitements")
        
        # Determine validation status
        if compliance_issues or safety_alerts:
            status = ValidationStatus.ERROR
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.VALIDATED
        
        # Generate recommendations
        if entry_data.intervention_type == InterventionType.PEST_CONTROL:
            recommendations.append("Vérifiez le délai avant récolte (DJR) des produits utilisés")
            recommendations.append("Respectez les équipements de protection individuelle (EPI)")
        
        if entry_data.intervention_type == InterventionType.FERTILIZATION:
            recommendations.append("Vérifiez les besoins en azote de la culture")
            recommendations.append("Respectez les périodes d'épandage autorisées")
        
        return ValidationResult(
            is_valid=status in [ValidationStatus.VALIDATED, ValidationStatus.WARNING],
            status=status,
            warnings=warnings if warnings else None,
            compliance_issues=compliance_issues if compliance_issues else None,
            safety_alerts=safety_alerts if safety_alerts else None,
            recommendations=recommendations if recommendations else None
        )
    
    async def validate_existing_entry(
        self,
        db: AsyncSession,
        entry: VoiceJournalEntry,
        user: User
    ) -> ValidationResult:
        """Re-validate an existing journal entry"""
        # Convert existing entry to JournalEntryCreate for validation
        entry_data = JournalEntryCreate(
            content=entry.content,
            intervention_type=entry.intervention_type,
            parcel_id=str(entry.parcel_id) if entry.parcel_id else None,
            products_used=entry.products_used,
            weather_conditions=entry.weather_conditions,
            temperature_celsius=entry.temperature_celsius,
            humidity_percent=entry.humidity_percent,
            wind_speed_kmh=entry.wind_speed_kmh,
            notes=entry.notes
        )
        
        return await self.validate_entry(db, entry_data, user)
    
    async def update_entry(
        self,
        db: AsyncSession,
        entry: VoiceJournalEntry,
        update_data: dict
    ) -> VoiceJournalEntry:
        """Update a journal entry"""
        for field, value in update_data.items():
            if hasattr(entry, field):
                setattr(entry, field, value)
        
        entry.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(entry)
        
        return entry
    
    async def delete_entry(
        self,
        db: AsyncSession,
        entry_id: str,
        user_id: str
    ) -> bool:
        """Delete a journal entry"""
        entry = await self.get_entry(db, entry_id, user_id)
        if entry:
            await db.delete(entry)
            await db.commit()
            return True
        return False
    
    async def get_entries_by_farm(
        self,
        db: AsyncSession,
        farm_siret: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[VoiceJournalEntry]:
        """Get journal entries for a specific farm"""
        result = await db.execute(
            select(VoiceJournalEntry)
            .where(VoiceJournalEntry.farm_siret == farm_siret)
            .order_by(desc(VoiceJournalEntry.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_entries_by_parcel(
        self,
        db: AsyncSession,
        parcel_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[VoiceJournalEntry]:
        """Get journal entries for a specific parcel"""
        result = await db.execute(
            select(VoiceJournalEntry)
            .where(VoiceJournalEntry.parcel_id == parcel_id)
            .order_by(desc(VoiceJournalEntry.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_entries_by_intervention_type(
        self,
        db: AsyncSession,
        intervention_type: InterventionType,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[VoiceJournalEntry]:
        """Get journal entries by intervention type"""
        result = await db.execute(
            select(VoiceJournalEntry)
            .where(
                and_(
                    VoiceJournalEntry.user_id == user_id,
                    VoiceJournalEntry.intervention_type == intervention_type
                )
            )
            .order_by(desc(VoiceJournalEntry.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_validation_statistics(
        self,
        db: AsyncSession,
        user_id: str
    ) -> dict:
        """Get validation statistics for a user"""
        # Total entries
        total_result = await db.execute(
            select(VoiceJournalEntry).where(VoiceJournalEntry.user_id == user_id)
        )
        total_entries = len(total_result.scalars().all())
        
        # Validated entries
        validated_result = await db.execute(
            select(VoiceJournalEntry).where(
                and_(
                    VoiceJournalEntry.user_id == user_id,
                    VoiceJournalEntry.validation_status == ValidationStatus.VALIDATED
                )
            )
        )
        validated_entries = len(validated_result.scalars().all())
        
        # Entries with warnings
        warning_result = await db.execute(
            select(VoiceJournalEntry).where(
                and_(
                    VoiceJournalEntry.user_id == user_id,
                    VoiceJournalEntry.validation_status == ValidationStatus.WARNING
                )
            )
        )
        warning_entries = len(warning_result.scalars().all())
        
        # Entries with errors
        error_result = await db.execute(
            select(VoiceJournalEntry).where(
                and_(
                    VoiceJournalEntry.user_id == user_id,
                    VoiceJournalEntry.validation_status == ValidationStatus.ERROR
                )
            )
        )
        error_entries = len(error_result.scalars().all())
        
        return {
            "total_entries": total_entries,
            "validated_entries": validated_entries,
            "warning_entries": warning_entries,
            "error_entries": error_entries,
            "validation_rate": (validated_entries / total_entries * 100) if total_entries > 0 else 0
        }
