from pathlib import Path
import sys, importlib.util, json
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_finds_legacy_folder_matching_old_naming(tmp_path):
    reviewer_root = tmp_path / "docs" / "reviewer"
    legacy = reviewer_root / "feature-post-slice"; legacy.mkdir(parents=True)
    (legacy / "r1-2026-04-01T0900-request.md").write_text("")

    found = er.discover_legacy_chain(
        reviewer_root=reviewer_root,
        target_stem="feature",
        kind="post-slice",
        new_slug="feature-P2-S3-post-slice",
    )
    assert found == legacy


def test_no_match_returns_none(tmp_path):
    root = tmp_path / "docs" / "reviewer"; root.mkdir(parents=True)
    assert er.discover_legacy_chain(root, "feature", "post-slice", "feature-P2-S3-post-slice") is None


def test_ambiguous_match_raises(tmp_path):
    root = tmp_path / "docs" / "reviewer"
    (root / "feature-post-slice").mkdir(parents=True)
    (root / "feature-post-slice").joinpath("r1-2026-04-01T0900-request.md").write_text("")
    (root / "feature-X-post-slice").mkdir()
    (root / "feature-X-post-slice").joinpath("r1-2026-04-01T0900-request.md").write_text("")

    # Both fold to base prefix "feature" — ambiguous when new naming arrives.
    import pytest
    with pytest.raises(er.AmbiguousLegacyChain):
        er.discover_legacy_chain(root, "feature", "post-slice", "feature-P2-S3-post-slice")
