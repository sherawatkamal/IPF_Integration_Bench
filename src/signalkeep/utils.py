"""Shared helpers: config loading, logging, seeding, timing/memory tracking, run manifests."""

from __future__ import annotations

import json
import logging
import os
import platform
import random
import resource
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from importlib import metadata
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

TRACKED_PACKAGES = [
    "numpy", "pandas", "scanpy", "anndata", "cellxgene-census", "tiledbsoma", "scvi-tools",
    "torch", "jax", "harmonypy", "bbknn", "scanorama", "scib-metrics", "pydeseq2", "scikit-learn",
]


def load_config(path: str | Path) -> dict:
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    cfg["_config_path"] = str(Path(path).resolve())
    return cfg


def resolve(cfg: dict, key: str) -> Path:
    """Absolute path for cfg['paths'][key], relative to the repo root; created if missing."""
    p = Path(cfg["paths"][key])
    p = p if p.is_absolute() else REPO_ROOT / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def setup_logging(cfg: dict, step: str) -> logging.Logger:
    log_dir = resolve(cfg, "logs")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = log_dir / f"{step}_{stamp}.log"
    logger = logging.getLogger("signalkeep")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for h in (logging.FileHandler(logfile), logging.StreamHandler(sys.stdout)):
        h.setFormatter(fmt)
        logger.addHandler(h)
    logger.info("step=%s log=%s config=%s", step, logfile, cfg.get("_config_path"))
    return logger


def set_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass


def peak_rss_gb() -> float:
    """Peak resident memory of this process in GB (Linux ru_maxrss is in KB)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2


@contextmanager
def track(stats: dict, name: str):
    """Record wall time (s) and peak RSS (GB) of a block into stats[name]."""
    t0 = time.perf_counter()
    yield
    stats[name] = {"seconds": round(time.perf_counter() - t0, 2), "peak_rss_gb": round(peak_rss_gb(), 3)}


def package_versions() -> dict:
    out = {}
    for pkg in TRACKED_PACKAGES:
        try:
            out[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            out[pkg] = None
    return out


def write_manifest(cfg: dict, step: str, inputs: list, outputs: list, stats: dict, extra: dict | None = None) -> Path:
    """Small JSON per step: inputs, outputs, versions, runtime and memory (engineering rule, spec section 8)."""
    out_dir = resolve(cfg, "logs")
    manifest = {
        "step": step,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "config": cfg.get("_config_path"),
        "host": platform.node(),
        "python": sys.version.split()[0],
        "inputs": [str(i) for i in inputs],
        "outputs": [str(o) for o in outputs],
        "stats": stats,
        "versions": package_versions(),
        **(extra or {}),
    }
    path = out_dir / f"{step}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str))
    return path
