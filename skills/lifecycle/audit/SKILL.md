---
name: audit
description: Perform a read-only repository integrity audit for redundant code, architectural gaps, undocumented processes, leakage, stale paths, production risks, and technical debt.
when-to-use:
  - audit repository
  - find technical debt
  - find duplicate code
  - assess repository health
user-invocable: true
disable-model-invocation: true
argument-hint: "[optional scope: full|code|data|modeling|production]"
metadata:
  author: mldugom
  short-description: Read-only repository health audit
---

# /audit — Repository Integrity Audit

This command is READ-ONLY by default.

Do not:
- modify code,
- delete files,
- refactor,
- commit,
- push,
- migrate databases,
- rerun expensive pipelines,
- alter production infrastructure.

The goal is diagnosis and prioritization.

## Audit strategy

Start with repository structure, instructions, project state, recent changes, and relevant configuration.

Audit this working copy. If the session is in a git-linked or Grok isolated worktree, say so and do not silently switch to the source checkout.

Prefer evidence-driven sampling over indiscriminate file reading.

If the repository is large, identify the most important execution paths and audit those first.

After approximately 5 investigative steps, synthesize what is known before broadening investigation.

## Audit dimensions

### 1. Architecture

Look for:

- duplicate implementations,
- multiple competing sources of truth,
- abandoned architecture,
- unnecessary indirection,
- circular dependencies,
- accidental coupling,
- unclear ownership boundaries,
- missing interfaces,
- modules that bypass intended architecture,
- transitional code that became permanent.

### 2. Code quality

Look for:

- dead code,
- duplicate logic,
- stale scripts,
- copy-pasted functionality,
- obsolete compatibility layers,
- unreferenced utilities,
- TODO/FIXME accumulation,
- overly broad modules,
- hidden side effects,
- error swallowing,
- inconsistent conventions that create correctness risk.

Do not equate stylistic differences with defects.

### 3. Repository hygiene

Inspect for:

- stale documentation,
- documentation/code disagreement,
- generated artifacts committed unnecessarily,
- large unexpected files,
- secrets or credential risk,
- untracked important state,
- obsolete branches/scripts referenced by current docs,
- unclear entry points,
- missing reproduction instructions.

### 4. Data architecture

When applicable inspect:

- source provenance,
- raw versus transformed boundaries,
- undocumented datasets,
- duplicate ingestion paths,
- schema drift,
- silent missing-data handling,
- non-idempotent processes,
- incomplete retry behavior,
- stale-data risk,
- event-time versus processing-time confusion,
- irreproducible transformations.

### 5. Quantitative / modeling integrity

When applicable inspect:

- target leakage,
- temporal leakage,
- discovery versus evaluation contamination,
- repeated holdout tuning,
- multiple-testing risk,
- untracked experiments,
- unstable samples,
- survivorship bias,
- look-ahead bias,
- label inconsistencies,
- unreproducible model artifacts,
- inconsistent metrics,
- evaluation/production feature mismatch.

### 6. Financial / trading integrity

When applicable inspect:

- unrealistic fills,
- missing transaction costs,
- market-timing assumptions,
- stale prices,
- incorrect event-time availability,
- silent position duplication,
- inconsistent sizing,
- execution/research mismatch,
- portfolio aggregation errors,
- missing concentration or ruin controls.

### 7. Production readiness

Look for:

- manual undocumented operations,
- silent failure modes,
- missing health checks,
- missing telemetry,
- unbounded retries,
- non-idempotent jobs,
- duplicate runners,
- scheduling gaps,
- stale workers,
- brittle credentials/configuration,
- missing rollback paths,
- missing operator visibility.

### 8. Testing

Assess:

- critical paths without tests,
- tests disconnected from production behavior,
- brittle fixtures,
- missing integration coverage,
- missing data-contract tests,
- overreliance on broad tests where targeted tests are needed,
- tests that cannot reproduce claimed behavior.

### 9. Documentation and operational knowledge

Identify:

- undocumented workflows,
- tribal knowledge encoded only in scripts or chat,
- stale runbooks,
- unclear source-of-truth documents,
- missing project-state handoff,
- missing decision records for material architecture choices.

### 10. Efficiency / waste

Look for:

- unnecessary full-history recomputation,
- duplicated pipelines,
- redundant caches,
- repeated downloads,
- unnecessary model calls,
- jobs that can silently remain alive,
- repeated repository scans,
- expensive tasks with no explicit output consumer.

## Evidence standard

Every material finding should include concrete evidence such as:

- file path,
- symbol/function,
- configuration,
- command/result,
- architectural relationship,
- documentation discrepancy.

Avoid speculative findings unsupported by repository evidence.

## Severity

Classify findings:

### CRITICAL
Can cause material corruption, leakage, loss, security exposure, false results, or production failure.

### HIGH
Likely correctness, operational, architectural, or reproducibility failure.

### MEDIUM
Meaningful technical debt, ambiguity, inefficiency, or maintainability risk.

### LOW
Minor cleanup or improvement.

## Output

### EXECUTIVE SUMMARY

### CRITICAL FINDINGS

### HIGH FINDINGS

### MEDIUM FINDINGS

### LOW FINDINGS

For each finding provide:

- Finding
- Evidence
- Impact
- Recommended remediation
- Estimated effort: S / M / L
- Confidence: High / Medium / Low

### DUPLICATION / DEAD CODE MAP

### UNDOCUMENTED OR FRAGILE PROCESSES

### ARCHITECTURAL VOIDS

### DATA / MODEL INTEGRITY RISKS
When applicable.

### PRODUCTION RISKS
When applicable.

### TOP 10 REMEDIATIONS
Ranked by risk reduction and value.

### WHAT NOT TO FIX YET
Identify cleanup that would create activity without meaningful value.

Do not implement remediation during `/audit`.

Stop after delivering the audit.
