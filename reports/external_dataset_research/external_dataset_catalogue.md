# External dataset research catalogue

Research checked 2026-11-16. Counts are source-reported and not local file verification. No downloads occurred. See [structured comparison](dataset_comparison.csv), [licence review](licence_and_provenance_review.md), and [download plan](download_plan.md).

## Grape

- **NGLD v5** — [Mendeley](https://data.mendeley.com/datasets/8nnd2ypcv3/5), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12210286/): 2,726 field/mobile images; H1,254, downy966, powdery406, bacterial spot100; CC BY 4.0 stated. No masks or verified IDs. Proposed complementary classification; validate label criteria and exact overlap.
- **Portugal vineyard dataset** — [Zenodo](https://zenodo.org/records/17343473), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13098524/): 5,267 field photos from four locations; H1,122, downy1,006, Esca complex1,000, powdery1,126, erineum mite1,013. Timestamps/some GPS can support site groups. No masks; item image licence unresolved. Potential external evaluation only after terms and hashes.
- **FieldVitis v2** — [Zenodo](https://zenodo.org/records/17307846), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12660085/): 555 mixed-source images, H158/Black rot39/Esca200/leaf blight158. Includes local-source overlap and reported label errors. Do not treat as independent.
- **ESCA field database** — [Mendeley v2](https://data.mendeley.com/datasets/3dr9r3w3jn/2), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10294005/): 1,483 vine-scale images, 128 shoot/bunch/background masks. Not leaf lesion segmentation; license verify.
- Local PlantSeg provides candidate Black rot122, downy280 and generic leaf spot91 photo-mask pairs; no healthy or Esca. Generic leaf spot is not automatically Isariopsis. GVLiD is withheld after metadata/duplicate conflicts.

## Apple

- **PlantVillage Apple subset (proposed)** — original [GitHub](https://github.com/spMohanty/PlantVillage-Dataset), [HF dataset](https://huggingface.co/datasets/mohanty/PlantVillage): reported folders healthy1,645, scab630, black rot621, cedar apple rust275. Controlled RGB, no masks or group IDs, CC BY-SA 3.0 upstream. Counts must be confirmed from exact pinned release before acquisition.
- **AppleLeaf9** — [official repository](https://github.com/JasonYangCode/AppleLeaf9), [paper](https://doi.org/10.3390/agronomy12112784): 14,582 images across nine classes, assembled from PlantVillage, Apple Tree Leaf Disease Segmentation Dataset and Plant Pathology data. Reported class imbalance; project says CC BY 4.0 but component rights must be checked. Field and controlled sources mixed; not independent and source overlap inherent.
- **Plant Pathology 2020 FGVC7** — [Kaggle](https://www.kaggle.com/competitions/plant-pathology-2020-fgvc7/data), [paper](https://bsapubs.onlinelibrary.wiley.com/doi/abs/10.1002/aps3.11390): 1,821 labeled train + 1,821 hidden-label test, orchard/field photos; healthy/multiple disease/rust/scab. Competition rules limit sharing. Potential independent evaluation only if no source-family overlap with AppleLeaf9/training and rules permit.
- Local PlantSeg apple photos/mask folders: black rot83, mosaic89, rust139, scab258. No healthy; license and mask-pair/semantics review needed.

## Rice

- **Rice Leaf Bacterial and Fungal Disease Dataset v2** — [Mendeley](https://data.mendeley.com/datasets/hx6f852hw4/2), [paper](https://www.sciencedirect.com/science/article/pii/S2352340925007012): 1,701 original photos reported; BLB180, brown spot267, healthy157, blast305, leaf scald189, narrow brown leaf spot117, Rice Hispa215, sheath blight271. Excluding the insect pest gives 1,486 photos for seven disease/healthy labels. Field and indoor varied backgrounds; Bangladesh. CC BY 4.0 stated. No verified leaf IDs/split/masks; archive includes augmentation derivatives—use originals only.
- Local PlantSeg has blast83 and sheath blight76 candidate photo-mask records; no healthy. Rights and overlap unresolved.

## Cassava

- **Cassava Leaf Disease Classification** — [Kaggle data](https://www.kaggle.com/competitions/cassava-leaf-disease-classification/data), [rules](https://www.kaggle.com/competitions/cassava-leaf-disease-classification/rules), [paper](https://arxiv.org/abs/1908.02900): 21,397 field images reported, five labels (healthy, CBB, CBSD, CGM, CMD), Uganda farmer images and expert labeling. Per-class counts not verified from authoritative source here. Academic/non-commercial and sharing limits; no masks or verified plant IDs. Conditional only.
- **Makerere Cassava Image Dataset** — [official Harvard Dataverse DOI](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T4RB0B): reported as CC0 in catalogue, but versions/counts/classes conflict across sources (9,103 vs 9,430; three vs five classes). Do not use third-party counts as authoritative. Reconcile official payload before use.

## Other candidates and reserves

| Crop | Evidence / decision |
|---|---|
| Wheat | [WFD portal](https://wfd.sysbio.ru/) and [paper](https://doi.org/10.3390/plants10081500): 2,414 expert-annotated images, H299, leaf rust655, powdery277, Septoria185, stem rust591, yellow rust457; multi-label tags and 4.84 GB reported. Request access; research/noncommercial conditions. Not directly exclusive-class softmax data. Reserve. |
| Wheat segmentation | [NWRD Zenodo](https://zenodo.org/records/21672928), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10422341/): 100 field images with binary stripe-rust masks; one site/season, item licence unclear. |
| Bell pepper | Existing PV H1,478 and bacterial spot997 unique controlled images; PlantSeg masks in four folders, no healthy; PlantDoc “leaf/leaf spot” labels ambiguous. Two-class reserve, no clean field external test. |
| Banana/Citrus/Soybean | PlantSeg-only disease folders (no healthy) and no complete, licensed, verified multi-class image source selected. Not recommended as current add-ons. |

## Knowledge references

Authoritative starting points: [APS grape diseases](https://www.apsnet.org/edcenter/resources/commonnames/Pages/Grape.aspx), [Penn State grape black rot](https://extension.psu.edu/grape-disease-black-rot), [APS rice diseases](https://www.apsnet.org/edcenter/resources/commonnames/Pages/Rice.aspx), [APS rice blast](https://www.apsnet.org/edcenter/pdlessons/Pages/RiceBlast.aspx), [APS sheath blight](https://www.apsnet.org/edcenter/pdlessons/Pages/RiceSheath.aspx), [Minnesota apple scab](https://extension.umn.edu/plant-diseases/apple-scab), [Minnesota cedar-apple rust](https://extension.umn.edu/plant-diseases/cedar-apple-rust), and [Uganda Ministry of Agriculture](https://www.agriculture.go.ug/) cassava resources. Disease-specific current weather thresholds and management references must be curated before the knowledge base is populated.
