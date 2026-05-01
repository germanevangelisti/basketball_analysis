---
name: feature-done
description: Close a feature as complete. Validates full DoD, updates the KB doc status, creates a PR with the implementation log as description, and archives the feature.
---

You are closing a feature as complete. This is the final gate before merge.

## Step 1 — Load feature context

```bash
git branch --show-current
```

Derive slug. If not on a feature branch → STOP.

Read:
- `knowledge/implementation/<slug>/dod.md`
- `knowledge/implementation/<slug>/log.md`
- `knowledge/implementation/<slug>/status.json`

## Step 2 — Final DoD validation

Read `dod.md`. Count ✅ and ❌ items.

If ANY item is ❌ or still `[ ]` (unchecked) → STOP:

```
## Cannot complete feature — DoD not satisfied

Blocking items:
❌ <item>: <reason>
[ ] <item>: not yet reviewed

Run /feature-review first. All DoD items must be ✅ before closing.
```

If status in `status.json` is not `"approved"` → STOP:
"Feature has not passed review. Run /feature-review first."

## Step 3 — Final commit check

```bash
git status --short
git log --oneline main..HEAD
```

If there are uncommitted changes → commit them:
```bash
git add <specific files>
git commit -m "chore(<slug>): finalize implementation"
```

## Step 4 — Update KB doc status

Read the KB doc at the path in `status.json → kb_doc`.

Add or update a status line at the top of the doc:
```markdown
> **Status:** IMPLEMENTED — <ISO date> | Branch: feature/<slug>
```

Commit this change:
```bash
git add knowledge/<kb-doc>
git commit -m "docs(<slug>): mark KB doc as implemented"
```

## Step 5 — Append completion to log

Append to `knowledge/implementation/<slug>/log.md`:
```markdown
## [<ISO timestamp>] Feature COMPLETED

DoD: all items ✅
PR: [to be added after creation]
```

Update `status.json`: `"status": "done"`, update `last_updated`.

Commit:
```bash
git add knowledge/implementation/<slug>/
git commit -m "chore(<slug>): close feature log"
```

## Step 6 — Create PR

Build the PR body from the log. Use:
- Feature name as title
- Summary from `plan.md` → Summary section
- DoD checklist from `dod.md`
- Key decisions and test results from `log.md`

```bash
gh pr create \
  --title "<feature name>" \
  --base main \
  --body "$(cat <<'EOF'
## Summary
<extracted from plan.md>

## Implementation log
<key decisions and changes from log.md>

## Definition of Done
<paste dod.md contents>

## Test results
<from last QA review in log.md>

🤖 Generated with Claude Code
EOF
)"
```

## Step 7 — Report to engineer

```
## Feature complete ✓

PR: <URL>

DoD: X/X items ✅
Commits on branch: <count>
Log archived: knowledge/implementation/<slug>/log.md

KB doc updated: knowledge/<doc>

--- What's next ---
1. Review the PR: <URL>
2. Merge when ready
3. Next feature in roadmap: <suggest next KB task based on dependency graph>
```
