from pathlib import Path
import importlib.util
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
sys.modules["external_reviewer"] = er
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in (
        "AGENT_REVIEWER_CMD",
        "AGENT_REVIEWER_PROVIDER",
        "AGENT_REVIEWER_CALLER",
        "CLAUDECODE",
        "CLAUDE_CODE",
        "CODEX_HOME",
        "OPENAI_CODEX",
    ):
        monkeypatch.delenv(key, raising=False)


def test_custom_reviewer_cmd_wins(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "/tmp/my-reviewer")
    resolved = er.resolve_reviewer_provider(
        reviewer_provider="auto",
        caller_provider="claude",
        reviewer_cmd="/tmp/my-reviewer",
        env=dict(),
    )
    assert resolved.provider == "custom"
    assert resolved.caller_provider == "claude"
    assert resolved.command == "/tmp/my-reviewer"


def test_claude_caller_auto_selects_codex():
    resolved = er.resolve_reviewer_provider(
        reviewer_provider="auto",
        caller_provider="claude",
        reviewer_cmd=None,
        env=dict(),
    )
    assert resolved.provider == "codex"
    assert resolved.command == "reviewer-agent"


def test_codex_caller_auto_selects_claude():
    resolved = er.resolve_reviewer_provider(
        reviewer_provider="auto",
        caller_provider="codex",
        reviewer_cmd=None,
        env=dict(),
    )
    assert resolved.provider == "claude"
    assert resolved.command == "reviewer-agent"


def test_unknown_caller_auto_fails_closed():
    with pytest.raises(er.ProviderResolutionError, match="caller provider"):
        er.resolve_reviewer_provider(
            reviewer_provider="auto",
            caller_provider="unknown",
            reviewer_cmd=None,
            env=dict(),
        )


def test_env_caller_detection_wins_over_process_fallback(monkeypatch):
    monkeypatch.setenv("CODEX_HOME", "/tmp/codex")
    monkeypatch.setattr(
        er,
        "_detect_caller_provider_from_process_tree",
        lambda: pytest.fail("process fallback should not run when env is explicit"),
    )

    assert er.detect_caller_provider() == "codex"


def test_process_tree_fallback_detects_codex(monkeypatch):
    monkeypatch.setattr(er, "_process_tokens_for_pid", lambda pid: {
        10: ["zsh"],
        9: ["/opt/codex/bin/codex"],
    }.get(pid, []))
    monkeypatch.setattr(er, "_parent_pid_for_pid", lambda pid: {
        10: 9,
        9: 1,
    }.get(pid))

    assert er._detect_caller_provider_from_process_tree(start_pid=10) == "codex"


def test_process_tree_fallback_detects_claude_package(monkeypatch):
    monkeypatch.setattr(er, "_process_tokens_for_pid", lambda pid: {
        10: ["node", "/usr/lib/node_modules/@anthropic-ai/claude-code/cli.js"],
    }.get(pid, []))
    monkeypatch.setattr(er, "_parent_pid_for_pid", lambda pid: 1)

    assert er._detect_caller_provider_from_process_tree(start_pid=10) == "claude"


def test_process_tree_fallback_fails_closed_on_ambiguous_hints(monkeypatch):
    monkeypatch.setattr(er, "_process_tokens_for_pid", lambda pid: {
        10: ["/opt/codex/bin/codex"],
        9: ["/usr/bin/claude"],
    }.get(pid, []))
    monkeypatch.setattr(er, "_parent_pid_for_pid", lambda pid: {
        10: 9,
        9: 1,
    }.get(pid))

    assert er._detect_caller_provider_from_process_tree(start_pid=10) == "unknown"


def test_explicit_provider_uses_reviewer_agent_command():
    resolved = er.resolve_reviewer_provider(
        reviewer_provider="codex",
        caller_provider="unknown",
        reviewer_cmd=None,
        env=dict(),
    )
    assert resolved.provider == "codex"
    assert resolved.command == "reviewer-agent"


def test_parse_args_accepts_provider_flags():
    args = er.parse_args([
        "review",
        "--kind", "spec",
        "--file", "docs/specs/example.md",
        "--reviewer-provider", "codex",
        "--caller-provider", "claude",
    ])
    assert args.reviewer_provider == "codex"
    assert args.caller_provider == "claude"


def test_env_provider_default_is_auto(monkeypatch):
    monkeypatch.delenv("AGENT_REVIEWER_PROVIDER", raising=False)
    args = er.parse_args(["review", "--kind", "spec", "--file", "x.md"])
    assert args.reviewer_provider == "auto"


def test_reviewer_cmd_default_is_none_without_env(monkeypatch):
    monkeypatch.delenv("AGENT_REVIEWER_CMD", raising=False)
    args = er.parse_args(["review", "--kind", "spec", "--file", "x.md"])
    assert args.reviewer_cmd is None


def test_reviewer_cmd_reads_env_override(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "/tmp/custom-reviewer")
    args = er.parse_args(["review", "--kind", "spec", "--file", "x.md"])
    assert args.reviewer_cmd == "/tmp/custom-reviewer"
