# Prioritized dataset download plan

No dataset was downloaded. Links, reported counts and access notes checked 2026-11-16. Every acquisition below requires separate approval.

| Order / purpose | Dataset and original page | Reported classes/count | Size/access | License gate and reason |
|---|---|---|---|---|
| 1 Grape classification | [NGLD v5 Mendeley](https://data.mendeley.com/datasets/8nnd2ypcv3/5) | H1254, downy966, powdery406, bacterial spot100; 2,726 | Exact archive bytes to verify | CC BY 4.0 stated. Adds field downy/powdery; defer bacterial spot. Check hashes/labels/metadata. |
| 2 Rice classification | [Rice Leaf Bacterial and Fungal v2](https://data.mendeley.com/datasets/hx6f852hw4/2) | 1,701 originals, eight folders; 1,486 after excluding 215 insect-pest Rice Hispa | Package reported 3.43 GB and includes augmented content; isolate original photos only | CC BY 4.0 stated. Preserve originals separately from augmentation. |
| 3 Apple classification | [Original PlantVillage GitHub RGB](https://github.com/spMohanty/PlantVillage-Dataset), [HF source](https://huggingface.co/datasets/mohanty/PlantVillage) | H1645, scab630, black rot621, cedar rust275 reported | Selective folders; byte total not verified; do not download full archive | CC BY-SA 3.0. Preserve attribution/share-alike. |
| 4 Grape external evaluation | [Portugal Zenodo](https://zenodo.org/records/17343473) | H1122, downy1006, Esca complex1000, powdery1126, erineum mite1013; 5,267 | Record/paper; bytes to confirm | Do not acquire until image data license confirmed. Useful independent sites; no Black rot/Isariopsis. |
| 5 Conditional Cassava | [Kaggle data](https://www.kaggle.com/competitions/cassava-leaf-disease-classification/data), [rules](https://www.kaggle.com/competitions/cassava-leaf-disease-classification/rules) | 21,397 total reported, five labels; class counts not verified | Kaggle account/rules acceptance; bytes unknown | Academic/non-commercial and sharing conditions may conflict with app/checkpoint. Require institutional compatibility. Alternative [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T4RB0B) has CC0 claim but unresolved payload classes/count. |
| 6 Optional Apple evaluation | [Plant Pathology 2020 Kaggle](https://www.kaggle.com/competitions/plant-pathology-2020-fgvc7/data) | 1,821 labeled train, 1,821 hidden-label test | Gated; size unknown | Rules restrict sharing; use only if no source-family overlap with training/AppleLeaf9. |
| 7 Optional distinct Grape task | [ESCA Mendeley v2](https://data.mendeley.com/datasets/3dr9r3w3jn/2) | 1,483 vine-scale images; 128 non-leaf masks | Mendeley; size unknown | Verify item rights. Whole-vine task, not leaf severity. |

Do not reacquire GVLiD or FieldVitis for training; do not fetch complete PlantVillage for Apple; do not acquire third-party PlantSeg mirrors while local mask rights remain unresolved.

After approval: inspect manifest/archive first; preserve original archive, source folder names, citations, license and IDs; record version/date/bytes/checksums; decode every image; count per original class; compare SHA-256 against every local dataset; review pHash/source families; retain location/session/plant IDs; form leakage groups before any manifest. No merge, new manifest, or training is included in this plan.
