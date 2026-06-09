from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def _run(kind, body, *, context=None, repo=None, tmp_path=None):
    repo = repo or tmp_path
    target = repo / "doc.md"
    target.write_text(body, encoding="utf-8")
    return er.run_preflight_checks(kind, target, [Path(c) for c in (context or [])], repo)


def _msgs(result, severity):
    bucket = result.failures if severity == "failure" else result.warnings
    return " || ".join(f.message for f in bucket)


# --- target readable ---
def test_missing_target_is_failure(tmp_path):
    res = er.run_preflight_checks("spec", tmp_path / "nope.md", [], tmp_path)
    assert not res.ok
    assert any(f.check == "target" for f in res.failures)


def test_empty_target_is_failure(tmp_path):
    res = _run("spec", "   \n\n", tmp_path=tmp_path)
    assert any(f.check == "target" for f in res.failures)


# --- placeholders ---
def test_placeholder_in_prose_fails(tmp_path):
    res = _run("spec", "# Spec\n\n## Acceptance criteria\n\nThis is TODO still.\n", tmp_path=tmp_path)
    assert any(f.check == "placeholder" for f in res.failures)


def test_placeholder_in_fenced_block_exempt(tmp_path):
    body = "# Spec\n\n## Acceptance criteria\n\n```\nTODO leftover\n```\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.check == "placeholder" for f in res.failures)


def test_placeholder_in_inline_code_exempt(tmp_path):
    body = "# Spec\n\n## Acceptance criteria\n\nThe scanner flags `TODO` tokens.\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.check == "placeholder" for f in res.failures)


def test_triple_question_mark_placeholder(tmp_path):
    res = _run("spec", "# S\n\n## Acceptance criteria\n\nvalue is ??? here\n", tmp_path=tmp_path)
    assert any(f.check == "placeholder" for f in res.failures)


def test_nested_fence_longer_open_exempts_placeholder(tmp_path):
    body = "# Spec\n\n## Acceptance criteria\n\n`````\n```python\nTODO leftover\n```\n`````\n\nreal prose\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.check == "placeholder" for f in res.failures)


# --- paths ---
def test_dangling_markdown_link_fails(tmp_path):
    body = "# S\n\n## Acceptance criteria\n\nSee [the file](docs/nope/missing.md).\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert any(f.check == "dangling-link" for f in res.failures)


def test_existing_markdown_link_ok(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "real.md").write_text("x")
    body = "# S\n\n## Acceptance criteria\n\nSee [the file](docs/real.md).\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.check == "dangling-link" for f in res.failures)


def test_dangling_backtick_path_warns(tmp_path):
    body = "# S\n\n## Acceptance criteria\n\nLook at `skills/gone/x.py` for details.\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert any(f.check == "dangling-path" for f in res.warnings)
    assert not any(f.check == "dangling-path" for f in res.failures)


def test_fenced_path_exempt(tmp_path):
    body = "# S\n\n## Acceptance criteria\n\n```\ncat skills/gone/x.py\n```\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.check in ("dangling-path", "dangling-link") for f in res.failures + res.warnings)


def test_glob_and_placeholder_paths_exempt(tmp_path):
    body = "# S\n\n## Acceptance criteria\n\nName is `docs/specs/YYYY-MM-DD-<id>-slug.md` here.\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.path for f in res.failures + res.warnings)


def test_docs_reviewer_path_exempt(tmp_path):
    body = "# S\n\n## Acceptance criteria\n\nChain at `docs/reviewer/foo-spec/chain.json`.\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.check == "dangling-path" for f in res.warnings)


def test_url_not_treated_as_path(tmp_path):
    body = "# S\n\n## Acceptance criteria\n\nSee [home](https://example.com/page).\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.check == "dangling-link" for f in res.failures)


def test_path_with_line_suffix_resolves(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x\n")
    body = "# S\n\n## Acceptance criteria\n\nFix `src/a.py:12` now.\n"
    res = _run("spec", body, tmp_path=tmp_path)
    assert not any(f.check == "dangling-path" for f in res.warnings)


# --- sections ---
def test_spec_missing_acceptance_section_fails(tmp_path):
    res = _run("spec", "# Spec\n\nProse only, no criteria heading.\n", tmp_path=tmp_path)
    assert any(f.check == "missing-section" for f in res.failures)


def test_plan_needs_task_and_verification(tmp_path):
    only_tasks = "# Plan\n\n### Task 1\n\n- [ ] do it\n"
    res = _run("plan", only_tasks, tmp_path=tmp_path)
    assert any("verif" in f.message or "verification" in f.message for f in res.failures)


def test_plan_with_checkbox_and_verification_ok(tmp_path):
    body = "# Plan\n\n### Task 1\n\n- [ ] do it\n\n## Verification\n\nrun pytest\n"
    res = _run("plan", body, tmp_path=tmp_path)
    assert not any(f.check == "missing-section" for f in res.failures)


def test_post_slice_needs_evidence_section(tmp_path):
    res = _run("post-slice", "# Slice\n\n### Task 1\n\nno evidence heading\n", tmp_path=tmp_path)
    assert any(f.check == "missing-section" for f in res.failures)


def test_design_kind_no_section_requirement(tmp_path):
    res = _run("design", "# Design\n\nfree-form, no fixed shape.\n", tmp_path=tmp_path)
    assert not any(f.check == "missing-section" for f in res.failures)


# --- context hygiene ---
def test_missing_context_file_fails(tmp_path):
    body = "# S\n\n## Acceptance criteria\n\nok\n"
    res = _run("spec", body, context=[tmp_path / "missing-ctx.md"], tmp_path=tmp_path)
    assert any(f.check == "context" for f in res.failures)


def test_oversized_context_warns(tmp_path):
    big = tmp_path / "big.json"
    big.write_text("x" * (17 * 1024))
    body = "# S\n\n## Acceptance criteria\n\nok\n"
    res = _run("spec", body, context=[big], tmp_path=tmp_path)
    assert any(f.check == "context" for f in res.warnings)


def test_clean_document_passes(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "real.md").write_text("x")
    body = (
        "# Spec\n\n## Acceptance criteria\n\n"
        "1. A real criterion referencing [a file](docs/real.md).\n"
        "2. Another grounded statement.\n"
    )
    res = _run("spec", body, tmp_path=tmp_path)
    assert res.ok
    assert res.failures == []
