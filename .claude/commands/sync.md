---
name: sync
description: Commit all dirty changes then pull --rebase and push. Stops on rebase conflicts.
allowed-tools: [Bash]
---

# Sync

Commit everything in the working tree, integrate upstream, and push.

## Steps

1. **Check state**
   ```bash
   git status
   git diff --stat
   ```

2. **If working tree is dirty** — commit all changes with a sensible Conventional Commit message scoped to what changed (e.g. `feat: add X`, `fix: correct Y`, `chore: update Z`).

   Use `scripts/committer` if available:
   ```bash
   scripts/committer "<message>" <file1> <file2> ...
   ```
   Otherwise stage and commit specific files (never `git add -A` with unreviewed files):
   ```bash
   git add <specific-files>
   git commit -m "<Conventional Commit message>"
   ```

3. **Pull with rebase**
   ```bash
   git pull --rebase origin $(git branch --show-current)
   ```
   If rebase conflicts occur: stop, report the conflicting files, and ask the user to resolve manually.

4. **Push**
   ```bash
   git push -u origin $(git branch --show-current)
   ```

## Safety rules

- Never use `git add -A` — stage only files you've intentionally changed
- Never use `--no-verify` on commit or push
- Never stash (multi-agent safety: other agents may have WIP)
- Never switch branches
- On rebase conflict: stop and report — do not force-resolve
