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

require start "current checkout path" "checkout path"
require start "git root" "git root"
require start "HEAD SHA" "HEAD SHA"
require start "detached HEAD" "detached HEAD"
require start "isolated/secondary" "secondary classification"
require start "### WORKTREE WARNING" "WORKTREE WARNING"
require start "may not yet exist in the user's primary checkout" "primary-checkout warning"

require checkpoint "Inspect git status and the relevant diff" "status and diff"
require checkpoint "smallest sufficient targeted verification" "targeted verification"
require checkpoint "If verification materially fails, do not commit" "no commit on failed verification"
require checkpoint "cannot be separated safely" "unsafe separation"
require checkpoint "Never push by default" "never push by default"
require checkpoint "resulting commit SHA" "report commit SHA"
require checkpoint "intended primary branch is known to contain" "primary-contains-commit"
require checkpoint "whether the commit has been pushed" "pushed status"
require checkpoint "Never imply that a worktree commit exists in the primary checkout" "no false landing"

require end "### WORKTREE LANDING REQUIRED" "landing required section"
require end "do not declare SESSION COMPLETE" "no complete without landing"
require end "do not silently cherry-pick" "no silent cherry-pick"
require end "do not force" "no force"
require end "do not push an unintended detached/worktree state" "no unintended push"
require end "provably safe fast-forward" "safe fast-forward"
require end "intended session commits actually exist on the intended primary branch" "landing check"

POLICY="$REPO_ROOT/policies/EFFICIENT_AGENT.md"
if grep -q "^## Worktree discipline$" "$POLICY" \
    && grep -q "Do not create or switch to an isolated worktree for ordinary single-agent work." "$POLICY" \
    && grep -q "Never declare work landed until the intended branch actually contains it." "$POLICY"; then
    echo "PASS  efficiency policy worktree discipline"
    PASS=$((PASS + 1))
else
    echo "FAIL  efficiency policy worktree discipline"
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
