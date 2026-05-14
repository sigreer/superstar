"""End-to-end tests asserting --work-id is persisted in chain.json and JSON output."""
from pathlib import Path
import subprocess, sys, os, json

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "stub.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    return repo


def _run(repo: Path, *extra):
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md",
         "--emit", "json", *extra],
        cwd=repo, env=env, capture_output=True, text=True,
    )


def test_work_id_persisted_in_manifest_and_json(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run(repo, "--work-id", "S1")
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert payload["work_id"] == "S1"
    chain = payload["chain"]
    manifest_path = repo / "docs" / "reviewer" / chain / "chain.json"
    data = json.loads(manifest_path.read_text())
    assert data["work_id"] == "S1"


def test_work_id_mismatch_refuses_reuse(tmp_path):
    repo = _init_repo(tmp_path)
    r1 = _run(repo, "--work-id", "S1")
    assert r1.returncode == 0, r1.stderr
    # Same target, same kind, different work-id → distinct folder, so this should
    # NOT clash. We need to assert that if someone synthesises a folder for one
    # work-id and re-invokes against THAT folder with a different work-id, it errors.
    # The natural mismatch happens via the synthesised manifest path: simulate by
    # writing a manifest with a particular work_id under the slug for a different one.
    chain_dir = repo / "docs" / "reviewer" / "plan-S2-post-slice"
    chain_dir.mkdir(parents=True)
    (chain_dir / "chain.json").write_text(json.dumps({
        "schema_version": 1,
        "chain": "plan-S2-post-slice",
        "kind": "post-slice",
        "target": "plan.md",
        "work_id": "S2",
        "legacy_migrated": False,
        "rounds": [],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }))
    # Trick discover_legacy_chain into reusing this folder by giving it a legacy
    # name that matches the bare slug AND no chain.json -> but we just wrote one.
    # Instead, directly invoke with --work-id that targets that exact slug.
    # discover_legacy_chain prefers new_path if it exists, so calling with --work-id S2
    # will hit it. Mismatch path: invoke with --work-id S3 against same slug — but
    # then new_path is plan-S3-post-slice, a fresh folder. So mismatch only really
    # arises when the same folder is reused. Simulate by also writing the request
    # files in the S1 chain folder and re-running with S2.
    # Simpler: use the new_path directly by symlinking the slug.
    r2_dir = repo / "docs" / "reviewer" / "plan-S2-post-slice"
    # already created above with work_id=S2 manifest. Run with --work-id S3:
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    # Force the script to use this folder by aliasing new_slug via --output-dir? No;
    # the slug derives from work_id. Instead, rewrite the manifest's work_id to
    # something that the script's slug would still resolve to. The slug for
    # --work-id S2 is plan-S2-post-slice. Run with --work-id S2 but stored is S2 - no mismatch.
    # Overwrite stored to a *different* value, then invoke with --work-id matching the slug.
    bad_manifest = json.loads((r2_dir / "chain.json").read_text())
    bad_manifest["work_id"] = "OTHER"
    (r2_dir / "chain.json").write_text(json.dumps(bad_manifest))
    r2 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "S2", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert r2.returncode == 6, (r2.returncode, r2.stderr, r2.stdout)
    assert "does not match" in r2.stderr


def test_existing_chain_folder_with_chain_json_not_reused_as_legacy(tmp_path):
    """A sibling chain folder that already has chain.json (different work-id) must
    NOT be matched as a legacy candidate for a new work-id."""
    repo = _init_repo(tmp_path)
    # Create a Slice-1 chain at the legacy/bare folder name "plan-post-slice"
    # WITH chain.json present (so it's a new-regime chain).
    s1_dir = repo / "docs" / "reviewer" / "plan-post-slice"
    s1_dir.mkdir(parents=True)
    (s1_dir / "chain.json").write_text(json.dumps({
        "schema_version": 1, "chain": "plan-post-slice", "kind": "post-slice",
        "target": "plan.md", "work_id": "S1", "legacy_migrated": False,
        "rounds": [], "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }))
    (s1_dir / "r1-2026-01-01T0000-request.md").write_text("")
    (s1_dir / "r1-2026-01-01T0000-response.md").write_text("Overall verdict: ready\n")

    r = _run(repo, "--work-id", "S2")
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    # New folder must be created — must NOT have reused the S1 folder.
    assert payload["chain"] == "plan-S2-post-slice"
    new_dir = repo / "docs" / "reviewer" / "plan-S2-post-slice"
    assert new_dir.exists()
    manifest = json.loads((new_dir / "chain.json").read_text())
    assert manifest["work_id"] == "S2"
    assert len(manifest["rounds"]) == 1
    # S1 folder must remain untouched (no round 2 added).
    s1_manifest = json.loads((s1_dir / "chain.json").read_text())
    assert len(s1_manifest["rounds"]) == 0
