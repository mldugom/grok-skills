#!/bin/bash

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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
echo "LIFECYCLE METADATA VALIDATION"
echo

for skill in "${SKILLS[@]}"; do

    SRC="$REPO_ROOT/skills/lifecycle/$skill/SKILL.md"

    if [ ! -f "$SRC" ]; then
        echo "FAIL  /$skill canonical source missing"
        FAIL=$((FAIL + 1))
        continue
    fi

    FRONTMATTER="$(awk 'BEGIN { p = 0 } /^---$/ { p += 1; next } p == 1 { print }' "$SRC")"

    if [ -z "$FRONTMATTER" ]; then
        echo "FAIL  /$skill missing YAML frontmatter"
        FAIL=$((FAIL + 1))
        continue
    fi

    if ! printf '%s\n' "$FRONTMATTER" | grep -q "^name:[[:space:]]*$skill$"; then
        echo "FAIL  /$skill metadata name mismatch"
        FAIL=$((FAIL + 1))
        continue
    fi

    if ! printf '%s\n' "$FRONTMATTER" | grep -q "^user-invocable:[[:space:]]*true$"; then
        echo "FAIL  /$skill is not user-invocable"
        FAIL=$((FAIL + 1))
        continue
    fi

    if ! printf '%s\n' "$FRONTMATTER" | grep -q "^disable-model-invocation:[[:space:]]*true$"; then
        echo "FAIL  /$skill is not explicit-only"
        FAIL=$((FAIL + 1))
        continue
    fi

    echo "PASS  /$skill"
    PASS=$((PASS + 1))
done

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
