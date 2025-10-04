"""
Unit tests for Farm Data Validator
Tests comprehensive validation functionality for farm data operations
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4

from app.services.validation import (
    FarmDataValidator,
    ValidationError,
    ParcelCreateRequest,
    InterventionCreateRequest,
    ExploitationCreateRequest
)


class TestFarmDataValidator:
    """Test suite for FarmDataValidator class"""

    def test_validate_siret_valid(self):
        """Test SIRET validation with valid numbers"""
        # Valid SIRET numbers (14 digits with correct checksum)
        valid_sirets = [
            "12345678901234",  # Example valid SIRET
            "12345678901235",  # Another valid SIRET
        ]
        
        for siret in valid_sirets:
            assert FarmDataValidator.validate_siret(siret) is True

    def test_validate_siret_invalid(self):
        """Test SIRET validation with invalid numbers"""
        invalid_sirets = [
            "",  # Empty
            "123",  # Too short
            "123456789012345",  # Too long
            "1234567890123a",  # Contains letters
            "12345678901233",  # Invalid checksum
        ]
        
        for siret in invalid_sirets:
            assert FarmDataValidator.validate_siret(siret) is False

    def test_validate_uuid_valid(self):
        """Test UUID validation with valid UUIDs"""
        valid_uuids = [
            str(uuid4()),
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        ]
        
        for uuid_str in valid_uuids:
            assert FarmDataValidator.validate_uuid(uuid_str) is True

    def test_validate_uuid_invalid(self):
        """Test UUID validation with invalid UUIDs"""
        invalid_uuids = [
            "",  # Empty
            "not-a-uuid",  # Invalid format
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
        ]
        
        for uuid_str in invalid_uuids:
            assert FarmDataValidator.validate_uuid(uuid_str) is False

    def test_validate_date_range_valid(self):
        """Test date range validation with valid ranges"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        same_date = date(2024, 6, 15)
        
        assert FarmDataValidator.validate_date_range(start_date, end_date) is True
        assert FarmDataValidator.validate_date_range(same_date, same_date) is True

    def test_validate_date_range_invalid(self):
        """Test date range validation with invalid ranges"""
        start_date = date(2024, 12, 31)
        end_date = date(2024, 1, 1)
        
        assert FarmDataValidator.validate_date_range(start_date, end_date) is False

    def test_validate_positive_number_valid(self):
        """Test positive number validation with valid numbers"""
        valid_numbers = [0, 1, 100, 3.14, "5", "10.5", Decimal("15.75")]
        
        for num in valid_numbers:
            result = FarmDataValidator.validate_positive_number(num, "test_field")
            assert isinstance(result, Decimal)
            assert result >= 0

    def test_validate_positive_number_invalid(self):
        """Test positive number validation with invalid numbers"""
        # Test negative numbers
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_positive_number(-1, "test_field")
        assert "must be positive" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_positive_number(-3.14, "test_field")
        assert "must be positive" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_positive_number("-5", "test_field")
        assert "must be positive" in str(exc_info.value)
        
        # Test invalid strings
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_positive_number("invalid", "test_field")
        assert "must be a valid number" in str(exc_info.value)

    def test_validate_percentage_valid(self):
        """Test percentage validation with valid percentages"""
        valid_percentages = [0, 50, 100, 25.5, "75", "99.9"]
        
        for pct in valid_percentages:
            result = FarmDataValidator.validate_percentage(pct, "test_percentage")
            assert isinstance(result, Decimal)
            assert 0 <= result <= 100

    def test_validate_percentage_invalid(self):
        """Test percentage validation with invalid percentages"""
        # Test negative percentages
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_percentage(-1, "test_percentage")
        assert "must be positive" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_percentage("-5", "test_percentage")
        assert "must be positive" in str(exc_info.value)
        
        # Test percentages over 100
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_percentage(101, "test_percentage")
        assert "cannot exceed 100%" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_percentage(150, "test_percentage")
        assert "cannot exceed 100%" in str(exc_info.value)
        
        # Test invalid strings
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_percentage("invalid", "test_percentage")
        assert "must be a valid number" in str(exc_info.value)

    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid coordinates"""
        valid_coords = [
            (0, 0),  # Equator, Prime Meridian
            (48.8566, 2.3522),  # Paris
            (-33.9249, 18.4241),  # Cape Town
            (90, 180),  # North Pole, International Date Line
            (-90, -180),  # South Pole, International Date Line
        ]
        
        for lat, lon in valid_coords:
            result_lat, result_lon = FarmDataValidator.validate_coordinates(lat, lon)
            assert result_lat == float(lat)
            assert result_lon == float(lon)

    def test_validate_coordinates_invalid(self):
        """Test coordinate validation with invalid coordinates"""
        invalid_coords = [
            (91, 0),  # Latitude too high
            (-91, 0),  # Latitude too low
            (0, 181),  # Longitude too high
            (0, -181),  # Longitude too low
        ]
        
        for lat, lon in invalid_coords:
            with pytest.raises(ValidationError) as exc_info:
                FarmDataValidator.validate_coordinates(lat, lon)
            
            if lat > 90 or lat < -90:
                assert "Latitude must be between -90 and 90" in str(exc_info.value)
            else:
                assert "Longitude must be between -180 and 180" in str(exc_info.value)

    def test_validate_culture_code_valid(self):
        """Test culture code validation with valid codes"""
        valid_codes = ["BLE_TENDRE", "MAIS", "COLZA", "JACHERE", "VIGNE"]
        
        for code in valid_codes:
            result = FarmDataValidator.validate_culture_code(code)
            assert result == code.upper()

    def test_validate_culture_code_invalid(self):
        """Test culture code validation with invalid codes"""
        # Test empty code
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_culture_code("")
        assert "Culture code is required" in str(exc_info.value)
        
        # Test None
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_culture_code(None)
        assert "Culture code is required" in str(exc_info.value)
        
        # Test invalid code
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_culture_code("INVALID_CROP")
        assert "Invalid culture code" in str(exc_info.value)
        
        # Test lowercase (should be converted to uppercase)
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_culture_code("ble_tendre")
        assert "Invalid culture code" in str(exc_info.value)

    def test_validate_intervention_type_valid(self):
        """Test intervention type validation with valid types"""
        valid_types = ["SEMIS", "TRAITEMENT_PHYTOSANITAIRE", "FERTILISATION", "RECOLTE"]
        
        for int_type in valid_types:
            result = FarmDataValidator.validate_intervention_type(int_type)
            assert result == int_type.upper()

    def test_validate_intervention_type_invalid(self):
        """Test intervention type validation with invalid types"""
        # Test empty type
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_intervention_type("")
        assert "Intervention type is required" in str(exc_info.value)
        
        # Test None
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_intervention_type(None)
        assert "Intervention type is required" in str(exc_info.value)
        
        # Test invalid type
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_intervention_type("INVALID_TYPE")
        assert "Invalid intervention type" in str(exc_info.value)
        
        # Test lowercase (should be converted to uppercase)
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_intervention_type("semis")
        assert "Invalid intervention type" in str(exc_info.value)

    def test_validate_unit_valid(self):
        """Test unit validation with valid units"""
        valid_units = ["L", "L/ha", "kg", "kg/ha", "m3", "ha"]
        
        for unit in valid_units:
            result = FarmDataValidator.validate_unit(unit)
            assert result == unit.lower()

    def test_validate_unit_invalid(self):
        """Test unit validation with invalid units"""
        invalid_units = ["", "INVALID_UNIT", "Liters", None]
        
        for unit in invalid_units:
            with pytest.raises(ValidationError) as exc_info:
                FarmDataValidator.validate_unit(unit)
            
            if not unit:
                assert "Unit is required" in str(exc_info.value)
            else:
                assert "Invalid unit" in str(exc_info.value)

    def test_validate_amm_number_valid(self):
        """Test AMM number validation with valid numbers"""
        valid_amms = ["1234567", "12345678", "2010448", "2050123"]
        
        for amm in valid_amms:
            result = FarmDataValidator.validate_amm_number(amm)
            assert result == amm

    def test_validate_amm_number_invalid(self):
        """Test AMM number validation with invalid numbers"""
        # Test empty AMM
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_amm_number("")
        assert "AMM number is required" in str(exc_info.value)
        
        # Test too short
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_amm_number("123456")
        assert "must be 7-8 digits" in str(exc_info.value)
        
        # Test too long
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_amm_number("123456789")
        assert "must be 7-8 digits" in str(exc_info.value)
        
        # Test with letters
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_amm_number("123456a")
        assert "must be 7-8 digits" in str(exc_info.value)
        
        # Test with dashes
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_amm_number("123-456-7")
        assert "must be 7-8 digits" in str(exc_info.value)

    def test_validate_weather_conditions_valid(self):
        """Test weather conditions validation with valid descriptions"""
        valid_conditions = [
            "Ensoleillé, 18°C, vent 5 km/h",
            "Nuageux, 15°C, vent 3 km/h",
            "Pluie, 12°C, humidité 80%",
            "",  # Empty is allowed
        ]
        
        for conditions in valid_conditions:
            result = FarmDataValidator.validate_weather_conditions(conditions)
            assert result == conditions.strip()

    def test_validate_weather_conditions_invalid(self):
        """Test weather conditions validation with invalid descriptions"""
        invalid_conditions = ["x" * 501]  # Too long
        
        for conditions in invalid_conditions:
            with pytest.raises(ValidationError) as exc_info:
                FarmDataValidator.validate_weather_conditions(conditions)
            
            assert "too long" in str(exc_info.value)

    def test_validate_notes_valid(self):
        """Test notes validation with valid notes"""
        valid_notes = [
            "Standard notes",
            "Notes with special characters: @#$%^&*()",
            "",  # Empty is allowed
            "x" * 1000,  # Maximum length
        ]
        
        for notes in valid_notes:
            result = FarmDataValidator.validate_notes(notes)
            assert result == notes.strip()

    def test_validate_notes_invalid(self):
        """Test notes validation with invalid notes"""
        invalid_notes = ["x" * 1001]  # Too long
        
        for notes in invalid_notes:
            with pytest.raises(ValidationError) as exc_info:
                FarmDataValidator.validate_notes(notes)
            
            assert "too long" in str(exc_info.value)

    def test_validate_parcel_data_valid(self):
        """Test complete parcel data validation with valid data"""
        valid_data = {
            "nom": "Test Parcel",
            "siret": "12345678901234",
            "culture_code": "BLE_TENDRE",
            "surface_ha": 10.5,
            "statut": "en_croissance",
            "date_semis": "2024-01-15",
            "coordonnees": {"latitude": 48.8566, "longitude": 2.3522},
            "notes": "Test notes"
        }
        
        result = FarmDataValidator.validate_parcel_data(valid_data)
        assert result["nom"] == "Test Parcel"
        assert result["culture_code"] == "BLE_TENDRE"
        assert result["surface_ha"] == Decimal("10.5")
        assert result["statut"] == "en_croissance"
        assert isinstance(result["date_semis"], date)
        assert result["coordonnees"]["latitude"] == 48.8566

    def test_validate_parcel_data_invalid(self):
        """Test complete parcel data validation with invalid data"""
        invalid_data = {
            "nom": "",  # Empty name
            "siret": "invalid",  # Invalid SIRET
            "culture_code": "INVALID",  # Invalid culture code
            "surface_ha": -5,  # Negative surface
        }
        
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_parcel_data(invalid_data)
        
        error_message = str(exc_info.value)
        assert "Validation failed" in error_message
        assert "Parcel name is required" in error_message or "Invalid SIRET" in error_message

    def test_validate_intervention_data_valid(self):
        """Test complete intervention data validation with valid data"""
        valid_data = {
            "parcelle_id": str(uuid4()),
            "siret": "12345678901234",
            "type_intervention": "SEMIS",
            "date_intervention": "2024-01-15",
            "produit_utilise": "Test Product",
            "dose_totale": 2.5,
            "unite_dose": "L/ha",
            "surface_traitee_ha": 5.0,
            "conditions_meteo": "Ensoleillé, 18°C",
            "cout_total": 150.75,
            "notes": "Test intervention"
        }
        
        result = FarmDataValidator.validate_intervention_data(valid_data)
        assert result["type_intervention"] == "SEMIS"
        assert result["dose_totale"] == Decimal("2.5")
        assert result["unite_dose"] == "l/ha"
        assert result["surface_traitee_ha"] == Decimal("5.0")
        assert isinstance(result["date_intervention"], date)

    def test_validate_intervention_data_invalid(self):
        """Test complete intervention data validation with invalid data"""
        invalid_data = {
            "parcelle_id": "invalid-uuid",
            "siret": "invalid",
            "type_intervention": "INVALID_TYPE",
            "date_intervention": "invalid-date",
        }
        
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_intervention_data(invalid_data)
        
        error_message = str(exc_info.value)
        assert "Validation failed" in error_message

    def test_validate_exploitation_data_valid(self):
        """Test complete exploitation data validation with valid data"""
        valid_data = {
            "siret": "12345678901234",
            "nom": "Test Farm",
            "surface_totale_ha": 100.0,
            "bio": True,
            "certification_bio": True,
            "date_certification_bio": "2023-01-01"
        }
        
        result = FarmDataValidator.validate_exploitation_data(valid_data)
        assert result["nom"] == "Test Farm"
        assert result["surface_totale_ha"] == Decimal("100.0")
        assert result["bio"] is True
        assert result["certification_bio"] is True
        assert isinstance(result["date_certification_bio"], date)

    def test_validate_exploitation_data_invalid(self):
        """Test complete exploitation data validation with invalid data"""
        invalid_data = {
            "siret": "invalid",
            "nom": "",  # Empty name
            "surface_totale_ha": -10,  # Negative surface
        }
        
        with pytest.raises(ValidationError) as exc_info:
            FarmDataValidator.validate_exploitation_data(invalid_data)
        
        error_message = str(exc_info.value)
        assert "Validation failed" in error_message


class TestPydanticModels:
    """Test suite for Pydantic validation models"""

    def test_parcel_create_request_valid(self):
        """Test ParcelCreateRequest with valid data"""
        valid_data = {
            "nom": "Test Parcel",
            "siret": "12345678901234",
            "culture_code": "BLE_TENDRE",
            "surface_ha": 10.5,
            "variete": "Test Variety",
            "date_semis": date(2024, 1, 15),
            "coordonnees": {"latitude": 48.8566, "longitude": 2.3522},
            "notes": "Test notes"
        }
        
        request = ParcelCreateRequest(**valid_data)
        assert request.nom == "Test Parcel"
        assert request.siret == "12345678901234"
        assert request.culture_code == "BLE_TENDRE"
        assert request.surface_ha == Decimal("10.5")

    def test_parcel_create_request_invalid(self):
        """Test ParcelCreateRequest with invalid data"""
        invalid_data = {
            "nom": "",  # Empty name
            "siret": "invalid",  # Invalid SIRET
            "culture_code": "INVALID",  # Invalid culture code
        }
        
        with pytest.raises(ValueError):
            ParcelCreateRequest(**invalid_data)

    def test_intervention_create_request_valid(self):
        """Test InterventionCreateRequest with valid data"""
        valid_data = {
            "parcelle_id": uuid4(),
            "siret": "12345678901234",
            "type_intervention": "SEMIS",
            "date_intervention": date(2024, 1, 15),
            "description": "Test intervention",
            "produit_utilise": "Test Product",
            "dose_totale": 2.5,
            "unite_dose": "L/ha",
            "surface_traitee_ha": 5.0,
            "conditions_meteo": "Ensoleillé, 18°C",
            "cout_total": 150.75,
            "notes": "Test notes"
        }
        
        request = InterventionCreateRequest(**valid_data)
        assert request.type_intervention == "SEMIS"
        assert request.dose_totale == Decimal("2.5")
        assert request.unite_dose == "l/ha"

    def test_intervention_create_request_invalid(self):
        """Test InterventionCreateRequest with invalid data"""
        invalid_data = {
            "parcelle_id": "invalid-uuid",
            "siret": "invalid",
            "type_intervention": "INVALID_TYPE",
            "date_intervention": "invalid-date",
        }
        
        with pytest.raises(ValueError):
            InterventionCreateRequest(**invalid_data)

    def test_exploitation_create_request_valid(self):
        """Test ExploitationCreateRequest with valid data"""
        valid_data = {
            "siret": "12345678901234",
            "nom": "Test Farm",
            "region_code": "75",
            "department_code": "75",
            "commune_insee": "75001",
            "surface_totale_ha": 100.0,
            "type_exploitation": "Polyculture",
            "bio": True,
            "certification_bio": True,
            "date_certification_bio": date(2023, 1, 1)
        }
        
        request = ExploitationCreateRequest(**valid_data)
        assert request.nom == "Test Farm"
        assert request.siret == "12345678901234"
        assert request.surface_totale_ha == Decimal("100.0")
        assert request.bio is True

    def test_exploitation_create_request_invalid(self):
        """Test ExploitationCreateRequest with invalid data"""
        invalid_data = {
            "siret": "invalid",
            "nom": "",  # Empty name
        }
        
        with pytest.raises(ValueError):
            ExploitationCreateRequest(**invalid_data)


class TestValidationError:
    """Test suite for ValidationError class"""

    def test_validation_error_creation(self):
        """Test ValidationError creation and properties"""
        error = ValidationError("Test error message", "test_field", "TEST_CODE")
        
        assert error.message == "Test error message"
        assert error.field == "test_field"
        assert error.code == "TEST_CODE"
        assert str(error) == "Test error message"

    def test_validation_error_minimal(self):
        """Test ValidationError creation with minimal parameters"""
        error = ValidationError("Test error message")
        
        assert error.message == "Test error message"
        assert error.field is None
        assert error.code is None
        assert str(error) == "Test error message"
