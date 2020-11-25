from pathlib import Path

import pandas as pd
import pytest

from cgr_gwas_qc.config import ConfigMgr, scan_for_yaml
from cgr_gwas_qc.testing import chdir

################################################################################
# Make sure both `config.yml` or `config.yaml` are found.
################################################################################
yaml_extensions = [
    ("config", "yml"),
    ("config", "yaml"),
]


@pytest.mark.parametrize("name,ext", yaml_extensions)
def test_scan_for_yaml(tmp_path, name, ext):
    # Create a config file
    cfg_file = tmp_path / f"{name}.{ext}"
    cfg_file.touch()

    found_config = scan_for_yaml(tmp_path, name)

    assert found_config.as_posix() == cfg_file.as_posix()


################################################################################
# Sanity check that ConfigMgr loads the yaml correctly.
################################################################################
def test_manually_loading_config(small_bed_working_dir: Path):
    with chdir(small_bed_working_dir):
        cfg = ConfigMgr.instance()
        assert cfg.config.project_name == "Test Project"
        assert isinstance(cfg.ss, pd.DataFrame)


def test_load_config(small_bed_working_dir: Path):
    from cgr_gwas_qc import load_config

    with chdir(small_bed_working_dir):
        cfg = load_config()
        assert cfg.config.project_name == "Test Project"
        assert isinstance(cfg.ss, pd.DataFrame)


################################################################################
# Make sure if we call ConfigMgr multiple times it only creates a single
# instance.
################################################################################
def test_config_only_uses_one_instance(small_bed_working_dir: Path):
    with chdir(small_bed_working_dir):
        cfg = ConfigMgr.instance()
    cfg2 = ConfigMgr.instance()
    assert cfg is cfg2
