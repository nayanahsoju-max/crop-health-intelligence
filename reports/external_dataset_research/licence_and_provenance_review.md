# Licence and provenance review

**Checked:** 2026-11-16. Documentary assessment, not legal advice. Public access is not permission to redistribute. Recheck terms before acquisition, publication, deployment, or distribution of derived data/model weights.

## Existing local sources

| Source | Recorded terms/provenance | Treatment |
|---|---|---|
| PlantVillage Grape/Maize | Acquisition report pins HF metadata revision and upstream Git commit, records [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) and attribution to Mohanty, Hughes & Salathé (2016), DOI 10.3389/fpls.2016.01419. | Preserve attribution/license. Redistribution/adaptation must follow attribution and share-alike terms. Legacy PlantVillage root lacks local notice. |
| GVLiD v5 | Local package cites CC BY 4.0; attribution/count/metadata artifacts inconsistent. | Quality problems remain independent of rights. Withhold classifier use. |
| PlantSeg v3 | Photo source URLs present, but no uniform grant for individually sourced images established. | URLs/citations do not prove image reuse rights. Verify per-source permissions. |
| PlantDoc-Selected | No uniform local license evidence; aggregate may include third-party web images. | Do not assume blanket training or redistribution rights. Resolve per-image terms. |

## Candidate sources

- **NGLD v5:** [Mendeley](https://data.mendeley.com/datasets/8nnd2ypcv3/5) states CC BY 4.0. Preserve authors, DOI/version, link, attribution, and changes; cite the [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12210286/). Check downloaded item files and any third-party exceptions.
- **Portugal Grape:** [Zenodo record](https://zenodo.org/records/17343473) item-level image license not verified here. Paper OA license is not automatically the data license. Do not acquire/use until image and derivative/model rights are confirmed.
- **FieldVitis:** [Zenodo](https://zenodo.org/records/17307846) item license not populated in inspected metadata. Source component citations do not establish rights to all compiled images; provenance overlap also disqualifies it as an independent set.
- **ESCA field database:** [Mendeley v2](https://data.mendeley.com/datasets/3dr9r3w3jn/2) item license and whether images/masks share terms need verification.
- **AppleLeaf9:** [repository](https://github.com/JasonYangCode/AppleLeaf9) says CC BY 4.0, but components derive from PlantVillage, ATLDSD and Plant Pathology. Corpus license cannot override upstream restrictions. Check each component grant.
- **Plant Pathology 2020:** [Kaggle rules](https://www.kaggle.com/competitions/plant-pathology-2020-fgvc7/rules) govern data use and sharing. Do not mirror/redistribute. Verify whether project, teammates and a public demo/checkpoint fit the rules.
- **Rice Leaf Bacterial and Fungal v2:** [Mendeley record](https://data.mendeley.com/datasets/hx6f852hw4/2) states CC BY 4.0. Attribute authors and DOI. Package includes original and augmented files; preserve distinction and verify third-party rights.
- **Cassava Kaggle:** [competition rules](https://www.kaggle.com/competitions/cassava-leaf-disease-classification/rules) limit use to academic/noncommercial purposes and sharing. May conflict with a public app, dataset or checkpoint. Obtain institution-level approval on intended use before acquisition.
- **Makerere Cassava Dataverse:** [official DOI](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T4RB0B) reported CC0 in catalog references, but reconcile official file-level terms and payload; third-party counts/labels conflict.
- **WFD:** [portal](https://wfd.sysbio.ru/) requires requested access and documents research/noncommercial terms. Confirm terms for weights/publication.
- **Wheat stripe rust masks:** [Zenodo](https://zenodo.org/records/21672928) item license unclear; do not acquire before permission.

## Provenance record required per source

Preserve title, author, version/revision, DOI, landing/download URL, date, archive and per-file SHA-256, source labels/folders, split/IDs, license text and citation. Record any filtering/conversion. Keep distinct licenses per source. Permission to download, train, redistribute images, publish a derived dataset, share weights, and host a service are separate questions. PlantVillage share-alike duties do not determine the rights of other sources or by themselves resolve model-weight distribution.
