#!/bin/bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GROK_HOME_DIR="${GROK_HOME:-$HOME/.grok}"
CONFIG="$GROK_HOME_DIR/config.toml"
ZSHRC="$HOME/.zshrc"
SOURCE_LINE='source "$HOME/repos/grok-skills/shell/grok-safe.zsh"'

mkdir -p "$GROK_HOME_DIR"

if [ -f "$CONFIG" ]; then
    cp "$CONFIG" "$CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
else
    touch "$CONFIG"
fi

python - "$CONFIG" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
text = p.read_text()
lines = text.splitlines()

# Replace or append [ui.status_line] without disturbing other sections.
out = []
i = 0
replaced = False
while i < len(lines):
    line = lines[i]
    if line.strip() == "[ui.status_line]":
        replaced = True
        out.append("[ui.status_line]")
        out.append('type = "builtin"')
        out.append('items = ["cwd", "model", "context", "cost", "turn-timer"]')
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith("[") and s.endswith("]"):
                break
            i += 1
        continue
    out.append(line)
    i += 1

if not replaced:
    if out and out[-1].strip():
        out.append("")
    out.extend([
        "[ui.status_line]",
        'type = "builtin"',
        'items = ["cwd", "model", "context", "cost", "turn-timer"]',
    ])

p.write_text("\n".join(out).rstrip() + "\n")
PY

if [ -f "$ZSHRC" ]; then
    cp "$ZSHRC" "$ZSHRC.backup.$(date +%Y%m%d_%H%M%S)"
else
    touch "$ZSHRC"
fi

if ! grep -Fqx "$SOURCE_LINE" "$ZSHRC"; then
    {
        echo
        echo "# Grok safe launcher (managed by ~/repos/grok-skills)"
        echo "$SOURCE_LINE"
    } >> "$ZSHRC"
fi

echo "Configured Grok runtime controls."
echo "- status line: cwd, model, context, cost, turn timer"
echo "- grok-safe source: $REPO_ROOT/shell/grok-safe.zsh"
echo
printf '%s\n' "Run: source ~/.zshrc"
