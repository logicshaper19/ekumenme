"""
Tests for database models
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User, UserRole, UserStatus, UserSession, UserActivity
from app.models.farm import Farm, FarmType, FarmStatus, Parcel, CropRotation


class TestUserModel:
    """Test User model"""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    def test_create_user(self, db_session):
        """Test creating a user"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            role=UserRole.FARMER,
            status=UserStatus.ACTIVE,
            language_preference="fr"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.FARMER
        assert user.status == UserStatus.ACTIVE
        assert user.language_preference == "fr"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_superuser is False
    
    def test_user_properties(self, db_session):
        """Test user property methods"""
        user = User(
            email="farmer@example.com",
            hashed_password="hashed_password",
            role=UserRole.FARMER
        )
        
        assert user.is_farmer is True
        assert user.is_advisor is False
        assert user.is_inspector is False
        assert user.is_admin is False
        
        user.role = UserRole.ADVISOR
        assert user.is_farmer is False
        assert user.is_advisor is True
    
    def test_user_display_name(self, db_session):
        """Test user display name property"""
        # Test with full name
        user1 = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Jean Dupont"
        )
        assert user1.display_name == "Jean Dupont"
        
        # Test without full name
        user2 = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        assert user2.display_name == "test"
    
    def test_user_session(self, db_session):
        """Test UserSession model"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        session = UserSession(
            user_id=user.id,
            session_token="test_token",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_type="desktop",
            expires_at=datetime.now(timezone.utc)
        )
        
        db_session.add(session)
        db_session.commit()
        
        assert session.id is not None
        assert session.user_id == user.id
        assert session.session_token == "test_token"
        assert session.is_active is True
    
    def test_user_activity(self, db_session):
        """Test UserActivity model"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        activity = UserActivity(
            user_id=user.id,
            activity_type="login",
            activity_description="User logged in",
            ip_address="192.168.1.1",
            endpoint="/api/v1/auth/login",
            method="POST"
        )
        
        db_session.add(activity)
        db_session.commit()
        
        assert activity.id is not None
        assert activity.user_id == user.id
        assert activity.activity_type == "login"
        assert activity.activity_description == "User logged in"


class TestFarmModel:
    """Test Farm model"""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def user(self, db_session):
        """Create a test user"""
        user = User(
            email="farmer@example.com",
            hashed_password="hashed_password",
            role=UserRole.FARMER
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    def test_create_farm(self, db_session, user):
        """Test creating a farm"""
        farm = Farm(
            siret="12345678901234",
            farm_name="Test Farm",
            owner_user_id=user.id,
            region_code="75",
            farm_type=FarmType.INDIVIDUAL,
            status=FarmStatus.ACTIVE,
            total_area_ha=100.5,
            organic_certified=True
        )
        
        db_session.add(farm)
        db_session.commit()
        
        assert farm.siret == "12345678901234"
        assert farm.farm_name == "Test Farm"
        assert farm.owner_user_id == user.id
        assert farm.region_code == "75"
        assert farm.farm_type == FarmType.INDIVIDUAL
        assert farm.status == FarmStatus.ACTIVE
        assert farm.total_area_ha == 100.5
        assert farm.organic_certified is True
    
    def test_farm_properties(self, db_session, user):
        """Test farm property methods"""
        farm = Farm(
            siret="12345678901234",
            farm_name="Test Farm",
            owner_user_id=user.id,
            region_code="75",
            organic_certified=True
        )
        
        assert farm.is_organic is True
        assert farm.display_name == "Test Farm"
        
        farm.organic_certified = False
        assert farm.is_organic is False
    
    def test_farm_display_name_fallback(self, db_session, user):
        """Test farm display name fallback"""
        farm = Farm(
            siret="12345678901234",
            owner_user_id=user.id,
            region_code="75"
        )
        
        assert farm.display_name == "Exploitation 12345678901234"
    
    def test_parcel_creation(self, db_session, user):
        """Test creating a parcel"""
        farm = Farm(
            siret="12345678901234",
            farm_name="Test Farm",
            owner_user_id=user.id,
            region_code="75"
        )
        db_session.add(farm)
        db_session.commit()
        
        parcel = Parcel(
            farm_siret=farm.siret,
            parcel_number="P001",
            area_ha=5.25,
            current_crop="blé",
            soil_type="loam"
        )
        
        db_session.add(parcel)
        db_session.commit()
        
        assert parcel.id is not None
        assert parcel.farm_siret == farm.siret
        assert parcel.parcel_number == "P001"
        assert parcel.area_ha == 5.25
        assert parcel.current_crop == "blé"
        assert parcel.soil_type == "loam"
    
    def test_parcel_display_name(self, db_session, user):
        """Test parcel display name"""
        farm = Farm(
            siret="12345678901234",
            farm_name="Test Farm",
            owner_user_id=user.id,
            region_code="75"
        )
        db_session.add(farm)
        db_session.commit()
        
        parcel = Parcel(
            farm_siret=farm.siret,
            parcel_number="P001",
            area_ha=5.25
        )
        
        assert parcel.display_name == "Parcelle P001 (5.25 ha)"
    
    def test_crop_rotation(self, db_session, user):
        """Test crop rotation creation"""
        farm = Farm(
            siret="12345678901234",
            farm_name="Test Farm",
            owner_user_id=user.id,
            region_code="75"
        )
        db_session.add(farm)
        db_session.commit()
        
        parcel = Parcel(
            farm_siret=farm.siret,
            parcel_number="P001",
            area_ha=5.25
        )
        db_session.add(parcel)
        db_session.commit()
        
        rotation = CropRotation(
            parcel_id=parcel.id,
            crop_name="blé",
            crop_variety="blé tendre",
            crop_family="cereals",
            planting_date=datetime.now(timezone.utc),
            season="autumn",
            yield_quantity=45.5,
            yield_unit="quintaux",
            yield_per_hectare=8.67
        )
        
        db_session.add(rotation)
        db_session.commit()
        
        assert rotation.id is not None
        assert rotation.parcel_id == parcel.id
        assert rotation.crop_name == "blé"
        assert rotation.crop_variety == "blé tendre"
        assert rotation.crop_family == "cereals"
        assert rotation.season == "autumn"
        assert rotation.yield_quantity == 45.5
        assert rotation.yield_unit == "quintaux"
        assert rotation.yield_per_hectare == 8.67
