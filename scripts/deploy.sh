#!/usr/bin/env bash
# Superstar deploy wrapper.
#
# Modes:
#   scripts/deploy.sh                 # publish caches, re-run installers, then --check summary
#   scripts/deploy.sh --check         # read-only diagnostic over global shims + plugin caches
#   scripts/deploy.sh --codex-only    # skip Claude publish step
#   scripts/deploy.sh --claude-only   # skip Codex publish step
#   scripts/deploy.sh --help          # this help
set -euo pipefail

usage() {
    sed -n '2,/^set -euo pipefail/{/^set -euo pipefail/!p;}' "${BASH_SOURCE[0]}"
}

MODE="deploy"
SKIP_CODEX=0
SKIP_CLAUDE=0

for arg in "$@"; do
    case "$arg" in
        --check) MODE="check" ;;
        --codex-only) SKIP_CLAUDE=1 ;;
        --claude-only) SKIP_CODEX=1 ;;
        --help|-h) usage; exit 0 ;;
        *) echo "deploy.sh: unknown argument: $arg" >&2; usage >&2; exit 2 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_ROOT="${SUPERSTAR_SOURCE_ROOT:-$REPO_ROOT}"

EXPAND_PATH() {
    local p="$1"
    case "$p" in
        '$HOME/'*) printf '%s' "${HOME}/${p#\$HOME/}" ;;
        '~/'*)     printf '%s' "${HOME}/${p#~/}" ;;
        '$HOME')   printf '%s' "${HOME}" ;;
        '~')       printf '%s' "${HOME}" ;;
        *)         printf '%s' "$p" ;;
    esac
}

PARSE_HEADER() {
    # Reads up to 32 lines of `# superstar-(shim|hook)-key: value`, emits key=value.
    local file="$1"
    awk 'NR<=32 && /^#[[:space:]]*superstar-(shim|hook)-/ {
        sub(/^#[[:space:]]*/, "", $0)
        idx = index($0, ":")
        if (idx == 0) next
        key = substr($0, 1, idx-1)
        val = substr($0, idx+1)
        sub(/^[[:space:]]+/, "", val)
        sub(/[[:space:]]+$/, "", val)
        print key "=" val
    }' "$file" 2>/dev/null || true
}

# Globals populated by run_check
EXIT_CODE=0
declare -A SHIM_SOURCE_ROOTS=()

print_row() {
    printf '  %-22s %-14s %s\n' "$1" "$2" "$3"
}

check_shim() {
    local name="$1"
    local target="${HOME}/.local/bin/${name}"
    local status=""
    local detail=""

    if [[ ! -f "$target" ]]; then
        status="MISSING_TARGET"
        detail="$target"
        EXIT_CODE=1
        print_row "$name" "$status" "$detail"
        return
    fi

    local header
    header="$(PARSE_HEADER "$target")"

    local stamped_version="" stamped_source_root=""
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        case "$line" in
            superstar-shim-version=*) stamped_version="${line#superstar-shim-version=}" ;;
            superstar-shim-source-root=*) stamped_source_root="${line#superstar-shim-source-root=}" ;;
        esac
    done <<< "$header"

    if [[ -z "$stamped_version" || -z "$stamped_source_root" ]]; then
        status="MALFORMED"
        detail="$target (missing version/source-root header)"
        EXIT_CODE=1
        print_row "$name" "$status" "$detail"
        return
    fi

    local expanded_root
    expanded_root="$(EXPAND_PATH "$stamped_source_root")"

    if [[ ! -d "$expanded_root" || ! -r "$expanded_root/VERSION" ]]; then
        status="MISSING_SOURCE"
        detail="$expanded_root (no readable VERSION)"
        EXIT_CODE=1
        print_row "$name" "$status" "$detail"
        return
    fi

    local source_version
    source_version="$(tr -d '[:space:]' < "$expanded_root/VERSION")"

    if [[ "$stamped_version" != "$source_version" ]]; then
        status="DRIFT"
        detail="shim=$stamped_version source=$source_version root=$expanded_root"
        EXIT_CODE=1
        print_row "$name" "$status" "$detail"
        return
    fi

    status="OK"
    detail="v$stamped_version root=$expanded_root"
    print_row "$name" "$status" "$detail"
    SHIM_SOURCE_ROOTS["$name"]="$expanded_root"
}

