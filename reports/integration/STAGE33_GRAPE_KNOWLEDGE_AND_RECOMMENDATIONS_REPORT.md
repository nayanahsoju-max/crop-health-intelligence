# Stage 33 — Grape Disease Knowledge Base and Weather-Aware Recommendations

**Project:** AI-Powered Crop Health Intelligence System  
**Stage:** 33  
**Date:** 2026-11-17  
**Status:** ✅ COMPLETE

---

## 1. Overview

Stage 33 extended the disease knowledge base and weather-aware recommendation engine to cover the three Grape disease classes identified during Stage 29–30 Grape pre-training and holdout evaluation:

| Class ID | Disease Name | Grape Classifier Index |
|---|---|---|
| `grape_black_rot` | Grape Black Rot | 0 |
| `grape_esca` | Grape Esca (Black Measles) | 1 |
| `grape_isariopsis_leaf_blight` | Grape Isariopsis Leaf Blight | 2 |

The class ordering follows the YAML configuration in `configs/dataset_config_grape.yaml` (confirmed in Stage 29 audit).

> [!NOTE]
> This stage was partially interrupted by an accidental session disconnect. State was fully recovered
> by inspecting all relevant files before any edits were applied. No data was lost and no incorrect
> edits were made. All implementation was completed in the same session and verified before the
> disconnect notification.

---

## 2. Files Changed

| File | Change |
|---|---|
| `src/crop_health/knowledge_base/diseases.json` | 3 Grape disease records added (10 total entries) |
| `configs/recommendation_config.yaml` | 2 Grape weather rules added (5 total rules) |
| `tests/test_knowledge_base.py` | Fully rewritten — 5 tests covering all 10 classes |
| `tests/test_recommendations.py` | 7 Grape-specific tests added (18 total) |
| `tests/test_prediction_api.py` | `test_routing_grape_routes_to_grape_model` updated |

No trained model checkpoints, class mapping JSONs, split manifests, evaluation reports, Stage 32
routing logic, or Tomato-Potato knowledge base entries were modified.

---

## 3. Disease Knowledge Base — New Entries

### 3.1 `grape_black_rot`

**Disease Name:** Grape Black Rot  
**Pathogen:** *Guignardia bidwellii* (anamorph: *Phyllosticta ampelicida*)  
**Condition Type:** fungal

**Description:**  
Grape black rot is a destructive fungal disease caused by *Guignardia bidwellii*. It can cause
complete crop loss in susceptible varieties under warm, wet conditions. All green tissues including
leaves, shoots, tendrils, and berries are susceptible.

**Symptoms:**
- Circular reddish-brown spots (1–4 mm) with darker margins on leaves
- Tiny black fruiting bodies (pycnidia) visible within leaf lesions
- Infected berries turn brown, shrivel, and become hard black mummies (sclerotia)
- Shoot and tendril infections appear as dark elongated cankers

**Favorable Weather Conditions:**
- Warm temperatures (20–27 °C) combined with free moisture (rain, dew, irrigation)
- Extended periods of leaf wetness (≥ 6–12 hours) accelerate infection
- High relative humidity (≥ 80%) during shoot elongation and bloom is especially critical

**Sources:**
1. Ohio State University Extension (PLPATH-FRU-24): *Grape Black Rot* —
   <https://ohioline.osu.edu/factsheet/plpath-fru-24>
2. UC IPM: *Grape — UC IPM Pest Management Guidelines* —
   <https://ipm.ucanr.edu/agriculture/grape/>

---

### 3.2 `grape_esca`

**Disease Name:** Grape Esca (Black Measles)  
**Pathogens:** *Phaeomoniella chlamydospora*, *Phaeoacremonium minimum* and related *Phaeoacremonium* species  
**Condition Type:** fungal (wood-colonising trunk disease complex)

**Description:**  
Esca is a chronic, destructive grapevine trunk disease complex. Wood-colonising fungi progressively
degrade internal trunk and cordon wood over seasons. Foliar symptoms are intermittent and are
triggered by vine stress (heat, water stress) rather than short-term weather events.

**Symptoms:**
- Classic "tiger-stripe" pattern — interveinal chlorosis and necrosis on leaves
- Small, circular dark spots (black measles) on berries, often with a chlorotic halo
- Apoplexy: sudden wilting and death of an entire shoot or vine during hot periods
- Brown, spongy wood decay visible in cross-section of affected canes

**Favorable Weather Conditions:**
- Summer heat and drought stress commonly trigger foliar symptom expression
- Pruning wounds during wet conditions provide infection courts for wood-colonising pathogens
- Symptom expression is associated with vine water stress rather than ambient humidity or precipitation

