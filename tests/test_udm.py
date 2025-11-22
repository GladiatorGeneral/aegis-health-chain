"""Tests for UDM mapper"""
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.udm_mapper import UDMMapper


class TestUDMMapper:
    def setup_method(self):
        self.mapper = UDMMapper()

    def test_epic_mapping(self):
        epic_data = {
            "PAT_MRN": "TEST123",
            "BIRTH_DATE": "1990-01-15",
            "SEX": "M",
            "RACE": "White",
            "ETHNICITY": "Not Hispanic"
        }
        
        result = self.mapper.map_ehr_to_udm(epic_data, "epic")
        assert "patient" in result
        assert result["patient"]["id"] == "TEST123"
        assert result["patient"]["gender"] == "male"

    def test_gender_mapping(self):
        assert self.mapper._map_gender_code("M") == "male"
        assert self.mapper._map_gender_code("F") == "female"
        assert self.mapper._map_gender_code("U") == "unknown"
        assert self.mapper._map_gender_code("unknown") == "unknown"

    def test_date_standardization(self):
        assert self.mapper._standardize_date("1990-01-15") == "1990-01-15"
        assert self.mapper._standardize_date("01/15/1990") == "1990-01-15"
        assert self.mapper._standardize_date("invalid") is None
