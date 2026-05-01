---
name: feature-start
description: Start implementing a KB feature. Checks DoR, creates git branch, generates implementation plan, and initializes the persistent feature log. Args: path to KB doc (e.g. knowledge/04_mejoras_visuales_hud.md)
---

You are orchestrating the start of a new feature. Follow these steps exactly and stop at any failure point.

## Step 1 — Parse input

Extract the KB doc path from args. Derive the feature slug:
- Strip `knowledge/` prefix and `.md` suffix
- Replace all `_` with `-`, lowercase
- Example: `knowledge/04_mejoras_visuales_hud.md` → slug = `04-mejoras-visuales-hud`

## Step 2 — Read KB doc

Read the full KB doc. Extract:
- Feature name
- Listed dependencies (other tasks that must be complete first)
- Definition of Done criteria (usually the last section)

## Step 3 — DoR Check (Definition of Ready)

Run these checks and present results to the engineer:

```bash
# Clean working tree?
git status --short

# Branch already exists?
git branch --list feature/<slug>

# All tests passing?
python -m pytest tests/ -q --no-header 2>&1 | tail -5
```

Present the checklist:
```
## DoR — [Feature name]

Specification:
[ ] KB doc exists and has no ⚠️ open questions blocking implementation
[ ] Acceptance criteria are unambiguous and testable

Dependencies:
[ ] <dependency 1> — status: [DONE / PENDING / WAIVED]
[ ] <dependency 2> — ...

Environment:
[ ] Working tree is clean
[ ] Feature branch feature/<slug> does not already exist
[ ] All existing tests pass
```

If any item FAILS → ask the engineer: "DoR has blockers. Proceed anyway? (y/n)"
If engineer says no → STOP here.

## Step 4 — Create feature branch

```bash
git checkout -b feature/<slug>
```

Confirm the branch was created: `git branch --show-current`

## Step 5 — Run planner agent

Invoke the `planner` subagent. Pass it:
1. The KB doc path
2. Instruction: "Read the KB doc, read all referenced source files, and produce the full implementation plan. Save the output to `knowledge/implementation/<slug>/plan.md` — create that file with the Write tool."

Wait for the planner to complete.

## Step 6 — Initialize persistent feature logs

After the planner finishes, create these files:

**`knowledge/implementation/<slug>/dod.md`** — extract the DoD from plan.md:
```markdown
# DoD — [Feature name]

Source: knowledge/<kb-doc>
Branch: feature/<slug>

## Standard criteria (every feature)
- [ ] All existing tests pass after implementation
- [ ] New tests written for every new public method
- [ ] No regressions in main.py pipeline
- [ ] Implementation log updated with key decisions

## Feature-specific criteria (from KB doc)
- [ ] <criterion extracted from KB>
- [ ] <criterion extracted from KB>
...
```

**`knowledge/implementation/<slug>/log.md`** — initialize:
```markdown
# Implementation Log — [Feature name]

KB doc: knowledge/<kb-doc>
Branch: feature/<slug>
Started: <ISO timestamp>

---

## [<timestamp>] Feature started

- DoR result: [PASSED / PASSED WITH WAIVERS: list]
- Plan: knowledge/implementation/<slug>/plan.md
- Engineer: German Evangelisti
```

**`knowledge/implementation/<slug>/status.json`**:
```json
{
  "feature_slug": "<slug>",
  "feature_name": "<name>",
  "kb_doc": "knowledge/<doc>",
  "branch": "feature/<slug>",
  "status": "planning",
  "started_at": "<ISO timestamp>",
  "last_updated": "<ISO timestamp>",
  "dod_total": <count of DoD items>,
  "dod_passing": 0
}
```

## Step 7 — Report to engineer

```
## Feature ready to implement

Branch:    feature/<slug>
Plan:      knowledge/implementation/<slug>/plan.md
DoD:       knowledge/implementation/<slug>/dod.md
Log:       knowledge/implementation/<slug>/log.md

--- DoD Summary ---
<paste the DoD checklist>

--- Execution order from plan ---
<paste the ordered steps>

Next: run /feature-implement to start coding.
```