> [!IMPORTANT]
> Esca is a wood-colonising disease complex. No short-term weather rule was added to the
> recommendation engine for Esca. Symptom expression is linked to multi-year wood colonisation
> and vine water stress — not to tractable real-time weather thresholds such as relative humidity
> or precipitation. Adding a simple humidity or precipitation trigger would be agronomically
> misleading. Users should consult a viticulture specialist or plant pathologist for management of
> suspected esca infections.

**Sources:**
1. UC IPM: *Esca (Black Measles) — Grapevine* —
   <https://ipm.ucanr.edu/PMG/r302100511.html>

---

### 3.3 `grape_isariopsis_leaf_blight`

**Disease Name:** Grape Isariopsis Leaf Blight  
**Pathogen:** *Pseudocercospora vitis* (synonyms: *Isariopsis clavispora*, *Phaeoisariopsis clavispora*; teleomorph: *Mycosphaerella personata*)  
**Condition Type:** fungal

**Description:**  
Isariopsis leaf blight causes large, angular necrotic lesions on grape foliage, leading to early
defoliation in severe cases. The disease is favoured by warm, humid conditions and is most
problematic in vineyards with dense canopies and poor air circulation.

**Symptoms:**
- Large (up to 2–3 cm), irregular angular dark brown to reddish-brown spots on upper leaf surface
- Lesions bounded by leaf veins, giving a blocky appearance
- Affected tissue becomes brittle and may fall out, leaving ragged holes
- Severe defoliation reduces photosynthetic capacity and can compromise fruit ripening

**Favorable Weather Conditions:**
- High relative humidity (≥ 85%) or persistent leaf wetness
- Warm temperatures with frequent rainfall events
- Dense canopy environments with restricted airflow exacerbate disease pressure

**Sources:**
1. NC State Extension — North Carolina Grape Grower's Guide, Chapter 8: Pest Management —
   <https://content.ces.ncsu.edu/north-carolina-grape-growers-guide/chapter-8-pest-management>

---

## 4. Weather Rules Added

Two rules were added to `configs/recommendation_config.yaml`. Esca intentionally received no rule
(see Section 3.2 above).

### Rule 1 — `grape_black_rot_warm_moist_context`

```yaml
id: grape_black_rot_warm_moist_context
disease_ids:
  - grape_black_rot
all_of:
  - field: temperature_celsius
    operator: ">="
    value: 20
any_of:
  - field: humidity_percent
    operator: ">="
    value: 80
  - field: precipitation_mm
    operator: ">="
    value: 0.2
note: >
  Weather conditions (warm temperatures combined with high humidity or recent rainfall) are
  favourable for black rot infection. This is contextual guidance, not a diagnosis.
  Consider protective fungicide applications during the pre-bloom and post-bloom periods,
  and remove berry mummies that may serve as inoculum sources.
```

**Threshold justification:**  
Temperature threshold (≥ 20 °C): OSU Extension factsheet PLPATH-FRU-24 states that black rot
infection requires warm temperatures in the 20–27 °C range. The 20 °C lower bound corresponds to
the documented minimum infection temperature.  
Humidity/precipitation threshold (≥ 80% RH or ≥ 0.2 mm): UC IPM grape guidelines and general
*G. bidwellii* infection literature specify that free moisture (rain, dew) or high humidity must
accompany warm temperatures for spore germination and infection. The 0.2 mm threshold represents
measurable precipitation (non-trace); 80% RH corresponds to conditions near dew-point that
facilitate leaf wetness.

**Rule logic (AND/OR):** ALL of `all_of` must be satisfied AND at least one of `any_of` must be
satisfied. This correctly models the documented dual requirement: temperature AND (humidity OR
moisture).

---

### Rule 2 — `grape_isariopsis_humid_wet_context`

```yaml
id: grape_isariopsis_humid_wet_context
disease_ids:
  - grape_isariopsis_leaf_blight
any_of:
  - field: humidity_percent
    operator: ">="
    value: 85
  - field: precipitation_mm
    operator: ">="
    value: 0.5
note: >
  Weather conditions (high humidity or recent rainfall) are favourable for isariopsis leaf blight
  development. This is contextual guidance, not a diagnosis. Consider improving canopy airflow,
  reducing overhead irrigation, and applying fungicide programmes recommended by a local extension
  advisor.
```

