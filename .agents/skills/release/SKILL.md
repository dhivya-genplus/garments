---
name: release
description: Release preparation — semantic version, changelog, migration audit, release notes, tag commands and tracker closure. Use by Releaser only.
---
# Release

Version: MAJOR.MINOR.PATCH; a module release bumps MINOR; hotfix bumps PATCH. Backend and
frontend repos carry the same version for a release.
Migration audit: list new migration files; flag `RemoveField`, `AlterField` type changes,
`RenameModel`, raw SQL; each flagged item needs a data plan and a reverse migration in the plan.
Release notes layout: Release vX.Y.Z — <date> · Modules included · New · Fixed · Changed
(user action needed) · Known issues · Upgrade steps (env vars, seeds, jobs).
Tag commands (human runs): `git checkout main && git merge --no-ff develop && git tag -a vX.Y.Z -m "..." && git push origin main --tags` in each repo.
Tracker closure after human confirmation: tickets → Deployed (version, date); product header →
current release; module row → release date.
