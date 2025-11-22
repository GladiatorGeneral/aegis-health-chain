"""Unified Data Model mapping engine"""
import pandas as pd
import json
from typing import Dict, Any, List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UDMMapper:
    """Core UDM mapping engine for healthcare data standardization"""

    def __init__(self):
        self.logical_model = self._load_logical_model()
        self.mapping_rules = self._load_mapping_rules()

    def _load_logical_model(self) -> pd.DataFrame:
        """Load our logical model spreadsheet"""
        try:
            return pd.read_csv("data/logical_model.csv")
        except FileNotFoundError:
            logger.warning("Logical model CSV not found, using empty DataFrame")
            return pd.DataFrame()

    def _load_mapping_rules(self) -> Dict[str, Any]:
        """Load mapping rules for different source systems"""
        return {
            "epic": self._get_epic_mapping_rules(),
            "cerner": self._get_cerner_mapping_rules(),
            "generic": self._get_generic_mapping_rules(),
        }

    def _get_epic_mapping_rules(self) -> Dict[str, Any]:
        """Epic-specific mapping rules"""
        return {
            "patient": {
                "PAT_MRN": "id",
                "BIRTH_DATE": "birthDate",
                "SEX": "gender",
                "RACE": "race",
                "ETHNICITY": "ethnicity",
            },
            "condition": {
                "PROBLEM_LIST": "Condition",
                "DIAGNOSIS": "Condition",
            },
        }

    def _get_cerner_mapping_rules(self) -> Dict[str, Any]:
        """Cerner-specific mapping rules"""
        return {
            "patient": {
                "PATIENT_ID": "id",
                "DOB": "birthDate",
                "GENDER": "gender",
            },
        }

    def _get_generic_mapping_rules(self) -> Dict[str, Any]:
        """Generic mapping rules for unknown systems"""
        return {
            "patient": {
                "id": "id",
                "birth_date": "birthDate",
                "birthdate": "birthDate",
                "gender": "gender",
                "sex": "gender",
            },
        }

    def map_ehr_to_udm(self, raw_data: Dict[str, Any], source_system: str) -> Dict[str, Any]:
        """Map raw EHR data to UDM format"""
        logger.info(f"Mapping data from {source_system} to UDM")

        if source_system not in self.mapping_rules:
            logger.warning(f"Unknown source system {source_system}, using generic mapping")
            source_system = "generic"

        mapper = getattr(self, f"_map_{source_system}_to_udm", self._map_generic_to_udm)
        return mapper(raw_data)

    def _map_epic_to_udm(self, epic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Epic-specific mapping logic"""
        udm_patient = {
            "resourceType": "Patient",
            "id": epic_data.get("PAT_MRN"),
            "birthDate": self._standardize_date(epic_data.get("BIRTH_DATE")),
            "gender": self._map_gender_code(epic_data.get("SEX")),
            "race": self._map_race_code(epic_data.get("RACE")),
            "ethnicity": self._map_ethnicity_code(epic_data.get("ETHNICITY")),
        }
        return {"patient": udm_patient}

    def _map_cerner_to_udm(self, cerner_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cerner-specific mapping logic"""
        udm_patient = {
            "resourceType": "Patient",
            "id": cerner_data.get("PATIENT_ID"),
            "birthDate": self._standardize_date(cerner_data.get("DOB")),
            "gender": self._map_gender_code(cerner_data.get("GENDER")),
        }
        return {"patient": udm_patient}

    def _map_generic_to_udm(self, generic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic mapping logic"""
        udm_patient = {
            "resourceType": "Patient",
            "id": generic_data.get("id") or generic_data.get("patient_id"),
            "birthDate": self._standardize_date(
                generic_data.get("birth_date") or generic_data.get("birthdate")
            ),
            "gender": self._map_gender_code(
                generic_data.get("gender") or generic_data.get("sex")
            ),
        }
        return {"patient": udm_patient}

    def _standardize_date(self, date_str: str) -> str:
        """Standardize date format to ISO 8601"""
        if not date_str:
            return None

        try:
            # Handle common date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            logger.warning(f"Could not parse date: {date_str}")
            return None
        except Exception as e:
            logger.error(f"Error standardizing date {date_str}: {e}")
            return None

    def _map_gender_code(self, gender_code: str) -> str:
        """Map gender codes to FHIR administrative-gender"""
        gender_map = {
            "M": "male",
            "F": "female",
            "U": "unknown",
            "O": "other",
            "male": "male",
            "female": "female",
            "unknown": "unknown",
            "other": "other",
        }
        return gender_map.get(str(gender_code).upper(), "unknown")

    def _map_race_code(self, race_code: str) -> Dict[str, Any]:
        """Map race codes to standardized format"""
        if not race_code:
            return None
        return {"text": str(race_code)}

    def _map_ethnicity_code(self, ethnicity_code: str) -> Dict[str, Any]:
        """Map ethnicity codes to standardized format"""
        if not ethnicity_code:
            return None
        return {"text": str(ethnicity_code)}

    def get_entity_attributes(self, entity_name: str) -> List[str]:
        """Get all attributes for a given entity from logical model"""
        if self.logical_model.empty:
            return []
        entity_attrs = self.logical_model[self.logical_model["Entity"] == entity_name]
        return entity_attrs["Attribute"].tolist()


# Singleton instance for easy access
udm_mapper = UDMMapper()

if __name__ == "__main__":
    # Test the mapper
    test_data = {
        "PAT_MRN": "12345",
        "BIRTH_DATE": "1985-03-15",
        "SEX": "F",
        "RACE": "Asian",
        "ETHNICITY": "Not Hispanic",
    }
    result = udm_mapper.map_ehr_to_udm(test_data, "epic")
    print("Test mapping result:")
    print(json.dumps(result, indent=2))
