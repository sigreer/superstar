from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - non-Unix fallback
    fcntl = None  # type: ignore[assignment]


MAX_QUEUE = 3


def _disabled() -> bool:
    return os.environ.get("SUPERSTAR_NOTIFY_DISABLE") == "1"


def _display_status(status: str) -> str:
    return status.replace("_", " ")


def _write_event(event: dict[str, str]) -> None:
    line = json.dumps(event, sort_keys=True)
    log = os.environ.get("SUPERSTAR_NOTIFY_LOG")
    if log:
        path = Path(log).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    else:
        print(line)


def _queue_dir() -> Path:
    configured = os.environ.get("SUPERSTAR_NOTIFY_QUEUE_DIR")
    if configured:
        return Path(configured).expanduser()
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        return Path(runtime) / "superstar-notify"
    return Path("/tmp") / f"superstar-notify-{os.getuid()}"


def _queue_path() -> Path:
    return _queue_dir() / "queue.json"


def _queue_lock_path() -> Path:
    return _queue_dir() / "queue.lock"


def _worker_lock_path() -> Path:
    return _queue_dir() / "worker.lock"


class _FileLock:
    def __init__(self, path: Path):
        self.path = path
        self.file = None

    def __enter__(self) -> "_FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+", encoding="utf-8")
        if fcntl is not None:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *_exc: object) -> None:
        if self.file is None:
            return
        if fcntl is not None:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
        self.file.close()


def _read_queue() -> list[dict[str, str]]:
    path = _queue_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "[]")
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _write_queue(events: list[dict[str, str]]) -> None:
    path = _queue_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(events, sort_keys=True), encoding="utf-8")


def _summary_event() -> dict[str, str]:
    return {
        "type": "tasktool-status",
        "id": "multiple",
        "kind": "summary",
        "status": "summary",
        "title": "Multiple other events",
        "message": "Multiple other events",
    }


def _is_summary(event: dict[str, str]) -> bool:
    return event.get("id") == "multiple" and event.get("status") == "summary"


def _enqueue_event(event: dict[str, str]) -> None:
    with _FileLock(_queue_lock_path()):
        events = _read_queue()
        if len(events) < MAX_QUEUE:
            events.append(event)
        elif not events or not _is_summary(events[-1]):
            events = events[: MAX_QUEUE - 1] + [_summary_event()]
        _write_queue(events)


def _pop_event() -> dict[str, str] | None:
    with _FileLock(_queue_lock_path()):
        events = _read_queue()
        if not events:
            _write_queue([])
            return None
        event = events.pop(0)
        _write_queue(events)
        return event


def _try_acquire_worker_lock() -> bool:
    path = _worker_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(f"{os.getpid()} {time.time()}\n")
    return True


def _release_worker_lock() -> None:
    try:
        _worker_lock_path().unlink()
    except FileNotFoundError:
        pass


