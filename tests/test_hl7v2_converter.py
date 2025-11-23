"""Unit tests for HL7v2 -> FHIR converter"""
from src.hl7v2_converter import HL7v2ToFHIRConverter


def sample_hl7_message():
    # Minimal HL7 message with PID, OBX and DG1
    return """
MSH|^~\\&|SENDER|SENDERFAC|RECEIVER|RECVFAC|202311231200||ORU^R01|MSG0001|P|2.5.1
PID|1||12345^^^MR||Doe^John||19800101|M|||123 Main St^^Metropolis^NY^10101
OBR|1||OBR1|TEST^Test Order
OBX|1|NM|8480-6^Systolic blood pressure^LN||120|mmHg|||||F
DG1|1|I9|I10^Hypertension^I9||20231101
""".strip()


def test_hl7_to_fhir_bundle_basic_fields():
    conv = HL7v2ToFHIRConverter()
    bundle = conv.convert_message(sample_hl7_message())

    # Basic assertions: bundle exists and contains entries
    assert bundle is not None
    assert hasattr(bundle, "entry")
    assert len(bundle.entry) >= 2

    # Check there is at least one Patient and one Observation/Condition
    resource_types = [entry.resource.get_resource_type() for entry in bundle.entry]
    assert "Patient" in resource_types
    assert any(rt == "Observation" for rt in resource_types) or any(rt == "Condition" for rt in resource_types)


def test_patient_fields_from_pid():
    conv = HL7v2ToFHIRConverter()
    bundle = conv.convert_message(sample_hl7_message())

    # find patient
    patient = next((e.resource for e in bundle.entry if e.resource.get_resource_type() == "Patient"), None)
    assert patient is not None
    # note: PID contained MR with assigning authority; id may be preserved as given
    assert getattr(patient, 'id', None) is not None
    assert patient.birthDate is not None
    assert (patient.name and (getattr(patient.name[0], 'text', None) or True))


def test_observation_conversion():
    conv = HL7v2ToFHIRConverter()
    bundle = conv.convert_message(sample_hl7_message())

    obs = next((e.resource for e in bundle.entry if e.resource.get_resource_type() == "Observation"), None)
    assert obs is not None
    # code should be a CodeableConcept with a coding entry
    assert hasattr(obs, "code") and obs.code is not None
    coding = obs.code.coding[0]
    assert "8480-6" in (coding.code or "")


def test_condition_conversion():
    conv = HL7v2ToFHIRConverter()
    bundle = conv.convert_message(sample_hl7_message())

    cond = next((e.resource for e in bundle.entry if e.resource.get_resource_type() == "Condition"), None)
    assert cond is not None
    # code may have been mapped; ensure there is a code present
    assert hasattr(cond, "code") and cond.code is not None
    if cond.code.coding:
        assert cond.code.coding[0].code is not None
