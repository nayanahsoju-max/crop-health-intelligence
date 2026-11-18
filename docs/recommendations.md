# Traceable recommendations

`RecommendationEngine` turns a classifier result and an existing Stage 8 knowledge-base record into a deterministic response. It copies the record's disease description and its prevention/general-management text; it does not generate new agricultural advice. Disease information, general guidance, weather context, and weather-specific context are separate response fields.

## API and inputs

`POST /recommendations/current` accepts a classifier class ID and confidence, optional severity, and optional location:

```json
{
  "class_id": "tomato_early_blight",
  "confidence": 0.91,
  "severity": {"category": "Moderate", "severity_percentage": 24.0},
  "location": "Pune"
}
```

The confidence gate is configured by `minimum_prediction_confidence` in `configs/recommendation_config.yaml` (default 0.5). Unsupported classes, malformed predictions, and predictions below the threshold return `status: "safe_fallback"`, no disease-specific details or guidance, and an explanatory `prediction_status`. The service does not request weather for these cases. Severity is optional; only configured categories are retained. A `Severe` category adds a traceable reminder to prioritize the existing general guidance and seek local extension advice.

## Weather rules

When a location is supplied for an accepted prediction, the Stage 9 weather service is queried. If weather is unavailable or malformed, the disease-based response remains intact, `weather_guidance` is empty, and `message` states that weather-specific guidance could not be generated. Without a location the weather status is `not_requested` and the same clear message is returned.

Configured conditions in `configs/recommendation_config.yaml` select whether current temperature, humidity, or precipitation matches the knowledge base's existing favorable-weather description. The numeric thresholds operationalize those descriptions for deterministic matching; they are not validated disease-risk cutoffs. A match repeats the related knowledge-base weather context and explicitly says it does not show that weather caused the symptoms. A match never prescribes an action.

Weather-aware context is shown only for records with favorable-weather information (currently the disease records). Healthy/status records have no disease-weather match.

## Traceability and response shape

- `disease_information.trace` points to the knowledge-base entry and its source metadata.
- Each item in `general_guidance` names its source record field and carries the record's sources.
- Each `weather_guidance` item carries the knowledge-base entry/field, the matching configured `rule_id`, a note describing the rule's relationship to the source text, and the same source references.
- `weather_context` records the provider's location, observation time, and measurements separately from recommendations.

No pesticide product, dosage, or application schedule is supplied. The engine does not diagnose: a model label is a prediction, and even a healthy label does not exclude unsupported conditions. Use local agricultural extension for diagnosis and locally appropriate management. Weather context is observational and does not establish causation. The underlying severity estimate is provisional and its categories have not been validated against expert-scored field data.

## Verification

`tests/test_recommendations.py` uses known local knowledge-base entries and fake weather services. It covers normal output and traceability, matching and non-matching weather rules, unavailable weather, unknown classes, low confidence, malformed prediction/severity/weather inputs, severe-category handling, and the API endpoint without live network access.
