# Local dataset coverage audit

**Verified:** 2026-11-16. Read-only review of local manifests, acquisition records and the saved Stage 3 fingerprint inventory. The saved scan covers 76,397 assets: 64,939 photos and 11,458 masks; all paths were present and decodable, with zero recorded errors. SHA-256 counts are unique file contents, not verified physical leaves. Perceptual-hash matches remain candidates. Masks are not classifier images.

## Inventory

| Source | Photo records / unique SHA | Conditions and labels | Split/group evidence | Qualification |
|---|---:|---|---|---|
| PlantVillage | 41,276 paths; 20,624 canonical contents | Controlled-background, all 256×256; Tomato 10 labels, Potato 3, Bell pepper 2 | Stage 20B applies only to original seven Tomato/Potato labels: 8,779 rows, 8,763 groups, no group crosses partitions | Legacy root lacks local license notice; labels are source-folder labels |
| PlantVillage-Grape | 4,062 / 4,062 | Controlled, four classes | Source split/leaf map preserved; only three diseased classes have direct IDs; new grouped split required | One exact match to PlantSeg generic grape leaf spot; unresolved mapping. CC BY-SA 3.0 recorded |
| PlantVillage-Maize | 3,852 / 3,852 | Controlled, four classes | Fallback IDs; train/test collisions in healthy 175, NLB 22, gray spot 19 | New grouped audit needed; CC BY-SA 3.0 |
| PlantSeg photos | 11,458 / 11,056 within disease folders | Diverse web/field-like dimensions; disease-only | 8,758 URL families; 871 across partitions; 185 exact groups cross existing partitions | 123 exact content groups span disease folder labels; source URLs do not establish reuse rights |
| PlantSeg masks | 11,458 / 11,451 unique mask contents | PNG masks paired by metadata | Seven duplicate-mask groups | Candidate lesion masks; verify semantics/pairing, no healthy masks, uniform license not found |
| PlantDoc-Selected | 814 / 807 | Variable field/web-like photos; Tomato, Potato, Bell pepper selection | No physical-leaf ID; five of six internal exact groups cross train/test | 28 PlantDoc–PlantSeg exact groups, seven conflicting labels; no uniform local license |
| GVLiD v5 | 3,477 / 2,409 | Field grape; 1080×1080 | Vineyard IDs unreliable across duplicate links; 437/446 duplicate groups cross vineyard IDs | 1,344 folder/metadata disagreements, conflicting Black rot/Esca groups; excluded from classifier training |

PlantVillage formats are mostly JPG; acquired Grape/Maize images are 256×256 JPEG. PlantSeg photos range 65–8256 by 52–5504; PlantDoc 143×137 to 6000×4000; GVLiD 1080×1080. Saved readability scan reports zero unreadable images.

## Local class counts

Counts are unique source-folder image contents; mirrored paths collapsed. Tomato: healthy 1,585; bacterial spot 2,127; early blight 1,000; late blight 1,901; leaf mold 952; Septoria 1,771; spider mites 1,676; target spot 1,404; yellow leaf curl 3,208; mosaic 373. Potato: healthy 152; early blight 1,000; late blight 1,000. Bell pepper: healthy 1,478; bacterial spot 997.

PlantVillage-Grape: healthy 423; Black rot 1,180; Esca 1,383; Isariopsis leaf blight 1,076. PlantVillage-Maize: healthy 1,162; common rust 1,192; Northern Leaf Blight 985; Gray Leaf Spot 513. All eight expansion classes are SHA-unique internally; source train/test assignments are provenance, not leakage-safe final splits.

PlantSeg photos (records / unique SHA within folder; masks are separate): Tomato bacterial109/109, early187/187, late163/163, leaf mold156/156, mosaic63/63, Septoria130/130, yellow curl93/93. Potato early126/125, late117/117. Grape black rot122/122, downy280/278, generic leaf spot91/91, grapevine leafroll71/71. Corn gray107/107, NLB130/130, rust177/177, smut202/202. Bell pepper bacterial spot76/71, blossom-end rot112/109, frogeye31/30, powdery28/27. Apple black rot83, mosaic89, rust139, scab258. Rice blast83, sheath blight76. These are photos with candidate paired masks, not validated lesion ground truth. Generic grape leaf spot is not proven equivalent to Isariopsis.

PlantDoc selected counts: Tomato bacterial110, early88, late111, Septoria151 records/150 unique; Potato early117, late105; Bell pepper leaf61, leaf spot71. These are not clean independent class totals.

GVLiD folder records / unique SHA: Healthy 1,109/1,093; Black rot 808/99; Esca 888/888; Leaf blight 672/331. Do not count these as eligible classifier data.

## Leakage, provenance and licence

Stage 3 found 29 exact cross-source photo groups (28 PlantDoc–PlantSeg, one Grape PlantVillage–PlantSeg). Groups 1–20 have decisions in the preserved review register; unresolved items remain unresolved. The 1,340 dHash pairs (139 cross-source) are candidates, not confirmed duplicates. Stage 20B remains the validated split only for its original seven classes. PlantDoc and PlantSeg have no uniform local reuse license; GVLiD asserts CC BY 4.0 with documentation inconsistencies. Grape/Maize acquisition records CC BY-SA 3.0 and attribution. Details: [readiness](../dataset_quality_audit/dataset_readiness_summary.md), [exact duplicates](../dataset_quality_audit/exact_duplicate_report.md), [near duplicates](../dataset_quality_audit/near_duplicate_candidate_report.md), [label conflicts](../dataset_quality_audit/label_conflict_report.md), [grouping](../dataset_quality_audit/grouping_and_leakage_report.md), [split strategy](../dataset_quality_audit/recommended_17_class_split_strategy.md), [human review](../dataset_quality_audit/human_review/README.md), [decision register](../dataset_quality_audit/human_review/review_decision_register.csv), [PV acquisition](../plantvillage_expansion/acquisition_report.md).

Counts derive from the saved image fingerprint inventory, source inventories and acquisition reports. Do not infer source-folder diagnoses, group identity from fallback IDs, or permission from source URLs.
