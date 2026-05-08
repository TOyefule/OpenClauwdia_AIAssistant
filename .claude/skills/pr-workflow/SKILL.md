---
name: pr-workflow
description: OpenClaw PR review, preparation, and merge workflow. Load when triaging issues, reviewing PRs, or landing changes.
disable-model-invocation: false
user-invocable: false
---

# PR Workflow — OpenClaw

## Auto-close labels

Apply the label and let `.github/workflows/auto-response.yml` handle comment/close/lock. Do not manually close + comment.

| Label | When to use |
|-------|-------------|
| `r: skill` | Requests to add features better shipped as Clawhub skills |
| `r: support` | Support questions → redirect to Discord |
| `r: no-ci-pr` | Test-fix-only PRs for already-failing `main` CI |
| `r: too-many-prs` | Author exceeds active PR limit |
| `r: testflight` | TestFlight requests (not available; build from source) |
| `r: third-party-extension` | Features better shipped as third-party plugins |
| `r: moltbook` | Off-topic (not affiliated) |
| `r: spam` | Spam — close + lock |
| `invalid` | Invalid items |
| `dirty` | PRs with too many unrelated changes |

## Merge gate (bug-fix PRs)

Never merge based on issue text, PR text, or AI rationale alone. Require:
1. Symptom evidence (repro/log/failing test)
2. Root cause verified in code with `file:line`
3. Fix touches the implicated code path
4. Regression test (fail before/pass after) OR manual proof + reason test wasn't added

If claim is unsubstantiated: request evidence, or close with `invalid`.

## Commit format

Use `scripts/committer "<msg>" <file...>` to scope staging. Commit messages are action-oriented: `CLI: add verbose flag to send`, `fix: correct routing for WhatsApp`. Group related changes; avoid bundling unrelated refactors.

## PR size

Soft limit: ≤150 lines diff (median). Flag larger PRs for scope review.

## Changelog rules

- User-facing changes only — no internal/meta notes
- Append to **end** of the target section (`### Changes` or `### Fixes`)
- ≤1 contributor mention per line: use `Thanks @author`, not `by @author` on the same line
- Pure test additions do not need a changelog entry unless they alter user-facing behavior

## GitHub search — avoiding the 500-result trap

When searching all issues/PRs (not just recent):
```bash
gh search prs --repo openclaw/openclaw --match title,body --limit 50 -- "keyword"
gh search issues --repo openclaw/openclaw --match title,body --limit 50 -- "keyword"
```
Keep paginating until you reach the last page — don't stop at 500.

## Git footguns

- GitHub comment with backticks/shell chars: use `-F - <<'EOF'` heredoc, never `-b "..."`
- Auto-linking: use plain `#24643` not `` `#24643` ``
- Bulk close safety: if >5 PRs affected, ask for explicit confirmation first
- Branch delete if policy-blocked: `git update-ref -d refs/heads/<branch>`

## GHSA advisories

Before triage: read `SECURITY.md` first. API cannot set `severity` and `cvss_vector_string` in same PATCH — do separate calls. Verify private fork has no open PRs before publishing (`state: "published"`).
