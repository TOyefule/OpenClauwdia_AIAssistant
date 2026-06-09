# Coding Style Rules — OpenClaw

## Language & types

- TypeScript ESM only; strict typing throughout
- No `any` — fix root causes instead
- No `@ts-nocheck` — ever
- No prototype mutation (`applyPrototypeMixins`, `Object.defineProperty` on `.prototype`, exporting `.prototype` for merges)
- Use explicit inheritance (`A extends B extends C`) or composition for shared behavior

## Formatting

- Linter: Oxlint
- Formatter: Oxfmt
- Run before every commit: `pnpm check`
- Auto-fix: `pnpm format:fix`

## File size guideline

- Aim for ~700 LOC per file (not a hard limit)
- Split/refactor when it improves clarity or testability
- Extract helpers instead of creating "V2" copies

## Dynamic imports

- Production paths: never mix `await import("x")` (dynamic) and `import x from "x"` (static) for the same module
- For lazy loading: create a dedicated `*.runtime.ts` boundary file, dynamically import only that
- After any refactor touching module boundaries: run `pnpm build` and check for `[INEFFECTIVE_DYNAMIC_IMPORT]` warnings

## Comments

- Add comments only for tricky or non-obvious logic (hidden constraints, subtle invariants, bug workarounds)
- Never explain WHAT the code does (identifiers do that); only explain WHY if non-obvious
- No multi-paragraph docstrings or multi-line comment blocks — one short line max

## Naming

- Product/app/docs headings: **OpenClaw**
- CLI command, package, binary, paths, config keys: `openclaw`
- American spelling: "color" not "colour", "behavior" not "behaviour", "analyze" not "analyse"

## Testing

- Framework: Vitest with V8 coverage
- File naming: `*.test.ts` colocated with source; e2e in `*.e2e.test.ts`
- Coverage thresholds: 70% lines/branches/functions/statements
- Per-instance stubs in tests — no prototype-level patching unless explicitly documented
- Never set Vitest workers above 16

## Dependency rules

- Exact versions (no `^`/`~`) for anything in `pnpm.patchedDependencies`
- Patching dependencies requires explicit approval
- Never update the Carbon dependency
- Plugin-only deps in the extension `package.json`; do not add to root unless core uses them
