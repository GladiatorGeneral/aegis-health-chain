"""HL7v2 to FHIR converter with standards support"""
from typing import Dict, Any, Optional, List, Tuple
import re
from datetime import datetime
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.condition import Condition
from .healthcare_standards import standards_mapper


class HL7v2Parser:
    """Parse HL7v2 messages"""

    def __init__(self, field_sep: str = "|", component_sep: str = "^", repeat_sep: str = "~"):
        self.field_sep = field_sep
        self.component_sep = component_sep
        self.repeat_sep = repeat_sep

    def parse_message(self, message: str) -> Dict[str, Any]:
        """Parse HL7v2 message into segments"""
        lines = message.strip().split("\n")
        segments = {}

        for line in lines:
            parts = line.split(self.field_sep)
            if not parts:
                continue

            segment_id = parts[0]
            if segment_id not in segments:
                segments[segment_id] = []

            segments[segment_id].append(parts)

        return segments

    def parse_pid_segment(self, pid_fields: List[str]) -> Dict[str, Any]:
        """Parse PID (Patient Identification) segment"""
        patient_data = {}

        if len(pid_fields) > 3:
            patient_data["patient_id"] = pid_fields[3]

        if len(pid_fields) > 5:
            name_parts = pid_fields[5].split(self.component_sep)
            if name_parts:
                family = name_parts[0] if len(name_parts) > 0 else ""
                given = name_parts[1] if len(name_parts) > 1 else ""
                patient_data["name"] = f"{given} {family}".strip()

        if len(pid_fields) > 8:
            gender_map = {"M": "M", "F": "F", "O": "O", "U": "U"}
            patient_data["gender"] = gender_map.get(pid_fields[8], "U")

        if len(pid_fields) > 7:
            patient_data["birth_date"] = self._parse_hl7_date(pid_fields[7])

        return patient_data

    def parse_obx_segment(self, obx_fields: List[str]) -> Dict[str, Any]:
        """Parse OBX (Observation) segment"""
        obs_data = {}

        if len(obx_fields) > 3:
            obs_data["code"] = obx_fields[3].split(self.component_sep)[0] if obx_fields[3] else ""

        if len(obx_fields) > 5:
            obs_data["value"] = obx_fields[5]

        if len(obx_fields) > 6:
            obs_data["unit"] = obx_fields[6]

        if len(obx_fields) > 14:
            obs_data["effective_datetime"] = self._parse_hl7_date(obx_fields[14])

        return obs_data

    def parse_dg1_segment(self, dg1_fields: List[str]) -> Dict[str, Any]:
        """Parse DG1 (Diagnosis) segment"""
        diagnosis_data = {}

        if len(dg1_fields) > 3:
            code_info = dg1_fields[3].split(self.component_sep)
            diagnosis_data["code"] = code_info[0] if code_info else ""
            diagnosis_data["description"] = code_info[1] if len(code_info) > 1 else ""

        if len(dg1_fields) > 5:
            diagnosis_data["diagnosis_date"] = self._parse_hl7_date(dg1_fields[5])

        return diagnosis_data

    def _parse_hl7_date(self, hl7_date: str) -> Optional[str]:
        """Parse HL7 date format (YYYYMMDD or YYYYMMDDHHMM) to ISO format"""
        if not hl7_date:
            return None

        try:
            if len(hl7_date) >= 8:
                year = int(hl7_date[0:4])
                month = int(hl7_date[4:6])
                day = int(hl7_date[6:8])
                dt = datetime(year, month, day)
                return dt.isoformat()
        except (ValueError, IndexError):
            return None

        return None