check_hook() {
    # Resolve git hooks path for the current working tree (worktree-safe).
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        print_row "pre-commit" "NOT_DEPLOYED" "(not in a git working tree)"
        return
    fi

    local repo_top
    repo_top="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    local hook_path
    hook_path="$(git rev-parse --git-path hooks/pre-commit 2>/dev/null || true)"
    if [[ -z "$hook_path" ]]; then
        print_row "pre-commit" "NOT_DEPLOYED" "(failed to resolve git hooks path)"
        return
    fi
    case "$hook_path" in
        /*) ;;
        *) hook_path="$repo_top/$hook_path" ;;
    esac

    if [[ ! -f "$hook_path" ]]; then
        EXIT_CODE=1
        print_row "pre-commit" "MISSING_TARGET" "$hook_path"
        return
    fi

    local header
    header="$(PARSE_HEADER "$hook_path")"

    local hook_name="" hook_version="" hook_source_root=""
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        case "$line" in
            superstar-hook-name=*) hook_name="${line#superstar-hook-name=}" ;;
            superstar-hook-version=*) hook_version="${line#superstar-hook-version=}" ;;
            superstar-hook-source-root=*) hook_source_root="${line#superstar-hook-source-root=}" ;;
        esac
    done <<< "$header"

    if [[ "$hook_name" != "tasktool-pre-commit" ]]; then
        print_row "pre-commit" "NOT_DEPLOYED" "(not a tasktool hook) $hook_path"
        return
    fi

    if [[ -z "$hook_version" || -z "$hook_source_root" ]]; then
        EXIT_CODE=1
        print_row "pre-commit" "MALFORMED" "$hook_path (missing version/source-root header)"
        return
    fi

    local expanded_root
    expanded_root="$(EXPAND_PATH "$hook_source_root")"

    if [[ ! -d "$expanded_root" || ! -r "$expanded_root/VERSION" ]]; then
        EXIT_CODE=1
        print_row "pre-commit" "MISSING_SOURCE" "$expanded_root (no readable VERSION)"
        return
    fi

    local src_version
    src_version="$(tr -d '[:space:]' < "$expanded_root/VERSION")"

    if [[ "$hook_version" != "$src_version" ]]; then
        EXIT_CODE=1
        print_row "pre-commit" "DRIFT" "hook=$hook_version source-root has $src_version root=$expanded_root"
        return
    fi

    print_row "pre-commit" "OK" "v$hook_version root=$expanded_root"
}

check_cache() {
    local name="$1" cache_dir="$2" dev_version="$3"
    local status="" detail=""

    if [[ ! -d "$cache_dir" ]]; then
        status="NOT_DEPLOYED"
        detail="$cache_dir"
        print_row "$name" "$status" "$detail"
        return
    fi

    if [[ ! -r "$cache_dir/VERSION" ]]; then
        status="MISSING_CACHE_VERSION"
        detail="$cache_dir (no readable VERSION)"
        EXIT_CODE=1
        print_row "$name" "$status" "$detail"
        return
    fi

    local cache_version
    cache_version="$(tr -d '[:space:]' < "$cache_dir/VERSION")"

    if [[ "$cache_version" != "$dev_version" ]]; then
        status="DRIFT"
        detail="cache=$cache_version dev=$dev_version dir=$cache_dir"
        EXIT_CODE=1
        print_row "$name" "$status" "$detail"
        return
    fi

    status="OK"
    detail="v$cache_version dir=$cache_dir"
    print_row "$name" "$status" "$detail"
}

run_check() {
    EXIT_CODE=0
    SHIM_SOURCE_ROOTS=()

    echo "Superstar deploy --check"
    echo "  source-root: $SOURCE_ROOT"
    if [[ -r "$SOURCE_ROOT/VERSION" ]]; then
        echo "  source-version: $(tr -d '[:space:]' < "$SOURCE_ROOT/VERSION")"
    else
        echo "  source-version: (missing $SOURCE_ROOT/VERSION)"
    fi
    echo
    echo "Global shims (~/.local/bin):"
    for n in external-reviewer reviewer-agent tasktool; do
        check_shim "$n"
    done

    # SOURCE_ROOT_INFO: informational only — if shims disagree on source-root
    local unique_roots=""
    for n in "${!SHIM_SOURCE_ROOTS[@]}"; do
        local r="${SHIM_SOURCE_ROOTS[$n]}"
        case " $unique_roots " in
            *" $r "*) ;;
            *) unique_roots="$unique_roots $r" ;;
        esac
    done
    # count tokens
    local count=0
    for r in $unique_roots; do count=$((count+1)); done
    if (( count > 1 )); then
        echo
        print_row "source-roots" "SOURCE_ROOT_INFO" "shims point at differing source roots:$unique_roots (informational)"
    fi

    echo
    echo "Pre-commit hook:"
    check_hook

    echo
    echo "Plugin caches:"
    local dev_version=""
    if [[ -r "$REPO_ROOT/VERSION" ]]; then
        dev_version="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
    fi
    check_cache "codex-cache" "${HOME}/.codex/plugins/cache/superstar-dev/superstar/current" "$dev_version"
    check_cache "claude-cache" "${HOME}/.claude/plugins/cache/superstar-dev/superstar/current" "$dev_version"

    echo
    if (( EXIT_CODE == 0 )); then
        echo "All checked rows OK."
    else
        echo "One or more rows failed; see statuses above."
    fi
    return "$EXIT_CODE"
}

run_deploy() {
    if (( SKIP_CODEX == 0 )); then
        echo "==> Publishing to local Codex cache"
        bash "$REPO_ROOT/scripts/publish-to-local-codex.sh"
    else
        echo "==> Skipping Codex publish (--claude-only)"
    fi

    if (( SKIP_CLAUDE == 0 )); then
        echo "==> Publishing to local Claude cache"
        bash "$REPO_ROOT/scripts/publish-to-local-claude.sh"
    else
        echo "==> Skipping Claude publish (--codex-only)"
    fi

    echo "==> Installing external-reviewer + reviewer-agent shims"
    bash "$REPO_ROOT/skills/project-setup/install-reviewer-agent.sh" --force

    echo "==> Installing tasktool shim"
    bash "$REPO_ROOT/tools/tasktool/install.sh" --force

    if git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "==> Installing tasktool pre-commit hook"
        bash "$REPO_ROOT/tools/tasktool/install.sh" --hook --force
    else
        echo "==> Skipping pre-commit hook (not inside a git work tree)"
    fi

    echo
    run_check
}

case "$MODE" in
    check)  run_check ;;
    deploy) run_deploy ;;
esac
