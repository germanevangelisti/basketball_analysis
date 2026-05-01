# Implementation Logs

Each subdirectory here is a feature implementation record. Created by `/feature-start`, maintained across sessions.

## Structure per feature

```
<feature-slug>/
  plan.md       — implementation plan (planner agent output)
  dod.md        — DoD checklist with ✅/❌ status after review
  log.md        — append-only implementation log (survives session resets)
  status.json   — machine-readable current state
```

## Status values

| Status | Meaning |
|--------|---------|
| `planning` | /feature-start ran, plan generated |
| `implementing` | /feature-implement in progress |
| `review_ready` | Specialist agent finished, awaiting /feature-review |
| `needs_fixes` | qa-reviewer found issues |
| `approved` | qa-reviewer approved, ready for /feature-done |
| `done` | PR created, feature closed |
| `blocked` | Engineer logged a blocker via /feature-update |

## SDLC flow

```
/feature-start <kb-doc>
    → DoR check → branch feature/<slug> → plan.md

/feature-implement
    → specialist agent → commits → log.md updated

/feature-update "feedback"     ← engineer manual testing
    → appends to log.md

/feature-review
    → qa-reviewer → dod.md updated → verdict

/feature-done
    → KB doc updated → PR created → feature archived
```
