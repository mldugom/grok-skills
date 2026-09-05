#!/bin/bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GROK_HOME_DIR="${GROK_HOME:-$HOME/.grok}"

SKILLS=(
    start
    checkpoint
    prioritize
    audit
    handoff
    end
)

echo
echo "Installing Grok lifecycle skills"
echo "Source: $REPO_ROOT"
echo "Target: $GROK_HOME_DIR"
echo

for skill in "${SKILLS[@]}"; do

    SRC="$REPO_ROOT/skills/lifecycle/$skill/SKILL.md"
    DST="$GROK_HOME_DIR/skills/$skill/SKILL.md"

    if [ ! -f "$SRC" ]; then
        echo "ERROR: canonical source missing:"
        echo "  $SRC"
        exit 1
    fi

    mkdir -p "$(dirname "$DST")"

    cp "$SRC" "$DST"

    echo "INSTALLED /$skill"
done

mkdir -p "$GROK_HOME_DIR/policies"

cp \
    "$REPO_ROOT/policies/EFFICIENT_AGENT.md" \
    "$GROK_HOME_DIR/policies/EFFICIENT_AGENT.md"

echo "INSTALLED efficiency policy"

echo
echo "Done."
