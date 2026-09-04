# Source this file from ~/.zshrc.
# Canonical source: ~/repos/grok-skills/shell/grok-safe.zsh

grok-safe() {
    local GROK_BIN="$HOME/.grok/bin/grok"
    local POLICY="$HOME/.grok/policies/EFFICIENT_AGENT.md"

    if [[ ! -x "$GROK_BIN" ]]; then
        echo "grok-safe: Grok binary not found at $GROK_BIN" >&2
        return 1
    fi

    if [[ ! -f "$POLICY" ]]; then
        echo "grok-safe: efficiency policy not found at $POLICY" >&2
        echo "Run ~/repos/grok-skills/scripts/install.sh first." >&2
        return 1
    fi

    "$GROK_BIN" \
        --rules "$(cat "$POLICY")" \
        --max-turns 6 \
        --no-subagents \
        "$@"
}
