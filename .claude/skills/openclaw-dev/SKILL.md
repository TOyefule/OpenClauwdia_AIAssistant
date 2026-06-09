---
name: openclaw-dev
description: OpenClaw project-specific patterns, gotchas, and non-obvious conventions. Load when working on source code, tests, or CI for this repo.
disable-model-invocation: false
user-invocable: false
---

# OpenClaw Development — Gotchas & Patterns

This skill contains information that shifts Claude's behavior beyond defaults for OpenClaw development. It focuses on what's non-obvious, not general TypeScript knowledge.

## Runtime & package manager

- Node **22+** required; keep both Node and Bun paths working
- Prefer **Bun** for TypeScript execution: `bun <file.ts>` / `bunx <tool>`
- Install deps: `pnpm install` (primary) or `bun install`
- If `node_modules` missing or `vitest not found`: run install, then retry once

## Build & type check

```bash
pnpm build          # TypeScript build + [INEFFECTIVE_DYNAMIC_IMPORT] warnings check
pnpm tsgo           # TypeScript checks only
pnpm check          # Lint + format (Oxlint + Oxfmt)
pnpm format:fix     # Auto-fix formatting
```

After any refactor touching lazy-loading/module boundaries: run `pnpm build` and check for `[INEFFECTIVE_DYNAMIC_IMPORT]` warnings.

## Dynamic import guardrail

**Do not mix** `await import("x")` and `import x from "x"` for the same module in production paths. If you need lazy loading, create a `*.runtime.ts` boundary that re-exports from `x`, and dynamically import only that boundary.

## Class composition

Never use prototype mutation (`applyPrototypeMixins`, `Object.defineProperty` on `.prototype`). Use explicit inheritance (`A extends B extends C`) or helper composition so TypeScript can typecheck. If you think you need it, stop and ask.

## Test gotchas

- Run: `pnpm test -- <path-or-filter>` (not raw `pnpm vitest run` — bypasses wrapper config)
- Workers: never set above 16
- Low-memory hosts: `OPENCLAW_TEST_PROFILE=low OPENCLAW_TEST_SERIAL_GATEWAY=1 pnpm test`
- Per-instance stubs only — no `SomeClass.prototype.method = ...` in tests unless explicitly documented
- Coverage threshold: 70% lines/branches/functions/statements

## Channel coverage

When touching routing, allowlists, pairing, command gating, or onboarding: consider ALL channels.

**Core**: `src/telegram`, `src/discord`, `src/slack`, `src/signal`, `src/imessage`, `src/web`, `src/channels`, `src/routing`
**Extensions**: `extensions/msteams`, `extensions/matrix`, `extensions/zalo`, `extensions/zalouser`, `extensions/voice-call`

## CLI progress & status output

- Progress bars/spinners: use `src/cli/progress.ts` (`osc-progress` + `@clack/prompts`)
- Tables + ANSI: `src/terminal/table.ts`
- Status: `--all` = read-only/pasteable; `--deep` = live probes; `--deep --require-rpc` for gateway verification

## Gateway (macOS)

Gateway runs as the menubar app, not a separate LaunchAgent. Restart via the OpenClaw Mac app or `scripts/restart-mac.sh`. To verify/kill: `launchctl print gui/$UID | grep openclaw`. Never start gateway in ad-hoc tmux sessions.

## Version locations (bump everywhere)

When bumping versions: `package.json`, `apps/android/app/build.gradle.kts`, `apps/ios/Sources/Info.plist`, `apps/ios/Tests/Info.plist`, `apps/macos/Sources/OpenClaw/Resources/Info.plist`, `docs/install/updating.md`. Do **not** touch `appcast.xml` unless cutting a macOS Sparkle release.

## Dependency rules

- Any dep in `pnpm.patchedDependencies` must use exact version (no `^`/`~`)
- Patching deps requires explicit approval — do not patch by default
- Never update the Carbon dependency

## SwiftUI

Prefer `Observation` framework (`@Observable`, `@Bindable`) over `ObservableObject`/`@StateObject`. Migrate existing usages when touching related code.

## Naming

- Product/app/docs headings: **OpenClaw**
- CLI command, package, paths, config keys: `openclaw`
- American spelling throughout: "color", "behavior", "analyze"
