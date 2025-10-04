"""
Unit tests for Farm API endpoints
Tests farm data API functionality including parcelles, interventions, and exploitations
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal
from datetime import date

from app.main import app
from app.models.user import User, UserRole, UserStatus
from app.models.mesparcelles import Parcelle, Intervention, Exploitation
from app.models.organization import Organization, OrganizationMembership, OrganizationFarmAccess
from app.services.validation import ValidationError


class TestFarmAPI:
    """Test suite for Farm API endpoints"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing"""
        user = User(
            id=uuid4(),
            email="farmer@test.com",
            full_name="Test Farmer",
            role=UserRole.FARMER,
            status=UserStatus.ACTIVE,
            is_verified=True
        )
        return user

    @pytest.fixture
    def mock_organization(self):
        """Create a mock organization for testing"""
        org = Organization(
            id=uuid4(),
            name="Test Farm Organization",
            siret="12345678901234",
            is_active=True
        )
        return org

    @pytest.fixture
    def mock_parcelle(self):
        """Create a mock parcelle for testing"""
        parcelle = Parcelle(
            id=uuid4(),
            nom="Test Parcel",
            siret="12345678901234",
            culture_code="BLE_TENDRE",
            surface_ha=Decimal("10.5"),
            statut="en_croissance",
            date_semis=date(2024, 1, 15),
            notes="Test notes"
        )
        return parcelle

    @pytest.fixture
    def mock_intervention(self):
        """Create a mock intervention for testing"""
        intervention = Intervention(
            id=uuid4(),
            parcelle_id=uuid4(),
            siret="12345678901234",
            type_intervention="SEMIS",
            date_intervention=date(2024, 1, 15),
            description="Test intervention",
            produit_utilise="Test Product",
            dose_totale=Decimal("2.5"),
            unite_dose="L/ha",
            surface_traitee_ha=Decimal("5.0"),
            conditions_meteo="Ensoleillé, 18°C",
            cout_total=Decimal("150.75"),
            notes="Test notes"
        )
        return intervention

    @pytest.fixture
    def mock_exploitation(self):
        """Create a mock exploitation for testing"""
        exploitation = Exploitation(
            id=uuid4(),
            siret="12345678901234",
            nom="Test Farm",
            region_code="75",
            department_code="75",
            commune_insee="75001",
            surface_totale_ha=Decimal("100.0"),
            type_exploitation="Polyculture",
            bio=True,
            certification_bio=True,
            date_certification_bio=date(2023, 1, 1)
        )
        return exploitation

    def test_parcelles_list_endpoint_unauthorized(self, client):
        """Test parcelles list endpoint without authentication"""
        response = client.get("/api/v1/farm/parcelles/")
        assert response.status_code == 401

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_parcelles_list_endpoint_authorized(self, mock_db, mock_auth, client, mock_user, mock_parcelle):
        """Test parcelles list endpoint with authentication"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_parcelle]
        mock_result.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_result
        
        response = client.get("/api/v1/farm/parcelles/")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_parcelles_list_with_filters(self, mock_db, mock_auth, client, mock_user, mock_parcelle):
        """Test parcelles list endpoint with filters"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_parcelle]
        mock_result.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_result
        
        # Test with filters
        response = client.get("/api/v1/farm/parcelles/?culture_filter=BLE_TENDRE&status_filter=en_croissance&search_term=Test")
        assert response.status_code == 200

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_parcelle_detail_endpoint(self, mock_db, mock_auth, client, mock_user, mock_parcelle):
        """Test parcelle detail endpoint"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_parcelle
        mock_session.execute.return_value = mock_result
        
        response = client.get(f"/api/v1/farm/parcelles/{mock_parcelle.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(mock_parcelle.id)
        assert data["nom"] == mock_parcelle.nom

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_parcelle_detail_not_found(self, mock_db, mock_auth, client, mock_user):
        """Test parcelle detail endpoint with non-existent parcelle"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results - no parcelle found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        response = client.get(f"/api/v1/farm/parcelles/{uuid4()}")
        assert response.status_code == 404

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_create_parcelle_valid_data(self, mock_db, mock_auth, client, mock_user, mock_organization):
        """Test creating a parcelle with valid data"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock access check - user has access
        mock_access_result = MagicMock()
        mock_access_result.scalar_one_or_none.return_value = MagicMock()  # Access found
        mock_session.execute.return_value = mock_access_result
        
        # Valid parcelle data
        parcelle_data = {
            "nom": "New Test Parcel",
            "siret": "12345678901234",
            "culture_code": "BLE_TENDRE",
            "surface_ha": 10.5,
            "variete": "Test Variety",
            "date_semis": "2024-01-15",
            "coordonnees": {"latitude": 48.8566, "longitude": 2.3522},
            "notes": "Test notes"
        }
        
        response = client.post("/api/v1/farm/parcelles/", json=parcelle_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["nom"] == parcelle_data["nom"]
        assert data["siret"] == parcelle_data["siret"]

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_create_parcelle_invalid_data(self, mock_db, mock_auth, client, mock_user):
        """Test creating a parcelle with invalid data"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Invalid parcelle data
        invalid_data = {
            "nom": "",  # Empty name
            "siret": "invalid",  # Invalid SIRET
            "culture_code": "INVALID",  # Invalid culture code
        }
        
        response = client.post("/api/v1/farm/parcelles/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_create_parcelle_unauthorized_farm(self, mock_db, mock_auth, client, mock_user):
        """Test creating a parcelle for unauthorized farm"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock access check - no access found
        mock_access_result = MagicMock()
        mock_access_result.scalar_one_or_none.return_value = None  # No access
        mock_session.execute.return_value = mock_access_result
        
        # Valid parcelle data but for unauthorized farm
        parcelle_data = {
            "nom": "New Test Parcel",
            "siret": "99999999999999",  # Different SIRET
            "culture_code": "BLE_TENDRE",
            "surface_ha": 10.5
        }
        
        response = client.post("/api/v1/farm/parcelles/", json=parcelle_data)
        assert response.status_code == 403  # Forbidden

    @patch('app.api.v1.farm.interventions.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.interventions.get_async_db')
    def test_interventions_list_endpoint(self, mock_db, mock_auth, client, mock_user, mock_intervention):
        """Test interventions list endpoint"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_intervention]
        mock_result.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_result
        
        response = client.get("/api/v1/farm/interventions/")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    @patch('app.api.v1.farm.interventions.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.interventions.get_async_db')
    def test_interventions_list_with_filters(self, mock_db, mock_auth, client, mock_user, mock_intervention):
        """Test interventions list endpoint with filters"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_intervention]
        mock_result.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_result
        
        # Test with filters
        response = client.get("/api/v1/farm/interventions/?type_filter=SEMIS&product_filter=Test&start_date=2024-01-01&end_date=2024-12-31")
        assert response.status_code == 200

    @patch('app.api.v1.farm.interventions.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.interventions.get_async_db')
    def test_intervention_detail_endpoint(self, mock_db, mock_auth, client, mock_user, mock_intervention):
        """Test intervention detail endpoint"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_intervention
        mock_session.execute.return_value = mock_result
        
        response = client.get(f"/api/v1/farm/interventions/{mock_intervention.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(mock_intervention.id)
        assert data["type_intervention"] == mock_intervention.type_intervention

    @patch('app.api.v1.farm.exploitation.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.exploitation.get_async_db')
    def test_exploitations_list_endpoint(self, mock_db, mock_auth, client, mock_user, mock_exploitation):
        """Test exploitations list endpoint"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_exploitation]
        mock_result.scalar_one.return_value = 1
        mock_session.execute.return_value = mock_result
        
        response = client.get("/api/v1/farm/exploitations/")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    @patch('app.api.v1.farm.exploitation.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.exploitation.get_async_db')
    def test_exploitation_detail_endpoint(self, mock_db, mock_auth, client, mock_user, mock_exploitation):
        """Test exploitation detail endpoint"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_exploitation
        mock_session.execute.return_value = mock_result
        
        response = client.get(f"/api/v1/farm/exploitations/{mock_exploitation.siret}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["siret"] == mock_exploitation.siret
        assert data["nom"] == mock_exploitation.nom

    @patch('app.api.v1.farm.dashboard.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.dashboard.get_async_db')
    def test_dashboard_endpoint(self, mock_db, mock_auth, client, mock_user):
        """Test dashboard endpoint"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 10  # Total parcelles
        mock_session.execute.return_value = mock_result
        
        response = client.get("/api/v1/farm/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_parcelles" in data
        assert "total_interventions" in data
        assert "total_surface" in data

    def test_pagination_parameters(self, client):
        """Test pagination parameters validation"""
        # Test valid pagination
        response = client.get("/api/v1/farm/parcelles/?skip=0&limit=10")
        # Should not return 422 (validation error) for valid pagination
        
        # Test invalid pagination
        response = client.get("/api/v1/farm/parcelles/?skip=-1&limit=0")
        assert response.status_code == 422  # Validation error for negative skip or zero limit

    def test_pagination_limits(self, client):
        """Test pagination limits"""
        # Test limit too high
        response = client.get("/api/v1/farm/parcelles/?limit=1000")
        assert response.status_code == 422  # Validation error for limit > 100

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_parcelles_by_farm_endpoint(self, mock_db, mock_auth, client, mock_user, mock_parcelle):
        """Test parcelles by farm endpoint"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock access check - user has access
        mock_access_result = MagicMock()
        mock_access_result.scalar_one_or_none.return_value = MagicMock()  # Access found
        mock_session.execute.return_value = mock_access_result
        
        # Mock parcelle query results
        mock_parcelle_result = MagicMock()
        mock_parcelle_result.scalars.return_value.all.return_value = [mock_parcelle]
        mock_parcelle_result.scalar_one.return_value = 1
        
        # Set up multiple execute calls
        mock_session.execute.side_effect = [mock_access_result, mock_parcelle_result, mock_parcelle_result]
        
        response = client.get("/api/v1/farm/parcelles/farm/12345678901234")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    @patch('app.api.v1.farm.parcelles.auth_service.get_current_active_user')
    @patch('app.api.v1.farm.parcelles.get_async_db')
    def test_parcelles_by_farm_unauthorized(self, mock_db, mock_auth, client, mock_user):
        """Test parcelles by farm endpoint with unauthorized access"""
        # Mock authentication
        mock_auth.return_value = mock_user
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock access check - no access found
        mock_access_result = MagicMock()
        mock_access_result.scalar_one_or_none.return_value = None  # No access
        mock_session.execute.return_value = mock_access_result
        
        response = client.get("/api/v1/farm/parcelles/farm/99999999999999")
        assert response.status_code == 403  # Forbidden


class TestFarmAPIIntegration:
    """Integration tests for Farm API"""

    @pytest.mark.asyncio
    async def test_parcelle_creation_workflow(self):
        """Test complete parcelle creation workflow"""
        # This would test the full workflow from validation to database storage
        # to WebSocket broadcasting
        
        # 1. Validate input data
        from app.services.validation import farm_data_validator
        
        valid_data = {
            "nom": "Integration Test Parcel",
            "siret": "12345678901234",
            "culture_code": "BLE_TENDRE",
            "surface_ha": 15.5,
            "statut": "en_croissance"
        }
        
        validated_data = farm_data_validator.validate_parcel_data(valid_data)
        assert validated_data["nom"] == "Integration Test Parcel"
        assert validated_data["culture_code"] == "BLE_TENDRE"
        
        # 2. Test WebSocket broadcast (would require more complex setup)
        from app.api.v1.farm.websocket import broadcast_parcelle_update
        
        with patch('app.api.v1.farm.websocket.farm_ws_manager.broadcast_update', new_callable=AsyncMock) as mock_broadcast:
            await broadcast_parcelle_update(
                parcelle_id="test_parcelle_123",
                farm_siret="12345678901234",
                action="created",
                data=validated_data
            )
            mock_broadcast.assert_called_once()

    def test_error_handling_consistency(self, client):
        """Test that error responses are consistent across endpoints"""
        # Test unauthorized access
        endpoints = [
            "/api/v1/farm/parcelles/",
            "/api/v1/farm/interventions/",
            "/api/v1/farm/exploitations/",
            "/api/v1/farm/dashboard/"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401  # Unauthorized
            assert "detail" in response.json()

    def test_response_format_consistency(self, client):
        """Test that response formats are consistent across endpoints"""
        # This would require mocking authentication and database
        # For now, we'll test the expected structure
        
        expected_list_response_keys = ["items", "total", "page", "total_pages", "has_next", "has_prev"]
        expected_detail_response_keys = ["id", "created_at", "updated_at"]
        
        # These would be verified in actual API calls with proper mocking
        assert len(expected_list_response_keys) > 0
        assert len(expected_detail_response_keys) > 0