def _ensure_worker() -> None:
    if not _try_acquire_worker_lock():
        return
    try:
        subprocess.Popen(
            [sys.executable, __file__, "worker"],
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        _release_worker_lock()


def _dry_run(event: dict[str, str]) -> bool:
    if os.environ.get("SUPERSTAR_NOTIFY_DRY_RUN") == "1":
        _write_event(event)
        return True
    return False


def _agent_style() -> str:
    explicit = os.environ.get("SUPERSTAR_NOTIFY_AGENT_STYLE")
    if explicit in {"claude", "codex", "generic"}:
        return explicit
    if os.environ.get("CODEX_HOME") or os.environ.get("OPENAI_CODEX"):
        return "codex"
    if (
        os.environ.get("CLAUDE_PLUGIN_ROOT")
        or os.environ.get("CLAUDECODE")
        or os.environ.get("CLAUDE_CODE")
    ):
        return "claude"
    return "generic"


def _ding(style: str) -> bool:
    # Prefer an explicit sound file before falling back to system sound-theme
    # names. canberra-gtk-play resolves names like "complete"/"bell" against the
    # active XDG sound theme (often freedesktop), which can be a harsh, piercing
    # sample. Playing a known-good file directly avoids that. The path is
    # existence-guarded, so machines without it fall through to the theme logic.
    # Override with SUPERSTAR_NOTIFY_DING_FILE.
    preferred: list[str] = []
    override = os.environ.get("SUPERSTAR_NOTIFY_DING_FILE")
    if override:
        preferred.append(override)
    preferred.append("/usr/share/sounds/Enchanted/stereo/bell.ogg")
    for filename in preferred:
        path = Path(filename).expanduser()
        if path.is_file() and _run_first([["paplay", str(path)]]):
            return True

    sound_names = {
        "claude": ["complete", "bell"],
        "codex": ["message", "bell", "complete"],
        "generic": ["bell", "complete", "message"],
        "tasktool": ["complete", "message", "bell"],
    }.get(style, ["bell", "complete"])

    if _run_first(
        [
            ["canberra-gtk-play", "-i", name, "-d", "Superstar notification"]
            for name in sound_names
        ]
    ):
        return True

    sound_files = {
        "claude": ["complete.oga", "bell.oga"],
        "codex": ["message.oga", "bell.oga", "complete.oga"],
        "generic": ["bell.oga", "complete.oga", "message.oga"],
        "tasktool": ["complete.oga", "message.oga", "bell.oga"],
    }.get(style, ["bell.oga", "complete.oga"])
    paplay_commands = []
    for filename in sound_files:
        path = Path("/usr/share/sounds/freedesktop/stereo") / filename
        if path.exists():
            paplay_commands.append(["paplay", str(path)])
    if _run_first(paplay_commands):
        return True

    try:
        tty = Path("/dev/tty")
        tty.write_text("\a", encoding="utf-8")
        return True
    except OSError:
        return False


def _run_first(commands: list[list[str]]) -> bool:
    for command in commands:
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            continue
        if result.returncode == 0:
            return True
    return False


def _play_event(event: dict[str, str]) -> None:
    if event.get("type") == "agent-ding":
        _ding(event.get("style", "generic"))
        return
    message = event.get("message") or "Multiple other events"
    if not _tts(message):
        _ding("tasktool")


def _worker_loop() -> None:
    while True:
        event = _pop_event()
        if event is None:
            _release_worker_lock()
            with _FileLock(_queue_lock_path()):
                if not _read_queue():
                    return
            if not _try_acquire_worker_lock():
                return
            continue
        _play_event(event)


def _read_tts_config() -> dict[str, str]:
    config_file = Path(
        os.environ.get(
            "SUPERSTAR_NOTIFY_TTS_CONFIG",
            str(Path.home() / ".config/hypr-tts/config.yaml"),
        )
    ).expanduser()
    config: dict[str, str] = {}
    if not config_file.is_file():
        return config

    try:
        import yaml  # type: ignore

        data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items() if v is not None}
    except Exception:
        pass

    for line in config_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        config[key.strip()] = value.strip().strip("'\"")
    return config


def _tts_duck_percent(config: dict[str, str]) -> int:
    raw = os.environ.get("SUPERSTAR_NOTIFY_DUCK_PERCENT") or config.get("media_duck_percent") or "35"
    try:
        value = int(float(str(raw)))
    except (TypeError, ValueError):
        return 35
    return max(0, min(value, 150))


