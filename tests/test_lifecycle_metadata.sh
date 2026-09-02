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

    echo "PASS  /$skill metadata"
    PASS=$((PASS + 1))
done

echo
echo "LIFECYCLE V1.1 CONTRACTS"
echo

require() {
    local skill="$1"
    local pattern="$2"
    local label="$3"
    local src="$REPO_ROOT/skills/lifecycle/$skill/SKILL.md"

    if grep -q "$pattern" "$src"; then
        echo "PASS  /$skill $label"
        PASS=$((PASS + 1))
    else
        echo "FAIL  /$skill missing $label"
        FAIL=$((FAIL + 1))
    fi
}

forbid() {
    local skill="$1"
    local pattern="$2"
    local label="$3"
    local src="$REPO_ROOT/skills/lifecycle/$skill/SKILL.md"

    if grep -q "$pattern" "$src"; then
        echo "FAIL  /$skill still has $label"
        FAIL=$((FAIL + 1))
    else
        echo "PASS  /$skill $label absent"
        PASS=$((PASS + 1))
    fi
}

for skill in "${SKILLS[@]}"; do
    require "$skill" "worktree" "worktree-awareness"
done

require start "### WORKSPACE" "WORKSPACE output"
require checkpoint "commit intended session work" "default checkpoint commits"
require checkpoint "Do not push" "checkpoint does not push"
forbid checkpoint "Do NOT automatically commit" "opt-in-only commits"
require end "source checkout" "end worktree source reporting"

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
