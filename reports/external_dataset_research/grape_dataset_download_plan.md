# Grape dataset download plan

No downloads were performed. Counts are published/source-reported as checked 2026-11-16; reconcile actual file payload and rights before use.

| Priority | Original source | Reported classes/counts | Role | Gate |
|---|---|---|---|---|
| 1 | [NGLD v5 Mendeley](https://data.mendeley.com/datasets/8nnd2ypcv3/5), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12210286/) | Healthy1254, downy966, powdery406, bacterial spot100; 2,726 JPEGs | Complementary field classification | CC BY 4.0 stated. Confirm item terms, original labels, checksums and exact overlap. Defer bacterial spot pending etiology review. |
| 2 | [Portugal grape Zenodo](https://zenodo.org/records/17343473), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13098524/) | Healthy1122, downy1006, Esca complex1000, powdery1126, erineum mite1013; total5267 | Prospective independent field/site test | Item image license unresolved; do not acquire until confirmed. Group by site/time; compare high/resized copies. No Black rot/Isariopsis. |
| 3 | [ESCA v2 Mendeley](https://data.mendeley.com/datasets/3dr9r3w3jn/2), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10294005/) | 1,483 vine-scale images; 128 shoot/bunch/background masks | Optional separate vine screening | Verify item rights and mask pairing; not leaf lesion severity. |
| Hold | [FieldVitis v2 Zenodo](https://zenodo.org/records/17307846), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12660085/) | H158, Black rot39, Esca200, leaf blight158; 555 total | Provenance audit only, not independent evaluation | Item license unresolved; source overlap and label errors. |

After approval, keep source-specific folders and archive unchanged; preserve all metadata, IDs, filenames, exact labels and licence/citation. Record version, DOI, retrieval date, bytes and SHA-256. Validate readable counts, then compare exact hashes against every local dataset. Treat near-duplicate distances as review candidates. Preserve location/vineyard/session IDs. Union exact duplicate components globally before grouping; no cross-partition content. Do not mix original Stage 20B manifest or GVLiD. No Grape dataset provides full-four-class independent field evaluation, and no verified Esca/Isariopsis lesion-mask source has been found.
