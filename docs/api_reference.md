# API Reference

## UDMMapper

```python
mapper = UDMMapper()
result = mapper.map_ehr_to_udm(raw_data, "epic")
```

## ClinicalForecastingModels

```python
models = ClinicalForecastingModels()
embeddings = models.get_clinical_embeddings(clinical_text)
```

## DataPipeline

```python
pipeline = DataPipeline()
synthetic_data = pipeline.generate_synthetic_data(100)
```
