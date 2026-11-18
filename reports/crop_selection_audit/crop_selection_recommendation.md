# Crop selection audit and recommendation

**Audit date:** 2026-11-16 (Asia/Kolkata)  
**Scope:** Read-only inventory and evidence review of all local image datasets. No images, labels, manifests, review decisions, source code, or configurations were changed.  
**Recommendation:** Tomato, Potato, and Grape, using 11 classes for the first defensible experiment. This is a recommendation for a candidate experiment; it does not certify the source folder labels as expert diagnoses.

## Executive recommendation

1. **Tomato — strongest readiness.** Four classes have substantial PlantVillage coverage, and the existing Stage 20B group-aware split has been revalidated for its seven-class scope. Tomato has the best available label/data volume combination, but source-style controlled backgrounds limit field generalization.
2. **Potato — retain with a class-imbalance caveat.** Its two disease classes have 1,000 unique source images apiece. Healthy has only 152 unique images, so performance on healthy leaves will be less precisely estimated. It shares the validated Stage 20B split.
3. **Grape — recommended as the third crop.** PlantVillage provides four well-populated, readable classes without internal exact duplicates. The source train/test assignments and leaf IDs are preserved, but only the three diseased classes have direct leaf-map IDs. A new group-aware split is required, and the one exact PlantVillage–PlantSeg match has a disease-name mapping concern already recorded in the human review register.

The recommended initial set is **11 classes** (4 Tomato + 3 Potato + 4 Grape), with **12,827 unique PlantVillage image contents** before any future group or human-review exclusions. This is a better-supported set than forcing a 12–15 class target. Grape's 4 classes add more useful breadth than Bell pepper's 2 classes; Potato is retained because its existing split is substantially more defensible than the available Maize split.

**Readiness qualification:** A credible internal classifier experiment is feasible after Grape receives a new grouped train/validation/test assignment and the original Stage 20B seven-class split is preserved. The available data does not yet support a strong independent field evaluation for all three crops. PlantDoc can provide limited external Tomato/Potato evaluation only after overlap, label, and split issues are handled; there is no usable local independent four-class Grape test source.

## Scope and method

The six data roots present under `data/` are `PlantVillage`, `PlantVillage-Grape`, `PlantVillage-Maize`, `plantsegv3`, `PlantDoc-Selected`, and `GVLiD-v5`. The full saved Stage 3 fingerprint inventory contains **76,397 assets**: 64,939 photos and 11,458 PlantSeg masks. All 76,397 paths were present during this audit; the saved full decode/hash scan reported **zero unreadable or hash-only items and zero fingerprint errors**. Counts below distinguish source records from unique SHA-256 image contents. Masks are never counted as classifier images.

The source-label inventory and earlier audit reports are screening evidence, not expert diagnosis. Near-duplicate perceptual-hash matches remain candidates unless a human review has confirmed them. They are not subtracted from the counts below.

Useful supporting records:

- [Stage 3 readiness summary](../dataset_quality_audit/dataset_readiness_summary.md)
- [Exact duplicate report](../dataset_quality_audit/exact_duplicate_report.md)
- [Grouping and leakage report](../dataset_quality_audit/grouping_and_leakage_report.md)
- [Label conflict report](../dataset_quality_audit/label_conflict_report.md)
- [Stage 20B original seven-class split](../data_manifest/plantvillage_classifier_split.csv)
- [PlantVillage Grape/Maize acquisition report](../plantvillage_expansion/acquisition_report.md)
- [PlantVillage selective-download/source metadata plan](../plantvillage_expansion/selective_download_plan.md)
- [GVLiD acquisition report](../gvlid_v5_acquisition_report.md)
- [Human-review decision register](../dataset_quality_audit/human_review/review_decision_register.csv)

## Dataset inventory and quality findings

