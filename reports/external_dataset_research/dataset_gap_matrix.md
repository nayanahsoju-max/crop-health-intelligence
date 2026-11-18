# Dataset gap matrix

Status checked 2026-11-16. Partial means records exist but label quality, rights, grouping or independence remain unresolved. Mask coverage is not validated severity ground truth.

| Crop | Classification | Healthy | Disease segmentation | Field images | Independent evaluation | Knowledge references |
|---|---|---|---|---|---|---|
| Tomato | Complete baseline PlantVillage labels; field-source labels need review | Complete PV | Partial PlantSeg paired folders; semantics/rights unresolved | Partial PlantDoc/PlantSeg | Partial PlantDoc only after human review and overlap removal | Available; curate authoritative source per disease |
| Potato | Complete PV healthy/early/late | Complete, only 152 unique | Partial PlantSeg early/late candidates | Partial PlantDoc/PlantSeg | No validated independent set; PlantDoc overlaps/conflicts | Available from extension/pathology sources |
| Grape | Partial: PV four controlled; NGLD proposed additions; GVLiD excluded | PV complete; field partial | Partial PlantSeg black rot/downy/generic spot; no verified Esca/Isariopsis lesions | Partial NGLD/Portugal/ESCA with limits | Missing complete four-class field set; Portugal is partial candidate pending terms | Available APS/Penn State |
| Apple | Partial: PV four proposed; AppleLeaf9 composite | PV and field candidates | Partial PlantSeg folders; validate pairs/rights | Partial AppleLeaf9/PP2020 | Possible PP2020 only after rules and source overlap check | Available University of Minnesota |
| Rice | Partial: one reported multiclasse source, seven candidate classes | Partial, 157 reported | Partial PlantSeg blast/sheath candidates | Partial Bangladesh field/indoor images | Missing verified independent source | Available APS rice references |
| Cassava | Partial and conditional; Kaggle or inconsistent Dataverse alternative | Reported, exact count pending | Missing verified lesion masks | Partial farmer field images | Missing verified independent source | Uganda Ministry/IAEA references available; curate per disease |
| Maize (not selected) | Four controlled PV classes | Complete PV | Partial PlantSeg disease masks; no healthy | Partial, labels/grouping concerns | No reliable independent four-class local set | Curate if later selected |
| Bell pepper (reserve) | Two PV classes; PlantDoc ambiguous | Complete PV | Partial PlantSeg masks | Partial PlantDoc/PlantSeg | Missing clean independent set | Curate if selected |

## Priority gaps

1. Grape: field Black rot and Isariopsis-compatible labels, validated Esca/Isariopsis lesion masks, and a full four-class external field set.
2. Apple: licensed field source with distinct plant/site grouping; PlantSeg mask rights and pair validation.
3. Rice: source group IDs, external evaluation and validated lesion masks.
4. Cassava: compatible rights and official payload/version, then independent test and segmentation ground truth.
5. All selected diseases: current authoritative sources and supported weather conditions before knowledge-base recommendations. Folder labels do not establish treatment guidance.
