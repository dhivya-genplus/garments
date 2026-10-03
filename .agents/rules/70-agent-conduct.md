---
trigger: always_on
---
# How every agent behaves

1. Start by reading GEMINI.md, the ticket row in docs/TRACKER.md and the PRD section it cites.
2. Produce an Implementation Plan and Task List. STOP and wait for human approval before
   writing or changing any file.
3. One ticket per conversation. Do not pick up related work the ticket did not ask for.
4. Implement one task at a time; run the relevant tests after each; show the diff.
5. If a test fails three times on the same cause, stop and report the root cause instead of
   trying again.
6. Never weaken, skip or delete an existing test to make the suite pass.
7. If anything in the PRD, contract or rules is ambiguous, ask the human counterpart; do not guess.
8. Finish with a Walkthrough: what changed, how it was tested, which acceptance criteria are
   met, which are not, and the exact tracker row update to apply.
9. Stay inside the repo and folders your workflow allows (see 00-workspace-layout).
