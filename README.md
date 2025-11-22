# Aegis Health Chain

AI-powered health forecasting platform with FHIR interoperability and HuggingFace integration.

## Project Structure

```
aegis-health-chain/
├── data/           # Data directories
├── fhir/           # FHIR profiles and resources
├── src/            # Source code
├── notebooks/      # Jupyter notebooks
├── tests/          # Test suites
└── docs/           # Documentation
```

## Quick Start

1. **Setup Environment**:
   ```bash
   conda env create -f environment.yml
   conda activate aegis-health
   pip install -e .
   ```

2. **Explore Data**:
   ```bash
   jupyter notebook notebooks/01_data_exploration.ipynb
   ```

3. **Run Tests**:
   ```bash
   pytest tests/
   ```

## Development Phases

- **Phase 1**: UDM Mapper & Data Pipeline
- **Phase 2**: FHIR Profile Development  
- **Phase 3**: HuggingFace Model Integration
- **Phase 4**: Forecasting Engine
