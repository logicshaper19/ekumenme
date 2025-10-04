"""
BBCH Service - Crop Phenology Stage Management

Provides database access and business logic for BBCH growth stages:
- Lookup BBCH stages by crop and code
- Get crop coefficients (Kc) for ET calculations
- Map between BBCH and FAO-56 stages
- Provide stage recommendations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.bbch_stage import BBCHStage

logger = logging.getLogger(__name__)


class BBCHService:
    """Service for BBCH growth stage operations"""
    
    def __init__(self, db: Session):
        """
        Initialize BBCH service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_stage_by_code(
        self,
        crop_type: str,
        bbch_code: int
    ) -> Optional[BBCHStage]:
        """
        Get BBCH stage by crop type and code
        
        Args:
            crop_type: Crop type (e.g., 'blé', 'maïs')
            bbch_code: BBCH code (0-99)
            
        Returns:
            BBCHStage or None if not found
        """
        return self.db.query(BBCHStage).filter(
            BBCHStage.crop_type == crop_type,
            BBCHStage.bbch_code == bbch_code
        ).first()
    
    def get_kc_for_stage(
        self,
        crop_type: str,
        bbch_code: Optional[int] = None,
        fao56_stage: Optional[str] = None
    ) -> float:
        """
        Get crop coefficient (Kc) for specific stage
        
        Priority:
        1. BBCH code (most precise)
        2. FAO-56 stage (average for stage)
        3. Default value (0.8)
        
        Args:
            crop_type: Crop type
            bbch_code: BBCH code (0-99)
            fao56_stage: FAO-56 stage ('initial', 'development', 'mid_season', 'late_season')
            
        Returns:
            Kc value (float)
        """
        # Method 1: Exact BBCH code
        if bbch_code is not None:
            stage = self.get_stage_by_code(crop_type, bbch_code)
            if stage and stage.kc_value:
                logger.debug(f"Kc from BBCH {bbch_code}: {stage.kc_value}")
                return float(stage.kc_value)
            
            # Fallback: Nearest BBCH code with Kc
            nearest = self.db.query(BBCHStage).filter(
                BBCHStage.crop_type == crop_type,
                BBCHStage.kc_value.isnot(None)
            ).order_by(
                func.abs(BBCHStage.bbch_code - bbch_code)
            ).first()
            
            if nearest and nearest.kc_value:
                logger.debug(f"Kc from nearest BBCH {nearest.bbch_code}: {nearest.kc_value}")
                return float(nearest.kc_value)
        
        # Method 2: FAO-56 stage (average)
        if fao56_stage:
            stage_ranges = {
                'initial': (0, 19),
                'development': (20, 49),
                'mid_season': (50, 79),
                'late_season': (80, 99)
            }
            
            min_code, max_code = stage_ranges.get(fao56_stage, (0, 99))
            
            # Get average Kc for this stage
            result = self.db.query(func.avg(BBCHStage.kc_value)).filter(
                BBCHStage.crop_type == crop_type,
                BBCHStage.bbch_code >= min_code,
                BBCHStage.bbch_code <= max_code,
                BBCHStage.kc_value.isnot(None)
            ).scalar()
            
            if result:
                logger.debug(f"Kc from FAO-56 stage {fao56_stage}: {result}")
                return float(result)
        
        # Method 3: Default
        logger.warning(f"No Kc found for {crop_type}, using default 0.8")
        return 0.8
    
    def get_stages_for_crop(
        self,
        crop_type: str,
        principal_stage: Optional[int] = None
    ) -> List[BBCHStage]:
        """
        Get all BBCH stages for a crop
        
        Args:
            crop_type: Crop type
            principal_stage: Optional filter by principal stage (0-9)
            
        Returns:
            List of BBCHStage objects
        """
        query = self.db.query(BBCHStage).filter(
            BBCHStage.crop_type == crop_type
        )
        
        if principal_stage is not None:
            query = query.filter(BBCHStage.principal_stage == principal_stage)
        
        return query.order_by(BBCHStage.bbch_code).all()
    
    def get_critical_stages(
        self,
        crop_type: str
    ) -> List[BBCHStage]:
        """
        Get critical growth stages for a crop
        
        Critical stages are typically:
        - Flowering (60-69)
        - Early fruit development (70-79)
        
        Args:
            crop_type: Crop type
            
        Returns:
            List of critical BBCHStage objects
        """
        return self.db.query(BBCHStage).filter(
            BBCHStage.crop_type == crop_type,
            BBCHStage.bbch_code >= 60,
            BBCHStage.bbch_code <= 79
        ).order_by(BBCHStage.bbch_code).all()
    
    def get_stage_description(
        self,
        crop_type: str,
        bbch_code: int,
        language: str = 'fr'
    ) -> Optional[str]:
        """
        Get description for BBCH stage
        
        Args:
            crop_type: Crop type
            bbch_code: BBCH code
            language: Language ('fr' or 'en')
            
        Returns:
            Description string or None
        """
        stage = self.get_stage_by_code(crop_type, bbch_code)
        if not stage:
            return None
        
        if language == 'en' and stage.description_en:
            return stage.description_en
        
        return stage.description_fr
    
    def recommend_next_stages(
        self,
        crop_type: str,
        current_bbch_code: int,
        days_ahead: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Recommend upcoming growth stages
        
        Args:
            crop_type: Crop type
            current_bbch_code: Current BBCH code
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming stages with estimated dates
        """
        # Get upcoming stages
        upcoming = self.db.query(BBCHStage).filter(
            BBCHStage.crop_type == crop_type,
            BBCHStage.bbch_code > current_bbch_code,
            BBCHStage.typical_duration_days.isnot(None)
        ).order_by(BBCHStage.bbch_code).limit(5).all()
        
        recommendations = []
        cumulative_days = 0
        
        for stage in upcoming:
            cumulative_days += stage.typical_duration_days or 7
            
            if cumulative_days <= days_ahead:
                recommendations.append({
                    'bbch_code': stage.bbch_code,
                    'description': stage.description_fr,
                    'estimated_days': cumulative_days,
                    'kc_value': float(stage.kc_value) if stage.kc_value else None,
                    'is_critical': stage.is_critical_stage,
                    'notes': stage.notes
                })
        
        return recommendations
    
    def get_fao56_stage_range(
        self,
        crop_type: str,
        fao56_stage: str
    ) -> List[int]:
        """
        Get BBCH codes for a FAO-56 stage
        
        Args:
            crop_type: Crop type
            fao56_stage: One of 'initial', 'development', 'mid_season', 'late_season'
            
        Returns:
            List of BBCH codes in that stage
        """
        stage_ranges = {
            'initial': (0, 19),
            'development': (20, 49),
            'mid_season': (50, 79),
            'late_season': (80, 99)
        }
        
        min_code, max_code = stage_ranges.get(fao56_stage, (0, 99))
        
        stages = self.db.query(BBCHStage).filter(
            BBCHStage.crop_type == crop_type,
            BBCHStage.bbch_code >= min_code,
            BBCHStage.bbch_code <= max_code
        ).order_by(BBCHStage.bbch_code).all()
        
        return [stage.bbch_code for stage in stages]
    
    def get_supported_crops(self) -> List[str]:
        """
        Get list of crops with BBCH data
        
        Returns:
            List of crop types
        """
        result = self.db.query(BBCHStage.crop_type).distinct().all()
        return [row[0] for row in result]
    
    def get_stage_statistics(
        self,
        crop_type: str
    ) -> Dict[str, Any]:
        """
        Get statistics about BBCH stages for a crop
        
        Args:
            crop_type: Crop type
            
        Returns:
            Dictionary with statistics
        """
        stages = self.get_stages_for_crop(crop_type)
        
        if not stages:
            return {
                'crop_type': crop_type,
                'total_stages': 0,
                'has_data': False
            }
        
        kc_values = [float(s.kc_value) for s in stages if s.kc_value]
        
        return {
            'crop_type': crop_type,
            'total_stages': len(stages),
            'has_data': True,
            'bbch_range': {
                'min': min(s.bbch_code for s in stages),
                'max': max(s.bbch_code for s in stages)
            },
            'kc_range': {
                'min': min(kc_values) if kc_values else None,
                'max': max(kc_values) if kc_values else None,
                'avg': sum(kc_values) / len(kc_values) if kc_values else None
            },
            'critical_stages_count': len([s for s in stages if s.is_critical_stage]),
            'principal_stages': list(set(s.principal_stage for s in stages))
        }

