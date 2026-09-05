#!/bin/bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$ROOT/skills/lifecycle/handoff/SKILL.md"
PASS=0
FAIL=0

require() {
  local pattern="$1"
  local label="$2"
  if grep -q "$pattern" "$SKILL"; then
    echo "PASS  $label"
    PASS=$((PASS + 1))
  else
    echo "FAIL  missing $label"
    FAIL=$((FAIL + 1))
  fi
}

if [ -f "$SKILL" ]; then
  echo "PASS  handoff skill exists"
  PASS=$((PASS + 1))
else
  echo "FAIL  handoff skill missing"
  exit 1
fi

require '^name:[[:space:]]*handoff$' 'metadata name'
require '^user-invocable:[[:space:]]*true$' 'user invocable'
require '^disable-model-invocation:[[:space:]]*false$' 'automatic safe invocation allowed'
require 'BOT REPORT' 'BOT REPORT contract'
require 'READY_FOR_INTEGRATION_REVIEW' 'review-ready status'
require 'Integration Owner' 'human integration gate'
require 'Never use `DONE`, `CERTIFIED`, `MERGED`, `PROMOTED`, or `LIVE`' 'no self-certification'
require 'PR synchronize' 'new-SHA event semantics'
require 'Provider-neutral interface' 'provider-neutral boundary'

echo
echo "PASS: $PASS"
echo "FAIL: $FAIL"
[ "$FAIL" -eq 0 ]