| Local source | Classifier-photo records | Unique SHA-256 photo contents | Masks | Readability | Source conditions / splits | Main quality and provenance finding |
|---|---:|---:|---:|---|---|---|
| `data/PlantVillage/` | 41,276 | 20,624 | 0 | 0 unreadable | Controlled-background leaf photos; source folders include train/test/validation partitions for original 7-class scope, while Bell pepper and added Tomato folders have no preserved split in the current local fingerprint inventory | 20,624 contents are mirrored under top-level and nested trees (20,610 double copies, 14 four-copy groups). Count each SHA once. Seven-class Stage 20B split is integrity-consistent; other folders need a new audit/split. |
| `data/PlantVillage-Grape/` | 4,062 | 4,062 | 0 | 0 unreadable | Controlled-background source; original train/test metadata preserved | No internal exact duplicates. One exact cross-source match with PlantSeg grape leaf spot. Grape healthy has fallback IDs; diseased classes have direct leaf-map IDs. Source split must not be assumed group-safe. |
| `data/PlantVillage-Maize/` | 3,852 | 3,852 | 0 | 0 unreadable | Controlled-background source; original train/test metadata preserved | No internal exact duplicates. All leaf IDs are generated filename fallbacks, not physical-leaf evidence; known fallback IDs cross source train/test in healthy, Northern Leaf Blight, and Gray Leaf Spot. |
| `data/plantsegv3/images/` | 11,458 | 11,056 | 0 | 0 unreadable | Mostly web/source-page images, generally field-like and variable backgrounds; original Training/Validation/Test folders | 384 within-label exact image groups; 123 exact content groups span disease folder labels. 871/8,758 source URL families cross partitions and 185 exact groups cross original partitions. Photos are separate from 11,458 paired masks. Not a clean classifier split. |
| `data/PlantDoc-Selected/` | 814 | 807 | 0 | 0 unreadable | Field-style, variable backgrounds; train/test folders | Six internal exact groups (five cross-label); five of six cross train/test. No reliable leaf/capture/source-family ID. 28 exact cross-source groups with PlantSeg, including seven conflicting label screens. Local use is external-only after de-overlap and label checks. |
| `data/GVLiD-v5/` | 3,477 | 2,409 | 0 | 0 unreadable | Grape imagery with vineyard metadata; no trusted source partition | 446 exact duplicate groups, 1,344 folder/`Disease_Type` disagreements, and two cross-label exact groups. All 28 vineyard IDs are connected through duplicate relations. Dataset remains expressly unapproved for classifier training. |

Across photos there are **21,489 exact duplicate groups** and 43,647 records in those groups; much of the total comes from the PlantVillage mirror. There are **29 cross-source exact photo groups**: 28 PlantDoc–PlantSeg, one PlantVillage-Grape–PlantSeg. The 29 groups and their human decisions are in the linked Stage 3 audit/register. Stage 3 also identified 1,340 dHash candidate pairs (139 cross-source). Those are not confirmed duplicates and are not excluded from the counts. Exact group handling must be global across any sources used together.

### PlantVillage source counts by class

These counts are readable, unique SHA contents within the named source folder after collapsing the nested mirror. The legacy PlantVillage folder itself has duplicated paths, so raw file records are nearly twice these amounts. For the recommended Tomato and Potato source classes, these counts are the available content pool; Stage 20B uses 8,779 manifest rows and 8,763 group IDs for its selected seven classes.

| Crop | Original source folder / class | Source records | Unique usable photo contents | Split and concern |
|---|---|---:|---:|---|
| Tomato | `Tomato_healthy` | 3,182 | 1,585 | Stage 20B grouped split |
| Tomato | `Tomato_Bacterial_spot` | 4,254 | 2,127 | Stage 20B grouped split |
| Tomato | `Tomato_Early_blight` | 2,000 | 1,000 | Stage 20B grouped split |
| Tomato | `Tomato_Late_blight` | 3,818 | 1,901 | Stage 20B grouped split |
| Tomato | `Tomato_Leaf_Mold` | 1,904 | 952 | Not in Stage 20B; new label/split audit needed |
| Tomato | `Tomato_Septoria_leaf_spot` | 3,542 | 1,771 | Not in Stage 20B; new label/split audit needed |
| Tomato | `Tomato_Spider_mites_Two_spotted_spider_mite` | 3,352 | 1,676 | Not in Stage 20B; new label/split audit needed |
| Tomato | `Tomato__Target_Spot` | 2,808 | 1,404 | Not in Stage 20B; new label/split audit needed |
| Tomato | `Tomato__Tomato_YellowLeaf__Curl_Virus` | 6,416 | 3,208 | Not in Stage 20B; new label/split audit needed |
| Tomato | `Tomato__Tomato_mosaic_virus` | 746 | 373 | Not in Stage 20B; new label/split audit needed |
| Potato | `Potato___healthy` | 304 | 152 | Stage 20B grouped split; notably small class |
| Potato | `Potato___Early_blight` | 2,000 | 1,000 | Stage 20B grouped split |
| Potato | `Potato___Late_blight` | 2,000 | 1,000 | Stage 20B grouped split |
| Bell pepper | `Pepper__bell___healthy` | 2,956 | 1,478 | No current Stage 20B split; new grouped audit required |
| Bell pepper | `Pepper__bell___Bacterial_spot` | 1,994 | 997 | No current Stage 20B split; new grouped audit required |

