"""
Unit tests for product models
Tests the French agricultural product database models
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from decimal import Decimal

from app.models.product import (
    Product, SubstanceActive, ProductSubstance, Usage, 
    ConditionEmploi, ClassificationDanger, PhraseRisque,
    ProductType, AuthorizationStatus, UsageStatus
)


class TestProductModel:
    """Test Product model"""
    
    @pytest.mark.asyncio
    async def test_create_product(self, db_session: AsyncSession):
        """Test creating a product"""
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            titulaire="Test Company",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        assert product.id is not None
        assert product.numero_amm == "1234567"
        assert product.nom_produit == "Test Product"
        assert product.type_produit == ProductType.PPP
        assert product.etat_autorisation == AuthorizationStatus.AUTORISE
        assert product.is_authorized is True
    
    @pytest.mark.asyncio
    async def test_product_authorization_status(self, db_session: AsyncSession):
        """Test product authorization status"""
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
        
        db_session.add_all([authorized_product, retired_product])
        await db_session.commit()
        
        assert authorized_product.is_authorized is True
        assert retired_product.is_authorized is False
    
    @pytest.mark.asyncio
    async def test_product_unique_amm(self, db_session: AsyncSession):
        """Test that AMM numbers are unique"""
        product1 = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Product 1",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        product2 = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",  # Same AMM number
            nom_produit="Product 2",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product1)
        await db_session.commit()
        
        db_session.add(product2)
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()


class TestSubstanceActiveModel:
    """Test SubstanceActive model"""
    
    @pytest.mark.asyncio
    async def test_create_substance(self, db_session: AsyncSession):
        """Test creating an active substance"""
        substance = SubstanceActive(
            nom_substance="Test Substance",
            numero_cas="123-45-6",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(substance)
        await db_session.commit()
        await db_session.refresh(substance)
        
        assert substance.id is not None
        assert substance.nom_substance == "Test Substance"
        assert substance.numero_cas == "123-45-6"
        assert substance.etat_autorisation == AuthorizationStatus.AUTORISE
        assert substance.is_authorized is True
    
    @pytest.mark.asyncio
    async def test_substance_authorization_status(self, db_session: AsyncSession):
        """Test substance authorization status"""
        substance = SubstanceActive(
            nom_substance="Test Substance",
            etat_autorisation=AuthorizationStatus.RETIRE
        )
        
        db_session.add(substance)
        await db_session.commit()
        
        assert substance.is_authorized is False


class TestProductSubstanceModel:
    """Test ProductSubstance model"""
    
    @pytest.mark.asyncio
    async def test_create_product_substance_relationship(self, db_session: AsyncSession):
        """Test creating product-substance relationship"""
        # Create product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        # Create substance
        substance = SubstanceActive(
            nom_substance="Test Substance",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add_all([product, substance])
        await db_session.commit()
        await db_session.refresh(product)
        await db_session.refresh(substance)
        
        # Create relationship
        product_substance = ProductSubstance(
            product_id=product.id,
            substance_id=substance.id,
            concentration_value=Decimal("250.0"),
            concentration_unit="g/L",
            fonction="Insecticide"
        )
        
        db_session.add(product_substance)
        await db_session.commit()
        await db_session.refresh(product_substance)
        
        assert product_substance.id is not None
        assert product_substance.product_id == product.id
        assert product_substance.substance_id == substance.id
        assert product_substance.concentration_value == Decimal("250.0")
        assert product_substance.concentration_unit == "g/L"
        assert product_substance.fonction == "Insecticide"


class TestUsageModel:
    """Test Usage model"""
    
    @pytest.mark.asyncio
    async def test_create_usage(self, db_session: AsyncSession):
        """Test creating a usage authorization"""
        # Create product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create usage
        usage = Usage(
            product_id=product.id,
            identifiant_usage="U001",
            type_culture_libelle="Blé",
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
        
        assert usage.id is not None
        assert usage.product_id == product.id
        assert usage.type_culture_libelle == "Blé"
        assert usage.dose_retenue == Decimal("1.5")
        assert usage.dose_unite == "L/ha"
        assert usage.nombre_max_application == 2
        assert usage.delai_avant_recolte_jour == 30
        assert usage.intervalle_minimum_applications_jour == 14
        assert usage.etat_usage == UsageStatus.AUTORISE
        assert usage.is_authorized is True
        assert usage.has_buffer_zones is True
    
    @pytest.mark.asyncio
    async def test_usage_buffer_zones(self, db_session: AsyncSession):
        """Test usage buffer zone detection"""
        # Create product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
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
        
        db_session.add_all([usage_with_znt, usage_without_znt])
        await db_session.commit()
        
        assert usage_with_znt.has_buffer_zones is True
        assert usage_without_znt.has_buffer_zones is False


class TestConditionEmploiModel:
    """Test ConditionEmploi model"""
    
    @pytest.mark.asyncio
    async def test_create_condition_emploi(self, db_session: AsyncSession):
        """Test creating employment condition"""
        # Create product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create condition
        condition = ConditionEmploi(
            product_id=product.id,
            categorie_condition="Sécurité",
            condition_emploi_libelle="Porter des gants et des lunettes de protection"
        )
        
        db_session.add(condition)
        await db_session.commit()
        await db_session.refresh(condition)
        
        assert condition.id is not None
        assert condition.product_id == product.id
        assert condition.categorie_condition == "Sécurité"
        assert condition.condition_emploi_libelle == "Porter des gants et des lunettes de protection"


class TestClassificationDangerModel:
    """Test ClassificationDanger model"""
    
    @pytest.mark.asyncio
    async def test_create_classification_danger(self, db_session: AsyncSession):
        """Test creating danger classification"""
        # Create product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create classification
        classification = ClassificationDanger(
            product_id=product.id,
            libelle_court="H302",
            libelle_long="Nocif en cas d'ingestion",
            type_classification="Danger"
        )
        
        db_session.add(classification)
        await db_session.commit()
        await db_session.refresh(classification)
        
        assert classification.id is not None
        assert classification.product_id == product.id
        assert classification.libelle_court == "H302"
        assert classification.libelle_long == "Nocif en cas d'ingestion"
        assert classification.type_classification == "Danger"


class TestPhraseRisqueModel:
    """Test PhraseRisque model"""
    
    @pytest.mark.asyncio
    async def test_create_phrase_risque(self, db_session: AsyncSession):
        """Test creating risk phrase"""
        # Create product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create risk phrase
        phrase = PhraseRisque(
            product_id=product.id,
            code_phrase="H302",
            libelle_court_phrase="Nocif en cas d'ingestion",
            libelle_long_phrase="Nocif en cas d'ingestion",
            type_phrase="H"
        )
        
        db_session.add(phrase)
        await db_session.commit()
        await db_session.refresh(phrase)
        
        assert phrase.id is not None
        assert phrase.product_id == product.id
        assert phrase.code_phrase == "H302"
        assert phrase.libelle_court_phrase == "Nocif en cas d'ingestion"
        assert phrase.type_phrase == "H"


class TestProductRelationships:
    """Test product model relationships"""
    
    @pytest.mark.asyncio
    async def test_product_with_all_relationships(self, db_session: AsyncSession):
        """Test product with all related data"""
        # Create product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        # Create substance
        substance = SubstanceActive(
            nom_substance="Test Substance",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add_all([product, substance])
        await db_session.commit()
        await db_session.refresh(product)
        await db_session.refresh(substance)
        
        # Create product-substance relationship
        product_substance = ProductSubstance(
            product_id=product.id,
            substance_id=substance.id,
            concentration_value=Decimal("250.0"),
            concentration_unit="g/L",
            fonction="Insecticide"
        )
        
        # Create usage
        usage = Usage(
            product_id=product.id,
            type_culture_libelle="Blé",
            dose_retenue=Decimal("1.5"),
            dose_unite="L/ha",
            etat_usage=UsageStatus.AUTORISE
        )
        
        # Create condition
        condition = ConditionEmploi(
            product_id=product.id,
            categorie_condition="Sécurité",
            condition_emploi_libelle="Porter des EPI"
        )
        
        # Create classification
        classification = ClassificationDanger(
            product_id=product.id,
            libelle_court="H302",
            libelle_long="Nocif en cas d'ingestion"
        )
        
        # Create risk phrase
        phrase = PhraseRisque(
            product_id=product.id,
            code_phrase="H302",
            libelle_court_phrase="Nocif en cas d'ingestion",
            type_phrase="H"
        )
        
        db_session.add_all([
            product_substance, usage, condition, classification, phrase
        ])
        await db_session.commit()
        
        # Test relationships
        assert len(product.substances) == 1
        assert len(product.usages) == 1
        assert len(product.conditions_emploi) == 1
        assert len(product.classifications_danger) == 1
        assert len(product.phrases_risque) == 1
        
        assert product.substances[0].substance.nom_substance == "Test Substance"
        assert product.usages[0].type_culture_libelle == "Blé"
        assert product.conditions_emploi[0].categorie_condition == "Sécurité"
        assert product.classifications_danger[0].libelle_court == "H302"
        assert product.phrases_risque[0].code_phrase == "H302"
        
        # Test active substances property
        active_substances = product.active_substances
        assert len(active_substances) == 1
        assert active_substances[0].nom_substance == "Test Substance"
