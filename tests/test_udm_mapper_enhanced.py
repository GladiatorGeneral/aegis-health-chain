"""Unit tests for Enhanced UDM mapper"""
from src.udm_mapper_enhanced import EnhancedUDMMapper


def test_udm_patient_to_fhir_and_back():
    mapper = EnhancedUDMMapper()
    udm = {
        "patient_id": "p-001",
        "name": "Jane Doe",
        "gender": "F",
        "birth_date": "1990-05-20",
        "contact": {"phone": "+15551234567", "email": "jane@example.com"},
        "address": {"street": "1 Health Way", "city": "City", "state": "ST", "zip": "12345"},
    }

    patient = mapper.udm_to_fhir_patient(udm)
    assert patient is not None
    assert patient.id == "p-001"
    assert patient.name and patient.name[0].text == "Jane Doe"

    # Convert back
    udm_back = mapper._fhir_patient_to_udm(patient)
    assert udm_back["patient_id"] == "p-001"
    assert udm_back["name"]


def test_udm_condition_conversion():
    mapper = EnhancedUDMMapper()
    udm_cond = {"id": "c1", "code": "J45", "system": "icd10", "onset_date": "2020-01-01"}

    cond = mapper.udm_to_fhir_condition(udm_cond, "p-001")
    assert cond is not None
    assert cond.resource_type == "Condition"
    assert cond.subject.reference == "Patient/p-001"


def test_udm_observation_conversion():
    mapper = EnhancedUDMMapper()
    udm_obs = {"id": "o1", "code": "85354-9", "value": 120, "unit": "mmHg", "effective_datetime": "2024-01-01T12:00:00"}

    obs = mapper.udm_to_fhir_observation(udm_obs, "p-001")
    assert obs is not None
    assert obs.resource_type == "Observation"
    assert obs.subject.reference == "Patient/p-001"
    assert hasattr(obs, "valueQuantity") or hasattr(obs, "valueString")
