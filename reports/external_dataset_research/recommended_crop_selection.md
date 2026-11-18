# Recommended crop selection

**Provisional recommendation: six crops and 27 candidate classes.** Keep the mandatory Tomato, Potato and Grape. Add Apple, Rice and Cassava. Cassava is conditional on resolving dataset terms and official payload discrepancies. If its Kaggle restrictions do not fit the intended deployment/weight sharing and the Dataverse alternative cannot be validated, stop at five crops and 24 classes; do not substitute a weakly supported crop.

## Ranked selection

| Rank | Crop | Readiness |
|---:|---|---|
| 1 | Tomato | Fixed; high internal readiness. Large local set and Stage 20B grouped split for its original scope. Mostly controlled-background data; field validation limited. |
| 2 | Potato | Fixed; moderate-high. Two diseases have 1,000 unique PV contents each; healthy only 152. Stage 20B applies. |
| 3 | Grape | Fixed; moderate. Four PV classes; new group split required. Field sources are partial/rights limited; GVLiD excluded. |
| 4 | Rice | Add. One reported field/diverse-background source supplies seven disease/healthy classes (1,486 originals after excluding insect pest); PlantSeg has two candidate mask categories. No verified group IDs or independent test. |
| 5 | Apple | Add. Four PV baseline classes, PlantSeg masks, orchard field leads; AppleLeaf9 is composite and overlapping, PP2020 has competition restrictions. |
| 6 | Cassava | Conditional add. Strong field-source lead (21,397 reported, five labels) but sharing limits and per-class counts not verified. CC0 alternative has version/class discrepancies. |

Reserve candidates: Wheat WFD (2,414 reported expert-annotated photos, but multilabel and request/non-commercial terms); Bell pepper (only two balanced controlled classes, no clean field healthy set); Banana/Citrus/Soybean (PlantSeg disease folders without a verified complete healthy-plus-disease licensed classification collection).

## Proposed class list and evidence

The recommended 27-class target is Tomato4 + Potato3 + Grape6 + Apple4 + Rice7 + Cassava3. The 3 Cassava classes are healthy, CBSD and CMD; exclude CGM because it is a mite pest rather than a disease, and defer CBB until etiologic label criteria and scope are verified.

Counts below are existing unique local counts or candidate source-reported counts. New-source counts are not deduplicated against local data; exact hashes and grouping may reduce usable records. “TBD” is deliberately not an estimate.

| Crop | Class | Reported/local available | Provisional usable | Source and concern |
|---|---|---:|---:|---|
| Tomato | Healthy | 1,585 | 1,585 | Local PlantVillage; controlled; Stage20B |
| Tomato | Bacterial spot | 2,127 | 2,127 | Local PlantVillage; controlled; Stage20B |
| Tomato | Early blight | 1,000 | 1,000 | Local PlantVillage; controlled; Stage20B |
| Tomato | Late blight | 1,901 | 1,901 | Local PlantVillage; controlled; Stage20B |
| Potato | Healthy | 152 | 152 | Local PlantVillage; small class; Stage20B |
| Potato | Early blight | 1,000 | 1,000 | Local PlantVillage; Stage20B |
| Potato | Late blight | 1,000 | 1,000 | Local PlantVillage; Stage20B |
| Grape | Healthy | 423 | 423 | Local PV Grape; controlled; new split |
| Grape | Black rot | 1,180 | 1,180 | Local PV Grape; folder label not expert-verified |
| Grape | Esca / Black Measles | 1,383 | 1,383 | Local PV Grape; field Esca-complex mapping must be reviewed |
| Grape | Isariopsis leaf blight | 1,076 | 1,076 | Local PV Grape; do not pool generic PlantSeg leaf spot |
| Grape | Downy mildew | 966 reported | TBD | NGLD v5; field; overlap/labels to audit |
| Grape | Powdery mildew | 406 reported | TBD | NGLD v5; smaller class; overlap/labels to audit |
| Apple | Healthy | 1,645 reported | TBD | Proposed PV Apple selective subset, not local |
| Apple | Scab | 630 reported | TBD | Proposed PV Apple; verify source payload |
| Apple | Black rot | 621 reported | TBD | Proposed PV Apple; verify source payload |
| Apple | Cedar apple rust | 275 reported | TBD | Proposed PV Apple; smallest class |
| Rice | Healthy | 157 reported | TBD | Mendeley v2; original photos only |
| Rice | Bacterial leaf blight | 180 reported | TBD | Verify disease-label criteria |
| Rice | Brown spot | 267 reported | TBD | Mendeley v2 originals |
| Rice | Blast | 305 reported | TBD | Mendeley v2; PlantSeg mask lead |
| Rice | Leaf scald | 189 reported | TBD | Mendeley v2 originals |
| Rice | Narrow brown leaf spot | 117 reported | TBD | Smallest Rice class |
| Rice | Sheath blight | 271 reported | TBD | Mendeley v2; PlantSeg mask lead |
| Cassava | Healthy | Per-class count unverified | TBD | Kaggle source conditional on intended-use rights |
| Cassava | Brown streak disease (CBSD) | Per-class count unverified | TBD | Kaggle source; validate class-specific expert labels |
| Cassava | Mosaic disease (CMD) | Per-class count unverified | TBD | Kaggle source; validate class-specific expert labels |

## Split and evaluation

- Preserve Stage 20B exactly as is for its original seven classes. Any future expanded split must be separately versioned and approved.
- Grape: use direct leaf-map IDs for the three disease folders, flag healthy fallback IDs as unverified, union global SHA groups and source families, and add reviewed near-duplicate groups. Create a separate grouped split.
- New datasets: group by physical leaf/plant, capture session, vineyard/farm/site where reliable; union exact content globally; review pHash candidates; keep all source-family variants together. Do not call image-level random splits leakage-safe.
- PlantDoc remains external-only after human review and cross-source overlap filtering. Portugal Grape and Plant Pathology Apple are candidate external sources only after rights, labels and overlap are established.

## Conclusion

A credible staged experiment is feasible, but not a field-ready claim. Tomato/Potato have the strongest existing split; Grape requires its own split and lacks a clean four-class external field set. New Rice/Apple/Cassava sources need acquisition, licensing and group audits. No new manifest or model was created.
