"""Step 01: CELLxGENE Census exploration and (later) download.

Exploration reads cell metadata only (no expression) so we can choose studies before pulling data.
"""

from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger("signalkeep")


def _value_filter(cfg: dict, primary: bool) -> str:
    c = cfg["census"]
    return f"tissue_general == '{c['tissue_general']}' and is_primary_data == {primary}"


def resolve_census_version(version: str) -> dict:
    import cellxgene_census

    desc = cellxgene_census.get_census_version_description(version)
    return {"requested": version, "release_build": desc.get("release_build"), "soma_uri": desc.get("soma", {}).get("uri")}


def read_lung_obs(cfg: dict, census_version: str, primary: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (lung obs metadata, census dataset table) for the pinned Census version."""
    import cellxgene_census

    c = cfg["census"]
    with cellxgene_census.open_soma(census_version=census_version) as census:
        obs = (
            census["census_data"][c["organism"]]
            .obs.read(value_filter=_value_filter(cfg, primary), column_names=c["obs_columns"])
            .concat()
            .to_pandas()
        )
        datasets = census["census_info"]["datasets"].read().concat().to_pandas()
    for col in obs.columns:
        if obs[col].dtype == object:
            obs[col] = obs[col].astype("category")
    return obs, datasets


def label_condition(obs: pd.DataFrame, cfg: dict) -> pd.Series:
    d = cfg["disease"]
    cond = pd.Series("other", index=obs.index, dtype=object)
    cond[obs["disease"].isin(d["ipf_labels"])] = "IPF"
    cond[obs["disease"].isin(d["control_labels"])] = "control"
    cond[obs["disease"].isin(d["side_labels"])] = "side"
    return cond


def summarize_disease_labels(obs: pd.DataFrame) -> pd.DataFrame:
    g = obs.groupby(["disease", "disease_ontology_term_id"], observed=True)
    out = pd.DataFrame({
        "n_cells": g.size(),
        "n_donors": g.apply(lambda x: x[["dataset_id", "donor_id"]].drop_duplicates().shape[0]),
        "n_datasets": g["dataset_id"].nunique(),
    }).reset_index()
    return out.sort_values("n_cells", ascending=False)


def summarize_datasets(obs: pd.DataFrame, datasets: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """One row per dataset that has any IPF or side-label cells: donors/cells per condition and assay mix."""
    obs = obs.assign(condition=label_condition(obs, cfg).values)
    relevant = obs.loc[obs["condition"].isin(["IPF", "side"]), "dataset_id"].unique()
    if len(relevant) == 0:
        return pd.DataFrame()
    sub = obs[obs["dataset_id"].isin(relevant)]
    preferred = set(cfg["assay"]["preferred"])

    rows = []
    for ds, x in sub.groupby("dataset_id", observed=True):
        row = {"dataset_id": ds}
        for cond in ["IPF", "control", "side", "other"]:
            xc = x[x["condition"] == cond]
            row[f"{cond}_donors"] = xc["donor_id"].nunique()
            row[f"{cond}_cells"] = len(xc)
        ic = x[x["condition"].isin(["IPF", "control"])]
        row["assays"] = "; ".join(f"{a} ({n})" for a, n in ic["assay"].value_counts().items() if n > 0)
        row["frac_10x3p"] = round(ic["assay"].isin(preferred).mean(), 3) if len(ic) else 0.0
        row["suspension"] = "; ".join(sorted(ic["suspension_type"].astype(str).unique()))
        row["n_cell_types"] = ic["cell_type"].nunique()
        row["other_diseases"] = "; ".join(sorted(x.loc[x["condition"] == "other", "disease"].astype(str).unique()))
        rows.append(row)
    summ = pd.DataFrame(rows)

    meta = datasets[["dataset_id", "collection_name", "dataset_title", "collection_doi"]]
    summ = summ.merge(meta, on="dataset_id", how="left")
    k = cfg["study_selection"]["min_donors_per_condition"]
    summ["has_both"] = (summ["IPF_donors"] >= k) & (summ["control_donors"] >= k)
    summ["has_both_10x3p"] = summ["has_both"] & (summ["frac_10x3p"] >= 0.99)
    front = ["dataset_id", "collection_name", "dataset_title", "has_both", "has_both_10x3p",
             "IPF_donors", "IPF_cells", "control_donors", "control_cells"]
    return summ[front + [c for c in summ.columns if c not in front]].sort_values(
        ["has_both", "IPF_donors"], ascending=False)


# --- Source h5ad metadata (author columns Census does not expose) -----------------------------------
# Census 2025-11-08 has no "idiopathic pulmonary fibrosis" label. IPF is identifiable only from author
# columns inside source h5ads (HLCA `lung_condition`, Natri 2024 `Diagnosis`). These readers fetch only the
# requested obs columns via S3 range requests; the expression matrix is never read.


def read_source_obs(census_version: str, dataset_id: str, columns: list[str]) -> pd.DataFrame:
    import h5py
    import s3fs
    from anndata.io import read_elem

    import cellxgene_census

    uri = cellxgene_census.get_source_h5ad_uri(dataset_id, census_version=census_version)["uri"]
    fs = s3fs.S3FileSystem(anon=True)
    with fs.open(uri.removeprefix("s3://"), "rb", block_size=8 * 2**20, cache_type="bytes") as fh, \
            h5py.File(fh, "r") as f:
        return pd.DataFrame({c: read_elem(f["obs"][c]) for c in columns})


def summarize_source_studies(obs: pd.DataFrame, src: dict, cfg: dict) -> pd.DataFrame:
    """Per author-study table: IPF/control donors and cells (primary cells only), assays, 3'-only flag."""
    obs = obs[obs["is_primary_data"].astype(bool)]
    cond = obs[src["condition_col"]].astype(str)
    obs = obs.assign(condition=cond.map({src["ipf_value"]: "IPF", **{v: "control" for v in src["control_values"]}}))
    preferred = set(cfg["assay"]["preferred"])
    k = cfg["study_selection"]["min_donors_per_condition"]
    rows = []
    for study, x in obs.groupby(src["study_col"], observed=True):
        ic = x[x["condition"].isin(["IPF", "control"])]
        if ic.empty:
            continue
        r = {"source": src["name"], "dataset_id": src["dataset_id"], "study": study}
        for c in ["IPF", "control"]:
            r[f"{c}_donors"] = ic.loc[ic["condition"] == c, "donor_id"].nunique()
            r[f"{c}_cells"] = int((ic["condition"] == c).sum())
        r["assays"] = "; ".join(f"{a} ({n})" for a, n in ic["assay"].value_counts().items() if n > 0)
        r["only_10x3p"] = bool(ic["assay"].isin(preferred).all())
        r["has_both"] = r["IPF_donors"] >= k and r["control_donors"] >= k
        rows.append(r)
    return pd.DataFrame(rows)
