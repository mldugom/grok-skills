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
LAUNCHER="$REPO_ROOT/shell/grok-safe.zsh"
RUNTIME="$REPO_ROOT/scripts/configure-runtime.sh"

check_policy() {
    local pattern="$1"
    local label="$2"
    if grep -q "$pattern" "$POLICY"; then
        echo "PASS  efficiency policy $label"
        PASS=$((PASS + 1))
    else
        echo "FAIL  efficiency policy missing $label"
        FAIL=$((FAIL + 1))
    fi
}

echo
echo "EFFICIENCY V1.2 CONTRACTS"
echo

check_policy "^## Worktree discipline$" "worktree discipline"
check_policy "One substantial epic or research question per session" "one-epic default"
check_policy "roughly 20 total tool calls" "implementation tool budget"
check_policy "At or above ~200k" "200k stop-new-scope rule"
check_policy "At or above ~250k" "250k end-session rule"
check_policy "^## Plan-mode discipline$" "plan-mode discipline"
check_policy "^## Verbose-command discipline$" "verbose-output discipline"
check_policy "^## Testing discipline$" "testing discipline"
check_policy "historical decision timestamp" "point-in-time research integrity"
check_policy "go directly to `/end` rather than checkpointing and ending back-to-back" "checkpoint/end deduplication"

if [ -f "$LAUNCHER" ] \
    && grep -q -- "--max-turns 6" "$LAUNCHER" \
    && grep -q -- "--no-subagents" "$LAUNCHER" \
    && grep -q -- "--rules" "$LAUNCHER"; then
    echo "PASS  grok-safe launcher cost controls"
    PASS=$((PASS + 1))
else
    echo "FAIL  grok-safe launcher missing cost controls"
    FAIL=$((FAIL + 1))
fi

if [ -f "$RUNTIME" ] \
    && grep -q '"context", "cost", "turn-timer"' "$RUNTIME" \
    && grep -q 'grok-safe.zsh' "$RUNTIME"; then
    echo "PASS  runtime setup status-line + launcher install"
    PASS=$((PASS + 1))
else
    echo "FAIL  runtime setup missing status-line or launcher install"
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
