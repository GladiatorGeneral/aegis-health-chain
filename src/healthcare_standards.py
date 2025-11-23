"""Healthcare standards mapping and terminology services"""
from typing import Dict, Optional
import requests
import pandas as pd
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding


class HealthcareStandardsMapper:
    """Map between different healthcare standards and terminologies"""

    def __init__(self):
        self.terminology_services = {
            "icd10": self._map_icd10,
            "snomed": self._map_snomed,
            "loinc": self._map_loinc,
            "cpt": self._map_cpt,
            "rxnorm": self._map_rxnorm,
        }

        # Common mappings for quick lookup
        self.common_mappings = self._load_common_mappings()

    def _load_common_mappings(self) -> Dict[str, Dict]:
        """Load common code mappings for performance"""
        return {
            "conditions": {
                # Asthma mappings across systems
                "J45": {"snomed": "195967001", "display": "Asthma"},
                "195967001": {"icd10": "J45", "display": "Asthma"},
                # Hypertension mappings
                "I10": {"snomed": "38341003", "display": "Hypertension"},
                "38341003": {"icd10": "I10", "display": "Hypertension"},
            },
            "observations": {
                # Blood pressure mappings
                "85354-9": {"display": "Blood pressure panel"},
                "8462-4": {"display": "Diastolic blood pressure"},
                "8480-6": {"display": "Systolic blood pressure"},
            },
        }

    def map_code(self, code: str, source_system: str, target_system: str) -> Optional[Dict]:
        """Map codes between healthcare terminology systems"""
        if not code:
            return None

        if source_system == target_system:
            return {"code": code, "system": source_system, "display": self._get_display(code, source_system)}

        # Check common mappings first
        if code in self.common_mappings.get("conditions", {}) and target_system in self.common_mappings["conditions"][code]:
            mapped_code = self.common_mappings["conditions"][code][target_system]
            return {"code": mapped_code, "system": target_system, "display": self.common_mappings["conditions"][code]["display"]}

        # Fall back to terminology service
        mapper = self.terminology_services.get(target_system)
        if mapper:
            return mapper(code, source_system)

        return None

    def create_fhir_codeable_concept(self, code: str, system: str, display: str = None) -> CodeableConcept:
        """Create FHIR CodeableConcept with proper coding"""
        system_uri = self._get_system_uri(system)
        coding = Coding(system=system_uri, code=code, display=display or self._get_display(code, system))
        return CodeableConcept.construct(coding=[coding], text=display or coding.display)

    def _get_system_uri(self, system: str) -> str:
        """Get FHIR system URI for terminology system"""
        system_uris = {
            "icd10": "http://hl7.org/fhir/sid/icd-10-cm",
            "snomed": "http://snomed.info/sct",
            "loinc": "http://loinc.org",
            "cpt": "http://www.ama-assn.org/go/cpt",
            "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm",
        }
        return system_uris.get(system, system)

    def _map_icd10(self, code: str, source_system: str) -> Dict:
        """Map to ICD-10-CM (placeholder)"""
        # In production, call a terminology/translation service (e.g., Apelon, SNOMED CT mapping)
        return {"code": code, "system": "icd10", "display": self._get_display(code, "icd10")}

    def _map_snomed(self, code: str, source_system: str) -> Dict:
        """Map to SNOMED CT (placeholder)"""
        return {"code": code, "system": "snomed", "display": self._get_display(code, "snomed")}

    def _map_loinc(self, code: str, source_system: str) -> Dict:
        """Map to LOINC (placeholder)"""
        return {"code": code, "system": "loinc", "display": self._get_display(code, "loinc")}

    def _map_cpt(self, code: str, source_system: str) -> Dict:
        """Map to CPT (placeholder)"""
        return {"code": code, "system": "cpt", "display": self._get_display(code, "cpt")}

    def _map_rxnorm(self, code: str, source_system: str) -> Dict:
        """Map to RxNorm (placeholder)"""
        return {"code": code, "system": "rxnorm", "display": self._get_display(code, "rxnorm")}

    def _get_display(self, code: str, system: str) -> str:
        """Get display text for a code (simplified)"""
        display_map = {
            "J45": "Asthma",
            "195967001": "Asthma",
            "I10": "Hypertension",
            "38341003": "Hypertension",
            "85354-9": "Blood pressure panel",
            "8462-4": "Diastolic blood pressure",
        }
        return display_map.get(code, f"Unknown {system} code: {code}")


# Global instance
standards_mapper = HealthcareStandardsMapper()
