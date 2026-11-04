import json

import numpy as np

from signalkeep import utils


def test_config_loads_and_has_required_sections():
    cfg = utils.load_config(utils.REPO_ROOT / "config" / "config.yaml")
    for key in ["paths", "seeds", "census", "disease", "slurm"]:
        assert key in cfg
    # Disease must never appear as a batch/covariate key anywhere in config.
    assert "disease" not in json.dumps(cfg.get("integration", {}))


def test_seeding_is_reproducible():
    utils.set_seeds(0)
    a = np.random.rand(5)
    utils.set_seeds(0)
    assert np.allclose(a, np.random.rand(5))


def test_track_and_manifest(tmp_path):
    cfg = {"paths": {"logs": str(tmp_path)}, "_config_path": "x"}
    stats = {}
    with utils.track(stats, "block"):
        sum(range(1000))
    assert stats["block"]["seconds"] >= 0 and stats["block"]["peak_rss_gb"] > 0
    path = utils.write_manifest(cfg, "unit", ["in"], ["out"], stats)
    assert json.loads(path.read_text())["step"] == "unit"