**Threshold justification:**  
NC State Extension (NC Grape Grower's Guide, Chapter 8) describes "high humidity and rainfall" as
the principal disease-favourable conditions for *P. vitis*. The 85% RH threshold represents the
upper end of persistently high humidity (above typical diurnal peaks); the 0.5 mm precipitation
threshold represents light-to-moderate rain (non-trace measurable rainfall). No temperature
constraint was applied because NC State extension does not define a narrow critical temperature
range specific to this pathogen.

**Rule logic (OR):** At least one of `any_of` must be satisfied. This correctly models "either
high humidity OR recent rainfall" as independent triggering conditions.

---

## 5. Recommendation Engine Behaviour

The existing recommendation engine (`src/crop_health/recommendations/engine.py`) evaluates rules
as follows:

```
rule matches  ⟺  all_of is empty OR all conditions in all_of match
                 AND
                 any_of is empty OR at least one condition in any_of matches
```

Both new rules correctly use this semantics:
- `grape_black_rot_warm_moist_context`: `all_of` (temperature) AND `any_of` (humidity OR precip)
- `grape_isariopsis_humid_wet_context`: no `all_of`; `any_of` (humidity OR precip)

When the classifier predicts `grape_black_rot` or `grape_isariopsis_leaf_blight` and weather
conditions satisfy the corresponding rule, the API response includes a contextual weather note
alongside the standard `general_guidance` from the knowledge base.

For `grape_esca`, the API returns knowledge base entries (`general_guidance`, `disease_information`)
without any weather contextualisation. This is the intended behaviour.

---

## 6. Test Coverage

### 6.1 `tests/test_knowledge_base.py` (mlenv) — 5 tests

| Test | Coverage |
|---|---|
| `test_all_disease_ids_present` | Confirms all 10 IDs load correctly |
| `test_grape_black_rot_fields` | Validates required fields for `grape_black_rot` |
| `test_grape_esca_fields` | Validates required fields for `grape_esca` |
| `test_grape_isariopsis_leaf_blight_fields` | Validates required fields for `grape_isariopsis_leaf_blight` |
| `test_all_entries_have_sources` | Confirms all 10 entries have at least one source with organization, title, url, accessed |

### 6.2 `tests/test_recommendations.py` (retail-forecast) — 7 new Grape tests (18 total)

| Test | Coverage |
|---|---|
| `test_grape_black_rot_recommendation_and_weather_rule` | Rule fires under warm + humid conditions |
| `test_grape_black_rot_weather_rule_does_not_trigger_when_cold_or_dry` | Rule correctly suppressed under cold/dry weather |
| `test_grape_isariopsis_leaf_blight_weather_rule` | Rule fires under high humidity |
| `test_grape_isariopsis_weather_rule_does_not_trigger_in_dry_conditions` | Rule correctly suppressed under dry conditions |
| `test_grape_esca_recommendation_and_weather_isolation` | Esca returns KB content; no weather rule fires |

### 6.3 `tests/test_prediction_api.py` (retail-forecast)

Updated `test_routing_grape_routes_to_grape_model`:
- **Before:** asserted `prediction_status == "unsupported_disease"`, `recommendation_status == "safe_fallback"`, `disease_information is None`
- **After:** asserts `prediction_status == "accepted"`, `recommendation_status == "available"`, `disease_information["id"] == "grape_black_rot"`, `general_guidance` count ≥ 4

This change reflects the correct post-Stage-33 behaviour: Grape diseases are now fully supported in the knowledge base, so the API no longer falls back.

---

## 7. Test Results

All tests confirmed passing after Stage 33 implementation.

### 7.1 mlenv (domain tests)

```
tests/test_knowledge_base.py           5 passed
tests/test_classifier_splits.py        3 passed
tests/test_classifier_grouped_splits.py  3 passed
tests/test_classifier_training_safety.py 7 passed
tests/test_explainability.py           4 passed
tests/test_severity.py                 5 passed
tests/test_deployment_config.py        4 passed
─────────────────────────────────────────────────
TOTAL                                 31 passed
```

### 7.2 retail-forecast (backend / API tests)

```
tests/test_prediction_api.py          32 passed
tests/test_recommendations.py         18 passed
tests/test_persistence.py              9 passed
tests/test_weather.py                  5 passed
─────────────────────────────────────────────────
TOTAL                                 64 passed
```

**Grand total: 95 tests, 0 failures, 0 errors.**

### 7.3 Ruff (linting)

```
All checks passed.
```

Files checked: `tests/test_knowledge_base.py`, `tests/test_recommendations.py`,
`tests/test_prediction_api.py`, `src/crop_health/knowledge_base/diseases.json` (JSON),
`configs/recommendation_config.yaml` (YAML).

---

## 8. Asset Integrity — Verified Unmodified

All trained model checkpoints, class mapping files, and split manifests remain byte-for-byte
identical to their post-training state.

| Asset | SHA-256 |
|---|---|
| `reports/grape_preparation/grape_classifier_split.csv` | `9978dff163509824a5af1457f5a597503cebbd284eaf928b62ccfa8066cafcb1` |
| `models/classifier/runs/tomato-potato-2026-11-17-b/efficientnet_b0_best.pt` | `ff89f20e59c8475481d3da56ceec93e3586eedcf984663ff26a88d6362ed8a27` |
| `models/classifier/runs/grape-2026-11-17-a/efficientnet_b0_best.pt` | `fdd8497e8ec7ac40de2f0aefd4eb498c2b83de4573e8e5e167c9cb88b0e17ae3` |
| `models/classifier/runs/tomato-potato-2026-11-17-b/class_mapping.json` | `1fd3233d017fe622281cbefbbd70db4e5c01b820fa8a585b515707e315ee423a` |
| `models/classifier/runs/grape-2026-11-17-a/class_mapping.json` | `39aa1f0d0b781b83c586897b79afa8ff49a627aea21fda17f48014b4ffb0a5c7` |

---

## 9. Knowledge Base — Final State

`src/crop_health/knowledge_base/diseases.json` now contains 10 entries in the following order:

| # | ID | Crop |
|---|---|---|
| 1 | `tomato_bacterial_spot` | tomato |
| 2 | `tomato_early_blight` | tomato |
| 3 | `potato_early_blight` | potato |
| 4 | `tomato_late_blight` | tomato |
| 5 | `potato_late_blight` | potato |
| 6 | `tomato_healthy` | tomato |
| 7 | `potato_healthy` | potato |
| 8 | `grape_black_rot` | grape |
| 9 | `grape_esca` | grape |
| 10 | `grape_isariopsis_leaf_blight` | grape |

Existing Tomato-Potato entries 1–7 were not modified.

---

## 10. Recommendation Config — Final State

`configs/recommendation_config.yaml` now contains 5 rules:

| # | Rule ID | Disease(s) | Trigger Logic |
|---|---|---|---|
| 1 | *(existing Tomato-Potato rule)* | tomato blight diseases | — |
| 2 | *(existing Tomato-Potato rule)* | potato blight diseases | — |
| 3 | *(existing Tomato-Potato rule)* | healthy classes | — |
| 4 | `grape_black_rot_warm_moist_context` | `grape_black_rot` | temp ≥ 20 °C AND (humidity ≥ 80% OR precip ≥ 0.2 mm) |
| 5 | `grape_isariopsis_humid_wet_context` | `grape_isariopsis_leaf_blight` | humidity ≥ 85% OR precip ≥ 0.5 mm |

`grape_esca` has no weather rule (intentional — see Section 3.2).

---

## 11. Limitations and Caveats

1. **Esca — no weather rule:** Esca is a wood-colonising trunk disease complex. No defensible
   short-term weather threshold exists that accurately predicts symptom expression. Users
   displaying suspected esca symptoms should consult a viticulture specialist or plant pathologist.

2. **Isariopsis leaf blight — source access:** The NC State Extension Grape Grower's Guide
   (Chapter 8) may require institutional or public university extension access in some regions.
   The URL provided is the canonical public NC State CES URL.

3. **Regional validity:** Disease pressure thresholds cited (temperature, humidity, precipitation)
   are drawn from US extension publications. Locally appropriate thresholds may vary by cultivar,
   region, and local climate. Users should consult regional extension advisors or plant pathologists
   for location-specific guidance.

4. **Knowledge base entries are descriptive, not diagnostic:** The `general_guidance` and weather
   contextualisation notes in the API response are informational aids. They are explicitly framed
   as contextual guidance and not as disease diagnoses.

5. **Scientific nomenclature note:** *Isariopsis clavispora* and *Phaeoisariopsis clavispora* are
   older synonyms for *Pseudocercospora vitis*. The teleomorph *Mycosphaerella personata* is cited
   in some literature. The entry uses the current accepted anamorph name *Pseudocercospora vitis*
   as the primary designation, with synonyms listed in the description.

---

## 12. Stage Boundaries

| Stage | Description | Status |
|---|---|---|
| 29 | Grape dataset preparation and manifest audit | ✅ Complete |
| 30 | Grape evaluator preparation | ✅ Complete |
| 31 | Grape holdout evaluation | ✅ Complete |
| 32 | Multi-crop model routing (FastAPI) | ✅ Complete |
| **33** | **Grape knowledge base and weather recommendations** | ✅ **Complete** |
| 34 | Frontend integration | ⬜ Not started |

> [!CAUTION]
> Stage 34 (frontend integration) has NOT been started. No frontend files were modified in
> Stage 33. Do not begin Stage 34 without explicit user approval.
