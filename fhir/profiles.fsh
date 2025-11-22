// FHIR Shorthand profiles for health forecasting

Profile: AegisHealthForecast
Parent: RiskAssessment
Id: aegis-health-forecast
Title: "Aegis Health Forecasting Profile"
Description: "Custom profile for AI-powered health risk predictions"
* ^status = #draft
* ^date = "2024-01-15"

* status MS
* subject MS
* method from ForecastMethodVS (required)
* basis MS
* prediction MS
* prediction.outcome MS
* prediction.probabilityDecimal MS
* prediction.whenRange MS

// Extensions for forecasting-specific data
* extension contains ForecastHorizon named forecastHorizon 1..1 MS
* extension contains ModelMetadata named modelMetadata 1..1 MS

Extension: ForecastHorizon
Id: forecast-horizon
Title: "Forecast Time Horizon"
Description: "Time period for which the forecast applies"
* ^context[+].type = #element
* ^context[=].expression = "RiskAssessment"
* value[x] 1..1 MS
* value[x] only Duration

Extension: ModelMetadata
Id: model-metadata
Title: "AI Model Metadata"
Description: "Information about the machine learning model used for forecasting"
* ^context[+].type = #element
* ^context[=].expression = "RiskAssessment"
* extension contains
    modelName 1..1 MS and
    modelVersion 1..1 MS and
    trainingData 0..1 MS and
    confidenceScore 0..1 MS

* extension[modelName].value[x] only string
* extension[modelVersion].value[x] only string
* extension[trainingData].value[x] only string
* extension[confidenceScore].value[x] only decimal

// Value Sets
ValueSet: ForecastMethodVS
Title: "Forecasting Method Value Set"
Description: "Methods used for health forecasting"
* ^status = #draft
* include codes from system ForecastMethodCS

CodeSystem: ForecastMethodCS
Title: "Forecasting Method Code System"
Description: "Codes for health forecasting methodologies"
* ^caseSensitive = true
* #bert-clinical "Clinical BERT Model"
* #survival-analysis "Survival Analysis"
* #time-series "Time Series Forecasting"
* #ensemble "Ensemble Methods"