There are no within-PlantVillage cross-label exact-hash groups in the scanned source. These are folder labels; they should not be represented as pathologist-verified diagnoses.

### Acquired PlantVillage Grape and Maize classes

All 7,914 RGB images are readable, and every image is unique by SHA within its acquired source. Source provenance records the pinned Hugging Face revision and original GitHub raw/color source, CC BY-SA 3.0 attribution/share-alike material, source labels and filenames. Train/test split lists and the source leaf map were retained. The original source split is not automatically leakage-safe.

| Crop | Exact original class folder | Images / unique SHA | Train | Test | Grouping evidence and concerns |
|---|---|---:|---:|---:|---|
| Grape | `Grape___healthy` | 423 | 323 | 100 | All 423 IDs are filename-derived fallbacks, not verified leaf IDs. |
| Grape | `Grape___Black_rot` | 1,180 | 1,012 | 168 | Direct source leaf-map IDs available. |
| Grape | `Grape___Esca_(Black_Measles)` | 1,383 | 1,099 | 284 | Direct source leaf-map IDs available. |
| Grape | `Grape___Leaf_blight_(Isariopsis_Leaf_Spot)` | 1,076 | 872 | 204 | Direct leaf-map IDs; one exact match in PlantSeg `grape leaf spot`, mapping unresolved. Stage 5 decision retains the PlantVillage record and does not count PlantSeg as additional training content. |
| Maize | `Corn_(maize)___healthy` | 1,162 | 912 | 250 | Fallback IDs; 175 IDs occur in both original splits. |
| Maize | `Corn_(maize)___Common_rust_` | 1,192 | 975 | 217 | Preserve trailing underscore; fallback IDs are not physical-leaf evidence. |
| Maize | `Corn_(maize)___Northern_Leaf_Blight` | 985 | 765 | 220 | Fallback IDs; 22 IDs cross original splits. |
| Maize | `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` | 513 | 406 | 107 | Fallback IDs; 19 IDs cross original splits. |

The PlantVillage expansion is documented as CC BY-SA 3.0 and includes attribution. The original `data/PlantVillage/` legacy subset has no local license/provenance document in its root; the broader PlantVillage upstream licensing was previously researched, but preserve the distinction that the legacy local subset lacks its own bundled notice. Review the source terms and attribution when distributing derived material.

### PlantDoc, PlantSeg, and GVLiD class coverage

**PlantDoc-Selected** contains 814 records / 807 unique image contents, no healthy class, and no Grape or Maize coverage. Its local mapped screening classes are: Bell pepper leaf 61, Bell pepper leaf spot 71; Potato early blight 117 and late blight 105; Tomato bacterial spot 110, early blight 88, late blight 111, and Septoria leaf spot 151 records / 150 unique contents. The Bell pepper folder labels are not sufficient to establish the two proposed canonical classes. It should not supply training labels or be used as a naive held-out test set. No uniform license statement was located in the local selected directory, so local rights/provenance are unresolved.

**PlantSeg** has 11,458 classifier photos and exactly 11,458 associated lesion masks; masks are not additional photos. The photo collection has 11,056 unique SHA contents. Below are photo records / within-label unique SHA for relevant target crops; none of these disease-only groups provides healthy class coverage:

