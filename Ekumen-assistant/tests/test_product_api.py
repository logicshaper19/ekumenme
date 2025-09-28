"""
Unit tests for product API endpoints
Tests the French agricultural product database API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.main import app
from app.models.user import User, UserRole, UserStatus
from app.models.product import (
    Product, SubstanceActive, ProductSubstance, Usage,
    ProductType, AuthorizationStatus, UsageStatus
)


class TestProductAPI:
    """Test Product API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client, test_user_token):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {test_user_token}"}
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, client, auth_headers, db_session: AsyncSession):
        """Test successful product search"""
        # Create test product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        
        # Test search
        response = client.get(
            "/api/v1/products/search",
            params={"search_term": "Test Product"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["numero_amm"] == "1234567"
        assert data[0]["nom_produit"] == "Test Product"
        assert data[0]["type_produit"] == "PPP"
        assert data[0]["etat_autorisation"] == "AUTORISE"
    
    @pytest.mark.asyncio
    async def test_search_products_by_type(self, client, auth_headers, db_session: AsyncSession):
        """Test product search by type"""
        # Create test products
        ppp_product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1111111",
            nom_produit="PPP Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        mfsc_product = Product(
            type_produit=ProductType.MFSC,
            numero_amm="2222222",
            nom_produit="MFSC Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add_all([ppp_product, mfsc_product])
        await db_session.commit()
        
        # Test search by PPP type
        response = client.get(
            "/api/v1/products/search",
            params={"product_type": "PPP"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type_produit"] == "PPP"
        assert data[0]["numero_amm"] == "1111111"
    
    @pytest.mark.asyncio
    async def test_search_products_invalid_type(self, client, auth_headers):
        """Test product search with invalid type"""
        response = client.get(
            "/api/v1/products/search",
            params={"product_type": "INVALID"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Type de produit invalide" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_product_by_amm_success(self, client, auth_headers, db_session: AsyncSession):
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
        
        # Test get by AMM
        response = client.get(
            "/api/v1/products/amm/1234567",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["numero_amm"] == "1234567"
        assert data["nom_produit"] == "Test Product"
        assert data["type_produit"] == "PPP"
    
    @pytest.mark.asyncio
    async def test_get_product_by_amm_not_found(self, client, auth_headers):
        """Test getting non-existent product by AMM"""
        response = client.get(
            "/api/v1/products/amm/9999999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "non trouvé" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_product_by_name_success(self, client, auth_headers, db_session: AsyncSession):
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
        
        # Test get by name
        response = client.get(
            "/api/v1/products/name/Test%20Product",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["nom_produit"] == "Test Product Name"
        assert data["numero_amm"] == "1234567"
    
    @pytest.mark.asyncio
    async def test_get_products_by_substance(self, client, auth_headers, db_session: AsyncSession):
        """Test getting products by substance"""
        # Create test data
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
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
        
        # Test get by substance
        response = client.get(
            "/api/v1/products/substance/Test%20Substance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["numero_amm"] == "1234567"
        assert data[0]["nom_produit"] == "Test Product"
    
    @pytest.mark.asyncio
    async def test_get_products_for_crop(self, client, auth_headers, db_session: AsyncSession):
        """Test getting products for a specific crop"""
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
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test get for crop
        response = client.get(
            "/api/v1/products/crop/Blé",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["numero_amm"] == "1234567"
        assert data[0]["nom_produit"] == "Test Product"
    
    @pytest.mark.asyncio
    async def test_validate_product_usage_valid(self, client, auth_headers, db_session: AsyncSession):
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
        response = client.post(
            "/api/v1/products/validate-usage",
            json={
                "numero_amm": "1234567",
                "crop_name": "Blé",
                "dose": 1.5,
                "unit": "L/ha"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["error"] is None
        assert data["usage"] is not None
    
    @pytest.mark.asyncio
    async def test_validate_product_usage_invalid_dose(self, client, auth_headers, db_session: AsyncSession):
        """Test validating product usage with invalid dose"""
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
        
        # Test validation with invalid dose
        response = client.post(
            "/api/v1/products/validate-usage",
            json={
                "numero_amm": "1234567",
                "crop_name": "Blé",
                "dose": 3.0,  # Too high
                "unit": "L/ha"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Dose trop élevée" in data["error"]
        assert data["usage"] is None
    
    @pytest.mark.asyncio
    async def test_validate_product_usage_invalid_request(self, client, auth_headers):
        """Test validating product usage with invalid request"""
        response = client.post(
            "/api/v1/products/validate-usage",
            json={
                "numero_amm": "",  # Empty AMM
                "crop_name": "Blé",
                "dose": 1.5,
                "unit": "L/ha"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_check_product_compatibility(self, client, auth_headers, db_session: AsyncSession):
        """Test checking product compatibility"""
        # Create test products
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
        
        # Test compatibility check
        response = client.post(
            "/api/v1/products/check-compatibility",
            json={
                "product1_amm": "1111111",
                "product2_amm": "2222222"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "compatible" in data
        assert "conflict_reason" in data
    
    @pytest.mark.asyncio
    async def test_check_product_compatibility_same_product(self, client, auth_headers):
        """Test checking compatibility with same product"""
        response = client.post(
            "/api/v1/products/check-compatibility",
            json={
                "product1_amm": "1111111",
                "product2_amm": "1111111"  # Same product
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_get_product_statistics(self, client, auth_headers, db_session: AsyncSession):
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
        
        # Test get statistics
        response = client.get(
            "/api/v1/products/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 3
        assert data["authorized_products"] == 2
        assert data["mfsc_products"] == 1
        assert data["ppp_products"] == 1
        assert data["total_substances"] == 1
        assert data["total_usages"] == 1
        assert data["authorization_rate"] == 66.67
    
    @pytest.mark.asyncio
    async def test_get_crop_statistics(self, client, auth_headers, db_session: AsyncSession):
        """Test getting crop statistics"""
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
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test get crop statistics
        response = client.get(
            "/api/v1/products/statistics/crops",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["crop"] == "Blé"
        assert data[0]["nb_products"] == 1
        assert data[0]["nb_usages"] == 1
    
    @pytest.mark.asyncio
    async def test_get_substance_statistics(self, client, auth_headers, db_session: AsyncSession):
        """Test getting substance statistics"""
        # Create test data
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
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
            fonction="Insecticide"
        )
        
        db_session.add(product_substance)
        await db_session.commit()
        
        # Test get substance statistics
        response = client.get(
            "/api/v1/products/statistics/substances",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["fonction"] == "Insecticide"
        assert data[0]["nom_substance"] == "Test Substance"
        assert data[0]["nb_products"] == 1
    
    @pytest.mark.asyncio
    async def test_get_products_with_buffer_zones(self, client, auth_headers, db_session: AsyncSession):
        """Test getting products with buffer zones"""
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
        
        # Create usage with buffer zone
        usage = Usage(
            product_id=product.id,
            type_culture_libelle="Blé",
            znt_aquatique_m=5,
            etat_usage=UsageStatus.AUTORISE
        )
        
        db_session.add(usage)
        await db_session.commit()
        
        # Test get products with buffer zones
        response = client.get(
            "/api/v1/products/buffer-zones",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["numero_amm"] == "1234567"
        assert data[0]["nom_produit"] == "Test Product"
    
    @pytest.mark.asyncio
    async def test_get_products_by_holder(self, client, auth_headers, db_session: AsyncSession):
        """Test getting products by holder"""
        # Create test product
        product = Product(
            type_produit=ProductType.PPP,
            numero_amm="1234567",
            nom_produit="Test Product",
            titulaire="Test Company",
            etat_autorisation=AuthorizationStatus.AUTORISE
        )
        
        db_session.add(product)
        await db_session.commit()
        
        # Test get by holder
        response = client.get(
            "/api/v1/products/holder/Test%20Company",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["numero_amm"] == "1234567"
        assert data[0]["titulaire"] == "Test Company"
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to product endpoints"""
        response = client.get("/api/v1/products/search")
        assert response.status_code == 401
    
    def test_invalid_token(self, client):
        """Test access with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/products/search", headers=headers)
        assert response.status_code == 401
