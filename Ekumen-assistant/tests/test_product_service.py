"""
Unit tests for product service
Tests the French agricultural product database service operations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.services.product_service import ProductService
from app.models.product import (
    Product, SubstanceActive, ProductSubstance, Usage,
    ProductType, AuthorizationStatus, UsageStatus
)


class TestProductService:
    """Test ProductService"""
    
    @pytest.fixture
    def product_service(self):
        """Create ProductService instance"""
        return ProductService()
    
    @pytest.mark.asyncio
    async def test_get_product_by_amm(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting product by AMM number"""
        # Create test product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        
        # Test getting product
        result = await product_service.get_product_by_amm(db_session, "1234567")
        
        assert result is not None
        assert result.numero_amm == "1234567"
        assert result.nom_produit == "Test Product"
        assert result.type_produit == ProductType.PPP
    
    @pytest.mark.asyncio
    async def test_get_product_by_amm_not_found(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting non-existent product by AMM"""
        result = await product_service.get_product_by_amm(db_session, "9999999")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_product_by_name(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting product by name"""
        # Create test product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product Name",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        
        # Test getting product
        result = await product_service.get_product_by_name(db_session, "Test Product")
        
        assert result is not None
        assert result.nom_produit == "Test Product Name"
        assert result.numero_amm == "1234567"
    
    @pytest.mark.asyncio
    async def test_get_products_by_substance(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting products by active substance"""
        # Create test data
        product1 = Product(
            type_produit=ProductType.PPP,
            numero_amm="1111111",
            nom_produit="Product 1",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        product2 = Product(
            type_produit=ProductType.PPP,
            numero_amm="2222222",
            nom_produit="Product 2",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        substance = SubstanceActive(
            nom_substance="Test Substance",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add_all([product1, product2, substance])
        await db_session.commit()
        await db_session.refresh(product1)
        await db_session.refresh(product2)
        await db_session.refresh(substance)
        
        # Create relationships
        ps1 = ProductSubstance(
            product_id=product1.id,
            substance_id=substance.id,
            concentration_value=Decimal("250.0"),
            concentration_unit="g/L",
            fonction="Insecticide"
        )
        
        ps2 = ProductSubstance(
            product_id=product2.id,
            substance_id=substance.id,
            concentration_value=Decimal("300.0"),
            concentration_unit="g/L",
            fonction="Fongicide"
        )
        
        db_session.add_all([ps1, ps2])
        await db_session.commit()
        
        # Test getting products by substance
        results = await product_service.get_products_by_substance(
            db_session, "Test Substance", limit=10
        )
        
        assert len(results) == 2
        assert any(p.numero_amm == "1111111" for p in results)
        assert any(p.numero_amm == "2222222" for p in results)
    
    @pytest.mark.asyncio
    async def test_get_products_for_crop(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting products for a specific crop"""
        # Create test data
        product1 = Product(
            type_produit=ProductType.PPP,
            numero_amm="1111111",
            nom_produit="Product 1",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        product2 = Product(
            type_produit=ProductType.PPP,
            numero_amm="2222222",
            nom_produit="Product 2",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add_all([product1, product2])
        await db_session.commit()
        await db_session.refresh(product1)
        await db_session.refresh(product2)
        
        # Create usages
        usage1 = Usage(
            product_id=product1.id,
            type_culture_libelle="Blé",
            etat_usage=UsageStatus.AUTORISE
        )
        
        usage2 = Usage(
            product_id=product2.id,
            type_culture_libelle="Maïs",
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add_all([usage1, usage2])
        await db_session.commit()
        
        # Test getting products for crop
        results = await product_service.get_products_for_crop(
            db_session, "Blé", limit=10
        )
        
        assert len(results) == 1
        assert results[0].numero_amm == "1111111"
        assert results[0].nom_produit == "Product 1"
    
    @pytest.mark.asyncio
    async def test_get_product_usage_for_crop(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting product usage for a specific crop"""
        # Create test data
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
            type_culture_libelle="Blé",
            dose_retenue=Decimal("1.5"),
            dose_unite="L/ha",
            nombre_max_application=2,
            delai_avant_recolte_jour=30,
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test getting usage for crop
        results = await product_service.get_product_usage_for_crop(
            db_session, "1234567", "Blé"
        )
        
        assert len(results) == 1
        assert results[0].type_culture_libelle == "Blé"
        assert results[0].dose_retenue == Decimal("1.5")
        assert results[0].dose_unite == "L/ha"
        assert results[0].nombre_max_application == 2
        assert results[0].delai_avant_recolte_jour == 30
    
    @pytest.mark.asyncio
    async def test_validate_product_usage_valid(self, db_session: AsyncSession, product_service: ProductService):
        """Test validating valid product usage"""
        # Create test data
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
            type_culture_libelle="Blé",
            dose_min_par_apport=Decimal("1.0"),
            dose_max_par_apport=Decimal("2.0"),
            dose_unite="L/ha",
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test validation
        result = await product_service.validate_product_usage(
            db_session, "1234567", "Blé", 1.5, "L/ha"
        )
        
        assert result["valid"] is True
        assert result["error"] is None
        assert result["usage"] is not None
        assert result["usage"]["dose_retenue"] == usage.dose_retenue
        assert result["usage"]["dose_unite"] == "L/ha"
    
    @pytest.mark.asyncio
    async def test_validate_product_usage_dose_too_low(self, db_session: AsyncSession, product_service: ProductService):
        """Test validating product usage with dose too low"""
        # Create test data
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
            type_culture_libelle="Blé",
            dose_min_par_apport=Decimal("1.0"),
            dose_max_par_apport=Decimal("2.0"),
            dose_unite="L/ha",
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test validation with dose too low
        result = await product_service.validate_product_usage(
            db_session, "1234567", "Blé", 0.5, "L/ha"
        )
        
        assert result["valid"] is False
        assert "Dose trop faible" in result["error"]
        assert result["usage"] is None
    
    @pytest.mark.asyncio
    async def test_validate_product_usage_dose_too_high(self, db_session: AsyncSession, product_service: ProductService):
        """Test validating product usage with dose too high"""
        # Create test data
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
            type_culture_libelle="Blé",
            dose_min_par_apport=Decimal("1.0"),
            dose_max_par_apport=Decimal("2.0"),
            dose_unite="L/ha",
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test validation with dose too high
        result = await product_service.validate_product_usage(
            db_session, "1234567", "Blé", 3.0, "L/ha"
        )
        
        assert result["valid"] is False
        assert "Dose trop élevée" in result["error"]
        assert result["usage"] is None
    
    @pytest.mark.asyncio
    async def test_validate_product_usage_wrong_unit(self, db_session: AsyncSession, product_service: ProductService):
        """Test validating product usage with wrong unit"""
        # Create test data
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
            type_culture_libelle="Blé",
            dose_unite="L/ha",
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test validation with wrong unit
        result = await product_service.validate_product_usage(
            db_session, "1234567", "Blé", 1.5, "kg/ha"
        )
        
        assert result["valid"] is False
        assert "Unité de dose non autorisée" in result["error"]
        assert result["usage"] is None
    
    @pytest.mark.asyncio
    async def test_validate_product_usage_no_usage_found(self, db_session: AsyncSession, product_service: ProductService):
        """Test validating product usage when no usage found"""
        # Create test data
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        
        # Test validation with no usage
        result = await product_service.validate_product_usage(
            db_session, "1234567", "Blé", 1.5, "L/ha"
        )
        
        assert result["valid"] is False
        assert "Aucun usage autorisé trouvé" in result["error"]
        assert result["usage"] is None
    
    @pytest.mark.asyncio
    async def test_get_products_with_buffer_zones(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting products with buffer zones"""
        # Create test data
        product1 = Product(
            type_produit=ProductType.PPP,
            numero_amm="1111111",
            nom_produit="Product with ZNT",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        product2 = Product(
            type_produit=ProductType.PPP,
            numero_amm="2222222",
            nom_produit="Product without ZNT",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add_all([product1, product2])
        await db_session.commit()
        await db_session.refresh(product1)
        await db_session.refresh(product2)
        
        # Create usages
        usage1 = Usage(
            product_id=product1.id,
            type_culture_libelle="Blé",
            znt_aquatique_m=5,
            etat_usage=UsageStatus.AUTORISE
        )
        
        usage2 = Usage(
            product_id=product2.id,
            type_culture_libelle="Maïs",
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add_all([usage1, usage2])
        await db_session.commit()
        
        # Test getting products with buffer zones
        results = await product_service.get_products_with_buffer_zones(
            db_session, limit=10
        )
        
        assert len(results) == 1
        assert results[0].numero_amm == "1111111"
        assert results[0].nom_produit == "Product with ZNT"
    
    @pytest.mark.asyncio
    async def test_get_products_by_holder(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting products by holder company"""
        # Create test data
        product1 = Product(
            type_produit=ProductType.PPP,
            numero_amm="1111111",
            nom_produit="Product 1",
            titulaire="Test Company",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        product2 = Product(
            type_produit=ProductType.PPP,
            numero_amm="2222222",
            nom_produit="Product 2",
            titulaire="Other Company",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add_all([product1, product2])
        await db_session.commit()
        
        # Test getting products by holder
        results = await product_service.get_products_by_holder(
            db_session, "Test Company", limit=10
        )
        
        assert len(results) == 1
        assert results[0].numero_amm == "1111111"
        assert results[0].titulaire == "Test Company"
    
    @pytest.mark.asyncio
    async def test_get_product_statistics(self, db_session: AsyncSession, product_service: ProductService):
        """Test getting product statistics"""
        # Create test data
        product1 = Product(
            type_produit=ProductType.PPP,
            numero_amm="1111111",
            nom_produit="PPP Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        product2 = Product(
            type_produit=ProductType.MFSC,
            numero_amm="2222222",
            nom_produit="MFSC Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        product3 = Product(
            type_produit=ProductType.PPP,
            numero_amm="3333333",
            nom_produit="Retired Product",
            etat_autorisation=AuthorizationStatus.RETIRE
        )
        
        substance = SubstanceActive(
            nom_substance="Test Substance",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add_all([product1, product2, product3, substance])
        await db_session.commit()
        await db_session.refresh(product1)
        await db_session.refresh(substance)
        
        # Create usage
        usage = Usage(
            product_id=product1.id,
            type_culture_libelle="Blé",
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test getting statistics
        stats = await product_service.get_product_statistics(db_session)
        
        assert stats["total_products"] == 3
        assert stats["authorized_products"] == 2
        assert stats["mfsc_products"] == 1
        assert stats["ppp_products"] == 1
        assert stats["total_substances"] == 1
        assert stats["total_usages"] == 1
        assert stats["authorization_rate"] == 66.67  # 2/3 * 100