| Crop | PlantSeg disease photo counts (records / unique SHA) | Classifier relevance |
|---|---|---|
| Bell pepper | Bacterial spot 76/71; blossom end rot 112/109; frogeye leaf spot 31/30; powdery mildew 28/27 | Disease mask coverage exists for these folders, but no healthy images. Bacterial spot is a candidate source only; mapping and grouped split still need review. |
| Grape | Black rot 122/122; downy mildew 280/278; leaf spot 91/91; grapevine leafroll 71/71 (metadata crop is Grapevine) | No healthy. “Grape leaf spot” is not established equivalent to the PlantVillage Isariopsis Leaf blight class. Masks are not classifier evidence or label verification. |
| Corn | Gray leaf spot 107/107; Northern leaf blight 130/130; rust 177/177; smut 202/202 | No healthy; names do not by themselves establish exact canonical label equivalence, and source URLs cross split boundaries. |
| Potato | Early blight 126/125; late blight 117/117 | No healthy; exact/near cross-source and internal label conflicts constrain use. |
| Tomato | Bacterial leaf spot 109/109; early blight 187/187; late blight 163/163; leaf mold 156/156; mosaic virus 63/63; Septoria leaf spot 130/130; yellow leaf curl virus 93/93 | Disease-only; useful segmentation research after provenance review, not an automatic expansion of classifier data. |

PlantSeg metadata includes source-page URLs and original partitions, but URLs are source-family proxies, not verified physical-leaf identity. 871 source URL families span the original partitions. Its disease folders include many labels that are not in the five-crop proposal or lack a corresponding healthy class. A local, uniform license grant was not located; source-level rights need resolution before redistribution or inclusion in a released classifier dataset.

**GVLiD v5** is not approved for training. Its raw folders contain Healthy 1,109, Black rot 808, Esca 888, Leaf blight 672; all 3,477 decode, but duplicates reduce to only 2,409 unique SHA contents (Black rot 99, Esca 888, Healthy 1,093, Leaf blight 331). There are 446 exact duplicate groups, including two Black rot/Esca conflicts; 1,344 of 3,477 records disagree between folder and `Disease_Type`. A strict folder/metadata agreement screen yielded no Leaf blight contents, so GVLiD cannot currently support a trustworthy four-class grape set. Of 437 duplicate groups with vineyard IDs, 437 cross different vineyard IDs; the exact-duplicate graph links all 28 vineyard IDs, making vineyard-only partitioning unreliable. Local source says CC BY 4.0, but package README attribution and bundled statistics/checksums are inconsistent. This source is excluded from the candidate classifier counts.

## Crop-by-crop suitability

Ratings combine useful image volume, class breadth, balance, label/provenance concerns, split quality, healthy coverage, field coverage, and license/documentation. “High” is relative to the current local alternatives and still subject to grouped split work.

| Rank / crop | Rating | Evidence-based assessment |
|---|---|---|
| 1. Tomato | **High for a controlled-source internal experiment** | Four established PlantVillage classes with 1,000–2,127 unique contents/class and healthy coverage. Stage 20B grouping and integrity checks cover these classes. Multiple additional Tomato folders exist but are excluded from the initial set until a new audit. PlantDoc/PlantSeg give field-like context but their class labels, overlaps and splits are not clean enough to mix into training. |
| 2. Potato | **Moderate to high, with healthy-class limitation** | Two disease classes each have 1,000 unique contents and share the verified Stage 20B split. Healthy has 152 unique images (about 6.6:1 imbalance versus either disease class). PlantDoc/PlantSeg can only be external or separately reviewed because of duplicate cross-partition and label conflicts. |
| 3. Grape | **Moderate; viable after new grouped split** | Four PlantVillage classes with 423–1,383 images/class and no internal exact duplicates; healthy is smaller but present. Diseased leaf IDs offer useful source grouping. Healthy uses fallbacks. One exact PlantSeg mapping overlap is explicitly unresolved; keep the PlantVillage source record, avoid adding the PlantSeg duplicate. GVLiD is unsuitable pending label repair; no clean local external four-class evaluation set. |
| 4. Bell pepper | **Low to moderate; only two clean candidate classes** | PlantVillage has balanced healthy (1,478) and bacterial spot (997), but this is a binary set and no Stage 20B split applies. PlantSeg has small disease-only field/mask coverage and PlantDoc's pepper labels are ambiguous. A new global duplicate/source-family split is necessary. It is a reasonable fallback if the final product needs pepper specifically, but offers less disease breadth than Grape. |
| 5. Maize | **Moderate image volume, low split readiness** | Four PlantVillage classes with 513–1,192 contents/class and healthy coverage. However, all source IDs are fallback IDs, and three classes have known train/test identifier overlap; those values do not prove leaves but invalidate assuming the released split is independent. No usable independent local external set exists. A new hash/family/group audit is required before reliable evaluation. |
| Other PlantSeg-only crops | **Low for the final classifier with current sources** | PlantSeg contains disease-only photo/mask folders across 35 crop metadata values, generally without healthy examples and with source-family leakage, repeated images, mixed-label exact groups, and unresolved uniform licensing. They do not presently offer a balanced multi-class classifier dataset or defensible independent test. Per-crop inventory is in the appendix. |

