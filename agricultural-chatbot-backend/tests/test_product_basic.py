"""
Basic unit tests for product models
Tests the French agricultural product database models with minimal setup
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
from decimal import Decimal

# Create isolated base for testing
TestBase = declarative_base()

# Create test engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
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

# Import only the product models
from app.models.product import (
    Product, SubstanceActive, ProductSubstance, Usage, 
    ProductType, AuthorizationStatus, UsageStatus
)

# Set the base for product models to our test base
Product.__table__.metadata = TestBase.metadata
SubstanceActive.__table__.metadata = TestBase.metadata
ProductSubstance.__table__.metadata = TestBase.metadata
Usage.__table__.metadata = TestBase.metadata


class TestProductBasic:
    """Test Product model with basic setup"""
    
    @pytest.mark.asyncio
    async def test_create_product_basic(self):
        """Test creating a product with basic setup"""
        # Create all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.create_all)
        
        # Create session
        async with TestSessionLocal() as session:
            product = Product(
                type_produit=ProductType.PPP,
                numero_amm="1234567",
                nom_produit="Test Product",
                titulaire="Test Company",
                etat_autorisation=AuthorizationStatus.AUTORISE
            )
            
            session.add(product)
            await session.commit()
            await session.refresh(product)
            
            assert product.id is not None
            assert product.numero_amm == "1234567"
            assert product.nom_produit == "Test Product"
            assert product.type_produit == ProductType.PPP
            assert product.etat_autorisation == AuthorizationStatus.AUTORISE
            assert product.is_authorized is True
        
        # Drop all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.drop_all)
    
    @pytest.mark.asyncio
    async def test_create_substance_basic(self):
        """Test creating a substance with basic setup"""
        # Create all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.create_all)
        
        # Create session
        async with TestSessionLocal() as session:
            substance = SubstanceActive(
                nom_substance="Test Substance",
                numero_cas="123-45-6",
                etat_autorisation=AuthorizationStatus.AUTORISE
            )
            
            session.add(substance)
            await session.commit()
            await session.refresh(substance)
            
            assert substance.id is not None
            assert substance.nom_substance == "Test Substance"
            assert substance.numero_cas == "123-45-6"
            assert substance.etat_autorisation == AuthorizationStatus.AUTORISE
            assert substance.is_authorized is True
        
        # Drop all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.drop_all)
    
    @pytest.mark.asyncio
    async def test_create_usage_basic(self):
        """Test creating a usage with basic setup"""
        # Create all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.create_all)
        
        # Create session
        async with TestSessionLocal() as session:
            # Create product first
            product = Product(
                type_produit=ProductType.PPP,
                numero_amm="1234567",
                nom_produit="Test Product",
                etat_autorisation=AuthorizationStatus.AUTORISE
            )
            
            session.add(product)
            await session.commit()
            await session.refresh(product)
            
            # Create usage
            usage = Usage(
                product_id=product.id,
                identifiant_usage="U001",
                type_culture_libelle="Blé",
                dose_retenue=Decimal("1.5"),
                dose_unite="L/ha",
                nombre_max_application=2,
                delai_avant_recolte_jour=30,
                etat_usage=UsageStatus.AUTORISE,
                znt_aquatique_m=5
            )
            
            session.add(usage)
            await session.commit()
            await session.refresh(usage)
            
            assert usage.id is not None
            assert usage.product_id == product.id
            assert usage.type_culture_libelle == "Blé"
            assert usage.dose_retenue == Decimal("1.5")
            assert usage.dose_unite == "L/ha"
            assert usage.nombre_max_application == 2
            assert usage.delai_avant_recolte_jour == 30
            assert usage.etat_usage == UsageStatus.AUTORISE
            assert usage.is_authorized is True
            assert usage.has_buffer_zones is True
        
        # Drop all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.drop_all)
    
    @pytest.mark.asyncio
    async def test_product_authorization_status_basic(self):
        """Test product authorization status with basic setup"""
        # Create all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.create_all)
        
        # Create session
        async with TestSessionLocal() as session:
            # Authorized product
            authorized_product = Product(
                type_produit=ProductType.PPP,
                numero_amm="1111111",
                nom_produit="Authorized Product",
                etat_autorisation=AuthorizationStatus.AUTORISE
            )
            
            # Retired product
            retired_product = Product(
                type_produit=ProductType.PPP,
                numero_amm="2222222",
                nom_produit="Retired Product",
                etat_autorisation=AuthorizationStatus.RETIRE
            )
            
            session.add_all([authorized_product, retired_product])
            await session.commit()
            
            assert authorized_product.is_authorized is True
            assert retired_product.is_authorized is False
        
        # Drop all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.drop_all)
    
    @pytest.mark.asyncio
    async def test_usage_buffer_zones_basic(self):
        """Test usage buffer zone detection with basic setup"""
        # Create all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.create_all)
        
        # Create session
        async with TestSessionLocal() as session:
            # Create product
            product = Product(
                type_produit=ProductType.PPP,
                numero_amm="1234567",
                nom_produit="Test Product",
                etat_autorisation=AuthorizationStatus.AUTORISE
            )
            
            session.add(product)
            await session.commit()
            await session.refresh(product)
            
            # Usage with buffer zones
            usage_with_znt = Usage(
                product_id=product.id,
                type_culture_libelle="Blé",
                etat_usage=UsageStatus.AUTORISE,
                znt_aquatique_m=5
            )
            
            # Usage without buffer zones
            usage_without_znt = Usage(
                product_id=product.id,
                type_culture_libelle="Maïs",
                etat_usage=UsageStatus.AUTORISE
            )
            
            session.add_all([usage_with_znt, usage_without_znt])
            await session.commit()
            
            assert usage_with_znt.has_buffer_zones is True
            assert usage_without_znt.has_buffer_zones is False
        
        # Drop all tables
        async with test_engine.begin() as conn:
            await conn.run_sync(TestBase.metadata.drop_all)
