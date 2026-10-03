---
description: Helper — apply a tracker row update for a ticket from its PR, CI result and walkthrough (owner: ticket owner)
---
# /update-tracker <ticket id> <new status> [notes]
Allowed to edit: docs/TRACKER.md only.

1. Find the ticket row. Read the branch/PR, CI result and latest Walkthrough if present.
2. Update only these cells: Status, Owner, Branch / PR, E2E, Reviewer, Release, AI usage
   (count of agent conversations used so far), Notes (one line). Keep every other cell.
3. If the status is Blocked, Notes must say why and who is needed. If Revision, add a row to the
   Revisions table. If an agent went outside scope, add a row to Agent incidents.
4. Show the before/after row for the owner to confirm; then save. Commit in the workspace repo:
   `tracker: <ticket> → <status>`.
