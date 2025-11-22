"""Data pipeline for ETL processes"""
import pandas as pd
from typing import Dict, Any, List
import logging
from .udm_mapper import udm_mapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPipeline:
    """ETL pipeline for healthcare data"""

    def __init__(self):
        self.udm_mapper = udm_mapper

    def process_ehr_data(self, raw_data_path: str, source_system: str) -> List[Dict[str, Any]]:
        """Process EHR data from file"""
        logger.info(f"Processing EHR data from {raw_data_path}")
        
        # Read raw data
        if raw_data_path.endswith('.csv'):
            raw_df = pd.read_csv(raw_data_path)
        elif raw_data_path.endswith('.json'):
            raw_df = pd.read_json(raw_data_path)
        else:
            raise ValueError(f"Unsupported file format: {raw_data_path}")
        
        # Convert to UDM format
        udm_data = []
        for _, row in raw_df.iterrows():
            try:
                udm_record = self.udm_mapper.map_ehr_to_udm(row.to_dict(), source_system)
                udm_data.append(udm_record)
            except Exception as e:
                logger.error(f"Error processing row {_}: {e}")
                continue
        
        logger.info(f"Processed {len(udm_data)} records")
        return udm_data

    def generate_synthetic_data(self, num_patients: int = 100) -> List[Dict[str, Any]]:
        """Generate synthetic patient data for testing"""
        import random
        from datetime import datetime, timedelta
        
        synthetic_data = []
        conditions = ["Asthma", "Hypertension", "Diabetes", "COPD", "Heart Failure"]
        genders = ["male", "female"]
        
        for i in range(num_patients):
            birth_date = datetime.now() - timedelta(days=random.randint(365*20, 365*80))
            patient_data = {
                "PAT_MRN": f"SYNTH{i:06d}",
                "BIRTH_DATE": birth_date.strftime("%Y-%m-%d"),
                "SEX": random.choice(genders),
                "RACE": random.choice(["White", "Black", "Asian", "Other"]),
                "ETHNICITY": random.choice(["Hispanic", "Not Hispanic"]),
            }
            
            # Add some random conditions
            patient_conditions = random.sample(conditions, random.randint(0, 3))
            if patient_conditions:
                patient_data["CONDITIONS"] = patient_conditions
            
            udm_record = self.udm_mapper.map_ehr_to_udm(patient_data, "epic")
            synthetic_data.append(udm_record)
        
        logger.info(f"Generated {len(synthetic_data)} synthetic patient records")
        return synthetic_data

    def save_udm_data(self, udm_data: List[Dict[str, Any]], output_path: str):
        """Save UDM data to file"""
        import json
        
        with open(output_path, 'w') as f:
            json.dump(udm_data, f, indent=2)
        
        logger.info(f"Saved UDM data to {output_path}")

    def load_udm_data(self, input_path: str) -> List[Dict[str, Any]]:
        """Load UDM data from file"""
        import json
        
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} UDM records from {input_path}")
        return data


# Global instance
data_pipeline = DataPipeline()
