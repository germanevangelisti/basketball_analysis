---
name: feature-update
description: Append a timestamped entry to the current feature's persistent log. Use to record engineer feedback, manual test results, decisions, or blockers. Args: the note to log (quoted string).
---

You are persisting engineer feedback or implementation notes to the feature log. This ensures the implementation history survives session resets.

## Step 1 — Identify current feature

```bash
git branch --show-current
```

Derive slug: strip `feature/` prefix.

If not on a feature branch → STOP: "Not on a feature branch."

Read `knowledge/implementation/<slug>/status.json` to confirm the feature exists.

## Step 2 — Categorize the note

Classify the input note as one of:
- `feedback` — engineer observed something unexpected or wrong
- `decision` — a design or implementation choice was made
- `test-result` — manual testing observation
- `blocker` — something preventing progress
- `note` — general observation

## Step 3 — Append to log

Append to `knowledge/implementation/<slug>/log.md`:

```markdown
## [<ISO timestamp>] [<category>] Engineer update

<The note content verbatim>
```

If the category is `feedback` or `blocker`, also note:
```
Action needed: yes
```

## Step 4 — Update status.json

Update `last_updated` timestamp.
If category is `blocker`: set `status` to `"blocked"`.

## Step 5 — Confirm to engineer

```
Logged to knowledge/implementation/<slug>/log.md

Category: <category>
Status: <current status>

<If feedback/blocker>:
To address this feedback, run /feature-implement again — the agent will read the log and see your note.
```
