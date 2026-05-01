---
name: feature-review
description: Run the QA gate for the current feature. Invokes qa-reviewer agent, validates DoD, updates the dod.md checklist, and appends review results to the log.
---

You are running the quality gate for a feature. Follow these steps exactly.

## Step 1 — Load feature context

```bash
git branch --show-current
```

Derive slug. If not on a feature branch → STOP.

Read:
- `knowledge/implementation/<slug>/plan.md`
- `knowledge/implementation/<slug>/dod.md`
- `knowledge/implementation/<slug>/log.md` (last 50 lines for context)
- `knowledge/implementation/<slug>/status.json`

## Step 2 — Pre-check

```bash
python -m pytest tests/ -q --no-header 2>&1 | tail -10
```

If tests fail → append to log and STOP:
```
## [<timestamp>] Review blocked — tests failing

Failing: <list>
Action: Fix failing tests before review.
```

## Step 3 — Invoke qa-reviewer agent

Pass the qa-reviewer:
1. The full `plan.md`
2. The full `dod.md`
3. The last 50 lines of `log.md` for context
4. This mandatory instruction:

```
You are reviewing the implementation on branch feature/<slug>.

Your job:
1. Read all modified/created files listed in the plan
2. Run: python -m pytest tests/ -v
3. Write any missing tests in tests/test_<module>.py
4. For each item in dod.md, mark it ✅ PASS or ❌ FAIL with a one-line reason
5. Update knowledge/implementation/<slug>/dod.md with the results (replace the [ ] with ✅/❌)
6. Append this section to knowledge/implementation/<slug>/log.md:

## [<timestamp>] QA Review

### Test results
X passed, Y failed

### New tests written
- tests/test_X.py: N tests

### DoD results
- ✅/❌ <item>: <one-line reason>
...

### Verdict
READY TO MERGE / NEEDS FIXES

### Required fixes (if any)
1. <file:line> — <what to fix>

7. Update knowledge/implementation/<slug>/status.json:
   - If verdict is READY TO MERGE: set status to "approved"
   - If NEEDS FIXES: set status to "needs_fixes"
```

## Step 4 — Present results to engineer

After qa-reviewer completes, read `dod.md` and show:

```
## Review complete

Verdict: <READY TO MERGE / NEEDS FIXES>

DoD:
<paste updated dod.md>

<If NEEDS FIXES>:
Fix the issues above, then run /feature-implement to address them.
Run /feature-review again after fixes.

<If READY TO MERGE>:
Run /feature-done to create the PR and close the feature.
```
