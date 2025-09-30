"""
Pytest configuration and fixtures for agricultural chatbot tests
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta

from app.main import app
from app.core.database import Base, get_async_db
from app.core.config import settings
from app.models.user import User, UserRole, UserStatus
from app.services.auth_service import AuthService


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """Create a test database session."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_async_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    auth_service = AuthService()
    
    user = User(
        email="test@example.com",
        hashed_password=auth_service.get_password_hash("testpassword"),
        full_name="Test User",
        role=UserRole.FARMER,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def test_user_token(test_user):
    """Create a JWT token for test user."""
    auth_service = AuthService()
    
    token_data = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture(scope="function")
async def test_admin_user(db_session: AsyncSession):
    """Create a test admin user."""
    auth_service = AuthService()
    
    user = User(
        email="admin@example.com",
        hashed_password=auth_service.get_password_hash("adminpassword"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def test_admin_token(test_admin_user):
    """Create a JWT token for test admin user."""
    auth_service = AuthService()
    
    token_data = {
        "sub": str(test_admin_user.id),
        "email": test_admin_user.email,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture(scope="function")
async def test_advisor_user(db_session: AsyncSession):
    """Create a test advisor user."""
    auth_service = AuthService()
    
    user = User(
        email="advisor@example.com",
        hashed_password=auth_service.get_password_hash("advisorpassword"),
        full_name="Advisor User",
        role=UserRole.ADVISOR,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def test_advisor_token(test_advisor_user):
    """Create a JWT token for test advisor user."""
    auth_service = AuthService()
    
    token_data = {
        "sub": str(test_advisor_user.id),
        "email": test_advisor_user.email,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token





@pytest.fixture(scope="function")
async def test_product(db_session: AsyncSession):
    """Create a test product."""
    from app.models.product import Product, ProductType, AuthorizationStatus
    
    product = Product(
        type_produit=ProductType.PPP,
        numero_amm="1234567",
        nom_produit="Test Product",
        titulaire="Test Company",
        etat_autorisation=AuthorizationStatus.AUTORISE,
        type_commercial="Insecticide",
        gamme_usage="Protection des cultures"
    )
    
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    
    return product


@pytest.fixture(scope="function")
async def test_substance(db_session: AsyncSession):
    """Create a test active substance."""
    from app.models.product import SubstanceActive, AuthorizationStatus
    
    substance = SubstanceActive(
        nom_substance="Test Substance",
        numero_cas="123-45-6",
        etat_autorisation=AuthorizationStatus.AUTORISE
    )
    
    db_session.add(substance)
    await db_session.commit()
    await db_session.refresh(substance)
    
    return substance


@pytest.fixture(scope="function")
async def test_usage(db_session: AsyncSession, test_product):
    """Create a test usage."""
    from app.models.product import Usage, UsageStatus
    from decimal import Decimal
    
    usage = Usage(
        product_id=test_product.id,
        identifiant_usage="U001",
        identifiant_usage_lib_court="Blé - Insecticide",
        type_culture_libelle="Blé",
        dose_min_par_apport=Decimal("1.0"),
        dose_max_par_apport=Decimal("2.0"),
        dose_retenue=Decimal("1.5"),
        dose_unite="L/ha",
        nombre_max_application=2,
        delai_avant_recolte_jour=30,
        intervalle_minimum_applications_jour=14,
        etat_usage=UsageStatus.AUTORISE,
        znt_aquatique_m=5,
        znt_arthropodes_non_cibles_m=20
    )
    
    db_session.add(usage)
    await db_session.commit()
    await db_session.refresh(usage)
    
    return usage


@pytest.fixture(scope="function")
async def test_conversation(db_session: AsyncSession, test_user, test_farm):
    """Create a test conversation."""
    from app.models.conversation import Conversation, AgentType, ConversationStatus
    
    conversation = Conversation(
        user_id=test_user.id,
        farm_siret=test_farm.siret,
        title="Test Conversation",
        agent_type=AgentType.FARM_DATA,
        status=ConversationStatus.ACTIVE
    )
    
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    
    return conversation


@pytest.fixture(scope="function")
async def test_message(db_session: AsyncSession, test_conversation):
    """Create a test message."""
    from app.models.conversation import Message, AgentType
    
    message = Message(
        conversation_id=test_conversation.id,
        content="Test message content",
        sender="user",
        message_type="text"
    )
    
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    
    return message


@pytest.fixture(scope="function")
async def test_journal_entry(db_session: AsyncSession, test_user, test_farm, test_parcel):
    """Create a test journal entry."""
    from app.models.intervention import VoiceJournalEntry, InterventionType, ValidationStatus
    
    entry = VoiceJournalEntry(
        user_id=test_user.id,
        farm_siret=test_farm.siret,
        parcel_id=test_parcel.id,
        content="Test journal entry",
        intervention_type=InterventionType.PEST_CONTROL,
        validation_status=ValidationStatus.PENDING
    )
    
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)
    
    return entry


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