**Verified facts** above are counts and metadata findings from the local files and saved audits. **Unresolved** items include whether visually similar but non-identical images are the same physical leaf, whether source labels are biologically correct, whether all PlantSeg source-page images may be reused, and whether fallback identifiers correspond to physical leaves. The recommendation does not assume those uncertainties away.

## Recommended 11-class structure

“Available” and “recommended usable” below mean the count of readable, unique SHA contents in the selected source folder before a new Grape group split. There are no within-source exact duplicates in the recommended Grape source. The single PlantVillage–PlantSeg exact overlap is handled by using the PlantVillage record and not pooling the PlantSeg copy. Final counts may decline if subsequent source-family or near-duplicate review excludes or quarantines records. No unreviewed perceptual-hash candidate is subtracted here.

| Crop | Disease class | Available images | Recommended usable images (provisional) | Source dataset | Concerns |
|---|---|---:|---:|---|---|
| Tomato | Healthy | 1,585 | 1,585 | PlantVillage | Controlled background; source folder label, not expert diagnosis. Stage 20B applies. |
| Tomato | Bacterial spot | 2,127 | 2,127 | PlantVillage | Controlled background; Stage 20B applies. |
| Tomato | Early blight | 1,000 | 1,000 | PlantVillage | Controlled background; Stage 20B applies. |
| Tomato | Late blight | 1,901 | 1,901 | PlantVillage | Controlled background; Stage 20B applies. |
| Potato | Healthy | 152 | 152 | PlantVillage | Smallest class; uncertain class-level precision; Stage 20B applies. |
| Potato | Early blight | 1,000 | 1,000 | PlantVillage | Controlled background; Stage 20B applies. |
| Potato | Late blight | 1,000 | 1,000 | PlantVillage | Controlled background; Stage 20B applies. |
| Grape | Healthy | 423 | 423 | PlantVillage-Grape | Source IDs are fallback values; new grouped split needed. |
| Grape | Black rot | 1,180 | 1,180 | PlantVillage-Grape | Direct leaf-map IDs; new grouped split needed. |
| Grape | Esca (Black Measles) | 1,383 | 1,383 | PlantVillage-Grape | Direct leaf-map IDs; new grouped split needed. |
| Grape | Leaf blight (Isariopsis Leaf Spot) | 1,076 | 1,076 | PlantVillage-Grape | One exact PlantSeg match has unresolved label equivalence; use the approved PlantVillage record only. |
| **Total** | **11 classes** | **12,827** | **12,827 provisional** |  | Counts can change after Grape grouping and near-duplicate review. |

The seven Tomato/Potato image counts above total 8,765 unique source contents. The existing Stage 20B CSV has 8,779 rows and 8,763 source-group IDs: its rows are the historical selected manifest records, whereas the table reports unique source image content after collapsing mirrored paths. The audit revalidated all manifest paths/hashes and found no group crossing train/validation/test. Preserve that manifest for the exact seven classes; do not silently replace it with the unique-count table.

