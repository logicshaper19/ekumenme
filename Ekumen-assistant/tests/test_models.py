"""
Tests for database models
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User, UserRole, UserStatus, UserSession, UserActivity


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
