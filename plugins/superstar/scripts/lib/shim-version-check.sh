# scripts/lib/shim-version-check.sh
#
# Embedded by Superstar shim installers (skills/external-review/install.sh,
# skills/project-setup/install-reviewer-agent.sh, tools/tasktool/install.sh).
# Provides __superstar_check_version, which hard-exits the calling shim if
# the stamped shim version differs from $SOURCE_ROOT/VERSION.
#
# Strict failure ONLY when BOTH sides are readable AND they differ. Missing or
# unreadable VERSION, or an empty stamped value, means "cannot compare" and
# the shim continues to exec normally.
#
# Args:
#   $1  shim_version       e.g. "6.3.2"
#   $2  shim_name          e.g. "external-reviewer"
#   $3  source_root        absolute or $HOME/... path
#   $4  installer          relative path under source_root, e.g.
#                          "skills/external-review/install.sh"

__superstar_check_version() {
    local shim_version="$1"
    local shim_name="$2"
    local source_root="$3"
    local installer="$4"

    [[ -n "$shim_version" ]] || return 0
    local version_file="$source_root/VERSION"
    [[ -r "$version_file" ]] || return 0

    local src_version
    src_version="$(head -n1 "$version_file" 2>/dev/null | tr -d '[:space:]')"
    [[ -n "$src_version" ]] || return 0

    if [[ "$src_version" != "$shim_version" ]]; then
        printf 'ERROR: %s shim is %s but Superstar source is %s\n' \
            "$shim_name" "$shim_version" "$src_version" >&2
        printf 'Re-run: bash %s/%s\n' "$source_root" "$installer" >&2
        exit 1
    fi
}
