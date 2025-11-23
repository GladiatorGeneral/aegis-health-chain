"""Unit tests for healthcare standards mapper"""
import pytest
from src.healthcare_standards import HealthcareStandardsMapper, standards_mapper


class TestHealthcareStandardsMapper:
    """Test the HealthcareStandardsMapper class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mapper = HealthcareStandardsMapper()

    def test_mapper_initialization(self):
        """Test that mapper initializes correctly"""
        assert self.mapper is not None
        assert len(self.mapper.common_mappings) > 0

    def test_map_same_system(self):
        """Test mapping code to same system returns code unchanged"""
        result = self.mapper.map_code("J45", "icd10", "icd10")
        assert result["code"] == "J45"
        assert result["system"] == "icd10"

    def test_map_icd10_to_snomed(self):
        """Test mapping from ICD-10 to SNOMED CT"""
        result = self.mapper.map_code("J45", "icd10", "snomed")
        assert result is not None
        assert result["system"] == "snomed"
        assert "display" in result

    def test_map_snomed_to_icd10(self):
        """Test mapping from SNOMED CT to ICD-10"""
        result = self.mapper.map_code("195967001", "snomed", "icd10")
        assert result is not None
        assert result["system"] == "icd10"

    def test_map_hypertension(self):
        """Test mapping hypertension code"""
        result = self.mapper.map_code("I10", "icd10", "snomed")
        assert result is not None
        assert result["display"] == "Hypertension"

    def test_create_fhir_codeable_concept(self):
        """Test creating FHIR CodeableConcept"""
        concept = self.mapper.create_fhir_codeable_concept("J45", "icd10", "Asthma")
        assert concept is not None
        assert concept.coding is not None
        assert len(concept.coding) > 0
        assert concept.coding[0].code == "J45"

    def test_get_system_uri(self):
        """Test getting FHIR system URIs"""
        uri = self.mapper._get_system_uri("icd10")
        assert uri == "http://hl7.org/fhir/sid/icd-10-cm"

        uri = self.mapper._get_system_uri("snomed")
        assert uri == "http://snomed.info/sct"

        uri = self.mapper._get_system_uri("loinc")
        assert uri == "http://loinc.org"

    def test_get_display(self):
        """Test getting display text for codes"""
        display = self.mapper._get_display("J45", "icd10")
        assert display == "Asthma"

        display = self.mapper._get_display("I10", "icd10")
        assert display == "Hypertension"

        # Unknown code
        display = self.mapper._get_display("UNKNOWN", "icd10")
        assert "Unknown" in display

    def test_null_code_handling(self):
        """Test handling of null/empty codes"""
        result = self.mapper.map_code(None, "icd10", "snomed")
        assert result is None

        result = self.mapper.map_code("", "icd10", "snomed")
        assert result is None

    def test_global_instance(self):
        """Test that global instance works"""
        assert standards_mapper is not None
        result = standards_mapper.map_code("J45", "icd10", "snomed")
        assert result is not None
