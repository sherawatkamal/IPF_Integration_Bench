"""Explore CELLxGENE Census lung metadata to choose IPF studies. Reads metadata only, downloads no counts."""

import argparse
import json

import pandas as pd

from signalkeep import download
from signalkeep.utils import load_config, resolve, setup_logging, track, write_manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/config.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)
    log = setup_logging(cfg, "00_explore_census")
    out = resolve(cfg, "census_exploration")
    stats: dict = {}

    ver = download.resolve_census_version(cfg["census"]["version"])
    log.info("Census version: %s", ver)
    pinned = ver["release_build"]

    with track(stats, "read_primary_obs"):
        obs, datasets = download.read_lung_obs(cfg, pinned, primary=True)
    log.info("Primary lung cells: %d across %d datasets", len(obs), obs["dataset_id"].nunique())

    with track(stats, "read_nonprimary_obs"):
        obs_np, _ = download.read_lung_obs(cfg, pinned, primary=False)

    labels = download.summarize_disease_labels(obs)
    labels.to_csv(out / "lung_disease_labels_primary.csv", index=False)

    summ = download.summarize_datasets(obs, datasets, cfg)
    summ.to_csv(out / "ipf_candidate_datasets_primary.csv", index=False)

    # Non-primary copies (e.g. HLCA re-releases) of fibrosis studies: tells us where harmonized labels live.
    summ_np = download.summarize_datasets(obs_np, datasets, cfg) if len(obs_np) else None
    if summ_np is not None:
        summ_np.to_csv(out / "ipf_candidate_datasets_nonprimary.csv", index=False)

    # Author-level study table: the only place a strict IPF diagnosis is recorded.
    tables = []
    for src in cfg["sources"]:
        with track(stats, f"read_source_obs_{src['name']}"):
            sobs = download.read_source_obs(pinned, src["dataset_id"], src["columns"])
        tables.append(download.summarize_source_studies(sobs, src, cfg))
        log.info("%s: %d cells read from source obs", src["name"], len(sobs))
    studies = pd.concat(tables, ignore_index=True).sort_values(["has_both", "IPF_donors"], ascending=False)
    studies.to_csv(out / "ipf_study_candidates.csv", index=False)
    log.info("Study candidates:\n%s", studies.to_string(index=False))

    outputs = sorted(str(p) for p in out.glob("*.csv"))
    (out / "census_version.json").write_text(json.dumps(ver, indent=2))
    write_manifest(cfg, "00_explore_census", inputs=[f"census:{pinned}"], outputs=outputs, stats=stats,
                   extra={"census_version": ver})
    log.info("Done. Outputs: %s", outputs)


if __name__ == "__main__":
    main()