## Why the alternatives are not in the top three

- **Maize:** attractive four-class coverage and more balanced counts than Potato, but the current evidence does not establish source leaf identity. The source train/test split has known fallback-ID crossovers in three classes. It may become a good fourth crop after rebuilding groups and making a new split, but the current evidence is weaker than Potato's Stage 20B split.
- **Bell pepper:** its two PlantVillage classes are balanced and materially cleaner than current field-source alternatives, but it only supports healthy versus bacterial spot. No existing grouped split covers it. PlantSeg masks and PlantDoc field images do not currently establish compatible, complete labels. Prefer Grape for a broader, four-class experiment.
- **GVLiD Grape:** withheld because repeated/conflicting content and the 1,344 metadata disagreements undermine the four-class labels; vineyard IDs do not isolate duplicates.
- **PlantSeg-only crops/classes:** do not use as extra classifier classes solely because folders exist. Most lack healthy counterparts, masks are not classifier samples, source-label conflicts/group leakage exist, and a uniform local reuse license was not found.
- **PlantDoc:** reserve for external evaluation only after overlap filtering and manual label review; do not include it in development training or treat its existing test folder as independent.

## Required work before the experiment

1. Retain the Stage 20B manifest unchanged for its seven classes; preserve its source labels and class mapping.
2. Build a separate Grape grouping audit. Use direct leaf-map identities for the three diseased classes; union exact SHA groups globally; include source-family/filename and reviewed near-duplicate components. Treat Grape healthy fallback IDs as unverified and report that limitation. Make a new reproducible stratified group split (target about 70/15/15 where group counts allow) without using original test labels to guide training.
3. Do not add the PlantSeg exact copy for Grape leaf blight until source nomenclature is resolved. It remains a segmentation/source review record, not another classifier image.
4. Reconcile source manifests, folder labels, file paths, image readability, source revision, and redistribution attribution. Maintain the CC BY-SA 3.0 attribution/share-alike notices for PlantVillage derivatives.
5. Report group counts and per-class counts in each split, not just image percentages. Audit duplicate components across train/validation/test and across any source boundaries.
6. Treat PlantDoc as an external set only after all overlapping SHA groups are removed from whichever development source is used, conflicting-label records are excluded pending verification, and its file-level labels are checked. Do not call this a complete Grape external test.
7. Keep GVLiD and unreviewed PlantSeg photos out of supervised training. Segmentation masks may be evaluated as separate mask resources only after label/provenance review; they are not classifier photos.
8. After the data split is frozen, evaluate only once on the held-out test partition. No model metrics are asserted by this audit.

## Overall conclusion

**Recommend Tomato, Potato, and Grape, with 11 initial classes and 12,827 provisional unique source images.** This is a credible basis for a controlled-source classifier experiment once Grape is independently group-split and all source/duplicate boundaries are enforced. It is not yet evidence of field-ready performance: the principal selected data are PlantVillage controlled-background images, Potato healthy is small, Grape has no clean local external four-class set, and source folder labels have not undergone expert diagnostic validation. If the requirement is a credible *field-generalization* experiment with independent external evaluation for all three crops, the available local datasets do not yet meet that bar; acquire/approve such data or narrow the claim.

## Appendix A — PlantSeg crop inventory

These are **image-photo counts only**, in records / unique SHA contents within that disease folder. Annotation masks are excluded. PlantSeg has no healthy image class for the listed crops. Counts and source disease names are reproduced from the local `Metadatav2.csv` and Stage 3 fingerprint inventory; identical photos may occur under different source labels, so the unique count is not a claim that those labels are correct.

