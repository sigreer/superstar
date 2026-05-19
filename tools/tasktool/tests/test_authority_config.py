import json

from tasktool.config import (
    DEFAULT_CONFIG_REL,
    TasklistConfig,
    TasktoolConfig,
    load_config,
    save_config,
)


def test_missing_config_defaults_to_local(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "local"


def test_round_trip_authoritative_config(tmp_path):
    cfg = TasktoolConfig(
        tasklist=TasklistConfig(
            mutation_mode="authoritative-checkout",
            authoritative_branch="main",
        )
    )
    save_config(tmp_path, cfg)
    raw = json.loads((tmp_path / DEFAULT_CONFIG_REL).read_text())
    assert raw["schema_version"] == 1
    assert raw["tasklist"]["mutation_mode"] == "authoritative-checkout"
    assert "authoritative_root" not in raw["tasklist"]
    assert load_config(tmp_path) == cfg


def test_invalid_mode_raises(tmp_path):
    path = tmp_path / DEFAULT_CONFIG_REL
    path.parent.mkdir()
    path.write_text('{"schema_version":1,"tasklist":{"mutation_mode":"bad"}}')
    try:
        load_config(tmp_path)
    except ValueError as exc:
        assert "unknown mutation_mode" in str(exc)
    else:
        raise AssertionError("expected ValueError")
