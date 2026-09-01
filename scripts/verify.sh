#!/bin/bash

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GROK_HOME_DIR="${GROK_HOME:-$HOME/.grok}"

SKILLS=(
    start
    checkpoint
    prioritize
    audit
    end
)

PASS=0
FAIL=0

echo
echo "GROK LIFECYCLE VERIFICATION"
echo

for skill in "${SKILLS[@]}"; do

    SRC="$REPO_ROOT/skills/lifecycle/$skill/SKILL.md"
    DST="$GROK_HOME_DIR/skills/$skill/SKILL.md"

    if [ ! -f "$SRC" ]; then
        echo "FAIL  /$skill canonical source missing"
        FAIL=$((FAIL + 1))
        continue
    fi

    if [ ! -f "$DST" ]; then
        echo "FAIL  /$skill not installed"
        FAIL=$((FAIL + 1))
        continue
    fi

    if ! grep -q "^name:[[:space:]]*$skill" "$SRC"; then
        echo "FAIL  /$skill metadata name mismatch"
        FAIL=$((FAIL + 1))
        continue
    fi

    if ! grep -q "^user-invocable:[[:space:]]*true" "$SRC"; then
        echo "FAIL  /$skill is not user-invocable"
        FAIL=$((FAIL + 1))
        continue
    fi

    if ! grep -q "^disable-model-invocation:[[:space:]]*true" "$SRC"; then
        echo "FAIL  /$skill is not explicit-only"
        FAIL=$((FAIL + 1))
        continue
    fi

    if cmp -s "$SRC" "$DST"; then
        echo "PASS  /$skill"
        PASS=$((PASS + 1))
    else
        echo "FAIL  /$skill installed copy differs from repo"
        FAIL=$((FAIL + 1))
    fi
done

echo

if cmp -s \
    "$REPO_ROOT/policies/EFFICIENT_AGENT.md" \
    "$GROK_HOME_DIR/policies/EFFICIENT_AGENT.md"; then

    echo "PASS  efficiency policy"
    PASS=$((PASS + 1))
else
    echo "FAIL  efficiency policy differs"
    FAIL=$((FAIL + 1))
fi

echo
echo "PASS: $PASS"
echo "FAIL: $FAIL"

if [ "$FAIL" -eq 0 ]; then
    echo
    echo "STATUS: CLEAN"
    exit 0
else
    echo
    echo "STATUS: NEEDS ATTENTION"
    exit 1
fi
