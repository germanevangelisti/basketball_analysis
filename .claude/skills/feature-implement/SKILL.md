---
name: feature-implement
description: Execute the implementation for the current feature branch. Reads the plan, picks the right specialist agent, and runs it. Must be called from a feature branch after /feature-start.
---

You are orchestrating the implementation phase of a feature. Follow these steps exactly.

## Step 1 — Load feature context

```bash
git branch --show-current
```

Derive slug: strip `feature/` prefix from the branch name.

If not on a `feature/` branch → STOP: "Not on a feature branch. Run /feature-start <kb-doc> first."

Read:
- `knowledge/implementation/<slug>/plan.md` — implementation plan
- `knowledge/implementation/<slug>/log.md` — history so far
- `knowledge/implementation/<slug>/status.json` — current status

## Step 2 — Determine specialist agent

Read the plan's "Files to modify" and "Files to create" tables. Apply this routing:

| Files touched | Agent to invoke |
|--------------|-----------------|
| `trackers/`, `team_assigner/`, `court_keypoint_detector/`, `tactical_view_converter/`, `ball_aquisition/`, `pass_and_interception_detector/` | `cv-engineer` |
| `models/`, `database/`, `export/`, `stats_accumulator` | `data-engineer` |
| `drawers/`, `dashboard/` | `frontend-engineer` |
| Mix of CV + Data | Ask engineer: "This plan spans cv-engineer and data-engineer. Which domain first?" |
| Mix of Data + Frontend | Ask engineer: "This plan spans data-engineer and frontend-engineer. Which domain first?" |

## Step 3 — Invoke specialist agent

Pass the selected agent:
1. The **complete plan** from `knowledge/implementation/<slug>/plan.md`
2. The **log summary** (last 30 lines) from `knowledge/implementation/<slug>/log.md` for context
3. This **mandatory instruction**:

```
You are implementing on branch feature/<slug>. Do NOT create or switch branches.

Git protocol:
- After completing each file or module: git add <files> && git commit -m "feat(<slug>): <short description>"
- Use conventional commit types: feat, fix, refactor, test, chore

After ALL work is complete:
1. Run: python -m pytest tests/ -v
2. Append to knowledge/implementation/<slug>/log.md:

## [<timestamp>] Implementation completed by <agent-name>

### Files modified
- <file>: <what changed and why>

### Files created
- <file>: <purpose>

### Test results
- X passed, Y failed
- [List any failing tests]

### Key decisions
- <decision>: <rationale>

### Known risks / follow-ups
- <risk if any>

3. Update knowledge/implementation/<slug>/status.json:
   set "status" to "review_ready" and update "last_updated"
```

## Step 4 — Update log after agent completes

Append to `knowledge/implementation/<slug>/log.md`:
```
## [<timestamp>] Implement phase completed

Specialist: <agent used>
Commits: <output of git log --oneline feature/<slug> ^main>
Tests: <pass/fail summary>
Status: review_ready
```

Update `status.json`: `"status": "review_ready"`.

## Step 5 — Report to engineer

```
## Implementation complete

Agent used: <name>
Commits on branch:
<git log --oneline output>

Tests: X passed, Y failed

Log updated: knowledge/implementation/<slug>/log.md

--- Engineer checkpoint ---
Before running /feature-review, please:
1. Test manually: run the pipeline on a sample video
2. Check the visual output / stats output matches expectations
3. Run /feature-update "your feedback here" to log observations

Then run /feature-review when ready.
```