class HL7v2ToFHIRConverter:
    """Convert HL7v2 messages to FHIR resources"""

    def __init__(self):
        self.parser = HL7v2Parser()
        self.standards_mapper = standards_mapper

    def convert_message(self, hl7_message: str) -> Bundle:
        """Convert complete HL7v2 message to FHIR Bundle"""
        segments = self.parser.parse_message(hl7_message)
        entries = []

        # Process PID for Patient
        patient = None
        if "PID" in segments and segments["PID"]:
            patient_data = self.parser.parse_pid_segment(segments["PID"][0])
            patient = self._create_fhir_patient(patient_data)
            entries.append(BundleEntry.construct(resource=patient))

        patient_id = patient.id if patient else "unknown"

        # Process OBX for Observations
        if "OBX" in segments:
            for obx_segment in segments["OBX"]:
                obs_data = self.parser.parse_obx_segment(obx_segment)
                obs = self._create_fhir_observation(obs_data, patient_id)
                entries.append(BundleEntry.construct(resource=obs))

        # Process DG1 for Conditions (Diagnoses)
        if "DG1" in segments:
            for dg1_segment in segments["DG1"]:
                diagnosis_data = self.parser.parse_dg1_segment(dg1_segment)
                condition = self._create_fhir_condition(diagnosis_data, patient_id)
                entries.append(BundleEntry.construct(resource=condition))

        bundle_data = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": entries,
        }

        return Bundle.construct(**bundle_data)

    def _create_fhir_patient(self, patient_data: Dict[str, Any]) -> Patient:
        """Create FHIR Patient from HL7v2 PID data"""
        fhir_data = {
            "resourceType": "Patient",
            "id": patient_data.get("patient_id", f"hl7-patient-{datetime.now().timestamp()}"),
        }

        if "name" in patient_data:
            fhir_data["name"] = [{"text": patient_data["name"]}]

        if "gender" in patient_data:
            gender_map = {"M": "male", "F": "female", "O": "other", "U": "unknown"}
            fhir_data["gender"] = gender_map.get(patient_data["gender"], "unknown")

        if "birth_date" in patient_data:
            fhir_data["birthDate"] = patient_data["birth_date"]

        return Patient.construct(**fhir_data)

    def _create_fhir_observation(self, obs_data: Dict[str, Any], patient_id: str) -> Observation:
        """Create FHIR Observation from HL7v2 OBX data"""
        fhir_data = {
            "resourceType": "Observation",
            "id": f"hl7-obs-{datetime.now().timestamp()}",
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
        }

        # Map LOINC code
        if "code" in obs_data:
            code = obs_data["code"]
            fhir_data["code"] = self.standards_mapper.create_fhir_codeable_concept(code, "loinc")

        # Value with unit
        if "value" in obs_data:
            value = obs_data["value"]
            try:
                value_float = float(value)
                fhir_data["valueQuantity"] = {
                    "value": value_float,
                    "unit": obs_data.get("unit", ""),
                    "system": "http://unitsofmeasure.org",
                }
            except ValueError:
                fhir_data["valueString"] = str(value)

        if "effective_datetime" in obs_data and obs_data["effective_datetime"]:
            fhir_data["effectiveDateTime"] = obs_data["effective_datetime"]

        return Observation.construct(**fhir_data)

    def _create_fhir_condition(self, diagnosis_data: Dict[str, Any], patient_id: str) -> Condition:
        """Create FHIR Condition from HL7v2 DG1 data"""
        fhir_data = {
            "resourceType": "Condition",
            "id": f"hl7-cond-{datetime.now().timestamp()}",
            "subject": {"reference": f"Patient/{patient_id}"},
        }

        # Map diagnosis code (typically ICD-10) to SNOMED CT
        if "code" in diagnosis_data:
            code = diagnosis_data["code"]
            # Assume ICD-10 format; map to SNOMED CT for FHIR preference
            mapped = self.standards_mapper.map_code(code, "icd10", "snomed")
            if mapped:
                fhir_data["code"] = self.standards_mapper.create_fhir_codeable_concept(
                    mapped["code"], "snomed", mapped.get("display")
                )
            else:
                fhir_data["code"] = self.standards_mapper.create_fhir_codeable_concept(
                    code, "icd10", diagnosis_data.get("description")
                )

        if "diagnosis_date" in diagnosis_data and diagnosis_data["diagnosis_date"]:
            fhir_data["onsetDateTime"] = diagnosis_data["diagnosis_date"]

        return Condition.construct(**fhir_data)


# Global instance
hl7_converter = HL7v2ToFHIRConverter()
