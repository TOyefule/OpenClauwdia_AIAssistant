# GitHub Operations Rules — OpenClaw

## Comment formatting

- Body with backticks or shell chars: always use single-quoted heredoc (`-F - <<'EOF'`), never `-b "..."`
- Real newlines in comments: use literal multiline strings or `$'...'` — never embed `\n` escape sequences
- Auto-linking issue/PR refs: use plain `#24643`, not `` `#24643` `` (backticks break GitHub auto-linking)

## PR review truthfulness gate

Never merge a bug-fix PR on issue text, PR description, or AI rationale alone. Required evidence:

1. Symptom evidence (repro/log/failing test)
2. Root cause in code: `file:line` + explanation
3. Fix touches that exact code path
4. Regression test (fail before / pass after); if not feasible, manual proof + reason

If unsubstantiated → request evidence or close with `invalid`. No speculative merges.

## Searching — avoid the 500-result cap

When searching all issues or PRs, keep paginating until you reach the last page:

```bash
gh search prs --repo openclaw/openclaw --match title,body --limit 50 -- "keyword"
gh search issues --repo openclaw/openclaw --match title,body --limit 50 --json number,title,state,url,updatedAt -- "keyword" \
  --jq '.[] | "\(.number) | \(.state) | \(.title) | \(.url)"'
```

Add `--match comments` when triaging follow-up threads.

## Auto-close labels

Let `.github/workflows/auto-response.yml` handle comment/close/lock — do not manually close + comment for these labels:

`r: skill`, `r: support`, `r: no-ci-pr`, `r: too-many-prs`, `r: testflight`, `r: third-party-extension`, `r: moltbook`, `r: spam`, `invalid`, `dirty`

## Bulk operations safety

If a close/reopen action would affect more than **5 PRs**, ask for explicit user confirmation with exact PR count and scope before proceeding.

## Security advisories (GHSA)

- Read `SECURITY.md` before any triage or severity decision
- Cannot set `severity` and `cvss_vector_string` in the same PATCH call — do two separate calls
- Verify private fork has zero open PRs before publishing an advisory
- Write description bodies via heredoc to a temp file (never `\n` strings)

## CODEOWNERS restriction

Do not edit files covered by security-focused `CODEOWNERS` rules unless a listed owner explicitly asked for the change or is actively reviewing it with you. Treat those paths as restricted — not candidates for drive-by cleanup.

## PR commit landing comments

When landing a PR, make commit SHAs clickable with full commit links (both landed SHA + source SHA when present).

## PR review bot conversations

Address and resolve bot-opened review conversations once fixed. Leave unresolved only when reviewer/maintainer judgment is still needed. Do not leave bot cleanup to maintainers.
