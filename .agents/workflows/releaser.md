---
description: Releaser — prepare a release: notes, migration check, version bump, tracker rows to Deployed after the human deploys (owner: Team lead / DevOps)
---
# /releaser <version e.g. v1.2.0> [module numbers included]
Allowed to edit: backend/CHANGELOG.md, frontend/<app>/CHANGELOG.md, version files
(pyproject/package.json version), docs/TRACKER.md. Never run deploy, migrate or server commands.
Skills to read: release.

1. Read docs/TRACKER.md: collect tickets with status Merged in the modules named; confirm each
   module's gate is marked passed. If any ticket in those modules is not Merged, stop and list them.
2. Plan artifact: tickets included, migrations included (list files; flag destructive ones:
   drops, renames, type changes), config/env changes needed, data migration steps. STOP for approval.
3. Write release notes grouped by module: features, fixes, changes requiring user action.
4. Bump version in both repos; update CHANGELOGs; propose the git tag commands for the human.
5. Produce the production checklist from the Team lead guide, pre-filled with this release's
   facts, for the team lead to sign.
6. After the human confirms "deployed to <env> on <date>": set every included ticket to Deployed
   with version and date, update the product header row (current release), add the module release
   date. Nothing before that confirmation.
