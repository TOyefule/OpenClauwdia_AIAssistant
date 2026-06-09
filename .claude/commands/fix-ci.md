---
name: fix-ci
description: Investigate and fix failing CI tests. Usage: /fix-ci [optional test filter or error snippet]
argument-hint: [test filter or error snippet]
allowed-tools: [Bash, Read, Edit, Write, Glob, Grep]
---

# Fix CI

Input: $ARGUMENTS (optional — test filter, file path, or error snippet from CI)

**Goal**: Find and fix the root cause of failing tests. Never paper over failures with `@ts-ignore`, skips, or `any`.

## Step 1 — Identify failures

If $ARGUMENTS provided, run targeted:
```bash
pnpm test -- $ARGUMENTS
```

Otherwise run the full suite:
```bash
OPENCLAW_TEST_PROFILE=low OPENCLAW_TEST_SERIAL_GATEWAY=1 pnpm test
```

## Step 2 — Triage

Determine if failure is:
- **(a) Real regression** — source code broke something tests relied on
- **(b) Test needs updating** — intentional behavior change, test not updated
- **(c) Flaky test** — non-deterministic; run 3x to confirm before touching

## Step 3 — Fix root cause

Read the failing test AND the source file it tests. Fix the underlying issue.

**Gotchas**:
- Use per-instance stubs in tests, not `SomeClass.prototype.method = ...`
- Never set Vitest workers above 16
- No mixed static+dynamic imports for same module in production paths
- If routing logic changed, run tests for ALL channels

## Step 4 — Type-check and lint

```bash
pnpm tsgo
pnpm check
```

## Step 5 — Verify fix

```bash
pnpm test -- <failing-test-path>
```

Then full suite if targeted test passes:
```bash
pnpm test
```

## Output

State:
1. Which test(s) failed and the root cause (not just the symptom)
2. What you changed: `file:line` with a brief explanation
3. Confirmation the fix passes: paste relevant test output
