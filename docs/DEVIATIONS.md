# Deviations from the original spec

Each entry lists the spec section, what changed, why, and when it was approved. The report's methods section draws on this file.

| # | Spec section | Change | Reason | Approved |
|---|---|---|---|---|
| 1 | 3.1, 5.2 | The disease arm is strictly `idiopathic pulmonary fibrosis`. `pulmonary fibrosis` and `interstitial lung disease` go to a side file. | The broader labels mix other fibrotic ILDs into the IPF arm. | 2026-11-04 |
| 2 | 3.4, 5.5, 5.6 | `cell_type` comes from a curated Cell Ontology → medium-level mapping table (about 20–30 types), committed to the repo. | Census `cell_type` is each author's own label, and granularity differs between studies. HLCA label transfer would be circular. | 2026-11-04 |
| 3 | 5.5 | scANVI is trained with disease-specific states (aberrant basaloid, profibrotic macrophage, pathologic fibroblast, transitional AT2) folded into their parent types. | Otherwise the biology checks pass trivially for scANVI. Flagged in the report. | 2026-11-04 |
| 4 | 5.7A | The study classifier uses donor-grouped CV, because a held-out study can't be predicted. Disease separability is scored inside an anchor study that has both conditions, using donor-grouped CV. | Leave-one-study-out is undefined for the study label, and for disease in the confounded design. | 2026-11-04 |
| 5 | 5.7A, 5.7C | **Donor-level AUROC is the primary disease metric** and cell-level AUROC is secondary. Enrichment uses a donor-level Mann-Whitney test, not a cell-level Fisher test. | Cells from the same donor aren't independent (pseudoreplication). | 2026-11-04 |
| 6 | 10 | If sanity check 10.1 (unintegrated is best on disease) fails, the result is treated as informative, not as a bug. | Study shift can stop the unintegrated classifier transferring to held-out data. | 2026-11-04 |
| 7 | 5.7B | DE concordance is framed as *cell-assignment fidelity*. | DE always uses raw counts; integration only changes how cells are grouped. | 2026-11-04 |
| 8 | 5.5, 5.6, 5.7 | BBKNN is scored on graph-based metrics only. Embedding metrics are NA for BBKNN. | BBKNN outputs a corrected kNN graph, not an embedding. | 2026-11-04 |
| 9 | 5.7C | Programs that require a gene to be absent are scored as positive markers minus the absent marker: basaloid minus KRT5, transitional AT2 minus SFTPC. | `sc.tl.score_genes` has no negative markers. | 2026-11-04 |
| 10 | 2 | **Aberrant basaloid cells are TP63 *positive*** (the spec said "TP63 low"). They also express LAMB3 and LAMC2, and lack KRT5 and KRT15. | Adams et al. 2020 Sci Adv (PMC7439502): "these cells express the basal cell markers TP63, KRT17, LAMB3, and LAMC2 but do not express other established basal markers such as KRT5 and KRT15". | 2026-11-04 (checked against the full text) |
| 11 | 3 | Prefer 10x 3′ assays. If fewer than 4 studies with both IPF and control donors remain, stop and present the options. | Full-length protocols would be a confounder of their own. | 2026-11-04 |
| 12 | 5.8 | HVGs are recomputed separately for each stress-test design. | Avoids information leaking between designs. | 2026-11-04 |
| 13 | 5.3 | Doublets are called with `sc.pp.scrublet` per donor. | Standalone `scrublet` is no longer maintained, and Census has no consistent library ID. | 2026-11-04 |
| 14 | 5.5 | Scanorama is set to `dimred=50` explicitly. | Its default is 100. | 2026-11-04 |
| 15 | 7 | Compute runs on VT ARC instead of a laptop. CPU steps go to Owl `normal_q`, GPU steps to Falcon A30 with L40S fallback. | Falcon rejects jobs that don't request a GPU. | 2026-11-04 (infrastructure) |
| 16 | 3.1 | **Census 2025-11-08 has no `idiopathic pulmonary fibrosis` label.** A strict IPF diagnosis is taken from author columns in the source h5ads: HLCA `lung_condition == "IPF"`, Natri 2024 `Diagnosis == "IPF"`. Census labels these cells `pulmonary fibrosis` or `interstitial lung disease`. | That is the only place a strict IPF diagnosis is recorded. | Pending |
| 17 | 3.4 | The batch key is the author `study` column, not `dataset_id`. | HLCA is one `dataset_id` that holds many studies. | Pending |

## GEO accession check (spec 3.2)

Checked against GEO series records and their linked PubMed entries on 2026-11-04. All four are correct.

| Accession | GEO title | PMID | Paper |
|---|---|---|---|
| GSE135893 | Single-cell RNA-sequencing reveals profibrotic roles of distinct epithelial and mesenchymal lineages in pulmonary fibrosis | 32832598 | Habermann et al. 2020 Sci Adv |
| GSE136831 | IPF Cell Atlas | 32832599 | Adams et al. 2020 Sci Adv |
| GSE122960 | Single-Cell Transcriptomic Analysis of Human Lung Reveals Complex Multicellular Changes During Pulmonary Fibrosis II | 30554520 | Reyfman et al. 2019 AJRCCM |
| GSE128033 | Proliferating SPP1/MERTK-expressing macrophages in idiopathic pulmonary fibrosis | 31221805 | Morse et al. 2019 ERJ |
