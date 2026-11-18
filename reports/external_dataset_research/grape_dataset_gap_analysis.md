# Grape dataset gap analysis

**Verified 2026-11-16.** The mandatory baseline remains Healthy, Black rot, Esca (Black Measles), and Leaf blight (Isariopsis Leaf Spot).

## Existing coverage

| Source | Counts and content | Suitability |
|---|---|---|
| PlantVillage-Grape | Healthy423, Black rot1180, Esca1383, Isariopsis leaf blight1076; 4,062 readable 256-square photos | Four-class controlled baseline; direct leaf-map IDs for three diseases, fallback IDs for healthy; make a new grouped split. One exact match with PlantSeg grape leaf spot is unresolved; retain PV record per Group 1 decision. CC BY-SA 3.0. |
| PlantSeg | Black rot122, downy280 (278 unique), generic leaf spot91, grapevine leafroll71 photo/mask records | Candidate masks; no healthy or Esca; generic leaf spot is not shown to equal Isariopsis. Rights/mask semantics require review. |
| PlantDoc-Selected | No local Grape class | Full PlantDoc is only a lead; known exact overlap means not automatically independent. |
| GVLiD v5 | Healthy1109, Black rot808, Esca888, Leaf blight672 records | Not approved for classifier use: 1,344 folder/metadata disagreements, conflicting duplicate groups, vineyard entanglement. |

Local support: [coverage](local_dataset_coverage.md), [GVLiD report](../gvlid_v5_acquisition_report.md), [decision register](../dataset_quality_audit/human_review/review_decision_register.csv).

## Candidate datasets

**NGLD v5 — recommended first acquisition for complementary field classes.** [Mendeley record](https://data.mendeley.com/datasets/8nnd2ypcv3/5) and [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12210286/) report 2,726 256×256 mobile photos from farms in Niphad, India, Jan 2023–Jan 2025: healthy1,254, downy mildew966, powdery mildew406, bacterial leaf spot100. Record states CC BY 4.0. No masks or verified plant IDs/split. Prioritize healthy/downy/powdery only after label, payload, hash and rights verification. Bacterial spot is small and etiologically uncertain.

**Portugal vineyard dataset — prospective independent site evaluation, license unresolved.** [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13098524/) reports 5,267 images from four Northern Portugal vineyards, 2024–25: healthy1,122, downy1,006, Esca complex1,000, powdery1,126, erineum mite1,013. High- and reduced-resolution variants; timestamps and some GPS/cultivar data permit site grouping. Visual labels were second-reviewed, not lab-confirmed. [Zenodo landing page](https://zenodo.org/records/17343473) item-level image license could not be verified here. No masks, Black rot or Isariopsis. Esca complex needs mapping review.

**FieldVitis v2 — do not treat as independent.** [Zenodo](https://zenodo.org/records/17307846), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12660085/): 555 field-like images, healthy158, Black rot39, Esca200, leaf blight158. Compiled from ESCA, PlantDoc, Mendeley Grape Disease and manual crops; known Black rot/Esca errors and questionable leaf-blight examples. The local source overlap and unpopulated item license field block independent evaluation/acquisition.

**ESCA field database.** [Mendeley v2](https://data.mendeley.com/datasets/3dr9r3w3jn/2), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10294005/): 1,483 vine-scale images, five cultivars, two years, 14 vineyard blocks. 128 masks relate to symptomatic shoots/bunches/background, not leaf lesions. Potential separate whole-vine screening task, not leaf classifier/severity. Confirm item license and exact mask correspondence.

## Segmentation and severity

PlantSeg candidate pairs exist for Black rot122, downy280, generic leaf spot91. Verify lesion pixels versus whole-leaf masks, pair correspondence and labels. No local compatible Esca or Isariopsis lesion-mask class is established. The [LDD grape paper](https://arxiv.org/abs/2206.10192) reports 1,092 images and 17,706 polygons across organ/disease categories but mixes internal, Kaggle and web-scraped content and inconsistent lesion/organ granularity; rights unresolved. [WG ISD](https://github.com/thsant/wgisd) segments fruit bunches, not leaf lesions. Grape severity remains unavailable/provisional without validated target-disease lesion masks and expert validation.

## Knowledge base sources

- Black rot: [Penn State Extension](https://extension.psu.edu/grape-disease-black-rot) and [grape fungal disease management](https://extension.psu.edu/fundamental-considerations-for-managing-fungal-diseases-of-grapevines) cover symptoms, weather and prevention.
- Esca: [APS review](https://apsjournals.apsnet.org/doi/full/10.1094/PDIS-04-17-0512-FE) documents its disease-complex nature.
- Isariopsis: [APS grape disease list](https://www.apsnet.org/edcenter/resources/commonnames/Pages/Grape.aspx) associates Isariopsis leaf spot with Pseudocercospora vitis (syn. Isariopsis clavispora). Generic “leaf spot” is not an acceptable mapping.
- Downy/powdery: use Penn State grape-specific fungal disease reference above; curate crop-specific current sources before production recommendations.

## Gap and recommendation

Keep the four PlantVillage labels as controlled baseline. Add NGLD field healthy/downy/powdery only after acquisition audit. Consider Portugal as an external site evaluation after image rights, label compatibility, duplicates and group separation are verified. No clean four-class Grape field test exists. No verified Esca/Isariopsis lesion masks or healthy leaf masks exist locally. See [download plan](grape_dataset_download_plan.md).