def _snapshot_sink_inputs() -> list[tuple[str, str]]:
    try:
        result = subprocess.run(
            ["pactl", "list", "sink-inputs"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []

    snapshots: list[tuple[str, str]] = []
    for block in re.split(r"\n(?=Sink Input #)", result.stdout):
        lines = block.splitlines()
        if not lines:
            continue
        match = re.match(r"Sink Input #(\d+)", lines[0].strip())
        if not match:
            continue
        if any(line.strip() == "Mute: yes" for line in lines):
            continue
        volume = None
        for line in lines:
            if line.lstrip().startswith("Volume:"):
                percent = re.search(r"/\s*(\d+)%\s*/", line)
                if percent:
                    volume = percent.group(1)
                    break
        if volume is not None:
            snapshots.append((match.group(1), volume))
    return snapshots


def _set_sink_input_volume(sink_input: str, percent: str | int) -> None:
    try:
        subprocess.run(
            ["pactl", "set-sink-input-volume", sink_input, f"{percent}%"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return


def _duck_sink_inputs(snapshots: list[tuple[str, str]], percent: int) -> None:
    for sink_input, _volume in snapshots:
        _set_sink_input_volume(sink_input, percent)


def _restore_sink_inputs(snapshots: list[tuple[str, str]]) -> None:
    for sink_input, volume in snapshots:
        _set_sink_input_volume(sink_input, volume)


def _tts(message: str) -> bool:
    config = _read_tts_config()
    api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return False

    body = {
        "model": config.get("model", "gpt-4o-mini-tts"),
        "voice": config.get("voice", "alloy"),
        "input": message,
        "response_format": config.get("format", "opus"),
        "speed": float(config.get("speed", "1.0")),
    }
    instructions = config.get("instructions")
    if body["model"] == "gpt-4o-mini-tts" and instructions:
        body["instructions"] = instructions

    try:
        curl = subprocess.run(
            [
                "curl",
                "-sS",
                "--fail-with-body",
                "-H",
                f"Authorization: Bearer {api_key}",
                "-H",
                "Content-Type: application/json",
                "-d",
                json.dumps(body),
                "https://api.openai.com/v1/audio/speech",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    if curl.returncode != 0 or not curl.stdout:
        return False

    sink_inputs = _snapshot_sink_inputs()
    if sink_inputs:
        _duck_sink_inputs(sink_inputs, _tts_duck_percent(config))
    try:
        try:
            mpv = subprocess.run(
                [
                    "mpv",
                    "--no-video",
                    "--really-quiet",
                    "--cache=no",
                    "--title=superstar-tasktool-tts",
                    "--audio-client-name=superstar-tasktool-tts",
                    "-",
                ],
                input=curl.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            return False
        return mpv.returncode == 0
    finally:
        if sink_inputs:
            _restore_sink_inputs(sink_inputs)


def notify_agent_finished() -> None:
    if _disabled():
        return
    style = _agent_style()
    event = {"type": "agent-ding", "style": style}
    if _dry_run(event):
        return
    _enqueue_event(event)
    _ensure_worker()


def _tasktool_event(*, work_id: str, kind: str, status: str, title: str) -> dict[str, str]:
    message = f"{work_id} {_display_status(status)}: {title}"
    return {
        "type": "tasktool-status",
        "id": work_id,
        "kind": kind,
        "status": status,
        "title": title,
        "message": message,
    }


def _tasktool_artifact_event(
    *, work_id: str, kind: str, artifact_kind: str, title: str
) -> dict[str, str]:
    message = f"{work_id} {artifact_kind} written: {title}"
    return {
        "type": "tasktool-artifact",
        "id": work_id,
        "kind": kind,
        "artifact_kind": artifact_kind,
        "title": title,
        "message": message,
    }


def _tasktool_workflow_step_event(
    *, work_id: str, kind: str, step: str, title: str
) -> dict[str, str]:
    return {
        "type": "tasktool-workflow-step",
        "id": work_id,
        "kind": kind,
        "step": step,
        "title": title,
        "message": f"{work_id} progressed to {step} step",
    }


def notify_tasktool_status(*, work_id: str, kind: str, status: str, title: str) -> None:
    if _disabled():
        return
    event = _tasktool_event(work_id=work_id, kind=kind, status=status, title=title)
    if _dry_run(event):
        return
    _enqueue_event(event)
    _ensure_worker()


def notify_tasktool_artifact(
    *, work_id: str, kind: str, artifact_kind: str, title: str
) -> None:
    if _disabled():
        return
    event = _tasktool_artifact_event(
        work_id=work_id,
        kind=kind,
        artifact_kind=artifact_kind,
        title=title,
    )
    if _dry_run(event):
        return
    _enqueue_event(event)
    _ensure_worker()


def notify_tasktool_workflow_step(
    *, work_id: str, kind: str, step: str, title: str
) -> None:
    if _disabled():
        return
    event = _tasktool_workflow_step_event(
        work_id=work_id,
        kind=kind,
        step=step,
        title=title,
    )
    if _dry_run(event):
        return
    _enqueue_event(event)
    _ensure_worker()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(
            "usage: notify.py agent-finished | tasktool-status ID KIND STATUS TITLE | "
            "tasktool-artifact ID KIND ARTIFACT_KIND TITLE | "
            "tasktool-workflow-step ID KIND STEP TITLE",
            file=sys.stderr,
        )
        return 2
    command = argv.pop(0)
    if command == "agent-finished":
        notify_agent_finished()
        return 0
    if command == "tasktool-status":
        if len(argv) != 4:
            print("usage: notify.py tasktool-status ID KIND STATUS TITLE", file=sys.stderr)
            return 2
        work_id, kind, status, title = argv
        notify_tasktool_status(work_id=work_id, kind=kind, status=status, title=title)
        return 0
    if command == "tasktool-artifact":
        if len(argv) != 4:
            print("usage: notify.py tasktool-artifact ID KIND ARTIFACT_KIND TITLE", file=sys.stderr)
            return 2
        work_id, kind, artifact_kind, title = argv
        notify_tasktool_artifact(
            work_id=work_id,
            kind=kind,
            artifact_kind=artifact_kind,
            title=title,
        )
        return 0
    if command == "tasktool-workflow-step":
        if len(argv) != 4:
            print("usage: notify.py tasktool-workflow-step ID KIND STEP TITLE", file=sys.stderr)
            return 2
        work_id, kind, step, title = argv
        notify_tasktool_workflow_step(work_id=work_id, kind=kind, step=step, title=title)
        return 0
    if command == "worker":
        _worker_loop()
        return 0
    print(f"unknown notify command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
