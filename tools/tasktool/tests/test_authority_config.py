import json

from tasktool.config import (
    DEFAULT_CONFIG_REL,
    TasklistConfig,
    TasktoolConfig,
    is_authoritative_required,
    load_config,
    save_config,
)


def test_missing_config_returns_unconfigured(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "unconfigured"
    assert is_authoritative_required(cfg) is True


def test_explicit_local_is_configured(tmp_path):
    path = tmp_path / DEFAULT_CONFIG_REL
    path.parent.mkdir()
    path.write_text(
        '{"schema_version":1,"tasklist":{"mutation_mode":"local","authoritative_branch":"main"}}'
    )

    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "local"
    assert is_authoritative_required(cfg) is False


def test_authoritative_checkout_is_configured(tmp_path):
    path = tmp_path / DEFAULT_CONFIG_REL
    path.parent.mkdir()
    path.write_text(
        '{"schema_version":1,"tasklist":{"mutation_mode":"authoritative-checkout","authoritative_branch":"main"}}'
    )

    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "authoritative-checkout"
    assert is_authoritative_required(cfg) is False


def test_config_with_omitted_mutation_mode_is_unconfigured(tmp_path):
    path = tmp_path / DEFAULT_CONFIG_REL
    path.parent.mkdir()
    path.write_text('{"schema_version":1,"tasklist":{"authoritative_branch":"main"}}')

    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "unconfigured"
    assert is_authoritative_required(cfg) is True


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
