# Disease knowledge base

`src/crop_health/knowledge_base/diseases.json` contains curated content returned for configured classifier classes. Disease descriptions, symptoms, weather associations, and cultural guidance are summarized from cited university extension sources. This is decision support; weather is contextual and does not establish disease causation.

There are five disease entries and two healthy-status entries. A healthy-status result means only that the classifier selected its supported healthy class. It does not exclude conditions outside the selected labels. Unknown IDs return no entry rather than being synthesized.

No pesticide product, dose, or application schedule is prescribed. For suspected disease, particularly late blight, the content directs users to local agricultural extension for confirmation and region-specific management. Guidance may not transfer unchanged across climates or production systems.

Each record has a stable ID, crop, name, condition type, description, symptom list, favorable-weather context, prevention, general management, and source metadata. `KnowledgeBase` provides file-based lookup; the record shape can later be normalized into disease and source tables.

Validate coverage against `configs/dataset_config.yaml` with:

```powershell
python scripts/validate_knowledge_base.py
```

The validator checks required fields, source metadata, crop consistency, and exact configured-class coverage.