| Metadata crop | PlantSeg disease folders (records / unique SHA) |
|---|---|
| Apple | black rot 83/83; mosaic virus 89/89; rust 139/139; scab 258/258 |
| Banana | anthracnose 71/69; black leaf streak 167/159; bunchy top 157/142; cigar end rot 60/57; cordana leaf spot 55/54; panama disease 63/63 |
| Basil | downy mildew 63/63 |
| Bean | halo blight 56/56; mosaic virus 58/58 |
| Bell pepper | bacterial spot 76/71; blossom end rot 112/109; frogeye leaf spot 31/30; powdery mildew 28/27 |
| Blueberry | anthracnose 42/40; botrytis blight 36/36; mummy berry 47/46; rust 43/43; scorch 43/42 |
| Broccoli | alternaria leaf spot 65/62; downy mildew 29/29; ring spot 16/16 |
| Cabbage | alternaria leaf spot 61/61; black rot 131/123; downy mildew 84/84 |
| Carrot | alternaria leaf blight 60/60; cavity spot 72/72; cercospora leaf blight 19/19 |
| Cauliflower | alternaria leaf spot 54/53; bacterial soft rot 36/34 |
| Celery | anthracnose 29/29; early blight 36/36 |
| Cherry | leaf spot 106/106; powdery mildew 33/33 |
| Citrus | canker 390/388; greening disease 133/133 |
| Coffee | berry blotch 118/113; black rot 7/7; brown eye spot 20/19; leaf rust 159/159 |
| Corn | gray leaf spot 107/107; northern leaf blight 130/130; rust 177/177; smut 202/202 |
| Cucumber | angular leaf spot 182/182; bacterial wilt 108/108; powdery mildew 188/188 |
| Eggplant | cercospora leaf spot 60/60; phomopsis fruit rot 46/46; phytophthora blight 33/33 |
| Garlic | leaf blight 92/92; rust 106/106 |
| Ginger | leaf spot 25/25; sheath blight 68/68 |
| Grape | black rot 122/122; downy mildew 280/278; leaf spot 91/91 |
| Grapevine | leafroll disease 71/71 |
| Lettuce | downy mildew 84/84; mosaic virus 39/39 |
| Maple | tar spot 114/114 |
| Peach | anthracnose 13/13; brown rot 173/170; leaf curl 182/182; rust 8/8; scab 78/75 |
| Plum | bacterial spot 16/16; brown rot 81/80; pocket disease 57/57; pox virus 33/32; rust 34/34 |
| Potato | early blight 126/125; late blight 117/117 |
| Raspberry | fire blight 34/31; gray mold 40/38; leaf spot 18/18; yellow rust 37/36 |
| Rice | blast 83/83; sheath blight 76/76 |
| Soybean | bean rust 233/231; bacterial blight 91/90; brown spot 71/65; downy mildew 153/141; frog eye leaf spot 238/219; mosaic 117/115 |
| Squash | powdery mildew 182/182 |
| Strawberry | anthracnose 58/58; leaf scorch 39/39 |
| Tobacco | blue mold 60/58; brown spot 66/66; frogeye leaf spot 28/27; mosaic virus 41/41 |
| Tomato | bacterial leaf spot 109/109; early blight 187/187; late blight 163/163; leaf mold 156/156; mosaic virus 63/63; Septoria leaf spot 130/130; yellow leaf curl virus 93/93 |
| Wheat | bacterial leaf streak (black chaff) 117/116; head scab 319/279; leaf rust 132/129; loose smut 215/191; powdery mildew 271/262; Septoria blotch 232/206; stem rust 148/140; stripe rust 358/332 |
| Zucchini | bacterial wilt 70/69; downy mildew 44/44; powdery mildew 213/203; yellow mosaic virus 95/95 |

## Appendix B — License and use documentation found locally

- **PlantVillage Grape/Maize expansion:** acquisition materials record CC BY-SA 3.0, source attribution, pinned revision, and share-alike instructions. Retain these notices for any redistributed adaptation.
- **Legacy PlantVillage directory:** no local license/provenance file was found at the directory root. The upstream PlantVillage license was researched previously; retain attribution and confirm the applied notice in any distribution package.
- **GVLiD:** Mendeley record and preserved package state CC BY 4.0. Attribution/citation inconsistencies and the package's stale statistics remain data-quality problems independent of the license statement.
- **PlantDoc-Selected and PlantSeg:** no uniform local license evidence was found for the selected/local collections. The PlantSeg metadata's source URLs do not themselves establish reuse permission for each photo. Resolve individual/source license terms before redistribution or classifier inclusion.


