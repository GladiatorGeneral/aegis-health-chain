"""Enhanced UDM (Universal Data Model) mapper with healthcare standards integration"""
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from fhir.resources.patient import Patient
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.resource import Resource
from .healthcare_standards import standards_mapper


class EnhancedUDMMapper:
    """Map between Universal Data Model and FHIR resources with standards support"""

    def __init__(self):
        self.standards_mapper = standards_mapper
        self.supported_resources = [
            "Patient",
            "Condition",
            "Observation",
            "Medication",
            "Procedure",
            "Encounter",
        ]

    def udm_to_fhir_patient(self, udm_record: Dict[str, Any]) -> Patient:
        """Convert UDM patient record to FHIR Patient resource"""
        patient_data = {
            "resourceType": "Patient",
            "id": udm_record.get("patient_id"),
        }

        # Name
        if "name" in udm_record:
            patient_data["name"] = [{"text": udm_record["name"]}]

        # Gender
        if "gender" in udm_record:
            gender_map = {"M": "male", "F": "female", "O": "other"}
            patient_data["gender"] = gender_map.get(udm_record["gender"], "unknown")

        # Birth date
        if "birth_date" in udm_record:
            patient_data["birthDate"] = udm_record["birth_date"]

        # Contact
        if "contact" in udm_record:
            patient_data["telecom"] = [
                {"system": "phone", "value": udm_record["contact"].get("phone")}
                if udm_record["contact"].get("phone")
                else None,
                {"system": "email", "value": udm_record["contact"].get("email")}
                if udm_record["contact"].get("email")
                else None,
            ]
            patient_data["telecom"] = [t for t in patient_data["telecom"] if t]

        # Address
        if "address" in udm_record:
            addr = udm_record["address"]
            patient_data["address"] = [
                {
                    "line": [addr.get("street", "")],
                    "city": addr.get("city", ""),
                    "state": addr.get("state", ""),
                    "postalCode": addr.get("zip", ""),
                }
            ]

        return Patient.construct(**patient_data)

    def udm_to_fhir_condition(self, udm_condition: Dict[str, Any], patient_id: str) -> Resource:
        """Convert UDM condition record to FHIR Condition resource with terminology mapping"""
        from fhir.resources.condition import Condition

        condition_data = {
            "resourceType": "Condition",
            "id": udm_condition.get("id", f"cond-{datetime.now().timestamp()}"),
            "subject": {"reference": f"Patient/{patient_id}"},
        }

        # Map condition code with standards support
        if "code" in udm_condition:
            code = udm_condition["code"]
            system = udm_condition.get("system", "icd10")

            # Try to map to SNOMED CT (preferred in FHIR)
            mapped = self.standards_mapper.map_code(code, system, "snomed")
            if mapped:
                condition_data["code"] = self.standards_mapper.create_fhir_codeable_concept(
                    mapped["code"], "snomed", mapped.get("display")
                )
            else:
                condition_data["code"] = self.standards_mapper.create_fhir_codeable_concept(code, system)

        # Onset date
        if "onset_date" in udm_condition:
            condition_data["onsetDateTime"] = udm_condition["onset_date"]

        # Abatement date
        if "abatement_date" in udm_condition:
            condition_data["abatementDateTime"] = udm_condition["abatement_date"]

        return Condition.construct(**condition_data)

    def udm_to_fhir_observation(self, udm_obs: Dict[str, Any], patient_id: str) -> Resource:
        """Convert UDM observation to FHIR Observation resource"""
        from fhir.resources.observation import Observation

        obs_data = {
            "resourceType": "Observation",
            "id": udm_obs.get("id", f"obs-{datetime.now().timestamp()}"),
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
        }

        # Observation code (LOINC preferred)
        if "code" in udm_obs:
            obs_data["code"] = self.standards_mapper.create_fhir_codeable_concept(
                udm_obs["code"], "loinc", udm_obs.get("display")
            )

        # Value
        if "value" in udm_obs:
            value = udm_obs["value"]
            if isinstance(value, (int, float)):
                obs_data["valueQuantity"] = {
                    "value": value,
                    "unit": udm_obs.get("unit", ""),
                    "system": "http://unitsofmeasure.org",
                }
            else:
                obs_data["valueString"] = str(value)

        # Effective date/time
        if "effective_datetime" in udm_obs:
            obs_data["effectiveDateTime"] = udm_obs["effective_datetime"]

        return Observation.construct(**obs_data)

    def fhir_to_udm(self, fhir_resource: Resource) -> Dict[str, Any]:
        """Convert FHIR resource to UDM format"""
        resource_type = fhir_resource.get_resource_type()

        if resource_type == "Patient":
            return self._fhir_patient_to_udm(fhir_resource)
        elif resource_type == "Condition":
            return self._fhir_condition_to_udm(fhir_resource)
        elif resource_type == "Observation":
            return self._fhir_observation_to_udm(fhir_resource)

        # Generic fallback
        return {"resource_type": resource_type, "data": fhir_resource.dict()}

    def _fhir_patient_to_udm(self, patient: Patient) -> Dict[str, Any]:
        """Convert FHIR Patient to UDM"""
        udm = {
            "type": "patient",
            "patient_id": patient.id,
        }

        if patient.name:
            udm["name"] = patient.name[0].text if patient.name[0].text else " ".join(
                filter(None, [patient.name[0].given[0] if patient.name[0].given else None, patient.name[0].family])
            )

        if patient.gender:
            gender_reverse = {"male": "M", "female": "F", "other": "O", "unknown": "U"}
            udm["gender"] = gender_reverse.get(patient.gender, "U")

        if patient.birthDate:
            udm["birth_date"] = str(patient.birthDate)

        return udm

    def _fhir_condition_to_udm(self, condition) -> Dict[str, Any]:
        """Convert FHIR Condition to UDM"""
        udm = {
            "type": "condition",
            "id": condition.id,
            "patient_id": condition.subject.reference.split("/")[-1] if condition.subject else None,
        }

        if condition.code and condition.code.coding:
            coding = condition.code.coding[0]
            udm["code"] = coding.code
            udm["system"] = self._parse_system_from_uri(coding.system)
            udm["display"] = coding.display

        if condition.onsetDateTime:
            udm["onset_date"] = str(condition.onsetDateTime)

        return udm

    def _fhir_observation_to_udm(self, observation) -> Dict[str, Any]:
        """Convert FHIR Observation to UDM"""
        udm = {
            "type": "observation",
            "id": observation.id,
            "patient_id": observation.subject.reference.split("/")[-1] if observation.subject else None,
        }

        if observation.code and observation.code.coding:
            coding = observation.code.coding[0]
            udm["code"] = coding.code
            udm["display"] = coding.display

        if hasattr(observation, "valueQuantity") and observation.valueQuantity:
            udm["value"] = observation.valueQuantity.value
            udm["unit"] = observation.valueQuantity.unit

        return udm

    def _parse_system_from_uri(self, uri: str) -> str:
        """Parse system name from FHIR system URI"""
        system_map = {
            "http://hl7.org/fhir/sid/icd-10-cm": "icd10",
            "http://snomed.info/sct": "snomed",
            "http://loinc.org": "loinc",
            "http://www.ama-assn.org/go/cpt": "cpt",
            "http://www.nlm.nih.gov/research/umls/rxnorm": "rxnorm",
        }
        return system_map.get(uri, uri)

    def create_fhir_bundle(self, udm_records: List[Dict[str, Any]], patient_id: str) -> Bundle:
        """Create a FHIR Bundle from multiple UDM records"""
        entries = []

        for record in udm_records:
            record_type = record.get("type", "").lower()

            if record_type == "condition":
                resource = self.udm_to_fhir_condition(record, patient_id)
            elif record_type == "observation":
                resource = self.udm_to_fhir_observation(record, patient_id)
            else:
                continue

            entries.append(BundleEntry.construct(resource=resource))

        bundle_data = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": entries,
        }

        return Bundle.construct(**bundle_data)


# Global instance
udm_mapper = EnhancedUDMMapper()
