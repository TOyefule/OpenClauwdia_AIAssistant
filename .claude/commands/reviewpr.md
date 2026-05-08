---
name: reviewpr
description: Review a pull request thoroughly. Usage: /reviewpr <PR number or URL>
argument-hint: <PR number>
allowed-tools: [Bash, Read, Glob, Grep, WebFetch]
---

# PR Review

Input: $ARGUMENTS (PR number or URL — if missing, use the most recent PR mentioned in conversation)

**Goal**: Produce a thorough review and a clear verdict. Do NOT merge, push, or modify the repo.

## Step 0 — Truthfulness gate (required for bug-fix PRs)

Do not trust the issue text or PR summary. Verify in code:
- Confirm the bug exists in the current codebase (repro/log/failing test/code-path proof)
- Pinpoint root cause: `path/file.ts:line` + explanation of why behavior is wrong
- Verify fix targets the same code path
- Require regression test (fail before / pass after); if not feasible, require manual proof + justification

Hallucination red flags (treat as BLOCKER until disproven):
- Changed files don't touch implicated path
- Only docs/comments changed for a runtime bug claim
- Vague AI rationale without concrete evidence

## Step 1 — Fetch PR metadata

```bash
gh pr view $ARGUMENTS --json number,title,state,isDraft,author,baseRefName,headRefName,url,body,labels,files,additions,deletions \
  --jq '{number,title,url,state,isDraft,author:.author.login,base:.baseRefName,head:.headRefName,additions,deletions,files:.files|length}'
```

## Step 2 — Read the PR description

Summarize: stated goal, scope, "why now?" rationale. Flag missing context (motivation, alternatives, rollout/compat notes, risk).

## Step 3 — Read the diff

```bash
gh pr diff $ARGUMENTS
```

## Step 4 — Validate the change

- What user/dev pain does this solve?
- Is this the smallest reasonable fix?
- Does it introduce complexity for marginal benefit?
- Does it need a changelog entry or docs update?

## Step 5 — Check project conventions

- TypeScript: strict types, no `any`, no `@ts-nocheck`
- Style: Oxlint/Oxfmt compliant; American spelling
- Tests: colocated `*.test.ts`; coverage 70%+
- Security: no hardcoded secrets, no injection vectors
- Channels: if routing/allowlist/onboarding touched, verify ALL channels covered
- Changelog: user-facing only; appended to end of section; ≤1 contributor mention per line

## Output

```
## Review: PR #<N> — <title>

**Verdict**: READY TO LAND | NEEDS WORK | INVALID CLAIM

### Summary
<what this PR does>

### Evidence (bug-fix PRs)
- Bug confirmed at: <file:line>
- Root cause: <explanation>
- Fix location: <file:line>
- Regression test: <present / absent / justified>

### Issues
- [ ] BLOCKER: <description>
- [ ] SUGGESTION: <description>

### Positives
- <what was done well>
```
